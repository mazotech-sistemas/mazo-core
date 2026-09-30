"""Branding whitelabel: nome, logo, cores, templates por cliente."""
import json
import os
import re
from pathlib import Path

DEFAULT = {
    "nome_fantasia": "Mazotech",
    "razao": "Mazotech",
    "logo_path": "",
    "cor_primaria": "#1f6feb",
    "cor_secundaria": "#0e1a2b",
    "whatsapp_numero": "",
    "msg_templates": {
        "retorno": "Ola {nome}, seu retorno venceu. Responda SIM para reagendar.",
        "cobranca": "Ola {nome}, fatura {ref} de R${valor} vence {venc}. Pix: {pix}",
        "avaliacao": "Obrigado {nome}. Avalie aqui: {link}",
    },
}

_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
_cache = dict(DEFAULT)

def _valida_cor(v, fallback):
    return v if isinstance(v, str) and _HEX.match(v.strip()) else fallback

def load(path=None, obj=None, resolver=None):
    global _cache
    r = resolver or os.getenv
    base = dict(DEFAULT)
    base["msg_templates"] = dict(DEFAULT["msg_templates"])
    data = {}
    if obj is not None:
        data = obj
    else:
        p = path or r("BRAND_PATH", "") or "config/brand.json"
        try:
            if p and Path(p).exists():
                data = json.loads(Path(p).read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[branding] json invalido em {p}: {e}, usando default")
            data = {}
    if isinstance(data, dict):
        for k in ("nome_fantasia", "razao", "logo_path", "whatsapp_numero"):
            if data.get(k):
                base[k] = str(data[k])
        if data.get("cor_primaria"):
            base["cor_primaria"] = _valida_cor(data["cor_primaria"], DEFAULT["cor_primaria"])
        if data.get("cor_secundaria"):
            base["cor_secundaria"] = _valida_cor(data["cor_secundaria"], DEFAULT["cor_secundaria"])
        mt = data.get("msg_templates")
        if isinstance(mt, dict):
            for k, v in mt.items():
                if isinstance(v, str) and v.strip():
                    base["msg_templates"][k] = v
    nome_env = r("BRAND_NOME", "")
    if nome_env:
        base["nome_fantasia"] = nome_env
    cor_env = r("BRAND_COR", "")
    if cor_env:
        base["cor_primaria"] = _valida_cor(cor_env, base["cor_primaria"])
    logo_env = r("BRAND_LOGO", "")
    if logo_env:
        base["logo_path"] = logo_env
    _cache = base
    return dict(_cache)

def get():
    return dict(_cache)

def css_vars():
    b = _cache
    return f":root{{--brand:{b['cor_primaria']};--brand2:{b['cor_secundaria']};}}"

def logo_url():
    p = _cache.get("logo_path", "")
    if p and Path(str(p)).exists():
        return "/brand/logo"
    return "/static/logo-default.svg"

def mensagem(chave, **vars):
    tpl = _cache.get("msg_templates", {}).get(chave, "")
    if not tpl:
        return f"{_cache['nome_fantasia']}: {_cache['nome_fantasia']}"
    try:
        return tpl.format(**vars)
    except KeyError:
        return tpl
