from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        # Store active connections: {screen_id: [websockets]}
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.screen_connections: Dict[int, str] = {}  # Map websocket id -> screen_id
        self._db = None  # Database reference set at startup

    def set_db(self, db):
        """Set database reference for screen status updates."""
        self._db = db

    async def connect(self, websocket: WebSocket, screen_id: str):
        """Connect a screen to WebSocket and update DB status."""
        await websocket.accept()

        if screen_id not in self.active_connections:
            self.active_connections[screen_id] = []

        self.active_connections[screen_id].append(websocket)
        self.screen_connections[id(websocket)] = screen_id

        logger.info(f"Screen {screen_id} connected. Active connections: {len(self.active_connections[screen_id])}")

        # Update screen status in database
        if self._db is not None:
            try:
                await self._db["screens"].update_one(
                    {"screen_id": screen_id},
                    {"$set": {
                        "websocket_connected": True,
                        "status": "online",
                        "last_seen": datetime.utcnow()
                    }}
                )
            except Exception as e:
                logger.error(f"Failed to update screen status on connect: {e}")

        # Broadcast connection event
        await self.broadcast_event({
            "event": "screen_online",
            "screen_id": screen_id,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def disconnect(self, websocket: WebSocket):
        """Disconnect a screen from WebSocket and update DB status."""
        screen_id = self.screen_connections.pop(id(websocket), None)

        if screen_id and screen_id in self.active_connections:
            if websocket in self.active_connections[screen_id]:
                self.active_connections[screen_id].remove(websocket)
                logger.info(f"Screen {screen_id} disconnected. Remaining: {len(self.active_connections[screen_id])}")

                # If no more connections for this screen
                if len(self.active_connections[screen_id]) == 0:
                    del self.active_connections[screen_id]

                    # Update screen status to offline in database
                    if self._db is not None:
                        try:
                            await self._db["screens"].update_one(
                                {"screen_id": screen_id},
                                {"$set": {
                                    "websocket_connected": False,
                                    "status": "offline",
                                    "last_seen": datetime.utcnow()
                                }}
                            )
                        except Exception as e:
                            logger.error(f"Failed to update screen status on disconnect: {e}")

                    # Broadcast offline event
                    await self.broadcast_event({
                        "event": "screen_offline",
                        "screen_id": screen_id,
                        "timestamp": datetime.utcnow().isoformat()
                    })

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all active WebSocket connections."""
        message_str = self._serialize_message(message)
        dead_connections = []

        for screen_id, connections in list(self.active_connections.items()):
            for connection in connections:
                try:
                    await connection.send_text(message_str)
                except Exception as e:
                    logger.error(f"Error broadcasting to screen {screen_id}: {e}")
                    dead_connections.append(connection)

        # Cleanup dead connections
        for conn in dead_connections:
            await self.disconnect(conn)

    async def send_to_screen(self, screen_id: str, message: Dict[str, Any]):
        """Send a message to a specific screen."""
        if screen_id not in self.active_connections:
            logger.warning(f"Screen {screen_id} not connected via WebSocket")
            return

        message_str = self._serialize_message(message)
        dead_connections = []

        for connection in self.active_connections[screen_id]:
            try:
                await connection.send_text(message_str)
            except Exception as e:
                logger.error(f"Error sending to screen {screen_id}: {e}")
                dead_connections.append(connection)

        for conn in dead_connections:
            await self.disconnect(conn)

    async def broadcast_event(self, event: Dict[str, Any]):
        """Broadcast an event to all connections."""
        event_message = {
            "type": "event",
            "data": event
        }
        await self.broadcast(event_message)

    async def send_campaign_update(self, screen_id: str, campaign_data: Dict[str, Any]):
        """Send campaign update to specific screen."""
        message = {
            "event": "campaign_update",
            "screen_id": screen_id,
            "campaign": campaign_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.send_to_screen(screen_id, message)

    async def send_campaign_play(self, screen_id: str, campaign_data: Dict[str, Any]):
        """Send campaign play trigger to specific screen."""
        message = {
            "event": "campaign_play",
            "screen_id": screen_id,
            "video": campaign_data.get("video_url"),
            "media_url": campaign_data.get("media_url"),
            "campaign_id": campaign_data.get("id"),
            "campaign_name": campaign_data.get("campaign_name"),
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.send_to_screen(screen_id, message)

    async def send_status_update(self, screen_id: str, status: str):
        """Send status update to all connections about a screen."""
        message = {
            "event": "screen_status_update",
            "screen_id": screen_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast_event(message)

    async def send_sync_request(self, screen_id: str):
        """Request screen to sync with cloud."""
        message = {
            "event": "sync_request",
            "screen_id": screen_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.send_to_screen(screen_id, message)

    def get_connected_screens(self) -> List[str]:
        """Get list of currently connected screen IDs."""
        return list(self.active_connections.keys())

    def is_screen_connected(self, screen_id: str) -> bool:
        """Check if a screen is connected."""
        return screen_id in self.active_connections and len(self.active_connections[screen_id]) > 0

    def get_connection_count(self) -> int:
        """Get total number of active WebSocket connections."""
        return sum(len(conns) for conns in self.active_connections.values())

    @staticmethod
    def _serialize_message(message: Dict[str, Any]) -> str:
        """Serialize message to JSON, handling datetime objects."""
        def json_serial(obj):
            if hasattr(obj, 'isoformat'):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")

        return json.dumps(message, default=json_serial)


# Global manager instance
manager = ConnectionManager()
