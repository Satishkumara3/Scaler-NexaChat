"""
WebSocket connection manager.

Manages the mapping of user_id → WebSocket connection.
In Phase 1 this is scaffolded with the full interface but minimal logic.
Message broadcasting and typing state will be wired in Phase 3.
"""

from fastapi import WebSocket
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        # user_id → active WebSocket
        self._connections: dict[str, WebSocket] = {}
        # conv_id → set of user_ids currently typing
        self._typing: dict[str, set[str]] = {}

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        # If user reconnects from a new tab, close old connection gracefully
        if user_id in self._connections:
            try:
                await self._connections[user_id].close(code=1001)
            except Exception:
                pass
        self._connections[user_id] = websocket
        logger.info(f"WS connected: {user_id}  (total={len(self._connections)})")

    def disconnect(self, user_id: str) -> None:
        self._connections.pop(user_id, None)
        # Remove from any typing sets
        for conv_id in list(self._typing.keys()):
            self._typing[conv_id].discard(user_id)
            if not self._typing[conv_id]:
                del self._typing[conv_id]
        logger.info(f"WS disconnected: {user_id}  (total={len(self._connections)})")

    def is_connected(self, user_id: str) -> bool:
        return user_id in self._connections

    def connected_user_ids(self) -> list[str]:
        return list(self._connections.keys())

    # ------------------------------------------------------------------
    # Sending helpers
    # ------------------------------------------------------------------

    async def send_to_user(self, user_id: str, payload: dict) -> bool:
        """Send a JSON event to one user. Returns False if not connected."""
        ws = self._connections.get(user_id)
        if not ws:
            return False
        try:
            await ws.send_json(payload)
            return True
        except Exception as exc:
            logger.warning(f"Failed to send to {user_id}: {exc}")
            self.disconnect(user_id)
            return False

    async def broadcast_to_users(
        self,
        user_ids: list[str],
        payload: dict,
        exclude_user: Optional[str] = None,
    ) -> None:
        """Broadcast a JSON event to multiple users."""
        for uid in user_ids:
            if uid == exclude_user:
                continue
            await self.send_to_user(uid, payload)

    # ------------------------------------------------------------------
    # Typing state helpers (Phase 3 will use these)
    # ------------------------------------------------------------------

    def set_typing(self, conv_id: str, user_id: str, is_typing: bool) -> None:
        if is_typing:
            self._typing.setdefault(conv_id, set()).add(user_id)
        else:
            if conv_id in self._typing:
                self._typing[conv_id].discard(user_id)

    def get_typing_users(self, conv_id: str) -> list[str]:
        return list(self._typing.get(conv_id, set()))

    # ------------------------------------------------------------------
    # Stats (used by health endpoint)
    # ------------------------------------------------------------------

    def stats(self) -> dict:
        return {
            "connected_users": len(self._connections),
            "active_typing_convs": len(self._typing),
        }


# Singleton — imported by routers
manager = ConnectionManager()
