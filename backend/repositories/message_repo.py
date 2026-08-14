import uuid
from datetime import datetime, timezone
import aiosqlite
from typing import List, Optional
from models.message import Message, Attachment, Reaction, ReplyPreview


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_message(row, reactions: List[Reaction] | None = None) -> Message:
    """Convert a DB row (with optional joined attachment + reply columns) to a Message."""
    keys = row.keys()

    # --- attachment ---
    att = None
    if "attachment_id" in keys and row["attachment_id"] is not None:
        att = Attachment(
            id=row["attachment_id"],
            message_id=row["id"],
            original_filename=row["original_filename"],
            stored_filename=row["stored_filename"],
            mime_type=row["mime_type"],
            file_size=row["file_size"],
            created_at=row["attachment_created_at"],
        )

    # --- reply preview ---
    reply_preview = None
    reply_to_id = row["reply_to_message_id"] if "reply_to_message_id" in keys else None
    if reply_to_id and "reply_sender_id" in keys and row["reply_sender_id"] is not None:
        raw_content = row["reply_content"] or ""
        reply_preview = ReplyPreview(
            id=reply_to_id,
            sender_id=row["reply_sender_id"],
            sender_name=row["reply_sender_name"] or "Unknown",
            content=raw_content[:80],
        )

    return Message(
        id=row["id"],
        conversation_id=row["conversation_id"],
        sender_id=row["sender_id"],
        content=row["content"],
        message_type=row["message_type"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        reply_to_message_id=reply_to_id,
        reply_preview=reply_preview,
        attachment=att,
        reactions=reactions or [],
    )


# --------------------------------------------------------------------------
# SQL snippets
# --------------------------------------------------------------------------

_MSG_SELECT = """
    SELECT
        m.*,
        -- attachment columns
        a.id               AS attachment_id,
        a.original_filename,
        a.stored_filename,
        a.mime_type,
        a.file_size,
        a.created_at       AS attachment_created_at,
        -- reply preview columns
        rm.sender_id       AS reply_sender_id,
        ru.display_name    AS reply_sender_name,
        rm.content         AS reply_content
    FROM messages m
    LEFT JOIN attachments a  ON a.message_id = m.id
    LEFT JOIN messages    rm ON rm.id = m.reply_to_message_id
    LEFT JOIN users       ru ON ru.id = rm.sender_id
"""


class MessageRepository:
    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    async def _fetch_reactions(self, message_ids: List[str]) -> dict[str, List[Reaction]]:
        """Fetch all reactions for a list of message IDs. Returns dict[msg_id -> [Reaction]]."""
        if not message_ids:
            return {}
        placeholders = ",".join("?" * len(message_ids))
        cursor = await self.db.execute(
            f"SELECT * FROM message_reactions WHERE message_id IN ({placeholders}) ORDER BY created_at ASC",
            message_ids,
        )
        rows = await cursor.fetchall()
        result: dict[str, List[Reaction]] = {}
        for row in rows:
            r = Reaction(id=row["id"], message_id=row["message_id"], user_id=row["user_id"],
                         emoji=row["emoji"], created_at=row["created_at"])
            result.setdefault(row["message_id"], []).append(r)
        return result

    # ------------------------------------------------------------------ #
    # Message CRUD                                                         #
    # ------------------------------------------------------------------ #

    async def create(self, conversation_id: str, sender_id: str, content: str,
                     message_type: str = "TEXT",
                     reply_to_message_id: Optional[str] = None) -> Message:
        msg_id = str(uuid.uuid4())
        now = _now_iso()
        await self.db.execute(
            """
            INSERT INTO messages
                (id, conversation_id, sender_id, content, message_type, status,
                 reply_to_message_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'SENT', ?, ?, ?)
            """,
            (msg_id, conversation_id, sender_id, content, message_type,
             reply_to_message_id, now, now),
        )
        await self.db.commit()
        return await self.get_by_id(msg_id)

    async def create_with_attachment(self, conversation_id: str, sender_id: str, content: str,
                                     message_type: str, original_filename: str,
                                     stored_filename: str, mime_type: str, file_size: int,
                                     reply_to_message_id: Optional[str] = None) -> Message:
        msg_id = str(uuid.uuid4())
        att_id = str(uuid.uuid4())
        now = _now_iso()
        await self.db.execute(
            """
            INSERT INTO messages
                (id, conversation_id, sender_id, content, message_type, status,
                 reply_to_message_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'SENT', ?, ?, ?)
            """,
            (msg_id, conversation_id, sender_id, content, message_type,
             reply_to_message_id, now, now),
        )
        await self.db.execute(
            """
            INSERT INTO attachments (id, message_id, original_filename, stored_filename, mime_type, file_size, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (att_id, msg_id, original_filename, stored_filename, mime_type, file_size, now),
        )
        await self.db.commit()
        return await self.get_by_id(msg_id)

    async def get_by_id(self, message_id: str) -> Optional[Message]:
        cursor = await self.db.execute(
            _MSG_SELECT + " WHERE m.id = ?", (message_id,)
        )
        row = await cursor.fetchone()
        if not row:
            return None
        reactions = await self._fetch_reactions([message_id])
        return _row_to_message(row, reactions.get(message_id, []))

    async def get_by_conversation(self, conversation_id: str, limit: int = 50,
                                  before_time: Optional[str] = None) -> List[Message]:
        params: list = [conversation_id]
        time_clause = ""
        if before_time:
            time_clause = "AND m.created_at < ?"
            params.append(before_time)

        query = f"""
        SELECT * FROM (
            {_MSG_SELECT}
            WHERE m.conversation_id = ? {time_clause}
            ORDER BY m.created_at DESC
            LIMIT ?
        ) ORDER BY created_at ASC
        """
        params = [conversation_id, *([before_time] if before_time else []), limit]
        cursor = await self.db.execute(query, params)
        rows = await cursor.fetchall()
        if not rows:
            return []
        message_ids = [r["id"] for r in rows]
        reactions = await self._fetch_reactions(message_ids)
        return [_row_to_message(row, reactions.get(row["id"], [])) for row in rows]

    async def get_attachment_by_filename(self, filename: str) -> Optional[Attachment]:
        cursor = await self.db.execute(
            "SELECT * FROM attachments WHERE stored_filename = ?", (filename,)
        )
        row = await cursor.fetchone()
        if row:
            return Attachment(
                id=row["id"], message_id=row["message_id"],
                original_filename=row["original_filename"],
                stored_filename=row["stored_filename"],
                mime_type=row["mime_type"], file_size=row["file_size"],
                created_at=row["created_at"],
            )
        return None

    async def update_status(self, message_id: str, new_status: str) -> None:
        now = _now_iso()
        await self.db.execute(
            "UPDATE messages SET status = ?, updated_at = ? WHERE id = ?",
            (new_status, now, message_id),
        )
        await self.db.commit()
        return await self.get_by_id(message_id)

    # ------------------------------------------------------------------ #
    # Reactions                                                            #
    # ------------------------------------------------------------------ #

    async def add_reaction(self, message_id: str, user_id: str, emoji: str) -> Reaction:
        """Add a reaction. If already exists (same user+emoji+msg) it's a no-op (toggle off handled by service)."""
        reaction_id = str(uuid.uuid4())
        now = _now_iso()
        await self.db.execute(
            """
            INSERT OR IGNORE INTO message_reactions (id, message_id, user_id, emoji, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (reaction_id, message_id, user_id, emoji, now),
        )
        await self.db.commit()
        # Return the actual row (may be existing if OR IGNORE)
        cursor = await self.db.execute(
            "SELECT * FROM message_reactions WHERE message_id=? AND user_id=? AND emoji=?",
            (message_id, user_id, emoji),
        )
        row = await cursor.fetchone()
        return Reaction(id=row["id"], message_id=row["message_id"], user_id=row["user_id"],
                        emoji=row["emoji"], created_at=row["created_at"])

    async def remove_reaction(self, message_id: str, user_id: str, emoji: str) -> bool:
        """Remove a reaction. Returns True if a row was deleted."""
        cursor = await self.db.execute(
            "DELETE FROM message_reactions WHERE message_id=? AND user_id=? AND emoji=?",
            (message_id, user_id, emoji),
        )
        await self.db.commit()
        return cursor.rowcount > 0

    async def get_reaction(self, message_id: str, user_id: str, emoji: str) -> Optional[Reaction]:
        cursor = await self.db.execute(
            "SELECT * FROM message_reactions WHERE message_id=? AND user_id=? AND emoji=?",
            (message_id, user_id, emoji),
        )
        row = await cursor.fetchone()
        if row:
            return Reaction(id=row["id"], message_id=row["message_id"], user_id=row["user_id"],
                            emoji=row["emoji"], created_at=row["created_at"])
        return None
