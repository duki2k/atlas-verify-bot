# Discord Verify & Welcome Bot (Python)

Bot simples para:
- Dar cargo de "não verificado" quando alguém entra
- Enviar boas-vindas (canal + DM)
- Verificar com botão ✅ e trocar cargos

## Requisitos
- Python 3.10+ (discord.py exige Python 3.8+, mas recomendo 3.10+)
- Um bot criado no Developer Portal
- **Server Members Intent** habilitado

## Configuração rápida

1) Clone o repo e instale deps:
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

2) Copie `.env.example` para `.env` e preencha.

3) Rode:
```bash
python main.py
```

## Como usar no servidor

1) Crie 2 cargos:
- `🕵️ Não Verificado` (ou qualquer nome)
- `✅ Membro` (ou qualquer nome)

2) Ajuste a **ordem dos cargos**:
- O cargo do bot precisa ficar **acima** dos cargos que ele vai adicionar/remover.

3) No Discord, rode:
- `/setup_verificacao` (apenas admin/gerenciar servidor)

Isso posta a mensagem de verificação com o botão ✅.

## Deploy (opções)
- Docker: use o `Dockerfile`
- Qualquer host que rode processo Python com env vars

> Dica: mantenha `DISCORD_TOKEN` só como variável de ambiente (nunca commitar token).
