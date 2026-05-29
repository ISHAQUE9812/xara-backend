from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AdResponse(BaseModel):
    ad_id: str
    media_id: Optional[str] = None
    user_id: str
    uploaded_by: Optional[str] = None
    campaign_id: Optional[str] = None
    type: str
    file_url: str
    url: Optional[str] = None
    title: str
    duration: int
    status: str
    created_at: datetime

