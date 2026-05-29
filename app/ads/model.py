from datetime import datetime
from typing import Optional

def get_ad_model(
    ad_id: str,
    user_id: str,
    ad_type: str,
    file_url: str,
    title: str,
    duration: int = 10,
    campaign_id: Optional[str] = None,
    status: str = "active"
) -> dict:
    return {
        "ad_id": ad_id,
        "media_id": ad_id, # compatibility alias
        "user_id": user_id,
        "uploaded_by": user_id, # compatibility alias
        "campaign_id": campaign_id,
        "type": ad_type,
        "file_url": file_url,
        "url": file_url, # compatibility alias
        "title": title,
        "duration": duration,
        "status": status,
        "created_at": datetime.utcnow()
    }

