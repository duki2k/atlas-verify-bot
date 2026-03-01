import discord
from discord import app_commands
from discord.ext import commands

from config import load_settings
from utils.embeds import make_embed, retro_divider

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
        lotes: app_commands.Range[int, 1, 50] = 5,
        apagar_fixadas: bool = False,
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        deleted_total = 0
        loops = 999999 if tudo else lotes

        def check(m: discord.Message) -> bool:
            if not apagar_fixadas and m.pinned:
                return False
            return True

        for _ in range(loops):
            deleted = await canal.purge(limit=100, check=check, bulk=True)
            deleted_total += len(deleted)
            if len(deleted) < 2:
                break

        e = make_embed(
            title="CLEAN",
            footer=settings.bot_name,
            author_name=f"{settings.bot_name} • cleanup",
            author_icon=self.bot.user.display_avatar.url if self.bot.user else None,
        )
        e.description = f"{retro_divider()}\n🧹 **limpeza concluída**\n{retro_divider()}"

        e.add_field(name="📍 Canal", value=canal.mention, inline=False)
        e.add_field(name="✅ Apagadas", value=f"**{deleted_total}**", inline=True)
        e.add_field(name="⚙️ Modo", value=("TUDO" if tudo else f"{lotes} lote(s)"), inline=True)
        e.add_field(name="📌 Fixadas", value=("apagar" if apagar_fixadas else "preservar"), inline=True)
        e.add_field(
            name="ℹ️ Nota",
            value="Mensagens muito antigas podem não ser removidas pela API. Para zerar 100%, use `/reset_channel`.",
            inline=False,
        )

        await interaction.followup.send(embed=e, ephemeral=True)

    @app_commands.command(name="reset_channel", description="Zera 100% o canal (clona e apaga o original).")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def reset_channel(self, interaction: discord.Interaction, canal: discord.TextChannel) -> None:
        await interaction.response.defer(ephemeral=True)

        new_ch = await canal.clone(reason=f"Reset solicitado por {interaction.user}")
        await new_ch.edit(position=canal.position, category=canal.category)
        await canal.delete(reason=f"Reset solicitado por {interaction.user}")

        e = make_embed(
            title="RESET",
            footer=settings.bot_name,
            author_name=f"{settings.bot_name} • channel ops",
            author_icon=self.bot.user.display_avatar.url if self.bot.user else None,
        )
        e.description = f"{retro_divider()}\n♻️ **canal resetado**\n{retro_divider()}"

        e.add_field(name="🆕 Novo canal", value=new_ch.mention, inline=False)
        e.add_field(name="⚠️ Atenção", value="ID mudou. Se canal estiver em env var, atualize.", inline=False)
        e.add_field(name="✅ Dica", value="Reset é o único método sem limite/idade pra limpar tudo.", inline=False)

        await interaction.followup.send(embed=e, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CleanupCog(bot))
