from fastapi import APIRouter, Depends, Form, UploadFile, File, HTTPException, status
from typing import List, Optional
from app.auth.role_middleware import require_authenticated_user, require_admin
from app.ads.schema import AdResponse
from app.ads.service import AdService

router = APIRouter()

@router.post("/upload", response_model=dict)
@router.post("", response_model=dict)
async def upload_ad(
    file: UploadFile = File(...),
    title: str = Form(...),
    type: str = Form(...),
    duration: Optional[int] = Form(10),
    campaign_id: Optional[str] = Form(None),
    current_user: dict = Depends(require_authenticated_user)
):
    ad_doc = await AdService.save_ad(
        file=file,
        title=title,
        ad_type=type,
        user_id=current_user["id"],
        duration=duration if duration is not None else 10,
        campaign_id=campaign_id
    )
    return {
        "message": "Advertisement uploaded successfully",
        "ad": ad_doc
    }

@router.get("", response_model=List[AdResponse])
@router.get("/", response_model=List[AdResponse])
async def get_all_ads(current_user: dict = Depends(require_authenticated_user)):
    # Standard users can see all shared ads in the platform or admins see all.
    # We allow standard users to see all shared media library ads.
    return await AdService.get_all_ads()

@router.get("/my-ads", response_model=List[AdResponse])
async def get_my_ads(current_user: dict = Depends(require_authenticated_user)):
    return await AdService.get_user_ads(current_user["id"])

@router.get("/{ad_id}", response_model=AdResponse)
async def get_ad_details(
    ad_id: str,
    current_user: dict = Depends(require_authenticated_user)
):
    ad = await AdService.get_ad_by_id(ad_id)
    if not ad:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Advertisement not found")
        
    # RBAC check: standard user can only view their own ad
    if current_user.get("role") != "admin" and ad["user_id"] != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this advertisement")
        
    return ad

@router.delete("/{ad_id}")
async def delete_ad(
    ad_id: str,
    current_user: dict = Depends(require_authenticated_user)
):
    ad = await AdService.get_ad_by_id(ad_id)
    if not ad:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Advertisement not found")
        
    # RBAC check: standard user can only delete their own ad
    if current_user.get("role") != "admin" and ad["user_id"] != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to delete this advertisement")
        
    success = await AdService.delete_ad(ad_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete advertisement")
        
    return {"detail": "Advertisement deleted successfully"}
