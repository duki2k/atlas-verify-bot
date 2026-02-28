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


def prettify_gamer_chaos(text: str) -> str:
    """
    Gamer caótico, mas legível:
    - separa em blocos (🎉 📌 🚀 🎮 etc.)
    - quebra bullets em linhas
    - cria "pergunta final" destacada
    - adiciona respiro (linhas em branco)
    """
    t = (text or "").strip()

    # 1) Normaliza espaços estranhos
    t = t.replace("\r", "")
    t = re.sub(r"[ \t]{2,}", " ", t)

    # 2) Garante que marcadores de seção virem novos blocos
    section_markers = ["🎉", "📌", "🚀", "🎮", "😂", "🎧", "🕹️", "🎲", "🌌", "🌟", "🛸", "🌠", "⚠️", "🔥", "💬", "🤝"]
    for m in section_markers:
        # se marcador aparece no meio, puxa pra novo bloco
        t = re.sub(rf"(?<!^)\s*{re.escape(m)}\s*", f"\n\n{m} ", t)

    # 3) Bullets sempre em linhas
    # casos comuns: "• texto" ou " • texto"
    t = t.replace(" • ", "\n• ")
    t = re.sub(r"\s*•\s*", "\n• ", t)

    # 4) Destaque de "pergunta final" (última frase com ?)
    # Se tiver mais de uma ?, pega a última
    q_positions = [m.start() for m in re.finditer(r"\?", t)]
    if q_positions:
        last_q = q_positions[-1]
        # tenta achar o começo da sentença da pergunta
        start = max(t.rfind("\n", 0, last_q), t.rfind(". ", 0, last_q), t.rfind("! ", 0, last_q))
        if start == -1:
            start = 0
        else:
            # se foi ". " ou "! ", avança 2; se foi "\n", avança 1
            start += 2 if t[start:start+2] in [". ", "! "] else 1

        question = t[start:last_q + 1].strip()
        before = t[:start].rstrip()

        # remove a pergunta do meio e joga como bloco final
        t = before + ("\n\n" if before else "")
        t += "🎯 **Pergunta da resenha:**\n" + f"👉 {question}"

    # 5) Compacta excesso de quebras
    t = re.sub(r"\n{3,}", "\n\n", t).strip()

    # 6) Se ficou MUITO grande, corta com elegância (embed limit: 4096)
    if len(t) > 3800:
        t = t[:3800].rstrip() + "\n\n⚠️ *Mensagem encurtada pra caber no embed.*"

    return t


class WelcomeCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        emoji = pick_emoji(settings.emoji_pool)

        # 1) Servidor: aleatório + gamer-chaos format
        if settings.welcome_channel_id:
            ch = member.guild.get_channel(settings.welcome_channel_id)
            if isinstance(ch, discord.TextChannel):
                try:
                    tpl = pick_welcome_template()
                    raw = tpl.format(member=member.mention, server=member.guild.name)
                    text = prettify_gamer_chaos(raw)

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

        # 2) DM: fallback fixo (pra não repetir)
        if settings.dm_welcome_enabled:
            try:
                dm_raw = settings.dm_welcome_text.format(member=member.mention, server=member.guild.name)
                dm_text = prettify_gamer_chaos(dm_raw)

                dm_embed = make_embed(
                    title=f"{emoji} Bem-vindo(a)!",
                    description=dm_text,
                    color=0x3498DB,
                    footer=settings.embed_footer,
                )
                await member.send(embed=dm_embed)
            except Exception:
                pass

        # 3) Log
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
                    await ch.send(
                        embed=log_embed,
                        allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False),
                    )
                except Exception:
                    logger.exception("Falha ao enviar log.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(WelcomeCog(bot))
