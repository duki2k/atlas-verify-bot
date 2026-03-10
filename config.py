# config.py
import os
from dataclasses import dataclass

@dataclass
class Settings:
    discord_token: str = os.getenv("DISCORD_TOKEN", "")
    admin_channel_id: int = int(os.getenv("ADMIN_CHANNEL_ID", "0"))
    rules_role_id: int = int(os.getenv("RULES_ROLE_ID", "0"))
    rules_text: str = os.getenv("RULES_TEXT", "")
    bot_name: str = os.getenv("BOT_NAME", "Robô Duki")

    events_category_id: int = int(os.getenv("EVENTS_CATEGORY_ID", "0"))
    events_logs_channel_id: int = int(os.getenv("EVENTS_LOGS_CHANNEL_ID", "0"))
    events_announce_channel_id: int = int(os.getenv("EVENTS_ANNOUNCE_CHANNEL_ID", "0"))


def _get_int(name: str, default: int | None = None) -> int | None:
    v = os.getenv(name)
    if v is None:
        return default
    v = v.strip()
    if not v:
        return default
    return int(v)


def load_settings() -> Settings:
    token = os.getenv("DISCORD_TOKEN", "").strip()
    if not token:
        raise RuntimeError("DISCORD_TOKEN não definido.")

    admin_id = _get_int("ADMIN_CHANNEL_ID")
    if not admin_id:
        raise RuntimeError("ADMIN_CHANNEL_ID não definido.")

    log_id = _get_int("LOG_CHANNEL_ID", None)
    dm_enabled = os.getenv("DM_WELCOME_ENABLED", "1").strip().lower() in ("1", "true", "yes")

    announce_id = _get_int("ANNOUNCE_CHANNEL_ID", None)

    rules_role_id = _get_int("RULES_ROLE_ID", None)
    rules_text = os.getenv("RULES_TEXT", "").strip() or None

    return Settings(
        discord_token=token,
        bot_name=os.getenv("BOT_NAME", "Robô Duki").strip() or "Robô Duki",
        admin_channel_id=int(admin_id),
        log_channel_id=int(log_id) if log_id else None,
        dm_welcome_enabled=dm_enabled,
        announce_channel_id=int(announce_id) if announce_id else None,
        rules_role_id=int(rules_role_id) if rules_role_id else None,
        rules_text=rules_text,
    )
