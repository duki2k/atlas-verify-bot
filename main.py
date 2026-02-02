import discord
from discord.ext import commands

from config import load_settings
from utils.logging_ import setup_logging

settings = load_settings()
logger = setup_logging()

intents = discord.Intents.default()
intents.members = True


class AtlasVerifyBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix="!", intents=intents)
        self._did_sync = False

    async def setup_hook(self) -> None:
        await self.load_extension("cogs.admin")
        await self.load_extension("cogs.welcome")
        await self.load_extension("cogs.verification")
        await self.load_extension("cogs.health")

        # View persistente
        from cogs.verification import VerificationView
        self.add_view(VerificationView())

    async def on_ready(self) -> None:
        logger.info("Online como %s (id=%s).", self.user, self.user.id)

        if self._did_sync:
            return
        self._did_sync = True

        try:
            for g in self.guilds:
                guild_obj = discord.Object(id=g.id)

                # ✅ aqui está o pulo do gato:
                # copia comandos globais para a guild e sincroniza
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


def main() -> None:
    bot = AtlasVerifyBot()
    bot.run(settings.discord_token)


if __name__ == "__main__":
    main()
