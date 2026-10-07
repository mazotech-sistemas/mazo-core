"""Testes do mazo_core.tenancy: mixin, resolucao e escopo."""

from mazo_core import tenancy


def test_mixin_tem_tenant_id():
    assert hasattr(tenancy.TenantMixin, "tenant_id")


def test_resolver_header_vence_jwt_e_usuario():
    out = tenancy.resolver_tenant(
        header_val="  t-header ",
        payload={"tenant_id": "t-jwt", "org": "t-org"},
        usuario_tenant="t-user",
    )
    assert out == "t-header"


def test_resolver_jwt_antes_de_usuario():
    assert tenancy.resolver_tenant(payload={"org": "t-org"}, usuario_tenant="t-user") == "t-org"
    assert tenancy.resolver_tenant(payload={}, usuario_tenant="t-user") == "t-user"
    assert tenancy.resolver_tenant() == ""


def test_resolver_claims_alternativos():
    for claim in ("tenant_id", "tenant", "org", "organization_id"):
        assert tenancy.resolver_tenant(payload={claim: "t1"}) == "t1"


def test_extrair_token_invalido_nao_levanta():
    assert tenancy.extrair_tenant_token(None) == ""
    assert tenancy.extrair_tenant_token("invalido") == ""
    assert tenancy.extrair_tenant_token("x", decodificador=lambda t: None) == ""
    assert (
        tenancy.extrair_tenant_token("x", decodificador=lambda t: {"org": "t-ok"}) == "t-ok"
    )


def test_escopo_exige_tenant():
    import pytest

    with pytest.raises(ValueError):
        tenancy.escopo_tenant("", obrigatorio=True)
    assert tenancy.escopo_tenant("", obrigatorio=False) == {}
    assert tenancy.escopo_tenant("t1") == {"tenant_id": "t1"}


def test_filtrar_linhas_isola_tenants():
    linhas = [
        {"id": 1, "tenant_id": "a"},
        {"id": 2, "tenant_id": "b"},
        {"id": 3, "tenant_id": "a"},
    ]
    so_a = tenancy.filtrar_linhas(linhas, "a")
    assert [l["id"] for l in so_a] == [1, 3]
    assert all(l["tenant_id"] == "a" for l in so_a)


def test_confere_tenant_linha():
    assert tenancy.confere_tenant_linha("a", "a") is True
    assert tenancy.confere_tenant_linha("a", "b") is False
    assert tenancy.confere_tenant_linha("", "") is False


def test_dependencia_sem_header_falha():
    import pytest

    try:
        from fastapi import HTTPException
    except ImportError:
        with pytest.raises(ValueError):
            tenancy.dependencia_tenant(None)
    else:
        import asyncio

        with pytest.raises(HTTPException):
            asyncio.run(tenancy.dependencia_tenant(None))
