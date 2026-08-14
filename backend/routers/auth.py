"""
Auth router — /api/auth/* endpoints.

Endpoints:
  POST /api/auth/register/request-otp   → issue OTP for new phone
  POST /api/auth/register/verify         → verify OTP + create user + session
  POST /api/auth/login/request-otp       → issue OTP for existing phone
  POST /api/auth/login/verify            → verify OTP + create session
  POST /api/auth/logout                  → delete session
  GET  /api/auth/me                      → return current user
  PUT  /api/auth/me                      → update profile (display_name, about)
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, Cookie, status
from pydantic import BaseModel, field_validator
import aiosqlite

from database import get_db
from services.auth_service import AuthService
from services.user_service import UserService
from dependencies import get_current_user, SESSION_COOKIE
from models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])

SESSION_MAX_AGE = 7 * 24 * 60 * 60  # 7 days in seconds


# ── Request / Response schemas ────────────────────────────────────────────────

class RequestOtpBody(BaseModel):
    phone: str

    @field_validator("phone")
    @classmethod
    def phone_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Phone number is required.")
        return v


class RegisterVerifyBody(BaseModel):
    phone: str
    otp_code: str
    display_name: str

    @field_validator("display_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Display name is required.")
        if len(v) < 2:
            raise ValueError("Display name must be at least 2 characters.")
        return v


class LoginVerifyBody(BaseModel):
    phone: str
    otp_code: str


class UpdateProfileBody(BaseModel):
    display_name: Optional[str] = None
    about: Optional[str] = None


def _set_session_cookie(response: Response, raw_token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE,
        value=raw_token,
        httponly=True,
        samesite="lax",
        secure=False,       # set True in production with HTTPS
        max_age=SESSION_MAX_AGE,
        path="/",
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/register/request-otp", status_code=200)
async def register_request_otp(
    body: RequestOtpBody,
    db: aiosqlite.Connection = Depends(get_db),
):
    """
    Step 1 of registration: send OTP to phone.
    In dev mode the OTP is always 123456.
    """
    auth = AuthService(db)
    try:
        await auth.request_otp(body.phone)
    except Exception as e:
        logger.error(f"OTP request error: {e}")
        raise HTTPException(status_code=500, detail="Failed to send OTP. Try again.")

    return {"message": "OTP sent. Use 123456 in development."}


@router.post("/register/verify", status_code=201)
async def register_verify(
    body: RegisterVerifyBody,
    response: Response,
    db: aiosqlite.Connection = Depends(get_db),
):
    """
    Step 2 of registration: verify OTP, create user, set session cookie.
    """
    auth = AuthService(db)
    try:
        user, raw_token = await auth.register_verify(
            phone=body.phone,
            otp_code=body.otp_code,
            display_name=body.display_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    _set_session_cookie(response, raw_token)
    return {"user": user.to_dict(), "message": "Registration successful."}


@router.post("/login/request-otp", status_code=200)
async def login_request_otp(
    body: RequestOtpBody,
    db: aiosqlite.Connection = Depends(get_db),
):
    """Step 1 of login: send OTP to phone."""
    auth = AuthService(db)
    try:
        await auth.request_otp(body.phone)
    except Exception as e:
        logger.error(f"OTP request error: {e}")
        raise HTTPException(status_code=500, detail="Failed to send OTP. Try again.")

    return {"message": "OTP sent. Use 123456 in development."}


@router.post("/login/verify", status_code=200)
async def login_verify(
    body: LoginVerifyBody,
    response: Response,
    db: aiosqlite.Connection = Depends(get_db),
):
    """Step 2 of login: verify OTP, create session, set cookie."""
    auth = AuthService(db)
    try:
        user, raw_token = await auth.login_verify(
            phone=body.phone,
            otp_code=body.otp_code,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    _set_session_cookie(response, raw_token)
    return {"user": user.to_dict(), "message": "Login successful."}


@router.post("/logout", status_code=200)
async def logout(
    response: Response,
    db: aiosqlite.Connection = Depends(get_db),
    scaler_session: Optional[str] = Cookie(default=None),
):
    """Delete session and clear cookie."""
    if scaler_session:
        auth = AuthService(db)
        await auth.logout(scaler_session)

    response.delete_cookie(key=SESSION_COOKIE, path="/")
    return {"message": "Logged out successfully."}


@router.get("/me", status_code=200)
async def me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user."""
    return {"user": current_user.to_dict()}


@router.put("/me", status_code=200)
async def update_me(
    body: UpdateProfileBody,
    db: aiosqlite.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update display_name and/or about for the current user."""
    if body.display_name is None and body.about is None:
        raise HTTPException(status_code=400, detail="Nothing to update.")

    svc = UserService(db)
    updated = await svc.update_profile(
        user_id=current_user.id,
        display_name=body.display_name,
        about=body.about,
    )
    return {"user": updated.to_dict()}
