import datetime as _dt
import random
import discord
from discord import app_commands
from discord.ext import commands

from config import load_settings
from utils.logging_ import setup_logging

settings = load_settings()
logger = setup_logging()

VERIFY_BUTTON_CUSTOM_ID = "verifybot:verify_button"


# ---------- helpers ----------
def _pool() -> list[str]:
    return getattr(settings, "emoji_pool", ["👋", "✅", "📌", "🎉", "🛡️", "🚀", "📈", "🧠", "🗞️", "💬"])


def _pick(pool: list[str]) -> str:
    return random.choice(pool) if pool else "✨"


def _footer() -> str:
    return getattr(settings, "embed_footer", "Atlas Community")


def _ch_mention(channel_id: int | None, fallback: str = "") -> str:
    return f"<#{channel_id}>" if channel_id else fallback


def _split(text: str, limit: int = 3900) -> list[str]:
    text = (text or "").strip()
    if not text:
        return [""]
    out = []
    while len(text) > limit:
        out.append(text[:limit])
        text = text[limit:]
    out.append(text)
    return out


def _embeds(title: str, text: str, color: int, fixed_emoji: str | None = None, exact_title: bool = False) -> list[discord.Embed]:
    # exact_title=True -> não prefixa emoji no título (para "✅ Acesso liberado!")
    pool = _pool()
    emoji = fixed_emoji or _pick(pool)

    chunks = _split(text)
    embeds = []
    for i, chunk in enumerate(chunks, start=1):
        t = title if exact_title else f"{emoji} {title}"
        if len(chunks) > 1:
            t = f"{t} ({i}/{len(chunks)})"
        e = discord.Embed(title=t, description=chunk, color=color)
        e.set_footer(text=_footer())
        embeds.append(e)
    return embeds


def _account_age_days(user: discord.abc.User) -> int:
    created = user.created_at
    if created is None:
        return 9999
    now = _dt.datetime.now(tz=_dt.timezone.utc)
    return int((now - created).days)


async def _clear_bot_pins(channel: discord.TextChannel, bot_user_id: int) -> None:
    try:
        pins = await channel.pins()
    except Exception:
        return

    for msg in pins:
        if msg.author and msg.author.id == bot_user_id:
            try:
                await msg.unpin()
            except Exception:
                pass
            try:
                await msg.delete()
            except Exception:
                pass


async def _post_and_pin(channel: discord.TextChannel, embeds: list[discord.Embed]) -> None:
    for e in embeds:
        m = await channel.send(embed=e)
        try:
            await m.pin(reason="Onboarding Atlas")
        except Exception:
            pass


async def _setup_pinned_messages(guild: discord.Guild, bot_user_id: int) -> tuple[bool, str]:
    # precisa desses IDs
    if not settings.welcome_channel_id or not settings.rules_channel_id:
        return (False, "WELCOME_CHANNEL_ID / RULES_CHANNEL_ID não configurados.")

    welcome_ch = guild.get_channel(settings.welcome_channel_id)
    rules_ch = guild.get_channel(settings.rules_channel_id)

    if not isinstance(welcome_ch, discord.TextChannel) or not isinstance(rules_ch, discord.TextChannel):
        return (False, "WELCOME_CHANNEL_ID / RULES_CHANNEL_ID não apontam para canais de texto.")

    rules_mention = _ch_mention(settings.rules_channel_id, "#regras")

    # textos longos (fixados) — não marca usuário aqui
    welcome_text = settings.post_verify_welcome_text.format(
        member="👤 membro verificado",
        rules_channel=rules_mention,
    )
    rules_text = settings.post_verify_rules_text.format(
        member="👤 membro verificado",
        rules_channel=rules_mention,
    )

    # limpa pins antigos do bot (pra não virar bagunça)
    await _clear_bot_pins(welcome_ch, bot_user_id)
    await _clear_bot_pins(rules_ch, bot_user_id)

    # posta e fixa
    await _post_and_pin(welcome_ch, _embeds("Boas-vindas", welcome_text, 0x2ECC71, fixed_emoji="🎉"))
    await _post_and_pin(rules_ch, _embeds("Regras", rules_text, 0xE67E22, fixed_emoji="📌"))

    return (True, "Mensagens fixadas em #boas-vindas e #regras.")

