from dataclasses import dataclass
from typing import Optional

@dataclass
class Conversation:
    id: str
    type: str  # DIRECT or GROUP
    created_at: str
    updated_at: str

@dataclass
class ConversationMember:
    conversation_id: str
    user_id: str
    role: str = "member"   # admin | member
    joined_at: str = ""

@dataclass
class GroupInfo:
    conversation_id: str
    name: str
    created_by: str
    created_at: str
    avatar_url: Optional[str] = None
