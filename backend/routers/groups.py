import aiosqlite
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, constr
from typing import List, Optional

from dependencies import get_db, get_current_user
from services.group_service import GroupService
from models.user import User
from routers.ws import manager

router = APIRouter(prefix="/api/groups", tags=["Groups"])

class CreateGroupRequest(BaseModel):
    name: str
    member_ids: List[str]
    avatar_url: Optional[str] = None

@router.post("")
async def create_group(
    req: CreateGroupRequest,
    current_user: User = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db)
):
    svc = GroupService(db, manager=manager)
    group = await svc.create_group(current_user.id, req.name, req.member_ids, req.avatar_url)
    return {"group": group}

@router.get("/{conversation_id}")
async def get_group(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db)
):
    svc = GroupService(db, manager=manager)
    group = await svc.get_group(current_user.id, conversation_id)
    return {"group": group}

class AddMemberRequest(BaseModel):
    user_id: str

@router.post("/{conversation_id}/members")
async def add_group_member(
    conversation_id: str,
    req: AddMemberRequest,
    current_user: User = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db)
):
    svc = GroupService(db, manager=manager)
    res = await svc.add_member(current_user.id, conversation_id, req.user_id)
    return {"message": "Member added", "member": res}

@router.delete("/{conversation_id}/members/{user_id}")
async def remove_group_member(
    conversation_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db)
):
    svc = GroupService(db, manager=manager)
    res = await svc.remove_member(current_user.id, conversation_id, user_id)
    return {"message": "Member removed", "member": res}

@router.post("/{conversation_id}/leave")
async def leave_group(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db)
):
    svc = GroupService(db, manager=manager)
    res = await svc.leave_group(current_user.id, conversation_id)
    return {"message": "Left group", "member": res}

class UpdateGroupRequest(BaseModel):
    name: Optional[str] = None
    avatar_url: Optional[str] = None

@router.put("/{conversation_id}")
async def update_group(
    conversation_id: str,
    req: UpdateGroupRequest,
    current_user: User = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db)
):
    svc = GroupService(db, manager=manager)
    res = await svc.update_group(current_user.id, conversation_id, req.name, req.avatar_url)
    return {"message": "Group updated", "group": res}
