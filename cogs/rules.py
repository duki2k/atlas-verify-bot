import discord
from discord import app_commands
from discord.ext import commands
from views.verify import VerifyRulesView

class RulesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings = bot.settings

    @app_commands.command(name="setup_regras", description="Envia a mensagem de regras com botão.")
    async def setup_regras(self, interaction: discord.Interaction):
        if interaction.channel_id != self.settings.admin_channel_id:
            return await interaction.response.send_message(
                "Este comando só pode ser usado no canal admin.",
                ephemeral=True
            )

        await interaction.channel.send(
            content=self.settings.rules_text,
            view=VerifyRulesView(self.settings.rules_role_id)
        )
        await interaction.response.send_message(
            "✅ Mensagem de regras enviada com sucesso.",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(RulesCog(bot))
