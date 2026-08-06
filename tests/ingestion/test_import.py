"""Idempotent transactional import tests."""

from __future__ import annotations

import sqlite3

import pytest

from backend.ingestion.exceptions import ConfirmationError, FeatureDisabledError, ReuploadBlockedError
from backend.ingestion.import_service import ImportService
from backend.ingestion.preview_service import PreviewService
from backend.ingestion.schema_sql import apply_epic1_schema
from tests.fixtures.ingestion.builders import csv_standard


@pytest.fixture
def enabled(monkeypatch):
    monkeypatch.setenv("ENABLE_INTELLIGENT_INGESTION", "true")


@pytest.fixture
def db():
    conn = sqlite3.connect(":memory:")
    apply_epic1_schema(conn, db_path=":memory:")
    yield conn
    conn.close()


def _preview(db):
    svc = PreviewService(db)
    return svc, svc.preview(
        data=csv_standard(),
        original_name="a.csv",
        client_id=99,
        competencia="2024-01",
    )


def test_import_requires_flag(monkeypatch, db):
    monkeypatch.setenv("ENABLE_INTELLIGENT_INGESTION", "false")
    with pytest.raises(FeatureDisabledError):
        ImportService(db).import_preview(
            preview_id="x",
            token="t",
            client_id=1,
            competencia="2024-01",
        )


def test_import_requires_confirm(enabled, db):
    svc, summary = _preview(db)
    with pytest.raises(ConfirmationError):
        ImportService(db, svc).import_preview(
            preview_id=summary.preview_id,
            token=summary.confirmation_token,
            client_id=99,
            competencia="2024-01",
        )


def test_import_transaction_success(enabled, db):
    svc, summary = _preview(db)
    svc.confirm_preview(summary.preview_id, token=summary.confirmation_token, client_id=99)
    result = ImportService(db, svc).import_preview(
        preview_id=summary.preview_id,
        token=summary.confirmation_token,
        client_id=99,
        competencia="2024-01",
        expected_content_hash=summary.content_hash_normalized,
    )
    assert result.status == "succeeded"
    assert result.inserted >= 1
    n = db.execute("SELECT COUNT(*) FROM ingestion_canonical_rows").fetchone()[0]
    assert n == result.inserted


def test_import_idempotent(enabled, db):
    svc, summary = _preview(db)
    svc.confirm_preview(summary.preview_id, token=summary.confirmation_token, client_id=99)
    imp = ImportService(db, svc)
    r1 = imp.import_preview(
        preview_id=summary.preview_id,
        token=summary.confirmation_token,
        client_id=99,
        competencia="2024-01",
    )
    # second preview same content
    svc2 = PreviewService(db)
    s2 = svc2.preview(
        data=csv_standard(),
        original_name="renamed.csv",
        client_id=99,
        competencia="2024-01",
    )
    # identical content should block at reupload on second import path —
    # for idempotency test: reuse same preview cannot (token consumed)
    with pytest.raises(ConfirmationError):
        imp.import_preview(
            preview_id=summary.preview_id,
            token=summary.confirmation_token,
            client_id=99,
            competencia="2024-01",
        )
    assert r1.inserted >= 1
    # try confirm+import s2 — may be blocked as identical content
    svc2.confirm_preview(s2.preview_id, token=s2.confirmation_token, client_id=99)
    with pytest.raises(ReuploadBlockedError):
        ImportService(db, svc2).import_preview(
            preview_id=s2.preview_id,
            token=s2.confirmation_token,
            client_id=99,
            competencia="2024-01",
        )


def test_client_change_blocked(enabled, db):
    svc, summary = _preview(db)
    svc.confirm_preview(summary.preview_id, token=summary.confirmation_token, client_id=99)
    with pytest.raises(ConfirmationError):
        ImportService(db, svc).import_preview(
            preview_id=summary.preview_id,
            token=summary.confirmation_token,
            client_id=100,
            competencia="2024-01",
        )


def test_competencia_change_blocked(enabled, db):
    svc, summary = _preview(db)
    svc.confirm_preview(summary.preview_id, token=summary.confirmation_token, client_id=99)
    with pytest.raises(ConfirmationError):
        ImportService(db, svc).import_preview(
            preview_id=summary.preview_id,
            token=summary.confirmation_token,
            client_id=99,
            competencia="2024-02",
        )


def test_bad_token(enabled, db):
    from backend.ingestion.exceptions import PreviewRequiredError

    svc, summary = _preview(db)
    with pytest.raises(PreviewRequiredError):
        svc.confirm_preview(summary.preview_id, token="wrong", client_id=99)


def test_rollback_leaves_no_partial(enabled, db):
    svc, summary = _preview(db)
    svc.confirm_preview(summary.preview_id, token=summary.confirmation_token, client_id=99)

    class ConnProxy:
        def __init__(self, inner):
            self._inner = inner
            self._ins = 0

        def execute(self, sql, parameters=()):
            if "INSERT INTO ingestion_canonical_rows" in str(sql):
                self._ins += 1
                if self._ins >= 2:
                    raise sqlite3.OperationalError("simulated failure")
            return self._inner.execute(sql, parameters)

        def commit(self):
            return self._inner.commit()

        def rollback(self):
            return self._inner.rollback()

        def __getattr__(self, name):
            return getattr(self._inner, name)

    proxy = ConnProxy(db)
    # PreviewService still uses real db for token consume; import uses proxy
    with pytest.raises(sqlite3.OperationalError):
        ImportService(proxy, svc).import_preview(
            preview_id=summary.preview_id,
            token=summary.confirmation_token,
            client_id=99,
            competencia="2024-01",
        )
    n = db.execute("SELECT COUNT(*) FROM ingestion_canonical_rows").fetchone()[0]
    assert n == 0


def test_counts_match(enabled, db):
    svc, summary = _preview(db)
    svc.confirm_preview(summary.preview_id, token=summary.confirmation_token, client_id=99)
    result = ImportService(db, svc).import_preview(
        preview_id=summary.preview_id,
        token=summary.confirmation_token,
        client_id=99,
        competencia="2024-01",
    )
    exec_row = db.execute(
        "SELECT inserted_rows, status FROM ingestion_executions WHERE execution_uuid = ?",
        (result.execution_id,),
    ).fetchone()
    assert exec_row[0] == result.inserted
    assert exec_row[1] == "succeeded"
