import time
import platform
import discord
from discord import app_commands
from discord.ext import commands

from config import load_settings
from utils.embeds import make_embed, format_embed_body

settings = load_settings()


def _uptime_seconds(bot: commands.Bot) -> int:
    start = getattr(bot, "_start_time", None)
    if not start:
        return 0
    return int(time.time() - start)


def _fmt_uptime(secs: int) -> str:
    if secs <= 0:
        return "—"
    days, rem = divmod(secs, 86400)
    hours, rem = divmod(rem, 3600)
    mins, rem = divmod(rem, 60)
    if days:
        return f"{days}d {hours}h {mins}m"
    if hours:
        return f"{hours}h {mins}m"
    if mins:
        return f"{mins}m {rem}s"
    return f"{rem}s"


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # marca início (pra uptime)
        if not hasattr(self.bot, "_start_time"):
            setattr(self.bot, "_start_time", time.time())

    # -------------------------
    # /about
    # -------------------------
    @app_commands.command(name="about", description="Mostra info do bot e comandos carregados (admin).")
    @app_commands.checks.has_permissions(administrator=True)
    async def about(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild
        guild_name = guild.name if guild else "DM"
        guild_id = guild.id if guild else "—"

        cmds = [c.name for c in self.bot.tree.get_commands()]
        cmds_sorted = ", ".join(f"`/{c}`" for c in sorted(cmds)) if cmds else "—"

        embed = make_embed(
            title="SOBRE",
            footer=settings.bot_name,
            author_name=settings.bot_name,
            author_icon=self.bot.user.display_avatar.url if self.bot.user else None,
            thumbnail_url=guild.icon.url if guild and guild.icon else None,
        )

        body = (
            f"🧠 **{settings.bot_name}** online.\n\n"
            f"🏷️ Servidor: **{guild_name}**\n"
            f"🆔 Guild ID: `{guild_id}`\n"
            f"⏱️ Uptime: **{_fmt_uptime(_uptime_seconds(self.bot))}**\n"
            f"🐍 Python: `{platform.python_version()}`\n"
            f"📦 discord.py: `{discord.__version__}`\n\n"
            f"🎮 **Comandos carregados**\n{cmds_sorted}"
        )

        embed.description = format_embed_body(body)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # -------------------------
    # /health
    # -------------------------
    @app_commands.command(name="health", description="Checagem rápida de saúde do bot (admin).")
    @app_commands.checks.has_permissions(administrator=True)
    async def health(self, interaction: discord.Interaction) -> None:
        embed = make_embed(
            title="HEALTH",
            footer=settings.bot_name,
            author_name=settings.bot_name,
            author_icon=self.bot.user.display_avatar.url if self.bot.user else None,
        )

        ws_ms = int(self.bot.latency * 1000)
        up = _fmt_uptime(_uptime_seconds(self.bot))

        body = (
            f"✅ **Status:** ONLINE\n"
            f"🛰️ **WebSocket:** `{ws_ms}ms`\n"
            f"⏱️ **Uptime:** `{up}`\n"
        )
        embed.description = format_embed_body(body)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # -------------------------
    # /ping (com latência)
    # -------------------------
    @app_commands.command(name="ping", description="Teste de latência (admin).")
    @app_commands.checks.has_permissions(administrator=True)
    async def ping(self, interaction: discord.Interaction) -> None:
        t0 = time.perf_counter()
        await interaction.response.defer(ephemeral=True)
        roundtrip_ms = int((time.perf_counter() - t0) * 1000)

        ws_ms = int(self.bot.latency * 1000)

        embed = make_embed(
            title="PING",
            footer=settings.bot_name,
            author_name=settings.bot_name,
            author_icon=self.bot.user.display_avatar.url if self.bot.user else None,
        )

        body = (
            f"🛰️ **WebSocket:** `{ws_ms}ms`\n"
            f"⚡ **Round-trip (interaction):** `{roundtrip_ms}ms`\n"
            f"🧩 **Shard:** `{interaction.guild.shard_id if interaction.guild else 0}`\n"
        )
        embed.description = format_embed_body(body)
        await interaction.followup.send(embed=embed, ephemeral=True)

    # -------------------------
    # /status (sem ranking)
    # -------------------------
    @app_commands.command(name="status", description="Resumo do servidor: membros e contagem por cargo (admin).")
    @app_commands.checks.has_permissions(administrator=True)
    async def status(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("Use no servidor.", ephemeral=True)
            return

        # membros
        total = guild.member_count or len(guild.members)
        humans = sum(1 for m in guild.members if not m.bot)
        bots = sum(1 for m in guild.members if m.bot)

        # contagem por cargos (top 12) sem poluir
        role_counts = []
        for role in guild.roles:
            if role.is_default():
                continue
            count = len(role.members)
            if count > 0:
                role_counts.append((count, role))

        role_counts.sort(reverse=True, key=lambda x: x[0])
        top = role_counts[:12]

        roles_text = "—"
        if top:
            roles_text = "\n".join([f"• {r.mention}: **{c}**" for c, r in top])

        embed = make_embed(
            title="STATUS",
            footer=settings.bot_name,
            author_name=f"{settings.bot_name} • status",
            author_icon=self.bot.user.display_avatar.url if self.bot.user else None,
            thumbnail_url=guild.icon.url if guild.icon else None,
        )

        body = (
            f"🏷️ **Servidor:** {guild.name}\n"
            f"👥 **Membros:** **{total}** (👤 {humans} / 🤖 {bots})\n"
            f"⏱️ **Uptime do bot:** {_fmt_uptime(_uptime_seconds(self.bot))}\n"
        )
        embed.description = format_embed_body(body)

        embed.add_field(name="📌 Cargos (top)", value=roles_text, inline=False)

        # dia de criação do servidor (contador de dias ativo)
        created = guild.created_at
        if created:
            days = (discord.utils.utcnow() - created).days
            embed.add_field(name="🗓️ Servidor ativo há", value=f"**{days} dias**", inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AdminCog(bot))
