import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def _norm(s: str | None) -> str:
    return (s or "").replace("\\n", "\n").strip()


def _clean_int(raw: str | None) -> str | None:
    if raw is None:
        return None
    raw = raw.strip().lstrip("= ")
    return raw if raw else None


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


def _get_bool(name: str, default: bool = False) -> bool:
    v = (_get_str(name, None) or "").strip().lower()
    if v == "":
        return default
    return v in ("1", "true", "yes", "y", "on")


def _parse_list(raw: str | None, sep: str = "|||") -> list[str]:
    if not raw:
        return []
    items = [x.strip() for x in raw.split(sep)]
    return [x for x in items if x]


def _parse_emoji_pool(raw: str | None) -> list[str]:
    if not raw:
        return ["🌌", "✨", "🚀", "🎮", "😂", "🎧", "🍕", "🧩", "🔥", "💫"]
    items = [x.strip() for x in raw.split(",")]
    items = [x for x in items if x]
    return items or ["🌌", "✨", "🚀", "🎮", "😂", "🎧", "🍕", "🧩", "🔥", "💫"]


@dataclass(frozen=True)
class Settings:
    discord_token: str

    admin_channel_id: int
    welcome_channel_id: int | None
    log_channel_id: int | None

    bot_name: str
    embed_footer: str
    emoji_pool: list[str]

    dm_welcome_enabled: bool
    welcome_text: str
    welcome_text_variants: list[str]
    dm_welcome_text: str

    enable_stats_tracking: bool


def load_settings() -> Settings:
    token = _get_str("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN não foi definido.")

    admin_channel_id = _get_int("ADMIN_CHANNEL_ID")
    if not admin_channel_id:
        raise RuntimeError("ADMIN_CHANNEL_ID é obrigatório (ID do canal #admin-bot).")

    return Settings(
        discord_token=token,
        admin_channel_id=admin_channel_id,
        welcome_channel_id=_get_int("WELCOME_CHANNEL_ID", None),
        log_channel_id=_get_int("LOG_CHANNEL_ID", None),

        bot_name=_get_str("BOT_NAME", "Robô Duki") or "Robô Duki",
        embed_footer=_get_str("EMBED_FOOTER", "Duki Odyssey ®") or "Duki Odyssey ®",
        emoji_pool=_parse_emoji_pool(_get_str("EMOJI_POOL", None)),

        dm_welcome_enabled=_get_bool("DM_WELCOME_ENABLED", True),

        welcome_text=_norm(_get_str("WELCOME_TEXT", "{member} chegou!")),
        welcome_text_variants=_parse_list(_get_str("WELCOME_TEXT_VARIANTS", None)),

        dm_welcome_text=_norm(_get_str(
            "DM_WELCOME_TEXT",
            "👋 Oi {member}! Aqui é o **Robô Duki** 💜\n\nBem-vindo(a) ao servidor! Chega na resenha 😄",
        )),

        enable_stats_tracking=_get_bool("ENABLE_STATS_TRACKING", False),
    )
