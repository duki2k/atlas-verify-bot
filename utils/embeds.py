import discord


def split_text(text: str, limit: int = 3900) -> list[str]:
    text = (text or "").strip()
    if not text:
        return [""]

    chunks: list[str] = []
    buf = ""

    for para in text.split("\n\n"):
        para = para.strip()
        if not para:
            continue
        candidate = para if not buf else f"{buf}\n\n{para}"
        if len(candidate) <= limit:
            buf = candidate
        else:
            if buf:
                chunks.append(buf)
                buf = ""
            while len(para) > limit:
                chunks.append(para[:limit])
                para = para[limit:]
            buf = para

    if buf:
        chunks.append(buf)

    return chunks or [""]


def make_embeds(
    *,
    title: str,
    text: str,
    color: int,
    footer: str,
) -> list[discord.Embed]:
    parts = split_text(text)
    embeds: list[discord.Embed] = []

    for i, part in enumerate(parts, start=1):
        t = title
        if len(parts) > 1:
            t = f"{t} ({i}/{len(parts)})"
        e = discord.Embed(title=t, description=part, color=color)
        e.set_footer(text=footer)
        embeds.append(e)

    return embeds
