import random
import datetime as dt
import discord

NEON_PURPLE = 0xB026FF  # roxo neon


def pick_emoji(pool: list[str]) -> str:
    return random.choice(pool) if pool else "✨"


def retro_header(title: str) -> str:
    # arcade retrô (sem cara “chatgpt”)
    # (curto pra não poluir)
    return f"⟦ {title} ⟧"


def retro_divider() -> str:
    return "═" * 22


def make_embed(
    *,
    title: str,
    description: str,
    footer: str,
    color: int = NEON_PURPLE,
    thumbnail_url: str | None = None,
) -> discord.Embed:
    e = discord.Embed(title=retro_header(title), description=description, color=color)
    if thumbnail_url:
        e.set_thumbnail(url=thumbnail_url)
    year = dt.datetime.now().year
    e.set_footer(text=f"{footer} • {year}")
    return e
