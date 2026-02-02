import discord
from discord import app_commands
from discord.ext import commands

from config import load_settings
from utils.embeds import make_embeds

settings = load_settings()


def _default_target_channel(interaction: discord.Interaction) -> discord.TextChannel | None:
    ch = interaction.channel
    return ch if isinstance(ch, discord.TextChannel) else None


class CleanupCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="limpar_canal",
        description="Apaga mensagens de um canal (admin).",
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def limpar_canal(
        self,
        interaction: discord.Interaction,
        canal: discord.TextChannel | None = None,
        quantidade: app_commands.Range[int, 1, 1000] = 200,
        apagar_fixadas: bool = False,
        apenas_do_bot: bool = False,
        mensagem_final: str | None = None,
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        if not interaction.guild:
            await interaction.followup.send("Use isso dentro de um servidor.", ephemeral=True)
            return

        target = canal or _default_target_channel(interaction)
        if not target:
            await interaction.followup.send("Não consegui identificar o canal alvo.", ephemeral=True)
            return

        # Permissões mínimas
        me = interaction.guild.me
        if me:
            perms = target.permissions_for(me)
            if not perms.read_message_history or not perms.manage_messages:
                await interaction.followup.send(
                    f"❌ Sem permissão em {target.mention}. Precisa de **Ler histórico** + **Gerenciar mensagens**.",
                    ephemeral=True,
                )
                return

        def check(m: discord.Message) -> bool:
            if not apagar_fixadas and m.pinned:
                return False
            if apenas_do_bot:
                return m.author and self.bot.user and (m.author.id == self.bot.user.id)
            return True

        deleted_count = 0
        try:
            deleted = await target.purge(limit=quantidade, check=check, bulk=True)
            deleted_count = len(deleted)
        except discord.Forbidden:
            await interaction.followup.send("❌ Eu não tenho permissão pra apagar mensagens nesse canal.", ephemeral=True)
            return
        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao limpar: `{type(e).__name__}`", ephemeral=True)
            return

        # Mensagem no canal (com canal “na frente”)
        final_text = mensagem_final.strip() if mensagem_final else "✅ Canal limpo!"
        try:
            await target.send(f"{target.mention} {final_text}")
        except Exception:
            pass

        # Confirmação no admin (ephemeral)
        emb = make_embeds(
            "🧹 Limpeza concluída",
            f"Canal: {target.mention}\nApagadas: **{deleted_count}** mensagens\nFiltro: "
            f"{'apenas do bot' if apenas_do_bot else 'todas'} | "
            f"{'incluiu fixadas' if apagar_fixadas else 'preservou fixadas'}",
            0x2ECC71,
            settings.embed_footer,
        )[0]
        await interaction.followup.send(embed=emb, ephemeral=True)

    @app_commands.command(
        name="resetar_canal",
        description="Zera 100% o canal (clona e apaga o original).",
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    async def resetar_canal(
        self,
        interaction: discord.Interaction,
        canal: discord.TextChannel | None = None,
        mensagem_final: str | None = None,
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        if not interaction.guild:
            await interaction.followup.send("Use isso dentro de um servidor.", ephemeral=True)
            return

        target = canal or _default_target_channel(interaction)
        if not target:
            await interaction.followup.send("Não consegui identificar o canal alvo.", ephemeral=True)
            return

        # ⚠️ Aviso importante sobre ID
        warn = (
            f"⚠️ Isso vai **criar um novo canal** e apagar o antigo.\n"
            f"O novo canal terá **outro ID**.\n"
            f"Se esse canal estiver em env vars (VERIFY_CHANNEL_ID etc.), você terá que atualizar o ID."
        )

        try:
            # clone preserva permissões/tema/tópico
            new_ch = await target.clone(reason=f"Reset solicitado por {interaction.user}")
            await new_ch.edit(position=target.position, category=target.category)

            # apaga antigo
            await target.delete(reason=f"Reset solicitado por {interaction.user}")

            # mensagem no novo canal (com canal “na frente”)
            final_text = mensagem_final.strip() if mensagem_final else "✅ Canal resetado e pronto!"
            try:
                await new_ch.send(f"{new_ch.mention} {final_text}")
            except Exception:
                pass

            emb = make_embeds(
                "♻️ Reset concluído",
                f"Canal antigo apagado.\nNovo canal: {new_ch.mention}\n\n{warn}",
                0xF1C40F,
                settings.embed_footer,
            )[0]
            await interaction.followup.send(embed=emb, ephemeral=True)

        except discord.Forbidden:
            await interaction.followup.send(
                "❌ Sem permissão pra clonar/apagar canal. Precisa de **Gerenciar canais**.",
                ephemeral=True,
            )
        except Exception as e:
            await interaction.followup.send(f"❌ Erro no reset: `{type(e).__name__}`", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CleanupCog(bot))
