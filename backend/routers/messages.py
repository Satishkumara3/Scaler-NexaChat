import aiosqlite
import os
import uuid
import shutil
from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional

from dependencies import get_db, get_current_user
from services.message_service import MessageService
from models.user import User
from routers.ws import manager

router = APIRouter(prefix="/api/messages", tags=["Messages"])

# ─── Send text message ────────────────────────────────────────────────────────

class SendMessageRequest(BaseModel):
    conversation_id: str
    content: str
    message_type: str = "TEXT"
    reply_to_message_id: Optional[str] = None

@router.post("")
async def send_message(
    req: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    """Send a text message, optionally as a reply."""
    svc = MessageService(db, manager=manager)
    msg = await svc.send_message(
        current_user.id, req.conversation_id, req.content, req.message_type,
        req.reply_to_message_id,
    )
    return {"message": msg}

# ─── Upload attachment ────────────────────────────────────────────────────────

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

@router.post("/{conversation_id}/attachments")
async def upload_attachment(
    conversation_id: str,
    file: UploadFile = File(...),
    reply_to_message_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    """Upload a file as a message attachment (optionally as a reply)."""
    svc = MessageService(db, manager=manager)
    if not await svc.conv_repo.is_member(conversation_id, current_user.id):
        raise HTTPException(status_code=403, detail="Not a member")

    file_bytes = await file.read()
    file_size = len(file_bytes)
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")
    if file_size == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    mime_type = file.content_type
    original_filename = file.filename or "unknown"

    allowed_types = [
        "image/jpeg", "image/png", "image/gif", "image/webp",
        "application/pdf", "text/plain",
    ]
    if mime_type not in allowed_types:
        raise HTTPException(status_code=415, detail="Unsupported file type")

    ext = os.path.splitext(original_filename)[1]
    stored_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, stored_filename)

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    msg_type = "IMAGE" if mime_type.startswith("image/") else "FILE"
    msg = await svc.send_attachment_message(
        current_user.id, conversation_id, original_filename, msg_type,
        original_filename, stored_filename, mime_type, file_size,
        reply_to_message_id,
    )
    return {"message": msg}

# ─── Download attachment ──────────────────────────────────────────────────────

@router.get("/attachments/{filename}")
async def get_attachment(
    filename: str,
    current_user: User = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    """Securely stream a stored attachment."""
    svc = MessageService(db)
    att = await svc.msg_repo.get_attachment_by_filename(filename)
    if not att:
        raise HTTPException(status_code=404, detail="Attachment not found")

    msg = await svc.msg_repo.get_by_id(att.message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    if not await svc.conv_repo.is_member(msg.conversation_id, current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")

    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File missing on disk")

    return FileResponse(file_path, media_type=att.mime_type, filename=att.original_filename)

# ─── Get messages ─────────────────────────────────────────────────────────────

@router.get("/{conversation_id}")
async def get_messages(
    conversation_id: str,
    limit: int = Query(50, ge=1, le=100),
    before: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    """Get messages for a conversation (includes replies + reactions)."""
    svc = MessageService(db)
    msgs = await svc.get_messages(current_user.id, conversation_id, limit, before)
    return {"messages": msgs}

# ─── Update message status ────────────────────────────────────────────────────

class UpdateMessageStatusRequest(BaseModel):
    status: str

@router.put("/{message_id}/status")
async def update_message_status(
    message_id: str,
    req: UpdateMessageStatusRequest,
    current_user: User = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    """Update message status (DELIVERED / READ)."""
    svc = MessageService(db, manager=manager)
    res = await svc.update_status(current_user.id, message_id, req.status)
    return res

# ─── Reactions ────────────────────────────────────────────────────────────────

class ReactionRequest(BaseModel):
    emoji: str

@router.post("/{message_id}/reactions")
async def toggle_reaction(
    message_id: str,
    req: ReactionRequest,
    current_user: User = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    """Toggle a reaction on a message (add if not present, remove if present)."""
    svc = MessageService(db, manager=manager)
    result = await svc.toggle_reaction(current_user.id, message_id, req.emoji)
    return result
