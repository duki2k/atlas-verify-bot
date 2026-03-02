    # =========================
    # /enviar_msg (texto longo preservando linhas)
    # =========================
    @app_commands.command(
        name="enviar_msg",
        description="Envia texto comum pegando o conteúdo de uma mensagem (ideal para texto longo com quebras).",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def enviar_msg(
        self,
        interaction: discord.Interaction,
        canal: discord.TextChannel,
        mensagem_id: str,
        pingar: bool = False,
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        try:
            mid = int(mensagem_id.strip())
        except ValueError:
            await interaction.followup.send("⚠️ mensagem_id inválido. Use o ID da mensagem (Modo desenvolvedor).", ephemeral=True)
            return

        src_channel = interaction.channel
        if not isinstance(src_channel, discord.TextChannel):
            await interaction.followup.send("Use esse comando em um canal de texto do servidor.", ephemeral=True)
            return

        try:
            msg = await src_channel.fetch_message(mid)
        except Exception:
            await interaction.followup.send("⚠️ Não consegui encontrar essa mensagem nesse canal.", ephemeral=True)
            return

        text = (msg.content or "").replace("\r\n", "\n").replace("\r", "\n").strip()
        if not text:
            await interaction.followup.send("⚠️ A mensagem está vazia (sem texto).", ephemeral=True)
            return

        if len(text) > 2000:
            await interaction.followup.send(
                "⚠️ O texto passa de 2000 caracteres (limite do Discord para mensagem comum). "
                "Divida em 2 mensagens ou use embed.",
                ephemeral=True,
            )
            return

        try:
            await canal.send(text, allowed_mentions=_safe_allowed_mentions(pingar))
        except Exception as e:
            await interaction.followup.send(f"⛔ Falha ao enviar: `{type(e).__name__}`", ephemeral=True)
            return

        await interaction.followup.send(f"✅ Texto enviado em {canal.mention}", ephemeral=True)
