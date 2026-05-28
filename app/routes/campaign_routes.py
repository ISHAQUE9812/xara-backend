from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import List, Optional
from app.core.database import get_db
from app.schemas.campaign_schema import (
    CampaignResponse, CampaignCreate, CampaignUpdate
)
from app.services.campaign_service import CampaignService
from app.utils.deps import get_optional_current_user
from app.websocket.manager import manager
import os
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


async def get_campaign_service(db=Depends(get_db)) -> CampaignService:
    return CampaignService(db)

@router.post("", response_model=CampaignResponse, tags=["Campaign Management"])
@router.post("/", response_model=CampaignResponse, tags=["Campaign Management"])
@router.post("/assign", response_model=CampaignResponse, tags=["Campaign Management"])
async def create_campaign(
    campaign: CampaignCreate,
    service: CampaignService = Depends(get_campaign_service),
    db=Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """Create a new campaign and automatically sync and notify assigned screens."""
    campaign_data = campaign.dict()
    if current_user:
        campaign_data["created_by"] = current_user["id"]
    created_campaign = await service.create_campaign(campaign_data)
    
    # Broadcast campaign created event
    await manager.broadcast_event({
        "event": "campaign_created",
        "campaign": created_campaign
    })
    
    # Unify creation and realtime screen assignment
    assigned_screens = campaign_data.get("assigned_screens", [])
    if assigned_screens:
        campaign_id = created_campaign.get("id")
        for screen_id_or_uuid in assigned_screens:
            # Look up screen by screen_id or uuid to ensure robust matching
            screen = await db["screens"].find_one({
                "$or": [
                    {"screen_id": screen_id_or_uuid},
                    {"uuid": screen_id_or_uuid}
                ]
            })
            if screen:
                target_screen_id = screen.get("screen_id")
                # Add campaign to screen's active assigned list
                await db["screens"].update_one(
                    {"_id": screen["_id"]},
                    {"$addToSet": {"assigned_campaigns": campaign_id}}
                )
                # Dispatch realtime socket update to the screen
                await manager.send_campaign_update(target_screen_id, created_campaign)
                # Broadcast campaign assignment to dashboards
                await manager.broadcast_event({
                    "event": "campaign_assigned",
                    "campaign_id": campaign_id,
                    "screen_id": target_screen_id
                })
                logger.info(f"Automatically synced campaign {campaign_id} to screen {target_screen_id}")
            else:
                logger.warning(f"Screen registration not found for reference: {screen_id_or_uuid}")
                
    return created_campaign

@router.get("", response_model=List[CampaignResponse], tags=["Campaign Management"])
@router.get("/", response_model=List[CampaignResponse], tags=["Campaign Management"])
async def get_all_campaigns(
    service: CampaignService = Depends(get_campaign_service)
):
    """Get all campaigns."""
    campaigns = await service.get_all_campaigns()
    return campaigns

@router.get("/active", response_model=List[CampaignResponse], tags=["Campaign Management"])
async def get_active_campaigns(
    service: CampaignService = Depends(get_campaign_service)
):
    """Get all active campaigns."""
    campaigns = await service.get_active_campaigns()
    return campaigns

@router.get("/{campaign_id}", response_model=CampaignResponse, tags=["Campaign Management"])
async def get_campaign(
    campaign_id: str,
    service: CampaignService = Depends(get_campaign_service)
):
    """Get campaign by ID."""
    campaign = await service.get_campaign_by_id(campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found"
        )
    return campaign

@router.patch("/{campaign_id}", response_model=CampaignResponse, tags=["Campaign Management"])
async def update_campaign(
    campaign_id: str,
    update: CampaignUpdate,
    service: CampaignService = Depends(get_campaign_service),
    # TODO: Re-enable strict JWT auth once login system is implemented
    # current_user: str = Depends(get_current_user)
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """Update campaign."""
    update_data = update.dict(exclude_unset=True)
    campaign = await service.update_campaign(campaign_id, update_data)
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found"
        )
    
    # Broadcast campaign update event
    await manager.broadcast_event({
        "event": "campaign_updated",
        "campaign": campaign
    })
    
    return campaign

@router.post("/{campaign_id}/assign-screens", tags=["Campaign Management"])
async def assign_screens_to_campaign(
    campaign_id: str,
    screen_ids: List[str],
    service: CampaignService = Depends(get_campaign_service),
    # TODO: Re-enable strict JWT auth once login system is implemented
    # current_user: str = Depends(get_current_user)
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """Assign campaign to multiple screens."""
    campaign = await service.assign_campaign_to_screens(campaign_id, screen_ids)
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found"
        )
    
    # Broadcast campaign assignment event for each screen
    for screen_id in screen_ids:
        await manager.send_campaign_update(screen_id, campaign)
        await manager.broadcast_event({
            "event": "campaign_assigned",
            "campaign_id": campaign_id,
            "screen_id": screen_id
        })
    
    return {"detail": "Campaign assigned to screens", "campaign": campaign}

@router.post("/{campaign_id}/play", tags=["Campaign Management"])
async def trigger_campaign_play(
    campaign_id: str,
    screen_id: str,
    service: CampaignService = Depends(get_campaign_service)
):
    """Trigger campaign playback on a specific screen."""
    campaign = await service.get_campaign_by_id(campaign_id)
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found"
        )
    
    # Send campaign play event to screen
    await manager.send_campaign_play(screen_id, campaign)
    
    return {"detail": f"Campaign {campaign_id} triggered for playback on screen {screen_id}"}

@router.delete("/{campaign_id}", tags=["Campaign Management"])
async def delete_campaign(
    campaign_id: str,
    service: CampaignService = Depends(get_campaign_service),
    # TODO: Re-enable strict JWT auth once login system is implemented
    # current_user: str = Depends(get_current_user)
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """Delete a campaign."""
    success = await service.delete_campaign(campaign_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found"
        )
    
    # Broadcast campaign deletion event
    await manager.broadcast_event({
        "event": "campaign_deleted",
        "campaign_id": campaign_id
    })
    
    return {"detail": f"Campaign {campaign_id} deleted successfully"}

@router.post("/{campaign_id}/archive", tags=["Campaign Management"])
async def archive_campaign(
    campaign_id: str,
    service: CampaignService = Depends(get_campaign_service),
    # TODO: Re-enable strict JWT auth once login system is implemented
    # current_user: str = Depends(get_current_user)
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """Archive a campaign."""
    campaign = await service.archive_campaign(campaign_id)
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found"
        )
    
    return {"detail": f"Campaign {campaign_id} archived", "campaign": campaign}
