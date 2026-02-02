import discord
from discord.ext import commands

from config import load_settings
from utils.logging_ import setup_logging
from utils.embeds import make_embeds

settings = load_settings()
logger = setup_logging()


def _mention_channel(channel_id: int | None, fallback: str) -> str:
    return f"<#{channel_id}>" if channel_id else fallback


class WelcomeCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        # DM (opcional e silencioso)
        try:
            verify_ch = _mention_channel(settings.verify_channel_id, "#verificação")
            text = settings.welcome_dm_text.format(member=member.mention, verify_channel=verify_ch)
            dm_embed = make_embeds(
                title="👋 Bem-vindo(a)!",
                text=text,
                color=0x2ECC71,
                footer=settings.embed_footer,
            )[0]
            await member.send(embed=dm_embed)
        except Exception:
            pass

        # log de entrada
        if settings.log_channel_id:
            ch = member.guild.get_channel(settings.log_channel_id)
            if isinstance(ch, discord.TextChannel):
                try:
                    e = make_embeds(
                        title="🟦 Novo membro",
                        text=f"{member.mention} entrou no servidor.\nID: `{member.id}`",
                        color=0x95A5A6,
                        footer=settings.embed_footer,
                    )[0]
                    await ch.send(embed=e)
                except Exception:
                    logger.exception("Falha ao enviar log de entrada.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(WelcomeCog(bot))
