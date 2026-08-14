import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import sys, os, uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

@pytest_asyncio.fixture(scope="session")
async def test_db_path_p5(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("testdb_p5")
    return str(tmp / "test_chat_p5.db")

@pytest_asyncio.fixture
async def client(test_db_path_p5, monkeypatch):
    monkeypatch.setenv("DB_PATH", test_db_path_p5)
    import config
    config.settings.DB_PATH = test_db_path_p5
    config.get_settings.cache_clear()
    config.settings = config.get_settings()
    from database import init_db
    from main import app
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

async def register_user(client, name):
    phone = f"+91-{uuid.uuid4().int % 10000000000:010d}"
    await client.post("/api/auth/register/request-otp", json={"phone": phone})
    r = await client.post("/api/auth/register/verify", json={
        "phone": phone, "otp_code": "123456", "display_name": name
    })
    return r.cookies["scaler_session"], r.json()["user"]["id"]

@pytest.mark.asyncio
async def test_create_and_get_group(client):
    c1, u1 = await register_user(client, "Alice")
    c2, u2 = await register_user(client, "Bob")
    c3, u3 = await register_user(client, "Charlie")

    # Create Group
    res_create = await client.post(
        "/api/groups",
        json={"name": "Test Group 1", "member_ids": [u2, u3]},
        cookies={"scaler_session": c1}
    )
    assert res_create.status_code == 200
    cid = res_create.json()["group"]["id"]
    assert res_create.json()["group"]["name"] == "Test Group 1"

    # Get Group Details
    res_get = await client.get(f"/api/groups/{cid}", cookies={"scaler_session": c1})
    assert res_get.status_code == 200
    group = res_get.json()["group"]
    assert group["name"] == "Test Group 1"
    assert len(group["members"]) == 3 # Alice, Bob, Charlie

    # Check roles
    roles = {m["id"]: m["role"] for m in group["members"]}
    assert roles[u1] == "admin"
    assert roles[u2] == "member"

@pytest.mark.asyncio
async def test_non_member_access(client):
    c1, u1 = await register_user(client, "Dave")
    c2, u2 = await register_user(client, "Eve")
    c3, u3 = await register_user(client, "Frank")

    # Dave creates group with Eve
    res = await client.post(
        "/api/groups",
        json={"name": "Top Secret", "member_ids": [u2]},
        cookies={"scaler_session": c1}
    )
    cid = res.json()["group"]["id"]

    # Frank tries to access
    res_frank = await client.get(f"/api/groups/{cid}", cookies={"scaler_session": c3})
    assert res_frank.status_code == 403

@pytest.mark.asyncio
async def test_admin_permissions(client):
    c1, u1 = await register_user(client, "George")
    c2, u2 = await register_user(client, "Hannah")
    c3, u3 = await register_user(client, "Ian")

    res = await client.post(
        "/api/groups",
        json={"name": "Perm Test", "member_ids": [u2]},
        cookies={"scaler_session": c1}
    )
    cid = res.json()["group"]["id"]

    # Hannah (member) tries to add Ian -> fail
    res_add_fail = await client.post(
        f"/api/groups/{cid}/members",
        json={"user_id": u3},
        cookies={"scaler_session": c2}
    )
    assert res_add_fail.status_code == 403

    # George (admin) adds Ian -> pass
    res_add_pass = await client.post(
        f"/api/groups/{cid}/members",
        json={"user_id": u3},
        cookies={"scaler_session": c1}
    )
    assert res_add_pass.status_code == 200

    # Hannah (member) tries to update info -> fail
    res_upd_fail = await client.put(
        f"/api/groups/{cid}",
        json={"name": "New Name"},
        cookies={"scaler_session": c2}
    )
    assert res_upd_fail.status_code == 403

    # George (admin) updates info -> pass
    res_upd_pass = await client.put(
        f"/api/groups/{cid}",
        json={"name": "New Admin Name"},
        cookies={"scaler_session": c1}
    )
    assert res_upd_pass.status_code == 200
    assert res_upd_pass.json()["group"]["name"] == "New Admin Name"

@pytest.mark.asyncio
async def test_leave_group(client):
    c1, u1 = await register_user(client, "Jack")
    c2, u2 = await register_user(client, "Kelly")

    res = await client.post(
        "/api/groups",
        json={"name": "Leave Test", "member_ids": [u2]},
        cookies={"scaler_session": c1}
    )
    cid = res.json()["group"]["id"]

    # Kelly leaves
    res_leave = await client.post(
        f"/api/groups/{cid}/leave",
        cookies={"scaler_session": c2}
    )
    assert res_leave.status_code == 200

    # Kelly cannot access anymore
    res_acc = await client.get(f"/api/groups/{cid}", cookies={"scaler_session": c2})
    assert res_acc.status_code == 403

@pytest.mark.asyncio
async def test_group_messages(client):
    c1, u1 = await register_user(client, "Leo")
    c2, u2 = await register_user(client, "Mia")

    res = await client.post(
        "/api/groups",
        json={"name": "Message Test", "member_ids": [u2]},
        cookies={"scaler_session": c1}
    )
    cid = res.json()["group"]["id"]

    # Leo sends message
    msg_res = await client.post(
        "/api/messages",
        json={"conversation_id": cid, "content": "Hello Group!"},
        cookies={"scaler_session": c1}
    )
    assert msg_res.status_code == 200
    msg_id = msg_res.json()["message"]["id"]

    # Mia can read
    get_res = await client.get(f"/api/messages/{cid}", cookies={"scaler_session": c2})
    assert get_res.status_code == 200
    assert len(get_res.json()["messages"]) == 1
    assert get_res.json()["messages"][0]["content"] == "Hello Group!"
    
    # Non member cannot read
    c3, u3 = await register_user(client, "Nate")
    get_fail = await client.get(f"/api/messages/{cid}", cookies={"scaler_session": c3})
    assert get_fail.status_code == 403
