"""
OTP repository — manages short-lived OTP codes.

In development mode: always accepts '123456'.
Codes are SHA-256 hashed before storage.
TTL: 5 minutes.
"""

import uuid
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

import aiosqlite

logger = logging.getLogger(__name__)

OTP_TTL_MINUTES = 5
MOCK_OTP = "123456"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _expires_iso() -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=OTP_TTL_MINUTES)).isoformat()


def hash_otp(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


class OtpRepository:
    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def create(self, phone: str) -> str:
        """
        Create an OTP entry. In dev mode returns '123456'.
        In a real system this would generate a random 6-digit code
        and send it via SMS.
        """
        code = MOCK_OTP
        otp_id = str(uuid.uuid4())
        now = _now_iso()

        # Invalidate any unused OTPs for this phone first
        await self.db.execute(
            "UPDATE otp_codes SET used = 1 WHERE phone = ? AND used = 0",
            (phone,),
        )

        await self.db.execute(
            """
            INSERT INTO otp_codes (id, phone, code_hash, expires_at, used, created_at)
            VALUES (?, ?, ?, ?, 0, ?)
            """,
            (otp_id, phone, hash_otp(code), _expires_iso(), now),
        )
        await self.db.commit()
        logger.info(f"OTP created for {phone} (mocked)")
        return code  # returned only for testing; in prod this would SMS it

    async def verify_and_consume(self, phone: str, code: str) -> bool:
        """
        Verify OTP for a phone number.
        Returns True and marks as used if valid. Returns False otherwise.
        """
        code_hash = hash_otp(code)
        now = _now_iso()

        cursor = await self.db.execute(
            """
            SELECT id FROM otp_codes
            WHERE phone = ?
              AND code_hash = ?
              AND used = 0
              AND expires_at > ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (phone, code_hash, now),
        )
        row = await cursor.fetchone()
        if not row:
            return False

        await self.db.execute(
            "UPDATE otp_codes SET used = 1 WHERE id = ?", (row["id"],)
        )
        await self.db.commit()
        return True
