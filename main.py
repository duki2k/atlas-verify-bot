import discord
from discord.ext import commands
from discord import app_commands

from config import load_settings
from utils.logging_ import setup_logging

settings = load_settings()
logger = setup_logging()

intents = discord.Intents.default()
intents.members = True  # join/leave


class RoboDukiBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix="!", intents=intents)
        self._ran = False

    async def setup_hook(self) -> None:
        # carrega SOMENTE cogs atuais
        await self.load_extension("cogs.welcome")
        await self.load_extension("cogs.admin")
        await self.load_extension("cogs.cleanup")

        # comandos só no canal admin
        async def only_admin_channel(interaction: discord.Interaction) -> bool:
            if interaction.guild is None:
                raise app_commands.CheckFailure("Comandos só no servidor.")
            if interaction.channel_id != settings.admin_channel_id:
                raise app_commands.CheckFailure(f"❌ Use comandos só em <#{settings.admin_channel_id}>.")
            return True

        self.tree.interaction_check = only_admin_channel

    async def on_ready(self) -> None:
        logger.info("Online como %s (id=%s).", self.user, self.user.id)

        # evita rodar duas vezes em reconnect
        if self._ran:
            return
        self._ran = True

        # pega o application id
        app_id = self.application_id
        if not app_id:
            app = await self.application_info()
            app_id = app.id

        try:
            local_cmds = self.tree.get_commands()
            logger.info("DEBUG local commands: %s", [c.name for c in local_cmds])

            payload = [c.to_dict(self.tree) for c in local_cmds]
            logger.info("DEBUG payload_count: %s", len(payload))

            logger.info("STEP 1: overwriting GLOBAL commands -> empty")
            await self.http.bulk_upsert_global_commands(app_id, [])
            logger.info("OK 1: Global commands overwritten with EMPTY list (nuked).")

            for g in self.guilds:
                logger.info("STEP 2: overwriting GUILD commands -> guild=%s (%s)", g.id, g.name)
                await self.http.bulk_upsert_guild_commands(app_id, g.id, payload)
                logger.info("OK 2: Guild commands overwritten: guild=%s (%s) count=%s", g.id, g.name, len(payload))

        except Exception:
            logger.exception("Hard overwrite of commands failed.")

    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        # erros de check (canal admin, permissão, etc.)
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
