from typing import List, Optional, Dict, Any
from app.database.db import get_db

class AdRepository:
    @staticmethod
    def _get_collection():
        return get_db()["ads"]

    @classmethod
    async def insert(cls, ad_doc: Dict[str, Any]) -> Dict[str, Any]:
        coll = cls._get_collection()
        await coll.insert_one(ad_doc)
        return ad_doc

    @classmethod
    async def get_by_id(cls, ad_id: str) -> Optional[Dict[str, Any]]:
        coll = cls._get_collection()
        return await coll.find_one({"ad_id": ad_id})

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
    async def delete(cls, ad_id: str) -> bool:
        coll = cls._get_collection()
        result = await coll.delete_one({"ad_id": ad_id})
        return result.deleted_count > 0
