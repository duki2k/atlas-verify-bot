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
except Exception:  # pragma: no cover
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
        if guild and guild.icon:
            return guild.icon.url
        return None

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

        # cargos (sem ranking): só contagens + opcional lista alfabética (limitada)
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
            # alfabético = “não ranking”
            roles_sorted = sorted(roles_with_members, key=lambda r: r.name.lower())
            lines = []
            # limita por tamanho do embed (mantém elegante)
            for r in roles_sorted[:25]:
                lines.append(f"• {r.mention}: `{len(r.members)}`")
            txt = "\n".join(lines) if lines else "_nenhum cargo com membros_"
            if len(roles_sorted) > 25:
                txt += f"\n… + `{len(roles_sorted) - 25}` cargos"
            e.add_field(name="📜 Cargos (A→Z)", value=txt, inline=False)
        else:
            e.add_field(
                name="ℹ️ Dica",
                value="Use `/status listar_cargos:true` pra listar cargos (A→Z).",
                inline=False,
            )

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
        e.add_field(name="📦 Process", value=f"`{os.getpid()}`", inline=True)
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
            e.add_field(name="⚠️ psutil", value="Não instalado/indisponível. (Host pode bloquear).", inline=False)

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
        e.description = f"{retro_divider()}\n💜 **robô duk i / arcade build**\n{retro_divider()}"

        e.add_field(name="🤖 Bot", value=f"**{settings.bot_name}**", inline=True)
        e.add_field(name="🆔 App ID", value=f"`{app_id}`", inline=True)
        e.add_field(name="🧩 Comandos", value=f"{cmd_names}", inline=False)

        e.add_field(name="📌 Regras", value=f"Comandos só em <#{settings.admin_channel_id}> (admin).", inline=False)
        e.add_field(name="🕒 Uptime", value=f"**{_fmt_uptime(_uptime_seconds())}**", inline=True)
        e.add_field(name="🏁 Build", value="neon purple • retro ui", inline=True)

        await interaction.response.send_message(embed=e, ephemeral=True)

    @app_commands.command(name="clean", description="Limpa mensagens de um canal (admin).")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clean(
        self,
        interaction: discord.Interaction,
        canal: discord.TextChannel,
        tudo: bool = False,
        lotes: app_commands.Range[int, 1, 50] = 5,
        apagar_fixadas: bool = False,
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        deleted_total = 0
        loops = 999999 if tudo else lotes

        def check(m: discord.Message) -> bool:
            if not apagar_fixadas and m.pinned:
                return False
            return True

        for _ in range(loops):
            deleted = await canal.purge(limit=100, check=check, bulk=True)
            deleted_total += len(deleted)
            if len(deleted) < 2:
                break

        e = make_embed(
            title="CLEAN",
            footer=settings.bot_name,
            author_name=f"{settings.bot_name} • cleanup",
            author_icon=self.bot.user.display_avatar.url if self.bot.user else None,
        )
        e.description = f"{retro_divider()}\n🧹 **limpeza concluída**\n{retro_divider()}"

        e.add_field(name="📍 Canal", value=canal.mention, inline=False)
        e.add_field(name="✅ Apagadas", value=f"**{deleted_total}**", inline=True)
        e.add_field(name="⚙️ Modo", value=("TUDO" if tudo else f"{lotes} lote(s)"), inline=True)
        e.add_field(name="📌 Fixadas", value=("apagar" if apagar_fixadas else "preservar"), inline=True)
        e.add_field(
            name="ℹ️ Nota",
            value="Mensagens muito antigas podem não ser removidas pela API. Para zerar 100%, use `/reset_channel`.",
            inline=False,
        )

        await interaction.followup.send(embed=e, ephemeral=True)

    @app_commands.command(name="reset_channel", description="Zera 100% o canal (clona e apaga o original).")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def reset_channel(self, interaction: discord.Interaction, canal: discord.TextChannel) -> None:
        await interaction.response.defer(ephemeral=True)

        new_ch = await canal.clone(reason=f"Reset solicitado por {interaction.user}")
        await new_ch.edit(position=canal.position, category=canal.category)
        await canal.delete(reason=f"Reset solicitado por {interaction.user}")

        e = make_embed(
            title="RESET",
            footer=settings.bot_name,
            author_name=f"{settings.bot_name} • channel ops",
            author_icon=self.bot.user.display_avatar.url if self.bot.user else None,
        )
        e.description = f"{retro_divider()}\n♻️ **canal resetado**\n{retro_divider()}"

        e.add_field(name="🆕 Novo canal", value=new_ch.mention, inline=False)
        e.add_field(name="⚠️ Atenção", value="ID mudou. Se canal estiver em env var, atualize.", inline=False)
        e.add_field(name="✅ Dica", value="Reset é o único método sem limite/idade pra limpar tudo.", inline=False)

        await interaction.followup.send(embed=e, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AdminCog(bot))
