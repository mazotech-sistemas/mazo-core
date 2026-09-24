"""Testes do mazo_core.auth: fail-fast, JWT, bcrypt."""

import os

import pytest


def test_import_sem_jwt_secret_falha(monkeypatch):
    os.environ["JWT_SECRET"] = "valido-para-importar-64-characters-0123456789abcd"
    import importlib
    import mazo_core.auth
    importlib.reload(mazo_core.auth)
    monkeypatch.delenv("JWT_SECRET", raising=False)
    with pytest.raises(ValueError, match="obrigatorio"):
        importlib.reload(mazo_core.auth)


def test_import_secret_curto_falha(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "curto")
    import importlib
    import mazo_core.auth
    with pytest.raises(ValueError, match="pelo menos 32"):
        importlib.reload(mazo_core.auth)


def _import_auth():
    os.environ.setdefault("JWT_SECRET", "teste-secret-com-64-characters-0123456789abcdef")
    import importlib
    import mazo_core.auth

    importlib.reload(mazo_core.auth)
    return mazo_core.auth


def test_hash_e_verificar_senha():
    auth = _import_auth()
    h = auth.hash_senha("minhaSenha123")
    assert h != "minhaSenha123"
    assert auth.verificar_senha("minhaSenha123", h) is True
    assert auth.verificar_senha("errada", h) is False


def test_verificar_senha_hash_invalido_nao_levanta():
    auth = _import_auth()
    assert auth.verificar_senha("x", "hash-invalido") is False


def test_criar_e_decodificar_token():
    auth = _import_auth()
    token = auth.criar_token({"sub": "u1", "role": "admin"})
    dados = auth.decodificar_token(token)
    assert dados["sub"] == "u1"
    assert dados["role"] == "admin"
    assert "exp" in dados


def test_refresh_token_markado():
    auth = _import_auth()
    dados = auth.decodificar_token(auth.criar_refresh_token({"sub": "u1"}))
    assert dados["tipo"] == "refresh"


def test_token_invalido_retorna_none():
    auth = _import_auth()
    assert auth.decodificar_token("token-invalido") is None


def test_algoritmo_fixo_hs256():
    auth = _import_auth()
    assert auth.ALGORITHM == "HS256"
