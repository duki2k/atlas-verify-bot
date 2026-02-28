import random
import datetime as dt
import discord
from discord.ext import commands

from config import load_settings
from utils.logging_ import setup_logging
from utils.embeds import pick_emoji, make_embed

settings = load_settings()
logger = setup_logging()


class _SafeDict(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def _local_hour() -> int:
    now_utc = dt.datetime.now(dt.timezone.utc)
    now_local = now_utc + dt.timedelta(minutes=settings.tz_offset_minutes)
    return now_local.hour


def _pick_by_time(morning: str, afternoon: str, night: str) -> str | None:
    # morning: 05-11, afternoon: 12-17, night: 18-04
    h = _local_hour()
    if 5 <= h <= 11 and morning:
        return morning
    if 12 <= h <= 17 and afternoon:
        return afternoon
    if (18 <= h <= 23 or 0 <= h <= 4) and night:
        return night
    return None


def _choose_template(*, base: str, variants: list[str], morning: str, afternoon: str, night: str) -> str:
    t = _pick_by_time(morning, afternoon, night)
    if t:
        return t
    if variants:
        return random.choice(variants)
    return base


def _apply_fun_line(text: str) -> str:
    if not settings.fun_lines:
        return text
    fun = random.choice(settings.fun_lines)
    # Se o template tiver {fun_line}, encaixa no lugar; senão, anexa no final
    if "{fun_line}" in text:
        return text.replace("{fun_line}", fun)
    return text + "\n\n" + fun


def _fmt(template: str, **kwargs) -> str:
    return template.format_map(_SafeDict(**kwargs))


class WelcomeCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        emoji = pick_emoji(settings.emoji_pool)

        # Template canal
        tpl_channel = _choose_template(
            base=settings.welcome_text,
            variants=settings.welcome_text_variants,
            morning=settings.welcome_morning,
            afternoon=settings.welcome_afternoon,
            night=settings.welcome_night,
        )

        # Template DM
        tpl_dm = _choose_template(
            base=settings.dm_welcome_text,
            variants=settings.dm_text_variants,
            morning=settings.dm_morning,
            afternoon=settings.dm_afternoon,
            night=settings.dm_night,
        )

        # Monta texto final (com safe format + fun line)
        channel_text = _apply_fun_line(_fmt(tpl_channel, member=member.mention, server=member.guild.name))
        dm_text = _apply_fun_line(_fmt(tpl_dm, member=member.mention, server=member.guild.name))

        # 1) Canal de boas-vindas
        if settings.welcome_channel_id:
            ch = member.guild.get_channel(settings.welcome_channel_id)
            if isinstance(ch, discord.TextChannel):
                try:
                    embed = make_embed(
                        title=f"{emoji} Boas-vindas — {member.guild.name}",
                        description=channel_text,
                        color=0x2ECC71,
                        footer=settings.embed_footer,
                    )
                    await ch.send(
                        embed=embed,
                        allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False),
                    )
                except Exception:
                    logger.exception("Falha ao enviar boas-vindas no canal.")

        # 2) DM
        if settings.dm_welcome_enabled:
            try:
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
                        title="🧾 Log",
                        description=f"Entrou: {member.mention}\nID: `{member.id}`",
                        color=0x95A5A6,
                        footer=settings.embed_footer,
                    )
                    await ch.send(
                        embed=log_embed,
                        allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False),
                    )
                except Exception:
                    logger.exception("Falha ao enviar log.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(WelcomeCog(bot))
