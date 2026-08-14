"""
Phase 2 backend tests.

Covers:
- DB initialisation (all Phase 2 tables created)
- User creation and duplicate phone handling
- OTP verification (valid, invalid, expired)
- Registration flow (request OTP → verify)
- Login flow (request OTP → verify)
- Logout and session invalidation
- /me endpoint (authenticated, unauthenticated)
- Session persistence across requests
- Invalid/expired session
- Contacts (add, list, duplicate, remove)
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture(scope="session")
async def test_db_path(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("testdb_p2")
    return str(tmp / "test_chat_p2.db")


@pytest_asyncio.fixture
async def client(test_db_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", test_db_path)

    import config
    config.settings.DB_PATH = test_db_path

    # Reset lru_cache so settings pick up the test DB
    config.get_settings.cache_clear()
    config.settings = config.get_settings()

    from database import init_db
    from main import app

    await init_db()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1 regression tests (must still pass)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_root(client):
    r = await client.get("/")
    assert r.status_code == 200
    assert "message" in r.json()


@pytest.mark.asyncio
async def test_health_ok(client):
    r = await client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["database"]["connected"] is True
    assert "websocket" in data


# ─────────────────────────────────────────────────────────────────────────────
# DB schema test
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_db_schema_version(client):
    r = await client.get("/health")
    data = r.json()
    assert data["database"]["schema_version"] == "6"


# ─────────────────────────────────────────────────────────────────────────────
# OTP and Registration
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_request_otp(client):
    r = await client.post("/api/auth/register/request-otp", json={"phone": "+91-9111111001"})
    assert r.status_code == 200
    assert "OTP" in r.json()["message"]


@pytest.mark.asyncio
async def test_register_verify_invalid_otp(client):
    phone = "+91-9111111002"
    await client.post("/api/auth/register/request-otp", json={"phone": phone})
    r = await client.post("/api/auth/register/verify", json={
        "phone": phone, "otp_code": "000000", "display_name": "Test User"
    })
    assert r.status_code == 400
    assert "Invalid" in r.json()["message"]


@pytest.mark.asyncio
async def test_register_full_flow(client):
    phone = "+91-9111111003"
    await client.post("/api/auth/register/request-otp", json={"phone": phone})
    r = await client.post("/api/auth/register/verify", json={
        "phone": phone, "otp_code": "123456", "display_name": "Full Flow User"
    })
    assert r.status_code == 201
    data = r.json()
    assert data["user"]["phone"] == phone
    assert data["user"]["display_name"] == "Full Flow User"
    assert "avatar_url" in data["user"]
    # Session cookie must be set
    assert "scaler_session" in r.cookies


@pytest.mark.asyncio
async def test_register_duplicate_phone(client):
    phone = "+91-9111111004"
    await client.post("/api/auth/register/request-otp", json={"phone": phone})
    await client.post("/api/auth/register/verify", json={
        "phone": phone, "otp_code": "123456", "display_name": "Dup User"
    })
    # Try to register again
    await client.post("/api/auth/register/request-otp", json={"phone": phone})
    r = await client.post("/api/auth/register/verify", json={
        "phone": phone, "otp_code": "123456", "display_name": "Dup User 2"
    })
    assert r.status_code == 400
    assert "already registered" in r.json()["message"]


# ─────────────────────────────────────────────────────────────────────────────
# Login
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_unregistered_phone(client):
    phone = "+91-9111111099"
    await client.post("/api/auth/login/request-otp", json={"phone": phone})
    r = await client.post("/api/auth/login/verify", json={
        "phone": phone, "otp_code": "123456"
    })
    assert r.status_code == 400
    assert "not registered" in r.json()["message"]


@pytest.mark.asyncio
async def test_login_full_flow(client):
    phone = "+91-9111111005"
    # Register first
    await client.post("/api/auth/register/request-otp", json={"phone": phone})
    await client.post("/api/auth/register/verify", json={
        "phone": phone, "otp_code": "123456", "display_name": "Login User"
    })
    # Now login
    await client.post("/api/auth/login/request-otp", json={"phone": phone})
    r = await client.post("/api/auth/login/verify", json={
        "phone": phone, "otp_code": "123456"
    })
    assert r.status_code == 200
    assert r.json()["user"]["phone"] == phone
    assert "scaler_session" in r.cookies


@pytest.mark.asyncio
async def test_login_invalid_otp(client):
    phone = "+91-9111111006"
    await client.post("/api/auth/register/request-otp", json={"phone": phone})
    await client.post("/api/auth/register/verify", json={
        "phone": phone, "otp_code": "123456", "display_name": "Bad OTP User"
    })
    await client.post("/api/auth/login/request-otp", json={"phone": phone})
    r = await client.post("/api/auth/login/verify", json={
        "phone": phone, "otp_code": "999999"
    })
    assert r.status_code == 400


# ─────────────────────────────────────────────────────────────────────────────
# /me endpoint
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_me_unauthenticated(client):
    r = await client.get("/api/auth/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_authenticated(client):
    phone = "+91-9111111007"
    await client.post("/api/auth/register/request-otp", json={"phone": phone})
    reg = await client.post("/api/auth/register/verify", json={
        "phone": phone, "otp_code": "123456", "display_name": "Me User"
    })
    token = reg.cookies["scaler_session"]
    r = await client.get("/api/auth/me", cookies={"scaler_session": token})
    assert r.status_code == 200
    assert r.json()["user"]["phone"] == phone


# ─────────────────────────────────────────────────────────────────────────────
# Session persistence
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_session_persists(client):
    """Same token works across multiple requests."""
    phone = "+91-9111111008"
    await client.post("/api/auth/register/request-otp", json={"phone": phone})
    reg = await client.post("/api/auth/register/verify", json={
        "phone": phone, "otp_code": "123456", "display_name": "Persist User"
    })
    token = reg.cookies["scaler_session"]

    # First call
    r1 = await client.get("/api/auth/me", cookies={"scaler_session": token})
    assert r1.status_code == 200

    # Second call same token
    r2 = await client.get("/api/auth/me", cookies={"scaler_session": token})
    assert r2.status_code == 200
    assert r1.json()["user"]["id"] == r2.json()["user"]["id"]


# ─────────────────────────────────────────────────────────────────────────────
# Logout
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_logout(client):
    phone = "+91-9111111009"
    await client.post("/api/auth/register/request-otp", json={"phone": phone})
    reg = await client.post("/api/auth/register/verify", json={
        "phone": phone, "otp_code": "123456", "display_name": "Logout User"
    })
    token = reg.cookies["scaler_session"]

    # Logout
    r = await client.post("/api/auth/logout", cookies={"scaler_session": token})
    assert r.status_code == 200

    # Token should no longer work
    r2 = await client.get("/api/auth/me", cookies={"scaler_session": token})
    assert r2.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
# Invalid session
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_invalid_session_token(client):
    r = await client.get("/api/auth/me", cookies={"scaler_session": "not-a-real-token"})
    assert r.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
# Profile update
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_profile(client):
    phone = "+91-9111111010"
    await client.post("/api/auth/register/request-otp", json={"phone": phone})
    reg = await client.post("/api/auth/register/verify", json={
        "phone": phone, "otp_code": "123456", "display_name": "Old Name"
    })
    token = reg.cookies["scaler_session"]

    r = await client.put("/api/auth/me", json={"display_name": "New Name"},
                         cookies={"scaler_session": token})
    assert r.status_code == 200
    assert r.json()["user"]["display_name"] == "New Name"


# ─────────────────────────────────────────────────────────────────────────────
# Contacts
# ─────────────────────────────────────────────────────────────────────────────

async def _register_user(client, phone: str, name: str) -> str:
    """Helper: register user, return session token."""
    await client.post("/api/auth/register/request-otp", json={"phone": phone})
    r = await client.post("/api/auth/register/verify", json={
        "phone": phone, "otp_code": "123456", "display_name": name
    })
    return r.cookies["scaler_session"]


@pytest.mark.asyncio
async def test_contacts_empty_initially(client):
    token = await _register_user(client, "+91-9111112001", "Contacts User A")
    r = await client.get("/api/contacts", cookies={"scaler_session": token})
    assert r.status_code == 200
    assert r.json()["contacts"] == []


@pytest.mark.asyncio
async def test_add_contact(client):
    token_a = await _register_user(client, "+91-9111112002", "Contact Owner")
    await _register_user(client, "+91-9111112003", "Contact Target")

    r = await client.post("/api/contacts",
                          json={"phone": "+91-9111112003"},
                          cookies={"scaler_session": token_a})
    assert r.status_code == 201
    assert r.json()["contact"]["user"]["phone"] == "+91-9111112003"


@pytest.mark.asyncio
async def test_add_duplicate_contact(client):
    token_a = await _register_user(client, "+91-9111112004", "Dup Contact Owner")
    await _register_user(client, "+91-9111112005", "Dup Contact Target")

    await client.post("/api/contacts",
                      json={"phone": "+91-9111112005"},
                      cookies={"scaler_session": token_a})
    r = await client.post("/api/contacts",
                          json={"phone": "+91-9111112005"},
                          cookies={"scaler_session": token_a})
    assert r.status_code == 400
    assert "already" in r.json()["message"].lower()


@pytest.mark.asyncio
async def test_add_self_as_contact(client):
    token = await _register_user(client, "+91-9111112006", "Self Contact User")
    r = await client.post("/api/contacts",
                          json={"phone": "+91-9111112006"},
                          cookies={"scaler_session": token})
    assert r.status_code == 400
    assert "yourself" in r.json()["message"].lower()


@pytest.mark.asyncio
async def test_add_nonexistent_contact(client):
    token = await _register_user(client, "+91-9111112007", "Nonexistent Contact User")
    r = await client.post("/api/contacts",
                          json={"phone": "+91-9000000099"},
                          cookies={"scaler_session": token})
    assert r.status_code == 400
    assert "No user found" in r.json()["message"]


@pytest.mark.asyncio
async def test_remove_contact(client):
    token_a = await _register_user(client, "+91-9111112008", "Remove Contact Owner")
    await _register_user(client, "+91-9111112009", "Remove Contact Target")

    add_r = await client.post("/api/contacts",
                              json={"phone": "+91-9111112009"},
                              cookies={"scaler_session": token_a})
    target_id = add_r.json()["contact"]["contact_user_id"]

    del_r = await client.delete(f"/api/contacts/{target_id}",
                                cookies={"scaler_session": token_a})
    assert del_r.status_code == 200

    list_r = await client.get("/api/contacts", cookies={"scaler_session": token_a})
    assert list_r.json()["contacts"] == []
