import discord
from discord import app_commands
from discord.ext import commands

from config import load_settings
from utils.logging_ import setup_logging

settings = load_settings()
logger = setup_logging()

class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="ping", description="Teste simples de latência.")
    async def ping(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(f"Pong 🏓 {round(self.bot.latency*1000)}ms", ephemeral=True)

    @app_commands.command(name="sync", description="Re-sincroniza slash commands (admin).")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def sync(self, interaction: discord.Interaction) -> None:
        if settings.guild_id:
            guild = discord.Object(id=settings.guild_id)
            synced = await self.bot.tree.sync(guild=guild)
            await interaction.response.send_message(
                f"Sync ok (guild) ✅ ({len(synced)} comandos).",
                ephemeral=True,
            )
        else:
            synced = await self.bot.tree.sync()
            await interaction.response.send_message(
                f"Sync ok (global) ✅ ({len(synced)} comandos).",
                ephemeral=True,
            )

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AdminCog(bot))
