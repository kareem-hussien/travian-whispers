"""
Transaction model for MongoDB integration.
"""
from datetime import datetime
from bson import ObjectId
from database.mongodb import MongoDB

class Transaction:
    """Transaction model for Travian Whispers payment system."""
    
    STATUS_OPTIONS = ["completed", "pending", "failed", "refunded"]
    TYPE_OPTIONS = ["subscription", "renewal"]
    PERIOD_OPTIONS = ["monthly", "yearly"]
    
    def __init__(self):
        """Initialize the Transaction model."""
        self.db = MongoDB().get_db()
        self.collection = None
        if self.db is not None:  # Explicit None check
            self.collection = self.db["transactions"]
    
    def create_transaction(self, user_id, plan_id, payment_id, amount, status, payment_type, 
                           payment_method, billing_period):
        """
        Create a new transaction record.
        
        Args:
            user_id (str): User ID
            plan_id (str): Subscription plan ID
            payment_id (str): Payment provider's transaction ID
            amount (float): Transaction amount
            status (str): Transaction status
            payment_type (str): Transaction type
            payment_method (str): Payment method
            billing_period (str): Billing period
            
        Returns:
            dict: Created transaction document or None if failed
        """
        if self.collection is None:  # Explicit None check
            return None
        
        # Validate inputs
        if not user_id or not plan_id or not payment_id:
            return None
        
        if status not in self.STATUS_OPTIONS:
            status = "pending"
            
        if payment_type not in self.TYPE_OPTIONS:
            payment_type = "subscription"
            
        if billing_period not in self.PERIOD_OPTIONS:
            billing_period = "monthly"
        
        # Create transaction document
        transaction = {
            "userId": ObjectId(user_id),
            "planId": ObjectId(plan_id),
            "paymentId": payment_id,
            "amount": float(amount),
            "status": status,
            "type": payment_type,
            "paymentMethod": payment_method,
            "billingPeriod": billing_period,
            "createdAt": datetime.utcnow()
        }
        
        try:
            result = self.collection.insert_one(transaction)
            if result.inserted_id:
                transaction["_id"] = result.inserted_id
                return transaction
        except Exception as e:
            print(f"Error creating transaction: {e}")
        
        return None
    
    def get_transaction(self, transaction_id):
        """
        Get a transaction by ID.
        
        Args:
            transaction_id (str): Transaction ID
            
        Returns:
            dict: Transaction document or None if not found
        """
        if self.collection is None:  # Explicit None check
            return None
        
        try:
            return self.collection.find_one({"_id": ObjectId(transaction_id)})
        except:
            return None
    
    def get_transaction_by_payment_id(self, payment_id):
        """
        Get a transaction by payment ID.
        
        Args:
            payment_id (str): Payment provider's transaction ID
            
        Returns:
            dict: Transaction document or None if not found
        """
        if self.collection is None:  # Explicit None check
            return None
        
        return self.collection.find_one({"paymentId": payment_id})
    
    def update_transaction_status(self, transaction_id, status):
        """
        Update a transaction's status.
        
        Args:
            transaction_id (str): Transaction ID
            status (str): New status
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.collection is None or status not in self.STATUS_OPTIONS:  # Explicit None check
            return False
        
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(transaction_id)},
                {"$set": {"status": status}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating transaction status: {e}")
            return False
    
    def update_payment_id(self, transaction_id, payment_id):
        """
        Update a transaction's payment ID.
        
        Args:
            transaction_id (str): Transaction ID
            payment_id (str): New payment ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.collection is None:  # Explicit None check
            return False
        
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(transaction_id)},
                {"$set": {"paymentId": payment_id}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating payment ID: {e}")
            return False
    
    def get_user_transactions(self, user_id, limit=10):
        """
        Get a user's transaction history.
        
        Args:
            user_id (str): User ID
            limit (int): Maximum number of transactions to return
            
        Returns:
            list: List of transaction documents
        """
        if self.collection is None:  # Explicit None check
            return []
        
        try:
            cursor = self.collection.find(
                {"userId": ObjectId(user_id)}
            ).sort("createdAt", -1).limit(limit)
            
            return list(cursor)
        except Exception as e:
            print(f"Error getting user transactions: {e}")
            return []
    
    def get_recent_transactions(self, limit=20, status=None):
        """
        Get recent transactions, optionally filtered by status.
        
        Args:
            limit (int): Maximum number of transactions to return
            status (str, optional): Filter by status
            
        Returns:
            list: List of transaction documents
        """
        if self.collection is None:  # Explicit None check
            return []
        
        query = {}
        if status and status in self.STATUS_OPTIONS:
            query["status"] = status
        
        try:
            cursor = self.collection.find(query).sort("createdAt", -1).limit(limit)
            return list(cursor)
        except Exception as e:
            print(f"Error getting recent transactions: {e}")
            return []