"""Preview (no-write) + IQB adapter + PII masking tests."""

from __future__ import annotations

import os
import sqlite3

import pytest

from backend.ingestion.exceptions import FeatureDisabledError
from backend.ingestion.iqb_adapter import IngestionIQBAdapter
from backend.ingestion.pii_mask import assert_no_raw_cpf, mask_row
from backend.ingestion.preview_service import PreviewService
from backend.ingestion.schema_sql import apply_epic1_schema
from tests.fixtures.ingestion.builders import csv_standard, csv_with_title_rows, xlsx_bytes


@pytest.fixture
def enabled(monkeypatch):
    monkeypatch.setenv("ENABLE_INTELLIGENT_INGESTION", "true")


@pytest.fixture
def disabled(monkeypatch):
    monkeypatch.setenv("ENABLE_INTELLIGENT_INGESTION", "false")


@pytest.fixture
def db():
    conn = sqlite3.connect(":memory:")
    apply_epic1_schema(conn, db_path=":memory:")
    yield conn
    conn.close()


def test_feature_flag_blocks_preview(disabled):
    svc = PreviewService(require_flag=True)
    with pytest.raises(FeatureDisabledError):
        svc.preview(
            data=csv_standard(),
            original_name="a.csv",
            client_id=99,
            competencia="2024-01",
        )


def test_preview_no_legacy_write(enabled, db):
    # Ensure only epic1 tables exist — no atestados table
    tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    assert "atestados" not in tables
    svc = PreviewService(db)
    summary = svc.preview(
        data=csv_standard(),
        original_name="a.csv",
        client_id=99,
        competencia="2024-01",
    )
    assert summary.total_rows >= 3
    assert summary.confirmation_token
    assert summary.iqb is not None
    assert summary.iqb.get("advisory_only") is True
    # still no atestados
    tables2 = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    assert "atestados" not in tables2


def test_preview_masks_sample(enabled):
    svc = PreviewService(require_flag=True)
    # inject cpf column via custom csv
    from tests.fixtures.ingestion.builders import make_csv_bytes

    data = make_csv_bytes(
        [
            ["Nome Completo", "CPF", "Data Afastamento", "Dias"],
            ["Ana Teste", "529.982.247-25", "2024-01-10", "2"],
        ]
    )
    summary = svc.preview(
        data=data,
        original_name="c.csv",
        client_id=99,
        competencia="2024-01",
    )
    public = summary.to_public_dict()
    assert_no_raw_cpf(public["sample_masked"])
    blob = str(public["sample_masked"])
    assert "529.982.247-25" not in blob


def test_preview_xlsx(enabled):
    svc = PreviewService(require_flag=True)
    summary = svc.preview(
        data=xlsx_bytes(),
        original_name="a.xlsx",
        client_id=99,
        competencia="2024-01",
    )
    assert summary.aba
    assert summary.mapping


def test_preview_title_rows(enabled):
    svc = PreviewService(require_flag=True)
    summary = svc.preview(
        data=csv_with_title_rows(),
        original_name="t.csv",
        client_id=99,
        competencia="2024-01",
    )
    assert summary.header_row is not None
    assert summary.header_row >= 2


def test_iqb_adapter_empty():
    out = IngestionIQBAdapter().evaluate(
        client_id=99, competencia="2024-01", normalized_rows=[]
    )
    assert out["iqb"] == 0.0
    assert out["does_not_gate_import_alone"] is True


def test_iqb_adapter_with_rows():
    rows = [
        {
            "nomecompleto": {"normalized": "Ana"},
            "matricula": {"normalized": "T1"},
            "setor": {"normalized": "Prod"},
            "centro_custo": {"normalized": "CC1"},
            "cid": {"normalized": "J00"},
            "data_afastamento": {"normalized": "2024-01-10"},
            "dias_atestados": {"normalized": 2},
            "horas_dia": {"normalized": 8},
            "mes_referencia": {"normalized": "2024-01"},
        }
    ]
    out = IngestionIQBAdapter().evaluate(
        client_id=99, competencia="2024-01", normalized_rows=rows
    )
    assert out["iqb"] is not None
    assert "dimensoes" in out
    assert "pesos" in out
    assert out["classificacao"]


def test_mask_row_matricula():
    masked = mask_row({"matricula": "T1001", "setor": "X"})
    assert masked["matricula"] != "T1001"
    assert masked["setor"] == "X"


def test_get_preview_hides_token(enabled):
    svc = PreviewService(require_flag=True)
    summary = svc.preview(
        data=csv_standard(),
        original_name="a.csv",
        client_id=99,
        competencia="2024-01",
    )
    got = svc.get_preview(summary.preview_id)
    assert "confirmation_token" not in got
