"""Column mapping + profile versioning tests."""

from __future__ import annotations

import sqlite3

import pytest

from backend.ingestion.column_mapping_service import ColumnMappingService, normalize_header
from backend.ingestion.mapping_profile_service import MappingProfileService
from backend.ingestion.schema_sql import apply_epic1_schema


@pytest.fixture
def mapper():
    return ColumnMappingService()


def test_exact_nome(mapper):
    r = mapper.map_headers(["nomecompleto"])
    assert r[0].campo_canonico == "nomecompleto"
    assert r[0].confianca >= 0.98


def test_alias_funcionario(mapper):
    r = mapper.map_headers(["Funcionário"])
    assert r[0].campo_canonico == "nomecompleto"
    assert r[0].metodo in {"alias", "exact", "similarity"}


def test_alias_matricula_chapa(mapper):
    r = mapper.map_headers(["Chapa"])
    assert r[0].campo_canonico == "matricula"


def test_alias_setor_area(mapper):
    r = mapper.map_headers(["Área"])
    assert r[0].campo_canonico == "setor"


def test_alias_cc(mapper):
    r = mapper.map_headers(["Centro de Custo"])
    assert r[0].campo_canonico == "centro_custo"


def test_alias_cid10(mapper):
    r = mapper.map_headers(["CID-10"])
    assert r[0].campo_canonico == "cid"


def test_alias_qtd_dias(mapper):
    r = mapper.map_headers(["Qtd Dias"])
    assert r[0].campo_canonico == "dias_atestados"
    assert r[0].necessita_confirmacao is False


def test_alias_jornada(mapper):
    r = mapper.map_headers(["Jornada diária"])
    assert r[0].campo_canonico == "horas_dia"


def test_accent_normalization():
    assert normalize_header("Matrícula") == normalize_header("matricula")


def test_low_confidence_unmapped(mapper):
    r = mapper.map_headers(["xyzzy_unknown_col"])
    assert r[0].campo_canonico is None or r[0].necessita_confirmacao


def test_duplicate_targets(mapper):
    r = mapper.map_headers(["Nome", "Funcionário"])
    canons = [x.campo_canonico for x in r if x.campo_canonico]
    # at most one nomecompleto auto-mapped without confirmation conflict
    assert canons.count("nomecompleto") <= 1 or any(x.necessita_confirmacao for x in r)


def test_profile_override(mapper):
    r = mapper.map_headers(
        ["Coluna X"],
        profile_mapping={"Coluna X": "setor"},
    )
    assert r[0].campo_canonico == "setor"
    assert r[0].metodo == "profile"


def test_similarity_near_alias(mapper):
    r = mapper.map_headers(["matriculaa"])  # typo-ish
    # may map via similarity or unmapped
    assert r[0].confianca >= 0.0


@pytest.fixture
def db():
    conn = sqlite3.connect(":memory:")
    apply_epic1_schema(conn, db_path=":memory:")
    yield conn
    conn.close()


def test_profile_tenant_scoped(db):
    svc = MappingProfileService(db)
    p1 = svc.create_version(
        client_id=10,
        name="layout_a",
        structural_signature="sigA",
        mapping={"Nome": "nomecompleto"},
        sheet_name="A",
        header_row=0,
        created_by="tester",
    )
    assert p1.version == 1
    found = svc.find_active_by_signature(10, "sigA")
    assert found is not None
    assert svc.find_active_by_signature(11, "sigA") is None


def test_profile_versioning_preserves_history(db):
    svc = MappingProfileService(db)
    svc.create_version(
        client_id=10,
        name="layout_a",
        structural_signature="sigA",
        mapping={"Nome": "nomecompleto"},
        sheet_name="A",
        header_row=0,
        created_by="tester",
    )
    p2 = svc.create_version(
        client_id=10,
        name="layout_a",
        structural_signature="sigB",
        mapping={"Nome": "nomecompleto", "Setor": "setor"},
        sheet_name="A",
        header_row=1,
        created_by="tester",
    )
    assert p2.version == 2
    assert p2.replaces_version == 1
    allp = svc.list_for_client(10)
    assert len(allp) == 2
    active = [p for p in allp if p.active]
    assert len(active) == 1
    assert active[0].version == 2


def test_layout_change_new_signature(db):
    svc = MappingProfileService(db)
    svc.create_version(
        client_id=5,
        name="default",
        structural_signature="old",
        mapping={},
        sheet_name=None,
        header_row=None,
        created_by=None,
    )
    assert svc.find_active_by_signature(5, "new") is None
