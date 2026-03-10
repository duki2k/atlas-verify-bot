import discord

class VerifyRulesView(discord.ui.View):
    def __init__(self, rules_role_id: int):
        super().__init__(timeout=None)
        self.rules_role_id = int(rules_role_id)

    @discord.ui.button(
        label="✅ Li e concordo",
        style=discord.ButtonStyle.success,
        custom_id="duki:rules:accept"
    )
    async def accept_rules(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if interaction.guild is None:
            return await interaction.response.send_message(
                "Este botão só funciona dentro do servidor.",
                ephemeral=True
            )

        member = interaction.user
        if not isinstance(member, discord.Member):
            try:
                member = interaction.guild.get_member(interaction.user.id) or await interaction.guild.fetch_member(interaction.user.id)
            except discord.HTTPException:
                return await interaction.response.send_message(
                    "Não consegui localizar seu perfil no servidor.",
                    ephemeral=True
                )

        role = interaction.guild.get_role(self.rules_role_id)
        if role is None:
            return await interaction.response.send_message(
                "O cargo de verificação não foi encontrado. Avise a staff.",
                ephemeral=True
            )

        bot_member = interaction.guild.me
        if bot_member is None:
            try:
                bot_member = await interaction.guild.fetch_member(interaction.client.user.id)
            except discord.HTTPException:
                return await interaction.response.send_message(
                    "Não consegui validar minhas permissões no servidor.",
                    ephemeral=True
                )

        if role >= bot_member.top_role:
            return await interaction.response.send_message(
                "Eu não consigo dar esse cargo porque ele está acima do meu cargo. "
                "Mova meu cargo para cima do cargo de verificação.",
                ephemeral=True
            )

        if role in member.roles:
            return await interaction.response.send_message(
                "Você já está verificado(a).",
                ephemeral=True
            )

        try:
            await member.add_roles(role, reason="Aceitou as regras do servidor")
        except discord.Forbidden:
            return await interaction.response.send_message(
                "Não tenho permissão para dar esse cargo. "
                "Verifique 'Gerenciar cargos' e a hierarquia.",
                ephemeral=True
            )
        except discord.HTTPException:
            return await interaction.response.send_message(
                "O Discord recusou a ação agora. Tente novamente em instantes.",
                ephemeral=True
            )

        await interaction.response.send_message(
            "✅ Verificação concluída. Seu acesso foi liberado.",
            ephemeral=True
        )
