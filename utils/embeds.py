import random
import discord


def pick_emoji(pool: list[str]) -> str:
    return random.choice(pool) if pool else "✨"


def make_embed(*, title: str, description: str, color: int, footer: str) -> discord.Embed:
    e = discord.Embed(title=title, description=description, color=color)
    e.set_footer(text=footer)
    return e
