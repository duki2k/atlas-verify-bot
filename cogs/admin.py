import discord
from discord.ext import commands
from discord import app_commands

from config import load_settings
from utils.embeds import make_embed

settings = load_settings()


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Ping do bot")
    @app_commands.checks.has_permissions(administrator=True)
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=make_embed(
                title="PING",
                description=f"🏓 Latência: {round(self.bot.latency * 1000)} ms",
                footer=settings.bot_name
            ),
            ephemeral=True
        )

    @app_commands.command(name="status", description="Status do servidor")
    @app_commands.checks.has_permissions(administrator=True)
    async def status(self, interaction: discord.Interaction):
        guild = interaction.guild
        await interaction.response.send_message(
            embed=make_embed(
                title="STATUS",
                description=f"👥 Membros: {guild.member_count}",
                footer=settings.bot_name
            ),
            ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))
