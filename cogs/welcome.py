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


def prettify_retro(text: str) -> str:
    t = (text or "").strip()
    t = re.sub(r"[ \t]{2,}", " ", t)

    markers = ["🎉", "📌", "🚀", "🎮", "😂", "🎧", "🕹️", "🎲", "🌌", "🌟", "🛸", "🌠", "🔥", "💬", "🤝", "⚠️"]
    for m in markers:
        t = re.sub(rf"(?<!^)\s*{re.escape(m)}\s*", f"\n\n{m} ", t)

    t = t.replace(" • ", "\n• ")
    t = re.sub(r"\s*•\s*", "\n• ", t)
    t = re.sub(r"\n{3,}", "\n\n", t).strip()

    if len(t) > 3800:
        t = t[:3800].rstrip() + "…"
    return t


def thumb_url(guild: discord.Guild, bot_user: discord.ClientUser | None) -> str | None:
    if guild.icon:
        return guild.icon.url
    if bot_user and bot_user.display_avatar:
        return bot_user.display_avatar.url
    return None


class WelcomeCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        emoji = pick_emoji(settings.emoji_pool)
        thumb = thumb_url(member.guild, self.bot.user)

        if settings.welcome_channel_id:
            ch = member.guild.get_channel(settings.welcome_channel_id)
            if isinstance(ch, discord.TextChannel):
                try:
                    tpl = pick_welcome_template()
                    raw = tpl.format(member=member.mention, server=member.guild.name)
                    text = prettify_retro(raw)

                    # “Robô Duki te deu boas-vindas” sem cara de template
                    text = f"🕹️ **{settings.bot_name}** te deu boas-vindas.\n\n{text}"

                    embed = make_embed(
                        title=f"{emoji} BOAS-VINDAS",
                        description=text,
                        footer=settings.embed_footer,
                        thumbnail_url=thumb,
                    )
                    await ch.send(
                        embed=embed,
                        allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False),
                    )
                except Exception:
                    logger.exception("Falha ao enviar boas-vindas no canal.")

        if settings.dm_welcome_enabled:
            try:
                dm_raw = settings.dm_welcome_text.format(member=member.mention, server=member.guild.name)
                dm_text = prettify_retro(dm_raw)
                dm_text = f"🕹️ **{settings.bot_name}** aqui.\n\n{dm_text}"

                dm_embed = make_embed(
                    title=f"{emoji} CHEGOU!",
                    description=dm_text,
                    footer=settings.embed_footer,
                    thumbnail_url=thumb,
                )
                await member.send(embed=dm_embed)
            except Exception:
                pass

        if settings.log_channel_id:
            ch = member.guild.get_channel(settings.log_channel_id)
            if isinstance(ch, discord.TextChannel):
                try:
                    embed = make_embed(
                        title="LOG +1",
                        description=f"🟢 Entrou: {member.mention}\n🆔 `{member.id}`",
                        footer=settings.embed_footer,
                        thumbnail_url=thumb,
                    )
                    await ch.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
                except Exception:
                    logger.exception("Falha ao enviar log.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(WelcomeCog(bot))
