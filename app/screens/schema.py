from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ScreenCreate(BaseModel):
    screen_name: str
    location: str

class ScreenAssignMediaRequest(BaseModel):
    screen_id: str
    mode: str = Field(..., pattern="^(single|multi)$")
    playlist_limit: int
    rotation_interval: int
    playlist: List[str]

class ScreenResponse(BaseModel):
    screen_id: str
    screen_name: str
    location: str
    status: str
    mode: str
    playlist_limit: int
    playlist: List[str]
    current_media_index: int
    rotation_interval: int
    audience: int
    engagement: int
    last_seen: datetime
    resolution: Optional[str] = "1920x1080"
    device_uuid: Optional[str] = None
    preview_image: Optional[str] = None

class CurrentMediaData(BaseModel):
    media_id: str
    title: str
    url: str
    type: str

class CurrentMediaResponse(BaseModel):
    screen_id: str
    mode: str
    current_media: Optional[CurrentMediaData] = None

# ============ NEW SCREEN-AD MAPPING SCHEMAS ============

class AssignAdRequest(BaseModel):
    screen_id: str
    ad_id: str
    mode: str = "single"

class AssignMultipleAdsRequest(BaseModel):
    screen_id: str
    ad_ids: List[str]
    mode: str = "multi"

class UpdateScreenModeRequest(BaseModel):
    mode: str = Field(..., pattern="^(single|multi)$")
