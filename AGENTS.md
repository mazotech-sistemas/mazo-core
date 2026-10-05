# AGENTS.md — mazo-core

Referencia rapida p/ agentes de codigo neste repo. Completa com o AGENTS.md do hub em ../..

## Dados basicos
- **Porta**: N/A
- **Preco**: N/A
- **Repo**: https://github.com/mazotech-sistemas/mazo-core.git
- **Status**: lib
- **Dominio**: biblioteca compartilhada
- **Dependencies**: nenhuma
- **Entrypoint**: N/A (lib)
- **Testes**: tests/

## mazo-core (biblioteca compartilhada, nao e app)
Modulos em src/mazo_core/: auth (JWT HS256 + bcrypt, fail-fast exige
JWT_SECRET min 32 chars), whatsapp (canais oficial/embutido/simulado),
lembretes (janelas e estado de envio), branding.
Instalacao: `pip install git+https://github.com/mazotech-sistemas/mazo-core.git`.

## Armadilhas locais
- SQLAlchemy <2.1. pytest-asyncio loop scope session.

## Commits
Mensagem em uma linha, imperativo, pt-BR. Sem prefixo, sem emoji.

## Antes de concluir
- Testes verdes
- Lint passa
- Docs atualizadas (README + docs/products/<nome>.md)
