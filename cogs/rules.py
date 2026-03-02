import discord
from discord import app_commands
from discord.ext import commands

from config import load_settings

settings = load_settings()


class AgreeView(discord.ui.View):
    def __init__(self, role_id: int, timeout: float | None = None):
        super().__init__(timeout=timeout)
        self.role_id = role_id

    @discord.ui.button(label="✅ Li e concordo", style=discord.ButtonStyle.success, custom_id="rules_agree_button")
    async def agree(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild is None:
            await interaction.response.send_message("Use no servidor.", ephemeral=True)
            return

        member = interaction.user
        if not isinstance(member, discord.Member):
            member = interaction.guild.get_member(interaction.user.id)

        role = interaction.guild.get_role(self.role_id)
        if role is None:
            await interaction.response.send_message("⚠️ Cargo configurado não existe.", ephemeral=True)
            return

        # já tem?
        if isinstance(member, discord.Member) and role in member.roles:
            await interaction.response.send_message("✅ Você já tem acesso.", ephemeral=True)
            return

        try:
            await member.add_roles(role, reason="Aceitou as regras")
        except discord.Forbidden:
            await interaction.response.send_message("⛔ Sem permissão para dar cargo (hierarquia).", ephemeral=True)
            return
        except Exception:
            await interaction.response.send_message("⛔ Erro ao dar cargo.", ephemeral=True)
            return

        await interaction.response.send_message(f"✅ Acesso liberado! Você recebeu {role.mention}.", ephemeral=True)


class RulesCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="setup_regras", description="Posta regras (texto normal) com botão de concordância (admin).")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_regras(
        self,
        interaction: discord.Interaction,
        canal: discord.TextChannel,
        fixar: bool = True,
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        if not settings.rules_role_id:
            await interaction.followup.send("⚠️ RULES_ROLE_ID não definido no host.", ephemeral=True)
            return

        # Texto vindo de variável de ambiente (mais fácil de editar sem mexer no código)
        text = (settings.rules_text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
        if not text:
            await interaction.followup.send("⚠️ RULES_TEXT está vazio. Configure no host.", ephemeral=True)
            return

        view = AgreeView(role_id=settings.rules_role_id, timeout=None)

        try:
            msg = await canal.send(content=text, view=view, allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=True))
            if fixar:
                try:
                    await msg.pin(reason="Regras - fixado pelo bot")
                except Exception:
                    # sem permissão de pin ou canal não permite
                    pass
        except Exception as e:
            await interaction.followup.send(f"⛔ Falha ao postar regras: `{type(e).__name__}`", ephemeral=True)
            return

        await interaction.followup.send(f"✅ Regras postadas em {canal.mention}", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RulesCog(bot))
