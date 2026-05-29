import uuid
from typing import List, Optional
from app.campaigns.repository import CampaignRepository
from app.ads.repository import AdRepository
from app.campaigns.model import get_campaign_model
from app.campaigns.schema import CampaignCreate, CampaignUpdate

class CampaignService:
    @staticmethod
    async def create_campaign(data: CampaignCreate, user_id: str) -> dict:
        campaign_id = f"CMP-{uuid.uuid4().hex[:8].upper()}"
        doc = get_campaign_model(
            campaign_id=campaign_id,
            user_id=user_id,
            campaign_name=data.campaign_name,
            ad_ids=data.ad_ids
        )
        await CampaignRepository.insert(doc)
        
        # Optionally update ads collection with campaign_id for mapping
        if data.ad_ids:
            # We can update ads collection using a custom repository or direct update (repos can expose generic DB if needed, but since it's Ad collection, let's do it via get_db)
            from app.database.db import get_db
            db = get_db()
            await db["ads"].update_many(
                {"ad_id": {"$in": data.ad_ids}},
                {"$set": {"campaign_id": campaign_id}}
            )
            
        doc.pop("_id", None)
        return doc

    @staticmethod
    async def get_campaign_by_id(campaign_id: str) -> Optional[dict]:
        doc = await CampaignRepository.get_by_id(campaign_id)
        if doc:
            doc.pop("_id", None)
        return doc

    @staticmethod
    async def get_all_campaigns() -> List[dict]:
        campaigns = await CampaignRepository.get_all()
        for c in campaigns:
            c.pop("_id", None)
        return campaigns

    @staticmethod
    async def get_user_campaigns(user_id: str) -> List[dict]:
        campaigns = await CampaignRepository.get_by_user_id(user_id)
        for c in campaigns:
            c.pop("_id", None)
        return campaigns

    @staticmethod
    async def update_campaign(campaign_id: str, data: CampaignUpdate) -> Optional[dict]:
        update_fields = {}
        if data.campaign_name is not None:
            update_fields["campaign_name"] = data.campaign_name
        if data.ad_ids is not None:
            update_fields["ad_ids"] = data.ad_ids
            
        if not update_fields:
            return await CampaignService.get_campaign_by_id(campaign_id)
            
        await CampaignRepository.update(campaign_id, update_fields)
        
        if data.ad_ids is not None:
            from app.database.db import get_db
            db = get_db()
            # Sync campaign_id in ads collection
            await db["ads"].update_many(
                {"campaign_id": campaign_id},
                {"$set": {"campaign_id": None}}
            )
            if data.ad_ids:
                await db["ads"].update_many(
                    {"ad_id": {"$in": data.ad_ids}},
                    {"$set": {"campaign_id": campaign_id}}
                )
                
        return await CampaignService.get_campaign_by_id(campaign_id)

    @staticmethod
    async def delete_campaign(campaign_id: str) -> bool:
        from app.database.db import get_db
        db = get_db()
        # Clean campaign_id reference from ads
        await db["ads"].update_many(
            {"campaign_id": campaign_id},
            {"$set": {"campaign_id": None}}
        )
        return await CampaignRepository.delete(campaign_id)
