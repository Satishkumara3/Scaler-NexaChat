"""
GroupRepository — CRUD for GROUP conversations.

Groups reuse the conversations + conversation_members tables.
Extra metadata (name, avatar, creator) lives in group_info.
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import aiosqlite

from models.conversation import Conversation, GroupInfo


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class GroupRepository:
    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    # ── Creation ──────────────────────────────────────────────────────────────

    async def create(
        self,
        name: str,
        creator_id: str,
        member_ids: List[str],
        avatar_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a GROUP conversation with creator as admin.
        member_ids should include IDs of additional members (not the creator).
        Returns combined dict of conversation + group_info.
        """
        conv_id = str(uuid.uuid4())
        now = _now_iso()

        # Insert conversation
        await self.db.execute(
            "INSERT INTO conversations (id, type, created_at, updated_at) VALUES (?, 'GROUP', ?, ?)",
            (conv_id, now, now),
        )
        # Insert group_info
        await self.db.execute(
            "INSERT INTO group_info (conversation_id, name, avatar_url, created_by, created_at) VALUES (?, ?, ?, ?, ?)",
            (conv_id, name, avatar_url, creator_id, now),
        )
        # Creator is admin
        await self.db.execute(
            "INSERT INTO conversation_members (conversation_id, user_id, role, joined_at) VALUES (?, ?, 'admin', ?)",
            (conv_id, creator_id, now),
        )
        # Additional members
        for m_id in member_ids:
            if m_id != creator_id:
                await self.db.execute(
                    "INSERT OR IGNORE INTO conversation_members (conversation_id, user_id, role, joined_at) VALUES (?, ?, 'member', ?)",
                    (conv_id, m_id, now),
                )
        await self.db.commit()

        return {
            "id": conv_id,
            "type": "GROUP",
            "name": name,
            "avatar_url": avatar_url,
            "created_by": creator_id,
            "created_at": now,
            "updated_at": now,
        }

    # ── Read ─────────────────────────────────────────────────────────────────

    async def get_by_id(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Return group details including group_info."""
        cursor = await self.db.execute(
            """
            SELECT c.id, c.type, c.created_at, c.updated_at,
                   g.name, g.avatar_url, g.created_by
            FROM conversations c
            JOIN group_info g ON c.id = g.conversation_id
            WHERE c.id = ? AND c.type = 'GROUP'
            """,
            (conversation_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_members(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Return members with user info and role."""
        cursor = await self.db.execute(
            """
            SELECT u.id, u.display_name, u.avatar_url, u.phone, u.last_seen,
                   cm.role, cm.joined_at
            FROM conversation_members cm
            JOIN users u ON cm.user_id = u.id
            WHERE cm.conversation_id = ?
            ORDER BY cm.role DESC, cm.joined_at ASC
            """,
            (conversation_id,),
        )
        return [dict(r) for r in await cursor.fetchall()]

    async def get_member_ids(self, conversation_id: str) -> List[str]:
        cursor = await self.db.execute(
            "SELECT user_id FROM conversation_members WHERE conversation_id = ?",
            (conversation_id,),
        )
        return [r["user_id"] for r in await cursor.fetchall()]

    async def is_member(self, conversation_id: str, user_id: str) -> bool:
        cursor = await self.db.execute(
            "SELECT 1 FROM conversation_members WHERE conversation_id = ? AND user_id = ?",
            (conversation_id, user_id),
        )
        return await cursor.fetchone() is not None

    async def get_role(self, conversation_id: str, user_id: str) -> Optional[str]:
        cursor = await self.db.execute(
            "SELECT role FROM conversation_members WHERE conversation_id = ? AND user_id = ?",
            (conversation_id, user_id),
        )
        row = await cursor.fetchone()
        return row["role"] if row else None

    # ── Mutations ─────────────────────────────────────────────────────────────

    async def add_member(self, conversation_id: str, user_id: str) -> bool:
        """Returns True if newly added, False if already a member."""
        cursor = await self.db.execute(
            "SELECT 1 FROM conversation_members WHERE conversation_id = ? AND user_id = ?",
            (conversation_id, user_id),
        )
        if await cursor.fetchone():
            return False
        await self.db.execute(
            "INSERT INTO conversation_members (conversation_id, user_id, role, joined_at) VALUES (?, ?, 'member', ?)",
            (conversation_id, user_id, _now_iso()),
        )
        await self.db.commit()
        return True

    async def remove_member(self, conversation_id: str, user_id: str) -> bool:
        """Returns True if removed."""
        cursor = await self.db.execute(
            "DELETE FROM conversation_members WHERE conversation_id = ? AND user_id = ?",
            (conversation_id, user_id),
        )
        await self.db.commit()
        return cursor.rowcount > 0

    async def update_info(
        self,
        conversation_id: str,
        name: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> None:
        if name is not None:
            await self.db.execute(
                "UPDATE group_info SET name = ? WHERE conversation_id = ?",
                (name, conversation_id),
            )
        if avatar_url is not None:
            await self.db.execute(
                "UPDATE group_info SET avatar_url = ? WHERE conversation_id = ?",
                (avatar_url, conversation_id),
            )
        await self.db.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (_now_iso(), conversation_id),
        )
        await self.db.commit()

    async def member_count(self, conversation_id: str) -> int:
        cursor = await self.db.execute(
            "SELECT COUNT(*) as cnt FROM conversation_members WHERE conversation_id = ?",
            (conversation_id,),
        )
        row = await cursor.fetchone()
        return row["cnt"] if row else 0
