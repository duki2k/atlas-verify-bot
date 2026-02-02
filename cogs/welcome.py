import discord
from discord.ext import commands

from config import load_settings
from utils.logging_ import setup_logging

settings = load_settings()
logger = setup_logging()


class WelcomeCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        # DM (não é garantido: depende das configs do usuário)
        try:
            dm = settings.welcome_message.format(member=member.mention)
            await member.send(dm)
        except Exception:
            pass

        # Log opcional
        if settings.log_channel_id:
            ch = member.guild.get_channel(settings.log_channel_id)
            if isinstance(ch, discord.TextChannel):
                try:
                    await ch.send(f"👋 Entrou: {member.mention} (id={member.id})")
                except Exception:
                    logger.exception("Falha ao enviar log de entrada.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(WelcomeCog(bot))
