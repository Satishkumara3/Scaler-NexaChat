"""
GroupService — business logic for group management.
Authorization rules enforced here, not in routers.
"""
from typing import List, Optional, Dict, Any
import aiosqlite
from fastapi import HTTPException

from repositories.group_repo import GroupRepository
from repositories.user_repo import UserRepository


class GroupService:
    def __init__(self, db: aiosqlite.Connection, manager=None):
        self._groups = GroupRepository(db)
        self._users = UserRepository(db)
        self.manager = manager

    # ── Create ────────────────────────────────────────────────────────────────

    async def create_group(
        self,
        creator_id: str,
        name: str,
        member_ids: List[str],
        avatar_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        name = name.strip()
        if not name:
            raise HTTPException(400, "Group name cannot be empty")
        if len(name) > 100:
            raise HTTPException(400, "Group name too long (max 100 chars)")

        # Remove duplicates and exclude creator (added separately as admin)
        others = list({m for m in member_ids if m != creator_id})
        if not others:
            raise HTTPException(400, "Group must have at least one other member")

        # Validate all member_ids exist
        for uid in others:
            if not await self._users.exists_by_id(uid):
                raise HTTPException(404, f"User {uid} not found")

        group = await self._groups.create(name, creator_id, others, avatar_url)

        # Broadcast group.created to all initial members
        if self.manager:
            all_ids = [creator_id] + others
            payload = {**group, "members": all_ids}
            await self.manager.broadcast_to_users(all_ids, "group.created", payload)

        return group

    # ── Read ─────────────────────────────────────────────────────────────────

    async def get_group(self, user_id: str, conversation_id: str) -> Dict[str, Any]:
        group = await self._groups.get_by_id(conversation_id)
        if not group:
            raise HTTPException(404, "Group not found")
        if not await self._groups.is_member(conversation_id, user_id):
            raise HTTPException(403, "Not a member of this group")

        members = await self._groups.get_members(conversation_id)
        group["members"] = members
        return group

    async def list_members(
        self, user_id: str, conversation_id: str
    ) -> List[Dict[str, Any]]:
        if not await self._groups.is_member(conversation_id, user_id):
            raise HTTPException(403, "Not a member of this group")
        return await self._groups.get_members(conversation_id)

    # ── Mutations ─────────────────────────────────────────────────────────────

    async def add_member(
        self, requester_id: str, conversation_id: str, new_user_id: str
    ) -> Dict[str, Any]:
        group = await self._groups.get_by_id(conversation_id)
        if not group:
            raise HTTPException(404, "Group not found")

        role = await self._groups.get_role(conversation_id, requester_id)
        if role != "admin":
            raise HTTPException(403, "Only admins can add members")

        if not await self._users.exists_by_id(new_user_id):
            raise HTTPException(404, "User not found")

        added = await self._groups.add_member(conversation_id, new_user_id)
        if not added:
            raise HTTPException(409, "User is already a member")

        user = await self._users.get_by_id(new_user_id)
        payload = {
            "conversation_id": conversation_id,
            "user_id": new_user_id,
            "display_name": user.display_name if user else "",
            "added_by": requester_id,
        }

        if self.manager:
            all_ids = await self._groups.get_member_ids(conversation_id)
            await self.manager.broadcast_to_users(all_ids, "group.member_added", payload)

        return payload

    async def remove_member(
        self, requester_id: str, conversation_id: str, target_user_id: str
    ) -> Dict[str, Any]:
        group = await self._groups.get_by_id(conversation_id)
        if not group:
            raise HTTPException(404, "Group not found")

        role = await self._groups.get_role(conversation_id, requester_id)
        if role != "admin":
            raise HTTPException(403, "Only admins can remove members")

        if target_user_id == requester_id:
            raise HTTPException(400, "Use /leave to remove yourself")

        if not await self._groups.is_member(conversation_id, target_user_id):
            raise HTTPException(404, "User is not a member")

        # Get member ids BEFORE removing (so target also gets the event)
        all_ids = await self._groups.get_member_ids(conversation_id)
        await self._groups.remove_member(conversation_id, target_user_id)

        payload = {
            "conversation_id": conversation_id,
            "user_id": target_user_id,
            "removed_by": requester_id,
        }
        if self.manager:
            await self.manager.broadcast_to_users(all_ids, "group.member_removed", payload)

        return payload

    async def leave_group(
        self, user_id: str, conversation_id: str
    ) -> Dict[str, Any]:
        if not await self._groups.is_member(conversation_id, user_id):
            raise HTTPException(403, "Not a member of this group")

        all_ids = await self._groups.get_member_ids(conversation_id)
        await self._groups.remove_member(conversation_id, user_id)

        payload = {"conversation_id": conversation_id, "user_id": user_id}
        if self.manager:
            await self.manager.broadcast_to_users(all_ids, "group.member_removed", payload)

        return payload

    async def update_group(
        self,
        requester_id: str,
        conversation_id: str,
        name: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        group = await self._groups.get_by_id(conversation_id)
        if not group:
            raise HTTPException(404, "Group not found")

        role = await self._groups.get_role(conversation_id, requester_id)
        if role != "admin":
            raise HTTPException(403, "Only admins can update group info")

        if name is not None:
            name = name.strip()
            if not name:
                raise HTTPException(400, "Group name cannot be empty")

        await self._groups.update_info(conversation_id, name, avatar_url)
        updated = await self._groups.get_by_id(conversation_id)

        if self.manager:
            all_ids = await self._groups.get_member_ids(conversation_id)
            await self.manager.broadcast_to_users(all_ids, "group.updated", updated)

        return updated
