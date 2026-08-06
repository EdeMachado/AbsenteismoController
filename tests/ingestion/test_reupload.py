"""Reupload classification tests."""

from __future__ import annotations

import sqlite3

import pytest

from backend.ingestion.reupload_detection_service import ReuploadDetectionService
from backend.ingestion.schema_sql import apply_epic1_schema
from backend.ingestion.schemas import ReuploadClass


@pytest.fixture
def db():
    conn = sqlite3.connect(":memory:")
    apply_epic1_schema(conn, db_path=":memory:")
    yield conn
    conn.close()


def test_novo_arquivo():
    r = ReuploadDetectionService().assess(
        client_id=1,
        competencia="2024-01",
        sha256_raw="aaa",
        content_hash_normalized="bbb",
        structural_signature="ccc",
        line_fingerprints=["f1", "f2"],
    )
    assert r.classification == ReuploadClass.NOVO_ARQUIVO
    assert r.blocks_auto_import is False


def test_raw_identical():
    r = ReuploadDetectionService().assess(
        client_id=1,
        competencia="2024-01",
        sha256_raw="aaa",
        content_hash_normalized="bbb",
        structural_signature="ccc",
        line_fingerprints=["f1"],
        known_raw_hashes={"aaa"},
    )
    assert r.classification == ReuploadClass.ARQUIVO_BRUTO_IDENTICO
    assert r.blocks_auto_import is True


def test_normalized_identical_renamed():
    r = ReuploadDetectionService().assess(
        client_id=1,
        competencia="2024-01",
        sha256_raw="different",
        content_hash_normalized="samecontent",
        structural_signature="ccc",
        line_fingerprints=["f1"],
        known_content_hashes={"samecontent"},
    )
    assert r.classification == ReuploadClass.CONTEUDO_NORMALIZADO_IDENTICO
    assert r.blocks_auto_import is True


def test_same_competencia_diff_content():
    r = ReuploadDetectionService().assess(
        client_id=1,
        competencia="2024-01",
        sha256_raw="n1",
        content_hash_normalized="n2",
        structural_signature="s",
        line_fingerprints=["a", "b", "c"],
        previous_fingerprints={"a", "x"},
        previous_execution_id="prev1",
    )
    assert r.classification == ReuploadClass.MESMA_COMPETENCIA_CONTEUDO_DIFERENTE
    assert r.aggregate_diff["linhas_novas"] >= 1
    assert r.aggregate_diff["linhas_ausentes"] >= 1
    # no line content exposed
    assert "conteudo" not in r.aggregate_diff


def test_possivel_complementar():
    r = ReuploadDetectionService().assess(
        client_id=1,
        competencia="2024-01",
        sha256_raw="n1",
        content_hash_normalized="n2",
        structural_signature="s",
        line_fingerprints=["a", "b", "c", "d"],
        previous_fingerprints={"a", "b", "c"},
    )
    assert r.classification == ReuploadClass.POSSIVEL_COMPLEMENTAR
    assert r.requires_admin_justification is True


def test_layout_alterado(db):
    db.execute(
        """
        INSERT INTO ingestion_mapping_profiles (
            client_id, name, version, structural_signature, mapping_json,
            sheet_name, header_row, active, created_at, created_by,
            replaces_version, status, observation
        ) VALUES (1, 'p', 1, 'old_sig', '{}', 'A', 0, 1, 't', 'u', NULL, 'active', NULL)
        """
    )
    db.commit()
    r = ReuploadDetectionService(db).assess(
        client_id=1,
        competencia="2024-01",
        sha256_raw="n1",
        content_hash_normalized="n2",
        structural_signature="brand_new_sig",
        line_fingerprints=["a"],
    )
    assert r.classification == ReuploadClass.LAYOUT_ALTERADO
