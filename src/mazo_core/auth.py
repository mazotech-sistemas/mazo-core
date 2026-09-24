"""Camada de autenticacao compartilhada (JWT + bcrypt).

Padrao Mazotech:
- fail-fast: nao importa sem JWT_SECRET valido
- HS256 fixo (sem downgrade por env)
- bcrypt com rounds configuravel
"""
import os
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

ALGORITHM = "HS256"
BCRYPT_ROUNDS = int(os.getenv("BCRYPT_ROUNDS", "12"))
MIN_LEN_SECRET = 32


def exigir_secret(env_var: str = "JWT_SECRET") -> str:
    """Le e valida o segredo do JWT. Falha no import se ausente/curto."""
    s = os.getenv(env_var)
    if not s:
        raise ValueError(
            f"{env_var} e obrigatorio no ambiente. Defina via variavel de ambiente "
            "(python -c \"import secrets; print(secrets.token_hex(32))\")."
        )
    if len(s) < MIN_LEN_SECRET:
        raise ValueError(
            f"{env_var} deve ter pelo menos {MIN_LEN_SECRET} caracteres (tem {len(s)})."
        )
    return s


JWT_SECRET = exigir_secret()

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTOS", "15"))
REFRESH_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_REFRESH_EXPIRE_MINUTOS", str(7 * 24 * 60)))


def hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode("utf-8")


def verificar_senha(senha_plana: str, hash_: str) -> bool:
    try:
        return bcrypt.checkpw(senha_plana.encode("utf-8"), hash_.encode("utf-8"))
    except ValueError:
        return False


def _codificar(dados: dict, expira_minutos: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=expira_minutos)
    return jwt.encode({**dados, "exp": exp}, JWT_SECRET, algorithm=ALGORITHM)


def criar_token(dados: dict) -> str:
    return _codificar(dados, ACCESS_TOKEN_EXPIRE_MINUTES)


def criar_refresh_token(dados: dict) -> str:
    return _codificar({**dados, "tipo": "refresh"}, REFRESH_TOKEN_EXPIRE_MINUTES)


def decodificar_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
    except JWTError:
        return None
