"""
PayPal integration for Travian Whispers subscription payments.
"""
import logging
import requests
import json
from datetime import datetime, timedelta
import config
from database.models.transaction import Transaction
from database.models.user import User
from database.models.subscription import SubscriptionPlan
from email_module.sender import send_subscription_confirmation_email

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('payment.paypal')

def get_access_token():
    """
    Get PayPal API access token.
    
    Returns:
        str: Access token or None if failed
    """
    try:
        url = f"{config.PAYPAL_BASE_URL}/v1/oauth2/token"
        headers = {
            "Accept": "application/json",
            "Accept-Language": "en_US"
        }
        data = "grant_type=client_credentials"
        
        response = requests.post(
            url,
            auth=(config.PAYPAL_CLIENT_ID, config.PAYPAL_SECRET),
            headers=headers,
            data=data
        )
        
        if response.status_code == 200:
            return response.json().get("access_token")
        
        logger.error(f"Failed to get PayPal access token: {response.text}")
        return None
    except Exception as e:
        logger.error(f"Error getting PayPal access token: {e}")
        return None

def create_subscription_order(plan_id, user_id, success_url, cancel_url):
    """
    Create a PayPal order for subscription payment.
    
    Args:
        plan_id (str): Subscription plan ID
        user_id (str): User ID
        success_url (str): Redirect URL after successful payment
        cancel_url (str): Redirect URL after cancelled payment
        
    Returns:
        tuple: (success, order_id, approval_url)
    """
    # Get subscription plan
    plan_model = SubscriptionPlan()
    plan = plan_model.get_plan_by_id(plan_id)
    
    if not plan:
        return False, None, None
    
    # Get user
    user_model = User()
    user = user_model.get_user_by_id(user_id)
    
    if not user:
        return False, None, None
    
    # Get access token
    access_token = get_access_token()
    if not access_token:
        return False, None, None
    
    try:
        url = f"{PAYPAL_BASE_URL}/v2/checkout/orders"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        
        # Create order payload
        payload = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "description": f"Travian Whispers {plan['name']} Subscription",
                    "amount": {
                        "currency_code": "USD",
                        "value": str(plan['price']['monthly'])
                    },
                    "custom_id": f"{user_id}|{plan_id}|monthly"
                }
            ],
            "application_context": {
                "brand_name": "Travian Whispers",
                "landing_page": "BILLING",
                "shipping_preference": "NO_SHIPPING",
                "user_action": "PAY_NOW",
                "return_url": success_url,
                "cancel_url": cancel_url
            }
        }
        
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(payload)
        )
        
        if response.status_code in (200, 201):
            data = response.json()
            order_id = data.get("id")
            
            # Find approval URL
            approval_url = next(
                (link["href"] for link in data.get("links", []) if link["rel"] == "approve"),
                None
            )
            
            if order_id and approval_url:
                # Create transaction record
                transaction_model = Transaction()
                transaction = transaction_model.create_transaction(
                    user_id=user_id,
                    plan_id=plan_id,
                    payment_id=order_id,
                    amount=float(plan['price']['monthly']),
                    status="pending",
                    payment_type="subscription",
                    payment_method="paypal",
                    billing_period="monthly"
                )
                
                if transaction:
                    return True, order_id, approval_url
            
            logger.error(f"Failed to extract order details from PayPal response: {data}")
            return False, None, None
        
        logger.error(f"Failed to create PayPal order: {response.text}")
        return False, None, None
    except Exception as e:
        logger.error(f"Error creating PayPal order: {e}")
        return False, None, None

