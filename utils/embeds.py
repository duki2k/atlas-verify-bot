import discord

NEON_PURPLE = 0xB026FF  # roxo neon


def retro_divider() -> str:
    return "━━━━━━━━━━━━━━━━━━━━━━"


def make_embed(
    title: str,
    footer: str,
    author_name: str | None = None,
    author_icon: str | None = None,
    thumbnail_url: str | None = None,
) -> discord.Embed:
    e = discord.Embed(title=f"{title}", color=NEON_PURPLE)

    # ✅ NÃO repetir o título dentro do texto
    # Se quiser um cabeçalho visual, deixe genérico
    e.description = f"{retro_divider()}"

    if author_name:
        e.set_author(name=author_name, icon_url=author_icon or discord.Embed.Empty)
    if thumbnail_url:
        e.set_thumbnail(url=thumbnail_url)

    e.set_footer(text=footer)
    return e
