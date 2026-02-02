import discord
from discord import app_commands
from discord.ext import commands

from config import load_settings
from utils.embeds import make_embeds

settings = load_settings()


def ok(v: bool) -> str:
    return "✅" if v else "❌"


class HealthCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="health", description="Status do bot e permissões (admin).")
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
        verified_role = guild.get_role(settings.verified_role_id)

        def ch_ok(cid: int | None) -> bool:
            if not cid:
                return False
            ch = guild.get_channel(cid)
            return isinstance(ch, discord.TextChannel)

        lines = [
            f"{ok(bool(settings.guild_id))} GUILD_ID: {settings.guild_id or 'não definido'}",
            f"{ok(ch_ok(settings.verify_channel_id))} VERIFY_CHANNEL_ID",
            f"{ok(ch_ok(settings.welcome_channel_id))} WELCOME_CHANNEL_ID",
            f"{ok(ch_ok(settings.rules_channel_id))} RULES_CHANNEL_ID",
            f"{ok(bool(verified_role))} VERIFIED_ROLE_ID (cargo existe)",
            f"{ok(True)} MIN_ACCOUNT_AGE_DAYS = {settings.min_account_age_days}",
            f"{ok(True)} REQUIRE_AVATAR = {settings.require_avatar}",
        ]

        # Permissões relevantes
        if bot_member and settings.verify_channel_id:
            ch = guild.get_channel(settings.verify_channel_id)
            if isinstance(ch, discord.TextChannel):
                p = ch.permissions_for(bot_member)
                lines += [
                    f"{ok(p.read_message_history)} Perm: ler histórico em #verificação",
                    f"{ok(p.send_messages)} Perm: enviar msg em #verificação",
                ]

        for label, cid in (("boas-vindas", settings.welcome_channel_id), ("regras", settings.rules_channel_id)):
            if bot_member and cid:
                ch = guild.get_channel(cid)
                if isinstance(ch, discord.TextChannel):
                    p = ch.permissions_for(bot_member)
                    lines += [
                        f"{ok(p.read_message_history)} Perm: ler histórico em #{label}",
                        f"{ok(p.send_messages)} Perm: enviar msg em #{label}",
                        f"{ok(p.manage_messages)} Perm: gerenciar msgs (pin) em #{label}",
                    ]

        if bot_member and settings.log_channel_id:
            ch = guild.get_channel(settings.log_channel_id)
            if isinstance(ch, discord.TextChannel):
                p = ch.permissions_for(bot_member)
                lines.append(f"{ok(p.send_messages)} Perm: enviar msg em #logs")

        e = make_embeds(
            title="🩺 Health",
            text="\n".join(lines),
            color=0x3498DB,
            footer=settings.embed_footer,
        )[0]
        await interaction.followup.send(embed=e, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HealthCog(bot))
