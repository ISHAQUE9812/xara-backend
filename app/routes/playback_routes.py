from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_db
from app.schemas.campaign_schema import CurrentCampaignResponse, PlaybackResponse
from app.services.playback_service import PlaybackService
from app.services.screen_service import ScreenService
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_playback_service(db=Depends(get_db)) -> PlaybackService:
    return PlaybackService(db)

async def get_screen_service(db=Depends(get_db)) -> ScreenService:
    return ScreenService(db)

@router.get("/{screen_id}/current-campaign", response_model=CurrentCampaignResponse, tags=["Playback"])
async def get_current_campaign(
    screen_id: str,
    service: PlaybackService = Depends(get_playback_service)
):
    """
    Get the current campaign for a screen.
    
    This is what the screen plays next.
    """
    campaign = await service.get_current_campaign_for_screen(screen_id)
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active campaign assigned to screen {screen_id}"
        )
    
    return {
        "video": campaign.get("video_filename") or campaign.get("video_url"),
        "campaign_name": campaign.get("campaign_name"),
        "campaign_id": campaign.get("id"),
        "duration": campaign.get("duration"),
        "assigned_screens": campaign.get("assigned_screens", []),
        "status": campaign.get("status")
    }

@router.get("/{screen_id}/trigger", response_model=PlaybackResponse, tags=["Playback"])
async def trigger_playback(
    screen_id: str,
    service: PlaybackService = Depends(get_playback_service)
):
    """
    Trigger playback for a screen.
    
    Returns campaign ready to play with all details.
    """
    playback = await service.trigger_playback(screen_id)
    
    if not playback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No campaign available for screen {screen_id}"
        )
    
    return {
        "video": playback.get("video"),
        "campaign": playback.get("campaign"),
        "duration": playback.get("duration"),
        "start_time": datetime.utcnow(),
        "status": "ready"
    }

@router.post("/{screen_id}/switch/{campaign_id}", tags=["Playback"])
async def switch_campaign(
    screen_id: str,
    campaign_id: str,
    service: PlaybackService = Depends(get_playback_service)
):
    """
    Switch campaign on a screen immediately.
    """
    campaign = await service.switch_campaign(screen_id, campaign_id)
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    return {
        "detail": f"Campaign switched on screen {screen_id}",
        "campaign": campaign
    }

@router.post("/{screen_id}/start-playback/{campaign_id}", tags=["Playback"])
async def start_playback(
    screen_id: str,
    campaign_id: str,
    service: PlaybackService = Depends(get_playback_service)
):
    """
    Record playback start.
    """
    playback = await service.start_playback(screen_id, campaign_id)
    return {"detail": "Playback started", "playback_id": playback.get("id")}

@router.post("/{screen_id}/end-playback/{campaign_id}", tags=["Playback"])
async def end_playback(
    screen_id: str,
    campaign_id: str,
    playback_id: str = None,
    duration_watched: int = 0,
    service: PlaybackService = Depends(get_playback_service)
):
    """
    Record playback end.
    """
    await service.end_playback(screen_id, campaign_id, playback_id, duration_watched)
    return {"detail": "Playback ended"}

@router.get("/{screen_id}/history", tags=["Playback"])
async def get_playback_history(
    screen_id: str,
    limit: int = 100,
    service: PlaybackService = Depends(get_playback_service)
):
    """
    Get playback history for a screen.
    """
    history = await service.get_playback_history(screen_id, limit)
    return {"screen_id": screen_id, "history": history}

@router.get("/{screen_id}/cached-videos", tags=["Playback"])
async def get_cached_videos(
    screen_id: str,
    service: PlaybackService = Depends(get_playback_service)
):
    """
    Get cached videos for offline playback.
    """
    cached = await service.get_cached_videos(screen_id)
    return {"screen_id": screen_id, "cached_videos": cached}
