"""Epic 1 — RAW file service & sanitization tests."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from backend.ingestion.exceptions import (
    EmptyFileError,
    FileTooLargeError,
    PathTraversalError,
    UnsupportedFormatError,
)
from backend.ingestion.limits import MAX_FILE_BYTES
from backend.ingestion.raw_file_service import (
    LocalTempStorage,
    MemoryStorage,
    RawFileService,
    sanitize_filename,
    sha256_bytes,
)
from tests.fixtures.ingestion.builders import csv_standard


@pytest.fixture
def raw_svc():
    return RawFileService(MemoryStorage())


def test_raw_hash_is_sha256_of_bytes(raw_svc):
    data = csv_standard()
    meta = raw_svc.ingest_bytes(
        data=data, original_name="ok.csv", client_id=99, competencia="2024-01"
    )
    assert meta.sha256_raw == sha256_bytes(data)
    assert meta.size_bytes == len(data)
    assert meta.extension == ".csv"
    assert meta.pipeline_version


def test_raw_rejects_empty(raw_svc):
    with pytest.raises(EmptyFileError):
        raw_svc.ingest_bytes(data=b"", original_name="x.csv", client_id=1, competencia="2024-01")


def test_raw_rejects_too_large(raw_svc):
    with pytest.raises(FileTooLargeError):
        raw_svc.ingest_bytes(
            data=b"a" * (MAX_FILE_BYTES + 1),
            original_name="big.csv",
            client_id=1,
            competencia="2024-01",
        )


def test_raw_rejects_xls(raw_svc):
    with pytest.raises(UnsupportedFormatError):
        raw_svc.ingest_bytes(data=b"fake", original_name="legacy.xls", client_id=1, competencia="2024-01")


def test_raw_rejects_exe(raw_svc):
    with pytest.raises(UnsupportedFormatError):
        raw_svc.ingest_bytes(data=b"MZ", original_name="evil.exe", client_id=1, competencia="2024-01")


def test_path_traversal_filename_stripped_to_basename():
    # Path components are stripped; result must not retain traversal
    name = sanitize_filename("../etc/passwd.csv")
    assert name == "passwd.csv"
    assert ".." not in name
    assert "/" not in name


def test_path_traversal_windows_style():
    # basename strips dirs — should sanitize to passwd.csv without raising if only name left
    name = sanitize_filename("..\\..\\secret.csv")
    assert ".." not in name
    assert name.endswith(".csv")


def test_sanitize_strips_control_chars():
    name = sanitize_filename("ok\x00name.csv")
    assert "\x00" not in name


def test_local_storage_never_overwrites(tmp_path):
    store = LocalTempStorage(tmp_path)
    key = "client_1/2024-01/abc_file.csv"
    store.store(storage_key=key, data=b"one")
    store.store(storage_key=key, data=b"two")
    assert (tmp_path / key).read_bytes() == b"one"


def test_local_storage_blocks_traversal(tmp_path):
    store = LocalTempStorage(tmp_path)
    with pytest.raises(PathTraversalError):
        store.store(storage_key="../escape.csv", data=b"x")


def test_public_dict_hides_storage_and_full_hash(raw_svc):
    meta = raw_svc.ingest_bytes(
        data=csv_standard(), original_name="ok.csv", client_id=99, competencia="2024-01"
    )
    pub = meta.to_public_dict()
    assert "storage_key" not in pub
    assert "sha256_raw" not in pub
    assert pub["sha256_raw_partial"]
    assert len(pub["sha256_raw_partial"]) == 12


def test_persist_uses_content_address(tmp_path):
    store = LocalTempStorage(tmp_path)
    svc = RawFileService(store)
    data = csv_standard()
    meta = svc.ingest_bytes(
        data=data,
        original_name="planilha.csv",
        client_id=7,
        competencia="2024-02",
        persist=True,
    )
    assert store.exists(meta.storage_key)
