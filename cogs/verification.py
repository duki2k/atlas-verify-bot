import datetime as _dt

import discord
from discord import app_commands
from discord.ext import commands

from config import load_settings
from utils.logging_ import setup_logging
from utils.embeds import make_embeds_from_text

settings = load_settings()
logger = setup_logging()

VERIFY_BUTTON_CUSTOM_ID = "verifybot:verify_button"


def _account_age_days(user: discord.abc.User) -> int:
    created = user.created_at
    if created is None:
        return 9999
    now = _dt.datetime.now(tz=_dt.timezone.utc)
    return int((now - created).days)


def _ch_mention(channel_id: int | None, fallback: str = "") -> str:
    return f"<#{channel_id}>" if channel_id else fallback


async def _send_post_verify_messages(guild: discord.Guild, member: discord.Member) -> None:
    rules_mention = _ch_mention(settings.rules_channel_id, "#regras")

    # Canais configurados
    welcome_ch = guild.get_channel(settings.welcome_channel_id) if settings.welcome_channel_id else None
    rules_ch = guild.get_channel(settings.rules_channel_id) if settings.rules_channel_id else None

    # Textos (format)
    welcome_text = settings.post_verify_welcome_text.format(
        member=member.mention,
        rules_channel=rules_mention,
    )
    rules_text = settings.post_verify_rules_text.format(
        member=member.mention,
        rules_channel=rules_mention,
    )

    # Envia no canal de boas-vindas
    if isinstance(welcome_ch, discord.TextChannel):
        try:
            embeds = make_embeds_from_text(
                title="Boas-vindas",
                text=welcome_text,
                emoji_pool=settings.emoji_pool,
                footer=settings.embed_footer,
                color=0x2ECC71,
            )
            for e in embeds:
                await welcome_ch.send(embed=e)
        except discord.Forbidden:
            logger.warning("Sem permissão para enviar embed no WELCOME_CHANNEL_ID.")
        except Exception:
            logger.exception("Falha ao enviar embed de boas-vindas pós-verificação.")

    # Envia no canal de regras
    if isinstance(rules_ch, discord.TextChannel):
        try:
            embeds = make_embeds_from_text(
                title="Regras do servidor",
                text=rules_text,
                emoji_pool=settings.emoji_pool,
                footer=settings.embed_footer,
                color=0xE67E22,
            )
            for e in embeds:
                await rules_ch.send(embed=e)
        except discord.Forbidden:
            logger.warning("Sem permissão para enviar embed no RULES_CHANNEL_ID.")
        except Exception:
            logger.exception("Falha ao enviar embed de regras pós-verificação.")


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
            await interaction.response.send_message("Isso só funciona dentro de um servidor.", ephemeral=True)
            return

        # responde rápido pra não estourar timeout
        await interaction.response.defer(ephemeral=True)

        member: discord.Member = interaction.user
        guild = interaction.guild

        verified = guild.get_role(settings.verified_role_id)
        if not verified:
            embeds = make_embeds_from_text(
                title="Configuração inválida",
                text="VERIFIED_ROLE_ID não existe nesse servidor.",
                emoji_pool=settings.emoji_pool,
                footer=settings.embed_footer,
                color=0xE74C3C,
            )
            await interaction.followup.send(embed=embeds[0], ephemeral=True)
            return

        # Anti-raid opcional: idade mínima da conta
        min_days = settings.min_account_age_days
        if min_days > 0:
            age = _account_age_days(member)
            if age < min_days:
                embeds = make_embeds_from_text(
                    title="Verificação bloqueada",
                    text=f"Sua conta precisa ter pelo menos {min_days} dias. (idade atual: {age}d)",
                    emoji_pool=settings.emoji_pool,
                    footer=settings.embed_footer,
                    color=0xE74C3C,
                )
                await interaction.followup.send(embed=embeds[0], ephemeral=True)
                return

        if verified in member.roles:
            embeds = make_embeds_from_text(
                title="Já verificado",
                text="Você já está verificado ✅",
                emoji_pool=settings.emoji_pool,
                footer=settings.embed_footer,
                color=0x2ECC71,
            )
            await interaction.followup.send(embed=embeds[0], ephemeral=True)
            return

        # Dar cargo
        try:
            await member.add_roles(verified, reason="Verificação por botão")
        except discord.Forbidden:
            embeds = make_embeds_from_text(
                title="Sem permissão",
                text="Eu não consigo dar esse cargo. Confere se meu cargo está acima do ✅ Verificado.",
                emoji_pool=settings.emoji_pool,
                footer=settings.embed_footer,
                color=0xE74C3C,
            )
            await interaction.followup.send(embed=embeds[0], ephemeral=True)
            return
        except Exception as e:
            logger.exception("Erro ao verificar: %s", e)
            embeds = make_embeds_from_text(
                title="Erro",
                text="Erro inesperado ao verificar. Tenta novamente.",
                emoji_pool=settings.emoji_pool,
                footer=settings.embed_footer,
                color=0xE74C3C,
            )
            await interaction.followup.send(embed=embeds[0], ephemeral=True)
            return

        # Envia boas-vindas + regras (embeds)
        await _send_post_verify_messages(guild, member)

        # Resposta ephemeral com links
        welcome_mention = _ch_mention(settings.welcome_channel_id, "")
        rules_mention = _ch_mention(settings.rules_channel_id, "")

        roteiro = "✅ Acesso liberado!\n"
        if welcome_mention:
            roteiro += f"1) Vá para {welcome_mention}\n"
        if rules_mention:
            roteiro += f"2) Leia {rules_mention}\n"

        embeds = make_embeds_from_text(
            title="Bem-vindo(a)! 🎉",
            text=roteiro.strip(),
            emoji_pool=settings.emoji_pool,
            footer=settings.embed_footer,
            color=0x3498DB,
        )
        await interaction.followup.send(embed=embeds[0], ephemeral=True)

        # Log opcional
        if settings.log_channel_id:
            ch = guild.get_channel(settings.log_channel_id)
            if isinstance(ch, discord.TextChannel):
                try:
                    log_embeds = make_embeds_from_text(
                        title="Membro verificado",
                        text=f"{member.mention} foi verificado e recebeu {verified.mention}.",
                        emoji_pool=settings.emoji_pool,
                        footer=settings.embed_footer,
                        color=0x95A5A6,
                    )
                    await ch.send(embed=log_embeds[0])
                except Exception:
                    pass


class VerificationCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="setup_verificacao",
        description="Posta a mensagem com botão de verificação no canal configurado (admin).",
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setup_verificacao(self, interaction: discord.Interaction) -> None:
        if not interaction.guild:
            await interaction.response.send_message("Use isso dentro de um servidor.", ephemeral=True)
            return

        if not settings.verify_channel_id:
            await interaction.response.send_message("VERIFY_CHANNEL_ID não configurado.", ephemeral=True)
            return

        ch = interaction.guild.get_channel(settings.verify_channel_id)
        if not isinstance(ch, discord.TextChannel):
            await interaction.response.send_message("VERIFY_CHANNEL_ID não aponta para um canal de texto.", ephemeral=True)
            return

        embeds = make_embeds_from_text(
            title="Verificação",
            text=settings.verify_message,
            emoji_pool=settings.emoji_pool,
            footer=settings.embed_footer,
            color=0x3498DB,
        )
        try:
            await ch.send(embed=embeds[0], view=VerificationView())
            ok = make_embeds_from_text(
                title="OK",
                text="Mensagem de verificação postada ✅",
                emoji_pool=settings.emoji_pool,
                footer=settings.embed_footer,
                color=0x2ECC71,
            )
            await interaction.response.send_message(embed=ok[0], ephemeral=True)
        except discord.Forbidden:
            err = make_embeds_from_text(
                title="Sem permissão",
                text="Eu não consigo enviar mensagem nesse canal.",
                emoji_pool=settings.emoji_pool,
                footer=settings.embed_footer,
                color=0xE74C3C,
            )
            await interaction.response.send_message(embed=err[0], ephemeral=True)
        except Exception as e:
            logger.exception("Erro ao postar verificação: %s", e)
            err = make_embeds_from_text(
                title="Erro",
                text="Erro ao postar a mensagem de verificação.",
                emoji_pool=settings.emoji_pool,
                footer=settings.embed_footer,
                color=0xE74C3C,
            )
            await interaction.response.send_message(embed=err[0], ephemeral=True)

    @setup_verificacao.error
    async def setup_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        if isinstance(error, app_commands.MissingPermissions):
            embeds = make_embeds_from_text(
                title="Sem permissão",
                text="Você precisa de permissão de Gerenciar Servidor.",
                emoji_pool=settings.emoji_pool,
                footer=settings.embed_footer,
                color=0xE74C3C,
            )
            try:
                await interaction.response.send_message(embed=embeds[0], ephemeral=True)
            except Exception:
                pass
        else:
            logger.exception("Erro no /setup_verificacao: %s", error)
            embeds = make_embeds_from_text(
                title="Erro",
                text="Erro ao executar o comando.",
                emoji_pool=settings.emoji_pool,
                footer=settings.embed_footer,
                color=0xE74C3C,
            )
            try:
                await interaction.response.send_message(embed=embeds[0], ephemeral=True)
            except Exception:
                pass


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(VerificationCog(bot))
