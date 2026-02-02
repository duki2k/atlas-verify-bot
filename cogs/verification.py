import datetime as _dt

import discord
from discord import app_commands
from discord.ext import commands

from config import load_settings
from utils.logging_ import setup_logging
from utils.embeds import make_embeds

settings = load_settings()
logger = setup_logging()

VERIFY_BUTTON_CUSTOM_ID = "verifybot:verify_button"


def _account_age_days(user: discord.abc.User) -> int:
    created = user.created_at
    if created is None:
        return 9999
    now = _dt.datetime.now(tz=_dt.timezone.utc)
    return int((now - created).days)


def _mention_channel(channel_id: int | None, fallback: str) -> str:
    return f"<#{channel_id}>" if channel_id else fallback


def _role_mention(role_id: int) -> str:
    return f"<@&{role_id}>"


async def _clear_bot_pins(channel: discord.TextChannel, bot_id: int) -> None:
    try:
        pins = await channel.pins()
    except Exception:
        return
    for msg in pins:
        if msg.author and msg.author.id == bot_id:
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
        m = await channel.send(
            embed=e,
            # ✅ mostra menções sem notificar geral
            allowed_mentions=discord.AllowedMentions(users=False, roles=False, everyone=False),
        )
        try:
            await m.pin(reason="Atlas onboarding")
        except Exception:
            pass


async def _setup_pinned_messages(guild: discord.Guild, bot_id: int) -> tuple[bool, str]:
    if not settings.welcome_channel_id or not settings.rules_channel_id:
        return (False, "Pins ignorados: WELCOME_CHANNEL_ID/RULES_CHANNEL_ID não configurados.")

    welcome_ch = guild.get_channel(settings.welcome_channel_id)
    rules_ch = guild.get_channel(settings.rules_channel_id)

    if not isinstance(welcome_ch, discord.TextChannel) or not isinstance(rules_ch, discord.TextChannel):
        return (False, "Pins ignorados: IDs não apontam para canais de texto.")

    rules_mention = _mention_channel(settings.rules_channel_id, "#regras")
    member_role = _role_mention(settings.verified_role_id)  # ✅ “marcar o cargo Membro” (mesmo ID do VERIFIED_ROLE_ID)

    welcome_text = settings.pinned_welcome_text.format(
        member_role=member_role,
        rules_channel=rules_mention,
    )
    rules_text = settings.pinned_rules_text.format(
        member_role=member_role,
        rules_channel=rules_mention,
    )

    # limpa pins antigos do bot para não acumular
    await _clear_bot_pins(welcome_ch, bot_id)
    await _clear_bot_pins(rules_ch, bot_id)

    welcome_embeds = make_embeds(
        title="🎉 Boas-vindas",
        text=welcome_text,
        color=0x2ECC71,
        footer=settings.embed_footer,
    )
    rules_embeds = make_embeds(
        title="📌 Regras",
        text=rules_text,
        color=0xE67E22,
        footer=settings.embed_footer,
    )

    await _post_and_pin(welcome_ch, welcome_embeds)
    await _post_and_pin(rules_ch, rules_embeds)

    return (True, "Mensagens fixadas em #boas-vindas e #regras.")


