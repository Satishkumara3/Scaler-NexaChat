import uuid
from datetime import datetime, timezone
import aiosqlite
from typing import Optional, List, Dict, Any
from models.conversation import Conversation, ConversationMember

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class ConversationRepository:
    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def create_direct(self, user1_id: str, user2_id: str) -> Conversation:
        """Create a direct conversation between two users."""
        conv_id = str(uuid.uuid4())
        now = _now_iso()
        
        await self.db.execute(
            "INSERT INTO conversations (id, type, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (conv_id, "DIRECT", now, now)
        )
        await self.db.execute(
            "INSERT INTO conversation_members (conversation_id, user_id, joined_at) VALUES (?, ?, ?)",
            (conv_id, user1_id, now)
        )
        if user1_id != user2_id:
             await self.db.execute(
                 "INSERT INTO conversation_members (conversation_id, user_id, joined_at) VALUES (?, ?, ?)",
                 (conv_id, user2_id, now)
             )
        await self.db.commit()

        return Conversation(id=conv_id, type="DIRECT", created_at=now, updated_at=now)

    async def get_direct_between(self, user1_id: str, user2_id: str) -> Optional[Conversation]:
        """Find an existing direct conversation between two users."""
        if user1_id == user2_id:
            # Special case for self messaging, if supported.
            cursor = await self.db.execute(
                """
                SELECT c.*
                FROM conversations c
                JOIN conversation_members cm ON c.id = cm.conversation_id
                WHERE c.type = 'DIRECT' AND cm.user_id = ?
                GROUP BY c.id
                HAVING COUNT(cm.user_id) = 1
                """,
                (user1_id,)
            )
        else:
            cursor = await self.db.execute(
                """
                SELECT c.*
                FROM conversations c
                JOIN conversation_members cm1 ON c.id = cm1.conversation_id
                JOIN conversation_members cm2 ON c.id = cm2.conversation_id
                WHERE c.type = 'DIRECT'
                  AND cm1.user_id = ?
                  AND cm2.user_id = ?
                """,
                (user1_id, user2_id)
            )
        row = await cursor.fetchone()
        if row:
            return Conversation(**row)
        return None

    async def is_member(self, conversation_id: str, user_id: str) -> bool:
        """Check if user is a member of the conversation."""
        cursor = await self.db.execute(
            "SELECT 1 FROM conversation_members WHERE conversation_id = ? AND user_id = ?",
            (conversation_id, user_id)
        )
        return await cursor.fetchone() is not None

    async def list_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """List distinct conversations for a user, sorted by updated_at."""
        cursor = await self.db.execute(
            """
            SELECT 
                c.id, c.type, c.created_at, c.updated_at,
                (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id AND m.status != 'READ' AND m.sender_id != ?) as unread_count
            FROM conversations c
            JOIN conversation_members cm ON c.id = cm.conversation_id
            WHERE cm.user_id = ?
            ORDER BY c.updated_at DESC
            """,
            (user_id, user_id)
        )
        conversations = []
        for row in await cursor.fetchall():
            conv_data = dict(row)
            cid = row["id"]
            
            if row["type"] == "GROUP":
                g_cursor = await self.db.execute("SELECT name, avatar_url, created_by FROM group_info WHERE conversation_id = ?", (cid,))
                g_row = await g_cursor.fetchone()
                if g_row:
                    conv_data["name"] = g_row["name"]
                    conv_data["avatar_url"] = g_row["avatar_url"]
                    conv_data["created_by"] = g_row["created_by"]
                
                # Fetch members
                m_cursor = await self.db.execute("""
                    SELECT u.id, u.display_name, u.avatar_url, u.last_seen, u.phone, cm.role, cm.joined_at
                    FROM users u
                    JOIN conversation_members cm ON u.id = cm.user_id
                    WHERE cm.conversation_id = ?
                """, (cid,))
                conv_data["members"] = [dict(r) for r in await m_cursor.fetchall()]
            else:
                # Find the other member(s) to populate UI info
                mem_cursor = await self.db.execute(
                    """
                    SELECT u.id, u.display_name, u.avatar_url, u.last_seen, u.phone
                    FROM users u
                    JOIN conversation_members cm ON u.id = cm.user_id
                    WHERE cm.conversation_id = ? AND u.id != ?
                    """,
                    (cid, user_id)
                )
                other_members = [dict(m_row) for m_row in await mem_cursor.fetchall()]
                
                if not other_members:
                    # If there are no other members (meaning it's chat with themselves or members deleted)
                     mem_cursor = await self.db.execute(
                        "SELECT id, display_name, avatar_url, last_seen, phone FROM users WHERE id = ?",
                        (user_id,)
                     )
                     other_members = [dict(await mem_cursor.fetchone())]
                     
                conv_data["other_user"] = other_members[0]
            
            # Fetch last message
            msg_cursor = await self.db.execute(
                """
                SELECT id, content, created_at, sender_id, status
                FROM messages
                WHERE conversation_id = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (cid,)
            )
            last_message_row = await msg_cursor.fetchone()
            conv_data["last_message"] = dict(last_message_row) if last_message_row else None
            conversations.append(conv_data)
            
        return conversations

    async def get_by_id(self, conversation_id: str) -> Optional[Conversation]:
        cursor = await self.db.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
        row = await cursor.fetchone()
        if row:
             return Conversation(**row)
        return None

    async def get_members(self, conversation_id: str) -> List[str]:
         cursor = await self.db.execute("SELECT user_id FROM conversation_members WHERE conversation_id = ?", (conversation_id,))
         return [r["user_id"] for r in await cursor.fetchall()]

    async def touch(self, conversation_id: str):
         """Update the updated_at timestamp."""
         now = _now_iso()
         await self.db.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (now, conversation_id))
         await self.db.commit()
