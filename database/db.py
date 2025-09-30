import os
from pymongo import MongoClient
from datetime import datetime
import asyncio
from typing import Optional, Dict, List

class Database:
    def __init__(self):
        self.client = None
        self.db = None
        
    async def connect(self):
        """Connect to MongoDB"""
        try:
            mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
            database_name = os.getenv('DATABASE_NAME', 'ip5x_discord_bot')
            
            self.client = MongoClient(mongodb_uri)
            self.db = self.client[database_name]
            
            # Test connection
            self.client.admin.command('ping')
            print("✅ Successfully connected to MongoDB")
            
            # Create indexes
            await self._create_indexes()
            
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            
    async def _create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # Users collection indexes
            self.db.users.create_index("user_id", unique=True)
            self.db.users.create_index("group")
            
            # Voice channels collection indexes  
            self.db.voice_channels.create_index("channel_id", unique=True)
            self.db.voice_channels.create_index("owner_id")
            
            # Applications collection indexes
            self.db.applications.create_index("user_id")
            self.db.applications.create_index("group")
            self.db.applications.create_index("status")
            
            print("✅ Database indexes created successfully")
        except Exception as e:
            print(f"❌ Failed to create indexes: {e}")

    # User Management
    async def add_user(self, user_id: int, username: str, group: str = None) -> bool:
        """Add new user to database"""
        try:
            user_data = {
                "user_id": user_id,
                "username": username,
                "group": group,
                "joined_at": datetime.utcnow(),
                "is_guest": group is None,
                "warnings": 0,
                "muted_until": None
            }
            
            result = self.db.users.update_one(
                {"user_id": user_id},
                {"$set": user_data},
                upsert=True
            )
            return True
        except Exception as e:
            print(f"❌ Failed to add user {user_id}: {e}")
            return False
    
    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user from database"""
        try:
            return self.db.users.find_one({"user_id": user_id})
        except Exception as e:
            print(f"❌ Failed to get user {user_id}: {e}")
            return None
    
    async def update_user_group(self, user_id: int, group: str) -> bool:
        """Update user's group"""
        try:
            result = self.db.users.update_one(
                {"user_id": user_id},
                {"$set": {"group": group, "is_guest": False}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"❌ Failed to update user group {user_id}: {e}")
            return False
    
    async def get_group_members(self, group: str) -> List[Dict]:
        """Get all members of a specific group"""
        try:
            return list(self.db.users.find({"group": group}))
        except Exception as e:
            print(f"❌ Failed to get group members for {group}: {e}")
            return []
    
    async def update_user_mute(self, user_id: int, mute_until: datetime) -> bool:
        """Update user mute status"""
        try:
            result = self.db.users.update_one(
                {"user_id": user_id},
                {"$set": {"muted_until": mute_until}}
            )
            return True
        except Exception as e:
            print(f"❌ Failed to update mute for user {user_id}: {e}")
            return False

    # Voice Channel Management
    async def add_voice_channel(self, channel_id: int, owner_id: int, channel_name: str) -> bool:
        """Add temporary voice channel to database"""
        try:
            voice_data = {
                "channel_id": channel_id,
                "owner_id": owner_id,
                "channel_name": channel_name,
                "created_at": datetime.utcnow(),
                "is_locked": False,
                "allowed_users": [],
                "banned_users": []
            }
            
            result = self.db.voice_channels.insert_one(voice_data)
            return result.inserted_id is not None
        except Exception as e:
            print(f"❌ Failed to add voice channel {channel_id}: {e}")
            return False
    
    async def get_voice_channel(self, channel_id: int) -> Optional[Dict]:
        """Get voice channel data"""
        try:
            return self.db.voice_channels.find_one({"channel_id": channel_id})
        except Exception as e:
            print(f"❌ Failed to get voice channel {channel_id}: {e}")
            return None
    
    async def remove_voice_channel(self, channel_id: int) -> bool:
        """Remove voice channel from database"""
        try:
            result = self.db.voice_channels.delete_one({"channel_id": channel_id})
            return result.deleted_count > 0
        except Exception as e:
            print(f"❌ Failed to remove voice channel {channel_id}: {e}")
            return False
    
    async def update_voice_channel(self, channel_id: int, update_data: Dict) -> bool:
        """Update voice channel data"""
        try:
            result = self.db.voice_channels.update_one(
                {"channel_id": channel_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"❌ Failed to update voice channel {channel_id}: {e}")
            return False

    # Applications Management
    async def add_application(self, user_id: int, username: str, group: str, full_name: str) -> bool:
        """Add group application"""
        try:
            # Check if user already has pending application
            existing = self.db.applications.find_one({
                "user_id": user_id,
                "status": "pending"
            })
            
            if existing:
                return False
            
            app_data = {
                "user_id": user_id,
                "username": username,
                "group": group,
                "full_name": full_name,
                "status": "pending",
                "applied_at": datetime.utcnow(),
                "reviewed_at": None,
                "reviewed_by": None
            }
            
            result = self.db.applications.insert_one(app_data)
            return result.inserted_id is not None
        except Exception as e:
            print(f"❌ Failed to add application for user {user_id}: {e}")
            return False
    
    async def get_pending_applications(self, group: str = None) -> List[Dict]:
        """Get pending applications"""
        try:
            query = {"status": "pending"}
            if group:
                query["group"] = group
            return list(self.db.applications.find(query))
        except Exception as e:
            print(f"❌ Failed to get pending applications: {e}")
            return []
    
    async def update_application_status(self, user_id: int, group: str, status: str, reviewed_by: int) -> bool:
        """Update application status"""
        try:
            result = self.db.applications.update_one(
                {"user_id": user_id, "group": group, "status": "pending"},
                {"$set": {
                    "status": status,
                    "reviewed_at": datetime.utcnow(),
                    "reviewed_by": reviewed_by
                }}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"❌ Failed to update application status: {e}")
            return False

    # Moderation
    async def add_warning(self, user_id: int, reason: str, moderator_id: int) -> bool:
        """Add warning to user"""
        try:
            # Add to warnings collection
            warning_data = {
                "user_id": user_id,
                "reason": reason,
                "moderator_id": moderator_id,
                "timestamp": datetime.utcnow()
            }
            self.db.warnings.insert_one(warning_data)
            
            # Increment warning count in users collection
            self.db.users.update_one(
                {"user_id": user_id},
                {"$inc": {"warnings": 1}}
            )
            return True
        except Exception as e:
            print(f"❌ Failed to add warning for user {user_id}: {e}")
            return False
    
    async def get_user_warnings(self, user_id: int) -> List[Dict]:
        """Get all warnings for user"""
        try:
            return list(self.db.warnings.find({"user_id": user_id}).sort("timestamp", -1))
        except Exception as e:
            print(f"❌ Failed to get warnings for user {user_id}: {e}")
            return []

    # Logging
    async def log_action(self, action: str, user_id: int, moderator_id: int = None, details: Dict = None) -> bool:
        """Log moderation action"""
        try:
            log_data = {
                "action": action,
                "user_id": user_id,
                "moderator_id": moderator_id,
                "details": details or {},
                "timestamp": datetime.utcnow()
            }
            
            result = self.db.logs.insert_one(log_data)
            return result.inserted_id is not None
        except Exception as e:
            print(f"❌ Failed to log action: {e}")
            return False

# Global database instance
db = Database()