"""
Evidência estática S01-A: páginas dos 9 endpoints carregam auth.js antes dos callers.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def _script_order(html_name: str):
    text = (FRONTEND / html_name).read_text(encoding="utf-8")
    scripts = []
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


def _auth_before(html_name: str, caller_js: str):
    scripts = _script_order(html_name)
    auth = next(i for i, s in enumerate(scripts) if s.endswith("/static/js/auth.js") or s.endswith("auth.js"))
    caller = next(i for i, s in enumerate(scripts) if caller_js in s)
    assert auth < caller, f"{html_name}: auth.js deve preceder {caller_js} ({scripts})"


def test_upload_page_loads_auth_before_upload_js():
    _auth_before("upload.html", "upload.js")


def test_produtividade_page_loads_auth_before_js():
    _auth_before("produtividade.html", "produtividade.js")


def test_dados_powerbi_loads_auth_before_js():
    _auth_before("dados_powerbi.html", "dados_powerbi.js")


def test_clientes_page_loads_auth_before_js():
    _auth_before("clientes.html", "clientes.js")


def test_dashboard_powerbi_loads_auth_before_js():
    _auth_before("dashboard_powerbi.html", "dashboard_powerbi.js")


def test_clonar_dados_requires_explicit_origem_query():
    text = (FRONTEND / "static/js/clientes.js").read_text(encoding="utf-8")
    assert "origem_id=1" not in text
    assert "clonar_dados?origem_id=${origem}" in text
    assert "montarUrlClonarDados" in text
    assert "listarClientesOrigemParaClone" in text


def test_auth_js_intercepts_window_fetch():
    text = (FRONTEND / "static/js/auth.js").read_text(encoding="utf-8")
    assert "window.fetch" in text
    assert "Authorization" in text
    assert "Bearer" in text
