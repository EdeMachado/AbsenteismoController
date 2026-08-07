"""
P0 — Bilateral tenant isolation (Converplast ↔ Roda de Ouro).

Proves:
1. Bound users cannot read the other tenant's data (403 or empty of foreign sentinels).
2. Admin querying client_id=2 never receives RODA sentinels in data payloads (and vice-versa).
3. Dashboard / apresentacao / produtividade / uploads / dados / alertas filter by tenant.

Does NOT mutate production. Uses in-memory SQLite only.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["SECRET_KEY"] = "p0-tenant-isolation-secret-not-for-production"
os.environ.setdefault("DISABLE_RATE_LIMIT", "1")
os.environ.setdefault("ENVIRONMENT", "test")

from backend.auth import create_access_token, get_password_hash
from backend.database import Base, get_db
from backend.main import app
from backend.models import Atestado, Client, Produtividade, Upload, User

ROOT = Path(__file__).resolve().parents[2]
CONVERPLAST_ID = 2
RODA_ID = 4
CONVERPLAST_SENTINEL = "CONVERPLAST_SENTINEL"
RODA_SENTINEL = "RODA_DE_OURO_SENTINEL"


def _is_tenant_denied(resp) -> bool:
    """Some handlers wrap HTTPException(403) into 500 — still deny data."""
    if resp.status_code == 403:
        return True
    if resp.status_code == 500:
        text = (resp.text or "").lower()
        return "acesso negado" in text or "403" in text
    return False


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = Session()

    c2 = Client(
        id=CONVERPLAST_ID,
        nome="CONVERPLAST INDUSTRIA SA",
        nome_fantasia="Converplast",
        cnpj="11111111000111",
        situacao="ativo",
    )
    c4 = Client(
        id=RODA_ID,
        nome="RODA DE OURO LTDA",
        nome_fantasia="Roda de Ouro",
        cnpj="22222222000122",
        situacao="ativo",
    )
    session.add_all([c2, c4])
    session.flush()

    session.add_all(
        [
            User(
                username="user_converplast",
                email="conver@example.test",
                password_hash=get_password_hash("pass-conver"),
                nome_completo="User Converplast",
                is_active=True,
                is_admin=False,
                client_id=CONVERPLAST_ID,
            ),
            User(
                username="user_roda",
                email="roda@example.test",
                password_hash=get_password_hash("pass-roda"),
                nome_completo="User Roda",
                is_active=True,
                is_admin=False,
                client_id=RODA_ID,
            ),
            User(
                username="admin_p0",
                email="admin_p0@example.test",
                password_hash=get_password_hash("pass-admin"),
                nome_completo="Admin P0",
                is_active=True,
                is_admin=True,
                client_id=None,
            ),
        ]
    )

    up2 = Upload(
        client_id=CONVERPLAST_ID,
        filename="converplast.xlsx",
        mes_referencia="2026-01",
        total_registros=1,
    )
    up4 = Upload(
        client_id=RODA_ID,
        filename="roda.xlsx",
        mes_referencia="2026-01",
        total_registros=1,
    )
    session.add_all([up2, up4])
    session.flush()

    session.add_all(
        [
            Atestado(
                upload_id=up2.id,
                nomecompleto=CONVERPLAST_SENTINEL,
                nome_funcionario=CONVERPLAST_SENTINEL,
                dias_atestados=3,
                horas_perdi=24,
                cid="Z00",
                diagnostico=f"DX-{CONVERPLAST_SENTINEL}",
                setor=f"SETOR-{CONVERPLAST_SENTINEL}",
                genero="M",
            ),
            Atestado(
                upload_id=up4.id,
                nomecompleto=RODA_SENTINEL,
                nome_funcionario=RODA_SENTINEL,
                dias_atestados=5,
                horas_perdi=40,
                cid="A00",
                diagnostico=f"DX-{RODA_SENTINEL}",
                setor=f"SETOR-{RODA_SENTINEL}",
                genero="F",
            ),
            Produtividade(
                client_id=CONVERPLAST_ID,
                mes_referencia="2026-01",
                numero_tipo="1",
                tipo_consulta=CONVERPLAST_SENTINEL,
                total=11,
            ),
            Produtividade(
                client_id=RODA_ID,
                mes_referencia="2026-01",
                numero_tipo="1",
                tipo_consulta=RODA_SENTINEL,
                total=22,
            ),
        ]
    )
    session.commit()

    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def client(db_session):
    def _override():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _token(username: str) -> str:
    return create_access_token({"sub": username})


def _auth(username: str) -> dict:
    return {"Authorization": f"Bearer {_token(username)}"}


def _dump(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, default=str)


DATA_ENDPOINTS = [
    ("GET", "/api/dashboard", lambda cid: {"client_id": cid}),
    ("GET", "/api/apresentacao", lambda cid: {"client_id": cid}),
    ("GET", "/api/alertas", lambda cid: {"client_id": cid}),
    ("GET", "/api/produtividade", lambda cid: {"client_id": cid}),
    ("GET", "/api/produtividade/evolucao", lambda cid: {"client_id": cid}),
    ("GET", "/api/dados/todos", lambda cid: {"client_id": cid}),
    ("GET", "/api/uploads", lambda cid: {"client_id": cid}),
    ("GET", "/api/relatorios/comparativo", lambda cid: {
        "client_id": cid,
        "periodo1_inicio": "2026-01",
        "periodo1_fim": "2026-01",
        "periodo2_inicio": "2025-12",
        "periodo2_fim": "2025-12",
    }),
]


@pytest.mark.parametrize("method,path,params_fn", DATA_ENDPOINTS)
def test_bound_converplast_cannot_access_roda(client, method, path, params_fn):
    r = client.request(method, path, params=params_fn(RODA_ID), headers=_auth("user_converplast"))
    assert _is_tenant_denied(r), (path, r.status_code, r.text[:300])
    assert RODA_SENTINEL not in (r.text or "")
    assert CONVERPLAST_SENTINEL not in (r.text or "")


@pytest.mark.parametrize("method,path,params_fn", DATA_ENDPOINTS)
def test_bound_roda_cannot_access_converplast(client, method, path, params_fn):
    r = client.request(method, path, params=params_fn(CONVERPLAST_ID), headers=_auth("user_roda"))
    assert _is_tenant_denied(r), (path, r.status_code, r.text[:300])
    assert CONVERPLAST_SENTINEL not in (r.text or "")
    assert RODA_SENTINEL not in (r.text or "")


@pytest.mark.parametrize("method,path,params_fn", DATA_ENDPOINTS)
def test_converplast_payload_has_own_sentinel_not_roda(client, method, path, params_fn):
    r = client.request(
        method, path, params=params_fn(CONVERPLAST_ID), headers=_auth("user_converplast")
    )
    assert r.status_code == 200, (path, r.status_code, r.text[:400])
    body = _dump(r.json())
    own_ok = (
        CONVERPLAST_SENTINEL in body
        or "converplast.xlsx" in body
        or path
        in {
            "/api/alertas",
            "/api/relatorios/comparativo",
            "/api/produtividade/evolucao",
        }
    )
    assert own_ok, (path, "expected Converplast data marker or empty-ok endpoint", body[:500])
    assert RODA_SENTINEL not in body, (path, "RODA sentinel leaked into Converplast response", body[:800])
    assert "roda.xlsx" not in body
    assert f"SETOR-{RODA_SENTINEL}" not in body
    assert f"DX-{RODA_SENTINEL}" not in body


@pytest.mark.parametrize("method,path,params_fn", DATA_ENDPOINTS)
def test_roda_payload_has_own_sentinel_not_converplast(client, method, path, params_fn):
    r = client.request(method, path, params=params_fn(RODA_ID), headers=_auth("user_roda"))
    assert r.status_code == 200, (path, r.status_code, r.text[:400])
    body = _dump(r.json())
    own_ok = (
        RODA_SENTINEL in body
        or "roda.xlsx" in body
        or path
        in {
            "/api/alertas",
            "/api/relatorios/comparativo",
            "/api/produtividade/evolucao",
        }
    )
    assert own_ok, (path, "expected Roda data marker or empty-ok endpoint", body[:500])
    assert CONVERPLAST_SENTINEL not in body, (
        path,
        "CONVERPLAST sentinel leaked into Roda response",
        body[:800],
    )
    assert "converplast.xlsx" not in body


@pytest.mark.parametrize("method,path,params_fn", DATA_ENDPOINTS)
def test_admin_query_converplast_excludes_roda_sentinel(client, method, path, params_fn):
    r = client.request(method, path, params=params_fn(CONVERPLAST_ID), headers=_auth("admin_p0"))
    assert r.status_code == 200, (path, r.status_code, r.text[:400])
    body = _dump(r.json())
    assert RODA_SENTINEL not in body, (path, body[:800])


@pytest.mark.parametrize("method,path,params_fn", DATA_ENDPOINTS)
def test_admin_query_roda_excludes_converplast_sentinel(client, method, path, params_fn):
    r = client.request(method, path, params=params_fn(RODA_ID), headers=_auth("admin_p0"))
    assert r.status_code == 200, (path, r.status_code, r.text[:400])
    body = _dump(r.json())
    assert CONVERPLAST_SENTINEL not in body, (path, body[:800])


def test_dashboard_metrics_match_tenant_sql(client, db_session):
    """KPI totals must match SQL filtered by tenant (contamination check)."""
    from sqlalchemy import func
    from backend.models import Atestado, Upload

    def sql_dias(cid: int) -> float:
        return (
            db_session.query(func.coalesce(func.sum(Atestado.dias_atestados), 0))
            .join(Upload)
            .filter(Upload.client_id == cid)
            .scalar()
        )

    for cid, user in ((CONVERPLAST_ID, "user_converplast"), (RODA_ID, "user_roda")):
        r = client.get("/api/dashboard", params={"client_id": cid}, headers=_auth(user))
        assert r.status_code == 200
        metricas = r.json().get("metricas") or {}
        assert float(metricas.get("total_dias_perdidos") or 0) == float(sql_dias(cid))


def test_auth_me_omits_client_id_for_admin_session_binding(client):
    """Architectural gap: /api/auth/me omits client_id — admin tenant is browser-only."""
    r = client.get("/api/auth/me", headers=_auth("admin_p0"))
    assert r.status_code == 200
    data = r.json()
    assert "client_id" not in data
    assert data.get("is_admin") is True


def test_frontend_dashboard_race_and_converplast_gate_documented():
    """Static proof of UI contamination vectors (no AbortController / deferred hide)."""
    dash = (ROOT / "frontend/static/js/dashboard.js").read_text(encoding="utf-8")
    html = (ROOT / "frontend/index-legacy.html").read_text(encoding="utf-8")
    comp = (ROOT / "frontend/static/js/comparativos.js").read_text(encoding="utf-8")

    assert "async function carregarDashboard" in dash
    assert "AbortController" not in dash
    assert "setTimeout(() => {" in dash
    assert "graficosConverplast" in dash
    assert "converplastClientId === 2" in dash

    assert 'id="graficosConverplast"' in html
    assert "chartCids" in html
    # Main shared charts live inside the Converplast-named container
    idx_conv = html.index('id="graficosConverplast"')
    idx_cids = html.index('id="chartCids"')
    idx_end = html.index("FIM GRÁFICOS CONVERPLAST")
    assert idx_conv < idx_cids < idx_end

    assert "getCurrentClientId(1)" in comp
    assert "|| 1" in comp


def test_clonar_dados_is_admin_only_cross_tenant_write(client):
    """Clone endpoint intentionally copies origem→destino (physical contamination vector)."""
    # Bound user cannot clone
    r = client.post(
        f"/api/clientes/{RODA_ID}/clonar_dados",
        params={"origem_id": CONVERPLAST_ID},
        headers=_auth("user_converplast"),
    )
    assert r.status_code in {403, 401, 404, 400, 422} or r.status_code >= 400

    # Admin can reach handler (may 400 if destino already has data — our fixture has data)
    r2 = client.post(
        f"/api/clientes/{RODA_ID}/clonar_dados",
        params={"origem_id": CONVERPLAST_ID},
        headers=_auth("admin_p0"),
    )
    # Destino already has uploads → 400 by design; proves admin path exists
    assert r2.status_code in {400, 200}, r2.text[:300]
    if r2.status_code == 400:
        assert "destino" in r2.text.lower() or "dados" in r2.text.lower()


def test_tenant_ids_documented_as_converplast_2_roda_4():
    """Confirm ID mapping from authoritative repo evidence (do not invent)."""
    fit07 = (ROOT / "docs/integration/FIT07_FINAL_MERGE_GATE.md").read_text(encoding="utf-8")
    master = (ROOT / "docs/master/ABSENTEISMO_MASTER_ARCHITECTURE_IMPLEMENTATION_PLAN.md").read_text(
        encoding="utf-8"
    )
    assert "Converplast (client_id=2)" in fit07 or "client_id=2" in fit07
    assert "Roda de Ouro (client_id=4)" in fit07 or "client_id=4" in fit07
    assert "CONVERPLAST" in master.upper() and "client_id=2" in master
    assert "RODA" in master.upper() and "client_id=4" in master
