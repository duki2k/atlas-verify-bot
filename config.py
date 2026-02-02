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
    except ValueError as e:
        raise ValueError(f"Env var {name} precisa ser inteiro. Valor atual: {v!r}") from e


def _get_str(name: str, default: str | None = None) -> str | None:
    v = os.getenv(name)
    if v is None or v == "":
        return default
    return v


def _normalize_text(s: str) -> str:
    # permite usar "\n" no painel de env vars e virar quebra de linha real
    return s.replace("\\n", "\n")


@dataclass(frozen=True)
class Settings:
    discord_token: str
    guild_id: int | None

    verify_channel_id: int | None
    welcome_channel_id: int | None
    rules_channel_id: int | None
    log_channel_id: int | None

    verified_role_id: int
    min_account_age_days: int

    welcome_message: str
    verify_message: str

    post_verify_welcome_text: str
    post_verify_rules_text: str


def load_settings() -> Settings:
    token = _get_str("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN não foi definido nas variáveis de ambiente.")

    verified_role_id = _get_int("VERIFIED_ROLE_ID")
    if not verified_role_id:
        raise RuntimeError("VERIFIED_ROLE_ID é obrigatório.")

    welcome_message = _get_str(
        "WELCOME_MESSAGE",
        "Bem-vindo(a) {member}! Vá no canal #verificar e clique no botão ✅.",
    ) or ""

    verify_message = _get_str(
        "VERIFY_MESSAGE",
        "Para acessar o servidor, clique no botão ✅ abaixo para verificar.",
    ) or ""

    post_verify_welcome_text = _get_str(
        "POST_VERIFY_WELCOME_TEXT",
        "🎉 Bem-vindo(a), {member}! Seja breve: apresente-se e confira {rules_channel} para as regras.",
    ) or ""

    post_verify_rules_text = _get_str(
        "POST_VERIFY_RULES_TEXT",
        "📌 {member}, regras rápidas: 1) respeito sempre 2) sem spam 3) nada ilegal 4) use canais corretos. ✅",
    ) or ""

    return Settings(
        discord_token=token,
        guild_id=_get_int("GUILD_ID", None),

        verify_channel_id=_get_int("VERIFY_CHANNEL_ID", None),
        welcome_channel_id=_get_int("WELCOME_CHANNEL_ID", None),
        rules_channel_id=_get_int("RULES_CHANNEL_ID", None),
        log_channel_id=_get_int("LOG_CHANNEL_ID", None),

        verified_role_id=verified_role_id,
        min_account_age_days=_get_int("MIN_ACCOUNT_AGE_DAYS", 0) or 0,

        welcome_message=_normalize_text(welcome_message),
        verify_message=_normalize_text(verify_message),

        post_verify_welcome_text=_normalize_text(post_verify_welcome_text),
        post_verify_rules_text=_normalize_text(post_verify_rules_text),
    )
