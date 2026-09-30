import os
from pathlib import Path
import tempfile
import json

def test_default_sem_arquivo():
    import importlib
    import mazo_core.branding as b
    importlib.reload(b)
    os.environ.pop("BRAND_PATH", None)
    os.environ.pop("BRAND_NOME", None)
    d = b.load(path="/tmp/inexistente-xyz.json")
    assert d["nome_fantasia"] == "Mazotech"
    assert d["cor_primaria"] == "#1f6feb"

def test_env_sobrepoe_json():
    import mazo_core.branding as b
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump({"nome_fantasia": "Clinica X", "cor_primaria": "#ff0000"}, f)
        p = f.name
    os.environ["BRAND_NOME"] = "Clinica Y"
    d = b.load(path=p)
    assert d["nome_fantasia"] == "Clinica Y"
    Path(p).unlink()
    del os.environ["BRAND_NOME"]

def test_cor_invalida_cai_default():
    import mazo_core.branding as b
    d = b.load(obj={"cor_primaria": "azul"})
    assert d["cor_primaria"] == "#1f6feb"

def test_json_invalido_usa_default(capsys):
    import mazo_core.branding as b
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        f.write("{invalido")
        p = f.name
    d = b.load(path=p)
    assert d["nome_fantasia"] == "Mazotech"
    Path(p).unlink()

def test_mensagem_com_fallback():
    import mazo_core.branding as b
    d = b.load(obj={"msg_templates": {"retorno": "Oi {nome}, retorno venceu"}})
    b._cache = d
    assert b.mensagem("retorno", nome="Ana") == "Oi Ana, retorno venceu"
    assert b.mensagem("chave_ausente") != ""

def test_logo_ausente_sem_404():
    import mazo_core.branding as b
    b.load(obj={"logo_path": "/tmp/logo-que-nao-existe.png"})
    assert b.logo_url() == "/static/logo-default.svg"
    assert "brand" in b.css_vars()
