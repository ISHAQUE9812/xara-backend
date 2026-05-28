from typing import Optional, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.services.campaign_service import CampaignService
from app.services.screen_service import ScreenService
import logging

logger = logging.getLogger(__name__)


class PlaybackService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.screen_service = ScreenService(db)
        self.campaign_service = CampaignService(db)
        self.playback_collection = db["playback_history"]

    async def get_current_campaign_for_screen(self, screen_id: str) -> Optional[Dict[str, Any]]:
        """Get the current campaign for a screen."""
        screen = await self.screen_service.get_screen_by_id(screen_id)
        if not screen:
            return None

        # Try current_campaign field first
        current_campaign_id = screen.get("current_campaign")
        if current_campaign_id:
            campaign = await self.campaign_service.get_campaign_by_id(current_campaign_id)
            if campaign:
                return campaign

        # Fall back to first assigned playable campaign
        campaign = await self.campaign_service.get_current_campaign_for_screen(screen_id)
        if campaign:
            return campaign

        # Last resort: check by screen uuid
        screen_uuid = screen.get("uuid")
        if screen_uuid:
            campaign = await self.campaign_service.get_current_campaign_for_screen(screen_uuid)
            if campaign:
                return campaign

        return None

    async def start_playback(self, screen_id: str, campaign_id: str) -> Dict[str, Any]:
        """Record playback start."""
        playback = {
            "screen_id": screen_id,
            "campaign_id": campaign_id,
            "start_time": datetime.utcnow(),
            "status": "playing"
        }
        result = await self.playback_collection.insert_one(playback)
        playback["id"] = str(result.inserted_id)
        return playback

    async def end_playback(self, screen_id: str, campaign_id: str, playback_id: str = None, duration_watched: int = 0):
        """Record playback end and update analytics."""
        if playback_id:
            from bson import ObjectId
            try:
                await self.playback_collection.update_one(
                    {"_id": ObjectId(playback_id)},
                    {
                        "$set": {
                            "end_time": datetime.utcnow(),
                            "status": "ended",
                            "duration_watched": duration_watched
                        }
                    }
                )
            except Exception:
                pass

        # Increment play count
        await self.campaign_service.increment_play_count(campaign_id)

    async def switch_campaign(self, screen_id: str, campaign_id: str) -> Optional[Dict[str, Any]]:
        """Switch campaign on screen."""
        await self.screen_service.update_current_campaign(screen_id, campaign_id)
        return await self.get_current_campaign_for_screen(screen_id)

    async def trigger_playback(self, screen_id: str) -> Optional[Dict[str, Any]]:
        """Trigger playback for a screen."""
        campaign = await self.get_current_campaign_for_screen(screen_id)
        if not campaign:
            return None

        video_url = campaign.get("video_url", "")
        media_url = campaign.get("media_url", video_url)

        return {
            "screen_id": screen_id,
            "video": campaign.get("video_filename") or video_url,
            "media_url": media_url,
            "campaign": campaign.get("campaign_name"),
            "campaign_id": campaign.get("id"),
            "duration": campaign.get("duration"),
            "status": "ready_to_play",
            "triggered_at": datetime.utcnow()
        }

    async def get_playback_history(self, screen_id: str, limit: int = 100) -> list:
        """Get playback history for a screen."""
        playbacks = await self.playback_collection.find(
            {"screen_id": screen_id}
        ).sort("start_time", -1).limit(limit).to_list(None)
        return playbacks

    async def cache_video_locally(self, screen_id: str, campaign_id: str, video_path: str) -> Dict[str, Any]:
        """Record local cache for offline support."""
        cache_info = {
            "screen_id": screen_id,
            "campaign_id": campaign_id,
            "video_path": video_path,
            "cached_at": datetime.utcnow(),
            "status": "cached"
        }
        result = await self.db["local_cache"].insert_one(cache_info)
        cache_info["id"] = str(result.inserted_id)
        return cache_info

    async def get_cached_videos(self, screen_id: str) -> list:
        """Get cached videos for offline playback."""
        cached = await self.db["local_cache"].find(
            {"screen_id": screen_id, "status": "cached"}
        ).to_list(None)
        return cached
