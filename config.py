import os
from dataclasses import dataclass


@dataclass
class Settings:
    discord_token: str
    bot_name: str
    admin_channel_id: int
    log_channel_id: int | None
    dm_welcome_enabled: bool
    announce_channel_id: int | None
    member_role_id: int | None


def _get_int(name: str, default: int | None = None) -> int | None:
    v = os.getenv(name)
    if v is None or v.strip() == "":
        return default
    try:
        return int(v.strip())
    except ValueError as e:
        raise RuntimeError(f"Env var {name} precisa ser inteiro. Valor atual: {v!r}") from e


def load_settings() -> Settings:
    token = os.getenv("DISCORD_TOKEN", "").strip()
    if not token:
        raise RuntimeError("DISCORD_TOKEN não definido.")

    admin_id = _get_int("ADMIN_CHANNEL_ID")
    if not admin_id:
        raise RuntimeError("ADMIN_CHANNEL_ID não definido.")

    log_id = _get_int("LOG_CHANNEL_ID", None)
    announce_id = _get_int("ANNOUNCE_CHANNEL_ID", None)
    member_role_id = _get_int("MEMBER_ROLE_ID", None)

    dm_enabled = os.getenv("DM_WELCOME_ENABLED", "1").strip() in ("1", "true", "True", "yes", "YES")
    bot_name = os.getenv("BOT_NAME", "Robô Duki").strip() or "Robô Duki"

    return Settings(
        discord_token=token,
        bot_name=bot_name,
        admin_channel_id=int(admin_id),
        log_channel_id=int(log_id) if log_id else None,
        dm_welcome_enabled=dm_enabled,
        announce_channel_id=int(announce_id) if announce_id else None,
        member_role_id=int(member_role_id) if member_role_id else None,
    )
