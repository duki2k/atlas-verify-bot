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
        await self.load_extension("cogs.admin")
        await self.load_extension("cogs.welcome")
        await self.load_extension("cogs.verification")

        try:
            if settings.guild_id:
                guild = discord.Object(id=settings.guild_id)
                # limpa cache de comandos do guild e sincroniza de novo
                self.tree.clear_commands(guild=guild)
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                logger.info("Slash commands synced (guild=%s).", settings.guild_id)
            else:
                await self.tree.sync()
                logger.info("Slash commands synced (global).")
        except Exception:
            logger.exception("Falha ao sincronizar slash commands.")

    async def on_ready(self) -> None:
        logger.info("Online como %s (id=%s).", self.user, self.user.id)


def main() -> None:
    bot = AtlasVerifyBot()
    bot.run(settings.discord_token)


if __name__ == "__main__":
    main()
