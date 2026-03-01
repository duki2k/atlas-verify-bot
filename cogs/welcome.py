import os
import random
import discord
from discord.ext import commands

from config import load_settings
from utils.embeds import make_embed, retro_divider

settings = load_settings()


def _get_text_pool() -> list[str]:
    """
    Lê WELCOME_TEXTS do ambiente.
    Formato: textos separados por '||'
    """
    raw = os.getenv("WELCOME_TEXTS", "").strip()
    if not raw:
        return []
    parts = [p.strip() for p in raw.split("||")]
    return [p for p in parts if p]


def _render(text: str, member: discord.Member) -> str:
    # troca placeholder
    return text.replace("{member}", member.mention)


class WelcomeCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.pool = _get_text_pool()

    async def _log(self, guild: discord.Guild, msg: str) -> None:
        if not settings.log_channel_id:
            return
        ch = guild.get_channel(settings.log_channel_id)
        if isinstance(ch, discord.TextChannel):
            try:
                await ch.send(msg)
            except Exception:
                pass

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        guild = member.guild

        # LOG (entrada)
        await self._log(guild, f"🟢 **ENTROU**: {member} (`{member.id}`)")

        if not settings.dm_welcome_enabled:
            return

        # escolhe texto
        if self.pool:
            text = random.choice(self.pool)
        else:
            text = "👋 Oi {member}! Bem-vindo(a) ao servidor!"

        text = _render(text, member)

        embed = make_embed(
            title="BEM-VINDO(A)",
            footer=settings.bot_name,
            author_name=settings.bot_name,
            author_icon=self.bot.user.display_avatar.url if self.bot.user else None,
        )
        embed.description = f"{retro_divider()}\n🌌 **Robô Duki te deu boas-vindas**\n{retro_divider()}\n\n{text}"

        # tenta DM
        try:
            await member.send(embed=embed)
        except Exception:
            # DM fechada: só loga
            await self._log(guild, f"🟡 DM BLOQUEADA: não consegui enviar boas-vindas para {member.mention}")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        # LOG (saída)
        await self._log(member.guild, f"🔴 **SAIU**: {member} (`{member.id}`)")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(WelcomeCog(bot))
