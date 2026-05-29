from typing import List, Optional, Dict, Any
from app.database.db import get_db

class CampaignRepository:
    @staticmethod
    def _get_collection():
        return get_db()["campaigns"]

    @classmethod
    async def insert(cls, doc: Dict[str, Any]) -> Dict[str, Any]:
        coll = cls._get_collection()
        await coll.insert_one(doc)
        return doc

    @classmethod
    async def get_by_id(cls, campaign_id: str) -> Optional[Dict[str, Any]]:
        coll = cls._get_collection()
        return await coll.find_one({"campaign_id": campaign_id})

    @classmethod
    async def get_all(cls) -> List[Dict[str, Any]]:
        coll = cls._get_collection()
        cursor = coll.find({}).sort("created_at", -1)
        return await cursor.to_list(length=1000)

    @classmethod
    async def get_by_user_id(cls, user_id: str) -> List[Dict[str, Any]]:
        coll = cls._get_collection()
        cursor = coll.find({"user_id": user_id}).sort("created_at", -1)
        return await cursor.to_list(length=1000)

    @classmethod
    async def update(cls, campaign_id: str, update_fields: Dict[str, Any]) -> bool:
        coll = cls._get_collection()
        result = await coll.update_one(
            {"campaign_id": campaign_id},
            {"$set": update_fields}
        )
        return result.matched_count > 0

    @classmethod
    async def delete(cls, campaign_id: str) -> bool:
        coll = cls._get_collection()
        result = await coll.delete_one({"campaign_id": campaign_id})
        return result.deleted_count > 0
