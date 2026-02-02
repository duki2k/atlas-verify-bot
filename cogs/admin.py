import time
import platform
import discord
from discord import app_commands
from discord.ext import commands

from config import load_settings

settings = load_settings()

START_TIME = time.time()


def _uptime() -> str:
    s = int(time.time() - START_TIME)
    d, s = divmod(s, 86400)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    if d > 0:
        return f"{d}d {h}h {m}m {s}s"
    if h > 0:
        return f"{h}h {m}m {s}s"
    if m > 0:
        return f"{m}m {s}s"
    return f"{s}s"


def _yn(v: bool) -> str:
    return "✅ Sim" if v else "❌ Não"


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="ping", description="Status do bot (admin).")
    async def ping(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)

        # Latência websocket (ms)
        ws_ms = round(self.bot.latency * 1000)

        # Qual canal chamou
        guild_name = interaction.guild.name if interaction.guild else "DM"
        channel_name = getattr(interaction.channel, "name", "desconhecido")

        # Checagem de canal admin
        in_admin_channel = (settings.admin_channel_id is None) or (interaction.channel_id == settings.admin_channel_id)

        # Embed “bonitão”
        e = discord.Embed(
            title="🏓 Atlas Verify — Status",
            description="Painel rápido do bot (saúde + diagnóstico).",
            color=0x00D26A,
        )

        # Thumbnail (ícone do bot)
        if self.bot.user and self.bot.user.display_avatar:
            e.set_thumbnail(url=self.bot.user.display_avatar.url)

        # Campos principais
        e.add_field(name="🟢 Estado", value="Online", inline=True)
        e.add_field(name="⚡ WebSocket", value=f"**{ws_ms} ms**", inline=True)
        e.add_field(name="⏱️ Uptime", value=_uptime(), inline=True)

        # Informações de runtime
        e.add_field(name="🧩 discord.py", value=f"`{discord.__version__}`", inline=True)
        e.add_field(name="🐍 Python", value=f"`{platform.python_version()}`", inline=True)
        e.add_field(name="🖥️ Host", value="JustRunMy.App", inline=True)

        # Contexto (servidor/canal)
        e.add_field(name="🏠 Servidor", value=f"`{guild_name}`", inline=False)
        e.add_field(name="📍 Canal", value=f"`#{channel_name}` (`{interaction.channel_id}`)", inline=False)

        # Segurança / governança
        e.add_field(
            name="🔒 Canal correto (admin-bot)",
            value=_yn(in_admin_channel) + (f"\nPermitido: <#{settings.admin_channel_id}>" if settings.admin_channel_id else ""),
            inline=False,
        )

        # Rodapé
        e.set_footer(text=settings.embed_footer)

        await interaction.followup.send(embed=e, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AdminCog(bot))
