"""FIT-04 — static frontend checks (no browser).

Validates auth.js inclusion/order and that landing does not call
/api/cadastro-empresa. Complements scripts/fit04_browser_validation.py.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def _script_srcs(html_name: str) -> list[str]:
    text = (FRONTEND / html_name).read_text(encoding="utf-8")
    scripts: list[str] = []
    needle = 'src="'
    idx = 0
    while True:
        i = text.find(needle, idx)
        if i < 0:
            break
        j = text.find('"', i + len(needle))
        scripts.append(text[i + len(needle) : j])
        idx = j + 1
    return scripts


def _is_auth_js(src: str) -> bool:
    # allow cache-bust query (?v=4)
    base = src.split("?", 1)[0]
    return base.endswith("/static/js/auth.js") or base.endswith("auth.js")


def _auth_index(scripts: list[str]) -> int:
    for i, s in enumerate(scripts):
        if _is_auth_js(s):
            return i
    raise AssertionError(f"auth.js not found in scripts: {scripts}")


def _auth_before(html_name: str, caller_js: str) -> None:
    scripts = _script_srcs(html_name)
    auth = _auth_index(scripts)
    caller = next(i for i, s in enumerate(scripts) if caller_js in s)
    assert auth < caller, (
        f"{html_name}: auth.js must precede {caller_js} (scripts={scripts})"
    )


# Pages that call authenticated APIs — auth.js must load before app JS.
_API_PAGES_AUTH_BEFORE = [
    ("clientes.html", "clientes.js"),
    ("dados_powerbi.html", "dados_powerbi.js"),
    ("funcionarios.html", "funcionarios.js"),
    ("upload.html", "upload.js"),
    ("produtividade.html", "produtividade.js"),
    ("dashboard_powerbi.html", "dashboard_powerbi.js"),
    ("comparativos.html", "comparativos.js"),
    ("configuracoes.html", "configuracoes.js"),
    ("perfil_funcionario.html", "perfil_funcionario.js"),
    ("apresentacao.html", "apresentacao.js"),
    ("inss.html", "inss.js"),
]


def test_api_pages_include_auth_js_before_app_js():
    for html_name, caller in _API_PAGES_AUTH_BEFORE:
        _auth_before(html_name, caller)


def test_index_loads_auth_js_before_dashboard_js():
    # RC-20: / is BioMed Hub; legacy dashboard lives at index-legacy.html (/dashboard).
    scripts = _script_srcs("index-legacy.html")
    auth = _auth_index(scripts)
    dash = next(i for i, s in enumerate(scripts) if "dashboard.js" in s)
    assert auth < dash, (
        f"index-legacy.html: auth.js must precede dashboard.js (scripts={scripts})"
    )


def test_upload_inteligente_includes_auth_js():
    scripts = _script_srcs("upload_inteligente.html")
    assert any(_is_auth_js(s) for s in scripts), (
        f"upload_inteligente.html must include auth.js (scripts={scripts})"
    )


def test_landing_does_not_call_cadastro_empresa():
    text = (FRONTEND / "landing.html").read_text(encoding="utf-8")
    assert "/api/cadastro-empresa" not in text, (
        "landing.html must not call /api/cadastro-empresa "
        "(endpoint requires auth; public landing must not hit it)"
    )
