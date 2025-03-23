"""
Cron jobs for Travian Whispers.
"""
import logging
import time
import threading
import schedule
from datetime import datetime, timedelta

from database.mongodb import MongoDB
from database.models.user import User
from database.models.subscription import SubscriptionPlan
from database.models.transaction import Transaction
from email_module.sender import send_subscription_expiry_email

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('cron_jobs')

# Initialize database connection
db = MongoDB()

def check_expired_subscriptions():
    """
    Check for expired subscriptions and update their status.
    This should run daily.
    """
    logger.info("Running subscription expiry check...")
    
    try:
        # Connect to database if not already connected
        if not db.get_db():
            db.connect()
        
        # Initialize models
        user_model = User()
        
        # Get current time
        now = datetime.utcnow()
        
        # Find users with expired subscriptions
        users_collection = db.get_collection("users")
        expired_users = users_collection.find({
            "subscription.status": "active",
            "subscription.endDate": {"$lt": now}
        })
        
        count = 0
        for user in expired_users:
            # Update subscription status to expired
            users_collection.update_one(
                {"_id": user["_id"]},
                {"$set": {
                    "subscription.status": "expired",
                    "updatedAt": now
                }}
            )
            
            # Send expiry email
            try:
                send_subscription_expiry_email(
                    user["email"],
                    user["username"]
                )
            except Exception as e:
                logger.error(f"Failed to send expiry email to {user['email']}: {e}")
            
            count += 1
        
        logger.info(f"Updated {count} expired subscriptions.")
    except Exception as e:
        logger.error(f"Error checking expired subscriptions: {e}")
    finally:
        # Don't disconnect as the connection is shared

def send_renewal_reminders():
    """
    Send renewal reminders to users whose subscriptions are about to expire.
    This should run daily.
    """
    logger.info("Sending renewal reminders...")
    
    try:
        # Connect to database if not already connected
        if not db.get_db():
            db.connect()
        
        # Initialize models
        user_model = User()
        
        # Get current time and calculate dates
        now = datetime.utcnow()
        three_days_from_now = now + timedelta(days=3)
        
        # Find users with subscriptions expiring in 3 days
        users_collection = db.get_collection("users")
        expiring_users = users_collection.find({
            "subscription.status": "active",
            "subscription.endDate": {
                "$gte": now,
                "$lte": three_days_from_now
            }
        })
        
        count = 0
        for user in expiring_users:
            # Get subscription plan details
            plan_model = SubscriptionPlan()
            plan = plan_model.get_plan_by_id(user["subscription"]["planId"])
            
            if not plan:
                continue
            
            # Send reminder email
            try:
                from email_module.sender import send_renewal_reminder_email
                send_renewal_reminder_email(
                    user["email"],
                    user["username"],
                    plan["name"],
                    user["subscription"]["endDate"].strftime("%Y-%m-%d")
                )
            except Exception as e:
                logger.error(f"Failed to send renewal reminder to {user['email']}: {e}")
            
            count += 1
        
        logger.info(f"Sent {count} renewal reminders.")
    except Exception as e:
        logger.error(f"Error sending renewal reminders: {e}")
    finally:
        # Don't disconnect as the connection is shared

def cleanup_old_tokens():
    """
    Clean up old verification and reset tokens.
    This should run weekly.
    """
    logger.info("Cleaning up old tokens...")
    
    try:
        # Connect to database if not already connected
        if not db.get_db():
            db.connect()
        
        # Get current time
        now = datetime.utcnow()
        one_week_ago = now - timedelta(days=7)
        
        # Find and update users with old verification tokens
        users_collection = db.get_collection("users")
        verification_result = users_collection.update_many(
            {
                "verificationToken": {"$ne": None},
                "createdAt": {"$lt": one_week_ago}
            },
            {"$set": {
                "verificationToken": None,
                "updatedAt": now
            }}
        )
        
        # Find and update users with expired reset tokens
        reset_result = users_collection.update_many(
            {
                "resetPasswordToken": {"$ne": None},
                "resetPasswordExpires": {"$lt": now}
            },
            {"$set": {
                "resetPasswordToken": None,
                "resetPasswordExpires": None,
                "updatedAt": now
            }}
        )
        
        logger.info(f"Cleaned up {verification_result.modified_count} verification tokens and {reset_result.modified_count} reset tokens.")
    except Exception as e:
        logger.error(f"Error cleaning up tokens: {e}")
    finally:
        # Don't disconnect as the connection is shared

