import discord
from discord import app_commands
from discord.ext import commands

from config import load_settings
from utils.embeds import make_embed, format_embed_body

settings = load_settings()


def _safe_allowed_mentions(pingar: bool) -> discord.AllowedMentions:
    if pingar:
        return discord.AllowedMentions(everyone=True, roles=True, users=True)
    return discord.AllowedMentions(everyone=False, roles=False, users=True)


async def _read_text_attachment(attachment: discord.Attachment, max_chars: int = 3800) -> str:
    # aceita txt/md
    name = (attachment.filename or "").lower()
    if not (name.endswith(".txt") or name.endswith(".md")):
        raise ValueError("Envie um arquivo .txt ou .md")

    data = await attachment.read()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = data.decode("latin-1")

    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        raise ValueError("Arquivo vazio.")
    if len(text) > max_chars:
        raise ValueError(f"Texto muito grande (>{max_chars} chars).")
    return text


class MessagesCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # =========================
    # /enviar (texto)
    # =========================
    @app_commands.command(name="enviar", description="Enviar uma mensagem (texto) em um canal (admin).")
    @app_commands.checks.has_permissions(administrator=True)
    async def enviar(
        self,
        interaction: discord.Interaction,
        canal: discord.TextChannel,
        mensagem: str,
        pingar: bool = False,
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        if len(mensagem) > 2000:
            await interaction.followup.send("⚠️ A mensagem passou de 2000 caracteres. Reduza o texto.", ephemeral=True)
            return

        try:
            await canal.send(mensagem, allowed_mentions=_safe_allowed_mentions(pingar))
        except Exception as e:
            await interaction.followup.send(f"⛔ Falha ao enviar: `{type(e).__name__}`", ephemeral=True)
            return

        await interaction.followup.send(f"✅ Enviado em {canal.mention}", ephemeral=True)

    # =========================
    # /enviarembed (curto) — mantém
    # =========================
    @app_commands.command(name="enviarembed", description="Enviar um embed premium (texto curto) em um canal (admin).")
    @app_commands.checks.has_permissions(administrator=True)
    async def enviarembed(
        self,
        interaction: discord.Interaction,
        canal: discord.TextChannel,
        titulo: str,
        texto: str,
        pingar: bool = False,
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        if len(titulo) > 256:
            await interaction.followup.send("⚠️ Título muito grande (máx 256).", ephemeral=True)
            return
        if len(texto) > 3800:
            await interaction.followup.send("⚠️ Texto muito grande. Para textos longos, use /enviarembed_txt ou /enviarembed_msg.", ephemeral=True)
            return

        embed = make_embed(
            title=titulo.strip(),
            footer=settings.bot_name,
            author_name=settings.bot_name,
            author_icon=self.bot.user.display_avatar.url if self.bot.user else None,
            thumbnail_url=interaction.guild.icon.url if interaction.guild and interaction.guild.icon else None,
        )
        embed.description = format_embed_body(texto, add_divider_top=True)

        try:
            await canal.send(embed=embed, allowed_mentions=_safe_allowed_mentions(pingar))
        except Exception as e:
            await interaction.followup.send(f"⛔ Falha ao enviar embed: `{type(e).__name__}`", ephemeral=True)
            return

        await interaction.followup.send(f"✅ Embed enviado em {canal.mention}", ephemeral=True)

    # =========================
    # /enviarembed_msg (melhor para texto longo)
    # =========================
    @app_commands.command(
        name="enviarembed_msg",
        description="Envia embed pegando o texto de uma mensagem existente (ideal para texto longo com quebras).",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def enviarembed_msg(
        self,
        interaction: discord.Interaction,
        canal: discord.TextChannel,
        titulo: str,
        mensagem_id: str,
        pingar: bool = False,
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        if len(titulo) > 256:
            await interaction.followup.send("⚠️ Título muito grande (máx 256).", ephemeral=True)
            return

        try:
            mid = int(mensagem_id.strip())
        except ValueError:
            await interaction.followup.send("⚠️ mensagem_id inválido. Use o ID da mensagem (Modo desenvolvedor).", ephemeral=True)
            return

        # busca a mensagem no canal atual onde o comando foi usado
        # (onde você escreveu o texto com ENTER)
        src_channel = interaction.channel
        if not isinstance(src_channel, discord.TextChannel):
            await interaction.followup.send("Use esse comando em um canal de texto do servidor.", ephemeral=True)
            return

        try:
            msg = await src_channel.fetch_message(mid)
        except Exception:
            await interaction.followup.send("⚠️ Não consegui encontrar essa mensagem nesse canal.", ephemeral=True)
            return

        text = (msg.content or "").replace("\r\n", "\n").replace("\r", "\n").strip()
        if not text:
            await interaction.followup.send("⚠️ A mensagem está vazia (sem texto).", ephemeral=True)
            return
        if len(text) > 3800:
            await interaction.followup.send("⚠️ Texto muito grande. Divida em 2 embeds ou reduza um pouco.", ephemeral=True)
            return

        embed = make_embed(
            title=titulo.strip(),
            footer=settings.bot_name,
            author_name=settings.bot_name,
            author_icon=self.bot.user.display_avatar.url if self.bot.user else None,
            thumbnail_url=interaction.guild.icon.url if interaction.guild and interaction.guild.icon else None,
        )
        embed.description = format_embed_body(text, add_divider_top=True)

        try:
            await canal.send(embed=embed, allowed_mentions=_safe_allowed_mentions(pingar))
        except Exception as e:
            await interaction.followup.send(f"⛔ Falha ao enviar embed: `{type(e).__name__}`", ephemeral=True)
            return

        await interaction.followup.send(f"✅ Embed enviado em {canal.mention}", ephemeral=True)

    # =========================
    # /enviarembed_txt (melhor para regras fixas)
    # =========================
    @app_commands.command(
        name="enviarembed_txt",
        description="Envia embed lendo o texto de um arquivo .txt/.md anexado (ideal para regras/avisos).",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def enviarembed_txt(
        self,
        interaction: discord.Interaction,
        canal: discord.TextChannel,
        titulo: str,
        arquivo: discord.Attachment,
        pingar: bool = False,
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        if len(titulo) > 256:
            await interaction.followup.send("⚠️ Título muito grande (máx 256).", ephemeral=True)
            return

        try:
            text = await _read_text_attachment(arquivo, max_chars=3800)
        except Exception as e:
            await interaction.followup.send(f"⚠️ Não consegui ler o arquivo: {e}", ephemeral=True)
            return

        embed = make_embed(
            title=titulo.strip(),
            footer=settings.bot_name,
            author_name=settings.bot_name,
            author_icon=self.bot.user.display_avatar.url if self.bot.user else None,
            thumbnail_url=interaction.guild.icon.url if interaction.guild and interaction.guild.icon else None,
        )
        embed.description = format_embed_body(text, add_divider_top=True)

        try:
            await canal.send(embed=embed, allowed_mentions=_safe_allowed_mentions(pingar))
        except Exception as e:
            await interaction.followup.send(f"⛔ Falha ao enviar embed: `{type(e).__name__}`", ephemeral=True)
            return

        await interaction.followup.send(f"✅ Embed enviado em {canal.mention}", ephemeral=True)

    # =========================
    # /anuncio
    # =========================
    @app_commands.command(name="anuncio", description="Enviar anúncio no canal oficial de anúncios (admin).")
    @app_commands.checks.has_permissions(administrator=True)
    async def anuncio(
        self,
        interaction: discord.Interaction,
        titulo: str,
        texto: str,
        pingar_everyone: bool = False,
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        if not settings.announce_channel_id:
            await interaction.followup.send("⚠️ ANNOUNCE_CHANNEL_ID não definido no host.", ephemeral=True)
            return

        guild = interaction.guild
        if not guild:
            await interaction.followup.send("Use no servidor.", ephemeral=True)
            return

        ch = guild.get_channel(settings.announce_channel_id)
        if not isinstance(ch, discord.TextChannel):
            await interaction.followup.send("⚠️ ANNOUNCE_CHANNEL_ID inválido (canal não encontrado).", ephemeral=True)
            return

        if len(titulo) > 256:
            await interaction.followup.send("⚠️ Título muito grande (máx 256).", ephemeral=True)
            return
        if len(texto) > 3800:
            await interaction.followup.send("⚠️ Texto muito grande. Para texto longo, use /enviarembed_txt e poste no canal.", ephemeral=True)
            return

        embed = make_embed(
            title="ANÚNCIO",
            footer=settings.bot_name,
            author_name=f"{settings.bot_name} • avisos",
            author_icon=self.bot.user.display_avatar.url if self.bot.user else None,
            thumbnail_url=guild.icon.url if guild.icon else None,
        )

        body = f"📣 **{titulo.strip()}**\n\n{texto.strip()}"
        embed.description = format_embed_body(body, add_divider_top=True)

        content = "@everyone" if pingar_everyone else None

        try:
            await ch.send(
                content=content,
                embed=embed,
                allowed_mentions=discord.AllowedMentions(everyone=pingar_everyone, roles=False, users=True),
            )
        except Exception as e:
            await interaction.followup.send(f"⛔ Falha ao enviar anúncio: `{type(e).__name__}`", ephemeral=True)
            return

        await interaction.followup.send(f"✅ Anúncio enviado em {ch.mention}", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MessagesCog(bot))
