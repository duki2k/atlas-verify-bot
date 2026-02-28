import time
import datetime as dt
import sqlite3
import discord
from discord import app_commands
from discord.ext import commands

from config import load_settings
from utils.embeds import make_embed

settings = load_settings()
START_TIME = time.time()


DB_PATH = "stats.db"


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


def _days_since(dt_obj: dt.datetime) -> int:
    now = dt.datetime.now(dt.timezone.utc)
    if dt_obj.tzinfo is None:
        dt_obj = dt_obj.replace(tzinfo=dt.timezone.utc)
    return max(0, (now - dt_obj).days)


def _init_db() -> None:
    if not settings.enable_stats_tracking:
        return
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_stats (
          guild_id INTEGER NOT NULL,
          user_id INTEGER NOT NULL,
          messages INTEGER NOT NULL DEFAULT 0,
          reactions INTEGER NOT NULL DEFAULT 0,
          PRIMARY KEY (guild_id, user_id)
        )
        """
    )
    con.commit()
    con.close()


def _get_stats(guild_id: int, user_id: int) -> tuple[int, int]:
    if not settings.enable_stats_tracking:
        return (0, 0)
    _init_db()
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT messages, reactions FROM user_stats WHERE guild_id=? AND user_id=?", (guild_id, user_id))
    row = cur.fetchone()
    con.close()
    return (row[0], row[1]) if row else (0, 0)


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        _init_db()

    # ✅ Admin-only global
    def _admin_only(self):
        return app_commands.checks.has_permissions(administrator=True)

    @app_commands.command(name="ping", description="Ping/latência do bot (admin).")
    @app_commands.checks.has_permissions(administrator=True)
    async def ping(self, interaction: discord.Interaction) -> None:
        # roundtrip estimado: tempo do interaction até agora (não é ping do PC do user)
        created = interaction.created_at
        now = dt.datetime.now(dt.timezone.utc)
        roundtrip_ms = int((now - created).total_seconds() * 1000)

        ws_ms = round(self.bot.latency * 1000)

        await interaction.response.send_message(
            embed=make_embed(
                title="PING",
                description=(
                    f"🟣 WS: **{ws_ms} ms**\n"
                    f"🟪 Roundtrip comando: **{roundtrip_ms} ms**\n"
                    f"🕒 Uptime: **{_uptime()}**"
                ),
                footer=f"{settings.bot_name}",
            ),
            ephemeral=True,
        )

    @app_commands.command(name="status", description="Status do servidor: membros, cargos e idade (admin).")
    @app_commands.checks.has_permissions(administrator=True)
    async def status(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("Use no servidor.", ephemeral=True)
            return

        total = guild.member_count or len(guild.members)
        days_active = _days_since(guild.created_at)

        # contagem por cargos (ignora @everyone)
        role_counts = []
        for role in sorted(guild.roles, key=lambda r: r.position, reverse=True):
            if role.is_default():
                continue
            role_counts.append((role.name, len(role.members)))

        # monta texto (limite do embed)
        lines = []
        for name, cnt in role_counts[:25]:  # top 25 por posição
            lines.append(f"• **{name}**: `{cnt}`")
        roles_block = "\n".join(lines) if lines else "_sem cargos_"

        embed = make_embed(
            title="STATUS",
            description=(
                f"👥 Membros: **{total}**\n"
                f"🗓️ Servidor ativo há: **{days_active} dias**\n\n"
                f"🧩 Cargos (top por hierarquia):\n{roles_block}"
            ),
            footer=f"{settings.bot_name}",
            thumbnail_url=guild.icon.url if guild.icon else None,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="user", description="Info de um usuário (admin).")
    @app_commands.checks.has_permissions(administrator=True)
    async def user(self, interaction: discord.Interaction, membro: discord.Member) -> None:
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("Use no servidor.", ephemeral=True)
            return

        joined_days = _days_since(membro.joined_at) if membro.joined_at else None
        account_days = _days_since(membro.created_at)

        roles = [r.mention for r in membro.roles if not r.is_default()]
        roles_txt = " ".join(roles[:20]) if roles else "_sem cargos_"

        msg_count, react_count = _get_stats(guild.id, membro.id)
        stats_txt = (
            f"\n\n📊 **Stats (desde que o tracking foi ligado):**\n"
            f"💬 Mensagens: `{msg_count}`\n"
            f"✨ Reações: `{react_count}`"
        ) if settings.enable_stats_tracking else "\n\n📊 Stats: _tracking desativado_"

        embed = make_embed(
            title="USER",
            description=(
                f"👤 {membro.mention}\n"
                f"🆔 `{membro.id}`\n\n"
                f"🧠 Conta criada: **há {account_days} dias**\n"
                f"📌 No servidor: **há {joined_days} dias**" if joined_days is not None else "📌 No servidor: _desconhecido_"
            ) + f"\n\n🏷️ Cargos:\n{roles_txt}{stats_txt}",
            footer=f"{settings.bot_name}",
            thumbnail_url=membro.display_avatar.url if membro.display_avatar else None,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # Tracking (opcional) — conta mensagens/reactions a partir de agora
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if not settings.enable_stats_tracking:
            return
        if not message.guild or message.author.bot:
            return

        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute(
            "INSERT INTO user_stats (guild_id, user_id, messages, reactions) VALUES (?, ?, 1, 0) "
            "ON CONFLICT(guild_id, user_id) DO UPDATE SET messages = messages + 1",
            (message.guild.id, message.author.id),
        )
        con.commit()
        con.close()

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User | discord.Member) -> None:
        if not settings.enable_stats_tracking:
            return
        if not reaction.message.guild:
            return
        if getattr(user, "bot", False):
            return

        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute(
            "INSERT INTO user_stats (guild_id, user_id, messages, reactions) VALUES (?, ?, 0, 1) "
            "ON CONFLICT(guild_id, user_id) DO UPDATE SET reactions = reactions + 1",
            (reaction.message.guild.id, user.id),
        )
        con.commit()
        con.close()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AdminCog(bot))
