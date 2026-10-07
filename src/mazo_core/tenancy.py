"""Multi-tenant basico Mazotech.

Contrato:
- cada linha pertence a um tenant via `TenantMixin.tenant_id` (string 36, nullable p/ migracao)
- resolucao: header `X-Tenant-ID` vence; senao claim do JWT
  (`tenant_id`, `tenant`, `org` ou `organization_id`); senao tenant do usuario
- escopo: toda query filtra por `tenant_id`; sem tenant = erro quando obrigatorio

Sem dependencia nova: sqlalchemy/fastapi sao opcionais (guardados).
"""

TENANT_HEADER = "X-Tenant-ID"

_CLAIMS = ("tenant_id", "tenant", "org", "organization_id")

try:
    from sqlalchemy import String as _SAString
    from sqlalchemy.orm import mapped_column as _mapped_column

    class TenantMixin:
        """Mixin SQLAlchemy: adiciona `tenant_id` indexado e nullable."""

        tenant_id = _mapped_column(_SAString(36), nullable=True, index=True)

except ImportError:  # nucleo puro sem sqlalchemy

    class TenantMixin:  # type: ignore[no-redef]
        """Fallback sem ORM: so o atributo."""

        tenant_id = None


def normalizar_tenant(valor: object) -> str:
    if valor is None:
        return ""
    texto = str(valor).strip()
    return texto


def resolver_tenant(
    header_val: object = None,
    payload: dict | None = None,
    usuario_tenant: object = None,
) -> str:
    """Resolve o tenant corrente. Precedencia: header > JWT > usuario."""
    cab = normalizar_tenant(header_val)
    if cab:
        return cab
    if isinstance(payload, dict):
        for chave in _CLAIMS:
            achado = normalizar_tenant(payload.get(chave))
            if achado:
                return achado
    return normalizar_tenant(usuario_tenant)


def extrair_tenant_token(token: str | None, decodificador=None) -> str:
    """Extrai tenant do JWT sem levantar. Retorna "" se ausente/invalido."""
    if not token:
        return ""
    try:
        dec = decodificador
        if dec is None:
            from mazo_core.auth import decodificar_token as _dec

            dec = _dec
        dados = dec(token)
    except Exception:
        return ""
    if not isinstance(dados, dict):
        return ""
    return resolver_tenant(payload=dados)


def escopo_tenant(tenant_id: object, obrigatorio: bool = True) -> dict:
    """Filtro de escopo p/ queries. Exige tenant quando obrigatorio."""
    tid = normalizar_tenant(tenant_id)
    if not tid and obrigatorio:
        raise ValueError("tenant_id obrigatorio no escopo")
    return {"tenant_id": tid} if tid else {}


def confere_tenant_linha(linha_tenant: object, tenant_id: object) -> bool:
    """True se a linha pertence ao tenant (comparacao normalizada)."""
    return normalizar_tenant(linha_tenant) == normalizar_tenant(tenant_id) and bool(
        normalizar_tenant(tenant_id)
    )


def filtrar_linhas(linhas: list, tenant_id: object, campo: str = "tenant_id") -> list:
    """Filtro puro em memoria (dicts ou objetos). Sem ORM."""
    tid = normalizar_tenant(tenant_id)
    if not tid:
        raise ValueError("tenant_id obrigatorio no escopo")
    saida = []
    for linha in linhas:
        if isinstance(linha, dict):
            dono = linha.get(campo)
        else:
            dono = getattr(linha, campo, None)
        if confere_tenant_linha(dono, tid):
            saida.append(linha)
    return saida


def termo_escopo(modelo, tenant_id: object):
    """Expressao SQLAlchemy `modelo.tenant_id == tid`. Exige sqlalchemy + coluna."""
    tid = normalizar_tenant(tenant_id)
    if not tid:
        raise ValueError("tenant_id obrigatorio no escopo")
    coluna = getattr(modelo, "tenant_id", None)
    if coluna is None:
        raise ValueError(f"{getattr(modelo, '__name__', modelo)} sem tenant_id")
    try:
        return coluna == tid
    except Exception as erro:
        raise ValueError(f"modelo sem suporte a filtro tenant: {erro}") from erro


try:
    from fastapi import Header, HTTPException  # type: ignore

    async def dependencia_tenant(
        x_tenant_id: str | None = Header(default=None, alias=TENANT_HEADER),
    ) -> str:
        """Dependencia FastAPI: exige header X-Tenant-ID. JWT entra via rota."""
        tid = normalizar_tenant(x_tenant_id)
        if not tid:
            raise HTTPException(status_code=400, detail="X-Tenant-ID obrigatorio")
        return tid

    def exigir_escopo_corrente(tenant_rota: object, tenant_usuario: object) -> str:
        """Confere header contra tenant do usuario logado."""
        rota = normalizar_tenant(tenant_rota)
        dono = normalizar_tenant(tenant_usuario)
        if not rota:
            raise HTTPException(status_code=400, detail="X-Tenant-ID obrigatorio")
        if dono and rota != dono:
            raise HTTPException(status_code=403, detail="tenant divergente do usuario")
        return rota

except ImportError:

    def dependencia_tenant(x_tenant_id: str | None = None) -> str:  # type: ignore[no-redef]
        tid = normalizar_tenant(x_tenant_id)
        if not tid:
            raise ValueError("X-Tenant-ID obrigatorio")
        return tid

    def exigir_escopo_corrente(tenant_rota: object, tenant_usuario: object) -> str:  # type: ignore[no-redef]
        rota = normalizar_tenant(tenant_rota)
        dono = normalizar_tenant(tenant_usuario)
        if not rota:
            raise ValueError("X-Tenant-ID obrigatorio")
        if dono and rota != dono:
            raise PermissionError("tenant divergente do usuario")
        return rota
