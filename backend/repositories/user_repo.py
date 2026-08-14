"""
User repository — all DB queries related to the users table.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

import aiosqlite

from models.user import User

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _avatar_url(display_name: str) -> str:
    """Generate a ui-avatars.com URL from a display name."""
    import urllib.parse
    name_encoded = urllib.parse.quote(display_name)
    return (
        f"https://ui-avatars.com/api/?name={name_encoded}"
        f"&background=00a884&color=fff&size=128&bold=true&rounded=true"
    )


class UserRepository:
    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def create(
        self,
        phone: str,
        display_name: str,
        about: str = "Hey there! I am using Scaler Chat.",
    ) -> User:
        user_id = str(uuid.uuid4())
        now = _now_iso()
        avatar = _avatar_url(display_name)

        await self.db.execute(
            """
            INSERT INTO users (id, phone, display_name, avatar_url, about, created_at, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, NULL)
            """,
            (user_id, phone, display_name, avatar, about, now),
        )
        await self.db.commit()
        logger.info(f"Created user {user_id} ({phone})")
        return User(
            id=user_id,
            phone=phone,
            display_name=display_name,
            avatar_url=avatar,
            about=about,
            created_at=now,
            last_seen=None,
        )

    async def get_by_id(self, user_id: str) -> Optional[User]:
        cursor = await self.db.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        return User.from_row(row) if row else None

    async def get_by_phone(self, phone: str) -> Optional[User]:
        cursor = await self.db.execute(
            "SELECT * FROM users WHERE phone = ?", (phone,)
        )
        row = await cursor.fetchone()
        return User.from_row(row) if row else None

    async def exists_by_phone(self, phone: str) -> bool:
        cursor = await self.db.execute(
            "SELECT 1 FROM users WHERE phone = ?", (phone,)
        )
        return await cursor.fetchone() is not None

    async def exists_by_id(self, user_id: str) -> bool:
        cursor = await self.db.execute(
            "SELECT 1 FROM users WHERE id = ?", (user_id,)
        )
        return await cursor.fetchone() is not None

    async def update_last_seen(self, user_id: str) -> None:
        await self.db.execute(
            "UPDATE users SET last_seen = ? WHERE id = ?",
            (_now_iso(), user_id),
        )
        await self.db.commit()

    async def update_profile(
        self,
        user_id: str,
        display_name: Optional[str] = None,
        about: Optional[str] = None,
    ) -> Optional[User]:
        if display_name is not None:
            avatar = _avatar_url(display_name)
            await self.db.execute(
                "UPDATE users SET display_name = ?, avatar_url = ? WHERE id = ?",
                (display_name, avatar, user_id),
            )
        if about is not None:
            await self.db.execute(
                "UPDATE users SET about = ? WHERE id = ?",
                (about, user_id),
            )
        await self.db.commit()
        return await self.get_by_id(user_id)

    async def get_all(self) -> list[User]:
        cursor = await self.db.execute(
            "SELECT * FROM users ORDER BY created_at ASC"
        )
        rows = await cursor.fetchall()
        return [User.from_row(r) for r in rows]
