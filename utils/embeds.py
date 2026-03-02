import discord

# Roxo neon (premium gamer)
NEON_PURPLE = 0xB026FF


def retro_divider() -> str:
    # Separador visual consistente e legível
    return "━━━━━━━━━━━━━━━━━━━━━━"


def make_embed(
    title: str | None = None,
    footer: str | None = None,
    author_name: str | None = None,
    author_icon: str | None = None,
    thumbnail_url: str | None = None,
    image_url: str | None = None,
) -> discord.Embed:
    """
    Embed base padronizado (roxo neon).
    - NÃO injeta título dentro do description (evita duplicação).
    - Deixa o caller decidir o layout do texto.
    """
    e = discord.Embed(color=NEON_PURPLE)

    if title:
        e.title = title

    if author_name:
        # discord.Embed.Empty evita erro se author_icon=None
        e.set_author(name=author_name, icon_url=author_icon or discord.Embed.Empty)

    if thumbnail_url:
        e.set_thumbnail(url=thumbnail_url)

    if image_url:
        e.set_image(url=image_url)

    if footer:
        e.set_footer(text=footer)

    return e


def format_embed_body(text: str, *, add_divider_top: bool = True, add_divider_bottom: bool = False) -> str:
    """
    Formata o corpo do embed com divisória opcional.
    Não repete título.
    """
    parts: list[str] = []
    if add_divider_top:
        parts.append(retro_divider())
    parts.append(text.strip())
    if add_divider_bottom:
        parts.append(retro_divider())
    return "\n\n".join(parts).strip()
