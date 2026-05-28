from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime
from app.core.database import get_db
from app.schemas.screen_schema import (
    ScreenResponse, ScreenRegister, ScreenUpdate, ScreenStatusUpdate
)
from app.services.screen_service import ScreenService
from app.utils.deps import get_current_user
from app.websocket.manager import manager
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


async def get_screen_service(db=Depends(get_db)) -> ScreenService:
    return ScreenService(db)


@router.post("/register", response_model=ScreenResponse, status_code=status.HTTP_201_CREATED, tags=["Screen Management"])
async def register_screen(
    screen: ScreenRegister,
    service: ScreenService = Depends(get_screen_service)
):
    """
    Register a new smart screen device or update an existing registration.
    Enforces idempotency by screen_id and generates unique hardware UUID if omitted.
    """
    screen_data = screen.dict()
    registered_screen = await service.register_screen(screen_data)
    
    # Broadcast registration event
    await manager.broadcast_event({
        "event": "screen_registered",
        "screen_id": screen.screen_id,
        "screen": registered_screen
    })
    
    return registered_screen


@router.get("", response_model=List[ScreenResponse], tags=["Screen Management"])
@router.get("/", response_model=List[ScreenResponse], tags=["Screen Management"])
async def get_all_screens(
    service: ScreenService = Depends(get_screen_service)
):
    """Retrieve all registered smart screen devices in the operating system."""
    return await service.get_all_screens()


@router.get("/online", response_model=List[ScreenResponse], tags=["Screen Management"])
async def get_online_screens(
    service: ScreenService = Depends(get_screen_service)
):
    """Retrieve all smart screen devices currently online and connected."""
    return await service.get_online_screens()


@router.get("/{screen_id}", response_model=ScreenResponse, tags=["Screen Management"])
async def get_screen(
    screen_id: str,
    service: ScreenService = Depends(get_screen_service)
):
    """Retrieve details for a single smart screen device by screen_id."""
    screen = await service.get_screen_by_id(screen_id)
    if not screen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Screen '{screen_id}' not found"
        )
    return screen


@router.patch("/{screen_id}", response_model=ScreenResponse, tags=["Screen Management"])
async def update_screen(
    screen_id: str,
    update: ScreenUpdate,
    service: ScreenService = Depends(get_screen_service)
):
    """Update configuration or properties of a screen device."""
    update_data = update.dict(exclude_unset=True)
    screen = await service.update_screen(screen_id, update_data)
    
    if not screen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Screen '{screen_id}' not found"
        )
    
    # Broadcast config update event
    await manager.broadcast_event({
        "event": "screen_updated",
        "screen_id": screen_id,
        "screen": screen
    })
    
    return screen


@router.patch("/{screen_id}/status", response_model=ScreenResponse, tags=["Screen Management"])
async def update_screen_status(
    screen_id: str,
    status_update: ScreenStatusUpdate,
    service: ScreenService = Depends(get_screen_service)
):
    """
    Update the operational state of a screen device (online, offline, syncing, playing).
    Broadcasts the status transition to all dashboards instantly.
    """
    screen = await service.update_screen_status(screen_id, status_update.status)
    
    if not screen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Screen '{screen_id}' not found or invalid status transition requested"
        )
    
    # Broadcast operational status update via Websocket Manager
    await manager.send_status_update(screen_id, status_update.status)
    
    return screen


@router.delete("/{screen_id}", tags=["Screen Management"])
async def delete_screen(
    screen_id: str,
    service: ScreenService = Depends(get_screen_service),
    current_user: str = Depends(get_current_user)
):
    """Delete a screen registration record. Restricted to authenticated users."""
    success = await service.delete_screen(screen_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Screen '{screen_id}' not found"
        )
    
    # Broadcast deletion event
    await manager.broadcast_event({
        "event": "screen_deleted",
        "screen_id": screen_id
    })
    
    return {"detail": f"Screen '{screen_id}' deleted successfully"}
