from typing import List, Dict, Any, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.models.screen_model import ScreenModel
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


class ScreenService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["screens"]

    async def register_screen(self, screen_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Idempotently register a smart screen device.
        If the screen_id already exists, update its connection metadata and configurations.
        Otherwise, create a new screen record with a unique hardware UUID.
        """
        screen_id = screen_data.get("screen_id")
        existing_screen = await self.collection.find_one({"screen_id": screen_id})

        if existing_screen:
            # Idempotent update: refresh registration info and update timestamp
            update_fields = {
                "name": screen_data.get("name") or existing_screen.get("name"),
                "location": screen_data.get("location") or existing_screen.get("location"),
                "resolution": screen_data.get("resolution") or existing_screen.get("resolution"),
                "updated_at": datetime.utcnow(),
                "last_seen": datetime.utcnow()
            }
            # Preserve existing UUID or set if missing
            if "uuid" in screen_data and screen_data["uuid"]:
                update_fields["uuid"] = screen_data["uuid"]

            await self.collection.update_one(
                {"screen_id": screen_id},
                {"$set": update_fields}
            )
            updated = await self.collection.find_one({"screen_id": screen_id})
            logger.info(f"Screen registration updated for existing screen_id: {screen_id}")
            return ScreenModel.format_response(updated)
        
        # New screen creation flow
        document = ScreenModel.create_document(screen_data)
        result = await self.collection.insert_one(document)
        created = await self.collection.find_one({"_id": result.inserted_id})
        logger.info(f"New screen successfully registered: {screen_id} with UUID: {created.get('uuid')}")
        return ScreenModel.format_response(created)

    async def get_screen_by_id(self, screen_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve screen information by custom screen_id."""
        screen = await self.collection.find_one({"screen_id": screen_id})
        return ScreenModel.format_response(screen) if screen else None

    async def get_screen_by_uuid(self, uuid: str) -> Optional[Dict[str, Any]]:
        """Retrieve screen information by unique UUID."""
        screen = await self.collection.find_one({"uuid": uuid})
        return ScreenModel.format_response(screen) if screen else None

    async def get_all_screens(self) -> List[Dict[str, Any]]:
        """Retrieve a list of all registered smart screens."""
        screens = await self.collection.find().to_list(None)
        return [ScreenModel.format_response(screen) for screen in screens]

    async def update_screen(self, screen_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update any subset of screen properties by screen_id."""
        update_data["updated_at"] = datetime.utcnow()
        
        # Avoid overriding structural constants if updated via this method
        if "screen_id" in update_data:
            del update_data["screen_id"]
        if "uuid" in update_data:
            del update_data["uuid"]
            
        result = await self.collection.update_one(
            {"screen_id": screen_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            logger.warning(f"Failed to update screen: {screen_id} - screen not found")
            return None
            
        updated = await self.collection.find_one({"screen_id": screen_id})
        logger.info(f"Screen details updated successfully for screen_id: {screen_id}")
        return ScreenModel.format_response(updated)

    async def update_screen_status(self, screen_id: str, status: str) -> Optional[Dict[str, Any]]:
        """
        Update screen operational state (online, offline, syncing, playing) 
        and refresh the last seen timestamp.
        """
        valid_statuses = {"online", "offline", "syncing", "playing"}
        if status not in valid_statuses:
            logger.warning(f"Invalid status transition attempted: '{status}' for screen: {screen_id}")
            return None
            
        return await self.update_screen(screen_id, {
            "status": status,
            "last_seen": datetime.utcnow()
        })

    async def update_current_campaign(self, screen_id: str, campaign_id: str) -> Optional[Dict[str, Any]]:
        """Update the currently playing campaign on a smart screen."""
        return await self.update_screen(screen_id, {
            "current_campaign": campaign_id
        })

    async def assign_campaigns(self, screen_id: str, campaign_ids: List[str]) -> Optional[Dict[str, Any]]:
        """Set the active campaign assignments for a smart screen."""
        return await self.update_screen(screen_id, {
            "assigned_campaigns": campaign_ids
        })

    async def update_websocket_status(self, screen_id: str, connected: bool) -> Optional[Dict[str, Any]]:
        """Update WebSocket connection state and sync online status."""
        status = "online" if connected else "offline"
        return await self.update_screen(screen_id, {
            "websocket_connected": connected,
            "status": status,
            "last_seen": datetime.utcnow()
        })

    async def delete_screen(self, screen_id: str) -> bool:
        """Delete a screen registration record by screen_id."""
        result = await self.collection.delete_one({"screen_id": screen_id})
        success = result.deleted_count > 0
        if success:
            logger.info(f"Screen successfully deleted: {screen_id}")
        else:
            logger.warning(f"Screen deletion failed: {screen_id} not found")
        return success

    async def get_online_screens(self) -> List[Dict[str, Any]]:
        """Retrieve all currently active/online smart screens."""
        screens = await self.collection.find({"status": "online"}).to_list(None)
        return [ScreenModel.format_response(screen) for screen in screens]

    async def get_screens_by_location(self, location: str) -> List[Dict[str, Any]]:
        """Filter screens by a specific physical location."""
        screens = await self.collection.find({"location": location}).to_list(None)
        return [ScreenModel.format_response(screen) for screen in screens]
