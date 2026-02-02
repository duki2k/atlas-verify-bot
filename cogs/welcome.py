import discord
from discord.ext import commands

from config import load_settings
from utils.logging_ import setup_logging
from utils.embeds import make_embeds_from_text

settings = load_settings()
logger = setup_logging()


def _rules_mention() -> str:
    return f"<#{settings.rules_channel_id}>" if settings.rules_channel_id else "#regras"


class WelcomeCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        # DM em embed
        try:
            text = settings.welcome_message.format(
                member=member.mention,
                rules_channel=_rules_mention(),
            )
            embeds = make_embeds_from_text(
                title="Bem-vindo(a)!",
                text=text,
                emoji_pool=settings.emoji_pool,
                footer=settings.embed_footer,
                color=0x2ECC71,
            )
            for e in embeds:
                await member.send(embed=e)
        except Exception:
            pass

        # Log opcional em embed
        if settings.log_channel_id:
            ch = member.guild.get_channel(settings.log_channel_id)
            if isinstance(ch, discord.TextChannel):
                try:
                    embeds = make_embeds_from_text(
                        title="Novo membro",
                        text=f"{member.mention} entrou no servidor. (id={member.id})",
                        emoji_pool=settings.emoji_pool,
                        footer=settings.embed_footer,
                        color=0x95A5A6,
                    )
                    await ch.send(embed=embeds[0])
                except Exception:
                    logger.exception("Falha ao enviar log de entrada.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(WelcomeCog(bot))
