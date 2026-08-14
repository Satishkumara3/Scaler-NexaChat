"""
Database connection management using aiosqlite.

Design decisions:
- We use aiosqlite (raw SQL) instead of SQLAlchemy ORM.
  SQLAlchemy async + SQLite adds significant complexity for demo scale.
  Raw SQL is also easier to explain in an interview.
- WAL mode enabled for better concurrent read performance.
- Row factory set to aiosqlite.Row so columns are accessible by name.
- init_db() runs all CREATE TABLE IF NOT EXISTS statements at startup.
"""

import aiosqlite
from contextlib import asynccontextmanager
from config import settings

# ---------------------------------------------------------------------------
# DDL — all schema lives here for Phase 1 foundation.
# Tables for auth, messaging etc. will be added in later phases.
# ---------------------------------------------------------------------------

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- Health-check / metadata table
CREATE TABLE IF NOT EXISTS app_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

INSERT OR IGNORE INTO app_meta (key, value)
VALUES ('schema_version', '6');
UPDATE app_meta SET value = '6' WHERE key = 'schema_version';

-- ── Users ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id           TEXT PRIMARY KEY,           -- UUID v4
    phone        TEXT NOT NULL UNIQUE,        -- E.164 format recommended
    display_name TEXT NOT NULL,
    avatar_url   TEXT,                        -- ui-avatars.com URL or custom
    about        TEXT NOT NULL DEFAULT 'Hey there! I am using Scaler Chat.',
    created_at   TEXT NOT NULL,              -- ISO-8601 UTC
    last_seen    TEXT                         -- ISO-8601 UTC, NULL = never
);

CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);

-- ── Sessions ───────────────────────────────────────────────────────────────
-- One row per active login. Token stored as a SHA-256 hash (never plaintext).
CREATE TABLE IF NOT EXISTS sessions (
    id           TEXT PRIMARY KEY,           -- UUID v4
    user_id      TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash   TEXT NOT NULL UNIQUE,       -- SHA-256(raw_token)
    expires_at   TEXT NOT NULL,              -- ISO-8601 UTC
    created_at   TEXT NOT NULL,
    last_used_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id    ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token_hash ON sessions(token_hash);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);

-- ── OTP codes ──────────────────────────────────────────────────────────────
-- Short-lived codes for login/register flows. Always mocked to '123456' in dev.
CREATE TABLE IF NOT EXISTS otp_codes (
    id         TEXT PRIMARY KEY,             -- UUID v4
    phone      TEXT NOT NULL,
    code_hash  TEXT NOT NULL,               -- SHA-256(otp)
    expires_at TEXT NOT NULL,               -- ISO-8601 UTC (5 min TTL)
    used       INTEGER NOT NULL DEFAULT 0, -- 0 = unused, 1 = consumed
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_otp_codes_phone ON otp_codes(phone);

-- ── Contacts ───────────────────────────────────────────────────────────────
-- Phase 2: one-directional contact list. Bidirectional = two rows.
CREATE TABLE IF NOT EXISTS contacts (
    id              TEXT PRIMARY KEY,        -- UUID v4
    owner_id        TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    contact_user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    nickname        TEXT,                    -- optional override name
    created_at      TEXT NOT NULL,

    UNIQUE(owner_id, contact_user_id)        -- no duplicate contacts
);

CREATE INDEX IF NOT EXISTS idx_contacts_owner_id ON contacts(owner_id);

-- ── Conversations ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL CHECK(type IN ('DIRECT', 'GROUP')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS conversation_members (
    conversation_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'member' CHECK(role IN ('admin', 'member')),
    joined_at TEXT NOT NULL,
    PRIMARY KEY (conversation_id, user_id),
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_conversation_members_user_id ON conversation_members(user_id);

-- ── Group Info ─────────────────────────────────────────────────────────────
-- Extra metadata only for GROUP conversations.
CREATE TABLE IF NOT EXISTS group_info (
    conversation_id TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    avatar_url      TEXT,
    created_by      TEXT NOT NULL,  -- user_id of creator/admin
    created_at      TEXT NOT NULL,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    sender_id TEXT NOT NULL,
    content TEXT,
    message_type TEXT NOT NULL DEFAULT 'TEXT',
    status TEXT NOT NULL DEFAULT 'SENT',
    reply_to_message_id TEXT,               -- Phase 7B: nullable reply reference
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (reply_to_message_id) REFERENCES messages(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_sender_id ON messages(sender_id);

-- ── Message Reactions ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS message_reactions (
    id         TEXT PRIMARY KEY,
    message_id TEXT NOT NULL,
    user_id    TEXT NOT NULL,
    emoji      TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id)    REFERENCES users(id)    ON DELETE CASCADE,
    UNIQUE(message_id, user_id, emoji)    -- one reaction per emoji per user per message
);
CREATE INDEX IF NOT EXISTS idx_reactions_message_id ON message_reactions(message_id);
CREATE INDEX IF NOT EXISTS idx_reactions_user_id    ON message_reactions(user_id);


-- ── Attachments ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS attachments (
    id TEXT PRIMARY KEY,
    message_id TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    stored_filename TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_attachments_message_id ON attachments(message_id);

"""


async def get_db() -> aiosqlite.Connection:
    """
    FastAPI dependency that yields an aiosqlite connection per request.

    Usage in a route:
        async def my_route(db: aiosqlite.Connection = Depends(get_db)):
            ...
    """
    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row          # dict-like row access
        await db.execute("PRAGMA foreign_keys=ON")
        yield db


@asynccontextmanager
async def get_db_connection():
    """Context manager version for use outside of FastAPI dependency injection."""
    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys=ON")
        yield db


async def init_db() -> None:
    """
    Run at application startup to ensure all tables exist.
    Safe to call multiple times (CREATE TABLE IF NOT EXISTS).
    Also performs incremental migrations for new columns.
    """
    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        # 1. Run all base CREATE TABLE statements
        await db.executescript(SCHEMA_SQL)
        
        # 2. Phase 3 migration: add role to conversation_members if not present
        cursor = await db.execute("PRAGMA table_info(conversation_members)")
        cm_cols = [row["name"] for row in await cursor.fetchall()]
        if cm_cols and "role" not in cm_cols:
            await db.execute("ALTER TABLE conversation_members ADD COLUMN role TEXT NOT NULL DEFAULT 'member'")

        # 3. Phase 7B migration: add reply_to_message_id if not present
        cursor = await db.execute("PRAGMA table_info(messages)")
        msg_cols = [row["name"] for row in await cursor.fetchall()]
        if msg_cols and "reply_to_message_id" not in msg_cols:
            await db.execute("ALTER TABLE messages ADD COLUMN reply_to_message_id TEXT REFERENCES messages(id) ON DELETE SET NULL")
        
        await db.commit()
    print(f"[OK] Database initialised at: {settings.DB_PATH}")

