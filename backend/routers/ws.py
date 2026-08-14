"""
WebSocket router — Phase 3 (Authenticated, Real-time messaging)
"""
import json
import logging
from typing import Dict, List, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException, status
from database import get_db
from services.auth_service import AuthService
from models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        # Maps user_id -> List of active WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"User {user_id} connected via WS.")

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"User {user_id} disconnected from WS.")

    async def send_personal_message(self, user_id: str, event_type: str, payload: Any):
        if user_id in self.active_connections:
            message = json.dumps({"type": event_type, "payload": payload})
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error(f"Error sending message to {user_id}: {e}")

    async def broadcast_to_users(self, user_ids: List[str], event_type: str, payload: Any):
        """Send an event to multiple users (e.g., all members of a conversation)."""
        for user_id in user_ids:
            await self.send_personal_message(user_id, event_type, payload)
            
    async def broadcast_global(self, event_type: str, payload: Any):
        """Broadcast to all connected users (for global presence in simple app logic)"""
        for user_id in self.active_connections.keys():
            await self.send_personal_message(user_id, event_type, payload)

manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(None, alias="token"),
    # In a real app we might pass the token differently, as HttpOnly cookies aren't always sent cleanly in WS handshakes depending on the client. 
    # For Phase 3, we allow passing it as a query param or checking cookies.
    db = Depends(get_db)
):
    # Authenticate
    auth_service = AuthService(db)
    user = None
    
    # Try query param first
    if token:
         user = await auth_service.get_current_user(token)
    
    # Try cookies if no query param
    if not user and "scaler_session" in websocket.cookies:
         user = await auth_service.get_current_user(websocket.cookies["scaler_session"])
         
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket, user.id)
    # Broadcast presence.online
    await manager.broadcast_global("presence.online", {"user_id": user.id})
    
    # Repositories for handling WS events
    from repositories.conversation_repo import ConversationRepository
    from repositories.user_repo import UserRepository
    conv_repo = ConversationRepository(db)
    user_repo = UserRepository(db)

    try:
        while True:
            data = await websocket.receive_text()
            try:
                event = json.loads(data)
                ev_type = event.get("type")
                
                # Handling Typing Indicators
                if ev_type in ["client.typing.start", "client.typing.stop"]:
                    payload = event.get("payload", {})
                    conv_id = payload.get("conversation_id")
                    if conv_id:
                        if await conv_repo.is_member(conv_id, user.id):
                            members = await conv_repo.get_members(conv_id)
                            out_event = "typing.start" if ev_type == "client.typing.start" else "typing.stop"
                            await manager.broadcast_to_users(
                                members, 
                                out_event, 
                                {"user_id": user.id, "conversation_id": conv_id}
                            )
                
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, user.id)
        # Update last seen and broadcast offline
        await user_repo.update_last_seen(user.id)
        await manager.broadcast_global("presence.offline", {"user_id": user.id, "last_seen": UserRepository._now_iso() if hasattr(UserRepository, '_now_iso') else None})

