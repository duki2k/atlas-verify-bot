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


def _parse_tz_offset(raw: str | None) -> int:
    """
    Retorna offset em minutos.
    Aceita: -03:00, +02:30, 0, -180 (minutos).
    """
    if raw is None or raw.strip() == "":
        return 0
    s = raw.strip()

    # minutos direto
    if s.lstrip("+-").isdigit():
        return int(s)

    sign = 1
    if s.startswith("-"):
        sign = -1
        s = s[1:]
    elif s.startswith("+"):
        s = s[1:]

    if ":" in s:
        hh, mm = s.split(":", 1)
        return sign * (int(hh) * 60 + int(mm))

    # fallback: horas
    if s.isdigit():
        return sign * int(s) * 60

    return 0


@dataclass(frozen=True)
class Settings:
    discord_token: str

    welcome_channel_id: int | None
    log_channel_id: int | None

    dm_welcome_enabled: bool

    embed_footer: str
    emoji_pool: list[str]

    tz_offset_minutes: int

    # Texto base (fallback)
    welcome_text: str
    dm_welcome_text: str

    # Variações (aleatórias)
    welcome_text_variants: list[str]
    dm_text_variants: list[str]

    # Variações por horário (se definidas, têm prioridade)
    welcome_morning: str
    welcome_afternoon: str
    welcome_night: str

    dm_morning: str
    dm_afternoon: str
    dm_night: str

    # Linhas divertidas aleatórias (opcional)
    fun_lines: list[str]


def load_settings() -> Settings:
    token = _get_str("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN não foi definido.")

    tz_offset = _parse_tz_offset(_get_str("TZ_OFFSET", "-03:00"))  # default Brasil

    return Settings(
        discord_token=token,

        welcome_channel_id=_get_int("WELCOME_CHANNEL_ID", None),
        log_channel_id=_get_int("LOG_CHANNEL_ID", None),

        dm_welcome_enabled=_get_bool("DM_WELCOME_ENABLED", True),

        embed_footer=_get_str("EMBED_FOOTER", "Duki Odyssey ®") or "Duki Odyssey ®",
        emoji_pool=_parse_emoji_pool(_get_str("EMOJI_POOL", None)),

        tz_offset_minutes=tz_offset,

        # fallback
        welcome_text=_norm(_get_str("WELCOME_TEXT", "Seja bem-vindo(a), {member}! 👋✨")),
        dm_welcome_text=_norm(_get_str("DM_WELCOME_TEXT", "👋 Oi {member}! Bem-vindo(a) ao Duki Odyssey ® 🌌✨")),

        # variantes (se quiser usar só isso, sem horário)
        welcome_text_variants=_parse_list(_get_str("WELCOME_TEXT_VARIANTS", None)),
        dm_text_variants=_parse_list(_get_str("DM_WELCOME_TEXT_VARIANTS", None)),

        # horário (se definidos, ganham prioridade)
        welcome_morning=_norm(_get_str("WELCOME_TEXT_MORNING", "")),
        welcome_afternoon=_norm(_get_str("WELCOME_TEXT_AFTERNOON", "")),
        welcome_night=_norm(_get_str("WELCOME_TEXT_NIGHT", "")),

        dm_morning=_norm(_get_str("DM_WELCOME_TEXT_MORNING", "")),
        dm_afternoon=_norm(_get_str("DM_WELCOME_TEXT_AFTERNOON", "")),
        dm_night=_norm(_get_str("DM_WELCOME_TEXT_NIGHT", "")),

        fun_lines=_parse_list(_get_str("FUN_LINES", None)),
    )
