"""Testes do mazo_core.whatsapp: canais, envio, assinatura."""

import hmac
import hashlib

import pytest

from mazo_core import whatsapp


def _resolver(**vals):
    def r(chave):
        return vals.get(chave, "")
    return r


def test_canal_ativo_padrao_sem_config():
    assert whatsapp.canal_ativo(_resolver()) == "embutido"


def test_canal_ativo_invalido_caem_no_padrao():
    assert whatsapp.canal_ativo(_resolver(WHATSAPP_CANAL="xyz")) == "embutido"


def test_canal_ativo_por_resolver():
    assert whatsapp.canal_ativo(_resolver(WHATSAPP_CANAL="oficial")) == "oficial"


def test_canal_label():
    assert "Meta Cloud" in whatsapp.canal_label(_resolver(WHATSAPP_CANAL="oficial"))
    assert "QR" in whatsapp.canal_label(_resolver(WHATSAPP_CANAL="embutido"))


def test_configurado_simulado_sempre_falso():
    assert whatsapp.configurado(_resolver(WHATSAPP_CANAL="simulado")) is False


def test_configurado_embutido_exige_sidecar():
    assert whatsapp.configurado(_resolver(WHATSAPP_CANAL="embutido")) is False
    assert whatsapp.configurado(_resolver(WHATSAPP_CANAL="embutido", SIDECAR_URL="http://s")) is True


def test_configurado_oficial_exige_token_e_phone():
    base = _resolver(WHATSAPP_CANAL="oficial", WHATSAPP_TOKEN="t")
    assert whatsapp.configurado(base) is False
    base = _resolver(WHATSAPP_CANAL="oficial", WHATSAPP_TOKEN="t", WHATSAPP_PHONE_NUMBER_ID="p")
    assert whatsapp.configurado(base) is True


def test_enviar_texto_simulado_loga_e_retorna_none(monkeypatch, capsys):
    r = _resolver(WHATSAPP_CANAL="simulado")
    assert whatsapp.enviar_texto("+551199999", "oi", r) is None
    saida = capsys.readouterr().out
    assert "SIMULADO" in saida and "+551199999" in saida


def test_enviar_texto_nao_configurado_fica_simulado(monkeypatch, capsys):
    # canal oficial sem credenciais: nao tenta chamada de rede
    assert whatsapp.enviar_texto("+551199999", "oi", _resolver(WHATSAPP_CANAL="oficial")) is None
    assert "SIMULADO" in capsys.readouterr().out


def test_enviar_oficial_erro_de_rede_retorna_none(monkeypatch, capsys):
    import requests as _requests

    def boom(*a, **k):
        raise _requests.RequestException("sem rede")

    monkeypatch.setattr(whatsapp.requests, "post", boom)
    r = _resolver(WHATSAPP_CANAL="oficial", WHATSAPP_TOKEN="t", WHATSAPP_PHONE_NUMBER_ID="p")
    assert whatsapp.enviar_texto("+551199999", "oi", r) is None
    assert "falhou envio" in capsys.readouterr().out


def test_enviar_oficial_retorna_message_id(monkeypatch, capsys):
    class R:
        def raise_for_status(self):
            pass

        def json(self):
            return {"messages": [{"id": "mid-1"}]}

    monkeypatch.setattr(whatsapp.requests, "post", lambda *a, **k: R())
    assert whatsapp.enviar_texto("+551199999", "oi", _resolver(WHATSAPP_CANAL="oficial", WHATSAPP_TOKEN="t", WHATSAPP_PHONE_NUMBER_ID="p")) == "mid-1"


def test_proxy_embutido_indisponivel(monkeypatch):
    import requests as _requests

    def boom(*a, **k):
        raise _requests.RequestException("down")

    monkeypatch.setattr(whatsapp.requests, "request", boom)
    assert whatsapp.status_embutido(_resolver(SIDECAR_URL="http://s")) == {"disponivel": False}
    assert whatsapp.qrcode_embutido(_resolver(SIDECAR_URL="http://s")) == {"disponivel": False}
    assert whatsapp.logout_embutido(_resolver(SIDECAR_URL="http://s")) == {"disponivel": False}


def test_validar_assinatura_valida():
    corpo = b'{"x": 1}'
    sig = "sha256=" + hmac.new(b"segredo-meta", corpo, hashlib.sha256).hexdigest()
    assert whatsapp.validar_assinatura(corpo, sig, segredo="segredo-meta") is True


def test_validar_assinatura_invalida():
    corpo = b'{"x": 1}'
    sig = "sha256=" + "0" * 64
    assert whatsapp.validar_assinatura(corpo, sig, segredo="segredo-meta") is False


def test_validar_assinatura_sem_segredo_falsa(monkeypatch):
    monkeypatch.delenv("META_APP_SECRET", raising=False)
    assert whatsapp.validar_assinatura(b"x", "sha256=abc") is False


def test_validar_assinatura_formato_errado_falso():
    assert whatsapp.validar_assinatura(b"x", "md5=abc", segredo="s") is False