# ---------- view ----------
class VerificationView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(label="Verificar ✅", style=discord.ButtonStyle.success, custom_id=VERIFY_BUTTON_CUSTOM_ID)
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Isso só funciona dentro de um servidor.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        member: discord.Member = interaction.user
        guild = interaction.guild

        verified = guild.get_role(settings.verified_role_id)
        if not verified:
            await interaction.followup.send(embed=_embeds("Erro", "VERIFIED_ROLE_ID inválido.", 0xE74C3C, fixed_emoji="⛔")[0], ephemeral=True)
            return

        # anti-raid opcional
        min_days = settings.min_account_age_days
        if min_days > 0:
            age = _account_age_days(member)
            if age < min_days:
                await interaction.followup.send(
                    embed=_embeds("Verificação bloqueada", f"Sua conta precisa ter **{min_days} dias**. (idade: **{age}d**)", 0xE74C3C, fixed_emoji="⛔")[0],
                    ephemeral=True,
                )
                return

        if verified in member.roles:
            await interaction.followup.send(embed=_embeds("OK", "Você já está verificado ✅", 0x2ECC71, fixed_emoji="✅")[0], ephemeral=True)
            return

        try:
            await member.add_roles(verified, reason="Verificação por botão")
        except discord.Forbidden:
            await interaction.followup.send(
                embed=_embeds("Sem permissão", "Eu não consigo dar esse cargo. Meu cargo precisa estar **acima** do ✅ Verificado.", 0xE74C3C, fixed_emoji="⛔")[0],
                ephemeral=True,
            )
            return

        # resposta FINAL (título exatamente como você pediu)
        welcome_m = _ch_mention(settings.welcome_channel_id)
        rules_m = _ch_mention(settings.rules_channel_id)
        desc = "✅ **Acesso liberado!**\n\n"
        if welcome_m:
            desc += f"1) Vá para {welcome_m}\n"
        if rules_m:
            desc += f"2) Leia {rules_m}\n"

        e = discord.Embed(title="✅ Acesso liberado!", description=desc.strip(), color=0x2ECC71)
        e.set_footer(text=_footer())
        await interaction.followup.send(embed=e, ephemeral=True)

        # log opcional
        if settings.log_channel_id:
            ch = guild.get_channel(settings.log_channel_id)
            if isinstance(ch, discord.TextChannel):
                try:
                    log = discord.Embed(title="📌 Membro verificado", description=f"{member.mention} recebeu {verified.mention}.", color=0x95A5A6)
                    log.set_footer(text=_footer())
                    await ch.send(embed=log)
                except Exception:
                    pass


# ---------- cog ----------
class VerificationCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="setup_verificacao", description="Posta verificação + fixa boas-vindas/regras (admin).")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setup_verificacao(self, interaction: discord.Interaction) -> None:
        if not interaction.guild:
            await interaction.response.send_message("Use isso dentro de um servidor.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        # 1) postar verificação
        if not settings.verify_channel_id:
            await interaction.followup.send(embed=_embeds("Erro", "VERIFY_CHANNEL_ID não configurado.", 0xE74C3C, fixed_emoji="⛔")[0], ephemeral=True)
            return

        ch = interaction.guild.get_channel(settings.verify_channel_id)
        if not isinstance(ch, discord.TextChannel):
            await interaction.followup.send(embed=_embeds("Erro", "VERIFY_CHANNEL_ID não aponta para canal de texto.", 0xE74C3C, fixed_emoji="⛔")[0], ephemeral=True)
            return

        verify_embed = _embeds("Verificação", settings.verify_message, 0x3498DB, fixed_emoji="🛡️")[0]
        await ch.send(embed=verify_embed, view=VerificationView())

        # 2) fixar mensagens longas (se configurado)
        pinned_ok = False
        pinned_msg = "Pins ignorados (sem IDs)."
        try:
            pinned_ok, pinned_msg = await _setup_pinned_messages(interaction.guild, self.bot.user.id)  # type: ignore
        except discord.Forbidden:
            pinned_msg = "Sem permissão para fixar. Dê **Gerenciar mensagens** ao bot em #boas-vindas e #regras."
        except Exception:
            logger.exception("Falha ao fixar mensagens.")
            pinned_msg = "Falha ao fixar mensagens. Verifique permissões do bot."

        # 3) resposta
        final = discord.Embed(
            title="✅ Setup concluído",
            description=f"• Verificação postada em <#{settings.verify_channel_id}>\n• {pinned_msg}",
            color=0x2ECC71 if pinned_ok else 0xF1C40F,
        )
        final.set_footer(text=_footer())
        await interaction.followup.send(embed=final, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(VerificationCog(bot))
