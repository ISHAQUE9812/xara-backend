import os
import uuid as py_uuid
import aiofiles
from fastapi import APIRouter, Depends, Form, UploadFile, File, Request, HTTPException, status
from typing import List
from app.auth.role_middleware import require_admin, require_authenticated_user
from app.screens.schema import (
    ScreenCreate, ScreenResponse, ScreenAssignMediaRequest, CurrentMediaResponse,
    AssignAdRequest, AssignMultipleAdsRequest, UpdateScreenModeRequest
)
from app.screens.service import ScreenService
from app.screens.repository import ScreenRepository, ScreenAdMappingRepository
from app.ads.repository import AdRepository
from app.database.db import get_db
from app.websocket.manager import manager

router = APIRouter()

import logging
logger = logging.getLogger(__name__)

@router.post("", response_model=dict)
@router.post("/", response_model=dict)
@router.post("/create", response_model=dict)
async def create_screen(
    request: Request,
    current_user: dict = Depends(require_admin)
):
    content_type = request.headers.get("content-type", "")
    
    name = ""
    location = ""
    resolution = "1920x1080"
    device_uuid = None
    file_bytes = None
    filename = None
    
    if "multipart/form-data" in content_type:
        form = await request.form()
        name = form.get("name") or form.get("screen_name") or ""
        location = form.get("location") or ""
        resolution = form.get("resolution") or "1920x1080"
        device_uuid = form.get("device_uuid") or form.get("uuid")
        
        file_upload = form.get("file")
        if file_upload and hasattr(file_upload, "filename") and file_upload.filename:
            filename = file_upload.filename
            file_bytes = await file_upload.read()
    else:
        try:
            body = await request.json()
            name = body.get("name") or body.get("screen_name") or ""
            location = body.get("location") or ""
            resolution = body.get("resolution") or "1920x1080"
            device_uuid = body.get("device_uuid") or body.get("uuid")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON or Form payload")
            
    preview_image_url = None
    if file_bytes and filename:
        screens_dir = os.path.join("media", "screens")
        os.makedirs(screens_dir, exist_ok=True)
        ext = filename.split('.')[-1] if '.' in filename else 'jpg'
        unique_filename = f"SCR_IMG_{py_uuid.uuid4().hex[:8].upper()}.{ext}"
        filepath = os.path.join(screens_dir, unique_filename)
        preview_image_url = f"/media/screens/{unique_filename}"
        
        async with aiofiles.open(filepath, 'wb') as out_file:
            await out_file.write(file_bytes)
            
    screen = await ScreenService.create_screen(
        name_or_data=name,
        location=location,
        resolution=resolution,
        device_uuid=device_uuid,
        preview_image=preview_image_url
    )
    return screen

@router.get("", response_model=List[ScreenResponse])
@router.get("/", response_model=List[ScreenResponse])
async def get_screens(current_user: dict = Depends(require_authenticated_user)):
    screens = await ScreenService.get_all_screens()
    return screens

@router.get("/live", response_model=List[ScreenResponse])
async def get_live_monitoring(current_user: dict = Depends(require_admin)):
    screens = await ScreenRepository.get_all()
    from datetime import datetime
    live_screens = []
    for screen in screens:
        if screen.get("status") == "online":
            screen.pop("_id", None)
            screen["id"] = screen.get("screen_id")
            if "screen_name" not in screen and "name" in screen:
                screen["screen_name"] = screen["name"]
            elif "name" not in screen and "screen_name" in screen:
                screen["name"] = screen["screen_name"]
            screen.setdefault("status", "online")
            screen.setdefault("mode", "single")
            screen.setdefault("playlist_limit", 5)
            screen.setdefault("playlist", [])
            screen.setdefault("current_media_index", 0)
            screen.setdefault("rotation_interval", 10)
            screen.setdefault("audience", 0)
            screen.setdefault("engagement", 0)
            screen.setdefault("last_seen", datetime.utcnow())
            live_screens.append(screen)
    return live_screens

@router.get("/{screen_id}", response_model=ScreenResponse)
async def get_screen_by_id(
    screen_id: str,
    current_user: dict = Depends(require_authenticated_user)
):
    screen = await ScreenRepository.get_by_id(screen_id)
    if not screen:
        raise HTTPException(status_code=404, detail="Screen not found")
        
    screen.pop("_id", None)
    screen["id"] = screen.get("screen_id")
    if "screen_name" not in screen and "name" in screen:
        screen["screen_name"] = screen["name"]
    return screen

