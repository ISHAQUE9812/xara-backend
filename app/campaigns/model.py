from datetime import datetime
from typing import List, Optional

def get_campaign_model(
    campaign_id: str,
    user_id: str,
    campaign_name: str,
    ad_ids: List[str]
) -> dict:
    return {
        "campaign_id": campaign_id,
        "user_id": user_id,
        "campaign_name": campaign_name,
        "ad_ids": ad_ids,
        "created_at": datetime.utcnow()
    }
