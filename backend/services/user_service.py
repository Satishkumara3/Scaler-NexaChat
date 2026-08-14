"""
User service — profile management.
"""

import logging
from typing import Optional

import aiosqlite

from models.user import User
from repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, db: aiosqlite.Connection):
        self.db = db
        self._users = UserRepository(db)

    async def get_by_id(self, user_id: str) -> Optional[User]:
        return await self._users.get_by_id(user_id)

    async def get_all(self) -> list[User]:
        return await self._users.get_all()

    async def update_profile(
        self,
        user_id: str,
        display_name: Optional[str] = None,
        about: Optional[str] = None,
    ) -> Optional[User]:
        return await self._users.update_profile(
            user_id=user_id,
            display_name=display_name,
            about=about,
        )

    async def find_by_phone(self, phone: str) -> Optional[User]:
        return await self._users.get_by_phone(phone)
