import discord
from discord import app_commands
from discord.ext import commands

from config import load_settings
from utils.embeds import make_embed

settings = load_settings()


class CleanupCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="clean", description="Limpa mensagens de um canal (admin).")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clean(
        self,
        interaction: discord.Interaction,
        canal: discord.TextChannel,
        tudo: bool = False,
        lotes: app_commands.Range[int, 1, 50] = 5,  # 5 lotes * 100 msgs = 500 por padrão
        apagar_fixadas: bool = False,
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        deleted_total = 0
        max_loops = 999999 if tudo else lotes

        def check(m: discord.Message) -> bool:
            if not apagar_fixadas and m.pinned:
                return False
            return True

        # purge apaga até 100 por chamada com bulk
        # e não apaga mensagens muito antigas (limite da API)
        for _ in range(max_loops):
            deleted = await canal.purge(limit=100, check=check, bulk=True)
            deleted_total += len(deleted)
            if len(deleted) < 2:
                break

        embed = make_embed(
            title="CLEAN",
            description=f"🧹 Canal: {canal.mention}\n✅ Apagadas: **{deleted_total}** mensagens",
            footer=f"{settings.bot_name}",
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="reset_channel", description="Zera 100% o canal (clona e apaga o original).")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def reset_channel(self, interaction: discord.Interaction, canal: discord.TextChannel) -> None:
        await interaction.response.defer(ephemeral=True)

        new_ch = await canal.clone(reason=f"Reset solicitado por {interaction.user}")
        await new_ch.edit(position=canal.position, category=canal.category)
        await canal.delete(reason=f"Reset solicitado por {interaction.user}")

        embed = make_embed(
            title="RESET",
            description=f"♻️ Canal resetado: {new_ch.mention}\n⚠️ Novo canal tem outro ID (se estiver em env var, atualize).",
            footer=f"{settings.bot_name}",
        )
        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CleanupCog(bot))
