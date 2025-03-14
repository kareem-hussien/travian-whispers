from pymongo import MongoClient
from bson.objectid import ObjectId
import config

def update_user_to_admin(user_id):
    """
    Update a user's role to admin in the MongoDB database.
    
    Args:
        user_id (str): User ID to update
    """
    try:
        # Connect to MongoDB
        client = MongoClient(config.MONGODB_URI)
        db = client[config.MONGODB_DB_NAME]
        users_collection = db["users"]
        
        # Convert string ID to ObjectId
        object_id = ObjectId(user_id)
        
        # Update the user
        result = users_collection.update_one(
            {"_id": object_id},
            {"$set": {"role": "admin"}}
        )
        
        if result.modified_count > 0:
            print(f"Success! User with ID {user_id} has been updated to admin role.")
            
            # Verify the update
            user = users_collection.find_one({"_id": object_id})
            print(f"Updated user details: Username: {user['username']}, Role: {user['role']}")
        else:
            print(f"No update made. User with ID {user_id} might already be an admin or not exist.")
        
        # Close the connection
        client.close()
        
    except Exception as e:
        print(f"Error updating user: {str(e)}")

# The user ID from your JSON
user_id = "67d3a970944d0daeeb2bdcb2"

# Call the function to update the user
update_user_to_admin(user_id)