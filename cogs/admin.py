import discord
from discord import app_commands
from discord.ext import commands

from config import load_settings
from utils.embeds import make_embeds_from_text

settings = load_settings()

class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="ping", description="Teste simples de latência.")
    async def ping(self, interaction: discord.Interaction) -> None:
        embeds = make_embeds_from_text(
            title="Pong 🏓",
            text=f"{round(self.bot.latency*1000)}ms",
            emoji_pool=settings.emoji_pool,
            footer=settings.embed_footer,
            color=0x3498DB,
        )
        await interaction.response.send_message(embed=embeds[0], ephemeral=True)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AdminCog(bot))
