import discord
from discord import app_commands
from discord.ext import commands

from config import load_settings
from utils.embeds import make_embed

settings = load_settings()


class CleanupCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="limpar_canal", description="Apaga mensagens de um canal (admin).")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def limpar_canal(
        self,
        interaction: discord.Interaction,
        canal: discord.TextChannel | None = None,
        quantidade: app_commands.Range[int, 1, 1000] = 200,
        apagar_fixadas: bool = False,
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        if not interaction.guild:
            await interaction.followup.send("Use isso dentro de um servidor.", ephemeral=True)
            return

        target = canal if canal else (interaction.channel if isinstance(interaction.channel, discord.TextChannel) else None)
        if not target:
            await interaction.followup.send("Não consegui identificar o canal alvo.", ephemeral=True)
            return

        def check(m: discord.Message) -> bool:
            if not apagar_fixadas and m.pinned:
                return False
            return True

        try:
            deleted = await target.purge(limit=quantidade, check=check, bulk=True)
            e = make_embed(
                title="🧹 Limpeza concluída",
                description=f"Canal: {target.mention}\nApagadas: **{len(deleted)}** mensagens",
                color=0x2ECC71,
                footer=settings.embed_footer,
            )
            await interaction.followup.send(embed=e, ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("❌ Sem permissão para limpar esse canal.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao limpar: `{type(e).__name__}`", ephemeral=True)

    @app_commands.command(name="resetar_canal", description="Zera 100% o canal (clona e apaga o original).")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def resetar_canal(
        self,
        interaction: discord.Interaction,
        canal: discord.TextChannel | None = None,
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        if not interaction.guild:
            await interaction.followup.send("Use isso dentro de um servidor.", ephemeral=True)
            return

        target = canal if canal else (interaction.channel if isinstance(interaction.channel, discord.TextChannel) else None)
        if not target:
            await interaction.followup.send("Não consegui identificar o canal alvo.", ephemeral=True)
            return

        try:
            new_ch = await target.clone(reason=f"Reset solicitado por {interaction.user}")
            await new_ch.edit(position=target.position, category=target.category)
            await target.delete(reason=f"Reset solicitado por {interaction.user}")

            warn = (
                "⚠️ Canal resetado.\n"
                "O novo canal tem **outro ID**. Se ele estiver em env vars, atualize o ID no host."
            )
            e = make_embed(
                title="♻️ Reset concluído",
                description=f"Novo canal: {new_ch.mention}\n\n{warn}",
                color=0xF1C40F,
                footer=settings.embed_footer,
            )
            await interaction.followup.send(embed=e, ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("❌ Sem permissão (precisa Gerenciar canais).", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Erro no reset: `{type(e).__name__}`", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CleanupCog(bot))
