# mazo-core

Camada compartilhada Mazotech: autenticacao (JWT + bcrypt), abstracao de canais WhatsApp e motor de lembretes.

Objetivo: um codigo, muitas verticais. As verticais (suite, oficina-pro) importam esta
camada em vez de duplicar servicos proprios.

## Modulos

- `mazo_core.auth` - JWT HS256 (fixo, sem downgrade por env), fail-fast no import
  (exige `JWT_SECRET` de no minimo 32 chars), helpers bcrypt e criacao/decodificacao
  de access/refresh tokens.
- `mazo_core.whatsapp` - abstracao de canais `oficial` (Meta Cloud API),
  `embutido` (sidecar WhatsApp Web) e `simulado`. Envio de texto, status/qrcode do
  sidecar e validacao de assinatura HMAC SHA-256 de webhook. Configuracao via
  `resolver(chave)`, injetavel para consumers com cache de painel.
- `mazo_core.lembretes` - janelas de lembrete (horas/minutos com margem) e
  derivacao de estado de envio (ENVIADA / FALHA / SIMULADA).

## Requisitos

- Python 3.11+
- Em qualquer app que importe `mazo_core.auth`: variavel `JWT_SECRET` (min 32 chars)

## Instalacao

```bash
pip install git+https://github.com/mazotech-sistemas/mazo-core.git
```

## Deploy em VPS (repo privado)

O core é privado: pip precisa de credencial no servidor. Duas opções:

```bash
# Opcao A: token (fine-grained, só leitura nos repos mazo)
pip install git+https://SEU_TOKEN@github.com/mazotech-sistemas/mazo-core.git@PIN
```

```bash
# Opcao B: chave SSH de deploy (somente leitura, por servidor)
ssh-keygen -t ed25519 -f ~/.ssh/mazo-deploy -N ""
# cadastra a .pub como deploy key no repo, depois:
pip install git+ssh://git@github.com/mazotech-sistemas/mazo-core.git@PIN
```

Troca PIN pelo commit fixado no requirements do produto. Sem credencial o pip falha com 404.

## Uso minimo

```python
from mazo_core import whatsapp

print(whatsapp.canal_ativo())            # "embutido" (padrao)
print(whatsapp.enviar_texto("+551199999", "oi"))  # None + log, canal simulado/sem config
```

```python
import os
os.environ["JWT_SECRET"] = "segredo-aleatorio-de-32-chars"
from mazo_core import auth

token = auth.criar_token({"sub": "1", "role": "admin"})
auth.decodificar_token(token)
```

## Testes

```bash
pytest
```
