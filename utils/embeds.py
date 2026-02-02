from __future__ import annotations

import random
import discord

DEFAULT_EMOJI_POOL = ["👋", "✅", "🚀", "🔥", "✨", "📌", "📈", "🧠", "💬", "🛡️", "🗞️", "📚", "🧾"]

def parse_emoji_pool(raw: str | None) -> list[str]:
    if not raw:
        return DEFAULT_EMOJI_POOL.copy()
    items = [x.strip() for x in raw.split(",")]
    items = [x for x in items if x]
    return items or DEFAULT_EMOJI_POOL.copy()

def pick_emoji(pool: list[str]) -> str:
    return random.choice(pool) if pool else "✨"

def split_text(text: str, limit: int = 3900) -> list[str]:
    text = (text or "").strip()
    if not text:
        return [""]

    parts: list[str] = []
    buff = ""

    for para in text.split("\n\n"):
        para = para.strip()
        if not para:
            continue

        candidate = para if not buff else f"{buff}\n\n{para}"
        if len(candidate) <= limit:
            buff = candidate
        else:
            if buff:
                parts.append(buff)
                buff = ""
            while len(para) > limit:
                parts.append(para[:limit])
                para = para[limit:]
            buff = para

    if buff:
        parts.append(buff)

    return parts or [""]

def make_embeds_from_text(
    *,
    title: str,
    text: str,
    emoji_pool: list[str],
    footer: str | None = None,
    color: int | None = None,
    prefix_emoji: bool = True,
    fixed_emoji: str | None = None,
) -> list[discord.Embed]:
    chunks = split_text(text)
    embeds: list[discord.Embed] = []

    emoji = fixed_emoji or pick_emoji(emoji_pool)
    for i, chunk in enumerate(chunks, start=1):
        t = title
        if prefix_emoji:
            t = f"{emoji} {t}"
        if len(chunks) > 1:
            t = f"{t} ({i}/{len(chunks)})"

        e = discord.Embed(title=t, description=chunk, color=color)
        if footer:
            e.set_footer(text=footer)
        embeds.append(e)

    return embeds
