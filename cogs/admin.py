import time
import platform
import datetime as dt
from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands

from config import load_settings
from utils.embeds import make_embed

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


def _ts(t: dt.datetime | None) -> int | None:
    if not t:
        return None
    if t.tzinfo is None:
        t = t.replace(tzinfo=dt.timezone.utc)
    return int(t.timestamp())


def _safe_line(line: str) -> str:
    # Mantém a descrição dentro do limite do embed (4096). Vamos controlar manualmente.
    return line.replace("\n", " ").strip()


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="ping", description="Status do bot (admin).")
    async def ping(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)

        ws_ms = round(self.bot.latency * 1000)
        guild = interaction.guild
        guild_name = guild.name if guild else "DM"
        channel_name = getattr(interaction.channel, "name", "desconhecido")

        e = discord.Embed(
            title="🏓 Duki Odyssey ® — Status",
            description="Painel rápido (saúde + contexto).",
            color=0x00D26A,
        )

        if self.bot.user and self.bot.user.display_avatar:
            e.set_thumbnail(url=self.bot.user.display_avatar.url)

        e.add_field(name="🟢 Estado", value="Online", inline=True)
        e.add_field(name="⚡ WebSocket", value=f"**{ws_ms} ms**", inline=True)
        e.add_field(name="⏱️ Uptime", value=_uptime(), inline=True)

        e.add_field(name="🧩 discord.py", value=f"`{discord.__version__}`", inline=True)
        e.add_field(name="🐍 Python", value=f"`{platform.python_version()}`", inline=True)
        e.add_field(name="🖥️ Host", value="JustRunMy.App", inline=True)

        e.add_field(name="🏠 Servidor", value=f"`{guild_name}`", inline=False)
        e.add_field(name="📍 Canal", value=f"`#{channel_name}`", inline=False)

        e.set_footer(text=settings.embed_footer)
        await interaction.followup.send(embed=e, ephemeral=True)

    @app_commands.command(name="config", description="Mostra configuração do bot (admin).")
    async def config(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)

        def ch(cid: int | None) -> str:
            return f"<#{cid}>" if cid else "—"

        e = discord.Embed(
            title="⚙️ Config (Duki Odyssey ®)",
            color=0x3498DB,
            description=(
                f"**Admin commands:** {ch(settings.admin_channel_id)}\n"
                f"**Boas-vindas:** {ch(settings.welcome_channel_id)}\n"
                f"**Logs:** {ch(settings.log_channel_id)}\n"
                f"**DM boas-vindas:** {'✅' if settings.dm_welcome_enabled else '❌'}"
            ),
        )
        e.set_footer(text=settings.embed_footer)
        await interaction.followup.send(embed=e, ephemeral=True)

    @app_commands.command(
        name="membros",
        description="Lista membros e há quanto tempo estão no servidor (admin).",
    )
    async def membros(
        self,
        interaction: discord.Interaction,
        ordem: Literal["mais_antigos", "mais_novos"] = "mais_antigos",
        limite: app_commands.Range[int, 5, 200] = 50,
        forcar_chunk: bool = False,
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        if not guild:
            await interaction.followup.send("Use isso dentro de um servidor.", ephemeral=True)
            return

        # Garante cache mais completo (pode demorar em servidores grandes)
        if forcar_chunk:
            try:
                await guild.chunk(cache=True)
            except Exception:
                pass

        members = [m for m in guild.members if not m.bot]
        total = len(members)

        # Ordenação por joined_at
        def key_joined(m: discord.Member):
            return m.joined_at or dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc)

        members.sort(key=key_joined, reverse=(ordem == "mais_novos"))

        # Monta linhas, mas respeita limite do embed
        lines = []
        max_chars = 3600  # margem segura
        used = 0
        shown = 0

        for i, m in enumerate(members[:limite], start=1):
            ts = _ts(m.joined_at)
            if ts:
                when = f"<t:{ts}:R> ( <t:{ts}:d> )"
            else:
                when = "desconhecido"

            line = _safe_line(f"**{i}.** {m.display_name} — entrou {when}")
            add_len = len(line) + 1
            if used + add_len > max_chars:
                break
            lines.append(line)
            used += add_len
            shown += 1

        desc = "\n".join(lines) if lines else "_Sem membros na lista._"
        header = f"Total: **{total}** | Mostrando: **{shown}** | Ordem: **{ordem}**"

        e = discord.Embed(
            title="👥 Membros — tempo no servidor",
            description=f"{header}\n\n{desc}",
            color=0x9B59B6,
        )
        e.set_footer(text=settings.embed_footer)

        # NÃO pingar ninguém
        await interaction.followup.send(
            embed=e,
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AdminCog(bot))
