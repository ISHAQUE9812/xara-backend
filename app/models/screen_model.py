from datetime import datetime
from typing import Optional, Dict, Any
from uuid import uuid4


class ScreenModel:
    @staticmethod
    def create_document(screen_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format raw input screen dictionary for MongoDB insertion.
        Guarantees that all essential signage fields are present with correct defaults.
        """
        now = datetime.utcnow()
        return {
            "screen_id": screen_data.get("screen_id"),
            "uuid": screen_data.get("uuid") or str(uuid4()),
            "name": screen_data.get("name") or screen_data.get("location", "Unnamed Screen"),
            "location": screen_data.get("location", ""),
            "status": screen_data.get("status", "online"),
            "resolution": screen_data.get("resolution", "1920x1080"),
            "health": screen_data.get("health", "good"),
            "current_campaign": screen_data.get("current_campaign"),
            "assigned_campaigns": screen_data.get("assigned_campaigns", []),
            "preview_image": screen_data.get("preview_image"),
            "websocket_connected": screen_data.get("websocket_connected", False),
            "last_seen": screen_data.get("last_seen") or now,
            "created_at": now,
            "updated_at": now
        }

    @staticmethod
    def format_response(screen: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format a MongoDB document to conform to the API Pydantic response schema.
        Removes _id (ObjectId) and ensures all required fields have defaults.
        """
        if not screen:
            return {}
        screen["id"] = str(screen.pop("_id"))
        # Ensure default arrays/booleans exist for Pydantic
        if "assigned_campaigns" not in screen:
            screen["assigned_campaigns"] = []
        if "websocket_connected" not in screen:
            screen["websocket_connected"] = False
        if "health" not in screen:
            screen["health"] = "good"
        return screen
