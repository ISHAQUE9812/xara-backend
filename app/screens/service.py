from datetime import datetime
from typing import Any, List, Optional
from fastapi import HTTPException
from app.screens.repository import ScreenRepository, ScreenAdMappingRepository
from app.ads.repository import AdRepository
from app.screens.model import get_screen_model
from app.screens.schema import ScreenAssignMediaRequest
from app.websocket.manager import manager

class ScreenService:
    @staticmethod
    async def create_screen(
        name_or_data: Any,
        location: Optional[str] = None,
        resolution: str = "1920x1080",
        device_uuid: Optional[str] = None,
        preview_image: Optional[str] = None,
        mode: str = "single",
        playlist_limit: int = 5,
        rotation_interval: int = 10,
        status: str = "offline",
        audience: int = 0,
        engagement: int = 0,
    ) -> dict:
        import uuid as py_uuid

        if hasattr(name_or_data, "screen_name") and not isinstance(name_or_data, str):
            name = name_or_data.screen_name
            location = getattr(name_or_data, "location", location)
            mode = getattr(name_or_data, "mode", mode)
            playlist_limit = getattr(name_or_data, "playlist_limit", playlist_limit)
            rotation_interval = getattr(name_or_data, "rotation_interval", rotation_interval)
            status = getattr(name_or_data, "status", status)
            audience = getattr(name_or_data, "audience", audience)
            engagement = getattr(name_or_data, "engagement", engagement)
            resolution = getattr(name_or_data, "resolution", resolution)
            device_uuid = getattr(name_or_data, "device_uuid", device_uuid)
            preview_image = getattr(name_or_data, "preview_image", preview_image)
        else:
            name = str(name_or_data)

        hardware_uuid = device_uuid or str(py_uuid.uuid4())
        screen_id = f"SCR-{py_uuid.uuid4().hex[:6].upper()}"

        screen_doc = get_screen_model(
            screen_id=screen_id,
            screen_name=name,
            location=location or "",
            resolution=resolution,
            device_uuid=hardware_uuid,
            preview_image=preview_image,
        )
        screen_doc["mode"] = mode
        screen_doc["status"] = status
        screen_doc["playlist_limit"] = max(1, int(playlist_limit))
        screen_doc["rotation_interval"] = max(1, int(rotation_interval))
        screen_doc["audience"] = int(audience)
        screen_doc["engagement"] = int(engagement)
        screen_doc["current_media_index"] = 0
        screen_doc["current_media_id"] = None
        screen_doc["playlist"] = []
        screen_doc["last_seen"] = datetime.utcnow()

        await ScreenRepository.insert(screen_doc)
        screen_doc.pop("_id", None)
        return screen_doc

    @staticmethod
    async def get_all_screens() -> List[dict]:
        screens = await ScreenRepository.get_all()

        for screen in screens:
            screen.pop("_id", None)

            if "screen_name" not in screen and "name" in screen:
                screen["screen_name"] = screen["name"]
            elif "name" not in screen and "screen_name" in screen:
                screen["name"] = screen["screen_name"]

            screen.setdefault("status", "offline")
            screen.setdefault("mode", "single")
            screen.setdefault("playlist_limit", 5)
            screen.setdefault("playlist", [])
            screen.setdefault("current_media_index", 0)
            screen.setdefault("rotation_interval", 10)
            screen.setdefault("audience", 0)
            screen.setdefault("engagement", 0)
            screen.setdefault("current_media_id", None)
            if "last_seen" not in screen:
                screen["last_seen"] = datetime.utcnow()

        return screens

    @staticmethod
    async def assign_media(data: ScreenAssignMediaRequest) -> dict:
        screen = await ScreenRepository.get_by_id(data.screen_id)

        if not screen:
            raise HTTPException(status_code=404, detail="Screen not found")

        playlist_limit = max(1, int(data.playlist_limit))
        rotation_interval = max(1, int(data.rotation_interval))
        if len(data.playlist) > playlist_limit:
            raise HTTPException(
                status_code=400,
                detail=f"Playlist exceeds the limit of {playlist_limit}",
            )

        mode = data.mode.lower().strip()
        if mode not in {"single", "multi"}:
            raise HTTPException(status_code=400, detail="Mode must be 'single' or 'multi'")

        playlist = list(data.playlist[:playlist_limit])
        if mode == "single":
            playlist = playlist[:1]

        current_media_id = playlist[0] if playlist else None
        update_data = {
            "mode": mode,
            "playlist_limit": playlist_limit,
            "rotation_interval": rotation_interval,
            "playlist": playlist,
            "current_media_index": 0,
            "current_media_id": current_media_id,
            "status": "online" if playlist else "offline",
            "last_seen": datetime.utcnow(),
        }

        await ScreenRepository.update(data.screen_id, update_data)

        # Also sync to screen_ad_mappings
        await ScreenAdMappingRepository.upsert_mapping(
            screen_id=data.screen_id,
            mapping_fields={
                "mode": mode,
                "ad_ids": playlist
            }
        )

        updated_screen = await ScreenRepository.get_by_id(data.screen_id)
        updated_screen.pop("_id", None)

        if "screen_name" not in updated_screen and "name" in updated_screen:
            updated_screen["screen_name"] = updated_screen["name"]

        await manager.broadcast_event({
            "event": "playback_changed",
            "screen_id": data.screen_id,
            "mode": mode,
            "playlist": playlist,
            "playlist_limit": playlist_limit,
            "rotation_interval": rotation_interval,
            "current_media_index": 0,
            "current_media_id": current_media_id,
            "timestamp": datetime.utcnow().isoformat(),
        })

        if playlist:
            ad = await AdRepository.get_by_id(current_media_id)
            if ad:
                await manager.send_to_screen(data.screen_id, {
                    "event": "media_changed",
                    "screen_id": data.screen_id,
                    "media_id": ad["ad_id"],
                    "title": ad["title"],
                    "url": ad["file_url"],
                    "type": ad["type"],
                    "duration": ad["duration"],
                    "current_media_index": 0,
                    "timestamp": datetime.utcnow().isoformat(),
                })

        return updated_screen

    @staticmethod
    async def update_metrics(screen_id: str, audience: Optional[int] = None, engagement: Optional[int] = None) -> dict:
        screen = await ScreenRepository.get_by_id(screen_id)
        if not screen:
            raise HTTPException(status_code=404, detail="Screen not found")

        update_data = {}
        if audience is not None:
            update_data["audience"] = int(audience)
        if engagement is not None:
            update_data["engagement"] = int(engagement)

        if not update_data:
            return {
                "screen_id": screen_id,
                "audience": screen.get("audience", 0),
                "engagement": screen.get("engagement", 0),
            }

        await ScreenRepository.update(screen_id, update_data)
        updated_screen = await ScreenRepository.get_by_id(screen_id)
        updated_screen.pop("_id", None)

        if audience is not None:
            await manager.broadcast_event({
                "event": "audience_updated",
                "screen_id": screen_id,
                "audience": updated_screen["audience"],
                "timestamp": datetime.utcnow().isoformat(),
            })

        if engagement is not None:
            await manager.broadcast_event({
                "event": "engagement_updated",
                "screen_id": screen_id,
                "engagement": updated_screen["engagement"],
                "timestamp": datetime.utcnow().isoformat(),
            })

        return updated_screen

    @staticmethod
    async def get_current_media(screen_id: str) -> dict:
        screen = await ScreenRepository.get_by_id(screen_id)

        if not screen:
            raise HTTPException(status_code=404, detail="Screen not found")

        response = {
            "screen_id": screen_id,
            "mode": screen.get("mode", "single"),
            "current_media": None,
        }

        playlist = screen.get("playlist", [])
        if not playlist:
            return response

        index = screen.get("current_media_index", 0)
        if index >= len(playlist):
            index = 0

        current_media_id = playlist[index]
        ad = await AdRepository.get_by_id(current_media_id)

        if ad:
            response["current_media"] = {
                "media_id": ad["ad_id"],
                "title": ad["title"],
                "url": ad["file_url"],
                "type": ad["type"],
            }

        return response
