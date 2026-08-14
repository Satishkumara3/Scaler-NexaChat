"""
Users router — /api/users/* endpoints.

Endpoints:
  GET /api/users               → list all users (dev convenience)
  GET /api/users/{user_id}     → get user by ID
"""

from fastapi import APIRouter, Depends, HTTPException
import aiosqlite

from database import get_db
from services.user_service import UserService
from dependencies import get_current_user
from models.user import User

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", status_code=200)
async def list_users(
    db: aiosqlite.Connection = Depends(get_db),
    _: User = Depends(get_current_user),   # requires auth
):
    """List all registered users (for dev seeding verification)."""
    svc = UserService(db)
    users = await svc.get_all()
    return {"users": [u.to_dict() for u in users]}


@router.get("/{user_id}", status_code=200)
async def get_user(
    user_id: str,
    db: aiosqlite.Connection = Depends(get_db),
    _: User = Depends(get_current_user),
):
    svc = UserService(db)
    user = await svc.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"user": user.to_dict()}
