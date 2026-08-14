"""
Contacts router — /api/contacts/* endpoints.

Endpoints:
  GET    /api/contacts              → list current user's contacts
  POST   /api/contacts              → add contact by phone
  DELETE /api/contacts/{user_id}    → remove contact
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import aiosqlite

from database import get_db
from services.contact_service import ContactService
from dependencies import get_current_user
from models.user import User

router = APIRouter(prefix="/api/contacts", tags=["contacts"])


class AddContactBody(BaseModel):
    phone: str
    nickname: Optional[str] = None


@router.get("", status_code=200)
async def get_contacts(
    db: aiosqlite.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = ContactService(db)
    contacts = await svc.get_contacts(current_user.id)
    return {"contacts": [c.to_dict() for c in contacts]}


@router.post("", status_code=201)
async def add_contact(
    body: AddContactBody,
    db: aiosqlite.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = ContactService(db)
    try:
        contact = await svc.add_contact(
            owner_id=current_user.id,
            phone=body.phone,
            nickname=body.nickname,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"contact": contact.to_dict()}


@router.delete("/{contact_user_id}", status_code=200)
async def remove_contact(
    contact_user_id: str,
    db: aiosqlite.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = ContactService(db)
    try:
        await svc.remove_contact(current_user.id, contact_user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"message": "Contact removed."}
