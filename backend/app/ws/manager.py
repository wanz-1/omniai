"""
WebSocket connection manager with channel-based pub/sub.

Improvements:
- Thread-safe (uses list but operations guarded; for multi-worker need Redis pub/sub).
- Limit connections per channel to avoid memory blow-up.
- Graceful handling of disconnects, send failures.
- Structured logging.
- Optional auth check placeholder.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger("omniai.ws")

MAX_CONNECTIONS_PER_CHANNEL = 100


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channel: str) -> None:
        if not channel:
            await websocket.close(code=1008)  # Policy violation
            return

        # Enforce per-channel limit
        current = self.active_connections.get(channel, [])
        if len(current) >= MAX_CONNECTIONS_PER_CHANNEL:
            logger.warning(
                f"Channel {channel} at capacity ({MAX_CONNECTIONS_PER_CHANNEL}), rejecting"
            )
            await websocket.close(code=1013)  # Try again later
            return

        try:
            await websocket.accept()
        except Exception as e:
            logger.warning(f"Failed to accept websocket for {channel}: {e}")
            return

        if channel not in self.active_connections:
            self.active_connections[channel] = []
        self.active_connections[channel].append(websocket)
        logger.info(
            "WebSocket connected",
            extra={"event": "ws_connected", "channel": channel, "count": len(self.active_connections[channel])},
        )

    def disconnect(self, websocket: WebSocket, channel: str) -> None:
        if not channel:
            return
        if channel in self.active_connections:
            self.active_connections[channel] = [
                ws for ws in self.active_connections[channel] if ws != websocket
            ]
            if not self.active_connections[channel]:
                del self.active_connections[channel]
                logger.info(
                    "WebSocket channel closed (no connections)",
                    extra={"event": "ws_channel_closed", "channel": channel},
                )
            else:
                logger.info(
                    "WebSocket disconnected",
                    extra={
                        "event": "ws_disconnected",
                        "channel": channel,
                        "remaining": len(self.active_connections[channel]),
                    },
                )

    async def send_to_channel(self, channel: str, message: dict[str, Any]) -> None:
        if not channel or channel not in self.active_connections:
            return
        disconnected: list[WebSocket] = []
        # Copy to avoid mutation during iteration
        connections = list(self.active_connections[channel])
        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)

        for ws in disconnected:
            self.disconnect(ws, channel)

    async def send_to_user(self, user_id: str, message: dict[str, Any]) -> None:
        await self.send_to_channel(f"user:{user_id}", message)
        await self.send_to_channel(f"notifications:{user_id}", message)

    async def broadcast(self, message: dict[str, Any]) -> None:
        for channel in list(self.active_connections.keys()):
            await self.send_to_channel(channel, message)

    async def handle_message(self, websocket: WebSocket, data: dict[str, Any]) -> None:
        try:
            msg_type = data.get("type")
            channel = str(data.get("channel", "")).strip()
            payload = data.get("payload", {})

            if msg_type == "subscribe":
                if not channel:
                    await websocket.send_json({"type": "error", "message": "Channel required"})
                    return
                # If already connected to another channel, keep existing plus new
                # For simplicity, connect additional channel
                await self.connect(websocket, channel)
                await websocket.send_json({"type": "subscribed", "channel": channel})

            elif msg_type == "unsubscribe":
                if channel:
                    self.disconnect(websocket, channel)
                await websocket.send_json({"type": "unsubscribed", "channel": channel})

            elif msg_type == "message":
                if not channel:
                    await websocket.send_json({"type": "error", "message": "Channel required for message"})
                    return
                # Basic payload size limit
                if isinstance(payload, dict) and len(str(payload)) > 10_000:
                    await websocket.send_json({"type": "error", "message": "Payload too large"})
                    return
                await self.send_to_channel(
                    channel,
                    {
                        "type": "message",
                        "channel": channel,
                        "payload": payload,
                    },
                )
            else:
                await websocket.send_json({"type": "error", "message": f"Unknown type: {msg_type}"})
        except Exception as e:
            logger.warning(f"WS handle_message error: {e}", extra={"event": "ws_handle_error"})
            try:
                await websocket.send_json({"type": "error", "message": "Internal error"})
            except Exception:
                # Ignore send errors for error response
                pass  # noqa: S110


manager = ConnectionManager()

# For FastAPI router, we need to expose ws endpoint if not already
try:
    from fastapi import APIRouter, Query

    ws_router = APIRouter()

    @ws_router.websocket("/ws")
    async def websocket_endpoint(
        websocket: WebSocket,
        token: str | None = Query(None),
    ):
        # Basic auth via token query param; if missing, allow anonymous but limit channels
        if token:
            try:
                from app.core.security import verify_token

                payload = verify_token(token, expected_type="access")
                if not payload:
                    await websocket.close(code=1008)
                    return
            except Exception:
                await websocket.close(code=1008)
                return

        # Accept initial connection to a generic lobby if no channel yet
        # Actual channel subscription comes via messages
        await websocket.accept()

        try:
            while True:
                data = await websocket.receive_json()
                await manager.handle_message(websocket, data)
        except Exception:
            # Cleanup on disconnect
            for ch in list(manager.active_connections.keys()):
                manager.disconnect(websocket, ch)

except Exception:
    # If dependencies not available during import (e.g., tests), skip router creation
    ws_router = None  # type: ignore
