from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from bson import ObjectId
from app.database.db import get_db
from app.schemas.campaign_schema import (
    CampaignResponse, CampaignCreate, CampaignUpdate
)
from app.services.campaign_service import CampaignService
from app.auth.role_middleware import require_authenticated_user
from app.websocket.manager import manager
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_campaign_service(db=Depends(get_db)) -> CampaignService:
    return CampaignService(db)

@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    campaign: CampaignCreate,
    current_user: dict = Depends(require_authenticated_user),
    service: CampaignService = Depends(get_campaign_service)
):
    campaign_data = campaign.dict()
    # Enforce created_by = current_user for standard users
    if current_user.get("role") != "admin":
        campaign_data["created_by"] = current_user["id"]
    elif not campaign_data.get("created_by"):
        campaign_data["created_by"] = current_user["id"]

    created_campaign = await service.create_campaign(campaign_data)
    
    # Broadcast realtime event
    await manager.broadcast_event({
        "event": "campaign_created",
        "campaign": created_campaign
    })
    
    return created_campaign

@router.get("", response_model=List[CampaignResponse])
@router.get("/", response_model=List[CampaignResponse])
async def get_campaigns(
    current_user: dict = Depends(require_authenticated_user),
    service: CampaignService = Depends(get_campaign_service)
):
    all_campaigns = await service.get_all_campaigns()
    # Filter by own campaigns if not admin
    if current_user.get("role") != "admin":
        user_id = current_user["id"]
        return [c for c in all_campaigns if c.get("created_by") == user_id]
    return all_campaigns

@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    current_user: dict = Depends(require_authenticated_user),
    service: CampaignService = Depends(get_campaign_service)
):
    campaign = await service.get_campaign_by_id(campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found"
        )
    
    # RBAC: user can only view their own campaign
    if current_user.get("role") != "admin" and campaign.get("created_by") != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this campaign"
        )
    return campaign

@router.put("/{campaign_id}", response_model=CampaignResponse)
@router.patch("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: str,
    update: CampaignUpdate,
    current_user: dict = Depends(require_authenticated_user),
    service: CampaignService = Depends(get_campaign_service)
):
    campaign = await service.get_campaign_by_id(campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found"
        )
        
    # RBAC: user can only update their own campaign
    if current_user.get("role") != "admin" and campaign.get("created_by") != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this campaign"
        )
        
    update_data = update.dict(exclude_unset=True)
    updated = await service.update_campaign(campaign_id, update_data)
    
    # Broadcast realtime event
    await manager.broadcast_event({
        "event": "campaign_updated",
        "campaign": updated
    })
    
    return updated

@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    current_user: dict = Depends(require_authenticated_user),
    service: CampaignService = Depends(get_campaign_service)
):
    campaign = await service.get_campaign_by_id(campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found"
        )
        
    # RBAC: user can only delete their own campaign
    if current_user.get("role") != "admin" and campaign.get("created_by") != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this campaign"
        )
        
    success = await service.delete_campaign(campaign_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete campaign"
        )
        
    # Broadcast realtime event
    await manager.broadcast_event({
        "event": "campaign_deleted",
        "campaign_id": campaign_id
    })
    
    return {"detail": "Campaign deleted successfully"}
