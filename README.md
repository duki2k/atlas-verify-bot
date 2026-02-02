# Atlas Verify Bot (Discord) — 1 cargo + 1 canal visível

Esse bot faz:
- Deixar o servidor “trancado” (novos membros só com @everyone não veem quase nada)
- Ter **um único canal** `#verificar` visível
- Postar uma mensagem com botão ✅
- Ao clicar: dar **um cargo** `✅ Verificado` que libera o resto do servidor

## Requisitos
- Python 3.10+
- Bot criado no Discord Developer Portal
- **Server Members Intent** habilitado (recomendado)

## Como configurar o servidor (Opção A)
1) Crie 1 cargo: `✅ Verificado`
2) Crie uma categoria `✅ VERIFICAÇÃO` com o canal `#verificar`
3) Crie uma categoria `🔒 SERVIDOR` com todos os outros canais

Permissões:
- Categoria `🔒 SERVIDOR`:
  - @everyone: **Ver canal ❌**
  - ✅ Verificado: **Ver canal ✅**
- Categoria `✅ VERIFICAÇÃO`:
  - @everyone: **Ver canal ✅**
  - (opcional) @everyone: **Enviar mensagens ❌** (evita spam)

IMPORTANTE:
- O cargo do bot precisa ficar **acima** do cargo ✅ Verificado.

## Variáveis de ambiente
Você NÃO deve commitar token no GitHub. Configure no seu host:

- DISCORD_TOKEN (obrigatório)
- VERIFIED_ROLE_ID (obrigatório)
- VERIFY_CHANNEL_ID (recomendado pra /setup_verificacao)
- GUILD_ID (opcional, acelera sync dos comandos)
- LOG_CHANNEL_ID (opcional)
- WELCOME_CHANNEL_ID (opcional)
- MIN_ACCOUNT_AGE_DAYS (opcional)

## Comandos
- /ping
- /setup_verificacao (admin)

## Rodar local (opcional)
Se quiser rodar localmente, você pode criar um `.env` no seu PC (não subir no GitHub) ou setar env vars no terminal.
