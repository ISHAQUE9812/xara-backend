import os
import aiofiles
import uuid
from typing import List, Optional
from fastapi import UploadFile
from app.ads.repository import AdRepository
from app.ads.model import get_ad_model

# Ensure media directory exists
MEDIA_DIR = "media"
os.makedirs(MEDIA_DIR, exist_ok=True)

def ensure_compat_fields(ad: Optional[dict]) -> Optional[dict]:
    if ad:
        ad.pop("_id", None)
        if "media_id" not in ad and "ad_id" in ad:
            ad["media_id"] = ad["ad_id"]
        if "uploaded_by" not in ad and "user_id" in ad:
            ad["uploaded_by"] = ad["user_id"]
        if "url" not in ad and "file_url" in ad:
            ad["url"] = ad["file_url"]
    return ad

class AdService:
    @staticmethod
    async def save_ad(file: UploadFile, title: str, ad_type: str, user_id: str, duration: int = 10, campaign_id: Optional[str] = None) -> dict:
        ad_id = f"AD-{uuid.uuid4().hex[:8].upper()}"
        ext = file.filename.split('.')[-1] if '.' in file.filename else 'bin'
        filename = f"{ad_id}.{ext}"
        filepath = os.path.join(MEDIA_DIR, filename)
        file_url = f"/media/{filename}"
        
        async with aiofiles.open(filepath, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
            
        ad_doc = get_ad_model(
            ad_id=ad_id,
            user_id=user_id,
            ad_type=ad_type,
            file_url=file_url,
            title=title,
            duration=duration,
            campaign_id=campaign_id
        )
        
        await AdRepository.insert(ad_doc)
        return ensure_compat_fields(ad_doc)

    @staticmethod
    async def get_ad_by_id(ad_id: str) -> Optional[dict]:
        ad = await AdRepository.get_by_id(ad_id)
        return ensure_compat_fields(ad)

    @staticmethod
    async def get_all_ads() -> List[dict]:
        ads = await AdRepository.get_all()
        return [ensure_compat_fields(ad) for ad in ads if ad]

    @staticmethod
    async def get_user_ads(user_id: str) -> List[dict]:
        ads = await AdRepository.get_by_user_id(user_id)
        return [ensure_compat_fields(ad) for ad in ads if ad]

    @staticmethod
    async def delete_ad(ad_id: str) -> bool:
        ad = await AdRepository.get_by_id(ad_id)
        if ad:
            file_url = ad.get("file_url", "")
            if file_url.startswith("/media/"):
                filename = file_url.split('/')[-1]
                filepath = os.path.join(MEDIA_DIR, filename)
                try:
                    if os.path.exists(filepath):
                        os.remove(filepath)
                except Exception:
                    pass
        return await AdRepository.delete(ad_id)