@router.put("/{screen_id}", response_model=dict)
async def update_screen(
    screen_id: str,
    request: Request,
    current_user: dict = Depends(require_admin)
):
    try:
        update_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
    update_data.pop("screen_id", None)
    update_data.pop("device_uuid", None)
    update_data.pop("uuid", None)
    update_data.pop("_id", None)
    
    success = await ScreenRepository.update(screen_id, update_data)
    if not success:
        raise HTTPException(status_code=404, detail="Screen not found")
        
    updated = await ScreenRepository.get_by_id(screen_id)
    updated.pop("_id", None)
    updated["id"] = updated.get("screen_id")
    
    if "screen_name" not in updated and "name" in updated:
        updated["screen_name"] = updated["name"]
        
    await manager.broadcast_event({
        "event": "screen_updated",
        "screen_id": screen_id,
        "screen": updated
    })
    
    return updated

@router.delete("/{screen_id}")
async def delete_screen(
    screen_id: str,
    current_user: dict = Depends(require_admin)
):
    success = await ScreenRepository.delete(screen_id)
    if not success:
        raise HTTPException(status_code=404, detail="Screen not found")
        
    # Also clean mapping
    await ScreenAdMappingRepository.delete_mapping(screen_id)
    
    await manager.broadcast_event({
        "event": "screen_deleted",
        "screen_id": screen_id
    })
    
    return {"detail": f"Screen {screen_id} deleted successfully"}

# ============ SCREEN-AD MAPPING ASSIGNMENT ENDPOINTS ============

@router.post("/assign-ad", response_model=dict)
async def assign_ad(
    data: AssignAdRequest,
    current_user: dict = Depends(require_admin)
):
    logger.info(f"Assign request received: Screen '{data.screen_id}' -> Ad '{data.ad_id}'")
    logger.info(f"User role: {current_user.get('role')}")
    
    screen = await ScreenRepository.get_by_id(data.screen_id)
    if not screen:
        logger.warning(f"Screen not found: {data.screen_id}")
        raise HTTPException(status_code=404, detail="Screen not found")
    logger.info(f"Screen found: {data.screen_id}")
        
    ad = await AdRepository.get_by_id(data.ad_id)
    if not ad:
        logger.warning(f"Advertisement not found: {data.ad_id}")
        raise HTTPException(status_code=404, detail="Advertisement not found")
    logger.info(f"Ad found: {data.ad_id}")
        
    # Upsert Mapping Collection
    await ScreenAdMappingRepository.upsert_mapping(
        screen_id=data.screen_id,
        mapping_fields={
            "mode": "single",
            "ad_ids": [data.ad_id],
            "current_ad_index": 0
        }
    )
    
    # Update Screen state
    await ScreenRepository.update(
        screen_id=data.screen_id,
        update_fields={
            "mode": "single",
            "playlist": [data.ad_id],
            "current_media_index": 0,
            "current_media_id": data.ad_id
        }
    )
    
    # Broadcast event playback_changed
    await manager.broadcast_event({
        "event": "playback_changed",
        "screen_id": data.screen_id,
        "mode": "single",
        "playlist": [data.ad_id]
    })
    
    # Broadcast event media_changed when assignment changes
    await manager.broadcast_event({
        "event": "media_changed",
        "screen_id": data.screen_id
    })
    
    # Push immediate media change over websocket
    await manager.send_to_screen(data.screen_id, {
        "event": "media_changed",
        "screen_id": data.screen_id,
        "media_id": ad["ad_id"],
        "url": ad["file_url"],
        "type": ad["type"]
    })
    
    return {"detail": f"Advertisement {data.ad_id} assigned successfully to screen {data.screen_id} in single mode"}

