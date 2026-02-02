import discord
from discord import app_commands
from discord.ext import commands

from config import load_settings
from utils.embeds import make_embeds

settings = load_settings()


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="ping", description="Teste simples do bot.")
    async def ping(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        e = make_embeds(
            title="🏓 Pong",
            text=f"{round(self.bot.latency * 1000)}ms",
            color=0x3498DB,
            footer=settings.embed_footer,
        )[0]
        await interaction.followup.send(embed=e, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AdminCog(bot))
