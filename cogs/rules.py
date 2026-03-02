import discord
from discord import app_commands
from discord.ext import commands

from config import load_settings
from utils.embeds import make_embed, retro_divider

settings = load_settings()

AGREE_BUTTON_ID = "robo_duki_rules_agree_v1"


def build_rules_embed(guild: discord.Guild | None, bot_user: discord.ClientUser | None) -> discord.Embed:
    thumb = guild.icon.url if guild and guild.icon else None

    e = make_embed(
        title="REGRAS",
        footer=settings.bot_name,
        thumbnail_url=thumb,
        author_name=f"{settings.bot_name} • Duki Odyssey ®",
        author_icon=bot_user.display_avatar.url if bot_user else None,
    )

    e.description = (
        f"🎮 **Duki Odyssey ® — Regras da Comunidade**\n"
        f"{retro_divider()}\n"
        f"💜 Aqui é resenha e jogo. **Respeito e bom senso são obrigatórios.**\n"
        f"{retro_divider()}\n"
    )

    e.add_field(
        name="🧠 Convivência",
        value=(
            "• Sem ataques, preconceito, assédio ou humilhação\n"
            "• Zoação ok ✅ / desrespeito não ❌\n"
            "• Se alguém pedir pra parar, **parou**"
        ),
        inline=False,
    )

    e.add_field(
        name="💬 Uso do servidor",
        value=(
            "• Evite spam/flood e excesso de mensagens/emojis\n"
            "• Use os canais corretamente (cada um tem um propósito)\n"
            "• Evite marcações desnecessárias (@everyone/cargos)"
        ),
        inline=False,
    )

    e.add_field(
        name="🚫 Conteúdo proibido",
        value=(
            "• +18, gore ou violência extrema\n"
            "• Links suspeitos, golpes, phishing ou vírus\n"
            "• Qualquer atitude mal-intencionada contra membros"
        ),
        inline=False,
    )

    e.add_field(
        name="📢 Divulgação",
        value=(
            "• Somente nos canais apropriados\n"
            "• Proibido vender produtos/contas/serviços\n"
            "• Parcerias: fale com a staff"
        ),
        inline=False,
    )

    e.add_field(
        name="🔒 Privacidade",
        value=(
            "• Não exponha dados pessoais (seu ou de terceiros)\n"
            "• Problemas no PV envolvendo membros podem gerar punição"
        ),
        inline=False,
    )

    e.add_field(
        name="⚖️ Punições",
        value="Aviso → Mute → Kick → Ban (casos graves podem ser ban direto).",
        inline=False,
    )

    e.add_field(
        name="✅ Liberação de acesso",
        value="Clique no botão **✅ Li e concordo** para receber o cargo e liberar os canais.",
        inline=False,
    )

    return e


class RulesView(discord.ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(
        label="Li e concordo",
        style=discord.ButtonStyle.success,
        custom_id=AGREE_BUTTON_ID,
        emoji="✅",
    )
    async def agree(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild is None or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Use isso dentro do servidor.", ephemeral=True)
            return

        role_id = getattr(settings, "member_role_id", None)
        if not role_id:
            await interaction.response.send_message("✅ Confirmado! (MEMBER_ROLE_ID não configurado.)", ephemeral=True)
            return

        role = interaction.guild.get_role(role_id)
        if role is None:
            await interaction.response.send_message("⚠️ Cargo não encontrado. Verifique MEMBER_ROLE_ID.", ephemeral=True)
            return

        member: discord.Member = interaction.user
        if role in member.roles:
            await interaction.response.send_message("✅ Você já tem acesso liberado.", ephemeral=True)
            return

        try:
            await member.add_roles(role, reason="Aceitou as regras (botão).")
        except discord.Forbidden:
            await interaction.response.send_message("⛔ Bot sem permissão/hierarquia pra dar cargos.", ephemeral=True)
            return

        await interaction.response.send_message("✅ Acesso liberado! Bem-vindo(a) 💜", ephemeral=True)


class RulesCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.bot.add_view(RulesView(bot))  # botão persistente

    @app_commands.command(name="setup_regras", description="Posta o embed de regras com botão (admin).")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_regras(self, interaction: discord.Interaction, canal: discord.TextChannel, fixar: bool = True):
        await interaction.response.defer(ephemeral=True)

        embed = build_rules_embed(interaction.guild, self.bot.user)
        view = RulesView(self.bot)

        msg = await canal.send(embed=embed, view=view)
        if fixar:
            try:
                await msg.pin(reason="Regras do servidor (Robô Duki).")
            except discord.Forbidden:
                await interaction.followup.send("⚠️ Postei, mas não consegui FIXAR (sem permissão).", ephemeral=True)
                return

        await interaction.followup.send(f"✅ Regras postadas em {canal.mention}", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RulesCog(bot))
