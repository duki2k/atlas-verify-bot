import discord
from discord import app_commands
from discord.ext import commands

from config import load_settings
from utils.embeds import make_embed, format_embed_body

settings = load_settings()


def _safe_allowed_mentions(pingar: bool) -> discord.AllowedMentions:
    # Evita ping acidental em everyone/cargos.
    if pingar:
        return discord.AllowedMentions(everyone=True, roles=True, users=True)
    return discord.AllowedMentions(everyone=False, roles=False, users=True)


class MessagesCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # =========================
    # /enviar
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
    # /enviarembed
    # =========================
    @app_commands.command(name="enviarembed", description="Enviar um embed premium em um canal (admin).")
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

        # limite conservador para description
        if len(texto) > 3800:
            await interaction.followup.send("⚠️ Texto muito grande. Reduza um pouco.", ephemeral=True)
            return

        embed = make_embed(
            title=titulo.strip(),
            footer=settings.bot_name,
            author_name=settings.bot_name,
            author_icon=self.bot.user.display_avatar.url if self.bot.user else None,
            thumbnail_url=interaction.guild.icon.url if interaction.guild and interaction.guild.icon else None,
        )

        # ✅ NÃO repetir o título no corpo
        embed.description = format_embed_body(texto, add_divider_top=True, add_divider_bottom=False)

        try:
            await canal.send(embed=embed, allowed_mentions=_safe_allowed_mentions(pingar))
        except Exception as e:
            await interaction.followup.send(f"⛔ Falha ao enviar embed: `{type(e).__name__}`", ephemeral=True)
            return

        await interaction.followup.send(f"✅ Embed enviado em {canal.mention}", ephemeral=True)

    # =========================
    # /anuncio (canal fixo via env)
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
            await interaction.followup.send("⚠️ Texto muito grande. Reduza um pouco.", ephemeral=True)
            return

        embed = make_embed(
            title="ANÚNCIO",
            footer=settings.bot_name,
            author_name=f"{settings.bot_name} • avisos",
            author_icon=self.bot.user.display_avatar.url if self.bot.user else None,
            thumbnail_url=guild.icon.url if guild.icon else None,
        )

        # Cabeçalho curto dentro do texto, sem repetir "ANÚNCIO"
        # (o título do embed já é ANÚNCIO)
        body = f"📣 **{titulo.strip()}**\n\n{texto.strip()}"
        embed.description = format_embed_body(body, add_divider_top=True, add_divider_bottom=False)

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
