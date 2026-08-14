"""
Contact service — contact list management.
"""

import logging
from typing import Optional

import aiosqlite

from models.contact import Contact
from repositories.contact_repo import ContactRepository
from repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)


class ContactService:
    def __init__(self, db: aiosqlite.Connection):
        self.db = db
        self._contacts = ContactRepository(db)
        self._users = UserRepository(db)

    async def add_contact(
        self,
        owner_id: str,
        phone: str,
        nickname: Optional[str] = None,
    ) -> Contact:
        """
        Add a contact by phone number.
        Raises ValueError if phone not found, is self, or already added.
        """
        # Resolve phone → user
        target = await self._users.get_by_phone(phone)
        if not target:
            raise ValueError("No user found with that phone number.")

        if target.id == owner_id:
            raise ValueError("You cannot add yourself as a contact.")

        if await self._contacts.exists(owner_id, target.id):
            raise ValueError("Contact already added.")

        contact = await self._contacts.add(
            owner_id=owner_id,
            contact_user_id=target.id,
            nickname=nickname,
        )
        contact.user = target
        return contact

    async def get_contacts(self, owner_id: str) -> list[Contact]:
        return await self._contacts.get_contacts_for_user(owner_id)

    async def remove_contact(self, owner_id: str, contact_user_id: str) -> None:
        removed = await self._contacts.remove(owner_id, contact_user_id)
        if not removed:
            raise ValueError("Contact not found.")