@router.post("/assign-multiple-ads", response_model=dict)
async def assign_multiple_ads(
    data: AssignMultipleAdsRequest,
    current_user: dict = Depends(require_admin)
):
    logger.info(f"Assign multiple ads request received: Screen '{data.screen_id}' -> Ads: {data.ad_ids}")
    logger.info(f"User role: {current_user.get('role')}")
    
    screen = await ScreenRepository.get_by_id(data.screen_id)
    if not screen:
        logger.warning(f"Screen not found: {data.screen_id}")
        raise HTTPException(status_code=404, detail="Screen not found")
    logger.info(f"Screen found: {data.screen_id}")
        
    # Verify all ads exist
    ads = []
    for ad_id in data.ad_ids:
        ad = await AdRepository.get_by_id(ad_id)
        if not ad:
            logger.warning(f"Advertisement not found: {ad_id}")
            raise HTTPException(status_code=404, detail=f"Advertisement {ad_id} not found")
        logger.info(f"Ad found: {ad_id}")
        ads.append(ad)
        
    # Upsert Mapping Collection
    await ScreenAdMappingRepository.upsert_mapping(
        screen_id=data.screen_id,
        mapping_fields={
            "mode": data.mode,
            "ad_ids": data.ad_ids,
            "current_ad_index": 0,
            "rotation_interval": 10
        }
    )
    
    # Update Screen state
    first_ad_id = data.ad_ids[0] if data.ad_ids else None
    await ScreenRepository.update(
        screen_id=data.screen_id,
        update_fields={
            "mode": data.mode,
            "playlist": data.ad_ids,
            "current_media_index": 0,
            "current_media_id": first_ad_id
        }
    )
    
    # Broadcast event playback_changed
    await manager.broadcast_event({
        "event": "playback_changed",
        "screen_id": data.screen_id,
        "mode": data.mode,
        "playlist": data.ad_ids
    })
    
    # Broadcast event media_changed when assignment changes
    await manager.broadcast_event({
        "event": "media_changed",
        "screen_id": data.screen_id
    })
    
    # Play the first ad in the list immediately
    if ads:
        first_ad = ads[0]
        await manager.send_to_screen(data.screen_id, {
            "event": "media_changed",
            "screen_id": data.screen_id,
            "media_id": first_ad["ad_id"],
            "url": first_ad["file_url"],
            "type": first_ad["type"]
        })
        
    return {"detail": f"{len(data.ad_ids)} advertisements assigned successfully to screen {data.screen_id} in {data.mode} mode"}

@router.put("/{screen_id}/mode", response_model=dict)
async def update_screen_mode(
    screen_id: str,
    data: UpdateScreenModeRequest,
    current_user: dict = Depends(require_admin)
):
    screen = await ScreenRepository.get_by_id(screen_id)
    if not screen:
        raise HTTPException(status_code=404, detail="Screen not found")
        
    # Update screens collection and mappings collection
    await ScreenRepository.update(
        screen_id=screen_id,
        update_fields={"mode": data.mode}
    )
    await ScreenAdMappingRepository.upsert_mapping(
        screen_id=screen_id,
        mapping_fields={"mode": data.mode}
    )
    
    # Fetch screen ad list from mapping to include in broadcast
    mapping = await ScreenAdMappingRepository.get_mapping_by_screen_id(screen_id)
    playlist = mapping["ad_ids"] if mapping else []
    
    # Broadcast event playback_changed
    await manager.broadcast_event({
        "event": "playback_changed",
        "screen_id": screen_id,
        "mode": data.mode,
        "playlist": playlist
    })
    
    return {"screen_id": screen_id, "mode": data.mode}

@router.get("/{screen_id}/current-media")
async def get_current_media(screen_id: str):
    screen = await ScreenRepository.get_by_id(screen_id)
    if not screen:
        raise HTTPException(status_code=404, detail="Screen not found")
        
    playlist = screen.get("playlist", [])
    if not playlist:
        return {
            "message": "No advertisement assigned",
            "current_media": None,
            "screen_id": screen_id,
            "mode": screen.get("mode", "single")
        }
        
    index = screen.get("current_media_index", 0)
    if index >= len(playlist):
        index = 0
        
    current_media_id = playlist[index]
    ad = await AdRepository.get_by_id(current_media_id)
    if not ad:
        return {
            "message": "No advertisement assigned",
            "current_media": None,
            "screen_id": screen_id,
            "mode": screen.get("mode", "single")
        }
        
    return {
        "screen_id": screen_id,
        "media_id": ad["ad_id"],
        "media_url": ad["file_url"],
        "url": ad["file_url"],
        "title": ad["title"],
        "type": ad["type"],
        "current_media": {
            "media_id": ad["ad_id"],
            "url": ad["file_url"],
            "media_url": ad["file_url"],
            "title": ad["title"],
            "type": ad["type"]
        },
        "mode": screen.get("mode", "single")
    }
