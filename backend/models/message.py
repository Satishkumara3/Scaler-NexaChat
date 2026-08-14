from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class Reaction:
    id: str
    message_id: str
    user_id: str
    emoji: str
    created_at: str

@dataclass
class ReplyPreview:
    """Lightweight reference included inside a reply message."""
    id: str
    sender_id: str
    sender_name: str
    content: str          # short preview (first 80 chars)

@dataclass
class Attachment:
    id: str
    message_id: str
    original_filename: str
    stored_filename: str
    mime_type: str
    file_size: int
    created_at: str

@dataclass
class Message:
    id: str
    conversation_id: str
    sender_id: str
    content: str
    message_type: str           # TEXT, IMAGE, FILE
    status: str                 # SENT, DELIVERED, READ
    created_at: str
    updated_at: str
    reply_to_message_id: Optional[str] = None
    reply_preview: Optional[ReplyPreview] = None
    attachment: Optional[Attachment] = None
    reactions: List[Reaction] = field(default_factory=list)
