import aiosqlite
from typing import List, Dict, Any

from repositories.conversation_repo import ConversationRepository
from repositories.user_repo import UserRepository
from models.conversation import Conversation
from fastapi import HTTPException

class ConversationService:
    def __init__(self, db: aiosqlite.Connection):
        self.conv_repo = ConversationRepository(db)
        self.user_repo = UserRepository(db)

    async def get_or_create_direct(self, user1_id: str, user2_id: str) -> dict:
        """Get or create direct conversation between two users."""
        # Ensure user2 exists
        user2 = await self.user_repo.get_by_id(user2_id)
        if not user2:
            raise HTTPException(status_code=404, detail="Target user not found")

        # Check if conversation already exists
        conv = await self.conv_repo.get_direct_between(user1_id, user2_id)
        if not conv:
            # Create a new direct conversation
            conv = await self.conv_repo.create_direct(user1_id, user2_id)
        
        return {
            "conversation": {
                "id": conv.id,
                "type": conv.type,
                "created_at": conv.created_at,
                "updated_at": conv.updated_at
            },
            "other_user": {
                "id": user2.id,
                "phone": user2.phone,
                "display_name": user2.display_name,
                "avatar_url": user2.avatar_url,
                "last_seen": user2.last_seen
            }
        }

    async def list_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """List current user's conversations."""
        return await self.conv_repo.list_for_user(user_id)

    async def get_details(self, user_id: str, conversation_id: str) -> dict:
        """Get conversation details if user is a member."""
        if not await self.conv_repo.is_member(conversation_id, user_id):
            raise HTTPException(status_code=403, detail="Not a member of this conversation")
        
        conv = await self.conv_repo.get_by_id(conversation_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        members = await self.conv_repo.get_members(conversation_id)
        other_user_id = next((m for m in members if m != user_id), user_id)
        other_user = await self.user_repo.get_by_id(other_user_id)

        return {
            "conversation": {
                "id": conv.id,
                "type": conv.type,
                "created_at": conv.created_at,
                "updated_at": conv.updated_at
            },
            "other_user": {
                "id": other_user.id,
                "phone": other_user.phone,
                "display_name": other_user.display_name,
                "avatar_url": other_user.avatar_url,
                "last_seen": other_user.last_seen
            } if other_user else None
        }
