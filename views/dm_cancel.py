# views/dm_cancel.py
import discord

class DmCancelPresenceView(discord.ui.View):
    def __init__(self, event_id: int):
        super().__init__(timeout=None)
        self.event_id = event_id

    @discord.ui.button(
        label="❌ Cancelar presença",
        style=discord.ButtonStyle.danger,
        custom_id="duki:karaoke:dm:cancel"
    )
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "✅ Sua presença foi cancelada.",
            ephemeral=True
        )
