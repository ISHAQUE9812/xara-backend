from datetime import datetime
from typing import Optional

def get_screen_model(
    screen_id: str,
    screen_name: str,
    location: str,
    resolution: Optional[str] = "1920x1080",
    device_uuid: Optional[str] = None,
    preview_image: Optional[str] = None
) -> dict:
    return {
        "screen_id": screen_id,
        "screen_name": screen_name,
        "name": screen_name,
        "location": location,
        "status": "offline",
        "mode": "single", # 'single' or 'multi'
        "playlist_limit": 5,
        "playlist": [],
        "current_media_index": 0,
        "rotation_interval": 10,
        "audience": 0,
        "engagement": 0,
        "last_seen": datetime.utcnow(),
        "resolution": resolution,
        "uuid": device_uuid,
        "device_uuid": device_uuid,
        "preview_image": preview_image
    }
