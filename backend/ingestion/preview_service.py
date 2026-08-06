"""Preview service — no commit/flush/insert into business tables."""

from __future__ import annotations

import hashlib
import json
import secrets
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any

from backend.ingestion import PIPELINE_VERSION, is_intelligent_ingestion_enabled
from backend.ingestion.column_mapping_service import ColumnMappingService, normalize_header
from backend.ingestion.exceptions import (
    AmbiguousStructureError,
    FeatureDisabledError,
    PreviewRequiredError,
)
from backend.ingestion.file_fingerprint_service import FileFingerprintService
from backend.ingestion.header_detector import HeaderDetector
from backend.ingestion.iqb_adapter import IngestionIQBAdapter
from backend.ingestion.logging_utils import new_correlation_id, partial_hash, timed_step
from backend.ingestion.mapping_profile_service import MappingProfileService
from backend.ingestion.normalization_service import NormalizationService
from backend.ingestion.pii_mask import mask_row
from backend.ingestion.raw_file_service import RawFileService
from backend.ingestion.reupload_detection_service import ReuploadDetectionService
from backend.ingestion.schemas import PreviewSummary
from backend.ingestion.spreadsheet_reader import SpreadsheetReader


class PreviewService:
    """Build ingestion preview without writing atestados / mutating legacy tables."""

    def __init__(
        self,
        conn: sqlite3.Connection | None = None,
        *,
        require_flag: bool = True,
    ) -> None:
        self.conn = conn
        self.require_flag = require_flag
        self.raw = RawFileService()
        self.reader = SpreadsheetReader()
        self.headers = HeaderDetector()
        self.mapper = ColumnMappingService()
        self.norm = NormalizationService()
        self.fp = FileFingerprintService()
        self.iqb = IngestionIQBAdapter()
        self.reupload = ReuploadDetectionService(conn)
        # In-memory preview store for tests when conn is None
        self._memory: dict[str, dict[str, Any]] = {}

    def preview(
        self,
        *,
        data: bytes,
        original_name: str,
        client_id: int,
        competencia: str,
        uploaded_by: str | None = None,
        sheet_override: str | None = None,
        header_row_override: int | None = None,
        mapping_override: dict[str, str] | None = None,
    ) -> PreviewSummary:
        if self.require_flag and not is_intelligent_ingestion_enabled():
            raise FeatureDisabledError("ENABLE_INTELLIGENT_INGESTION is false")

        correlation_id = new_correlation_id()
        with timed_step(correlation_id, "raw_metadata", client_id=client_id):
            meta = self.raw.ingest_bytes(
                data=data,
                original_name=original_name,
                client_id=client_id,
                competencia=competencia,
                uploaded_by=uploaded_by,
                persist=False,
            )

        with timed_step(correlation_id, "read_spreadsheet"):
            content = self.reader.read(data, filename=meta.original_name)

        with timed_step(correlation_id, "detect_header"):
            detection = self.headers.detect(content)
            if detection.necessita_confirmacao and sheet_override is None and header_row_override is None:
                # Still build preview but mark decision as needs confirmation
                pass

            aba = sheet_override or detection.aba_sugerida
            header_row = (
                header_row_override
                if header_row_override is not None
                else detection.linha_cabecalho_sugerida
            )
            if aba is None or header_row is None:
                raise AmbiguousStructureError("sheet/header requires confirmation")

            sheet = next((s for s in content.sheets if s.name == aba), None)
            if sheet is None:
                raise AmbiguousStructureError("requested sheet not found")
            headers, data_rows = self.headers.extract_headers_and_data(sheet, header_row)

        profile = None
        profile_mapping = mapping_override
        cols_norm = [normalize_header(h) for h in headers]
        inferred_types = ["text"] * len(headers)
        structural = self.fp.structural_signature(
            columns_normalized=cols_norm,
            inferred_types=inferred_types,
            aba=aba,
            header_row=header_row,
        )

        if self.conn and profile_mapping is None:
            mps = MappingProfileService(self.conn)
            profile = mps.find_active_by_signature(client_id, structural)
            if profile:
                profile_mapping = profile.mapping_json

        with timed_step(correlation_id, "map_columns"):
            mappings = self.mapper.map_headers(
                headers,
                sample_columns=data_rows[:30],
                profile_mapping=profile_mapping,
            )
            map_conf = (
                sum(m.confianca for m in mappings if m.campo_canonico) / max(len(mappings), 1)
            )

        # Build normalized canonical rows
        normalized_rows: list[dict[str, Any]] = []
        valid = alert = invalid = 0
        missing_fields: set[str] = set()
        setores: set[str] = set()
        ccs: set[str] = set()
        with_id = 0
        with_hours = 0

        for row in data_rows:
            if not any(c is not None and str(c).strip() for c in row):
                continue
            mapped: dict[str, Any] = {}
            for i, m in enumerate(mappings):
                if m.campo_canonico and i < len(row):
                    mapped[m.campo_canonico] = row[i]
            if "mes_referencia" not in mapped:
                mapped["mes_referencia"] = competencia
            norm_row = self.norm.normalize_row(mapped)
            # classify
            has_alert = any(nv.alert for nv in norm_row.values())
            required_ok = all(
                norm_row.get(f) and norm_row[f].normalized is not None
                for f in ("nomecompleto", "data_afastamento", "dias_atestados")
            )
            if not required_ok:
                invalid += 1
                for f in ("nomecompleto", "data_afastamento", "dias_atestados"):
                    if not norm_row.get(f) or norm_row[f].normalized is None:
                        missing_fields.add(f)
            elif has_alert:
                alert += 1
                valid += 1
            else:
                valid += 1

            if norm_row.get("matricula") and norm_row["matricula"].normalized:
                with_id += 1
            if norm_row.get("horas_dia") and norm_row["horas_dia"].normalized is not None:
                with_hours += 1
            if norm_row.get("setor") and norm_row["setor"].normalized:
                setores.add(str(norm_row["setor"].normalized))
            if norm_row.get("centro_custo") and norm_row["centro_custo"].normalized:
                ccs.add(str(norm_row["centro_custo"].normalized))

            normalized_rows.append({k: v.to_dict() for k, v in norm_row.items()})

        total = valid + invalid  # alert counted in valid
        # fix double count: valid already includes alert rows
        # total rows processed:
        total_rows = len(normalized_rows)
        identity_cov = with_id / total_rows if total_rows else 0.0
        hours_cov = with_hours / total_rows if total_rows else 0.0

        content_hash = self.fp.content_hash_normalized(normalized_rows)
        fingerprints = [
            self.fp.line_fingerprint({k: v for k, v in row.items()})
            for row in normalized_rows
        ]

        with timed_step(correlation_id, "iqb"):
            iqb = self.iqb.evaluate(
                client_id=client_id,
                competencia=competencia,
                normalized_rows=normalized_rows,
            )

        with timed_step(correlation_id, "reupload"):
            reup = self.reupload.assess(
                client_id=client_id,
                competencia=competencia,
                sha256_raw=meta.sha256_raw,
                content_hash_normalized=content_hash,
                structural_signature=structural,
                line_fingerprints=fingerprints,
            )

        decision = "PROCEED"
        if detection.necessita_confirmacao:
            decision = "CONFIRM_STRUCTURE"
        if any(m.necessita_confirmacao for m in mappings):
            decision = "CONFIRM_MAPPING"
        if reup.blocks_auto_import:
            decision = "BLOCKED_REUPLOAD" if not reup.requires_admin_justification else "CONFIRM_REUPLOAD"
        if invalid > total_rows * 0.5 and total_rows:
            decision = "REJECT_QUALITY"

        preview_id = uuid.uuid4().hex
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        sample = [mask_row(r) for r in normalized_rows[:5]]

        summary = PreviewSummary(
            preview_id=preview_id,
            confirmation_token=token,
            client_id=client_id,
            competencia=competencia,
            file_name=meta.original_name,
            sha256_raw_partial=partial_hash(meta.sha256_raw),
            aba=aba,
            header_row=header_row,
            profile_id=profile.id if profile else None,
            profile_version=profile.version if profile else None,
            mapping=[m.to_dict() for m in mappings],
            mapping_confidence=round(map_conf, 4),
            iqb=iqb,
            total_rows=total_rows,
            valid_rows=valid,
            alert_rows=alert,
            invalid_rows=invalid,
            missing_fields=sorted(missing_fields),
            setor_variants=sorted(setores)[:50],
            centro_custo_variants=sorted(ccs)[:50],
            identity_coverage=round(identity_cov, 4),
            hours_coverage=round(hours_cov, 4),
            reupload=reup.to_dict(),
            recommended_decision=decision,
            structural_signature=structural,
            content_hash_normalized=content_hash,
            sample_masked=sample,
        )

        # Persist preview metadata only into epic1 tables (optional) — never atestados
        payload = {
            "summary": summary.to_public_dict(),
            "token_hash": token_hash,
            "sha256_raw": meta.sha256_raw,
            "normalized_rows": normalized_rows,
            "fingerprints": fingerprints,
            "correlation_id": correlation_id,
            "pipeline_version": PIPELINE_VERSION,
            "confirmed": False,
            "consumed": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._store_preview(payload)
        return summary

    def get_preview(self, preview_id: str) -> dict[str, Any]:
        data = self._load_preview(preview_id)
        if not data:
            raise PreviewRequiredError("preview not found")
        public = dict(data["summary"])
        # never re-expose token on GET
        public.pop("confirmation_token", None)
        return public

    def confirm_preview(
        self,
        preview_id: str,
        *,
        token: str,
        client_id: int,
        admin_justification: str | None = None,
    ) -> dict[str, Any]:
        data = self._load_preview(preview_id)
        if not data:
            raise PreviewRequiredError("preview not found")
        if data["summary"]["client_id"] != client_id:
            raise PreviewRequiredError("client mismatch")
        th = hashlib.sha256(token.encode()).hexdigest()
        if th != data["token_hash"]:
            raise PreviewRequiredError("invalid confirmation token")
        reup = data["summary"].get("reupload") or {}
        if reup.get("requires_admin_justification") and not (admin_justification or "").strip():
            raise PreviewRequiredError("admin justification required")
        data["confirmed"] = True
        data["admin_justification"] = (admin_justification or "")[:500]
        self._store_preview(data, preview_id=preview_id)
        return {"preview_id": preview_id, "confirmed": True}

    def _store_preview(self, payload: dict[str, Any], preview_id: str | None = None) -> None:
        pid = preview_id or payload["summary"]["preview_id"]
        if self.conn is None:
            self._memory[pid] = payload
            return
        # Store as execution mode=preview row
        summary = payload["summary"]
        self.conn.execute(
            """
            INSERT OR REPLACE INTO ingestion_executions (
                execution_uuid, raw_file_id, client_id, competencia, profile_id, profile_version,
                mode, started_at, finished_at, status, total_rows, valid_rows, alert_rows, error_rows,
                inserted_rows, ignored_rows, structural_signature, content_hash_normalized,
                idempotency_key, safe_message, correlation_id, confirmation_token_hash, preview_payload_json
            ) VALUES (?, NULL, ?, ?, ?, ?, 'preview', ?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?, NULL, ?, ?, ?, ?)
            """,
            (
                pid,
                summary["client_id"],
                summary["competencia"],
                summary.get("profile_id"),
                summary.get("profile_version"),
                payload["created_at"],
                payload["created_at"],
                "succeeded" if payload.get("confirmed") else "pending",
                summary["total_rows"],
                summary["valid_rows"],
                summary["alert_rows"],
                summary["invalid_rows"],
                summary["structural_signature"],
                summary["content_hash_normalized"],
                "preview_stored",
                payload["correlation_id"],
                payload["token_hash"],
                json.dumps(
                    {
                        "summary": {k: v for k, v in summary.items() if k != "confirmation_token"},
                        "confirmed": payload.get("confirmed", False),
                        "consumed": payload.get("consumed", False),
                        "normalized_rows": payload["normalized_rows"],
                        "fingerprints": payload["fingerprints"],
                        "sha256_raw": payload["sha256_raw"],
                        "pipeline_version": payload["pipeline_version"],
                        "admin_justification": payload.get("admin_justification"),
                    },
                    ensure_ascii=False,
                ),
            ),
        )
        self.conn.commit()
        self._memory[pid] = payload

    def _load_preview(self, preview_id: str) -> dict[str, Any] | None:
        if preview_id in self._memory:
            return self._memory[preview_id]
        if self.conn is None:
            return None
        cur = self.conn.execute(
            "SELECT preview_payload_json, confirmation_token_hash FROM ingestion_executions WHERE execution_uuid = ? AND mode = 'preview'",
            (preview_id,),
        )
        row = cur.fetchone()
        if not row or not row[0]:
            return None
        body = json.loads(row[0])
        summary = body["summary"]
        summary["preview_id"] = preview_id
        # token not stored plaintext
        payload = {
            "summary": summary,
            "token_hash": row[1],
            "sha256_raw": body["sha256_raw"],
            "normalized_rows": body["normalized_rows"],
            "fingerprints": body["fingerprints"],
            "correlation_id": "reloaded",
            "pipeline_version": body.get("pipeline_version", PIPELINE_VERSION),
            "confirmed": body.get("confirmed", False),
            "consumed": body.get("consumed", False),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "admin_justification": body.get("admin_justification"),
        }
        self._memory[preview_id] = payload
        return payload
