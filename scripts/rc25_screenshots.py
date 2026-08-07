#!/usr/bin/env python3
"""RC25 BEFORE/AFTER screenshots with mocked API payloads (no DB mutation)."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8770"
ROOT = Path("/workspace")
FRONTEND = ROOT / "frontend"
BEFORE = Path("/opt/cursor/artifacts/rc25-before")
AFTER = Path("/opt/cursor/artifacts/rc25-after")
BEFORE.mkdir(parents=True, exist_ok=True)
AFTER.mkdir(parents=True, exist_ok=True)

DASH = {
    "metricas": {
        "total_dias_perdidos": 128.5,
        "total_horas_perdidas": 1028.0,
        "total_atestados": 46,
        "total_registros": 46,
        "funcionarios_afetados": 31,
        "custo_estimado": 18450.0,
    },
    "evolucao_mensal": [
        {"mes": "2026-01", "total_atestados": 9, "total_dias": 22},
        {"mes": "2026-02", "total_atestados": 11, "total_dias": 28},
        {"mes": "2026-03", "total_atestados": 8, "total_dias": 19},
        {"mes": "2026-04", "total_atestados": 12, "total_dias": 31},
        {"mes": "2026-05", "total_atestados": 6, "total_dias": 14},
    ],
    "top_setores": [
        {"setor": "Produção", "total": 18, "total_dias": 52},
        {"setor": "Logística", "total": 11, "total_dias": 29},
        {"setor": "Administrativo", "total": 7, "total_dias": 18},
        {"setor": "Manutenção", "total": 6, "total_dias": 16},
        {"setor": "Qualidade", "total": 4, "total_dias": 13},
    ],
    "top_cids": [
        {"cid": "J06", "diagnostico": "Infecções vias aéreas", "total": 9},
        {"cid": "M54", "diagnostico": "Dorsalgia", "total": 8},
        {"cid": "A09", "diagnostico": "Gastroenterite", "total": 6},
        {"cid": "F41", "diagnostico": "Ansiedade", "total": 5},
        {"cid": "S93", "diagnostico": "Entorse tornozelo", "total": 4},
    ],
    "top_motivos": [
        {"motivo": "Doença", "total": 28},
        {"motivo": "Consulta", "total": 10},
        {"motivo": "Acidente", "total": 5},
        {"motivo": "Outros", "total": 3},
    ],
    "top_escalas": [
        {"escala": "Turno A", "total": 16},
        {"escala": "Turno B", "total": 12},
        {"escala": "Administrativo", "total": 7},
    ],
    "dias_centro_custo": [
        {"centro_custo": "CC-100", "total_dias": 40},
        {"centro_custo": "CC-200", "total_dias": 33},
        {"centro_custo": "CC-310", "total_dias": 22},
    ],
    "distribuicao_dias": [
        {"faixa": "1 dia", "total": 18},
        {"faixa": "2-3 dias", "total": 14},
        {"faixa": "4-7 dias", "total": 9},
        {"faixa": "8+ dias", "total": 5},
    ],
    "distribuicao_genero": [
        {"genero": "Feminino", "total": 25},
        {"genero": "Masculino", "total": 21},
    ],
    "frequencia_atestados": [
        {"nome": "Ana Souza", "total": 5},
        {"nome": "Bruno Lima", "total": 4},
        {"nome": "Carla Mendes", "total": 3},
        {"nome": "Diego Alves", "total": 3},
        {"nome": "Elena Rocha", "total": 2},
    ],
    "heatmap_setores_meses": {
        "setores": ["Produção", "Logística", "Admin"],
        "meses": ["Jan/26", "Fev/26", "Mar/26", "Abr/26", "Mai/26"],
        "dados": [
            [12, 15, 10, 18, 8],
            [7, 9, 6, 8, 5],
            [3, 4, 3, 5, 1],
        ],
    },
    "produtividade": [
        {"tipo_consulta": "Doença", "total": 28},
        {"tipo_consulta": "Consulta", "total": 10},
        {"tipo_consulta": "Acidente", "total": 5},
    ],
    "top_funcionarios": [
        {"nome": "Ana Souza", "setor": "Produção", "total_dias": 7},
        {"nome": "Bruno Lima", "setor": "Logística", "total_dias": 2},
    ],
}

CLIENTES = [
    {
        "id": 2,
        "nome": "Converplast",
        "nome_fantasia": "Converplast",
        "ativo": True,
        "status": "ativo",
        "situacao": "ativo",
        "total_funcionarios": 180,
        "total_registros": 940,
        "total_uploads": 14,
        "qtd_funcionarios": 180,
        "qtd_registros": 940,
        "ultimo_processamento": "2026-08-05T14:22:00",
    },
    {
        "id": 4,
        "nome": "Roda de Ouro",
        "nome_fantasia": "Roda de Ouro",
        "ativo": True,
        "status": "ativo",
        "situacao": "ativo",
        "total_funcionarios": 95,
        "total_registros": 410,
        "total_uploads": 9,
        "qtd_funcionarios": 95,
        "qtd_registros": 410,
        "ultimo_processamento": "2026-08-04T09:10:00",
    },
]

FUNCIONARIOS = {
    "items": [
        {
            "id": 1,
            "nome": "Ana Souza",
            "setor": "Produção",
            "cargo": "Operadora",
            "status": "ativo",
            "total_atestados": 3,
            "dias_perdidos": 7,
        },
        {
            "id": 2,
            "nome": "Bruno Lima",
            "setor": "Logística",
            "cargo": "Auxiliar",
            "status": "ativo",
            "total_atestados": 1,
            "dias_perdidos": 2,
        },
        {
            "id": 3,
            "nome": "Carla Mendes",
            "setor": "Administrativo",
            "cargo": "Analista",
            "status": "afastado",
            "total_atestados": 5,
            "dias_perdidos": 18,
        },
    ],
    "funcionarios": [
        {
            "id": 1,
            "nome": "Ana Souza",
            "setor": "Produção",
            "cargo": "Operadora",
            "status": "ativo",
            "total_atestados": 3,
            "dias_perdidos": 7,
        },
        {
            "id": 2,
            "nome": "Bruno Lima",
            "setor": "Logística",
            "cargo": "Auxiliar",
            "status": "ativo",
            "total_atestados": 1,
            "dias_perdidos": 2,
        },
        {
            "id": 3,
            "nome": "Carla Mendes",
            "setor": "Administrativo",
            "cargo": "Analista",
            "status": "afastado",
            "total_atestados": 5,
            "dias_perdidos": 18,
        },
    ],
    "total": 3,
}

PROD_EVOL = [
    {"mes": "2026-01", "total": 210},
    {"mes": "2026-02", "total": 240},
    {"mes": "2026-03", "total": 190},
    {"mes": "2026-04", "total": 260},
    {"mes": "2026-05", "total": 128},
]

COMP = {
    "periodo1": {
        "total_dias_perdidos": 69,
        "total_atestados": 28,
        "total_horas_perdidas": 552,
    },
    "periodo2": {
        "total_dias_perdidos": 45,
        "total_atestados": 18,
        "total_horas_perdidas": 360,
    },
}

UPLOADS = [
    {
        "id": 11,
        "filename": "atestados_maio.xlsx",
        "status": "processado",
        "total_registros": 42,
        "mes_referencia": "2026-05",
        "data_upload": "2026-08-05T11:00:00",
    },
    {
        "id": 10,
        "filename": "atestados_abril.xlsx",
        "status": "processado_com_erros",
        "total_registros": 38,
        "mes_referencia": "2026-04",
        "data_upload": "2026-07-28T16:40:00",
    },
]

DADOS_TODOS = [
    {
        "nomecompleto": "Ana Souza",
        "setor": "Produção",
        "dias_atestados": 3,
        "horas_perdi": 24,
    },
    {
        "nomecompleto": "Ana Souza",
        "setor": "Produção",
        "dias_atestados": 4,
        "horas_perdi": 32,
    },
    {
        "nomecompleto": "Bruno Lima",
        "setor": "Logística",
        "dias_atestados": 2,
        "horas_perdi": 16,
    },
    {
        "nomecompleto": "Carla Mendes",
        "setor": "Administrativo",
        "dias_atestados": 5,
        "horas_perdi": 40,
    },
    {
        "nomecompleto": "Carla Mendes",
        "setor": "Administrativo",
        "dias_atestados": 3,
        "horas_perdi": 24,
    },
]

PROD_LIST = [
    {"tipo_consulta": "Doença", "total": 620},
    {"tipo_consulta": "Consulta", "total": 210},
    {"tipo_consulta": "Acidente", "total": 198},
]

ME = {
    "id": 1,
    "nome": "Ede Machado",
    "name": "Ede Machado",
    "email": "ede@biomed.local",
    "perfil": "admin",
    "role": "admin",
    "cliente_id": 2,
    "client_id": 2,
    "cliente_nome": "Converplast",
}


def old_home_html() -> str:
    return subprocess.check_output(
        ["git", "show", "ad8b757:frontend/index.html"], cwd=str(ROOT)
    ).decode("utf-8")


def install_api_mocks(page):
    def fulfill(route, body, status=200):
        route.fulfill(
            status=status,
            content_type="application/json",
            body=json.dumps(body, ensure_ascii=False),
        )

    def handler(route):
        url = route.request.url
        method = route.request.method
        path = url.split("?", 1)[0]
        if "/api/auth/me" in path or path.endswith("/auth/me"):
            return fulfill(route, ME)
        if "/api/clientes" in path and method == "GET":
            return fulfill(route, CLIENTES)
        if "/api/dashboard" in path:
            return fulfill(route, DASH)
        if "/api/dados/todos" in path:
            return fulfill(route, DADOS_TODOS)
        if "/api/funcionarios" in path:
            return fulfill(route, FUNCIONARIOS)
        if "/api/produtividade/evolucao" in path:
            return fulfill(route, PROD_EVOL)
        if "/api/produtividade" in path:
            return fulfill(route, PROD_LIST)
        if "/api/relatorios/comparativo" in path or "/comparativo" in path:
            return fulfill(route, COMP)
        if "/api/uploads" in path or path.rstrip("/").endswith("/upload"):
            return fulfill(route, UPLOADS)
        if "/api/alertas" in path:
            return fulfill(
                route,
                [
                    {
                        "titulo": "Setor Produção acima da média",
                        "mensagem": "Concentração de 40% dos dias perdidos no mês.",
                        "tipo": "alerta",
                    }
                ],
            )
        if "/api/" in path:
            return fulfill(route, {})
        return route.continue_()

    page.route("**/api/**", handler)
    page.add_init_script(
        """
        localStorage.setItem('access_token', 'rc25-demo-token');
        localStorage.setItem('token', 'rc25-demo-token');
        localStorage.setItem('cliente_selecionado', '2');
        localStorage.setItem('cliente_selecionado_nome', 'Converplast');
        localStorage.setItem('client_id', '2');
        localStorage.setItem('cliente_id', '2');
        localStorage.setItem('cliente_nome', 'Converplast');
        localStorage.setItem('user_nome', 'Ede Machado');
        localStorage.setItem('user_name', 'Ede Machado');
        localStorage.setItem('user', JSON.stringify({nome:'Ede Machado', perfil:'admin', cliente_id:2}));
        """
    )


def install_legacy_html_overrides(page):
    """Serve pre-RC25 HTML for pages rebuilt in place (BEFORE set)."""
    mapping = {
        f"{BASE}/": old_home_html(),
        f"{BASE}/funcionarios": (FRONTEND / "funcionarios.html").read_text(encoding="utf-8"),
        f"{BASE}/upload": (FRONTEND / "upload.html").read_text(encoding="utf-8"),
        f"{BASE}/comparativos": (FRONTEND / "comparativos.html").read_text(encoding="utf-8"),
        f"{BASE}/produtividade": (FRONTEND / "produtividade.html").read_text(encoding="utf-8"),
    }

    def html_handler(route):
        url = route.request.url.split("?", 1)[0].rstrip("/") or f"{BASE}/"
        # normalize trailing slash
        key = url if url.endswith("/") or url.count("/") > 3 else url
        for target, html in mapping.items():
            t = target.rstrip("/") or f"{BASE}/"
            u = url.rstrip("/") or f"{BASE}/"
            if u == t:
                return route.fulfill(status=200, content_type="text/html", body=html)
        return route.continue_()

    page.route(f"{BASE}/", html_handler)
    page.route(f"{BASE}/funcionarios", html_handler)
    page.route(f"{BASE}/upload", html_handler)
    page.route(f"{BASE}/comparativos", html_handler)
    page.route(f"{BASE}/produtividade", html_handler)


def shot(page, folder: Path, name: str):
    path = folder / name
    page.screenshot(path=str(path), full_page=True)
    print("saved", path, "bytes", path.stat().st_size)


def capture(page, folder: Path, slug: str, path: str, wait_ms: int = 1400):
    page.goto(f"{BASE}{path}", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(wait_ms)
    shot(page, folder, f"{slug}.png")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True, executable_path="/usr/local/bin/google-chrome"
        )

        # BEFORE
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        install_api_mocks(page)
        install_legacy_html_overrides(page)
        capture(page, BEFORE, "01_dashboard", "/dashboard-legacy", 2000)
        capture(page, BEFORE, "02_empresas", "/clientes-legacy", 1600)
        capture(page, BEFORE, "03_home", "/", 1400)
        capture(page, BEFORE, "04_apresentacao", "/apresentacao-legacy", 1800)
        capture(page, BEFORE, "05_funcionarios", "/funcionarios", 1600)
        capture(page, BEFORE, "06_upload", "/upload", 1400)
        capture(page, BEFORE, "07_comparativos", "/comparativos", 1600)
        capture(page, BEFORE, "08_produtividade", "/produtividade", 1600)
        page.close()
        context.close()

        # AFTER
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        install_api_mocks(page)
        capture(page, AFTER, "01_dashboard", "/dashboard", 2200)
        capture(page, AFTER, "02_empresas", "/clientes", 1800)
        capture(page, AFTER, "03_home", "/", 1600)
        capture(page, AFTER, "04_apresentacao", "/apresentacao", 2200)
        capture(page, AFTER, "05_funcionarios", "/funcionarios", 1600)
        capture(page, AFTER, "06_upload", "/upload", 1400)
        capture(page, AFTER, "07_comparativos", "/comparativos", 1800)
        capture(page, AFTER, "08_produtividade", "/produtividade", 1800)
        page.set_viewport_size({"width": 390, "height": 844})
        capture(page, AFTER, "01_dashboard_mobile", "/dashboard", 1600)
        capture(page, AFTER, "03_home_mobile", "/", 1400)

        browser.close()

    print("BEFORE", sorted(p.name for p in BEFORE.glob("*.png")))
    print("AFTER", sorted(p.name for p in AFTER.glob("*.png")))


if __name__ == "__main__":
    main()
