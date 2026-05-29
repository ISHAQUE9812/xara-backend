from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class CampaignCreate(BaseModel):
    campaign_name: str
    ad_ids: List[str]

class CampaignUpdate(BaseModel):
    campaign_name: Optional[str] = None
    ad_ids: Optional[List[str]] = None

class CampaignResponse(BaseModel):
    campaign_id: str
    user_id: str
    campaign_name: str
    ad_ids: List[str]
    created_at: datetime
