"""
Subscription plan model for MongoDB integration.
"""
from datetime import datetime
from bson import ObjectId
from database.mongodb import MongoDB

class SubscriptionPlan:
    """Subscription plan model for Travian Whispers."""
    
    def __init__(self):
        """Initialize the SubscriptionPlan model."""
        self.db = MongoDB().get_db()
        self.collection = self.db["subscriptionPlans"] if self.db else None
    
    def create_plan(self, name, description, monthly_price, yearly_price, features):
        """
        Create a new subscription plan.
        
        return None
    
    def get_plan_by_id(self, plan_id):
        """
        Get a plan by ID.
        
        Args:
            plan_id (str): Plan ID
            
        Returns:
            dict: Plan document or None if not found
        """
        if not self.collection:
            return None
            
        try:
            return self.collection.find_one({"_id": ObjectId(plan_id)})
        except:
            return None
    
    def get_plan_by_name(self, name):
        """
        Get a plan by name.
        
        Args:
            name (str): Plan name
            
        Returns:
            dict: Plan document or None if not found
        """
        if not self.collection:
            return None
        
        return self.collection.find_one({"name": name})
    
    def update_plan(self, plan_id, update_data):
        """
        Update a subscription plan.
        
        Args:
            plan_id (str): Plan ID
            update_data (dict): Data to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.collection:
            return False
            
        try:
            # Don't allow updating some fields directly
            protected_fields = ["_id", "createdAt"]
            for field in protected_fields:
                if field in update_data:
                    del update_data[field]
            
            update_data["updatedAt"] = datetime.utcnow()
            
            result = self.collection.update_one(
                {"_id": ObjectId(plan_id)},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating plan: {e}")
            return False
    
    def delete_plan(self, plan_id):
        """
        Delete a subscription plan.
        
        Args:
            plan_id (str): Plan ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.collection:
            return False
            
        try:
            result = self.collection.delete_one({"_id": ObjectId(plan_id)})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting plan: {e}")
            return False
    
    def list_plans(self):
        """
        List all subscription plans.
        
        Returns:
            list: List of plan documents
        """
        if not self.collection:
            return []
            
        try:
            cursor = self.collection.find().sort("price.monthly", 1)
            return list(cursor)
        except Exception as e:
            print(f"Error listing plans: {e}")
            return []
    
    def create_default_plans(self):
        """
        Create default subscription plans if none exist.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.collection:
            return False
        
        # Check if plans already exist
        if self.collection.count_documents({}) > 0:
            return False
        
        try:
            # Basic plan
            basic = {
                "name": "Basic",
                "description": "Basic automation for small Travian players",
                "price": {
                    "monthly": 4.99,
                    "yearly": 49.99
                },
                "features": {
                    "autoFarm": True,
                    "trainer": False,
                    "notification": True,
                    "maxVillages": 2,
                    "maxTasks": 1
                },
                "createdAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow()
            }
            
            # Standard plan
            standard = {
                "name": "Standard",
                "description": "Standard automation for regular Travian players",
                "price": {
                    "monthly": 9.99,
                    "yearly": 99.99
                },
                "features": {
                    "autoFarm": True,
                    "trainer": True,
                    "notification": True,
                    "maxVillages": 5,
                    "maxTasks": 2
                },
                "createdAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow()
            }
            
            # Premium plan
            premium = {
                "name": "Premium",
                "description": "Premium automation for dedicated Travian players",
                "price": {
                    "monthly": 19.99,
                    "yearly": 199.99
                },
                "features": {
                    "autoFarm": True,
                    "trainer": True,
                    "notification": True,
                    "maxVillages": 15,
                    "maxTasks": 5
                },
                "createdAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow()
            }
            
            self.collection.insert_many([basic, standard, premium])
            return True
        except Exception as e:
            print(f"Error creating default plans: {e}")
            return False
Args:
            name (str): Plan name
            description (str): Plan description
            monthly_price (float): Monthly price
            yearly_price (float): Yearly price
            features (dict): Plan features
            
        Returns:
            dict: Created plan document or None if failed
        """
        if not self.collection:
            return None
            
        # Validate inputs
        if not name or not isinstance(monthly_price, (int, float)) or not isinstance(yearly_price, (int, float)):
            return None
            
        # Check if plan name already exists
        if self.collection.find_one({"name": name}):
            return None
        
        # Validate features
        required_features = ["autoFarm", "trainer", "notification", "maxVillages", "maxTasks"]
        for feature in required_features:
            if feature not in features:
                if feature in ["maxVillages", "maxTasks"]:
                    features[feature] = 1  # Default value
                else:
                    features[feature] = False  # Default value
        
        # Create plan document
        plan = {
            "name": name,
            "description": description,
            "price": {
                "monthly": float(monthly_price),
                "yearly": float(yearly_price)
            },
            "features": features,
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
        
        try:
            result = self.collection.insert_one(plan)
            if result.inserted_id:
                plan["_id"] = result.inserted_id
                return plan
        except Exception as e:
            print(f"Error creating plan: {e}")
        
        