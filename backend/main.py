"""
FastAPI application factory — entry point.

Startup order:
1. Init DB (create tables if missing)
2. Register CORS middleware
3. Register exception handlers
4. Mount routers
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import init_db
from routers import health, ws as ws_router
from routers import auth as auth_router
from routers import users as users_router
from routers import contacts as contacts_router
from routers import conversations as conversations_router
from routers import messages as messages_router
from routers import groups as groups_router
from middleware.error_handlers import (
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
)
from database import get_db_connection
from repositories.user_repo import UserRepository

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan (replaces deprecated @app.on_event)
# ---------------------------------------------------------------------------
async def seed_dev_users() -> None:
    """Create 4 development seed users (idempotent — skips existing phones)."""
    seeds = [
        ("Alice Sharma",    "+91-9000000001"),
        ("Bob Mehta",       "+91-9000000002"),
        ("Carol D'Souza",   "+91-9000000003"),
        ("David Nair",      "+91-9000000004"),
    ]
    async with get_db_connection() as db:
        repo = UserRepository(db)
        for display_name, phone in seeds:
            if not await repo.exists_by_phone(phone):
                user = await repo.create(phone=phone, display_name=display_name)
                logger.info(f"Seeded dev user: {user.display_name} ({user.phone})")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting Scaler Chat API …")
    await init_db()
    await seed_dev_users()
    yield
    logger.info("👋 Scaler Chat API shutting down.")


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Signal-inspired secure messaging API",
        lifespan=lifespan,
        # Disable default /docs redirect behaviour in production
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    # ---- CORS ---------------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,          # needed for HttpOnly cookies
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ---- Exception handlers -------------------------------------------------
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # ---- Routers ------------------------------------------------------------
    app.include_router(health.router)               # GET / and GET /health
    app.include_router(ws_router.router)            # WS /ws
    # Phase 2 routers
    app.include_router(auth_router.router)          # /api/auth/*
    app.include_router(users_router.router)         # /api/users/*
    app.include_router(contacts_router.router)      # /api/contacts/*
    
    # Phase 3 routers
    app.include_router(conversations_router.router) # /api/conversations/*
    app.include_router(messages_router.router)      # /api/messages/*
    app.include_router(groups_router.router)        # /api/groups/*

    return app


app = create_app()


# ---------------------------------------------------------------------------
# Dev entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
