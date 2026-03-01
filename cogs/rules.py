import discord
from discord import app_commands
from discord.ext import commands

from config import load_settings
from utils.embeds import make_embed, retro_divider

settings = load_settings()

# custom_id fixo = view persistente (continua funcionando após restart)
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

    # Layout gamer/arcade (bem legível)
    e.description = (
        f"{retro_divider()}\n"
        f"🎮 **LEIA E CONFIRME PARA LIBERAR O ACESSO**\n"
        f"{retro_divider()}\n\n"
        f"💜 Este servidor é pra amizade, resenha e jogo.\n"
        f"✅ Respeito e bom senso são obrigatórios.\n"
    )

    e.add_field(
        name="🧠 Convivência",
        value=(
            "• Sem ataques, humilhação, preconceito ou assédio\n"
            "• Zoação ok ✅ / falta de respeito não ❌\n"
            "• Se alguém pedir pra parar, parou."
        ),
        inline=False,
    )

    e.add_field(
        name="💬 Uso dos canais",
        value=(
            "• Evite spam/flood e marcações desnecessárias\n"
            "• Use cada canal pro seu propósito\n"
            "• LFG é pra chamar pra jogar — não pra briga 😈"
        ),
        inline=False,
    )

    e.add_field(
        name="🚫 Proibido",
        value=(
            "• Conteúdo +18, gore, violência extrema\n"
            "• Links suspeitos, golpes, phishing, vírus\n"
            "• Qualquer tentativa de prejudicar membros"
        ),
        inline=False,
    )

    e.add_field(
        name="🔒 Privacidade",
        value=(
            "• Não poste dados pessoais (seu ou de terceiros)\n"
            "• Problemas no PV envolvendo membros podem virar punição"
        ),
        inline=False,
    )

    e.add_field(
        name="⚖️ Moderação",
        value="Aviso → Mute → Kick → Ban (casos graves podem ser ban direto).",
        inline=False,
    )

    e.add_field(
        name="✅ Para liberar o acesso",
        value="Clique no botão **✅ Li e concordo** abaixo.",
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

        member: discord.Member = interaction.user
        role_id = settings.member_role_id

        # Se não configurou role, ainda confirma
        if not role_id:
            await interaction.response.send_message("✅ Confirmado! (Cargo não configurado no host.)", ephemeral=True)
            return

        role = interaction.guild.get_role(role_id)
        if role is None:
            await interaction.response.send_message("⚠️ Cargo de membro não encontrado. Verifique MEMBER_ROLE_ID.", ephemeral=True)
            return

        if role in member.roles:
            await interaction.response.send_message("✅ Você já tem acesso liberado.", ephemeral=True)
            return

        try:
            await member.add_roles(role, reason="Aceitou as regras (botão).")
        except discord.Forbidden:
            await interaction.response.send_message("⛔ Sem permissão para dar cargos. Ajuste a hierarquia do bot.", ephemeral=True)
            return
        except Exception:
            await interaction.response.send_message("⛔ Erro ao liberar acesso. Veja o host/logs.", ephemeral=True)
            return

        # Log opcional
        if settings.log_channel_id:
            ch = interaction.guild.get_channel(settings.log_channel_id)
            if isinstance(ch, discord.TextChannel):
                try:
                    await ch.send(f"✅ {member.mention} aceitou as regras e recebeu {role.mention}.")
                except Exception:
                    pass

        await interaction.response.send_message(f"✅ Acesso liberado! Bem-vindo(a), {member.mention} 💜", ephemeral=True)


class RulesCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # view persistente (botão continua funcionando após restart)
        self.bot.add_view(RulesView(bot))

    @app_commands.command(name="setup_regras", description="Posta o embed de regras com botão (admin).")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_regras(self, interaction: discord.Interaction, canal: discord.TextChannel, fixar: bool = True) -> None:
        await interaction.response.defer(ephemeral=True)

        embed = build_rules_embed(interaction.guild, self.bot.user)
        view = RulesView(self.bot)

        try:
            msg = await canal.send(embed=embed, view=view)
        except Exception as e:
            await interaction.followup.send(f"⛔ Não consegui postar: `{type(e).__name__}`", ephemeral=True)
            return

        if fixar:
            try:
                await msg.pin(reason="Regras do servidor (Robô Duki).")
            except discord.Forbidden:
                await interaction.followup.send("⚠️ Postei, mas não consegui FIXAR (sem permissão).", ephemeral=True)
                return
            except Exception:
                await interaction.followup.send("⚠️ Postei, mas falhou ao fixar.", ephemeral=True)
                return

        await interaction.followup.send(f"✅ Regras postadas em {canal.mention}", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RulesCog(bot))
