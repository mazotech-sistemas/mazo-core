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

## Padrao fabrica
FastAPI + SQLAlchemy >=2.0,<2.1 + SQLite demo em ./data.
JWT_SECRET 32 chars, auth seed admin@admin.com, rate-limit login 5/min.
GET /health e /brand.json publicos, POSTs com auth.
TestClient nao dispara lifespan: create_all no import.
DB limpo por rodada de teste.

## Armadilhas locais
- SQLAlchemy <2.1. pytest-asyncio loop scope session.

## Commits
Mensagem em uma linha, imperativo, pt-BR. Sem prefixo, sem emoji.

## Antes de concluir
- Testes verdes
- Lint passa
- Docs atualizadas (README + docs/products/<nome>.md)
