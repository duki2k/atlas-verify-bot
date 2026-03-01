import random
import datetime as dt
import discord

NEON_PURPLE = 0xB026FF  # roxo neon


def pick_emoji(pool: list[str]) -> str:
    return random.choice(pool) if pool else "✨"


def retro_header(title: str) -> str:
    return f"⟦ {title} ⟧"


def retro_divider() -> str:
    return "═" * 22


def make_embed(
    *,
    title: str,
    description: str = "",
    footer: str,
    color: int = NEON_PURPLE,
    thumbnail_url: str | None = None,
    author_name: str | None = None,
    author_icon: str | None = None,
    timestamp: bool = True,
) -> discord.Embed:
    e = discord.Embed(title=retro_header(title), description=description, color=color)
    if thumbnail_url:
        e.set_thumbnail(url=thumbnail_url)
    if author_name:
        e.set_author(name=author_name, icon_url=author_icon or discord.Embed.Empty)

    if timestamp:
        e.timestamp = dt.datetime.now(dt.timezone.utc)

    year = dt.datetime.now().year
    e.set_footer(text=f"{footer} • {year}")
    return e
