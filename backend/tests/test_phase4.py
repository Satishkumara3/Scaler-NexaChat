"""
Phase 4 Tests: Delivery Receipts, Typing Indicators, Presence
Uses both async httpx client (for REST) and sync TestClient (for WS).
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import sys, os, uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

@pytest.fixture(scope="session")
def test_db_path_p4(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("testdb_p4")
    return str(tmp / "test_chat_p4.db")

@pytest_asyncio.fixture
async def client(test_db_path_p4, monkeypatch):
    monkeypatch.setenv("DB_PATH", test_db_path_p4)
    import config
    config.settings.DB_PATH = test_db_path_p4
    config.get_settings.cache_clear()
    config.settings = config.get_settings()
    from database import init_db
    from main import app
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

import asyncio
from fastapi.testclient import TestClient

@pytest.fixture
def sync_client_p4(test_db_path_p4, monkeypatch):
    monkeypatch.setenv("DB_PATH", test_db_path_p4)
    import config
    config.settings.DB_PATH = test_db_path_p4
    config.get_settings.cache_clear()
    config.settings = config.get_settings()
    from main import app
    # Guarantee tables are created since TestClient triggers lifespan inside its loop
    with TestClient(app) as test_client:
        yield test_client

# ─── Helper ───────────────────────────────────────────────────────────────────
async def register_user(client, name):
    phone = f"+91-{uuid.uuid4().int % 10000000000:010d}"
    await client.post("/api/auth/register/request-otp", json={"phone": phone})
    r = await client.post("/api/auth/register/verify", json={
        "phone": phone, "otp_code": "123456", "display_name": name
    })
    return r.cookies["scaler_session"], r.json()["user"]["id"]

# ─── Test 1: Message status update REST API (DELIVERED) ──────────────────────
@pytest.mark.asyncio
async def test_message_status_delivered(client):
    c1, u1 = await register_user(client, "Alice_D")
    c2, u2 = await register_user(client, "Bob_D")

    # Create conversation
    conv = await client.post("/api/conversations", json={"user_id": u2}, cookies={"scaler_session": c1})
    cid = conv.json()["conversation"]["id"]

    # Alice sends message
    send = await client.post("/api/messages", json={
        "conversation_id": cid, "content": "Hello!"
    }, cookies={"scaler_session": c1})
    msg_id = send.json()["message"]["id"]
    assert send.json()["message"]["status"] == "SENT"

    # Bob marks as DELIVERED
    r = await client.put(f"/api/messages/{msg_id}/status",
                         json={"status": "DELIVERED"},
                         cookies={"scaler_session": c2})
    assert r.status_code == 200

    # Verify persisted
    msgs = await client.get(f"/api/messages/{cid}", cookies={"scaler_session": c2})
    assert msgs.json()["messages"][-1]["status"] == "DELIVERED"


# ─── Test 2: Message status update REST API (READ) ───────────────────────────
@pytest.mark.asyncio
async def test_message_status_read(client):
    c1, u1 = await register_user(client, "Alice_R")
    c2, u2 = await register_user(client, "Bob_R")

    conv = await client.post("/api/conversations", json={"user_id": u2}, cookies={"scaler_session": c1})
    cid = conv.json()["conversation"]["id"]

    send = await client.post("/api/messages", json={
        "conversation_id": cid, "content": "Read me!"
    }, cookies={"scaler_session": c1})
    msg_id = send.json()["message"]["id"]

    # Mark DELIVERED then READ
    await client.put(f"/api/messages/{msg_id}/status",
                     json={"status": "DELIVERED"},
                     cookies={"scaler_session": c2})
    r = await client.put(f"/api/messages/{msg_id}/status",
                         json={"status": "READ"},
                         cookies={"scaler_session": c2})
    assert r.status_code == 200

    msgs = await client.get(f"/api/messages/{cid}", cookies={"scaler_session": c1})
    assert msgs.json()["messages"][-1]["status"] == "READ"


# ─── Test 3: Cannot mark own message as delivered ────────────────────────────
@pytest.mark.asyncio
async def test_cannot_mark_own_message(client):
    c1, u1 = await register_user(client, "Alice_Own")
    c2, u2 = await register_user(client, "Bob_Own")

    conv = await client.post("/api/conversations", json={"user_id": u2}, cookies={"scaler_session": c1})
    cid = conv.json()["conversation"]["id"]

    send = await client.post("/api/messages", json={
        "conversation_id": cid, "content": "Self mark"
    }, cookies={"scaler_session": c1})
    msg_id = send.json()["message"]["id"]

    # Alice tries to mark her own message DELIVERED — should fail
    r = await client.put(f"/api/messages/{msg_id}/status",
                         json={"status": "DELIVERED"},
                         cookies={"scaler_session": c1})
    assert r.status_code == 403


# ─── Test 4: Non-member cannot update status ────────────────────────────────
@pytest.mark.asyncio
async def test_nonmember_cannot_update_status(client):
    c1, u1 = await register_user(client, "Alice_NM")
    c2, u2 = await register_user(client, "Bob_NM")
    c3, u3 = await register_user(client, "Charlie_NM")

    conv = await client.post("/api/conversations", json={"user_id": u2}, cookies={"scaler_session": c1})
    cid = conv.json()["conversation"]["id"]

    send = await client.post("/api/messages", json={
        "conversation_id": cid, "content": "Private"
    }, cookies={"scaler_session": c1})
    msg_id = send.json()["message"]["id"]

    # Charlie (non-member) tries to update
    r = await client.put(f"/api/messages/{msg_id}/status",
                         json={"status": "READ"},
                         cookies={"scaler_session": c3})
    assert r.status_code == 403


def test_ws_presence_online(sync_client_p4):
    """Single-user presence: connecting broadcasts presence.online."""
    phone = f"+91-{uuid.uuid4().int % 10000000000:010d}"
    sync_client_p4.post("/api/auth/register/request-otp", json={"phone": phone})
    reg = sync_client_p4.post("/api/auth/register/verify", json={"phone": phone, "otp_code": "123456", "display_name": "PresTest"})
    token = reg.cookies.get("scaler_session")
    if not token:
        # Check set-cookie header if cookies dict empty
        token = reg.cookies["scaler_session"]
    uid = reg.json()["user"]["id"]

    with sync_client_p4.websocket_connect(f"/ws?token={token}") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "presence.online"
        assert msg["payload"]["user_id"] == uid


def test_ws_typing_indicators(sync_client_p4):
    """Typing indicators are dispatched via WebSocket."""
    phone1 = f"+91-{uuid.uuid4().int % 10000000000:010d}"
    phone2 = f"+91-{uuid.uuid4().int % 10000000000:010d}"

    sync_client_p4.post("/api/auth/register/request-otp", json={"phone": phone1})
    reg1 = sync_client_p4.post("/api/auth/register/verify", json={"phone": phone1, "otp_code": "123456", "display_name": "TypeA"})
    t1 = reg1.cookies["scaler_session"]

    sync_client_p4.post("/api/auth/register/request-otp", json={"phone": phone2})
    reg2 = sync_client_p4.post("/api/auth/register/verify", json={"phone": phone2, "otp_code": "123456", "display_name": "TypeB"})
    t2 = reg2.cookies["scaler_session"]
    u1 = reg1.json()["user"]["id"]
    u2 = reg2.json()["user"]["id"]

    # Create conversation via REST before opening WS
    conv = sync_client_p4.post("/api/conversations", json={"user_id": u2}, cookies={"scaler_session": t1})
    cid = conv.json()["conversation"]["id"]

    def drain_until(ws, ev_type, max_msgs=15):
        for _ in range(max_msgs):
            msg = ws.receive_json()
            if msg.get("type") == ev_type:
                return msg
        raise Exception(f"Did not receive {ev_type}")

    with sync_client_p4.websocket_connect(f"/ws?token={t1}") as ws_a:
        drain_until(ws_a, "presence.online")

        with sync_client_p4.websocket_connect(f"/ws?token={t2}") as ws_b:
            drain_until(ws_a, "presence.online")
            drain_until(ws_b, "presence.online")

            # Alice sends typing start
            ws_a.send_json({
                "type": "client.typing.start",
                "payload": {"conversation_id": cid}
            })

            # Both should receive typing.start
            ta = drain_until(ws_a, "typing.start")
            assert ta["payload"]["user_id"] == u1
            tb = drain_until(ws_b, "typing.start")
            assert tb["payload"]["user_id"] == u1


def test_ws_message_delivery_receipt(sync_client_p4):
    """Full flow: send message via REST, mark DELIVERED via REST, verify WS events."""
    phone1 = f"+91-{uuid.uuid4().int % 10000000000:010d}"
    phone2 = f"+91-{uuid.uuid4().int % 10000000000:010d}"

    sync_client_p4.post("/api/auth/register/request-otp", json={"phone": phone1})
    reg1 = sync_client_p4.post("/api/auth/register/verify", json={"phone": phone1, "otp_code": "123456", "display_name": "WsDelA"})
    t1 = reg1.cookies["scaler_session"]
    u1 = reg1.json()["user"]["id"]

    sync_client_p4.post("/api/auth/register/request-otp", json={"phone": phone2})
    reg2 = sync_client_p4.post("/api/auth/register/verify", json={"phone": phone2, "otp_code": "123456", "display_name": "WsDelB"})
    t2 = reg2.cookies["scaler_session"]
    u2 = reg2.json()["user"]["id"]

    # Create conversation
    conv = sync_client_p4.post("/api/conversations", json={"user_id": u2}, cookies={"scaler_session": t1})
    cid = conv.json()["conversation"]["id"]

    def drain_until(ws, ev_type, max_msgs=15):
        for _ in range(max_msgs):
            msg = ws.receive_json()
            if msg.get("type") == ev_type:
                return msg
        raise Exception(f"Did not receive {ev_type}")

    with sync_client_p4.websocket_connect(f"/ws?token={t1}") as ws_a:
        drain_until(ws_a, "presence.online")

        with sync_client_p4.websocket_connect(f"/ws?token={t2}") as ws_b:
            drain_until(ws_a, "presence.online")
            drain_until(ws_b, "presence.online")

            # Send message via REST
            send = sync_client_p4.post("/api/messages", json={
                "conversation_id": cid, "content": "WS Receipt Test"
            }, cookies={"scaler_session": t1})
            msg_id = send.json()["message"]["id"]

            # Both receive message.new
            drain_until(ws_a, "message.new")
            drain_until(ws_b, "message.new")

            # Bob marks DELIVERED via REST
            sync_client_p4.put(f"/api/messages/{msg_id}/status",
                            json={"status": "DELIVERED"},
                            cookies={"scaler_session": t2})

            # Alice should get message.delivered
            ev = drain_until(ws_a, "message.delivered")
            assert ev["payload"]["message_id"] == msg_id
            assert ev["payload"]["status"] == "DELIVERED"
