import datetime as _dt
import random
import discord
from discord import app_commands
from discord.ext import commands

from config import load_settings
from utils.logging_ import setup_logging

settings = load_settings()
logger = setup_logging()

VERIFY_BUTTON_CUSTOM_ID = "verifybot:verify_button"


# ---------- helpers ----------
def _pool() -> list[str]:
    return getattr(settings, "emoji_pool", ["👋", "✅", "📌", "🎉", "🛡️", "🚀", "📈", "🧠", "🗞️", "💬"])


def _pick(pool: list[str]) -> str:
    return random.choice(pool) if pool else "✨"


def _footer() -> str:
    return getattr(settings, "embed_footer", "Atlas Community")


def _ch_mention(channel_id: int | None, fallback: str = "") -> str:
    return f"<#{channel_id}>" if channel_id else fallback


def _split(text: str, limit: int = 3900) -> list[str]:
    text = (text or "").strip()
    if not text:
        return [""]
    out = []
    while len(text) > limit:
        out.append(text[:limit])
        text = text[limit:]
    out.append(text)
    return out


def _embeds(title: str, text: str, color: int, fixed_emoji: str | None = None, exact_title: bool = False) -> list[discord.Embed]:
    # exact_title=True -> não prefixa emoji no título (para "✅ Acesso liberado!")
    pool = _pool()
    emoji = fixed_emoji or _pick(pool)

    chunks = _split(text)
    embeds = []
    for i, chunk in enumerate(chunks, start=1):
        t = title if exact_title else f"{emoji} {title}"
        if len(chunks) > 1:
            t = f"{t} ({i}/{len(chunks)})"
        e = discord.Embed(title=t, description=chunk, color=color)
        e.set_footer(text=_footer())
        embeds.append(e)
    return embeds


def _account_age_days(user: discord.abc.User) -> int:
    created = user.created_at
    if created is None:
        return 9999
    now = _dt.datetime.now(tz=_dt.timezone.utc)
    return int((now - created).days)


async def _clear_bot_pins(channel: discord.TextChannel, bot_user_id: int) -> None:
    try:
        pins = await channel.pins()
    except Exception:
        return

    for msg in pins:
        if msg.author and msg.author.id == bot_user_id:
            try:
                await msg.unpin()
            except Exception:
                pass
            try:
                await msg.delete()
            except Exception:
                pass


async def _post_and_pin(channel: discord.TextChannel, embeds: list[discord.Embed]) -> None:
    for e in embeds:
        m = await channel.send(embed=e)
        try:
            await m.pin(reason="Onboarding Atlas")
        except Exception:
            pass


async def _setup_pinned_messages(guild: discord.Guild, bot_user_id: int) -> tuple[bool, str]:
    # precisa desses IDs
    if not settings.welcome_channel_id or not settings.rules_channel_id:
        return (False, "WELCOME_CHANNEL_ID / RULES_CHANNEL_ID não configurados.")

    welcome_ch = guild.get_channel(settings.welcome_channel_id)
    rules_ch = guild.get_channel(settings.rules_channel_id)

    if not isinstance(welcome_ch, discord.TextChannel) or not isinstance(rules_ch, discord.TextChannel):
        return (False, "WELCOME_CHANNEL_ID / RULES_CHANNEL_ID não apontam para canais de texto.")

    rules_mention = _ch_mention(settings.rules_channel_id, "#regras")

    # textos longos (fixados) — não marca usuário aqui
    welcome_text = settings.post_verify_welcome_text.format(
        member="👤 membro verificado",
        rules_channel=rules_mention,
    )
    rules_text = settings.post_verify_rules_text.format(
        member="👤 membro verificado",
        rules_channel=rules_mention,
    )

    # limpa pins antigos do bot (pra não virar bagunça)
    await _clear_bot_pins(welcome_ch, bot_user_id)
    aw
