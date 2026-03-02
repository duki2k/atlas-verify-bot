import discord
from discord import app_commands
from discord.ext import commands

from config import load_settings
from utils.embeds import make_embed, format_embed_body

settings = load_settings()


class CleanupCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # -------------------------
    # /clean (purge)
    # -------------------------
    @app_commands.command(name="clean", description="Limpa mensagens de um canal (admin).")
    @app_commands.checks.has_permissions(administrator=True)
    async def clean(
        self,
        interaction: discord.Interaction,
        canal: discord.TextChannel,
        quantidade: app_commands.Range[int, 1, 1000] = 100,
        incluir_fixadas: bool = False,
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        def check(msg: discord.Message) -> bool:
            if incluir_fixadas:
                return True
            return not msg.pinned

        try:
            deleted = await canal.purge(limit=quantidade, check=check, bulk=True, reason=f"{settings.bot_name}: clean")
        except discord.Forbidden:
            await interaction.followup.send("⛔ Sem permissão para apagar mensagens nesse canal.", ephemeral=True)
            return
        except Exception as e:
            await interaction.followup.send(f"⛔ Falha ao limpar: `{type(e).__name__}`", ephemeral=True)
            return

        embed = make_embed(
            title="LIMPEZA",
            footer=settings.bot_name,
            author_name=settings.bot_name,
            author_icon=self.bot.user.display_avatar.url if self.bot.user else None,
        )
        body = (
            f"🧹 Canal: {canal.mention}\n"
            f"🗑️ Removidas: **{len(deleted)}** mensagens\n"
            f"📌 Fixadas incluídas: **{'sim' if incluir_fixadas else 'não'}**\n"
        )
        embed.description = format_embed_body(body)
        await interaction.followup.send(embed=embed, ephemeral=True)

    # -------------------------
    # /reset_channel (clona e remove o antigo)
    # -------------------------
    @app_commands.command(name="reset_channel", description="Reseta um canal (clona e remove o antigo) (admin).")
    @app_commands.checks.has_permissions(administrator=True)
    async def reset_channel(self, interaction: discord.Interaction, canal: discord.TextChannel) -> None:
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        if not guild:
            await interaction.followup.send("Use no servidor.", ephemeral=True)
            return

        try:
            new_ch = await canal.clone(reason=f"{settings.bot_name}: reset_channel")
            await new_ch.edit(position=canal.position)
            await canal.delete(reason=f"{settings.bot_name}: reset_channel")
        except discord.Forbidden:
            await interaction.followup.send("⛔ Sem permissão para clonar/deletar canal.", ephemeral=True)
            return
        except Exception as e:
            await interaction.followup.send(f"⛔ Falha ao resetar canal: `{type(e).__name__}`", ephemeral=True)
            return

        embed = make_embed(
            title="RESET DE CANAL",
            footer=settings.bot_name,
            author_name=settings.bot_name,
            author_icon=self.bot.user.display_avatar.url if self.bot.user else None,
        )
        body = (
            f"♻️ Canal resetado com sucesso.\n"
            f"✅ Novo canal: {new_ch.mention}\n"
        )
        embed.description = format_embed_body(body)

        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CleanupCog(bot))
