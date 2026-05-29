import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.campaign_model import AIMetadataModel
from app.websocket.manager import manager

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["ai_metadata"]
        self.campaign_collection = db["campaigns"]

    async def record_metadata(self, metadata_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record AI metadata from screen sensors."""
        document = AIMetadataModel.create_document(metadata_data)
        result = await self.collection.insert_one(document)

        metadata = await self.collection.find_one({"_id": result.inserted_id})
        formatted = AIMetadataModel.format_response(metadata)

        screen_id = formatted.get("screen_id")
        audience_count = formatted.get("audience_count")
        engagement_score = formatted.get("engagement_score")

        if screen_id:
            update_fields = {}
            if audience_count is not None:
                update_fields["audience"] = int(audience_count)
            if engagement_score is not None:
                update_fields["engagement"] = int(engagement_score)

            if update_fields:
                await self.db["screens"].update_one({"screen_id": screen_id}, {"$set": update_fields})
                if "audience" in update_fields:
                    await manager.broadcast_event({
                        "event": "audience_updated",
                        "screen_id": screen_id,
                        "audience": int(audience_count),
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                if "engagement" in update_fields:
                    await manager.broadcast_event({
                        "event": "engagement_updated",
                        "screen_id": screen_id,
                        "engagement": int(engagement_score),
                        "timestamp": datetime.utcnow().isoformat(),
                    })

        return formatted

    async def get_screen_metadata(self, screen_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent metadata for a screen."""
        metadata = await self.collection.find(
            {"screen_id": screen_id}
        ).sort("timestamp", -1).limit(limit).to_list(None)
        
        return [AIMetadataModel.format_response(m) for m in metadata]

    async def get_latest_metadata(self, screen_id: str) -> Optional[Dict[str, Any]]:
        """Get the latest metadata for a screen."""
        metadata = await self.collection.find_one(
            {"screen_id": screen_id},
            sort=[("timestamp", -1)]
        )
        return AIMetadataModel.format_response(metadata) if metadata else None

    async def decide_campaign(self, screen_id: str, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        AI Decision Engine - Decide which campaign to play based on metadata.
        
        Decision factors:
        - emotion
        - age_group
        - engagement_score
        - audience_count
        - screen location
        - targeting criteria
        """
        emotion = metadata.get("emotion")
        age_group = metadata.get("age_group")
        engagement_score = metadata.get("engagement_score", 0)

        # Find campaigns matching the targeting criteria
        pipeline = [
            {
                "$match": {
                    "assigned_screens": screen_id,
                    "status": "active",
                    "$or": [
                        {"targeting.emotion": emotion},
                        {"targeting.age_group": age_group},
                        {"targeting": None}
                    ]
                }
            },
            {
                "$addFields": {
                    "match_score": {
                        "$sum": [
                            {"$cond": [{"$eq": ["$targeting.emotion", emotion]}, 50, 0]},
                            {"$cond": [{"$eq": ["$targeting.age_group", age_group]}, 30, 0]},
                            {"$cond": [{"$gte": [engagement_score, 75]}, 20, 0]}
                        ]
                    }
                }
            },
            {"$sort": {"match_score": -1}},
            {"$limit": 1}
        ]
        
        result = await self.campaign_collection.aggregate(pipeline).to_list(1)
        
        if result:
            campaign = result[0]
            campaign["id"] = str(campaign["_id"])
            return campaign
        
        return None

    async def get_audience_insights(self, screen_id: str, hours: int = 24) -> Dict[str, Any]:
        """Get audience insights for a screen."""
        from datetime import timedelta
        
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
                    "_id": None,
                    "avg_audience_count": {"$avg": "$audience_count"},
                    "avg_engagement": {"$avg": "$engagement_score"},
                    "peak_emotion": {"$max": "$emotion"},
                    "dominant_age_group": {"$max": "$age_group"},
                    "total_records": {"$sum": 1}
                }
            }
        ]
        
        result = await self.collection.aggregate(pipeline).to_list(1)
        
        if result:
            return result[0]
        
        return {
            "screen_id": screen_id,
            "avg_audience_count": 0,
            "avg_engagement": 0,
            "peak_emotion": None,
            "dominant_age_group": None,
            "total_records": 0
        }

    async def get_emotion_distribution(self, screen_id: str, hours: int = 24) -> Dict[str, int]:
        """Get emotion distribution for a screen."""
        from datetime import timedelta
        
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        pipeline = [
            {
                "$match": {
                    "screen_id": screen_id,
                    "emotion": {"$exists": True, "$ne": None},
                    "timestamp": {"$gte": start_time}
                }
            },
            {
                "$group": {
                    "_id": "$emotion",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        result = await self.collection.aggregate(pipeline).to_list(None)
        
        emotion_dist = {}
        for item in result:
            emotion_dist[item["_id"]] = item["count"]
        
        return emotion_dist

    async def get_age_distribution(self, screen_id: str, hours: int = 24) -> Dict[str, int]:
        """Get age group distribution for a screen."""
        from datetime import timedelta
        
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        pipeline = [
            {
                "$match": {
                    "screen_id": screen_id,
                    "age_group": {"$exists": True, "$ne": None},
                    "timestamp": {"$gte": start_time}
                }
            },
            {
                "$group": {
                    "_id": "$age_group",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        result = await self.collection.aggregate(pipeline).to_list(None)
        
        age_dist = {}
        for item in result:
            age_dist[item["_id"]] = item["count"]
        
        return age_dist
