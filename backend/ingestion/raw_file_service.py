"""RAW file preservation — metadata only; never overwrite originals."""

from __future__ import annotations

import hashlib
import mimetypes
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from backend.ingestion import PIPELINE_VERSION
from backend.ingestion.exceptions import (
    EmptyFileError,
    FileTooLargeError,
    PathTraversalError,
    UnsupportedFormatError,
)
from backend.ingestion.limits import ALLOWED_EXTENSIONS, MAX_FILE_BYTES, REJECTED_EXTENSIONS
from backend.ingestion.schemas import RawFileMetadata


class StorageBackend(Protocol):
    def store(self, *, storage_key: str, data: bytes) -> None: ...

    def exists(self, storage_key: str) -> bool: ...


class MemoryStorage:
    """In-memory storage for tests — never used for production activation."""

    def __init__(self) -> None:
        self._files: dict[str, bytes] = {}

    def store(self, *, storage_key: str, data: bytes) -> None:
        if storage_key in self._files:
            # Never overwrite — store under content-addressed key only once.
            return
        self._files[storage_key] = data

    def exists(self, storage_key: str) -> bool:
        return storage_key in self._files

    def get(self, storage_key: str) -> bytes | None:
        return self._files.get(storage_key)


class LocalTempStorage:
    """Local directory storage for ephemeral/temp use only (not public web root)."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def store(self, *, storage_key: str, data: bytes) -> None:
        target = self._resolve(storage_key)
        if target.exists():
            return  # never overwrite
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    def exists(self, storage_key: str) -> bool:
        return self._resolve(storage_key).exists()

    def _resolve(self, storage_key: str) -> Path:
        # Prevent path traversal
        if ".." in storage_key.replace("\\", "/") or storage_key.startswith(("/", "\\")):
            raise PathTraversalError("storage_key contains path traversal")
        target = (self.root / storage_key).resolve()
        if not str(target).startswith(str(self.root)):
            raise PathTraversalError("resolved path escapes storage root")
        return target


_UNSAFE_CHARS = re.compile(r"[^\w.\-]+", re.UNICODE)


def sanitize_filename(name: str) -> str:
    """Sanitize original filename; strip path components and traversal."""
    base = Path(name.replace("\\", "/")).name
    if not base or base in {".", ".."}:
        raise PathTraversalError("invalid filename")
    if ".." in base:
        raise PathTraversalError("filename path traversal")
    # Normalize unicode, drop control chars
    norm = unicodedata.normalize("NFKC", base)
    norm = "".join(ch for ch in norm if unicodedata.category(ch)[0] != "C")
    safe = _UNSAFE_CHARS.sub("_", norm).strip("._")
    if not safe:
        raise PathTraversalError("filename sanitized to empty")
    return safe[:180]


def detect_extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class RawFileService:
    """Receive bytes, compute metadata, optionally store without mutation."""

    def __init__(self, storage: StorageBackend | None = None) -> None:
        self.storage = storage or MemoryStorage()

    def ingest_bytes(
        self,
        *,
        data: bytes,
        original_name: str,
        client_id: int,
        competencia: str,
        uploaded_by: str | None = None,
        persist: bool = False,
    ) -> RawFileMetadata:
        if not data:
            raise EmptyFileError("empty file rejected")
        if len(data) > MAX_FILE_BYTES:
            raise FileTooLargeError(f"file exceeds {MAX_FILE_BYTES} bytes")

        safe_name = sanitize_filename(original_name)
        ext = detect_extension(safe_name)
        if ext in REJECTED_EXTENSIONS or ext == ".xls":
            raise UnsupportedFormatError(
                f"format {ext or '(none)'} is not supported; use .xlsx or .csv "
                "(legacy .xls requires a secure reader not bundled)"
            )
        if ext not in ALLOWED_EXTENSIONS:
            raise UnsupportedFormatError(f"format {ext or '(none)'} is not allowed")

        digest = sha256_bytes(data)
        mime, _ = mimetypes.guess_type(safe_name)
        mime = mime or "application/octet-stream"
        received_at = datetime.now(timezone.utc).isoformat()
        storage_key = f"client_{client_id}/{competencia}/{digest[:16]}_{safe_name}"

        if persist:
            self.storage.store(storage_key=storage_key, data=data)

        return RawFileMetadata(
            original_name=safe_name,
            safe_storage_name=f"{digest[:16]}_{safe_name}",
            extension=ext,
            mime_type=mime,
            size_bytes=len(data),
            sha256_raw=digest,
            received_at=received_at,
            client_id=client_id,
            competencia=competencia,
            uploaded_by=uploaded_by,
            status="received",
            pipeline_version=PIPELINE_VERSION,
            storage_key=storage_key,
        )
