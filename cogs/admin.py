import os
import time
import platform
import datetime as dt
import discord
from discord import app_commands
from discord.ext import commands

from config import load_settings
from utils.embeds import make_embed, retro_divider

settings = load_settings()
START_TIME = time.time()

try:
    import psutil  # type: ignore
except Exception:
    psutil = None


def _uptime_seconds() -> int:
    return int(time.time() - START_TIME)


def _fmt_uptime(sec: int) -> str:
    d, s = divmod(sec, 86400)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    if d > 0:
        return f"{d}d {h}h {m}m {s}s"
    if h > 0:
        return f"{h}h {m}m {s}s"
    if m > 0:
        return f"{m}m {s}s"
    return f"{s}s"


def _days_since(dt_obj: dt.datetime) -> int:
    now = dt.datetime.now(dt.timezone.utc)
    if dt_obj.tzinfo is None:
        dt_obj = dt_obj.replace(tzinfo=dt.timezone.utc)
    return max(0, (now - dt_obj).days)


def _human_bytes(n: float) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while n >= 1024 and i < len(units) - 1:
        n /= 1024
        i += 1
    return f"{n:.1f}{units[i]}"


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def _thumb(self, guild: discord.Guild | None) -> str | None:
        return guild.icon.url if guild and guild.icon else None

    @app_commands.command(name="ping", description="Latência e saúde do Robô Duki (admin).")
    @app_commands.checks.has_permissions(administrator=True)
    async def ping(self, interaction: discord.Interaction) -> None:
        created = interaction.created_at
        now = dt.datetime.now(dt.timezone.utc)
        roundtrip_ms = int((now - created).total_seconds() * 1000)
        ws_ms = int(self.bot.latency * 1000)
        up = _fmt_uptime(_uptime_seconds())

        guild = interaction.guild
        e = make_embed(
            title="PING",
            footer=settings.bot_name,
            thumbnail_url=self._thumb(guild),
            author_name=settings.bot_name,
            author_icon=self.bot.user.display_avatar.url if self.bot.user else None,
        )

        e.description = f"{retro_divider()}\n🕹️ **telemetria ao vivo**\n{retro_divider()}"

        e.add_field(name="🏓 WebSocket", value=f"**{ws_ms} ms**", inline=True)
        e.add_field(name="⚡ Roundtrip", value=f"**{roundtrip_ms} ms**", inline=True)
        e.add_field(name="🕒 Uptime", value=f"**{up}**", inline=True)

        quality = "🟢 LISO" if ws_ms < 120 else "🟡 OK" if ws_ms < 250 else "🔴 LENTO"
        e.add_field(name="📡 Qualidade", value=quality, inline=True)
        e.add_field(name="🌐 Servidor", value=(guild.name if guild else "DM"), inline=True)
        e.add_field(name="🧩 Comandos", value=f"`{len(self.bot.tree.get_commands())}` carregados", inline=True)

        await interaction.response.send_message(embed=e, ephemeral=True)

    @app_commands.command(name="status", description="Painel do servidor (admin). Sem ranking de cargos.")
    @app_commands.checks.has_permissions(administrator=True)
    async def status(self, interaction: discord.Interaction, listar_cargos: bool = False) -> None:
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("Use no servidor.", ephemeral=True)
            return

        total = guild.member_count or len(guild.members)
        days_active = _days_since(guild.created_at)
        online = sum(1 for m in guild.members if m.status in (discord.Status.online, discord.Status.idle, discord.Status.dnd))
        bots = sum(1 for m in guild.members if m.bot)

        roles = [r for r in guild.roles if not r.is_default()]
        roles_with_members = [r for r in roles if len(r.members) > 0]

        e = make_embed(
            title="STATUS",
            footer=settings.bot_name,
            thumbnail_url=self._thumb(guild),
            author_name=f"{settings.bot_name} • painel",
            author_icon=self.bot.user.display_avatar.url if self.bot.user else None,
        )
        e.description = f"{retro_divider()}\n🌌 **duki odyssey® • console**\n{retro_divider()}"

        e.add_field(name="👥 Membros", value=f"**{total}**", inline=True)
        e.add_field(name="🟢 Online (aprox.)", value=f"**{online}**", inline=True)
        e.add_field(name="🤖 Bots", value=f"**{bots}**", inline=True)

        e.add_field(name="🗓️ Idade do servidor", value=f"**{days_active} dias**", inline=True)
        e.add_field(name="🏷️ Cargos (total)", value=f"**{len(roles)}**", inline=True)
        e.add_field(name="🧩 Cargos (com membros)", value=f"**{len(roles_with_members)}**", inline=True)

        if listar_cargos:
            roles_sorted = sorted(roles_with_members, key=lambda r: r.name.lower())
            lines = [f"• {r.mention}: `{len(r.members)}`" for r in roles_sorted[:25]]
            txt = "\n".join(lines) if lines else "_nenhum cargo com membros_"
            if len(roles_sorted) > 25:
                txt += f"\n… + `{len(roles_sorted) - 25}` cargos"
            e.add_field(name="📜 Cargos (A→Z)", value=txt, inline=False)
        else:
            e.add_field(name="ℹ️ Dica", value="Use `/status listar_cargos:true` pra listar cargos (A→Z).", inline=False)

        await interaction.response.send_message(embed=e, ephemeral=True)

    @app_commands.command(name="health", description="Saúde do host (CPU/RAM/Disk) + uptime (admin).")
    @app_commands.checks.has_permissions(administrator=True)
    async def health(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild
        e = make_embed(
            title="HEALTH",
            footer=settings.bot_name,
            thumbnail_url=self._thumb(guild),
            author_name=f"{settings.bot_name} • diagnostics",
            author_icon=self.bot.user.display_avatar.url if self.bot.user else None,
        )
        e.description = f"{retro_divider()}\n🧪 **status do host**\n{retro_divider()}"

        ws_ms = int(self.bot.latency * 1000)
        e.add_field(name="🏓 WebSocket", value=f"**{ws_ms} ms**", inline=True)
        e.add_field(name="🕒 Uptime", value=f"**{_fmt_uptime(_uptime_seconds())}**", inline=True)
        e.add_field(name="🧰 Python", value=f"`{platform.python_version()}`", inline=True)

        e.add_field(name="🖥️ SO", value=f"`{platform.system()} {platform.release()}`", inline=True)
        e.add_field(name="📦 PID", value=f"`{os.getpid()}`", inline=True)
        e.add_field(name="🧠 Mode", value="guild-only commands", inline=True)

        if psutil:
            try:
                cpu = psutil.cpu_percent(interval=0.3)
                mem = psutil.virtual_memory()
                disk = psutil.disk_usage("/")

                e.add_field(name="🔥 CPU", value=f"**{cpu:.0f}%**", inline=True)
                e.add_field(name="🧠 RAM", value=f"**{mem.percent:.0f}%**\n({_human_bytes(mem.used)}/{_human_bytes(mem.total)})", inline=True)
                e.add_field(name="💾 Disco", value=f"**{disk.percent:.0f}%**\n({_human_bytes(disk.used)}/{_human_bytes(disk.total)})", inline=True)
            except Exception:
                e.add_field(name="⚠️ psutil", value="Falhou ao ler métricas do host.", inline=False)
        else:
            e.add_field(name="⚠️ psutil", value="Não instalado/indisponível.", inline=False)

        await interaction.response.send_message(embed=e, ephemeral=True)

    @app_commands.command(name="about", description="Sobre o Robô Duki (admin).")
    @app_commands.checks.has_permissions(administrator=True)
    async def about(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild
        app_id = getattr(self.bot, "application_id", None) or "auto"
        cmds = self.bot.tree.get_commands()
        cmd_names = ", ".join(f"`/{c.name}`" for c in cmds)

        e = make_embed(
            title="ABOUT",
            footer=settings.bot_name,
            thumbnail_url=self._thumb(guild),
            author_name=settings.bot_name,
            author_icon=self.bot.user.display_avatar.url if self.bot.user else None,
        )
        e.description = f"{retro_divider()}\n💜 **robô duki / arcade build**\n{retro_divider()}"

        e.add_field(name="🤖 Bot", value=f"**{settings.bot_name}**", inline=True)
        e.add_field(name="🆔 App ID", value=f"`{app_id}`", inline=True)
        e.add_field(name="🧩 Comandos", value=cmd_names, inline=False)
        e.add_field(name="📌 Regra", value=f"Comandos só em <#{settings.admin_channel_id}> (admin).", inline=False)

        await interaction.response.send_message(embed=e, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AdminCog(bot))
