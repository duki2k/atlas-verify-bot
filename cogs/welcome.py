import random
import re
import discord
from discord.ext import commands

from config import load_settings
from utils.logging_ import setup_logging
from utils.embeds import pick_emoji, make_embed, NEON_PURPLE

settings = load_settings()
logger = setup_logging()


def pick_welcome_template() -> str:
    pool = [settings.welcome_text] + (settings.welcome_text_variants or [])
    return random.choice(pool)


def prettify_gamer(text: str) -> str:
    """
    Gamer caótico porém legível:
    - abre respiro em blocos com emojis (🎉 📌 🚀 etc.)
    - bullets em linhas
    - pergunta final em destaque simples (🎯)
    - sem títulos "chatgptizados"
    """
    t = (text or "").strip()
    t = t.replace("\r", "")
    t = re.sub(r"[ \t]{2,}", " ", t)

    # força respiro antes de marcadores comuns
    markers = ["🎉", "📌", "🚀", "🎮", "😂", "🎧", "🕹️", "🎲", "🌌", "🌟", "🛸", "🌠", "🔥", "💬", "🤝", "⚠️"]
    for m in markers:
        t = re.sub(rf"(?<!^)\s*{re.escape(m)}\s*", f"\n\n{m} ", t)

    # bullets sempre em linha
    t = t.replace(" • ", "\n• ")
    t = re.sub(r"\s*•\s*", "\n• ", t)

    # pergunta final: pega a última frase que termina com '?'
    q_positions = [m.start() for m in re.finditer(r"\?", t)]
    if q_positions:
        last_q = q_positions[-1]
        start = max(t.rfind("\n", 0, last_q), t.rfind(". ", 0, last_q), t.rfind("! ", 0, last_q))
        if start == -1:
            start = 0
        else:
            start += 2 if t[start:start+2] in [". ", "! "] else 1

        question = t[start:last_q + 1].strip()
        before = t[:start].rstrip()

        t = before + ("\n\n" if before else "")
        t += f"🎯 {question}"

    # compacta excesso de quebra
    t = re.sub(r"\n{3,}", "\n\n", t).strip()

    # corta se passar do limite com sutileza (sem msg meta)
    if len(t) > 3800:
        t = t[:3800].rstrip() + "…"

    return t


def _thumb_url(guild: discord.Guild, bot_user: discord.ClientUser | None) -> str | None:
    # Prioridade: ícone do servidor; fallback: avatar do bot
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

        thumb = _thumb_url(member.guild, self.bot.user)
        member_count = member.guild.member_count or 0

        # 1) Servidor: aleatório + formatado
        if settings.welcome_channel_id:
            ch = member.guild.get_channel(settings.welcome_channel_id)
            if isinstance(ch, discord.TextChannel):
                try:
                    tpl = pick_welcome_template()
                    raw = tpl.format(member=member.mention, server=member.guild.name)
                    text = prettify_gamer(raw)

                    embed = make_embed(
                        title=f"{emoji} Boas-vindas 💜",
                        description=text,
                        footer=f"{settings.embed_footer} • {member_count} membros",
                        color=NEON_PURPLE,
                        thumbnail_url=thumb,
                    )
                    await ch.send(
                        embed=embed,
                        allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False),
                    )
                except Exception:
                    logger.exception("Falha ao enviar boas-vindas no canal.")

        # 2) DM: fallback fixo (pra não repetir a do servidor)
        if settings.dm_welcome_enabled:
            try:
                dm_raw = settings.dm_welcome_text.format(member=member.mention, server=member.guild.name)
                dm_text = prettify_gamer(dm_raw)

                dm_embed = make_embed(
                    title=f"{emoji} Bem-vindo(a) 💜",
                    description=dm_text,
                    footer=settings.embed_footer,
                    color=NEON_PURPLE,
                    thumbnail_url=thumb,
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
                        footer=settings.embed_footer,
                        color=NEON_PURPLE,
                        thumbnail_url=thumb,
                    )
                    await ch.send(
                        embed=log_embed,
                        allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False),
                    )
                except Exception:
                    logger.exception("Falha ao enviar log.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(WelcomeCog(bot))
