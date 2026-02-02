import discord
from discord import app_commands
from discord.ext import commands

from config import load_settings
from utils.embeds import make_embeds

settings = load_settings()


def _ok(v: bool) -> str:
    return "✅" if v else "❌"


class HealthCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="health", description="Mostra status do bot (admin).")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def health(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        if not guild:
            e = make_embeds(
                title="⛔ Erro",
                text="Use isso dentro de um servidor.",
                color=0xE74C3C,
                footer=settings.embed_footer,
            )[0]
            await interaction.followup.send(embed=e, ephemeral=True)
            return

        bot_member = guild.get_member(self.bot.user.id) if self.bot.user else None  # type: ignore
        role = guild.get_role(settings.verified_role_id)

        verify_ch = guild.get_channel(settings.verify_channel_id) if settings.verify_channel_id else None
        welcome_ch = guild.get_channel(settings.welcome_channel_id) if settings.welcome_channel_id else None
        rules_ch = guild.get_channel(settings.rules_channel_id) if settings.rules_channel_id else None
        log_ch = guild.get_channel(settings.log_channel_id) if settings.log_channel_id else None

        lines = []
        lines.append(f"{_ok(bool(settings.guild_id))} GUILD_ID: {settings.guild_id or 'não definido'}")
        lines.append(f"{_ok(bool(settings.verify_channel_id and isinstance(verify_ch, discord.TextChannel)))} VERIFY_CHANNEL_ID")
        lines.append(f"{_ok(bool(settings.welcome_channel_id and isinstance(welcome_ch, discord.TextChannel)))} WELCOME_CHANNEL_ID")
        lines.append(f"{_ok(bool(settings.rules_channel_id and isinstance(rules_ch, discord.TextChannel)))} RULES_CHANNEL_ID")
        lines.append(f"{_ok(bool(role))} VERIFIED_ROLE_ID (cargo existe)")
        lines.append(f"{_ok(True)} Bot online: {self.bot.user}")  # type: ignore

        # Permissões nos canais onde precisa pin
        if bot_member and isinstance(welcome_ch, discord.TextChannel):
            p = welcome_ch.permissions_for(bot_member)
            lines.append(f"{_ok(p.send_messages)} Perm: enviar msg em #boas-vindas")
            lines.append(f"{_ok(p.manage_messages)} Perm: gerenciar msgs (pin) em #boas-vindas")

        if bot_member and isinstance(rules_ch, discord.TextChannel):
            p = rules_ch.permissions_for(bot_member)
            lines.append(f"{_ok(p.send_messages)} Perm: enviar msg em #regras")
            lines.append(f"{_ok(p.manage_messages)} Perm: gerenciar msgs (pin) em #regras")

        if bot_member and isinstance(log_ch, discord.TextChannel):
            p = log_ch.permissions_for(bot_member)
            lines.append(f"{_ok(p.send_messages)} Perm: enviar msg em #logs")

        # Anti-raid opcional
        lines.append(f"{_ok(settings.min_account_age_days >= 0)} MIN_ACCOUNT_AGE_DAYS = {settings.min_account_age_days}")
        lines.append(f"{_ok(True)} REQUIRE_AVATAR = {settings.require_avatar}")

        e = make_embeds(
            title="🩺 Health",
            text="\n".join(lines),
            color=0x3498DB,
            footer=settings.embed_footer,
        )[0]
        await interaction.followup.send(embed=e, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HealthCog(bot))
