import os
from pymongo import MongoClient
from datetime import datetime

class MongoDBHandler:
    def __init__(self):
        self.uri = os.environ.get('MONGO_URI')
        self.client = None
        self.db = None
        self.collection = None
        
        if self.uri:
            try:
                self.client = MongoClient(self.uri)
                self.db = self.client['zombie_hunter']
                self.collection = self.db['scans']
                print("MongoDB: Connected successfully.")
            except Exception as e:
                print(f"MongoDB Error: {e}")

    def save_scan(self, data):
        """Saves scan results to MongoDB Atlas."""
        if not self.collection:
            print("MongoDB Alert: No connection. Skipping save.")
            return False
            
        try:
            # Ensure timestamp is a datetime object for better querying
            data_to_store = data.copy()
            if isinstance(data_to_store.get('timestamp'), str):
                data_to_store['timestamp'] = datetime.fromisoformat(data_to_store['timestamp'])
            
            result = self.collection.insert_one(data_to_store)
            print(f"MongoDB: Saved scan with ID {result.inserted_id}")
            return True
        except Exception as e:
            print(f"MongoDB Save Error: {e}")
            return False

    def get_history(self, limit=50):
        """Retrieves scan history from MongoDB."""
        if not self.collection:
            print("MongoDB Alert: No connection. Returning empty history.")
            return []
            
        try:
            # Sort by timestamp descending
            cursor = self.collection.find({}, {'_id': 0}).sort('timestamp', -1).limit(limit)
            history = list(cursor)
            
            # Convert datetime back to string for JSON serialization
            for item in history:
                if isinstance(item.get('timestamp'), datetime):
                    item['timestamp'] = item['timestamp'].isoformat()
            
            return history[::-1] # Return in chronological order for the chart
        except Exception as e:
            print(f"MongoDB Fetch Error: {e}")
            return []

# Singleton instance
mongo_handler = MongoDBHandler()
