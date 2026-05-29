import asyncio
from datetime import datetime
import logging
from app.screens.repository import ScreenRepository, ScreenAdMappingRepository
from app.ads.repository import AdRepository
from app.websocket.manager import manager

logger = logging.getLogger(__name__)

class PlaybackEngine:
    def __init__(self):
        self.is_running = False
        self.last_rotations = {} # screen_id -> datetime
        self.task = None

    async def start(self):
        self.is_running = True
        self.task = asyncio.create_task(self.run())
        logger.info("Playback Engine started.")

    async def stop(self):
        self.is_running = False
        if self.task:
            self.task.cancel()
        logger.info("Playback Engine stopped.")

    async def run(self):
        while self.is_running:
            try:
                await self._process_screens()
            except Exception as e:
                logger.error(f"Error in PlaybackEngine: {e}")
            
            await asyncio.sleep(1) # Run every second

    async def _process_screens(self):
        now = datetime.utcnow()
        
        # Only process screens that are online
        screens = await ScreenRepository.get_all()
        for screen in screens:
            if screen.get("status") != "online":
                continue
                
            screen_id = screen["screen_id"]
            
            # Fetch active screen ad mapping
            mapping = await ScreenAdMappingRepository.get_mapping_by_screen_id(screen_id)
            if not mapping or not mapping.get("ad_ids"):
                continue
                
            mode = mapping.get("mode", "single")
            if mode != "multi":
                # Single mode doesn't rotate!
                continue
                
            ad_ids = mapping["ad_ids"]
            interval = screen.get("rotation_interval", 10)
            
            # Check if it's time to rotate
            last_rotation = self.last_rotations.get(screen_id)
            if not last_rotation or (now - last_rotation).total_seconds() >= interval:
                await self._rotate_ad(screen, ad_ids)
                self.last_rotations[screen_id] = now
                 
    async def _rotate_ad(self, screen, ad_ids):
        screen_id = screen["screen_id"]
        
        # Advance index
        current_index = screen.get("current_media_index", 0)
        next_index = (current_index + 1) % len(ad_ids)
        
        # Update screens state in MongoDB
        await ScreenRepository.update(
            screen_id=screen_id,
            update_fields={"current_media_index": next_index, "current_media_id": ad_ids[next_index]}
        )
        
        # Fetch next advertisement details from ads collection
        next_ad_id = ad_ids[next_index]
        ad = await AdRepository.get_by_id(next_ad_id)
        
        if ad:
            # Broadcast update event to all connected listeners (e.g. admin panels)
            await manager.broadcast_event({
                "event": "playback_changed",
                "screen_id": screen_id,
                "current_media_index": next_index,
                "current_media_id": next_ad_id
            })
            
            # Send immediate change to the specific physical screen
            await manager.send_to_screen(screen_id, {
                "event": "media_changed",
                "screen_id": screen_id,
                "media_id": ad["ad_id"],
                "url": ad["file_url"],
                "type": ad["type"]
            })
            logger.info(f"Screen {screen_id} rotated to ad {next_ad_id}")

playback_engine = PlaybackEngine()
