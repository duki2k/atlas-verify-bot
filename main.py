import discord
from discord.ext import commands

from config import load_settings
from utils.logging_ import setup_logging

settings = load_settings()
logger = setup_logging()

intents = discord.Intents.default()
intents.members = True  # on_member_join (logs/DM)


class AtlasVerifyBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self) -> None:
        # cogs
        await self.load_extension("cogs.admin")
        await self.load_extension("cogs.welcome")
        await self.load_extension("cogs.verification")
        await self.load_extension("cogs.health")

        # ✅ View persistente: botão de verificação não morre após restart
        try:
            from cogs.verification import VerificationView
            self.add_view(VerificationView())
            logger.info("Persistent VerificationView registered.")
        except Exception:
            logger.exception("Failed to register persistent VerificationView.")

        # ✅ Sync no servidor (guild) pra aparecer rápido
        try:
            if settings.guild_id:
                guild = discord.Object(id=settings.guild_id)
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
