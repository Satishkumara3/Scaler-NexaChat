"""
Auth service — OTP-based registration and login flows.

Flow:
  1. request_otp(phone)   → creates OTP row (mocked as '123456')
  2. register_verify(phone, otp, display_name)
       → verify OTP → create user → create session → return (user, raw_token)
  3. login_verify(phone, otp)
       → verify OTP → get user → create session → return (user, raw_token)
  4. logout(raw_token) → delete session row
  5. get_current_user(raw_token) → validate session → return User or None
"""

import logging
from typing import Optional

import aiosqlite

from models.user import User
from repositories.user_repo import UserRepository
from repositories.session_repo import SessionRepository
from repositories.otp_repo import OtpRepository

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, db: aiosqlite.Connection):
        self.db = db
        self._users = UserRepository(db)
        self._sessions = SessionRepository(db)
        self._otps = OtpRepository(db)

    async def request_otp(self, phone: str) -> None:
        """Issue an OTP for the given phone (always mocked to '123456' in dev)."""
        await self._otps.create(phone)
        logger.info(f"OTP requested for {phone}")

    async def register_verify(
        self,
        phone: str,
        otp_code: str,
        display_name: str,
        about: str = "Hey there! I am using Scaler Chat.",
    ) -> tuple[User, str]:
        """
        Verify OTP, create new user, create session.
        Raises ValueError with a user-friendly message on failure.
        """
        # 1. Phone must not already be registered
        if await self._users.exists_by_phone(phone):
            raise ValueError("Phone number is already registered. Please log in instead.")

        # 2. Verify OTP
        valid = await self._otps.verify_and_consume(phone, otp_code)
        if not valid:
            raise ValueError("Invalid or expired OTP code.")

        # 3. Create user
        user = await self._users.create(phone=phone, display_name=display_name, about=about)

        # 4. Create session
        raw_token, _ = await self._sessions.create(user.id)
        logger.info(f"Registered new user {user.id} ({phone})")
        return user, raw_token

    async def login_verify(self, phone: str, otp_code: str) -> tuple[User, str]:
        """
        Verify OTP, look up existing user, create session.
        Raises ValueError on failure.
        """
        # 1. User must exist
        user = await self._users.get_by_phone(phone)
        if not user:
            raise ValueError("Phone number not registered. Please register first.")

        # 2. Verify OTP
        valid = await self._otps.verify_and_consume(phone, otp_code)
        if not valid:
            raise ValueError("Invalid or expired OTP code.")

        # 3. Update last_seen
        await self._users.update_last_seen(user.id)

        # 4. Create session
        raw_token, _ = await self._sessions.create(user.id)
        logger.info(f"Logged in user {user.id} ({phone})")
        return user, raw_token

    async def logout(self, raw_token: str) -> None:
        """Invalidate a session."""
        await self._sessions.delete(raw_token)
        logger.info("Session deleted")

    async def get_current_user(self, raw_token: str) -> Optional[User]:
        """
        Validate raw_token. Returns the User if session is valid, else None.
        Also touches last_used_at on valid sessions.
        """
        if not raw_token:
            return None

        is_valid = await self._sessions.is_valid(raw_token)
        if not is_valid:
            return None

        session = await self._sessions.get_by_token(raw_token)
        if not session:
            return None

        await self._sessions.touch(raw_token)
        user = await self._users.get_by_id(session.user_id)
        return user
