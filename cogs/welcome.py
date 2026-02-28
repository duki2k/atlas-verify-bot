import discord
from discord.ext import commands

from config import load_settings
from utils.logging_ import setup_logging
from utils.embeds import pick_emoji, make_embed

settings = load_settings()
logger = setup_logging()


class WelcomeCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        emoji = pick_emoji(settings.emoji_pool)

        # 1) Boas-vindas no canal
        if settings.welcome_channel_id:
            ch = member.guild.get_channel(settings.welcome_channel_id)
            if isinstance(ch, discord.TextChannel):
                try:
                    text = settings.welcome_text.format(member=member.mention, server=member.guild.name)
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

        # 2) DM (opcional)
        if settings.dm_welcome_enabled:
            try:
                dm_text = settings.dm_welcome_text.format(member=member.mention, server=member.guild.name)
                dm_embed = make_embed(
                    title=f"{emoji} Bem-vindo(a)!",
                    description=dm_text,
                    color=0x3498DB,
                    footer=settings.embed_footer,
                )
                await member.send(embed=dm_embed)
            except Exception:
                pass  # DM pode estar bloqueada

        # 3) Log de entrada (opcional)
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
                    logger.exception("Falha ao enviar log de entrada.")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        # Log de saída (opcional)
        if settings.log_channel_id:
            ch = member.guild.get_channel(settings.log_channel_id)
            if isinstance(ch, discord.TextChannel):
                try:
                    log_embed = make_embed(
                        title="🔴 Saiu",
                        description=f"{member.mention}\nID: `{member.id}`",
                        color=0x95A5A6,
                        footer=settings.embed_footer,
                    )
                    await ch.send(embed=log_embed, allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False))
                except Exception:
                    logger.exception("Falha ao enviar log de saída.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(WelcomeCog(bot))
