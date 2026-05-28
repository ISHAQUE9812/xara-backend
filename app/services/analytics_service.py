from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.models.campaign_model import AnalyticsModel
import logging

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["analytics"]

    async def record_analytics(self, analytics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record analytics event."""
        document = AnalyticsModel.create_document(analytics_data)
        result = await self.collection.insert_one(document)
        
        analytics = await self.collection.find_one({"_id": result.inserted_id})
        return AnalyticsModel.format_response(analytics)

    async def get_screen_analytics(self, screen_id: str, days: int = 7) -> List[Dict[str, Any]]:
        """Get analytics for a screen in the last N days."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        analytics = await self.collection.find({
            "screen_id": screen_id,
            "timestamp": {"$gte": start_date}
        }).to_list(None)
        
        return [AnalyticsModel.format_response(a) for a in analytics]

    async def get_campaign_analytics(self, campaign_id: str, days: int = 7) -> List[Dict[str, Any]]:
        """Get analytics for a campaign in the last N days."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        analytics = await self.collection.find({
            "campaign_id": campaign_id,
            "timestamp": {"$gte": start_date}
        }).to_list(None)
        
        return [AnalyticsModel.format_response(a) for a in analytics]

    async def get_screen_performance(self, screen_id: str) -> Dict[str, Any]:
        """Get performance metrics for a screen."""
        pipeline = [
            {"$match": {"screen_id": screen_id}},
            {
                "$group": {
                    "_id": "$screen_id",
                    "total_impressions": {"$sum": "$impressions"},
                    "total_plays": {"$sum": "$play_count"},
                    "avg_engagement": {"$avg": "$engagement_score"},
                    "total_audience": {"$sum": "$audience_count"},
                    "avg_duration_watched": {"$avg": "$duration_watched"}
                }
            }
        ]
        
        result = await self.collection.aggregate(pipeline).to_list(1)
        if result:
            return result[0]
        
        return {
            "screen_id": screen_id,
            "total_impressions": 0,
            "total_plays": 0,
            "avg_engagement": 0,
            "total_audience": 0,
            "avg_duration_watched": 0
        }

    async def get_campaign_performance(self, campaign_id: str) -> Dict[str, Any]:
        """Get performance metrics for a campaign."""
        pipeline = [
            {"$match": {"campaign_id": campaign_id}},
            {
                "$group": {
                    "_id": "$campaign_id",
                    "total_impressions": {"$sum": "$impressions"},
                    "total_plays": {"$sum": "$play_count"},
                    "avg_engagement": {"$avg": "$engagement_score"},
                    "total_audience": {"$sum": "$audience_count"}
                }
            }
        ]
        
        result = await self.collection.aggregate(pipeline).to_list(1)
        if result:
            return result[0]
        
        return {
            "campaign_id": campaign_id,
            "total_impressions": 0,
            "total_plays": 0,
            "avg_engagement": 0,
            "total_audience": 0
        }

    async def get_top_campaigns(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top campaigns by engagement."""
        pipeline = [
            {
                "$group": {
                    "_id": "$campaign_id",
                    "total_impressions": {"$sum": "$impressions"},
                    "avg_engagement": {"$avg": "$engagement_score"},
                    "total_plays": {"$sum": "$play_count"}
                }
            },
            {"$sort": {"avg_engagement": -1}},
            {"$limit": limit}
        ]
        
        return await self.collection.aggregate(pipeline).to_list(None)

    async def get_top_screens(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top screens by engagement."""
        pipeline = [
            {
                "$group": {
                    "_id": "$screen_id",
                    "total_impressions": {"$sum": "$impressions"},
                    "avg_engagement": {"$avg": "$engagement_score"},
                    "total_audience": {"$sum": "$audience_count"}
                }
            },
            {"$sort": {"total_impressions": -1}},
            {"$limit": limit}
        ]
        
        return await self.collection.aggregate(pipeline).to_list(None)

    async def get_hourly_analytics(self, screen_id: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get hourly analytics for a screen."""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        pipeline = [
            {
                "$match": {
                    "screen_id": screen_id,
                    "timestamp": {"$gte": start_time}
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d %H:00",
                            "date": "$timestamp"
                        }
                    },
                    "impressions": {"$sum": "$impressions"},
                    "plays": {"$sum": "$play_count"},
                    "avg_engagement": {"$avg": "$engagement_score"}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        return await self.collection.aggregate(pipeline).to_list(None)

    async def sync_local_analytics(self, screen_id: str, local_analytics: List[Dict[str, Any]]) -> int:
        """Sync analytics recorded locally during offline mode."""
        count = 0
        for analytics in local_analytics:
            try:
                await self.record_analytics(analytics)
                count += 1
            except Exception as e:
                logger.error(f"Error syncing analytics: {e}")
        
        return count
