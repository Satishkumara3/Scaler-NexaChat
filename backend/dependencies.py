"""
Auth dependency — reusable FastAPI dependency for authenticating requests.

Usage in a router:
    from dependencies import get_current_user
    
    @router.get("/me")
    async def me(user: User = Depends(get_current_user)):
        return user.to_dict()
"""

from fastapi import Depends, HTTPException, Cookie, status
from typing import Optional
import aiosqlite

from database import get_db
from models.user import User
from services.auth_service import AuthService

SESSION_COOKIE = "scaler_session"


async def get_current_user(
    db: aiosqlite.Connection = Depends(get_db),
    scaler_session: Optional[str] = Cookie(default=None),
) -> User:
    """
    FastAPI dependency that validates the HttpOnly session cookie.
    Raises 401 if missing or invalid.
    """
    if not scaler_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    auth = AuthService(db)
    user = await auth.get_current_user(scaler_session)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid. Please log in again.",
        )
    return user


async def get_optional_user(
    db: aiosqlite.Connection = Depends(get_db),
    scaler_session: Optional[str] = Cookie(default=None),
) -> Optional[User]:
    """Like get_current_user but returns None instead of raising 401."""
    if not scaler_session:
        return None
    auth = AuthService(db)
    return await auth.get_current_user(scaler_session)
