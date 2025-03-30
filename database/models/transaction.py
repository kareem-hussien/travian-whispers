"""
Transaction model for Travian Whispers web application.
This module defines the transaction model for subscription payments.
"""
import logging
from datetime import datetime
from bson import ObjectId
from pymongo import DESCENDING

from database.models.init import get_collection
from database.models.user import User

# Initialize logger
logger = logging.getLogger(__name__)

class Transaction:
    """Transaction model for subscription payments."""
    
    def __init__(self):
        """Initialize transaction model."""
        self.collection = get_collection('transactions')
    
    def create_transaction(self, user_id, plan_id, amount, payment_method, payment_id, billing_period):
        """
        Create a new transaction record.
        
        Args:
            user_id (str): User ID
            plan_id (str): Subscription plan ID
            amount (float): Transaction amount
            payment_method (str): Payment method (paypal, credit_card, etc.)
            payment_id (str): Payment ID from payment gateway
            billing_period (str): Billing period (monthly, yearly)
        
        Returns:
            str: Transaction ID if successful, None otherwise
        """
        try:
            # Create transaction record
            transaction = {
                'userId': user_id,
                'planId': ObjectId(plan_id),
                'amount': float(amount),
                'status': 'pending',
                'paymentMethod': payment_method,
                'paymentId': payment_id,
                'billingPeriod': billing_period,
                'createdAt': datetime.utcnow()
            }
            
            # Insert transaction
            result = self.collection.insert_one(transaction)
            
            if result.inserted_id:
                return str(result.inserted_id)
            else:
                return None
        except Exception as e:
            logger.error(f"Error creating transaction: {e}")
            return None
    
    def get_transaction(self, transaction_id):
        """
        Get transaction details.
        
        Args:
            transaction_id (str): Transaction ID
        
        Returns:
            dict: Transaction details or None if not found
        """
        try:
            # Get transaction
            transaction = self.collection.find_one({'_id': ObjectId(transaction_id)})
            
            return transaction
        except Exception as e:
            logger.error(f"Error getting transaction: {e}")
            return None
    
    def update_transaction_status(self, transaction_id, status):
        """
        Update transaction status.
        
        Args:
            transaction_id (str): Transaction ID
            status (str): New status (completed, failed, refunded)
        
        Returns:
            bool: True if status was updated successfully, False otherwise
        """
        try:
            # Update transaction status
            result = self.collection.update_one(
                {'_id': ObjectId(transaction_id)},
                {'$set': {'status': status, 'updatedAt': datetime.utcnow()}}
            )
            
            # If transaction is completed, update user subscription
            if status == 'completed':
                transaction = self.get_transaction(transaction_id)
                
                if transaction:
                    # Update user subscription
                    self._update_user_subscription(transaction)
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating transaction status: {e}")
            return False
    
    def get_user_transactions(self, user_id, status=None):
        """
        Get transactions for a user.
        
        Args:
            user_id (str): User ID
            status (str): Filter by status (optional)
        
        Returns:
            list: List of transactions
        """
        try:
            # Build query
            query = {'userId': user_id}
            
            # Add status filter if provided
            if status:
                query['status'] = status
            
            # Get transactions
            transactions = list(self.collection.find(query).sort('createdAt', DESCENDING))
            
            return transactions
        except Exception as e:
            logger.error(f"Error getting user transactions: {e}")
            return []
    
    def _update_user_subscription(self, transaction):
        """
        Update user subscription based on completed transaction.
        
        Args:
            transaction (dict): Transaction data
        
        Returns:
            bool: True if subscription was updated successfully, False otherwise
        """
        try:
            # Initialize user model
            user_model = User()
            
            # Get user
            user = user_model.get_user_by_id(transaction['userId'])
            
            if not user:
                logger.error(f"User not found: {transaction['userId']}")
                return False
            
            # Calculate subscription period based on billing period
            from datetime import timedelta
            
            # Start subscription from now or extend existing subscription
            if user['subscription']['status'] == 'active' and user['subscription']['endDate'] > datetime.utcnow():
                # Extend existing subscription
                start_date = user['subscription']['endDate']
            else:
                # Start new subscription
                start_date = datetime.utcnow()
            
            # Determine duration based on billing period
            if transaction['billingPeriod'] == 'yearly':
                end_date = start_date + timedelta(days=365)
            else:
                # Default to monthly
                end_date = start_date + timedelta(days=30)
            
            # Update subscription data
            subscription_data = {
                'subscription': {
                    'planId': transaction['planId'],
                    'status': 'active',
                    'startDate': start_date,
                    'endDate': end_date
                }
            }
            
            # Add payment to history
            payment_entry = {
                'transactionId': transaction['_id'],
                'amount': transaction['amount'],
                'date': transaction['createdAt'],
                'method': transaction['paymentMethod']
            }
            
            # Update user subscription
            result = user_model.collection.update_one(
                {'_id': ObjectId(transaction['userId'])},
                {
                    '$set': subscription_data,
                    '$push': {'subscription.paymentHistory': payment_entry}
                }
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating user subscription: {e}")
            return False
