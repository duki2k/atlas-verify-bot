# utils/event_service.py
import random
from datetime import datetime
from utils.database import get_conn

def create_event(guild_id: int, title: str, created_by_id: int):
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO events (guild_id, event_type, title, status, created_by_id, created_at)
            VALUES (?, 'karaoke', ?, 'signup_open', ?, ?)
            """,
            (guild_id, title, created_by_id, datetime.utcnow().isoformat())
        )
        return cur.lastrowid

def get_open_karaoke_event(guild_id: int):
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT * FROM events
            WHERE guild_id = ? AND event_type = 'karaoke' AND status IN ('signup_open', 'active')
            ORDER BY id DESC LIMIT 1
            """,
            (guild_id,)
        ).fetchone()
        return row

def log_staff_action(guild_id, event_id, action_type, actor_user_id, actor_display_name, target_user_id=None, reason=None, metadata_json=None):
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO staff_logs (guild_id, event_id, action_type, target_user_id, actor_user_id, actor_display_name, reason, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (guild_id, event_id, action_type, target_user_id, actor_user_id, actor_display_name, reason, metadata_json, datetime.utcnow().isoformat())
        )

def randomize_queue(user_ids: list[int]):
    data = user_ids[:]
    random.shuffle(data)
    return data
