# 🛡️ Atlas Verify Bot (Discord)

Bot de verificação para Discord com **botão ✅**, liberação de acesso por cargo, **mensagens fixadas** (boas-vindas e regras), **logs** e comandos de administração travados para **um único canal** (`#admin-bot`).

---

## ✅ O que ele faz

- ✅ **Verificação por botão** (sem captcha externo)
- ✅ Após verificar, dá o cargo **Membro** (ou o cargo definido por `VERIFIED_ROLE_ID`)
- ✅ **Bloqueia canais para @everyone** e libera acesso só após o cargo (configuração no Discord)
- ✅ Mensagens longas ficam **fixadas** em:
  - `#boas-vindas` (com texto personalizado)
  - `#regras` (com texto personalizado)
- ✅ Textos com **menções clicáveis** dos canais (via placeholders)
- ✅ Canal privado de **logs** (`LOG_CHANNEL_ID`)
- ✅ Comandos **somente no #admin-bot** (`ADMIN_CHANNEL_ID`)
- ✅ Comando `/health` para diagnóstico rápido de permissões/IDs
- ✅ Comando `/setup_verificacao` que:
  - cria/atualiza a mensagem de verificação (sem spam)
  - cria/atualiza as mensagens fixadas
- ✅ Hospedagem gratuita (ex.: **JustRunMy.App**) com atualização pelo GitHub

---

## 📦 Requisitos

- Python 3.10+ (para rodar localmente)
- `discord.py` (via `requirements.txt`)
- Um app/bot criado no Discord Developer Portal
- Permissões configuradas no servidor (detalhes abaixo)

---

## 🔐 Configuração no Discord (IMPORTANTE)

### 1) Crie o cargo “Membro”
- Nome sugerido: **Membro**
- Esse cargo será dado após verificação (via `VERIFIED_ROLE_ID`)

### 2) Trave os canais para @everyone
**Objetivo:** usuário entra e só vê o mínimo até verificar.

No servidor, faça:
- Para `@everyone`:
  - ❌ **View Channel** (negado) nos canais que você quer esconder
- Para o cargo **Membro**:
  - ✅ **View Channel** nos canais liberados

💡 Geralmente você deixa visível para @everyone apenas:
- `#verificação` (ou o mínimo necessário)
- `#boas-vindas` e `#regras` podem ficar visíveis também (opcional)

### 3) Permissões do bot
O bot precisa:
- No canal `#verificação`:
  - ✅ Send Messages
- Em `#boas-vindas` e `#regras`:
  - ✅ Send Messages
  - ✅ Manage Messages (para fixar/pinar)
  - ✅ Read Message History (para editar pins sem travar)
- No servidor:
  - ✅ Manage Roles (ou permissão pra atribuir o cargo)
  - ✅ O cargo do bot deve ficar **acima** do cargo “Membro” na hierarquia

---

## ⚙️ Variáveis de ambiente (Environment Variables)

> ✅ Nunca comite `DISCORD_TOKEN` no GitHub.

### Obrigatórias
- `DISCORD_TOKEN` = token do bot
- `GUILD_ID` = ID do seu servidor
- `ADMIN_CHANNEL_ID` = ID do canal `#admin-bot` (onde comandos serão permitidos)
- `VERIFIED_ROLE_ID` = ID do cargo que libera acesso (ex.: Membro)
- `VERIFY_CHANNEL_ID` = canal onde fica o botão de verificação
- `WELCOME_CHANNEL_ID` = canal onde fica a mensagem fixada de boas-vindas
- `RULES_CHANNEL_ID` = canal onde fica a mensagem fixada de regras

### Recomendadas
- `LOG_CHANNEL_ID` = canal privado de logs (somente admins)

### Canais clicáveis (opcional, mas recomendado)
- `NEWS_CHANNEL_ID` = #notícias
- `ASSETS_CHANNEL_ID` = #ativos-mundiais
- `EDUCATION_CHANNEL_ID` = #educação-financeira
- `CHAT_CHANNEL_ID` = #chat-geral
- `SUPPORT_CHANNEL_ID` = #suporte

### Segurança (opcional)
- `MIN_ACCOUNT_AGE_DAYS` = idade mínima da conta para verificar (ex.: `7`)
- `REQUIRE_AVATAR` = exigir avatar para verificar (`1` ou `0`)

### Textos do bot
- `VERIFY_MESSAGE` = texto da mensagem do botão de verificação
- `PINNED_WELCOME_TEXT` = texto que o bot vai postar e fixar em `#boas-vindas`
- `PINNED_RULES_TEXT` = texto que o bot vai postar e fixar em `#regras`
- `EMBED_FOOTER` = rodapé padrão dos embeds (ex.: “Atlas Community”)

---

## 🧩 Placeholders suportados nos textos fixados

Você pode usar estes placeholders no `PINNED_WELCOME_TEXT` e `PINNED_RULES_TEXT`:

- `{member_role}` → mostra o cargo “Membro” (texto/menção dependendo da versão)
- `{rules_channel}` → menção do canal de regras
- `{news_channel}` `{assets_channel}` `{education_channel}` `{chat_channel}` `{support_channel}` → menções clicáveis

⚠️ Não use placeholders fora dessa lista.

---

## 🧠 Comandos

> ✅ Todos os comandos só funcionam no canal definido em `ADMIN_CHANNEL_ID`.

- `/setup_verificacao`  
  Posta/atualiza o embed de verificação no canal e cria/atualiza mensagens fixadas.

- `/health`  
  Diagnóstico rápido: verifica IDs e permissões do bot nos canais.

- `/ping`  
  Mostra status do bot e latência (embed robusto).

---

## 🚀 Primeiro uso (passo-a-passo)

1) Configure as env vars no host (JustRunMy.App ou outro)
2) Reinicie o bot
3) No Discord, **no #admin-bot**, execute:
   - `/setup_verificacao`
4) Teste a verificação no canal `#verificação` clicando no botão ✅

---

## ☁️ Deploy no JustRunMy.App (atualizar pelo GitHub)

### Atualizar o código no host (Shell)
Cole no Shell do JustRunMy.App:

```bash
cd /app/discord-verify-bot
curl -L "https://github.com/duki2k/atlas-verify-bot/archive/refs/heads/main.zip" -o update.zip
unzip -o update.zip
cp -rf atlas-verify-bot-main/* .
rm -rf atlas-verify-bot-main update.zip
pip install -r requirements.txt
