"""
Phase 7B Tests: Message Replies + Emoji Reactions
Covers:
  - Replies (valid, nonexistent ID, cross-conversation, unauthorized, persistence)
  - Reactions (add, toggle-remove, two emojis, invalid emoji, unauthorized, persistence)
  - Regression: text, group messaging, delivery receipts
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture(scope="session")
async def test_db_path(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("testdb_p7b")
    return str(tmp / "test_chat_p7b.db")


@pytest_asyncio.fixture
async def client(test_db_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", test_db_path)

    import config
    config.settings.DB_PATH = test_db_path
    config.get_settings.cache_clear()
    config.settings = config.get_settings()

    from database import init_db
    from main import app

    await init_db()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def register_and_login(client, phone, name):
    await client.post("/api/auth/register/request-otp", json={"phone": phone})
    r = await client.post("/api/auth/register/verify",
                          json={"phone": phone, "otp_code": "123456", "display_name": name})
    if r.status_code not in (200, 201):
        # Already exists, login instead
        await client.post("/api/auth/login/request-otp", json={"phone": phone})
        r = await client.post("/api/auth/login/verify",
                              json={"phone": phone, "otp_code": "123456"})
    assert r.status_code in (200, 201), f"Auth failed for {name}: {r.text}"
    return r.json()["user"]["id"]


async def login(client, phone):
    await client.post("/api/auth/login/request-otp", json={"phone": phone})
    r = await client.post("/api/auth/login/verify",
                          json={"phone": phone, "otp_code": "123456"})
    assert r.status_code in (200, 201)
    return r.json()["user"]["id"]


async def create_dm(client, other_user_id):
    r = await client.post("/api/conversations", json={"user_id": other_user_id})
    assert r.status_code == 200, r.text
    return r.json()["conversation"]["id"]


async def send_text(client, conv_id, content, reply_to=None):
    body = {"conversation_id": conv_id, "content": content, "message_type": "TEXT"}
    if reply_to:
        body["reply_to_message_id"] = reply_to
    r = await client.post("/api/messages", json=body)
    assert r.status_code == 200, f"send_text failed: {r.text}"
    return r.json()["message"]


# ─── Setup users in shared session ────────────────────────────────────────────

@pytest.fixture(scope="module")
def user_phones():
    return {
        "alice": "+91-7200000001",
        "bob":   "+91-7200000002",
        "charlie": "+91-7200000003",
    }


# ─── Reply Tests ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_reply_valid(client, user_phones):
    """User can reply to a message in the same conversation."""
    uid_a = await register_and_login(client, user_phones["alice"], "Alice7B")
    uid_b = await register_and_login(client, user_phones["bob"], "Bob7B")
    await login(client, user_phones["alice"])

    conv_id = await create_dm(client, uid_b)
    original = await send_text(client, conv_id, "Hello!")

    reply = await send_text(client, conv_id, "Hi back!", reply_to=original["id"])
    assert reply["reply_to_message_id"] == original["id"]
    assert reply["reply_preview"] is not None
    assert reply["reply_preview"]["content"] == "Hello!"
    assert reply["reply_preview"]["id"] == original["id"]


@pytest.mark.asyncio
async def test_reply_nonexistent_message(client, user_phones):
    """Reply to a non-existent message → 404."""
    uid_b = await register_and_login(client, user_phones["bob"], "Bob7B")
    await login(client, user_phones["alice"])
    conv_id = await create_dm(client, uid_b)

    body = {
        "conversation_id": conv_id,
        "content": "ghost reply",
        "message_type": "TEXT",
        "reply_to_message_id": "00000000-0000-0000-0000-000000000000",
    }
    r = await client.post("/api/messages", json=body)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_reply_cross_conversation_rejected(client, user_phones):
    """Reply using a message from a different conversation → 400."""
    uid_b = await register_and_login(client, user_phones["bob"], "Bob7B")
    uid_c = await register_and_login(client, user_phones["charlie"], "Charlie7B")
    await login(client, user_phones["alice"])

    conv1 = await create_dm(client, uid_b)
    conv2 = await create_dm(client, uid_c)

    original = await send_text(client, conv1, "Msg in conv1")

    body = {
        "conversation_id": conv2,
        "content": "cross reply",
        "message_type": "TEXT",
        "reply_to_message_id": original["id"],
    }
    r = await client.post("/api/messages", json=body)
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_reply_unauthorized_non_member(client, user_phones):
    """Non-member cannot send a reply."""
    uid_b = await register_and_login(client, user_phones["bob"], "Bob7B")
    await login(client, user_phones["alice"])
    conv_id = await create_dm(client, uid_b)
    original = await send_text(client, conv_id, "Hello!")

    # Login as Charlie (not a member of this DM)
    await login(client, user_phones["charlie"])

    body = {
        "conversation_id": conv_id,
        "content": "intruder reply",
        "message_type": "TEXT",
        "reply_to_message_id": original["id"],
    }
    r = await client.post("/api/messages", json=body)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_reply_persists(client, user_phones):
    """Reply metadata survives a GET fetch."""
    uid_b = await register_and_login(client, user_phones["bob"], "Bob7B")
    await login(client, user_phones["alice"])
    conv_id = await create_dm(client, uid_b)

    original = await send_text(client, conv_id, "Persist original")
    reply = await send_text(client, conv_id, "Persist reply", reply_to=original["id"])

    r = await client.get(f"/api/messages/{conv_id}")
    assert r.status_code == 200
    msgs = r.json()["messages"]
    reply_msg = next((m for m in msgs if m["id"] == reply["id"]), None)
    assert reply_msg is not None
    assert reply_msg["reply_to_message_id"] == original["id"]
    assert reply_msg["reply_preview"]["content"] == "Persist original"


# ─── Reaction Tests ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_reaction_add(client, user_phones):
    """Can add a valid emoji reaction."""
    uid_b = await register_and_login(client, user_phones["bob"], "Bob7B")
    await login(client, user_phones["alice"])
    conv_id = await create_dm(client, uid_b)
    msg = await send_text(client, conv_id, "React to me!")

    r = await client.post(f"/api/messages/{msg['id']}/reactions", json={"emoji": "❤️"})
    assert r.status_code == 200
    data = r.json()
    assert data["event"] == "reaction.added"
    assert data["emoji"] == "❤️"


@pytest.mark.asyncio
async def test_reaction_toggle_removes(client, user_phones):
    """Reacting twice removes the reaction (toggle behaviour)."""
    uid_b = await register_and_login(client, user_phones["bob"], "Bob7B")
    await login(client, user_phones["alice"])
    conv_id = await create_dm(client, uid_b)
    msg = await send_text(client, conv_id, "Toggle me!")

    r1 = await client.post(f"/api/messages/{msg['id']}/reactions", json={"emoji": "👍"})
    assert r1.json()["event"] == "reaction.added"

    r2 = await client.post(f"/api/messages/{msg['id']}/reactions", json={"emoji": "👍"})
    assert r2.json()["event"] == "reaction.removed"


@pytest.mark.asyncio
async def test_reaction_two_different_emojis(client, user_phones):
    """Two different emojis can coexist independently."""
    uid_b = await register_and_login(client, user_phones["bob"], "Bob7B")
    await login(client, user_phones["alice"])
    conv_id = await create_dm(client, uid_b)
    msg = await send_text(client, conv_id, "Multi react!")

    r1 = await client.post(f"/api/messages/{msg['id']}/reactions", json={"emoji": "❤️"})
    r2 = await client.post(f"/api/messages/{msg['id']}/reactions", json={"emoji": "👍"})
    assert r1.json()["event"] == "reaction.added"
    assert r2.json()["event"] == "reaction.added"


@pytest.mark.asyncio
async def test_reaction_invalid_emoji_rejected(client, user_phones):
    """Disallowed emoji → 400."""
    uid_b = await register_and_login(client, user_phones["bob"], "Bob7B")
    await login(client, user_phones["alice"])
    conv_id = await create_dm(client, uid_b)
    msg = await send_text(client, conv_id, "emoji test")

    r = await client.post(f"/api/messages/{msg['id']}/reactions", json={"emoji": "🦄"})
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_reaction_unauthorized_non_member(client, user_phones):
    """Non-member cannot react."""
    uid_b = await register_and_login(client, user_phones["bob"], "Bob7B")
    await login(client, user_phones["alice"])
    conv_id = await create_dm(client, uid_b)
    msg = await send_text(client, conv_id, "Can Charlie react?")

    # Login as Charlie
    await login(client, user_phones["charlie"])
    r = await client.post(f"/api/messages/{msg['id']}/reactions", json={"emoji": "❤️"})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_reactions_persisted_in_messages(client, user_phones):
    """Reactions appear in GET /api/messages/{conv_id}."""
    uid_b = await register_and_login(client, user_phones["bob"], "Bob7B")
    await login(client, user_phones["alice"])
    conv_id = await create_dm(client, uid_b)
    msg = await send_text(client, conv_id, "Persist reaction")
    await client.post(f"/api/messages/{msg['id']}/reactions", json={"emoji": "😂"})

    r = await client.get(f"/api/messages/{conv_id}")
    assert r.status_code == 200
    msgs = r.json()["messages"]
    target = next((m for m in msgs if m["id"] == msg["id"]), None)
    assert target is not None
    emojis = [rx["emoji"] for rx in target.get("reactions", [])]
    assert "😂" in emojis


# ─── Regression Tests ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_regression_text_messaging(client, user_phones):
    uid_b = await register_and_login(client, user_phones["bob"], "Bob7B")
    await login(client, user_phones["alice"])
    conv_id = await create_dm(client, uid_b)
    msg = await send_text(client, conv_id, "regression text")
    assert msg["id"]
    assert msg["content"] == "regression text"
    assert msg["reactions"] == []
    assert msg["reply_to_message_id"] is None


@pytest.mark.asyncio
async def test_regression_get_messages_has_reactions_field(client, user_phones):
    uid_b = await register_and_login(client, user_phones["bob"], "Bob7B")
    await login(client, user_phones["alice"])
    conv_id = await create_dm(client, uid_b)
    r = await client.get(f"/api/messages/{conv_id}")
    assert r.status_code == 200
    msgs = r.json()["messages"]
    for m in msgs:
        assert "reactions" in m


@pytest.mark.asyncio
async def test_regression_delivery_status(client, user_phones):
    uid_b = await register_and_login(client, user_phones["bob"], "Bob7B")
    await login(client, user_phones["alice"])
    conv_id = await create_dm(client, uid_b)
    msg = await send_text(client, conv_id, "status test")

    # Bob marks as READ
    await login(client, user_phones["bob"])
    r = await client.put(f"/api/messages/{msg['id']}/status", json={"status": "READ"})
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_regression_group_messaging(client, user_phones):
    uid_b = await register_and_login(client, user_phones["bob"], "Bob7B")
    uid_c = await register_and_login(client, user_phones["charlie"], "Charlie7B")
    await login(client, user_phones["alice"])

    r = await client.post("/api/groups",
                          json={"name": "7BGroup", "member_ids": [uid_b, uid_c]})
    assert r.status_code == 200
    grp_conv_id = r.json()["group"]["id"]

    msg = await send_text(client, grp_conv_id, "group msg regression")
    assert msg["conversation_id"] == grp_conv_id
    assert msg["reactions"] == []


@pytest.mark.asyncio
async def test_schema_version_updated(client):
    """Schema version must be 6."""
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["database"]["schema_version"] == "6"
