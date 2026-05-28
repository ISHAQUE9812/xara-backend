from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ScreenBase(BaseModel):
    screen_id: str = Field(..., description="Unique alphanumeric identifier for the screen, e.g. SCREEN_001")
    name: str = Field(..., description="Friendly name of the screen, e.g. Mall Entrance Screen")
    location: str = Field(..., description="Physical location of the screen, e.g. Dubai Mall")
    resolution: str = Field("1920x1080", description="Display resolution of the screen")
    preview_image: Optional[str] = Field(None, description="URL to the screen's preview frame")


class ScreenRegister(BaseModel):
    screen_id: str = Field(..., description="Device assigned screen_id")
    name: str = Field(..., description="Descriptive screen name")
    location: str = Field(..., description="Device location")
    resolution: str = Field("1920x1080", description="Default screen resolution")
    uuid: Optional[str] = Field(None, description="Optional unique UUID, generated if not provided")


class ScreenCreate(ScreenBase):
    uuid: Optional[str] = Field(None, description="Optional device unique UUID")


class ScreenUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Updated friendly name")
    location: Optional[str] = Field(None, description="Updated physical location")
    status: Optional[str] = Field(None, description="Operational status: online, offline, syncing, playing")
    resolution: Optional[str] = Field(None, description="Updated resolution")
    health: Optional[str] = Field(None, description="Hardware health status")
    preview_image: Optional[str] = Field(None, description="Updated preview image URL")
    current_campaign: Optional[str] = Field(None, description="Currently playing campaign ID")


class ScreenResponse(ScreenBase):
    id: str = Field(..., description="MongoDB ObjectID representation as string")
    uuid: str = Field(..., description="Cryptographically unique hardware UUID")
    status: str = Field(..., description="Current operational state")
    health: str = Field("good", description="Hardware health assessment")
    current_campaign: Optional[str] = Field(None, description="Currently active campaign ID")
    assigned_campaigns: List[str] = Field(default_factory=list, description="List of all campaigns assigned to this screen")
    websocket_connected: bool = Field(False, description="Real-time WebSocket connection state")
    last_seen: datetime = Field(..., description="ISO timestamp of the last heartbeat or connection")
    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Last document modification timestamp")

    class Config:
        from_attributes = True


class ScreenStatusUpdate(BaseModel):
    status: str = Field(..., description="Status string: online, offline, syncing, playing")
