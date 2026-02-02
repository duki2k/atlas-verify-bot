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

    async def setup_hook(self) -> None:
        # Cogs
        await self.load_extension("cogs.admin")
        await self.load_extension("cogs.welcome")
        await self.load_extension("cogs.verification")
        await self.load_extension("cogs.health")

        # ✅ View persistente: botão não morre após restart
        from cogs.verification import VerificationView
        self.add_view(VerificationView())

        # ✅ Sync no servidor (guild) + limpa cache (garante /health aparecer)
        try:
            if settings.guild_id:
                guild = discord.Object(id=settings.guild_id)
                self.tree.clear_commands(guild=guild)
                synced = await self.tree.sync(guild=guild)
                logger.info(
                    "Slash commands synced (guild=%s): %s",
                    settings.guild_id,
                    ", ".join([c.name for c in synced]),
                )
            else:
                synced = await self.tree.sync()
                logger.info("Slash commands synced (global): %s", ", ".join([c.name for c in synced]))
        except Exception:
            logger.exception("Slash commands sync failed.")

    async def on_ready(self) -> None:
        logger.info("Online como %s (id=%s).", self.user, self.user.id)


def main() -> None:
    bot = AtlasVerifyBot()
    bot.run(settings.discord_token)


if __name__ == "__main__":
    main()
