import asyncio
import discord
from discord.ext import commands

from config import load_settings
from utils.logging_ import setup_logging
from cogs.verification import VerificationView

settings = load_settings()
logger = setup_logging()

INTENTS = discord.Intents.default()
INTENTS.members = True  # necessário p/ on_member_join + manipular membros/cargos
INTENTS.guilds = True

class VerifyBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(
            command_prefix="!",
            intents=INTENTS,
            help_command=None,
        )

    async def setup_hook(self) -> None:
        # Carrega cogs
        await self.load_extension("cogs.welcome")
        await self.load_extension("cogs.verification")
        await self.load_extension("cogs.admin")

        # View persistente (botão de verificação continua funcionando após restart)
        self.add_view(VerificationView())

        # Sync de comandos
        if settings.guild_id:
            guild = discord.Object(id=settings.guild_id)
            await self.tree.sync(guild=guild)
            logger.info("Slash commands synced (guild=%s).", settings.guild_id)
        else:
            await self.tree.sync()
            logger.info("Slash commands synced (global).")

    async def on_ready(self) -> None:
        logger.info("Online como %s (id=%s).", self.user, self.user.id)

async def main() -> None:
    bot = VerifyBot()
    await bot.start(settings.discord_token)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