def generate_admin_report():
    """
    Generate and email a report for admins.
    This should run weekly.
    """
    logger.info("Generating admin report...")
    
    try:
        # Connect to database if not already connected
        if not db.get_db():
            db.connect()
        
        # Initialize models
        user_model = User()
        transaction_model = Transaction()
        
        # Get statistics
        total_users = user_model.collection.count_documents({})
        active_users = user_model.collection.count_documents({"subscription.status": "active"})
        expired_users = user_model.collection.count_documents({"subscription.status": "expired"})
        
        # Transactions in the last 7 days
        now = datetime.utcnow()
        seven_days_ago = now - timedelta(days=7)
        recent_transactions = transaction_model.collection.count_documents({
            "createdAt": {"$gte": seven_days_ago}
        })
        
        # Calculate revenue in the last 7 days
        revenue_pipeline = [
            {"$match": {
                "createdAt": {"$gte": seven_days_ago},
                "status": "completed"
            }},
            {"$group": {
                "_id": None,
                "total": {"$sum": "$amount"}
            }}
        ]
        revenue_result = list(transaction_model.collection.aggregate(revenue_pipeline))
        revenue = revenue_result[0]["total"] if revenue_result else 0
        
        # Email the report to admins
        try:
            # Find admin users
            admin_users = user_model.collection.find({"role": "admin"})
            
            for admin in admin_users:
                from email_module.sender import send_admin_report_email
                send_admin_report_email(
                    admin["email"],
                    admin["username"],
                    {
                        "total_users": total_users,
                        "active_users": active_users,
                        "expired_users": expired_users,
                        "recent_transactions": recent_transactions,
                        "revenue": revenue,
                        "date_range": f"{seven_days_ago.strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')}"
                    }
                )
        except Exception as e:
            logger.error(f"Failed to send admin report: {e}")
        
        logger.info("Admin report generated and sent.")
    except Exception as e:
        logger.error(f"Error generating admin report: {e}")
    finally:
        # Don't disconnect as the connection is shared

def run_scheduler():
    """Run the scheduler in a separate thread."""
    # Schedule jobs
    schedule.every().day.at("00:00").do(check_expired_subscriptions)
    schedule.every().day.at("12:00").do(send_renewal_reminders)
    schedule.every().monday.at("03:00").do(cleanup_old_tokens)
    schedule.every().sunday.at("06:00").do(generate_admin_report)
    
    # Run continuously
    while True:
        schedule.run_pending()
        time.sleep(60)  # Sleep for 1 minute

def start_scheduler():
    """Start the scheduler in a background thread."""
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    logger.info("Cron job scheduler started.")
    return scheduler_thread

# IP rotation job
@scheduler.scheduled_job('interval', minutes=15)
def rotate_ips():
    from utils.rotation_strategy import RotationStrategy
    
    strategy = RotationStrategy()
    rotated = strategy.apply_rotation_strategy(strategy.STRATEGY_PATTERN_BASED)
    
    logger.info(f"Scheduled IP rotation: {rotated} IPs rotated")

# Proxy health check job
@scheduler.scheduled_job('interval', hours=2)
def check_proxy_health():
    from utils.proxy_metrics import ProxyHealthCheck
    
    health_check = ProxyHealthCheck()
    actions = health_check.handle_failing_proxies()
    
    logger.info(f"Proxy health check: "
                f"{len(actions['banned'])} banned, "
                f"{len(actions['flagged'])} flagged, "
                f"{len(actions['rotated'])} rotated")

# Fetch new proxies job
@scheduler.scheduled_job('interval', hours=6)
def fetch_new_proxies():
    from database.models.proxy_service import ProxyService
    
    proxy_service = ProxyService()
    fetched = proxy_service.auto_fetch_proxies()
    
    logger.info(f"Auto-fetched {fetched} new proxies")