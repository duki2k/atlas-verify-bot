import discord
from discord.ext import commands
from discord import app_commands

from config import load_settings
from utils.logging_ import setup_logging

settings = load_settings()
logger = setup_logging()

intents = discord.Intents.default()
intents.members = True


# ✅ nomes que você quer GARANTIR que sumam
BANNED_COMMAND_NAMES = {"sync", "setup_verificacao", "setup_verificacaoo", "setup_verificacao"}


class RoboDukiBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self) -> None:
        await self.load_extension("cogs.welcome")
        await self.load_extension("cogs.admin")
        await self.load_extension("cogs.cleanup")

        # trava global: comandos só no canal admin
        async def only_admin_channel(interaction: discord.Interaction) -> bool:
            if interaction.guild is None:
                raise app_commands.CheckFailure("Comandos só no servidor.")
            if interaction.channel_id != settings.admin_channel_id:
                raise app_commands.CheckFailure(f"❌ Use comandos só em <#{settings.admin_channel_id}>.")
            return True

        self.tree.interaction_check = only_admin_channel

    async def on_ready(self) -> None:
        logger.info("Online como %s (id=%s).", self.user, self.user.id)

        try:
            # ✅ 1) Remover comandos globais antigos (se existirem)
            global_cmds = await self.tree.fetch_commands()
            deleted = 0
            for c in global_cmds:
                if c.name in BANNED_COMMAND_NAMES:
                    await self.tree.delete_command(c)
                    deleted += 1
            if deleted:
                logger.info("Deleted %s global stale commands.", deleted)

            # ✅ 2) Para cada guild, remover comandos antigos + sync (atualiza quase instantâneo)
            for g in self.guilds:
                guild_obj = discord.Object(id=g.id)

                # apaga comandos indesejados na guild
                guild_cmds = await self.tree.fetch_commands(guild=guild_obj)
                deleted_g = 0
                for c in guild_cmds:
                    if c.name in BANNED_COMMAND_NAMES:
                        await self.tree.delete_command(c, guild=guild_obj)
                        deleted_g += 1
                if deleted_g:
                    logger.info("Deleted %s guild stale commands in %s.", deleted_g, g.id)

                # sincroniza comandos atuais na guild
                self.tree.copy_global_to(guild=guild_obj)
                synced = await self.tree.sync(guild=guild_obj)
                logger.info("Synced guild=%s (%s): %s", g.id, g.name, ", ".join([x.name for x in synced]) or "(none)")

            # ✅ 3) Sync global (pode levar um pouco pra refletir no cliente, mas o delete já foi feito)
            await self.tree.sync()
            logger.info("Synced global commands.")

        except Exception:
            logger.exception("Command cleanup/sync failed.")

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
