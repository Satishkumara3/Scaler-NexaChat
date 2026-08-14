"""
Session repository — manages DB-backed sessions.
Tokens are stored as SHA-256 hashes; the raw token only ever lives in memory
and the HttpOnly cookie.
"""

import uuid
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

import aiosqlite

from models.session import Session
from config import settings

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _expires_iso(days: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def hash_token(raw_token: str) -> str:
    """One-way hash — never stored in plaintext."""
    return hashlib.sha256(raw_token.encode()).hexdigest()


class SessionRepository:
    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def create(self, user_id: str) -> tuple[str, Session]:
        """
        Create a new session. Returns (raw_token, Session).
        raw_token must be placed in the HttpOnly cookie — never persisted.
        """
        raw_token = str(uuid.uuid4()) + "-" + str(uuid.uuid4())  # 73 chars entropy
        token_hash = hash_token(raw_token)
        session_id = str(uuid.uuid4())
        now = _now_iso()
        expires = _expires_iso(settings.ACCESS_TOKEN_EXPIRE_DAYS)

        await self.db.execute(
            """
            INSERT INTO sessions (id, user_id, token_hash, expires_at, created_at, last_used_at)
            VALUES (?, ?, ?, ?, ?, NULL)
            """,
            (session_id, user_id, token_hash, expires, now),
        )
        await self.db.commit()

        session = Session(
            id=session_id,
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires,
            created_at=now,
            last_used_at=None,
        )
        logger.info(f"Session created for user {user_id}, expires {expires}")
        return raw_token, session

    async def get_by_token(self, raw_token: str) -> Optional[Session]:
        token_hash = hash_token(raw_token)
        cursor = await self.db.execute(
            "SELECT * FROM sessions WHERE token_hash = ?", (token_hash,)
        )
        row = await cursor.fetchone()
        return Session.from_row(row) if row else None

    async def is_valid(self, raw_token: str) -> bool:
        """True iff session exists and hasn't expired."""
        session = await self.get_by_token(raw_token)
        if not session:
            return False
        expires = datetime.fromisoformat(session.expires_at)
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) < expires

    async def touch(self, raw_token: str) -> None:
        """Update last_used_at to now."""
        token_hash = hash_token(raw_token)
        await self.db.execute(
            "UPDATE sessions SET last_used_at = ? WHERE token_hash = ?",
            (_now_iso(), token_hash),
        )
        await self.db.commit()

    async def delete(self, raw_token: str) -> None:
        token_hash = hash_token(raw_token)
        await self.db.execute(
            "DELETE FROM sessions WHERE token_hash = ?", (token_hash,)
        )
        await self.db.commit()

    async def delete_all_for_user(self, user_id: str) -> None:
        await self.db.execute(
            "DELETE FROM sessions WHERE user_id = ?", (user_id,)
        )
        await self.db.commit()

    async def delete_expired(self) -> int:
        """Cleanup job — delete all expired sessions. Returns count deleted."""
        now = _now_iso()
        cursor = await self.db.execute(
            "DELETE FROM sessions WHERE expires_at < ?", (now,)
        )
        await self.db.commit()
        return cursor.rowcount or 0
