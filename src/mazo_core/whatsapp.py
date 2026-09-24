"""Abstracao de canais WhatsApp (oficial / embutido / simulado).

Semantica por canal:
- oficial: Meta Cloud API (WHATSAPP_TOKEN + WHATSAPP_PHONE_NUMBER_ID)
- embutido: sidecar WhatsApp Web via SIDECAR_URL (POST /api/sendText)
- simulado: loga no console, sem envio real

Todos os acessos a configuracao passam por `resolver(chave) -> str`
(padrao: os.getenv). O consumidor pode injetar um resolver que misture
cache de painel + ambiente, sem mudar esta camada.
"""
import hashlib
import hmac
import os
from typing import Callable

import requests

Resolver = Callable[[str], str]

GRAPH_API_URL = "https://graph.facebook.com/v23.0"
CANAL_PADRAO = "embutido"
CANAIS_VALIDOS = ("oficial", "embutido", "simulado")


def resolver_padrao(chave: str) -> str:
    return os.getenv(chave, "") or ""


def _env(chave: str, resolver: Resolver | None = None) -> str:
    r = resolver or resolver_padrao
    return r(chave)


def canal_ativo(resolver: Resolver | None = None) -> str:
    r = resolver or resolver_padrao
    canal = (r("WHATSAPP_CANAL") or os.getenv("WHATSAPP_CANAL", "")).strip().lower()
    return canal if canal in CANAIS_VALIDOS else CANAL_PADRAO


def canal_label(resolver: Resolver | None = None) -> str:
    nomes = {
        "oficial": "WhatsApp Business (Meta Cloud API)",
        "embutido": "WhatsApp Web embutido (QR code)",
        "simulado": "Simulado (sem envio real)",
    }
    c = canal_ativo(resolver)
    return nomes.get(c, c)


def configurado(resolver: Resolver | None = None) -> bool:
    canal = canal_ativo(resolver)
    if canal == "simulado":
        return False
    if canal == "embutido":
        return bool(_env("SIDECAR_URL", resolver))
    return bool(_env("WHATSAPP_TOKEN", resolver) and _env("WHATSAPP_PHONE_NUMBER_ID", resolver))


def enviar_texto(telefone: str, texto: str, resolver: Resolver | None = None) -> str | None:
    canal = canal_ativo(resolver)
    if canal == "simulado" or not configurado(resolver):
        print(f"[whatsapp {canal} SIMULADO] para {telefone}: {texto[:80]}...")
        return None
    if canal == "embutido":
        return enviar_embutido(telefone, texto, resolver)
    return _enviar_oficial(telefone, texto, resolver)


def _enviar_oficial(telefone: str, texto: str, resolver: Resolver | None = None) -> str | None:
    try:
        resposta = requests.post(
            f"{GRAPH_API_URL}/{_env('WHATSAPP_PHONE_NUMBER_ID', resolver)}/messages",
            headers={"Authorization": f"Bearer {_env('WHATSAPP_TOKEN', resolver)}"},
            json={
                "messaging_product": "whatsapp",
                "to": telefone,
                "type": "text",
                "text": {"body": texto},
            },
            timeout=15,
        )
        resposta.raise_for_status()
        dados = resposta.json()
    except (requests.RequestException, ValueError) as erro:
        print(f"[whatsapp/oficial] falhou envio para {telefone}: {erro}")
        return None
    mensagens = dados.get("messages") or []
    return mensagens[0].get("id") if mensagens else None


def enviar_embutido(telefone: str, texto: str, resolver: Resolver | None = None) -> str | None:
    """Envia via sidecar (WhatsApp Web embutido).

    A URL deve aceitar POST com {'number': ..., 'text': ...}. No sidecar,
    use a rota /api/sendText que recebe exatamente esse formato.
    """
    url = _env("SIDECAR_URL", resolver).rstrip("/") + "/api/sendText"
    headers = {}
    api_key = _env("SIDECAR_API_KEY", resolver)
    if api_key:
        headers["X-API-Key"] = api_key
    try:
        resposta = requests.post(
            url,
            json={"number": telefone, "text": texto},
            headers=headers,
            timeout=15,
        )
        resposta.raise_for_status()
        return resposta.json().get("messageId")
    except (requests.RequestException, ValueError) as erro:
        print(f"[whatsapp/embutido] falhou envio para {telefone}: {erro}")
        return None


def proxy_embutido(metodo: str, rota: str, resolver: Resolver | None = None, timeout: float = 2.0) -> dict:
    url = _env("SIDECAR_URL", resolver).rstrip("/") + rota
    headers = {}
    api_key = _env("SIDECAR_API_KEY", resolver)
    if api_key:
        headers["X-API-Key"] = api_key
    try:
        resposta = requests.request(metodo, url, headers=headers or None, timeout=timeout)
        if not resposta.ok:
            return {"disponivel": False}
        return resposta.json()
    except requests.RequestException:
        return {"disponivel": False}


def status_embutido(resolver: Resolver | None = None) -> dict:
    return proxy_embutido("GET", "/status", resolver)


def qrcode_embutido(resolver: Resolver | None = None) -> dict:
    return proxy_embutido("GET", "/qrcode", resolver)


def logout_embutido(resolver: Resolver | None = None) -> dict:
    return proxy_embutido("POST", "/logout", resolver)


def validar_assinatura(corpo: bytes, assinatura_header: str | None, segredo: str | None = None) -> bool:
    """Valida assinatura HMAC SHA-256 do webhook da Meta (header X-Hub-Signature-256)."""
    if segredo is None:
        segredo = os.getenv("META_APP_SECRET")
    if not segredo:
        return False
    if not assinatura_header or not assinatura_header.startswith("sha256="):
        return False
    esperado = hmac.new(
        segredo.encode(), corpo, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(assinatura_header.removeprefix("sha256="), esperado)
