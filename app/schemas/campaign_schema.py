from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============ TARGETING SCHEMAS ============

class TargetingInfo(BaseModel):
    emotion: Optional[str] = Field(None, description="Target emotional state, e.g. happy")
    age_group: Optional[str] = Field(None, description="Target age demographic, e.g. 18-25")
    location: Optional[str] = Field(None, description="Target screen location, e.g. Dubai Mall")
    time_slot: Optional[str] = Field(None, description="Target hour window, e.g. Morning")


# ============ CAMPAIGN SCHEMAS ============

class CampaignBase(BaseModel):
    campaign_name: str = Field(..., description="Unique user-friendly name for the campaign")
    video_url: str = Field(..., description="Outbound video file url, can be absolute or relative path")
    video_filename: Optional[str] = Field(None, description="Extracted video filename")
    description: Optional[str] = Field(None, description="Optional brief description of campaign content")
    objective: Optional[str] = Field(None, description="Signage campaign business objective")
    priority: int = Field(1, ge=1, le=5, description="Priority rating from 1 (lowest) to 5 (highest)")
    budget: float = Field(0.0, ge=0.0, description="Campaign budget allocation")
    duration: int = Field(30, ge=0, description="Media playback duration in seconds")
    assigned_screens: List[str] = Field(default_factory=list, description="List of screen IDs or hardware UUIDs assigned to this campaign")
    targeting: Optional[TargetingInfo] = Field(default_factory=TargetingInfo, description="AI demographic and scheduling targets")
    status: str = Field("draft", description="State: draft, pending, approved, live, completed")
    start_date: Optional[datetime] = Field(None, description="Starting calendar date for campaign delivery")
    end_date: Optional[datetime] = Field(None, description="Ending calendar date for campaign delivery")
    start_time: Optional[str] = Field(None, description="Daily start time for playback, e.g. 08:00")
    end_time: Optional[str] = Field(None, description="Daily stop time for playback, e.g. 22:00")


class CampaignCreate(CampaignBase):
    created_by: Optional[str] = Field(None, description="ID of the advertiser who created the campaign")


class CampaignUpdate(BaseModel):
    campaign_name: Optional[str] = None
    video_url: Optional[str] = None
    description: Optional[str] = None
    objective: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    budget: Optional[float] = Field(None, ge=0.0)
    duration: Optional[int] = Field(None, ge=0)
    assigned_screens: Optional[List[str]] = None
    targeting: Optional[TargetingInfo] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None


class CampaignResponse(CampaignBase):
    id: str = Field(..., description="Represented databaseObjectID string")
    created_at: datetime
    updated_at: datetime
    play_count: int = 0
    impressions: int = 0
    created_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ============ ANALYTICS SCHEMAS ============

class AnalyticsCreate(BaseModel):
    screen_id: str
    campaign_id: Optional[str] = None
    play_count: int = 0
    impressions: int = 0
    engagement_score: float = 0.0
    audience_count: int = 0
    duration_watched: int = 0


class AnalyticsResponse(BaseModel):
    id: str
    screen_id: str
    campaign_id: Optional[str] = None
    play_count: int
    impressions: int
    engagement_score: float
    audience_count: int
    duration_watched: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


# ============ AI METADATA SCHEMAS ============

class AIMetadataCreate(BaseModel):
    device_id: str
    screen_id: Optional[str] = None
    emotion: Optional[str] = None
    age_group: Optional[str] = None
    audience_count: int = 0
    engagement_score: float = 0.0
    detected_objects: List[str] = Field(default_factory=list)


class AIMetadataResponse(BaseModel):
    id: str
    device_id: str
    screen_id: str
    emotion: Optional[str] = None
    age_group: Optional[str] = None
    audience_count: int
    engagement_score: float
    detected_objects: List[str]
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


# ============ PLAYBACK SCHEMAS ============

class PlaybackResponse(BaseModel):
    video: str
    campaign: str
    campaign_id: Optional[str] = None
    duration: int
    start_time: datetime
    status: str


class CurrentCampaignResponse(BaseModel):
    video: str
    campaign_name: str
    campaign_id: str
    duration: int
    assigned_screens: List[str]
    status: str
