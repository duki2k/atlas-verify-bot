# utils/database.py
import sqlite3
from contextlib import contextmanager

DB_NAME = "duki_bot.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL,
    created_by_id INTEGER NOT NULL,
    started_by_id INTEGER,
    ended_by_id INTEGER,
    created_at TEXT NOT NULL,
    started_at TEXT,
    ended_at TEXT,
    voice_channel_id INTEGER,
    text_channel_id INTEGER,
    singer_role_id INTEGER,
    spectator_role_id INTEGER,
    custom_voice_channel_name TEXT,
    custom_text_channel_name TEXT
);

CREATE TABLE IF NOT EXISTS event_signups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    signup_type TEXT NOT NULL,
    status TEXT NOT NULL,
    confirmed_at TEXT NOT NULL,
    updated_at TEXT,
    cancelled_at TEXT,
    UNIQUE(event_id, user_id)
);

CREATE TABLE IF NOT EXISTS event_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    queue_position INTEGER NOT NULL,
    queue_status TEXT NOT NULL,
    UNIQUE(event_id, user_id)
);

CREATE TABLE IF NOT EXISTS staff_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    event_id INTEGER,
    action_type TEXT NOT NULL,
    target_user_id INTEGER,
    actor_user_id INTEGER NOT NULL,
    actor_display_name TEXT,
    reason TEXT,
    metadata_json TEXT,
    created_at TEXT NOT NULL
);
"""

@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)
