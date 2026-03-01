import time
import datetime as dt
import discord
from discord import app_commands
from discord.ext import commands

from config import load_settings
from utils.embeds import make_embed, retro_divider

settings = load_settings()
START_TIME = time.time()


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


def _percent(part: int, total: int) -> str:
    if total <= 0:
        return "0%"
    return f"{(part / total) * 100:.1f}%"


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="ping", description="Latência e saúde do bot (admin).")
    @app_commands.checks.has_permissions(administrator=True)
    async def ping(self, interaction: discord.Interaction) -> None:
        created = interaction.created_at
        now = dt.datetime.now(dt.timezone.utc)
        roundtrip_ms = int((now - created).total_seconds() * 1000)
        ws_ms = int(self.bot.latency * 1000)
        up = _fmt_uptime(_uptime_seconds())

        guild = interaction.guild
        thumb = guild.icon.url if guild and guild.icon else None

        e = make_embed(
            title="PING",
            footer=settings.bot_name,
            thumbnail_url=thumb,
        )

        # Bloco retrô
        e.description = f"{retro_divider()}\n🕹️ **Sinal do Robô Duki**\n{retro_divider()}"

        e.add_field(name="🏓 WebSocket (Discord ↔ Bot)", value=f"**{ws_ms} ms**", inline=True)
        e.add_field(name="⚡ Roundtrip (comando)", value=f"**{roundtrip_ms} ms**", inline=True)
        e.add_field(name="🕒 Uptime", value=f"**{up}**", inline=False)

        # indicadores rápidos (não é “ping do usuário”, é do bot)
        quality = "🟢 LISO" if ws_ms < 120 else "🟡 OK" if ws_ms < 250 else "🔴 LENTO"
        e.add_field(name="📡 Qualidade", value=quality, inline=True)
        e.add_field(name="🧠 Shard", value=str(getattr(self.bot, "shard_id", "auto")), inline=True)
        e.add_field(name="🔧 Versão", value="discord.py 2.x", inline=True)

        await interaction.response.send_message(embed=e, ephemeral=True)

    @app_commands.command(name="status", description="Status do servidor: membros, cargos, idade (admin).")
    @app_commands.checks.has_permissions(administrator=True)
    async def status(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("Use no servidor.", ephemeral=True)
            return

        total = guild.member_count or len(guild.members)
        days_active = _days_since(guild.created_at)

        # status online (aproximado)
        online = sum(1 for m in guild.members if m.status in (discord.Status.online, discord.Status.idle, discord.Status.dnd))
        bots = sum(1 for m in guild.members if m.bot)

        # contagem por cargos (ignora @everyone)
        role_counts: list[tuple[discord.Role, int]] = []
        for role in guild.roles:
            if role.is_default():
                continue
            role_counts.append((role, len(role.members)))

        # ✅ ordena por quantidade (desc), desempate pela posição
        role_counts.sort(key=lambda x: (x[1], x[0].position), reverse=True)

        # top 10 mais usados
        top_lines = []
        for role, cnt in role_counts[:10]:
            top_lines.append(f"• {role.mention}: `{cnt}` ({_percent(cnt, total)})")
        top_text = "\n".join(top_lines) if top_lines else "_sem cargos_"

        thumb = guild.icon.url if guild.icon else None

        e = make_embed(
            title="STATUS",
            footer=settings.bot_name,
            thumbnail_url=thumb,
        )

        e.description = f"{retro_divider()}\n🌌 **Duki Odyssey ® — Painel**\n{retro_divider()}"

        e.add_field(name="👥 Membros", value=f"**{total}**", inline=True)
        e.add_field(name="🟢 Online (aprox.)", value=f"**{online}**", inline=True)
        e.add_field(name="🤖 Bots", value=f"**{bots}**", inline=True)

        e.add_field(name="🗓️ Dias desde criação", value=f"**{days_active} dias**", inline=True)
        e.add_field(name="🏷️ Cargos (total)", value=f"**{len(role_counts)}**", inline=True)
        e.add_field(name="🧩 Top cargos (por membros)", value=top_text, inline=False)

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
            # se apagou quase nada, para
            if len(deleted) < 2:
                break

        e = make_embed(title="CLEAN", footer=settings.bot_name)
        e.description = f"{retro_divider()}\n🧹 **Limpeza executada**\n{retro_divider()}"

        e.add_field(name="📍 Canal", value=canal.mention, inline=False)
        e.add_field(name="✅ Apagadas", value=f"**{deleted_total}**", inline=True)
        e.add_field(name="⚙️ Modo", value=("TUDO" if tudo else f"{lotes} lote(s)"), inline=True)
        e.add_field(name="📌 Fixadas", value=("apagar" if apagar_fixadas else "preservar"), inline=True)

        e.add_field(
            name="ℹ️ Nota",
            value="Mensagens muito antigas podem não ser removidas por limitações da API do Discord. Para zerar 100%, use `/reset_channel`.",
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

        e = make_embed(title="RESET", footer=settings.bot_name)
        e.description = f"{retro_divider()}\n♻️ **Canal resetado**\n{retro_divider()}"

        e.add_field(name="🆕 Novo canal", value=new_ch.mention, inline=False)
        e.add_field(name="⚠️ Atenção", value="O canal novo tem outro ID. Se ele estiver em env var, atualize.", inline=False)
        e.add_field(name="✅ Dica", value="Use reset quando quiser *limpar tudo* sem limite.", inline=False)

        await interaction.followup.send(embed=e, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AdminCog(bot))
