import random
import re
import discord
from discord.ext import commands

from config import load_settings
from utils.logging_ import setup_logging
from utils.embeds import pick_emoji, make_embed

settings = load_settings()
logger = setup_logging()


def pick_welcome_template() -> str:
    pool = [settings.welcome_text] + (settings.welcome_text_variants or [])
    return random.choice(pool)


def prettify(text: str) -> str:
    """
    Deixa o texto mais legível no embed:
    - cria separação entre blocos (🎉 📌 🚀 etc)
    - quebra bullets em linhas
    - reduz espaços duplicados
    """
    t = text.strip()

    # garante espaçamento antes de blocos/sessões (quando não estiver no começo)
    for marker in ["🎉", "📌", "🚀", "🎮", "😂", "🎧", "🌌", "🌟", "🛸", "🌠", "🕹️", "🎲", "⚠️"]:
        t = re.sub(rf"(?<!^)\s*{re.escape(marker)}\s*", f"\n\n{marker} ", t)

    # bullets em linha separada
    t = t.replace(" • ", "\n• ")
    t = t.replace("• ", "• ")  # mantém

    # limpeza: remove excesso de espaços
    t = re.sub(r"[ \t]{2,}", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)

    return t.strip()


class WelcomeCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        emoji = pick_emoji(settings.emoji_pool)

        # 1) Servidor: mensagem aleatória + formatação bonita
        if settings.welcome_channel_id:
            ch = member.guild.get_channel(settings.welcome_channel_id)
            if isinstance(ch, discord.TextChannel):
                try:
                    tpl = pick_welcome_template()
                    raw = tpl.format(member=member.mention, server=member.guild.name)
                    text = prettify(raw)

                    embed = make_embed(
                        title=f"{emoji} Boas-vindas — {member.guild.name}",
                        description=text,
                        color=0x2ECC71,
                        footer=settings.embed_footer,
                    )
                    await ch.send(
                        embed=embed,
                        allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False),
                    )
                except Exception:
                    logger.exception("Falha ao enviar boas-vindas no canal.")

        # 2) DM: fallback fixo (também formatado)
        if settings.dm_welcome_enabled:
            try:
                dm_raw = settings.dm_welcome_text.format(member=member.mention, server=member.guild.name)
                dm_text = prettify(dm_raw)

                dm_embed = make_embed(
                    title=f"{emoji} Bem-vindo(a)!",
                    description=dm_text,
                    color=0x3498DB,
                    footer=settings.embed_footer,
                )
                await member.send(embed=dm_embed)
            except Exception:
                pass

        # 3) Log (opcional)
        if settings.log_channel_id:
            ch = member.guild.get_channel(settings.log_channel_id)
            if isinstance(ch, discord.TextChannel):
                try:
                    log_embed = make_embed(
                        title="🟢 Entrou",
                        description=f"{member.mention}\nID: `{member.id}`",
                        color=0x95A5A6,
                        footer=settings.embed_footer,
                    )
                    await ch.send(embed=log_embed, allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False))
                except Exception:
                    logger.exception("Falha ao enviar log.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(WelcomeCog(bot))
