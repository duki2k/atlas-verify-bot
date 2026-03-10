# views/karaoke_signup.py
import discord

class KaraokeSignupView(discord.ui.View):
    def __init__(self, event_id: int):
        super().__init__(timeout=None)
        self.event_id = event_id

    @discord.ui.button(
        label="🎤 Vou cantar",
        style=discord.ButtonStyle.success,
        custom_id="duki:karaoke:signup:singer"
    )
    async def singer_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "✅ Inscrição como cantor registrada.",
            ephemeral=True
        )

    @discord.ui.button(
        label="👀 Só assistir",
        style=discord.ButtonStyle.primary,
        custom_id="duki:karaoke:signup:spectator"
    )
    async def spectator_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "✅ Inscrição como espectador registrada.",
            ephemeral=True
        )
