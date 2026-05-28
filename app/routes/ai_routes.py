from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_db
from app.schemas.campaign_schema import AIMetadataCreate, AIMetadataResponse
from app.services.ai_service import AIService
from app.services.playback_service import PlaybackService
from app.websocket.manager import manager
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_ai_service(db=Depends(get_db)) -> AIService:
    return AIService(db)

async def get_playback_service(db=Depends(get_db)) -> PlaybackService:
    return PlaybackService(db)

@router.post("/metadata", response_model=AIMetadataResponse, tags=["AI"])
async def record_metadata(
    metadata: AIMetadataCreate,
    service: AIService = Depends(get_ai_service),
    playback_service: PlaybackService = Depends(get_playback_service)
):
    """
    Record AI metadata from screen sensors.
    
    Includes: emotion, audience count, engagement score, detected objects.
    """
    metadata_data = metadata.dict()
    result = await service.record_metadata(metadata_data)
    
    # Trigger AI decision engine to select best campaign
    recommended_campaign = await service.decide_campaign(
        metadata.screen_id,
        metadata_data
    )
    
    # If a good campaign match found, trigger playback
    if recommended_campaign:
        await manager.send_campaign_play(
            metadata.screen_id,
            recommended_campaign
        )
    
    return result

@router.get("/screen/{screen_id}/metadata", response_model=list, tags=["AI"])
async def get_screen_metadata(
    screen_id: str,
    limit: int = 100,
    service: AIService = Depends(get_ai_service)
):
    """Get recent metadata for a screen."""
    metadata = await service.get_screen_metadata(screen_id, limit)
    return metadata

@router.get("/screen/{screen_id}/latest", response_model=AIMetadataResponse, tags=["AI"])
async def get_latest_metadata(
    screen_id: str,
    service: AIService = Depends(get_ai_service)
):
    """Get the latest metadata for a screen."""
    metadata = await service.get_latest_metadata(screen_id)
    
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No metadata found for screen {screen_id}"
        )
    
    return metadata

@router.post("/decide/{screen_id}", tags=["AI"])
async def decide_campaign(
    screen_id: str,
    service: AIService = Depends(get_ai_service)
):
    """
    AI Decision Engine - Decide which campaign to play based on latest metadata.
    
    Decision factors:
    - emotion
    - age_group
    - engagement_score
    - audience_count
    - screen location
    - targeting criteria
    """
    latest_metadata = await service.get_latest_metadata(screen_id)
    
    if not latest_metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No metadata found for screen {screen_id}"
        )
    
    recommended_campaign = await service.decide_campaign(
        screen_id,
        latest_metadata
    )
    
    if not recommended_campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No matching campaign found for screen {screen_id}"
        )
    
    return {
        "screen_id": screen_id,
        "recommended_campaign": recommended_campaign,
        "based_on_metadata": latest_metadata
    }

@router.get("/screen/{screen_id}/audience-insights", tags=["AI"])
async def get_audience_insights(
    screen_id: str,
    hours: int = 24,
    service: AIService = Depends(get_ai_service)
):
    """Get audience insights for a screen."""
    insights = await service.get_audience_insights(screen_id, hours)
    return {"screen_id": screen_id, "insights": insights}

@router.get("/screen/{screen_id}/emotion-distribution", tags=["AI"])
async def get_emotion_distribution(
    screen_id: str,
    hours: int = 24,
    service: AIService = Depends(get_ai_service)
):
    """Get emotion distribution for a screen."""
    emotion_dist = await service.get_emotion_distribution(screen_id, hours)
    return {"screen_id": screen_id, "emotion_distribution": emotion_dist}

@router.get("/screen/{screen_id}/age-distribution", tags=["AI"])
async def get_age_distribution(
    screen_id: str,
    hours: int = 24,
    service: AIService = Depends(get_ai_service)
):
    """Get age group distribution for a screen."""
    age_dist = await service.get_age_distribution(screen_id, hours)
    return {"screen_id": screen_id, "age_distribution": age_dist}
