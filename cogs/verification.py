import datetime as _dt

import discord
from discord import app_commands
from discord.ext import commands

from config import load_settings
from utils.logging_ import setup_logging

settings = load_settings()
logger = setup_logging()

VERIFY_BUTTON_CUSTOM_ID = "verifybot:verify_button"


def _account_age_days(user: discord.abc.User) -> int:
    created = user.created_at
    if created is None:
        return 9999
    now = _dt.datetime.now(tz=_dt.timezone.utc)
    return int((now - created).days)


def _channel_mention(channel_id: int | None) -> str:
    return f"<#{channel_id}>" if channel_id else ""


async def _send_post_verify_messages(guild: discord.Guild, member: discord.Member) -> None:
    # Canais
    welcome_ch = guild.get_channel(settings.welcome_channel_id) if settings.welcome_channel_id else None
    rules_ch = guild.get_channel(settings.rules_channel_id) if settings.rules_channel_id else None

    rules_mention = _channel_mention(settings.rules_channel_id)

    # Mensagens configuráveis
    welcome_text = settings.post_verify_welcome_text.format(
        member=member.mention,
        rules_channel=rules_mention,
    )
    rules_text = settings.post_verify_rules_text.format(
        member=member.mention,
        rules_channel=rules_mention,
    )

    # Envia no canal de boas-vindas (se configurado)
    if isinstance(welcome_ch, discord.TextChannel):
        try:
            await welcome_ch.send(welcome_text)
        except discord.Forbidden:
            logger.warning("Sem permissão para enviar mensagem no WELCOME_CHANNEL_ID.")
        except Exception:
            logger.exception("Falha ao enviar mensagem de boas-vindas pós-verificação.")

    # Envia no canal de regras (se configurado)
    if isinstance(rules_ch, discord.TextChannel):
        try:
            await rules_ch.send(rules_text)
        except discord.Forbidden:
            logger.warning("Sem permissão para enviar mensagem no RULES_CHANNEL_ID.")
        except Exception:
            logger.exception("Falha ao enviar mensagem de regras pós-verificação.")


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

        member: discord.Member = interaction.user
        guild = interaction.guild

        verified = guild.get_role(settings.verified_role_id)
        if not verified:
            await interaction.response.send_message(
                "Configuração inválida: VERIFIED_ROLE_ID não existe nesse servidor.",
                ephemeral=True,
            )
            return

        # Anti-raid opcional: idade mínima da conta
        min_days = settings.min_account_age_days
        if min_days > 0:
            age = _account_age_days(member)
            if age < min_days:
                await interaction.response.send_message(
                    f"Sua conta precisa ter pelo menos {min_days} dias para verificar. (idade: {age}d)",
                    ephemeral=True,
                )
                if settings.log_channel_id:
                    ch = guild.get_channel(settings.log_channel_id)
                    if isinstance(ch, discord.TextChannel):
                        try:
                            await ch.send(f"⚠️ Bloqueado por idade: {member.mention} ({age}d)")
                        except Exception:
                            pass
                return

        # Se já verificado
        if verified in member.roles:
            await interaction.response.send_message("Você já está verificado ✅", ephemeral=True)
            return

        # Dar cargo verificado
        try:
            await member.add_roles(verified, reason="Verificação por botão")
        except discord.Forbidden:
            await interaction.response.send_message(
                "Eu não tenho permissão para dar esse cargo. "
                "Confere se meu cargo está acima do cargo ✅ Verificado.",
                ephemeral=True,
            )
            return
        except Exception as e:
            logger.exception("Erro ao verificar: %s", e)
            await interaction.response.send_message("Erro inesperado. Tenta de novo.", ephemeral=True)
            return

        # Mensagens pós-verificação (boas-vindas + regras)
        await _send_post_verify_messages(guild, member)

        # Resposta pro usuário com “roteiro” clicável
        welcome_mention = _channel_mention(settings.welcome_channel_id)
        rules_mention = _channel_mention(settings.rules_channel_id)
        roteiro = "✅ Verificado! "
        if welcome_mention:
            roteiro += f"Agora vá para {welcome_mention} "
        if rules_mention:
            roteiro += f"e depois confira {rules_mention}."
        await interaction.response.send_message(roteiro, ephemeral=True)

        # Log opcional
        if settings.log_channel_id:
            ch = guild.get_channel(settings.log_channel_id)
            if isinstance(ch, discord.TextChannel):
                try:
                    await ch.send(f"✅ Verificado: {member.mention}")
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

        embed = discord.Embed(
            title="Verificação",
            description=settings.verify_message,
        )
        try:
            await ch.send(embed=embed, view=VerificationView())
            await interaction.response.send_message("Mensagem de verificação postada ✅", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("Sem permissão para enviar mensagens nesse canal.", ephemeral=True)
        except Exception as e:
            logger.exception("Erro ao postar mensagem de verificação: %s", e)
            await interaction.response.send_message("Erro ao postar a mensagem.", ephemeral=True)

    @setup_verificacao.error
    async def setup_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("Sem permissão (manage_guild).", ephemeral=True)
        else:
            logger.exception("Erro no /setup_verificacao: %s", error)
            try:
                await interaction.response.send_message("Erro ao executar o comando.", ephemeral=True)
            except Exception:
                pass


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(VerificationCog(bot))
