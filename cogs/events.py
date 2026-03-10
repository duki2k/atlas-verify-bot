# cogs/events.py
import discord
from discord import app_commands
from discord.ext import commands

from utils.database import init_db
from utils.event_service import create_event, get_open_karaoke_event, log_staff_action
from views.karaoke_signup import KaraokeSignupView

class EventsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        init_db()

    evento = app_commands.Group(name="evento", description="Comandos de eventos")
    karaoke = app_commands.Group(name="karaoke", description="Comandos do karaokê", parent=evento)

    @karaoke.command(name="chamada", description="Abre a chamada do karaokê")
    @app_commands.describe(
        titulo="Título do evento",
        descricao="Descrição do evento",
    )
    async def chamada(self, interaction: discord.Interaction, titulo: str, descricao: str | None = None):
        event_id = create_event(
            guild_id=interaction.guild.id,
            title=titulo,
            created_by_id=interaction.user.id
        )

        embed = discord.Embed(
            title=f"🎤 {titulo}",
            description=descricao or "Clique abaixo para participar do karaokê.",
            color=discord.Color.magenta()
        )
        embed.add_field(name="🎤 Vou cantar", value="Entra como cantor.", inline=False)
        embed.add_field(name="👀 Só assistir", value="Entra como espectador.", inline=False)

        await interaction.channel.send(embed=embed, view=KaraokeSignupView(event_id))
        log_staff_action(
            interaction.guild.id, event_id, "open_signup",
            interaction.user.id, str(interaction.user)
        )
        await interaction.response.send_message("✅ Chamada criada com sucesso.", ephemeral=True)

    @karaoke.command(name="iniciar", description="Inicia o karaokê")
    @app_commands.describe(
        titulo="Título visual do evento",
        nome_canal_voz="Nome do canal de voz",
        nome_canal_texto="Nome do canal de texto"
    )
    async def iniciar(
        self,
        interaction: discord.Interaction,
        titulo: str,
        nome_canal_voz: str | None = None,
        nome_canal_texto: str | None = None
    ):
        await interaction.response.send_message(
            "🚧 Esqueleto criado. Próximo passo: ligar criação dos canais, fila aleatória e cargos temporários.",
            ephemeral=True
        )

    @karaoke.command(name="proximo", description="Avança a vez")
    async def proximo(self, interaction: discord.Interaction):
        await interaction.response.send_message("🚧 Comando /evento karaoke proximo pronto para implementação.", ephemeral=True)

    @karaoke.command(name="pular", description="Pula um cantor para o final da fila")
    async def pular(self, interaction: discord.Interaction, usuario: discord.Member, motivo: str):
        await interaction.response.send_message(
            f"🚧 {usuario.mention} será movido para o final da fila. Motivo: {motivo}",
            ephemeral=True
        )

    @karaoke.command(name="status", description="Mostra o status do karaokê")
    async def status(self, interaction: discord.Interaction):
        await interaction.response.send_message("🚧 Painel de status do karaokê em preparação.", ephemeral=True)

    @karaoke.command(name="encerrar", description="Encerra o karaokê")
    async def encerrar(self, interaction: discord.Interaction):
        await interaction.response.send_message("🚧 Encerramento do karaokê em preparação.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(EventsCog(bot))
