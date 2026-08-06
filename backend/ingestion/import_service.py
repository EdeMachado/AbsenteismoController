"""Idempotent transactional import into epic1 canonical layer (not legacy upload)."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any

from backend.ingestion import PIPELINE_VERSION, is_intelligent_ingestion_enabled
from backend.ingestion.exceptions import (
    ConfirmationError,
    FeatureDisabledError,
    IdempotencyConflictError,
    ReuploadBlockedError,
)
from backend.ingestion.file_fingerprint_service import FileFingerprintService
from backend.ingestion.logging_utils import new_correlation_id, timed_step
from backend.ingestion.preview_service import PreviewService
from backend.ingestion.schemas import ImportResult, ReuploadClass


class ImportService:
    """
    Import confirmed preview into ingestion_canonical_rows inside one transaction.
    Does NOT write to legacy atestados / uploads tables in this epic.
    Does NOT delete or replace prior competência data.
    """

    def __init__(self, conn: sqlite3.Connection, preview_service: PreviewService | None = None) -> None:
        self.conn = conn
        self.previews = preview_service or PreviewService(conn, require_flag=True)
        self.fp = FileFingerprintService()

    def import_preview(
        self,
        *,
        preview_id: str,
        token: str,
        client_id: int,
        competencia: str,
        expected_content_hash: str | None = None,
        expected_sha_partial: str | None = None,
    ) -> ImportResult:
        if not is_intelligent_ingestion_enabled():
            raise FeatureDisabledError("ENABLE_INTELLIGENT_INGESTION is false")

        correlation_id = new_correlation_id()
        data = self.previews._load_preview(preview_id)
        if not data:
            raise ConfirmationError("preview not found")
        summary = data["summary"]

        if summary["client_id"] != client_id:
            raise ConfirmationError("client changed between preview and import")
        if summary["competencia"] != competencia:
            raise ConfirmationError("competencia changed between preview and import")
        th = hashlib.sha256(token.encode()).hexdigest()
        if th != data["token_hash"]:
            raise ConfirmationError("invalid confirmation token")
        if not data.get("confirmed"):
            raise ConfirmationError("preview not confirmed")
        if data.get("consumed"):
            raise ConfirmationError("confirmation token already consumed")
        if expected_content_hash and expected_content_hash != summary["content_hash_normalized"]:
            raise ConfirmationError("content hash mismatch")
        if expected_sha_partial and not summary["sha256_raw_partial"].startswith(expected_sha_partial[:8]):
            raise ConfirmationError("file hash mismatch")

        reup = summary.get("reupload") or {}
        blocked = {
            ReuploadClass.ARQUIVO_BRUTO_IDENTICO.value,
            ReuploadClass.CONTEUDO_NORMALIZADO_IDENTICO.value,
        }
        if reup.get("classification") in blocked:
            raise ReuploadBlockedError("identical upload cannot be imported")
        if reup.get("requires_admin_justification") and not data.get("admin_justification"):
            raise ConfirmationError("admin justification missing")

        idem = self.fp.idempotency_key(
            client_id=client_id,
            competencia=competencia,
            content_hash=summary["content_hash_normalized"],
            profile_version=summary.get("profile_version"),
            pipeline_version=PIPELINE_VERSION,
        )

        # Idempotent hit?
        existing = self.conn.execute(
            """
            SELECT execution_uuid, inserted_rows, ignored_rows, alert_rows, error_rows, status
            FROM ingestion_executions
            WHERE client_id = ? AND idempotency_key = ?
              AND status IN ('succeeded', 'idempotent_hit') AND mode = 'import'
            LIMIT 1
            """,
            (client_id, idem),
        ).fetchone()
        if existing:
            return ImportResult(
                execution_id=existing[0],
                status="idempotent_hit",
                inserted=existing[1] or 0,
                ignored=existing[2] or 0,
                alerts=existing[3] or 0,
                errors=existing[4] or 0,
                idempotent=True,
                message="idempotent hit — previous import result returned",
                correlation_id=correlation_id,
            )

        exec_uuid = uuid.uuid4().hex
        started = datetime.now(timezone.utc).isoformat()

        try:
            with timed_step(correlation_id, "import_transaction", client_id=client_id):
                self.conn.execute("BEGIN")
                # Register raw file (additive)
                self.conn.execute(
                    """
                    INSERT OR IGNORE INTO ingestion_raw_files (
                        client_id, competencia, original_name, safe_storage_name, extension,
                        mime_type, size_bytes, sha256_raw, storage_key, status, pipeline_version,
                        uploaded_by, received_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'imported', ?, ?, ?)
                    """,
                    (
                        client_id,
                        competencia,
                        summary["file_name"],
                        summary["file_name"],
                        "." + summary["file_name"].rsplit(".", 1)[-1] if "." in summary["file_name"] else "",
                        None,
                        0,
                        data["sha256_raw"],
                        f"virtual/{data['sha256_raw'][:16]}",
                        PIPELINE_VERSION,
                        None,
                        started,
                    ),
                )
                raw_id = self.conn.execute(
                    "SELECT id FROM ingestion_raw_files WHERE client_id = ? AND sha256_raw = ?",
                    (client_id, data["sha256_raw"]),
                ).fetchone()[0]

                self.conn.execute(
                    """
                    INSERT INTO ingestion_executions (
                        execution_uuid, raw_file_id, client_id, competencia, profile_id, profile_version,
                        mode, started_at, finished_at, status, total_rows, valid_rows, alert_rows, error_rows,
                        inserted_rows, ignored_rows, structural_signature, content_hash_normalized,
                        idempotency_key, safe_message, correlation_id, confirmation_token_hash, preview_payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?, 'import', ?, NULL, 'running', ?, ?, ?, ?, 0, 0, ?, ?, ?, ?, ?, ?, NULL)
                    """,
                    (
                        exec_uuid,
                        raw_id,
                        client_id,
                        competencia,
                        summary.get("profile_id"),
                        summary.get("profile_version"),
                        started,
                        summary["total_rows"],
                        summary["valid_rows"],
                        summary["alert_rows"],
                        summary["invalid_rows"],
                        summary["structural_signature"],
                        summary["content_hash_normalized"],
                        idem,
                        "import_running",
                        correlation_id,
                        data["token_hash"],
                    ),
                )
                eid = self.conn.execute(
                    "SELECT id FROM ingestion_executions WHERE execution_uuid = ?",
                    (exec_uuid,),
                ).fetchone()[0]

                inserted = 0
                ignored = 0
                errors = 0
                for idx, (row, fp) in enumerate(
                    zip(data["normalized_rows"], data["fingerprints"]), start=1
                ):
                    # Skip invalid required
                    def nv(field: str) -> Any:
                        v = row.get(field)
                        if isinstance(v, dict):
                            return v.get("normalized")
                        return v

                    if nv("nomecompleto") is None or nv("data_afastamento") is None or nv("dias_atestados") is None:
                        errors += 1
                        self.conn.execute(
                            """
                            INSERT INTO ingestion_line_errors (
                                execution_id, line_number, field, error_code, safe_message, severity
                            ) VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (eid, idx, "required", "REQUIRED_MISSING", "required field missing", "error"),
                        )
                        ignored += 1
                        continue

                    # Canonical payload without raw CPF plaintext
                    safe_payload = {}
                    for k, v in row.items():
                        if k == "cpf" and isinstance(v, dict):
                            digits = v.get("normalized")
                            safe_payload[k] = {
                                "normalized_hash": hashlib.sha256(str(digits).encode()).hexdigest()
                                if digits
                                else None,
                                "rule": v.get("rule"),
                                "alert": v.get("alert"),
                                "confidence": v.get("confidence"),
                            }
                        else:
                            safe_payload[k] = v

                    try:
                        self.conn.execute(
                            """
                            INSERT INTO ingestion_canonical_rows (
                                execution_id, client_id, competencia, line_fingerprint, payload_json, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (
                                eid,
                                client_id,
                                competencia,
                                fp,
                                json.dumps(safe_payload, ensure_ascii=False),
                                started,
                            ),
                        )
                        inserted += 1
                    except sqlite3.IntegrityError:
                        ignored += 1

                finished = datetime.now(timezone.utc).isoformat()
                self.conn.execute(
                    """
                    UPDATE ingestion_executions
                    SET finished_at = ?, status = 'succeeded', inserted_rows = ?, ignored_rows = ?,
                        error_rows = ?, alert_rows = ?, safe_message = ?
                    WHERE id = ?
                    """,
                    (
                        finished,
                        inserted,
                        ignored,
                        errors,
                        summary["alert_rows"],
                        "import_succeeded",
                        eid,
                    ),
                )
                # consume preview token
                data["consumed"] = True
                self.previews._store_preview(data, preview_id=preview_id)
                self.conn.commit()

                return ImportResult(
                    execution_id=exec_uuid,
                    status="succeeded",
                    inserted=inserted,
                    ignored=ignored,
                    alerts=summary["alert_rows"],
                    errors=errors,
                    idempotent=False,
                    message="import committed",
                    correlation_id=correlation_id,
                )
        except Exception as exc:
            self.conn.rollback()
            # mark failed execution if row exists
            try:
                self.conn.execute(
                    """
                    UPDATE ingestion_executions
                    SET status = 'failed', finished_at = ?, safe_message = ?
                    WHERE execution_uuid = ?
                    """,
                    (datetime.now(timezone.utc).isoformat(), type(exc).__name__, exec_uuid),
                )
                self.conn.commit()
            except sqlite3.Error:
                pass
            raise

    def get_execution(self, execution_id: str, *, client_id: int) -> dict[str, Any]:
        row = self.conn.execute(
            """
            SELECT execution_uuid, client_id, competencia, mode, status, total_rows, valid_rows,
                   alert_rows, error_rows, inserted_rows, ignored_rows, safe_message, correlation_id,
                   started_at, finished_at
            FROM ingestion_executions WHERE execution_uuid = ?
            """,
            (execution_id,),
        ).fetchone()
        if not row or row[1] != client_id:
            raise ConfirmationError("execution not found")
        keys = [
            "execution_id",
            "client_id",
            "competencia",
            "mode",
            "status",
            "total_rows",
            "valid_rows",
            "alert_rows",
            "error_rows",
            "inserted_rows",
            "ignored_rows",
            "safe_message",
            "correlation_id",
            "started_at",
            "finished_at",
        ]
        return dict(zip(keys, row))
