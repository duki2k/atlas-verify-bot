import os
import discord
from discord.ext import commands

from config import load_settings
from utils.embeds import make_embed, retro_divider

settings = load_settings()


def _render(text: str, member: discord.Member) -> str:
    return text.replace("{member}", member.mention)


class WelcomeCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.text = os.getenv("DM_WELCOME_TEXT", "").strip()

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

        # log entrada
        await self._log(guild, f"🟢 ENTROU: {member} ({member.id})")

        if not settings.dm_welcome_enabled:
            return

        if not self.text:
            return

        text = _render(self.text, member)

        embed = make_embed(
            title="BEM-VINDO(A)",
            footer=settings.bot_name,
            author_name=settings.bot_name,
            author_icon=self.bot.user.display_avatar.url if self.bot.user else None,
        )

        embed.description = (
            f"{retro_divider()}\n"
            f"🌌 Robô Duki te deu boas-vindas\n"
            f"{retro_divider()}\n\n"
            f"{text}"
        )

        try:
            await member.send(embed=embed)
        except Exception:
            await self._log(guild, f"⚠️ DM BLOQUEADA: {member.mention}")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        await self._log(member.guild, f"🔴 SAIU: {member} ({member.id})")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(WelcomeCog(bot))
