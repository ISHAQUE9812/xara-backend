from typing import List, Optional, Dict, Any
from app.database.db import get_db

class ScreenRepository:
    @staticmethod
    def _get_collection():
        return get_db()["screens"]

    @classmethod
    async def insert(cls, doc: Dict[str, Any]) -> Dict[str, Any]:
        coll = cls._get_collection()
        await coll.insert_one(doc)
        return doc

    @classmethod
    async def get_by_id(cls, screen_id: str) -> Optional[Dict[str, Any]]:
        coll = cls._get_collection()
        return await coll.find_one({"screen_id": screen_id})

    @classmethod
    async def get_by_uuid(cls, uuid: str) -> Optional[Dict[str, Any]]:
        coll = cls._get_collection()
        return await coll.find_one({"uuid": uuid})

    @classmethod
    async def get_all(cls) -> List[Dict[str, Any]]:
        coll = cls._get_collection()
        cursor = coll.find({}).sort("created_at", -1)
        return await cursor.to_list(length=1000)

    @classmethod
    async def update(cls, screen_id: str, update_fields: Dict[str, Any]) -> bool:
        coll = cls._get_collection()
        result = await coll.update_one(
            {"screen_id": screen_id},
            {"$set": update_fields}
        )
        return result.matched_count > 0

    @classmethod
    async def delete(cls, screen_id: str) -> bool:
        coll = cls._get_collection()
        result = await coll.delete_one({"screen_id": screen_id})
        return result.deleted_count > 0


class ScreenAdMappingRepository:
    @staticmethod
    def _get_collection():
        return get_db()["screen_ad_mappings"]

    @classmethod
    async def upsert_mapping(cls, screen_id: str, mapping_fields: Dict[str, Any]) -> None:
        coll = cls._get_collection()
        await coll.update_one(
            {"screen_id": screen_id},
            {"$set": mapping_fields},
            upsert=True
        )

    @classmethod
    async def get_mapping_by_screen_id(cls, screen_id: str) -> Optional[Dict[str, Any]]:
        coll = cls._get_collection()
        return await coll.find_one({"screen_id": screen_id})

    @classmethod
    async def delete_mapping(cls, screen_id: str) -> bool:
        coll = cls._get_collection()
        result = await coll.delete_one({"screen_id": screen_id})
        return result.deleted_count > 0
