"""
Health-check router.

GET /health  → confirms the API is live, DB is reachable, WS manager is up.
GET /        → root redirect / welcome message
"""

from fastapi import APIRouter, Depends
import aiosqlite
from database import get_db
from ws.manager import manager

router = APIRouter(tags=["health"])


@router.get("/")
async def root():
    return {"message": "Scaler Chat API is running 🚀"}


@router.get("/health")
async def health_check(db: aiosqlite.Connection = Depends(get_db)):
    # Verify DB is reachable
    cursor = await db.execute("SELECT value FROM app_meta WHERE key = 'schema_version'")
    row = await cursor.fetchone()
    schema_version = row["value"] if row else "unknown"

    return {
        "status": "ok",
        "database": {
            "connected": True,
            "schema_version": schema_version,
        },
        "websocket": manager.stats(),
    }
