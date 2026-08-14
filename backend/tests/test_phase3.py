import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

@pytest.fixture(scope="session")
def test_db_path_p3(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("testdb_p3")
    return str(tmp / "test_chat_p3.db")

@pytest_asyncio.fixture
async def client(test_db_path_p3, monkeypatch):
    monkeypatch.setenv("DB_PATH", test_db_path_p3)
    
    import config
    config.settings.DB_PATH = test_db_path_p3
    config.get_settings.cache_clear()
    config.settings = config.get_settings()
    
    from database import init_db
    from main import app
    await init_db()
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

from fastapi.testclient import TestClient
@pytest.fixture
def sync_client_p3(test_db_path_p3, monkeypatch):
    monkeypatch.setenv("DB_PATH", test_db_path_p3)
    import config
    config.settings.DB_PATH = test_db_path_p3
    config.get_settings.cache_clear()
    config.settings = config.get_settings()
    from main import app
    with TestClient(app) as test_client:
        yield test_client

async def register_user(client, phone, name):
    await client.post("/api/auth/register/request-otp", json={"phone": phone})
    r = await client.post("/api/auth/register/verify", json={
        "phone": phone, "otp_code": "123456", "display_name": name
    })
    return r.cookies["scaler_session"], r.json()["user"]["id"]

@pytest.mark.asyncio
async def test_create_direct_conversation(client):
    c1, u1 = await register_user(client, "+91-9000003001", "User A")
    c2, u2 = await register_user(client, "+91-9000003002", "User B")
    
    r = await client.post("/api/conversations", json={"user_id": u2}, cookies={"scaler_session": c1})
    assert r.status_code == 200
    data = r.json()
    assert data["conversation"]["type"] == "DIRECT"
    assert data["other_user"]["id"] == u2
    
@pytest.mark.asyncio
async def test_prevent_duplicate_direct(client):
    c1, u1 = await register_user(client, "+91-9000003003", "User C")
    c2, u2 = await register_user(client, "+91-9000003004", "User D")
    
    r1 = await client.post("/api/conversations", json={"user_id": u2}, cookies={"scaler_session": c1})
    cid1 = r1.json()["conversation"]["id"]
    
    # Try again
    r2 = await client.post("/api/conversations", json={"user_id": u2}, cookies={"scaler_session": c1})
    cid2 = r2.json()["conversation"]["id"]
    
    # Try from other side
    r3 = await client.post("/api/conversations", json={"user_id": u1}, cookies={"scaler_session": c2})
    cid3 = r3.json()["conversation"]["id"]
    
    assert cid1 == cid2 == cid3

@pytest.mark.asyncio
async def test_list_conversations(client):
    c1, u1 = await register_user(client, "+91-9000003005", "User E")
    c2, u2 = await register_user(client, "+91-9000003006", "User F")
    
    await client.post("/api/conversations", json={"user_id": u2}, cookies={"scaler_session": c1})
    
    r = await client.get("/api/conversations", cookies={"scaler_session": c1})
    assert r.status_code == 200
    data = r.json()["conversations"]
    assert len(data) == 1
    assert data[0]["other_user"]["id"] == u2

@pytest.mark.asyncio
async def test_send_and_retrieve_messages(client):
    c1, u1 = await register_user(client, "+91-9000003007", "User G")
    c2, u2 = await register_user(client, "+91-9000003008", "User H")
    
    conv_r = await client.post("/api/conversations", json={"user_id": u2}, cookies={"scaler_session": c1})
    cid = conv_r.json()["conversation"]["id"]
    
    # User 1 sends message
    r = await client.post("/api/messages", json={
        "conversation_id": cid,
        "content": "Hello H!"
    }, cookies={"scaler_session": c1})
    assert r.status_code == 200
    assert r.json()["message"]["content"] == "Hello H!"
    
    # User 2 gets messages
    r2 = await client.get(f"/api/messages/{cid}", cookies={"scaler_session": c2})
    assert r2.status_code == 200
    msgs = r2.json()["messages"]
    assert len(msgs) == 1
    assert msgs[0]["content"] == "Hello H!"

@pytest.mark.asyncio
async def test_unauthorized_conversation_access(client):
    c1, u1 = await register_user(client, "+91-9000003009", "User I")
    c2, u2 = await register_user(client, "+91-9000003010", "User J")
    c3, u3 = await register_user(client, "+91-9000003011", "User K")
    
    conv_r = await client.post("/api/conversations", json={"user_id": u2}, cookies={"scaler_session": c1})
    cid = conv_r.json()["conversation"]["id"]
    
    r_bad_details = await client.get(f"/api/conversations/{cid}", cookies={"scaler_session": c3})
    assert r_bad_details.status_code == 403
    
    r_bad_msgs = await client.get(f"/api/messages/{cid}", cookies={"scaler_session": c3})
    assert r_bad_msgs.status_code == 403
    
    r_bad_send = await client.post("/api/messages", json={"conversation_id": cid, "content": "im hacking"}, cookies={"scaler_session": c3})
    assert r_bad_send.status_code == 403

def test_websocket_auth_and_messaging(sync_client_p3):
    """Testing WS. TestClient is synchronous but handles websockets seamlessly."""
    # Register Alice
    sync_client_p3.post("/api/auth/register/request-otp", json={"phone": "+91-9000003111"})
    reg1 = sync_client_p3.post("/api/auth/register/verify", json={"phone": "+91-9000003111", "otp_code": "123456", "display_name": "WSA"})
    token1 = reg1.cookies.get("scaler_session")
    if not token1: token1 = reg1.cookies["scaler_session"]
    uid1 = reg1.json()["user"]["id"]
    
    # Register Bob
    sync_client_p3.post("/api/auth/register/request-otp", json={"phone": "+91-9000003112"})
    reg2 = sync_client_p3.post("/api/auth/register/verify", json={"phone": "+91-9000003112", "otp_code": "123456", "display_name": "WSB"})
    token2 = reg2.cookies.get("scaler_session")
    if not token2: token2 = reg2.cookies["scaler_session"]
    uid2 = reg2.json()["user"]["id"]
    
    # Alice creates conversation with Bob
    conv = sync_client_p3.post("/api/conversations", json={"user_id": uid2}, cookies={"scaler_session": token1})
    cid = conv.json()["conversation"]["id"]

    # Connect WebSocket for Alice
    with sync_client_p3.websocket_connect(f"/ws?token={token1}") as ws1:
        msg1 = ws1.receive_json()
        assert msg1["type"] == "presence.online"
        
        # Connect WebSocket for Bob
        with sync_client_p3.websocket_connect(f"/ws?token={token2}") as ws2:
            ws1.receive_json()

            # Alice sends message via REST
            send = sync_client_p3.post("/api/messages", json={
                "conversation_id": cid,
                "content": "Real-time hello!",
                "message_type": "TEXT"
            }, cookies={"scaler_session": token1})
            
            # Both should receive it eventually
            def wait_for_msg(ws):
                for _ in range(10):
                    m = ws.receive_json()
                    if m.get("type") == "message.new":
                        return m
                return None
                
            data_alice = wait_for_msg(ws1)
            assert data_alice is not None
            assert data_alice["payload"]["content"] == "Real-time hello!"
            
            data_bob = wait_for_msg(ws2)
            assert data_bob is not None
            assert data_bob["payload"]["content"] == "Real-time hello!"
