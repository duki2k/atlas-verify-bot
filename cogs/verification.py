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
HELP_BUTTON_CUSTOM_ID = "verifybot:help_button"


def _account_age_days(user: discord.abc.User) -> int:
    created = user.created_at
    if created is None:
        return 9999
    now = _dt.datetime.now(tz=_dt.timezone.utc)
    return int((now - created).days)


def _mention_channel(channel_id: int | None, fallback: str) -> str:
    return f"<#{channel_id}>" if channel_id else fallback


async def _log(guild: discord.Guild, title: str, text: str) -> None:
    if not settings.log_channel_id:
        return
    ch = guild.get_channel(settings.log_channel_id)
    if isinstance(ch, discord.TextChannel):
        try:
            e = make_embeds(title=title, text=text, color=0x95A5A6, footer=settings.embed_footer)[0]
            await ch.send(embed=e)
        except Exception:
            pass


async def _upsert_verify_message(ch: discord.TextChannel, embed: discord.Embed, view: discord.ui.View, bot_id: int) -> None:
    # Tenta editar mensagem existente do bot; se não conseguir ler histórico, cria nova.
    try:
        async for msg in ch.history(limit=30):
            if msg.author and msg.author.id == bot_id and msg.components:
                found = False
                for row in msg.components:
                    for comp in getattr(row, "children", []):
                        if getattr(comp, "custom_id", None) == VERIFY_BUTTON_CUSTOM_ID:
                            found = True
                            break
                    if found:
                        break
                if found:
                    await msg.edit(embed=embed, view=view)
                    return
    except discord.Forbidden:
        # Sem Read Message History → cai no send novo
        pass
    except Exception:
        pass

    await ch.send(embed=embed, view=view)


async def _upsert_single_pinned(channel: discord.TextChannel, embed: discord.Embed, bot_id: int) -> None:
    # Atualiza 1 mensagem fixada do bot; se não existir, cria e fixa.
    try:
        pins = await channel.pins()
        bot_pins = [m for m in pins if m.author and m.author.id == bot_id]
        if bot_pins:
            # edita a primeira
            await bot_pins[0].edit(embed=embed)
            # garante pin
            try:
                await bot_pins[0].pin(reason="Atlas onboarding")
            except Exception:
                pass
            # remove duplicadas
            for extra in bot_pins[1:]:
                try:
                    await extra.unpin()
                except Exception:
                    pass
                try:
                    await extra.delete()
                except Exception:
                    pass
            return
    except discord.Forbidden:
        raise
    except Exception:
        # se pins falhar, tenta só postar (sem pin)
        await channel.send(embed=embed)
        return

    # não tinha pin do bot → cria e fixa
    m = await channel.send(embed=embed)
    await m.pin(reason="Atlas onboarding")


