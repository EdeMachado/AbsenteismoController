from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SHELL = ROOT / "frontend" / "static" / "js" / "biomed-platform-shell.js"


def _source() -> str:
    return SHELL.read_text(encoding="utf-8")


def test_tenant_guard_is_installed_once():
    src = _source()
    assert "__bmTenantIsolationInstalled" in src
    assert "installTenantIsolationGuard" in src


def test_requests_with_client_id_must_match_active_tenant():
    src = _source()
    assert 'url.searchParams.get("client_id")' in src
    assert "requestTenant !== activeTenantAtStart" in src
    assert "Tenant context mismatch" in src


def test_stale_tenant_response_is_discarded_after_switch():
    src = _source()
    assert "tenantEpoch !== epochAtStart" in src
    assert "activeTenantNow !== activeTenantAtStart" in src
    assert "activeTenantNow !== requestTenant" in src
    assert "Stale tenant response discarded" in src


def test_tenant_change_clears_dashboard_state_when_available():
    src = _source()
    assert 'CustomEvent("biomed:tenant-changed"' in src
    assert "limparTodosDadosDashboard" in src


def test_shared_dashboard_charts_are_not_hidden_for_roda_de_ouro():
    src = _source()
    assert '#graficosConverplast{display:block!important;}' in src
    assert 'link("/dashboard#chartSetores", "Setores"' in src


def test_logout_clears_tenant_context():
    src = _source()
    assert 'localStorage.removeItem("cliente_selecionado")' in src
    assert 'localStorage.removeItem("cliente_selecionado_nome")' in src