def capture_payment(order_id):
    """
    Capture a payment after approval.
    
    Args:
        order_id (str): PayPal order ID
        
    Returns:
        tuple: (success, capture_id)
    """
    # Get access token
    access_token = get_access_token()
    if not access_token:
        return False, None
    
    try:
        url = f"{PAYPAL_BASE_URL}/v2/checkout/orders/{order_id}/capture"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        
        response = requests.post(url, headers=headers)
        
        if response.status_code in (200, 201):
            data = response.json()
            capture_id = data.get("id")
            
            if capture_id:
                return True, capture_id
            
            logger.error(f"Failed to extract capture_id from PayPal response: {data}")
            return False, None
        
        logger.error(f"Failed to capture PayPal payment: {response.text}")
        return False, None
    except Exception as e:
        logger.error(f"Error capturing PayPal payment: {e}")
        return False, None

def process_successful_payment(order_id):
    """
    Process a successful payment and update user subscription.
    
    Args:
        order_id (str): PayPal order ID
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Get transaction details
    transaction_model = Transaction()
    transaction = transaction_model.get_transaction_by_payment_id(order_id)
    
    if not transaction:
        logger.error(f"Transaction not found for order_id: {order_id}")
        return False
    
    # Update transaction status
    if not transaction_model.update_transaction_status(transaction["_id"], "completed"):
        logger.error(f"Failed to update transaction status: {transaction['_id']}")
        return False
    
    # Get user and plan details
    user_model = User()
    plan_model = SubscriptionPlan()
    
    user = user_model.get_user_by_id(transaction["userId"])
    plan = plan_model.get_plan_by_id(transaction["planId"])
    
    if not user or not plan:
        logger.error(f"User or plan not found: user_id={transaction['userId']}, plan_id={transaction['planId']}")
        return False
    
    # Calculate subscription dates
    start_date = datetime.utcnow()
    
    if transaction["billingPeriod"] == "monthly":
        end_date = start_date + timedelta(days=30)
    else:  # yearly
        end_date = start_date + timedelta(days=365)
    
    # Update user subscription
    if not user_model.update_subscription(
        user_id=str(user["_id"]),
        plan_id=str(plan["_id"]),
        status="active",
        start_date=start_date,
        end_date=end_date
    ):
        logger.error(f"Failed to update user subscription: {user['_id']}")
        return False
    
    # Add payment record
    if not user_model.add_payment_record(
        user_id=str(user["_id"]),
        payment_id=order_id,
        amount=transaction["amount"],
        method="paypal"
    ):
        logger.error(f"Failed to add payment record for user: {user['_id']}")
        # Continue as this is not critical
    
    # Send confirmation email
    try:
        send_subscription_confirmation_email(
            to_email=user["email"],
            username=user["username"],
            plan_name=plan["name"],
            end_date=end_date.strftime("%Y-%m-%d"),
            amount=transaction["amount"],
            payment_id=order_id
        )
    except Exception as e:
        logger.error(f"Failed to send subscription confirmation email: {e}")
        # Continue as this is not critical
    
    return True

def verify_webhook_signature(request_body, headers):
    """
    Verify PayPal webhook signature.
    
    Args:
        request_body (bytes): Raw request body
        headers (dict): Request headers
        
    Returns:
        bool: True if signature is valid, False otherwise
    """
    # This is a simplified implementation
    # For production, implement proper webhook signature verification
    # https://developer.paypal.com/docs/api/webhooks/v1/#verify-webhook-signature
    
    return True  # Placeholder for actual verification

def handle_webhook_event(event_type, event_data):
    """
    Handle PayPal webhook events.
    
    Args:
        event_type (str): Event type
        event_data (dict): Event data
        
    Returns:
        bool: True if handled successfully, False otherwise
    """
    logger.info(f"Received PayPal webhook event: {event_type}")
    
    if event_type == "PAYMENT.CAPTURE.COMPLETED":
        resource = event_data.get("resource", {})
        order_id = resource.get("supplementary_data", {}).get("related_ids", {}).get("order_id")
        
        if order_id:
            return process_successful_payment(order_id)
        
        logger.error(f"Order ID not found in webhook event data: {event_data}")
        return False
    
    # Handle other event types as needed
    return True  # Return True for unhandled events to acknowledge receipt
