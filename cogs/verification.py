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


def _ch_mention(channel_id: int | None) -> str:
    return f"<#{channel_id}>" if channel_id else ""


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
            await m.pin(reason="Onboarding")
        except Exception:
            pass


async def _setup_pinned_messages(guild: discord.Guild, bot_user_id: int) -> None:
    if not settings.welcome_channel_id or not settings.rules_channel_id:
        return

    welcome_ch = guild.get_channel(settings.welcome_channel_id)
    rules_ch = guild.get_channel(settings.rules_channel_id)

    if not isinstance(welcome_ch, discord.TextChannel) or not isinstance(rules_ch, discord.TextChannel):
        return

    rules_mention = _ch_mention(settings.rules_channel_id) or "#regras"

    welcome_text = settings.post_verify_welcome_text.format(
        member="{member}",
        rules_channel=rules_mention,
    )
    rules_text = settings.post_verify_rules_text.format(
        member="{member}",
        rules_channel=rules_mention,
    )

    # remove pins antigos do bot, posta novamente e fixa
    await _clear_bot_pins(welcome_ch, bot_user_id)
    await _clear_bot_pins(rules_ch, bot_user_id)

    welcome_embeds = make_embeds_from_text(
        title="Boas-vindas",
        text=welcome_text.replace("{member}", "👤 (membro verificado)"),
        emoji_pool=settings.emoji_pool,
        footer=settings.embed_footer,
        color=0x2ECC71,
        prefix_emoji=False,  # título limpo
        fixed_emoji="🎉",
    )
    rules_embeds = make_embeds_from_text(
        title="Regras",
        text=rules_text.replace("{member}", "👤 (membro verificado)"),
        emoji_pool=settings.emoji_pool,
        footer=settings.embed_footer,
        color=0xE67E22,
        prefix_emoji=False,
        fixed_emoji="📌",
    )

    await _post_and_pin(welcome_ch, welcome_embeds)
    await _post_and_pin(rules_ch, rules_embeds)


async def _ping_member_after_verify(guild: discord.Guild, member: discord.Member) -> None:
    welcome_ch = guild.get_channel(settings.welcome_channel_id) if settings.welcome_channel_id else None
    rules_ch = guild.get_channel(settings.rules_channel_id) if settings.rules_channel_id else None

    # embed curto marcando o membro — pra ele notar a mensagem fixada
    if isinstance(welcome_ch, discord.TextChannel):
        try:
            embeds = make_embeds_from_text(
                title="Boas-vindas",
                text=f"{member.mention} 👋 Leia a mensagem **fixada** 📌 aqui no canal para começar.",
                emoji_pool=settings.emoji_pool,
                footer=settings.embed_footer,
                color=0x2ECC71,
                prefix_emoji=False,
                fixed_emoji="🎉",
            )
            await welcome_ch.send(embed=embeds[0])
        except Exception:
            logger.exception("Falha ao pingar no canal de boas-vindas.")

    if isinstance(rules_ch, discord.TextChannel):
        try:
            embeds = make_embeds_from_text(
                title="Regras",
                text=f"{member.mention} ✅ Leia a mensagem **fixada** 📌 com as regras antes de postar.",
                emoji_pool=settings.emoji_pool,
                footer=settings.embed_footer,
                color=0xE67E22,
                prefix_emoji=False,
                fixed_emoji="📌",
            )
            await rules_ch.send(embed=embeds[0])
        except Exception:
            logger.exception("Falha ao pingar no canal de regras.")


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

        await interaction.response.defer(ephemeral=True)

        member: discord.Member = interaction.user
        guild = interaction.guild

        verified = guild.get_role(settings.verified_role_id)
        if not verified:
            await interaction.followup.send("VERIFIED_ROLE_ID inválido.", ephemeral=True)
            return

        # Anti-raid opcional
        min_days = settings.min_account_age_days
        if min_days > 0:
            age = _account_age_days(member)
            if age < min_days:
                e = discord.Embed(
                    title="⛔ Verificação bloqueada",
                    description=f"Sua conta precisa ter pelo menos **{min_days} dias**. (idade atual: **{age}d**)",
                    color=0xE74C3C,
                )
                e.set_footer(text=settings.embed_footer)
                await interaction.followup.send(embed=e, ephemeral=True)
                return

        if verified in member.roles:
            e = discord.Embed(
                title="✅ Você já está verificado",
                description="Tudo certo por aqui.",
                color=0x2ECC71,
            )
            e.set_footer(text=settings.embed_footer)
            await interaction.followup.send(embed=e, ephemeral=True)
            return

        # Dar cargo
        try:
            await member.add_roles(verified, reason="Verificação por botão")
        except discord.Forbidden:
            e = discord.Embed(
                title="⛔ Sem permissão",
                description="Eu não consigo dar esse cargo. Confere se meu cargo está **acima** do ✅ Verificado.",
                color=0xE74C3C,
            )
            e.set_footer(text=settings.embed_footer)
            await interaction.followup.send(embed=e, ephemeral=True)
            return

        # Ping nos canais (mensagens fixadas)
        await _ping_member_after_verify(guild, member)

        # Resposta final: título EXATO como você quer
        welcome_m = _ch_mention(settings.welcome_channel_id)
        rules_m = _ch_mention(settings.rules_channel_id)
        desc = "✅ **Acesso liberado!**\n\n"
        if welcome_m:
            desc += f"1) Vá para {welcome_m}\n"
        if rules_m:
            desc += f"2) Leia {rules_m}\n"

        e = discord.Embed(
            title="✅ Acesso liberado!",
            description=desc.strip(),
            color=0x2ECC71,
        )
        e.set_footer(text=settings.embed_footer)
        await interaction.followup.send(embed=e, ephemeral=True)

        # Log opcional
        if settings.log_channel_id:
            ch = guild.get_channel(settings.log_channel_id)
            if isinstance(ch, discord.TextChannel):
                try:
                    log = discord.Embed(
                        title="📌 Membro verificado",
                        description=f"{member.mention} recebeu {verified.mention}.",
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
            prefix_emoji=False,
            fixed_emoji="🛡️",
        )

        await ch.send(embed=embeds[0], view=VerificationView())

        ok = discord.Embed(title="✅ OK", description="Mensagem de verificação postada.", color=0x2ECC71)
        ok.set_footer(text=settings.embed_footer)
        await interaction.response.send_message(embed=ok, ephemeral=True)

    @app_commands.command(
        name="setup_mensagens",
        description="Cria e fixa as mensagens de boas-vindas e regras (admin).",
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setup_mensagens(self, interaction: discord.Interaction) -> None:
        if not interaction.guild:
            await interaction.response.send_message("Use isso dentro de um servidor.", ephemeral=True)
            return

        if not settings.welcome_channel_id or not settings.rules_channel_id:
            await interaction.response.send_message("Configure WELCOME_CHANNEL_ID e RULES_CHANNEL_ID.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            await _setup_pinned_messages(interaction.guild, self.bot.user.id)  # type: ignore
            e = discord.Embed(
                title="📌 Mensagens fixadas",
                description="Boas-vindas e regras foram postadas e fixadas com sucesso.",
                color=0x2ECC71,
            )
            e.set_footer(text=settings.embed_footer)
            await interaction.followup.send(embed=e, ephemeral=True)
        except Exception:
            logger.exception("Falha no /setup_mensagens")
            e = discord.Embed(
                title="⛔ Erro",
                description="Não consegui fixar as mensagens. Verifique permissões do bot nos canais.",
                color=0xE74C3C,
            )
            e.set_footer(text=settings.embed_footer)
            await interaction.followup.send(embed=e, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(VerificationCog(bot))
