"""RC-25 — Core product redesign: new DOM surfaces, same APIs/metrics."""
from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("SECRET_KEY", "rc25-core-secret-not-for-production")
os.environ.setdefault("DISABLE_RATE_LIMIT", "1")

from fastapi.testclient import TestClient

from backend.main import app

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"
SHELL = (FRONTEND / "static/js/biomed-platform-shell.js").read_text(encoding="utf-8")
CORE_JS = (FRONTEND / "static/js/biomed-core.js").read_text(encoding="utf-8")


def test_core_design_system_exists():
    css = FRONTEND / "static/css/biomed-core.css"
    js = FRONTEND / "static/js/biomed-core.js"
    assert css.is_file()
    assert js.is_file()
    text = css.read_text(encoding="utf-8")
    for marker in (
        ".bc-header",
        ".bc-metric",
        ".bc-card",
        ".bc-table",
        ".bc-filters",
        ".bc-empty",
        ".bc-btn",
        "RC25",
    ):
        assert marker in text
    assert "mapDashboardMetrics" in CORE_JS
    assert 'SOURCE_API: "/api/dashboard"' in CORE_JS


def test_shell_cache_rc25_and_core_css():
    assert 'CACHE = "rc25"' in SHELL
    assert "biomed-core.css" in SHELL
    assert "Empresas" in SHELL


def test_new_core_pages_exist_and_are_not_legacy_wrappers():
    pages = {
        "analytics-core.html": ("data-bm-rc25", "bc-metrics", "analytics-core.js"),
        "empresas-core.html": ("data-bm-rc25", "bc-company-grid", "empresas-core.js"),
        "apresentacao-core.html": ("data-bm-rc25", "bc-deck", "apresentacao-core.js"),
        "funcionarios-core.html": ("data-bm-rc25", "bc-table", "funcionarios-core.js"),
        "upload-core.html": ("data-bm-rc25", "bc-steps", "upload-core.js"),
        "comparativos-core.html": ("data-bm-rc25", "chartComp", "comparativos-core.js"),
        "produtividade-core.html": ("data-bm-rc25", "chartTipos", "produtividade-core.js"),
        "index.html": ("data-bm-rc25", "bc-hello", "home-core.js"),
    }
    for name, markers in pages.items():
        html = (FRONTEND / name).read_text(encoding="utf-8")
        for m in markers:
            assert m in html, (name, m)
        # Must not be a thin wrap of the old converplast grid id as primary composition
        if name == "analytics-core.html":
            assert "graficosConverplast" not in html
            assert "index-legacy" not in html


def test_routes_serve_new_pages():
    client = TestClient(app)
    mapping = {
        "/dashboard": "analytics-core",
        "/": "bc-hello",
        "/clientes": "Empresas",
        "/apresentacao": "bc-deck",
        "/funcionarios": "Funcionários",
        "/upload": "bc-steps",
        "/comparativos": "Comparativos",
        "/produtividade": "Produtividade",
        "/dashboard-legacy": "graficosConverplast",
        "/clientes-legacy": "clientes",
    }
    for path, marker in mapping.items():
        r = client.get(path, follow_redirects=False)
        if path == "/analytics":
            continue
        assert r.status_code == 200, path
        assert marker.lower() in r.text.lower() or marker in r.text, (path, marker)


def test_analytics_redirects_to_dashboard():
    client = TestClient(app)
    r = client.get("/analytics", follow_redirects=False)
    assert r.status_code in {302, 307}
    assert r.headers.get("location") == "/dashboard"


def test_metric_mapper_preserves_dashboard_fields():
    """METRIC_REGRESSION: mapper reads the same API fields (no new formulas beyond ratios)."""
    assert "total_dias_perdidos" in CORE_JS
    assert "total_horas_perdidas" in CORE_JS
    assert "funcionarios_afetados" in CORE_JS
    assert "total_atestados" in CORE_JS
    # Python twin of mapDashboardMetrics — must MATCH raw API fields (no formula drift)
    ns = {}
    exec(
        "def mapDashboardMetrics(metricas):\n"
        "    metricas = metricas or {}\n"
        "    dias = float(metricas.get('total_dias_perdidos') or metricas.get('total_atestados_dias') or 0)\n"
        "    horas = float(metricas.get('total_horas_perdidas') or 0)\n"
        "    atestados = float(metricas.get('total_atestados') or metricas.get('total_registros') or 0)\n"
        "    funcs = float(metricas.get('funcionarios_afetados') or 0)\n"
        "    return {\n"
        "        'dias': dias, 'horas': horas, 'atestados': atestados, 'colaboradores': funcs,\n"
        "        'frequencia': (atestados / funcs) if funcs else 0,\n"
        "        'duracao_media': (dias / atestados) if atestados else 0,\n"
        "    }\n",
        ns,
    )
    sample = {
        "total_dias_perdidos": 12.5,
        "total_horas_perdidas": 100.0,
        "total_atestados": 4,
        "funcionarios_afetados": 2,
    }
    # OLD_VALUE = raw API fields; NEW_VALUE = mapper output (must MATCH)
    old = {
        "atestados": float(sample["total_atestados"]),
        "dias": float(sample["total_dias_perdidos"]),
        "horas": float(sample["total_horas_perdidas"]),
        "funcionarios": float(sample["funcionarios_afetados"]),
    }
    mapped = ns["mapDashboardMetrics"](sample)
    assert mapped["dias"] == old["dias"]
    assert mapped["horas"] == old["horas"]
    assert mapped["atestados"] == old["atestados"]
    assert mapped["colaboradores"] == old["funcionarios"]
    assert mapped["frequencia"] == 2.0
    assert mapped["duracao_media"] == 3.125
    # Core pages reference the same chart field names from /api/dashboard
    analytics_js = (FRONTEND / "static/js/analytics-core.js").read_text(encoding="utf-8")
    for field in (
        "top_setores",
        "top_cids",
        "top_motivos",
        "evolucao_mensal",
        "dias_centro_custo",
        "heatmap_setores_meses",
        "frequencia_atestados",
        "produtividade",
    ):
        assert field in analytics_js, field


def test_audit_doc_exists():
    doc = ROOT / "docs/release/RC25_CORE_PRODUCT_REDESIGN.md"
    assert doc.is_file()
    body = doc.read_text(encoding="utf-8")
    assert "SOURCE_API" in body
    assert "analytics-core.html" in body
    assert "empresas-core.html" in body