async def _setup_pinned_messages(guild: discord.Guild, bot_id: int) -> tuple[bool, str]:
    if not settings.welcome_channel_id or not settings.rules_channel_id:
        return (False, "Pins ignorados: WELCOME_CHANNEL_ID/RULES_CHANNEL_ID não configurados.")

    welcome_ch = guild.get_channel(settings.welcome_channel_id)
    rules_ch = guild.get_channel(settings.rules_channel_id)

    if not isinstance(welcome_ch, discord.TextChannel) or not isinstance(rules_ch, discord.TextChannel):
        return (False, "Pins ignorados: IDs não apontam para canais de texto.")

    # placeholders
    rules_mention = _mention_channel(settings.rules_channel_id, "#regras")

    verified_role = guild.get_role(settings.verified_role_id)
    member_role_text = f"@{verified_role.name}" if verified_role else "@Membro"

    news = _mention_channel(settings.news_channel_id, "#notícias")
    assets = _mention_channel(settings.assets_channel_id, "#ativos-mundiais")
    education = _mention_channel(settings.education_channel_id, "#educação-financeira")
    chat = _mention_channel(settings.chat_channel_id, "#chat-geral")
    support = _mention_channel(settings.support_channel_id, "#suporte")

    if not settings.pinned_welcome_text or not settings.pinned_rules_text:
        return (False, "PINNED_WELCOME_TEXT / PINNED_RULES_TEXT não definidos.")

    try:
        welcome_text = settings.pinned_welcome_text.format(
            member_role=member_role_text,
            rules_channel=rules_mention,
            news_channel=news,
            assets_channel=assets,
            education_channel=education,
            chat_channel=chat,
            support_channel=support,
        )
        rules_text = settings.pinned_rules_text.format(
            member_role=member_role_text,
            rules_channel=rules_mention,
            news_channel=news,
            assets_channel=assets,
            education_channel=education,
            chat_channel=chat,
            support_channel=support,
        )
    except KeyError as e:
        return (False, f"Placeholder inválido no texto: {e}")

    # cria/edita 1 pin por canal (rápido)
    welcome_embed = make_embeds("🎉 Boas-vindas", welcome_text, 0x2ECC71, settings.embed_footer)[0]
    rules_embed = make_embeds("📌 Regras", rules_text, 0xE67E22, settings.embed_footer)[0]

    await _upsert_single_pinned(welcome_ch, welcome_embed, bot_id)
    await _upsert_single_pinned(rules_ch, rules_embed, bot_id)

    return (True, "Mensagens fixadas/atualizadas em #boas-vindas e #regras.")


class VerificationView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(label="Verificar ✅", style=discord.ButtonStyle.success, custom_id=VERIFY_BUTTON_CUSTOM_ID)
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Use isso dentro de um servidor.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        member: discord.Member = interaction.user
        guild = interaction.guild

        verified_role = guild.get_role(settings.verified_role_id)
        if not verified_role:
            e = make_embeds("⛔ Erro", "VERIFIED_ROLE_ID não existe nesse servidor.", 0xE74C3C, settings.embed_footer)[0]
            await interaction.followup.send(embed=e, ephemeral=True)
            return

        # anti-raid idade
        if settings.min_account_age_days > 0:
            age = _account_age_days(member)
            if age < settings.min_account_age_days:
                e = make_embeds(
                    "⛔ Verificação bloqueada",
                    f"Sua conta precisa ter pelo menos **{settings.min_account_age_days} dias**.\nIdade atual: **{age}d**",
                    0xE74C3C,
                    settings.embed_footer,
                )[0]
                await interaction.followup.send(embed=e, ephemeral=True)
                return

        # anti-raid avatar (opcional)
        if settings.require_avatar and member.avatar is None:
            e = make_embeds("⛔ Verificação bloqueada", "Para verificar, sua conta precisa ter **avatar**.", 0xE74C3C, settings.embed_footer)[0]
            await interaction.followup.send(embed=e, ephemeral=True)
            return

        if verified_role in member.roles:
            e = make_embeds("✅ Já verificado", "Você já está verificado.", 0x2ECC71, settings.embed_footer)[0]
            await interaction.followup.send(embed=e, ephemeral=True)
            return

        try:
            await member.add_roles(verified_role, reason="Verificação por botão")
        except discord.Forbidden:
            e = make_embeds(
                "⛔ Sem permissão",
                "Eu não consigo dar esse cargo. Coloque o **cargo do bot acima** do cargo ✅ Verificado.",
                0xE74C3C,
                settings.embed_footer,
            )[0]
            await interaction.followup.send(embed=e, ephemeral=True)
            return
        except Exception:
            logger.exception("Erro ao adicionar cargo.")
            e = make_embeds("⛔ Erro", "Erro inesperado ao verificar. Tente novamente.", 0xE74C3C, settings.embed_footer)[0]
            await interaction.followup.send(embed=e, ephemeral=True)
            return

        welcome_m = _mention_channel(settings.welcome_channel_id, "#boas-vindas")
        rules_m = _mention_channel(settings.rules_channel_id, "#regras")
        desc = f"1) Vá para {welcome_m}\n2) Leia {rules_m}"

        e = discord.Embed(title="✅ Acesso liberado!", description=desc, color=0x2ECC71)
        e.set_footer(text=settings.embed_footer)
        await interaction.followup.send(embed=e, ephemeral=True)

        await _log(guild, "🟩 Verificado", f"{member.mention} recebeu {verified_role.mention} (id={member.id}).")

    @discord.ui.button(label="Me enviar instruções 📩", style=discord.ButtonStyle.secondary, custom_id=HELP_BUTTON_CUSTOM_ID)
    async def help_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Use isso dentro de um servidor.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        verify_ch = _mention_channel(settings.verify_channel_id, "#verificação")
        welcome_ch = _mention_channel(settings.welcome_channel_id, "#boas-vindas")
        rules_ch = _mention_channel(settings.rules_channel_id, "#regras")

        dm_text = (
            f"👋 Oi, {interaction.user.mention}!\n\n"
            f"✅ Para liberar acesso, vá em {verify_ch} e clique em **Verificar ✅**.\n\n"
            f"Depois disso:\n"
            f"1) Leia {welcome_ch} (mensagem fixada)\n"
            f"2) Leia {rules_ch} (mensagem fixada)\n"
        )

        try:
            e = make_embeds("📩 Instruções", dm_text, 0x3498DB, settings.embed_footer)[0]
            await interaction.user.send(embed=e)
            ok = make_embeds("✅ Enviado!", "Te mandei as instruções no privado.", 0x2ECC71, settings.embed_footer)[0]
            await interaction.followup.send(embed=ok, ephemeral=True)
        except discord.Forbidden:
            err = make_embeds("⛔ DM bloqueada", "Seu privado está bloqueado. Libere DM do servidor.", 0xE74C3C, settings.embed_footer)[0]
            await interaction.followup.send(embed=err, ephemeral=True)


class VerificationCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="setup_verificacao", description="Posta/atualiza verificação e atualiza pins (admin).")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setup_verificacao(self, interaction: discord.Interaction) -> None:
        if not interaction.guild:
            await interaction.response.send_message("Use isso dentro de um servidor.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        results = []
        guild = interaction.guild

        try:
            if not settings.verify_channel_id:
                results.append("❌ VERIFY_CHANNEL_ID não configurado.")
            else:
                ch = guild.get_channel(settings.verify_channel_id)
                if not isinstance(ch, discord.TextChannel):
                    results.append("❌ VERIFY_CHANNEL_ID não aponta para canal de texto.")
                else:
                    verify_embed = make_embeds("🛡️ Verificação", settings.verify_message, 0x3498DB, settings.embed_footer)[0]
                    await _upsert_verify_message(ch, verify_embed, VerificationView(), self.bot.user.id)  # type: ignore
                    results.append(f"✅ Verificação atualizada em <#{settings.verify_channel_id}>.")
        except Exception:
            logger.exception("Falha ao atualizar verificação.")
            results.append("❌ Erro ao atualizar a verificação (veja Diagnostics).")

        try:
            ok, msg = await _setup_pinned_messages(guild, self.bot.user.id)  # type: ignore
            results.append(("✅ " if ok else "⚠️ ") + msg)
        except discord.Forbidden:
            results.append("⚠️ Sem permissão pra atualizar pins. Dê **Read Message History + Manage Messages** em #boas-vindas/#regras.")
        except Exception:
            logger.exception("Falha ao atualizar pins.")
            results.append("❌ Erro ao atualizar pins (veja Diagnostics).")

        e = make_embeds(
            title="✅ Setup (resultado)",
            text="\n".join(results),
            color=0x2ECC71,
            footer=settings.embed_footer,
        )[0]
        await interaction.followup.send(embed=e, ephemeral=True)

        await _log(guild, "⚙️ Setup", f"Executado por {interaction.user.mention}.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(VerificationCog(bot))
