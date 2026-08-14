"""
User model — typed dataclass wrapping a DB row.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    id: str
    phone: str
    display_name: str
    avatar_url: Optional[str]
    about: str
    created_at: str
    last_seen: Optional[str]

    @classmethod
    def from_row(cls, row) -> "User":
        return cls(
            id=row["id"],
            phone=row["phone"],
            display_name=row["display_name"],
            avatar_url=row["avatar_url"],
            about=row["about"],
            created_at=row["created_at"],
            last_seen=row["last_seen"],
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "phone": self.phone,
            "display_name": self.display_name,
            "avatar_url": self.avatar_url,
            "about": self.about,
            "created_at": self.created_at,
            "last_seen": self.last_seen,
        }
