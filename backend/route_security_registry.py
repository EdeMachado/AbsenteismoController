"""Runtime route classification registry (FIT-04).

Every registered /api/* route must appear here with a security class.
Tests fail if an unclassified API route appears.
"""

from __future__ import annotations

from typing import Dict, FrozenSet, Tuple

# (METHOD, path) → class id matching FIT-03 matrix
# path patterns use FastAPI path templates as registered.

PUBLIC_INTENTIONAL: FrozenSet[Tuple[str, str]] = frozenset(
    {
        ("POST", "/api/auth/login"),
        ("GET", "/api/health"),
    }
)

# All other /api routes are authenticated (classes 2–4). Experimental routes
# must not be registered when flags are OFF.

KNOWN_API_PATHS: FrozenSet[str] = frozenset(
    {
        "/api/alertas",
        "/api/analises/cids",
        "/api/analises/funcionarios",
        "/api/analises/setores",
        "/api/apresentacao",
        "/api/auth/login",
        "/api/auth/logout",
        "/api/auth/me",
        "/api/backup/create",
        "/api/backup/list",
        "/api/buscar-cnpj/{cnpj}",
        "/api/cadastro-empresa",
        "/api/clientes",
        "/api/clientes/{client_id}/campos-disponiveis",
        "/api/clientes/{client_id}/column-mapping",
        "/api/clientes/{client_id}/column-mapping/preview",
        "/api/clientes/{client_id}/graficos",
        "/api/clientes/{client_id}/graficos/gerar-dados",
        "/api/clientes/{cliente_id}",
        "/api/clientes/{cliente_id}/arquivar",
        "/api/clientes/{cliente_id}/ativar",
        "/api/clientes/{cliente_id}/clonar_dados",
        "/api/clientes/{cliente_id}/cores",
        "/api/clientes/{cliente_id}/logo",
        "/api/clientes/{cliente_id}/logos",
        "/api/clientes/{cliente_id}/logos/{logo_id}",
        "/api/clientes/{cliente_id}/logos/{logo_id}/principal",
        "/api/config",
        "/api/config/{chave}",
        "/api/dados",
        "/api/dados/todos",
        "/api/dados/{atestado_id}",
        "/api/dashboard",
        "/api/executive/action-plan",
        "/api/executive/command-center",
        "/api/executive/health",
        "/api/executive/intelligence",
        "/api/executive/meta",
        "/api/executive/performance",
        "/api/export/excel",
        "/api/export/pptx",
        "/api/filtros",
        "/api/filtros-salvos",
        "/api/filtros-salvos/{filtro_id}",
        "/api/filtros-salvos/{filtro_id}/aplicar",
        "/api/funcionario/atualizar",
        "/api/funcionario/perfil",
        "/api/funcionarios/atualizar-massa",
        "/api/health",
        "/api/health/integrity",
        "/api/notifications",
        "/api/notifications/{notification_id}/read",
        "/api/preview/{upload_id}",
        "/api/produtividade",
        "/api/produtividade/evolucao",
        "/api/produtividade/{produtividade_id}",
        "/api/relatorios/comparativo",
        "/api/tendencias",
        "/api/upload",
        "/api/upload/analyze",
        "/api/upload/process",
        "/api/uploads",
        "/api/uploads/{upload_id}",
        "/api/users",
        "/api/users/atualizar-permissoes",
        "/api/users/{user_id}",
        "/api/users/{user_id}/desativar",
    }
)


def classify_api_route(method: str, path: str) -> str:
    key = (method.upper(), path)
    if key in PUBLIC_INTENTIONAL:
        return "1_public_intentional"
    if path in KNOWN_API_PATHS:
        return "authenticated_classified"
    return "UNCLASSIFIED"


def inventory_unclassified(app) -> list[Dict[str, str]]:
    from fastapi.routing import APIRoute

    bad = []
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        if not route.path.startswith("/api"):
            continue
        methods = sorted(m for m in (route.methods or []) if m not in {"HEAD", "OPTIONS"})
        for method in methods:
            cls = classify_api_route(method, route.path)
            if cls == "UNCLASSIFIED":
                bad.append(
                    {
                        "method": method,
                        "path": route.path,
                        "endpoint": route.endpoint.__name__,
                    }
                )
    return bad
