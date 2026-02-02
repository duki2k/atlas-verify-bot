import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

def _get_int(name: str, default: int | None = None) -> int | None:
    v = os.getenv(name)
    if v is None or v == "":
        return default
    try:
        return int(v)
    except ValueError:
        raise ValueError(f"Env var {name} precisa ser inteiro. Valor atual: {v!r}")

def _get_str(name: str, default: str | None = None) -> str | None:
    v = os.getenv(name)
    if v is None or v == "":
        return default
    return v

@dataclass(frozen=True)
class Settings:
    discord_token: str
    guild_id: int | None

    welcome_channel_id: int | None
    verify_channel_id: int | None
    log_channel_id: int | None

    pending_role_id: int
    verified_role_id: int

    min_account_age_days: int

    welcome_message: str
    verify_message: str

def load_settings() -> Settings:
    token = _get_str("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN não foi definido no .env / variáveis de ambiente.")

    pending_role_id = _get_int("PENDING_ROLE_ID")
    verified_role_id = _get_int("VERIFIED_ROLE_ID")
    if not pending_role_id or not verified_role_id:
        raise RuntimeError("PENDING_ROLE_ID e VERIFIED_ROLE_ID são obrigatórios.")

    return Settings(
        discord_token=token,
        guild_id=_get_int("GUILD_ID", None),

        welcome_channel_id=_get_int("WELCOME_CHANNEL_ID", None),
        verify_channel_id=_get_int("VERIFY_CHANNEL_ID", None),
        log_channel_id=_get_int("LOG_CHANNEL_ID", None),

        pending_role_id=pending_role_id,
        verified_role_id=verified_role_id,

        min_account_age_days=_get_int("MIN_ACCOUNT_AGE_DAYS", 0) or 0,

        welcome_message=_get_str(
            "WELCOME_MESSAGE",
            "Bem-vindo(a) {member}! Clique em ✅ no canal de verificação para liberar seu acesso.",
        ) or "",
        verify_message=_get_str(
            "VERIFY_MESSAGE",
            "Para acessar o servidor, clique em ✅ para verificar.",
        ) or "",
    )
