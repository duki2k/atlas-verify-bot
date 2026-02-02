import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def _norm(s: str | None) -> str:
    return (s or "").replace("\\n", "\n").strip()


def _clean_int(raw: str | None) -> str | None:
    if raw is None:
        return None
    raw = raw.strip()
    raw = raw.lstrip("= ")  # evita crash por "=123..."
    return raw if raw != "" else None


def _get_int(name: str, default: int | None = None) -> int | None:
    v = _clean_int(os.getenv(name))
    if v is None:
        return default
    try:
        return int(v)
    except ValueError as e:
        raise ValueError(f"Env var {name} precisa ser inteiro. Valor atual: {os.getenv(name)!r}") from e


def _get_str(name: str, default: str | None = None) -> str | None:
    v = os.getenv(name)
    if v is None or v == "":
        return default
    return v


@dataclass(frozen=True)
class Settings:
    discord_token: str
    guild_id: int | None

    verify_channel_id: int | None
    welcome_channel_id: int | None
    rules_channel_id: int | None
    log_channel_id: int | None

    # ✅ novos canais clicáveis
    news_channel_id: int | None
    assets_channel_id: int | None
    education_channel_id: int | None
    chat_channel_id: int | None
    support_channel_id: int | None

    verified_role_id: int
    min_account_age_days: int

    embed_footer: str

    verify_message: str
    welcome_dm_text: str

    pinned_welcome_text: str
    pinned_rules_text: str


def load_settings() -> Settings:
    token = _get_str("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN não foi definido.")

    verified_role_id = _get_int("VERIFIED_ROLE_ID")
    if not verified_role_id:
        raise RuntimeError("VERIFIED_ROLE_ID é obrigatório.")

    return Settings(
        discord_token=token,
        guild_id=_get_int("GUILD_ID", None),

        verify_channel_id=_get_int("VERIFY_CHANNEL_ID", None),
        welcome_channel_id=_get_int("WELCOME_CHANNEL_ID", None),
        rules_channel_id=_get_int("RULES_CHANNEL_ID", None),
        log_channel_id=_get_int("LOG_CHANNEL_ID", None),

        # ✅ novos canais clicáveis
        news_channel_id=_get_int("NEWS_CHANNEL_ID", None),
        assets_channel_id=_get_int("ASSETS_CHANNEL_ID", None),
        education_channel_id=_get_int("EDUCATION_CHANNEL_ID", None),
        chat_channel_id=_get_int("CHAT_CHANNEL_ID", None),
        support_channel_id=_get_int("SUPPORT_CHANNEL_ID", None),

        verified_role_id=verified_role_id,
        min_account_age_days=_get_int("MIN_ACCOUNT_AGE_DAYS", 0) or 0,

        embed_footer=_get_str("EMBED_FOOTER", "Atlas Community") or "Atlas Community",

        verify_message=_norm(_get_str(
            "VERIFY_MESSAGE",
            "Para acessar o servidor, clique no botão ✅ abaixo para verificar.",
        )),

        welcome_dm_text=_norm(_get_str(
            "WELCOME_DM_TEXT",
            "👋 Bem-vindo(a), {member}!\n\nPara liberar acesso, vá em {verify_channel} e clique no botão ✅.",
        )),

        # Placeholders suportados:
        # {member_role} {rules_channel}
        # {news_channel} {assets_channel} {education_channel} {chat_channel} {support_channel}
        pinned_welcome_text=_norm(_get_str(
            "PINNED_WELCOME_TEXT",
            "🎉 Seja bem-vindo(a) à Atlas Community!\n\n📌 Cargo: {member_role}\n📌 Leia {rules_channel} antes de postar.",
        )),

        pinned_rules_text=_norm(_get_str(
            "PINNED_RULES_TEXT",
            "📌 Regras do servidor (fixado).\n\nRespeito acima de tudo.",
        )),
    )
