import json
import logging
from datetime import datetime
from typing import Any, Dict, List

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.screen_connections: Dict[int, str] = {}
        self._db = None

    def set_db(self, db):
        self._db = db

    async def connect(self, websocket: WebSocket, screen_id: str):
        await websocket.accept()

        self.active_connections.setdefault(screen_id, []).append(websocket)
        self.screen_connections[id(websocket)] = screen_id

        logger.info(f"Screen {screen_id} connected. Active connections: {len(self.active_connections[screen_id])}")

        if self._db is not None:
            try:
                await self._db["screens"].update_one(
                    {"screen_id": screen_id},
                    {"$set": {
                        "websocket_connected": True,
                        "status": "online",
                        "last_seen": datetime.utcnow(),
                    }},
                )
            except Exception as exc:
                logger.error(f"Failed to update screen status on connect: {exc}")

        await self.broadcast_event({
            "event": "screen_online",
            "screen_id": screen_id,
            "timestamp": datetime.utcnow().isoformat(),
        })

    async def disconnect(self, websocket: WebSocket):
        screen_id = self.screen_connections.pop(id(websocket), None)

        if not screen_id:
            return

        if screen_id in self.active_connections:
            connections = self.active_connections[screen_id]
            if websocket in connections:
                connections.remove(websocket)
                logger.info(f"Screen {screen_id} disconnected. Remaining: {len(connections)}")

                if not connections:
                    del self.active_connections[screen_id]

                    if self._db is not None:
                        try:
                            await self._db["screens"].update_one(
                                {"screen_id": screen_id},
                                {"$set": {
                                    "websocket_connected": False,
                                    "status": "offline",
                                    "last_seen": datetime.utcnow(),
                                }},
                            )
                        except Exception as exc:
                            logger.error(f"Failed to update screen status on disconnect: {exc}")

                    await self.broadcast_event({
                        "event": "screen_offline",
                        "screen_id": screen_id,
                        "timestamp": datetime.utcnow().isoformat(),
                    })

    async def broadcast(self, message: Dict[str, Any]):
        message_str = self._serialize_message(message)
        dead_connections = []

        for screen_id, connections in list(self.active_connections.items()):
            for connection in connections:
                try:
                    await connection.send_text(message_str)
                except Exception as exc:
                    logger.error(f"Error broadcasting to screen {screen_id}: {exc}")
                    dead_connections.append(connection)

        for connection in dead_connections:
            await self.disconnect(connection)

    async def send_to_screen(self, screen_id: str, message: Dict[str, Any]):
        if screen_id not in self.active_connections:
            logger.warning(f"Screen {screen_id} not connected via WebSocket")
            return

        message_str = self._serialize_message(message)
        dead_connections = []

        for connection in self.active_connections[screen_id]:
            try:
                await connection.send_text(message_str)
            except Exception as exc:
                logger.error(f"Error sending to screen {screen_id}: {exc}")
                dead_connections.append(connection)

        for connection in dead_connections:
            await self.disconnect(connection)

    async def update_screen_metrics(self, screen_id: str, audience: int = None, engagement: int = None):
        if self._db is None:
            return None

        update_fields = {}
        if audience is not None:
            update_fields["audience"] = audience
        if engagement is not None:
            update_fields["engagement"] = engagement

        if not update_fields:
            return None

        await self._db["screens"].update_one({"screen_id": screen_id}, {"$set": update_fields})

        if audience is not None:
            await self.broadcast_event({
                "event": "audience_updated",
                "screen_id": screen_id,
                "audience": audience,
                "timestamp": datetime.utcnow().isoformat(),
            })

        if engagement is not None:
            await self.broadcast_event({
                "event": "engagement_updated",
                "screen_id": screen_id,
                "engagement": engagement,
                "timestamp": datetime.utcnow().isoformat(),
            })

        return await self._db["screens"].find_one({"screen_id": screen_id})

    async def broadcast_event(self, event: Dict[str, Any]):
        event_message = {
            "type": "event",
            "data": event,
        }
        await self.broadcast(event_message)

    async def send_campaign_update(self, screen_id: str, campaign_data: Dict[str, Any]):
        message = {
            "event": "campaign_update",
            "screen_id": screen_id,
            "campaign": campaign_data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self.send_to_screen(screen_id, message)

    async def send_campaign_play(self, screen_id: str, campaign_data: Dict[str, Any]):
        message = {
            "event": "campaign_play",
            "screen_id": screen_id,
            "video": campaign_data.get("video_url"),
            "media_url": campaign_data.get("media_url"),
            "campaign_id": campaign_data.get("id"),
            "campaign_name": campaign_data.get("campaign_name"),
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self.send_to_screen(screen_id, message)

    async def send_status_update(self, screen_id: str, status: str):
        message = {
            "event": "screen_status_update",
            "screen_id": screen_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self.broadcast_event(message)

    async def send_sync_request(self, screen_id: str):
        message = {
            "event": "sync_request",
            "screen_id": screen_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self.send_to_screen(screen_id, message)

    def get_connected_screens(self) -> List[str]:
        return list(self.active_connections.keys())

    def is_screen_connected(self, screen_id: str) -> bool:
        return screen_id in self.active_connections and len(self.active_connections[screen_id]) > 0

    def get_connection_count(self) -> int:
        return sum(len(conns) for conns in self.active_connections.values())

    @staticmethod
    def _serialize_message(message: Dict[str, Any]) -> str:
        def json_serial(obj):
            if hasattr(obj, "isoformat"):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")

        return json.dumps(message, default=json_serial)


manager = ConnectionManager()
