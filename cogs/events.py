import discord
from discord import app_commands
from discord.ext import commands
import random

class EventsCog(commands.GroupCog, group_name="evento"):
    def __init__(self, bot):
        self.bot = bot

    karaoke = app_commands.Group(name="karaoke", description="Comandos do karaokê")

    @karaoke.command(name="chamada", description="Abre a chamada do karaokê")
    @app_commands.describe(
        titulo="Título do evento",
        descricao="Descrição do evento"
    )
    async def chamada(
        self,
        interaction: discord.Interaction,
        titulo: str,
        descricao: str | None = None
    ):
        embed = discord.Embed(
            title=f"🎤 {titulo}",
            description=descricao or "Clique abaixo para participar.",
            color=discord.Color.magenta()
        )
        await interaction.response.send_message(
            "✅ Esqueleto da chamada funcionando. Próximo passo: ligar botões e banco.",
            ephemeral=True
        )
        await interaction.channel.send(embed=embed)

    @karaoke.command(name="iniciar", description="Inicia o karaokê")
    @app_commands.describe(
        titulo="Título do evento",
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
            f"✅ Esqueleto do karaokê iniciado.\nTítulo: {titulo}\nVoz: {nome_canal_voz or 'padrão'}\nTexto: {nome_canal_texto or 'padrão'}",
            ephemeral=True
        )

    @karaoke.command(name="status", description="Mostra o status do karaokê")
    async def status(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "✅ Esqueleto do status funcionando.",
            ephemeral=True
        )

    @karaoke.command(name="proximo", description="Avança para o próximo cantor")
    async def proximo(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "✅ Esqueleto do próximo funcionando.",
            ephemeral=True
        )

    @karaoke.command(name="pular", description="Move um cantor para o final da fila")
    @app_commands.describe(
        usuario="Cantor que será movido",
        motivo="Motivo do pulo"
    )
    async def pular(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member,
        motivo: str
    ):
        await interaction.response.send_message(
            f"✅ {usuario.mention} seria movido para o fim da fila. Motivo: {motivo}",
            ephemeral=True
        )

    @karaoke.command(name="encerrar", description="Encerra o karaokê")
    async def encerrar(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "✅ Esqueleto do encerramento funcionando.",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(EventsCog(bot))
