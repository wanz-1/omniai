import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger("omniai.ws")


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channel: str) -> None:
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = []
        self.active_connections[channel].append(websocket)
        logger.info(f"WebSocket connected to channel: {channel}")

    def disconnect(self, websocket: WebSocket, channel: str) -> None:
        if channel in self.active_connections:
            self.active_connections[channel] = [
                ws for ws in self.active_connections[channel] if ws != websocket
            ]
            if not self.active_connections[channel]:
                del self.active_connections[channel]
        logger.info(f"WebSocket disconnected from channel: {channel}")

    async def send_to_channel(self, channel: str, message: dict[str, Any]) -> None:
        if channel not in self.active_connections:
            return
        disconnected = []
        for websocket in self.active_connections[channel]:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)
        for ws in disconnected:
            self.disconnect(ws, channel)

    async def send_to_user(self, user_id: str, message: dict[str, Any]) -> None:
        await self.send_to_channel(f"user:{user_id}", message)

    async def broadcast(self, message: dict[str, Any]) -> None:
        for channel in list(self.active_connections.keys()):
            await self.send_to_channel(channel, message)

    async def handle_message(self, websocket: WebSocket, data: dict[str, Any]) -> None:
        msg_type = data.get("type")
        channel = data.get("channel", "")
        payload = data.get("payload", {})

        if msg_type == "subscribe":
            await self.connect(websocket, channel)
            await websocket.send_json({"type": "subscribed", "channel": channel})
        elif msg_type == "unsubscribe":
            self.disconnect(websocket, channel)
            await websocket.send_json({"type": "unsubscribed", "channel": channel})
        elif msg_type == "message":
            await self.send_to_channel(channel, {
                "type": "message",
                "channel": channel,
                "payload": payload,
            })


manager = ConnectionManager()
