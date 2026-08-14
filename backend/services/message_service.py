import aiosqlite
from typing import List, Optional

from repositories.message_repo import MessageRepository
from repositories.conversation_repo import ConversationRepository
from models.message import Message
from fastapi import HTTPException


class MessageService:
    def __init__(self, db: aiosqlite.Connection, manager=None):
        self.msg_repo = MessageRepository(db)
        self.conv_repo = ConversationRepository(db)
        self.manager = manager

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def _msg_to_dict(self, msg: Message) -> dict:
        d = {
            "id": msg.id,
            "conversation_id": msg.conversation_id,
            "sender_id": msg.sender_id,
            "content": msg.content,
            "message_type": msg.message_type,
            "status": msg.status,
            "created_at": msg.created_at,
            "updated_at": msg.updated_at,
            "reply_to_message_id": msg.reply_to_message_id,
        }
        if msg.reply_preview:
            d["reply_preview"] = {
                "id": msg.reply_preview.id,
                "sender_id": msg.reply_preview.sender_id,
                "sender_name": msg.reply_preview.sender_name,
                "content": msg.reply_preview.content,
            }
        if msg.attachment:
            d["attachment"] = {
                "id": msg.attachment.id,
                "original_filename": msg.attachment.original_filename,
                "stored_filename": msg.attachment.stored_filename,
                "mime_type": msg.attachment.mime_type,
                "file_size": msg.attachment.file_size,
                "url": f"/api/messages/attachments/{msg.attachment.stored_filename}",
            }
        d["reactions"] = [
            {"id": r.id, "message_id": r.message_id, "user_id": r.user_id,
             "emoji": r.emoji, "created_at": r.created_at}
            for r in (msg.reactions or [])
        ]
        return d

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    async def _validate_reply(self, reply_to_message_id: Optional[str],
                               conversation_id: str) -> None:
        """Raise 400/404 if the reply target is invalid or cross-conversation."""
        if not reply_to_message_id:
            return
        original = await self.msg_repo.get_by_id(reply_to_message_id)
        if not original:
            raise HTTPException(status_code=404, detail="Replied-to message not found")
        if original.conversation_id != conversation_id:
            raise HTTPException(status_code=400, detail="Cannot reply across conversations")

    # ------------------------------------------------------------------
    # Message sending
    # ------------------------------------------------------------------

    async def send_message(self, user_id: str, conversation_id: str, content: str,
                           message_type: str = "TEXT",
                           reply_to_message_id: Optional[str] = None) -> dict:
        if not await self.conv_repo.is_member(conversation_id, user_id):
            raise HTTPException(status_code=403, detail="Not a member of this conversation")

        await self._validate_reply(reply_to_message_id, conversation_id)

        msg = await self.msg_repo.create(
            conversation_id, user_id, content, message_type, reply_to_message_id
        )
        await self.conv_repo.touch(conversation_id)
        msg_dict = self._msg_to_dict(msg)

        if self.manager:
            members = await self.conv_repo.get_members(conversation_id)
            await self.manager.broadcast_to_users(members, "message.new", msg_dict)

        return msg_dict

    async def send_attachment_message(self, user_id: str, conversation_id: str, content: str,
                                      message_type: str, original_filename: str,
                                      stored_filename: str, mime_type: str, file_size: int,
                                      reply_to_message_id: Optional[str] = None) -> dict:
        if not await self.conv_repo.is_member(conversation_id, user_id):
            raise HTTPException(status_code=403, detail="Not a member of this conversation")

        await self._validate_reply(reply_to_message_id, conversation_id)

        msg = await self.msg_repo.create_with_attachment(
            conversation_id, user_id, content, message_type,
            original_filename, stored_filename, mime_type, file_size,
            reply_to_message_id,
        )
        await self.conv_repo.touch(conversation_id)
        msg_dict = self._msg_to_dict(msg)

        if self.manager:
            members = await self.conv_repo.get_members(conversation_id)
            await self.manager.broadcast_to_users(members, "message.new", msg_dict)

        return msg_dict

    async def get_messages(self, user_id: str, conversation_id: str,
                           limit: int = 50, before: str = None) -> List[dict]:
        if not await self.conv_repo.is_member(conversation_id, user_id):
            raise HTTPException(status_code=403, detail="Not a member of this conversation")
        msgs = await self.msg_repo.get_by_conversation(conversation_id, limit, before)
        return [self._msg_to_dict(m) for m in msgs]

    async def update_status(self, user_id: str, message_id: str, status: str) -> dict:
        msg = await self.msg_repo.get_by_id(message_id)
        if not msg:
            raise HTTPException(status_code=404, detail="Message not found")
        if not await self.conv_repo.is_member(msg.conversation_id, user_id):
            raise HTTPException(status_code=403, detail="Not a member of this conversation")
        if status in ["DELIVERED", "READ"] and msg.sender_id == user_id:
            raise HTTPException(status_code=403, detail="Cannot mark your own message as read/delivered")

        await self.msg_repo.update_status(message_id, status)

        if self.manager:
            members = await self.conv_repo.get_members(msg.conversation_id)
            event_type = f"message.{status.lower()}"
            payload = {
                "message_id": message_id,
                "conversation_id": msg.conversation_id,
                "status": status,
                "user_id": user_id,
            }
            await self.manager.broadcast_to_users(members, event_type, payload)

        return {"id": message_id, "status": status}

    # ------------------------------------------------------------------
    # Reactions
    # ------------------------------------------------------------------

    ALLOWED_EMOJIS = {"❤️", "👍", "😂", "😮", "😢"}

    async def toggle_reaction(self, user_id: str, message_id: str, emoji: str) -> dict:
        """Add reaction if not present; remove it if already present (toggle)."""
        if emoji not in self.ALLOWED_EMOJIS:
            raise HTTPException(status_code=400, detail=f"Emoji not allowed. Use: {', '.join(self.ALLOWED_EMOJIS)}")

        msg = await self.msg_repo.get_by_id(message_id)
        if not msg:
            raise HTTPException(status_code=404, detail="Message not found")
        if not await self.conv_repo.is_member(msg.conversation_id, user_id):
            raise HTTPException(status_code=403, detail="Not a member of this conversation")

        existing = await self.msg_repo.get_reaction(message_id, user_id, emoji)

        if existing:
            # Toggle OFF
            await self.msg_repo.remove_reaction(message_id, user_id, emoji)
            event = "reaction.removed"
            payload = {
                "message_id": message_id,
                "conversation_id": msg.conversation_id,
                "user_id": user_id,
                "emoji": emoji,
            }
        else:
            # Toggle ON
            reaction = await self.msg_repo.add_reaction(message_id, user_id, emoji)
            event = "reaction.added"
            payload = {
                "message_id": message_id,
                "conversation_id": msg.conversation_id,
                "user_id": user_id,
                "emoji": emoji,
                "reaction_id": reaction.id,
                "created_at": reaction.created_at,
            }

        if self.manager:
            members = await self.conv_repo.get_members(msg.conversation_id)
            await self.manager.broadcast_to_users(members, event, payload)

        return {"event": event, **payload}
