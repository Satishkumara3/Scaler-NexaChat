"""
Contact repository — manages the contacts table.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

import aiosqlite

from models.contact import Contact
from models.user import User

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ContactRepository:
    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def add(
        self,
        owner_id: str,
        contact_user_id: str,
        nickname: Optional[str] = None,
    ) -> Contact:
        contact_id = str(uuid.uuid4())
        now = _now_iso()
        await self.db.execute(
            """
            INSERT INTO contacts (id, owner_id, contact_user_id, nickname, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (contact_id, owner_id, contact_user_id, nickname, now),
        )
        await self.db.commit()
        return Contact(
            id=contact_id,
            owner_id=owner_id,
            contact_user_id=contact_user_id,
            nickname=nickname,
            created_at=now,
        )

    async def get_contacts_for_user(self, owner_id: str) -> list[Contact]:
        """Return all contacts for a user, with the contact's User joined."""
        cursor = await self.db.execute(
            """
            SELECT
                c.id, c.owner_id, c.contact_user_id, c.nickname, c.created_at,
                u.id AS u_id, u.phone, u.display_name, u.avatar_url,
                u.about, u.created_at AS u_created_at, u.last_seen
            FROM contacts c
            JOIN users u ON u.id = c.contact_user_id
            WHERE c.owner_id = ?
            ORDER BY u.display_name ASC
            """,
            (owner_id,),
        )
        rows = await cursor.fetchall()
        contacts = []
        for row in rows:
            contact = Contact(
                id=row["id"],
                owner_id=row["owner_id"],
                contact_user_id=row["contact_user_id"],
                nickname=row["nickname"],
                created_at=row["created_at"],
            )
            contact.user = User(
                id=row["u_id"],
                phone=row["phone"],
                display_name=row["display_name"],
                avatar_url=row["avatar_url"],
                about=row["about"],
                created_at=row["u_created_at"],
                last_seen=row["last_seen"],
            )
            contacts.append(contact)
        return contacts

    async def exists(self, owner_id: str, contact_user_id: str) -> bool:
        cursor = await self.db.execute(
            "SELECT 1 FROM contacts WHERE owner_id = ? AND contact_user_id = ?",
            (owner_id, contact_user_id),
        )
        return await cursor.fetchone() is not None

    async def remove(self, owner_id: str, contact_user_id: str) -> bool:
        cursor = await self.db.execute(
            "DELETE FROM contacts WHERE owner_id = ? AND contact_user_id = ?",
            (owner_id, contact_user_id),
        )
        await self.db.commit()
        return (cursor.rowcount or 0) > 0
