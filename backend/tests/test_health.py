"""
Phase 1 backend tests.
Tests the health endpoint and DB connectivity.

Test isolation strategy:
- We use a temp file-based SQLite DB (not :memory:) because aiosqlite
  opens a new connection per call, and :memory: DBs are not shared.
- The temp DB is initialised once before tests and deleted after.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import sys, os, tempfile

# Make the backend root importable
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@pytest_asyncio.fixture(scope="session")
async def test_db_path(tmp_path_factory):
    """Create a temporary SQLite DB file for the test session."""
    tmp = tmp_path_factory.mktemp("testdb")
    return str(tmp / "test_chat.db")


@pytest_asyncio.fixture
async def client(test_db_path, monkeypatch):
    """
    Patch settings to use the test DB, initialise schema,
    then yield an httpx AsyncClient.
    """
    # Patch before importing database/config so settings picks it up
    monkeypatch.setenv("DB_PATH", test_db_path)

    # Re-read settings with patched env
    import config
    config.settings.DB_PATH = test_db_path

    from database import init_db
    from main import app

    await init_db()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_root(client):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


@pytest.mark.asyncio
async def test_health_ok(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"]["connected"] is True
    assert data["database"]["schema_version"] == "6"
    assert "websocket" in data
    assert "connected_users" in data["websocket"]


@pytest.mark.asyncio
async def test_health_db_schema_version(client):
    # Phase 7B: expected version is '6'
    response = await client.get("/health")
    data = response.json()
    assert data["database"]["schema_version"] == "6"
