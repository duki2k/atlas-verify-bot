import discord
from discord import app_commands
from discord.ext import commands

from config import load_settings
from utils.embeds import make_embed

settings = load_settings()


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="ping", description="Teste do bot (admin).")
    async def ping(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        ws_ms = round(self.bot.latency * 1000)
        e = make_embed(
            title="🏓 Pong",
            description=f"Latência: **{ws_ms} ms**",
            color=0x3498DB,
            footer=settings.embed_footer,
        )
        await interaction.followup.send(embed=e, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AdminCog(bot))
