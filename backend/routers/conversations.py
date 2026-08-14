import aiosqlite
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from dependencies import get_db, get_current_user
from services.conversation_service import ConversationService
from models.user import User

router = APIRouter(prefix="/api/conversations", tags=["Conversations"])

class CreateDirectRequest(BaseModel):
    user_id: str

@router.post("")
async def create_or_get_direct(
    req: CreateDirectRequest,
    current_user: User = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db)
):
    """Create or get a direct conversation with another user."""
    svc = ConversationService(db)
    return await svc.get_or_create_direct(current_user.id, req.user_id)

@router.get("")
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db)
):
    """List all conversations for the current user."""
    svc = ConversationService(db)
    conversations = await svc.list_for_user(current_user.id)
    return {"conversations": conversations}

@router.get("/{conversation_id}")
async def get_conversation_details(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db)
):
    """Get details of a specific conversation."""
    svc = ConversationService(db)
    return await svc.get_details(current_user.id, conversation_id)
