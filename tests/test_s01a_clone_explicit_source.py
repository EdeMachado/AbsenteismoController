"""
Testes estáticos/unitários da clonagem explícita (S01-A).
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENTES_JS = (ROOT / "frontend/static/js/clientes.js").read_text(encoding="utf-8")
CLIENTES_HTML = (ROOT / "frontend/clientes.html").read_text(encoding="utf-8")


def test_no_origem_id_one_hardcoded():
    assert "origem_id=1" not in CLIENTES_JS
    assert "origem_id=1" not in CLIENTES_HTML
    # sem fallback numérico literal na montagem da URL
    assert not re.search(r"origem_id\s*=\s*1\b", CLIENTES_JS)


def test_no_numeric_origem_fallback_in_url_builder():
    assert "function montarUrlClonarDados" in CLIENTES_JS
    # URL só com variável origem selecionada
    assert "clonar_dados?origem_id=${origem}" in CLIENTES_JS
    assert "clonar_dados?origem_id=1" not in CLIENTES_JS


def test_origem_destino_cannot_be_equal_in_helper():
    # lógica embutida: destino === origem → return null
    assert "if (destino === origem)" in CLIENTES_JS
    assert "return null" in CLIENTES_JS


def test_api_called_only_after_explicit_selection():
    assert "if (!origemId)" in CLIENTES_JS
    assert "Selecione explicitamente o cliente origem" in CLIENTES_JS
    assert "montarUrlClonarDados(destinoId, origemId)" in CLIENTES_JS
    assert "confirmarClonarDadosSelecionados" in CLIENTES_JS


def test_non_admin_cannot_run_clone_action():
    assert "if (typeof isAdmin === 'function' && !isAdmin())" in CLIENTES_JS
    assert "Apenas administradores podem clonar dados" in CLIENTES_JS
    assert "btn-clonar-dados" in CLIENTES_JS
    assert "isAdmin()" in CLIENTES_JS


def test_confirmation_shows_origem_and_destino_names():
    assert 'Origem: ${origemNome}' in CLIENTES_JS
    assert 'Destino: ${destinoNome}' in CLIENTES_JS
    assert "clonarDestinoNome" in CLIENTES_HTML
    assert "clonarConfirmacaoTexto" in CLIENTES_HTML
    assert 'Confirmar clonagem de dados de "' in CLIENTES_JS


def test_modal_has_empty_default_option():
    assert 'Selecione o cliente origem…' in CLIENTES_HTML
    assert 'value="">' in CLIENTES_HTML or "value=\"\">" in CLIENTES_HTML


def test_listar_origens_excludes_destino():
    assert "listarClientesOrigemParaClone" in CLIENTES_JS
    assert "Number(c.id) !== destino" in CLIENTES_JS
