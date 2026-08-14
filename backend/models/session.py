"""
Session model — typed dataclass wrapping a DB row.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Session:
    id: str
    user_id: str
    token_hash: str
    expires_at: str
    created_at: str
    last_used_at: Optional[str]

    @classmethod
    def from_row(cls, row) -> "Session":
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            token_hash=row["token_hash"],
            expires_at=row["expires_at"],
            created_at=row["created_at"],
            last_used_at=row["last_used_at"],
        )
