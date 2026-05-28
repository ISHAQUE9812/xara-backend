from typing import List, Dict, Any, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.models.campaign_model import CampaignModel
import logging

logger = logging.getLogger(__name__)


class CampaignService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["campaigns"]

    # Statuses that count as "playable" on a screen
    PLAYABLE_STATUSES = ["draft", "live", "active", "approved", "pending"]

    async def create_campaign(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new campaign."""
        document = CampaignModel.create_document(campaign_data)
        result = await self.collection.insert_one(document)

        campaign = await self.collection.find_one({"_id": result.inserted_id})
        return CampaignModel.format_response(campaign)

    async def get_campaign_by_id(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """Get campaign by ID."""
        try:
            campaign = await self.collection.find_one({"_id": ObjectId(campaign_id)})
            return CampaignModel.format_response(campaign) if campaign else None
        except Exception:
            return None

    async def get_all_campaigns(self) -> List[Dict[str, Any]]:
        """Get all campaigns."""
        campaigns = await self.collection.find().to_list(None)
        return [CampaignModel.format_response(c) for c in campaigns]

    async def get_active_campaigns(self) -> List[Dict[str, Any]]:
        """Get all campaigns in a playable state."""
        campaigns = await self.collection.find(
            {"status": {"$in": self.PLAYABLE_STATUSES}}
        ).to_list(None)
        return [CampaignModel.format_response(c) for c in campaigns]

    async def get_campaigns_by_screen(self, screen_id: str) -> List[Dict[str, Any]]:
        """Get campaigns assigned to a specific screen."""
        campaigns = await self.collection.find({
            "assigned_screens": screen_id,
            "status": {"$in": self.PLAYABLE_STATUSES}
        }).to_list(None)
        return [CampaignModel.format_response(c) for c in campaigns]

    async def get_current_campaign_for_screen(self, screen_id: str) -> Optional[Dict[str, Any]]:
        """Get the current/active campaign for a screen (any playable status)."""
        campaign = await self.collection.find_one({
            "assigned_screens": screen_id,
            "status": {"$in": self.PLAYABLE_STATUSES}
        })
        if not campaign:
            # Fallback: get the most recently created campaign assigned to this screen
            campaign = await self.collection.find_one(
                {"assigned_screens": screen_id},
                sort=[("created_at", -1)]
            )
        return CampaignModel.format_response(campaign) if campaign else None

    async def update_campaign(self, campaign_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update campaign."""
        update_data["updated_at"] = datetime.utcnow()

        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(campaign_id)},
                {"$set": update_data}
            )

            if result.matched_count == 0:
                return None

            campaign = await self.collection.find_one({"_id": ObjectId(campaign_id)})
            return CampaignModel.format_response(campaign)
        except Exception as e:
            logger.error(f"Error updating campaign: {e}")
            return None

    async def assign_campaign_to_screens(self, campaign_id: str, screen_ids: List[str]) -> Optional[Dict[str, Any]]:
        """Assign campaign to multiple screens."""
        return await self.update_campaign(campaign_id, {
            "assigned_screens": screen_ids
        })

    async def increment_play_count(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """Increment campaign play count."""
        try:
            await self.collection.update_one(
                {"_id": ObjectId(campaign_id)},
                {"$inc": {"play_count": 1}, "$set": {"updated_at": datetime.utcnow()}}
            )
            campaign = await self.collection.find_one({"_id": ObjectId(campaign_id)})
            return CampaignModel.format_response(campaign)
        except Exception as e:
            logger.error(f"Error incrementing play count: {e}")
            return None

    async def increment_impressions(self, campaign_id: str, count: int = 1) -> Optional[Dict[str, Any]]:
        """Increment campaign impressions."""
        try:
            await self.collection.update_one(
                {"_id": ObjectId(campaign_id)},
                {"$inc": {"impressions": count}, "$set": {"updated_at": datetime.utcnow()}}
            )
            campaign = await self.collection.find_one({"_id": ObjectId(campaign_id)})
            return CampaignModel.format_response(campaign)
        except Exception as e:
            logger.error(f"Error incrementing impressions: {e}")
            return None

    async def delete_campaign(self, campaign_id: str) -> bool:
        """Delete a campaign."""
        try:
            result = await self.collection.delete_one({"_id": ObjectId(campaign_id)})
            return result.deleted_count > 0
        except Exception:
            return False

    async def archive_campaign(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """Archive a campaign (set status to archived)."""
        return await self.update_campaign(campaign_id, {
            "status": "archived"
        })
