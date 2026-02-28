import discord
from discord.ext import commands

from config import load_settings
from utils.logging_ import setup_logging

settings = load_settings()
logger = setup_logging()

intents = discord.Intents.default()
intents.members = True  # necessário para on_member_join


class AtlasWelcomeBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self) -> None:
        await self.load_extension("cogs.welcome")

    async def on_ready(self) -> None:
        logger.info("Online como %s (id=%s).", self.user, self.user.id)


def main() -> None:
    bot = AtlasWelcomeBot()
    bot.run(settings.discord_token)


if __name__ == "__main__":
    main()
