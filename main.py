import discord
from discord.ext import commands
from discord import app_commands

from config import load_settings
from utils.logging_ import setup_logging

settings = load_settings()
logger = setup_logging()

intents = discord.Intents.default()
intents.members = True  # join/leave + status

# Se você ativar stats tracking, é recomendável ligar isto no Developer Portal também.
# intents.message_content = settings.enable_stats_tracking
# intents.reactions = settings.enable_stats_tracking  # discord.py usa intents.default() já cobre reactions em muitos casos


class RoboDukiBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self) -> None:
        await self.load_extension("cogs.welcome")
        await self.load_extension("cogs.admin")
        await self.load_extension("cogs.cleanup")

        async def only_admin_channel(interaction: discord.Interaction) -> bool:
            if interaction.guild is None:
                raise app_commands.CheckFailure("Comandos só no servidor.")
            if interaction.channel_id != settings.admin_channel_id:
                raise app_commands.CheckFailure(f"❌ Use comandos só em <#{settings.admin_channel_id}>.")
            return True

        self.tree.interaction_check = only_admin_channel

    async def on_ready(self) -> None:
        logger.info("Online como %s (id=%s).", self.user, self.user.id)

    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        if isinstance(error, app_commands.CheckFailure):
            msg = str(error) or "❌ Comando não permitido aqui."
            try:
                if interaction.response.is_done():
                    await interaction.followup.send(msg, ephemeral=True)
                else:
                    await interaction.response.send_message(msg, ephemeral=True)
            except Exception:
                pass
            return

        logger.exception("App command error: %s", error)
        try:
            if interaction.response.is_done():
                await interaction.followup.send("⛔ Erro ao executar. Veja Diagnostics.", ephemeral=True)
            else:
                await interaction.response.send_message("⛔ Erro ao executar. Veja Diagnostics.", ephemeral=True)
        except Exception:
            pass


def main() -> None:
    bot = RoboDukiBot()
    bot.run(settings.discord_token)


if __name__ == "__main__":
    main()
