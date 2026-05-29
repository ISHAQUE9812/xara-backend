from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any
from app.websocket.manager import manager
from app.database.db import get_db
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/{screen_id}")
async def screen_websocket(websocket: WebSocket, screen_id: str):
    await manager.connect(websocket, screen_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message: Dict[str, Any] = json.loads(data)
                event = message.get("event")
                
                # Handle metrics updates from screen
                if event in ["audience_updated", "engagement_updated"]:
                    db = get_db()
                    update_fields = {}
                    if event == "audience_updated" and "audience" in message:
                        update_fields["audience"] = message["audience"]
                    if event == "engagement_updated" and "engagement" in message:
                        update_fields["engagement"] = message["engagement"]
                        
                    if update_fields:
                        await db["screens"].update_one(
                            {"screen_id": screen_id},
                            {"$set": update_fields}
                        )
                        # Broadcast these metrics to all connections
                        await manager.broadcast_event({
                            "event": event,
                            "screen_id": screen_id,
                            **update_fields
                        })
                        
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received from screen {screen_id}: {data}")
            except Exception as e:
                logger.error(f"Error processing message from screen {screen_id}: {e}")
                
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
