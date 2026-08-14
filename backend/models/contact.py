"""
Contact model — typed dataclass wrapping a DB row.
"""

from dataclasses import dataclass
from typing import Optional
from models.user import User


@dataclass
class Contact:
    id: str
    owner_id: str
    contact_user_id: str
    nickname: Optional[str]
    created_at: str
    user: Optional[User] = None  # joined eagerly when needed

    @classmethod
    def from_row(cls, row) -> "Contact":
        return cls(
            id=row["id"],
            owner_id=row["owner_id"],
            contact_user_id=row["contact_user_id"],
            nickname=row["nickname"],
            created_at=row["created_at"],
        )

    def to_dict(self) -> dict:
        d: dict = {
            "id": self.id,
            "owner_id": self.owner_id,
            "contact_user_id": self.contact_user_id,
            "nickname": self.nickname,
            "created_at": self.created_at,
        }
        if self.user:
            d["user"] = self.user.to_dict()
        return d
