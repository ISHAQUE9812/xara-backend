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
        import logging
        logger = logging.getLogger(__name__)
        coll = cls._get_collection()
        result = await coll.update_one(
            {"screen_id": screen_id},
            {"$set": update_fields}
        )
        matched = getattr(result, "matched_count", 0)
        modified = getattr(result, "modified_count", 0)
        logger.info(f"ScreenRepository.update screen_id: '{screen_id}', fields: {update_fields}, matched: {matched}, modified: {modified}")
        return matched > 0

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
        import logging
        logger = logging.getLogger(__name__)
        coll = cls._get_collection()
        result = await coll.update_one(
            {"screen_id": screen_id},
            {"$set": mapping_fields},
            upsert=True
        )
        matched = getattr(result, "matched_count", 0)
        modified = getattr(result, "modified_count", 0)
        upserted_id = getattr(result, "upserted_id", None)
        logger.info(f"ScreenAdMappingRepository.upsert_mapping screen_id: '{screen_id}', fields: {mapping_fields}, upserted_id: '{upserted_id}', matched: {matched}, modified: {modified}")

    @classmethod
    async def get_mapping_by_screen_id(cls, screen_id: str) -> Optional[Dict[str, Any]]:
        coll = cls._get_collection()
        return await coll.find_one({"screen_id": screen_id})

    @classmethod
    async def delete_mapping(cls, screen_id: str) -> bool:
        coll = cls._get_collection()
        result = await coll.delete_one({"screen_id": screen_id})
        return result.deleted_count > 0
