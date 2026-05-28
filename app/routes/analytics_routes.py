from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.core.database import get_db
from app.schemas.campaign_schema import AnalyticsCreate, AnalyticsResponse
from app.services.analytics_service import AnalyticsService
from app.utils.deps import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_analytics_service(db=Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db)

@router.post("/", response_model=AnalyticsResponse, tags=["Analytics"])
async def record_analytics(
    analytics: AnalyticsCreate,
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Record analytics event."""
    analytics_data = analytics.dict()
    result = await service.record_analytics(analytics_data)
    return result

@router.get("/screen/{screen_id}", response_model=List[AnalyticsResponse], tags=["Analytics"])
async def get_screen_analytics(
    screen_id: str,
    days: int = 7,
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get analytics for a screen in the last N days."""
    analytics = await service.get_screen_analytics(screen_id, days)
    return analytics

@router.get("/campaign/{campaign_id}", response_model=List[AnalyticsResponse], tags=["Analytics"])
async def get_campaign_analytics(
    campaign_id: str,
    days: int = 7,
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get analytics for a campaign in the last N days."""
    analytics = await service.get_campaign_analytics(campaign_id, days)
    return analytics

@router.get("/screen/{screen_id}/performance", tags=["Analytics"])
async def get_screen_performance(
    screen_id: str,
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get performance metrics for a screen."""
    performance = await service.get_screen_performance(screen_id)
    return performance

@router.get("/campaign/{campaign_id}/performance", tags=["Analytics"])
async def get_campaign_performance(
    campaign_id: str,
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get performance metrics for a campaign."""
    performance = await service.get_campaign_performance(campaign_id)
    return performance

@router.get("/top-campaigns", tags=["Analytics"])
async def get_top_campaigns(
    limit: int = 10,
    service: AnalyticsService = Depends(get_analytics_service),
    current_user: str = Depends(get_current_user)
):
    """Get top campaigns by engagement."""
    campaigns = await service.get_top_campaigns(limit)
    return {"top_campaigns": campaigns}

@router.get("/top-screens", tags=["Analytics"])
async def get_top_screens(
    limit: int = 10,
    service: AnalyticsService = Depends(get_analytics_service),
    current_user: str = Depends(get_current_user)
):
    """Get top screens by engagement."""
    screens = await service.get_top_screens(limit)
    return {"top_screens": screens}

@router.get("/screen/{screen_id}/hourly", tags=["Analytics"])
async def get_hourly_analytics(
    screen_id: str,
    hours: int = 24,
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get hourly analytics for a screen."""
    analytics = await service.get_hourly_analytics(screen_id, hours)
    return {"screen_id": screen_id, "hourly_data": analytics}

@router.post("/sync-local", tags=["Analytics"])
async def sync_local_analytics(
    screen_id: str,
    local_analytics: List[AnalyticsCreate],
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Sync analytics recorded locally during offline mode."""
    count = await service.sync_local_analytics(
        screen_id,
        [a.dict() for a in local_analytics]
    )
    return {"detail": f"Synced {count} analytics records"}
