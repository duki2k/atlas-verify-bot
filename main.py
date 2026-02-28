import discord
from discord.ext import commands
from discord import app_commands

from config import load_settings
from utils.logging_ import setup_logging

settings = load_settings()
logger = setup_logging()

intents = discord.Intents.default()
intents.members = True


class DukiOdysseyBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix="!", intents=intents)
        self._did_sync = False

    async def setup_hook(self) -> None:
        # cogs que você quer manter
        await self.load_extension("cogs.welcome")
        await self.load_extension("cogs.admin")
        await self.load_extension("cogs.cleanup")

        # ✅ trava global: comandos só no canal admin
        async def only_admin_channel(interaction: discord.Interaction) -> bool:
            if interaction.guild is None:
                raise app_commands.CheckFailure("Comandos só funcionam dentro do servidor.")
            if interaction.channel_id != settings.admin_channel_id:
                raise app_commands.CheckFailure(f"❌ Use comandos apenas em <#{settings.admin_channel_id}>.")
            return True

        self.tree.interaction_check = only_admin_channel

    async def on_ready(self) -> None:
        logger.info("Online como %s (id=%s).", self.user, self.user.id)

        # ✅ sync por guild (rápido)
        if self._did_sync:
            return
        self._did_sync = True

        try:
            for g in self.guilds:
                guild_obj = discord.Object(id=g.id)
                self.tree.copy_global_to(guild=guild_obj)
                synced = await self.tree.sync(guild=guild_obj)
                logger.info(
                    "Synced guild=%s (%s): %s",
                    g.id,
                    g.name,
                    ", ".join([c.name for c in synced]) if synced else "(nenhum)",
                )
        except Exception:
            logger.exception("Guild sync failed.")

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
                await interaction.followup.send("⛔ Erro ao executar comando. Veja o Diagnostics.", ephemeral=True)
            else:
                await interaction.response.send_message("⛔ Erro ao executar comando. Veja o Diagnostics.", ephemeral=True)
        except Exception:
            pass


def main() -> None:
    bot = DukiOdysseyBot()
    bot.run(settings.discord_token)


if __name__ == "__main__":
    main()
