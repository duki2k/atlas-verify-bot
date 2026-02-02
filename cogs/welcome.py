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
        # Define cargo "pendente"
        try:
            pending = member.guild.get_role(settings.pending_role_id)
            if pending:
                await member.add_roles(pending, reason="Auto: membro entrou (pendente)")
        except discord.Forbidden:
            logger.warning("Sem permissão para adicionar cargo pendente em %s.", member.guild.id)
        except Exception as e:
            logger.exception("Erro ao adicionar cargo pendente: %s", e)

        # Mensagem no canal (se configurado)
        if settings.welcome_channel_id:
            ch = member.guild.get_channel(settings.welcome_channel_id)
            if isinstance(ch, discord.TextChannel):
                msg = settings.welcome_message.format(member=member.mention)
                try:
                    await ch.send(msg)
                except Exception:
                    logger.exception("Falha ao enviar boas-vindas no canal.")

        # DM (não é garantido - depende das configs do usuário)
        try:
            dm = settings.welcome_message.format(member=member.mention)
            await member.send(dm)
        except Exception:
            pass

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(WelcomeCog(bot))