class VerificationView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Verificar ✅",
        style=discord.ButtonStyle.success,
        custom_id=VERIFY_BUTTON_CUSTOM_ID,
    )
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Use isso dentro de um servidor.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        member: discord.Member = interaction.user
        guild = interaction.guild

        verified_role = guild.get_role(settings.verified_role_id)
        if not verified_role:
            e = make_embeds(
                title="⛔ Erro",
                text="VERIFIED_ROLE_ID não existe nesse servidor.",
                color=0xE74C3C,
                footer=settings.embed_footer,
            )[0]
            await interaction.followup.send(embed=e, ephemeral=True)
            return

        # Anti-raid opcional
        if settings.min_account_age_days > 0:
            age = _account_age_days(member)
            if age < settings.min_account_age_days:
                e = make_embeds(
                    title="⛔ Verificação bloqueada",
                    text=f"Sua conta precisa ter pelo menos **{settings.min_account_age_days} dias**.\nIdade atual: **{age}d**",
                    color=0xE74C3C,
                    footer=settings.embed_footer,
                )[0]
                await interaction.followup.send(embed=e, ephemeral=True)
                return

        if verified_role in member.roles:
            e = make_embeds(
                title="✅ Já verificado",
                text="Você já está verificado.",
                color=0x2ECC71,
                footer=settings.embed_footer,
            )[0]
            await interaction.followup.send(embed=e, ephemeral=True)
            return

        try:
            await member.add_roles(verified_role, reason="Verificação por botão")
        except discord.Forbidden:
            e = make_embeds(
                title="⛔ Sem permissão",
                text="Eu não consigo dar esse cargo. Coloque o **cargo do bot acima** do cargo ✅ Verificado.",
                color=0xE74C3C,
                footer=settings.embed_footer,
            )[0]
            await interaction.followup.send(embed=e, ephemeral=True)
            return
        except Exception:
            logger.exception("Erro ao adicionar cargo.")
            e = make_embeds(
                title="⛔ Erro",
                text="Erro inesperado ao verificar. Tente novamente.",
                color=0xE74C3C,
                footer=settings.embed_footer,
            )[0]
            await interaction.followup.send(embed=e, ephemeral=True)
            return

        # ✅ Resposta final EXATA como você pediu
        welcome_m = _mention_channel(settings.welcome_channel_id, "#boas-vindas")
        rules_m = _mention_channel(settings.rules_channel_id, "#regras")

        desc = f"1) Vá para {welcome_m}\n2) Leia {rules_m}"
        e = discord.Embed(title="✅ Acesso liberado!", description=desc, color=0x2ECC71)
        e.set_footer(text=settings.embed_footer)
        await interaction.followup.send(embed=e, ephemeral=True)

        # log de verificação
        if settings.log_channel_id:
            ch = guild.get_channel(settings.log_channel_id)
            if isinstance(ch, discord.TextChannel):
                try:
                    log = discord.Embed(
                        title="🟩 Membro verificado",
                        description=f"{member.mention} recebeu {verified_role.mention}.\nID: `{member.id}`",
                        color=0x95A5A6,
                    )
                    log.set_footer(text=settings.embed_footer)
                    await ch.send(embed=log)
                except Exception:
                    pass


class VerificationCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="setup_verificacao",
        description="Posta a verificação e fixa boas-vindas/regras (admin).",
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setup_verificacao(self, interaction: discord.Interaction) -> None:
        if not interaction.guild:
            await interaction.response.send_message("Use isso dentro de um servidor.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        if not settings.verify_channel_id:
            e = make_embeds(
                title="⛔ Erro",
                text="VERIFY_CHANNEL_ID não configurado.",
                color=0xE74C3C,
                footer=settings.embed_footer,
            )[0]
            await interaction.followup.send(embed=e, ephemeral=True)
            return

        ch = interaction.guild.get_channel(settings.verify_channel_id)
        if not isinstance(ch, discord.TextChannel):
            e = make_embeds(
                title="⛔ Erro",
                text="VERIFY_CHANNEL_ID não aponta para um canal de texto.",
                color=0xE74C3C,
                footer=settings.embed_footer,
            )[0]
            await interaction.followup.send(embed=e, ephemeral=True)
            return

        # Posta mensagem de verificação (com botão)
        verify_embed = make_embeds(
            title="🛡️ Verificação",
            text=settings.verify_message,
            color=0x3498DB,
            footer=settings.embed_footer,
        )[0]
        await ch.send(embed=verify_embed, view=VerificationView())

        # Fixar mensagens (boas-vindas + regras)
        pinned_ok = False
        pinned_msg = ""
        try:
            pinned_ok, pinned_msg = await _setup_pinned_messages(interaction.guild, self.bot.user.id)  # type: ignore
        except discord.Forbidden:
            pinned_msg = "Sem permissão para fixar. Dê **Gerenciar mensagens** ao bot em #boas-vindas e #regras."
        except Exception:
            logger.exception("Falha ao fixar mensagens.")
            pinned_msg = "Falha ao fixar mensagens. Verifique permissões do bot."

        status_color = 0x2ECC71 if pinned_ok else 0xF1C40F
        resp = discord.Embed(
            title="✅ Setup concluído",
            description=f"• Verificação postada em <#{settings.verify_channel_id}>\n• {pinned_msg or 'Pins processados.'}",
            color=status_color,
        )
        resp.set_footer(text=settings.embed_footer)
        await interaction.followup.send(embed=resp, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(VerificationCog(bot))
