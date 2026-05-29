from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.auth.role_middleware import require_authenticated_user
from app.campaigns.schema import CampaignCreate, CampaignUpdate, CampaignResponse
from app.campaigns.service import CampaignService

router = APIRouter()

@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    campaign: CampaignCreate,
    current_user: dict = Depends(require_authenticated_user)
):
    return await CampaignService.create_campaign(campaign, current_user["id"])

@router.get("", response_model=List[CampaignResponse])
@router.get("/", response_model=List[CampaignResponse])
async def get_campaigns(current_user: dict = Depends(require_authenticated_user)):
    if current_user.get("role") == "admin":
        return await CampaignService.get_all_campaigns()
    return await CampaignService.get_user_campaigns(current_user["id"])

@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign_details(
    campaign_id: str,
    current_user: dict = Depends(require_authenticated_user)
):
    campaign = await CampaignService.get_campaign_by_id(campaign_id)
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
        
    if current_user.get("role") != "admin" and campaign["user_id"] != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this campaign")
        
    return campaign

@router.put("/{campaign_id}", response_model=CampaignResponse)
@router.patch("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: str,
    update: CampaignUpdate,
    current_user: dict = Depends(require_authenticated_user)
):
    campaign = await CampaignService.get_campaign_by_id(campaign_id)
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
        
    if current_user.get("role") != "admin" and campaign["user_id"] != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to update this campaign")
        
    updated = await CampaignService.update_campaign(campaign_id, update)
    return updated

@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    current_user: dict = Depends(require_authenticated_user)
):
    campaign = await CampaignService.get_campaign_by_id(campaign_id)
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
        
    if current_user.get("role") != "admin" and campaign["user_id"] != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to delete this campaign")
        
    success = await CampaignService.delete_campaign(campaign_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete campaign")
        
    return {"detail": "Campaign deleted successfully"}
