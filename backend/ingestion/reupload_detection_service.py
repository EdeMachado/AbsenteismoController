"""Reupload classification — tenant + competência scoped."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Any

from backend.ingestion.schemas import ReuploadClass


@dataclass
class ReuploadAssessment:
    classification: ReuploadClass
    previous_execution_id: str | None
    aggregate_diff: dict[str, Any]
    blocks_auto_import: bool
    requires_admin_justification: bool
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "classification": self.classification.value,
            "previous_execution_id": self.previous_execution_id,
            "aggregate_diff": self.aggregate_diff,
            "blocks_auto_import": self.blocks_auto_import,
            "requires_admin_justification": self.requires_admin_justification,
            "message": self.message,
        }


class ReuploadDetectionService:
    def __init__(self, conn: sqlite3.Connection | None = None) -> None:
        self.conn = conn

    def assess(
        self,
        *,
        client_id: int,
        competencia: str,
        sha256_raw: str,
        content_hash_normalized: str,
        structural_signature: str,
        line_fingerprints: list[str],
        known_raw_hashes: set[str] | None = None,
        known_content_hashes: set[str] | None = None,
        known_signatures: set[str] | None = None,
        previous_fingerprints: set[str] | None = None,
        previous_execution_id: str | None = None,
    ) -> ReuploadAssessment:
        raw_hits = known_raw_hashes or set()
        content_hits = known_content_hashes or set()
        sig_hits = known_signatures or set()
        prev_fp = previous_fingerprints or set()

        if self.conn is not None:
            raw_hits |= self._load_raw_hashes(client_id)
            content_hits |= self._load_content_hashes(client_id, competencia)
            sig_hits |= self._load_signatures(client_id)
            db_prev = self._load_previous_fingerprints(client_id, competencia)
            if db_prev:
                prev_fp |= db_prev[0]
                previous_execution_id = previous_execution_id or db_prev[1]

        empty_diff = {
            "linhas_novas": 0,
            "linhas_ausentes": 0,
            "linhas_alteradas": 0,
            "total_anterior": 0,
            "total_novo": len(line_fingerprints),
        }

        if sha256_raw in raw_hits:
            return ReuploadAssessment(
                ReuploadClass.ARQUIVO_BRUTO_IDENTICO,
                previous_execution_id,
                empty_diff,
                True,
                False,
                "identical raw file hash; auto-import blocked",
            )

        if content_hash_normalized in content_hits:
            return ReuploadAssessment(
                ReuploadClass.CONTEUDO_NORMALIZADO_IDENTICO,
                previous_execution_id,
                empty_diff,
                True,
                False,
                "normalized content identical (possibly renamed); auto-import blocked",
            )

        if prev_fp:
            new_set = set(line_fingerprints)
            added = new_set - prev_fp
            removed = prev_fp - new_set
            # "altered" approximated as neither pure add-only nor identical
            altered = 0
            if added and removed:
                # cannot expose line content — aggregate only
                altered = min(len(added), len(removed))
            diff = {
                "linhas_novas": len(added),
                "linhas_ausentes": len(removed),
                "linhas_alteradas": altered,
                "total_anterior": len(prev_fp),
                "total_novo": len(new_set),
            }
            if not added and not removed:
                return ReuploadAssessment(
                    ReuploadClass.CONTEUDO_NORMALIZADO_IDENTICO,
                    previous_execution_id,
                    diff,
                    True,
                    False,
                    "line fingerprints identical for competência",
                )
            # Complementary heuristic: mostly additions, few removals
            if len(added) > 0 and len(removed) == 0 and len(added) < len(prev_fp):
                return ReuploadAssessment(
                    ReuploadClass.POSSIVEL_COMPLEMENTAR,
                    previous_execution_id,
                    diff,
                    True,
                    True,
                    "possible complementary upload; admin confirmation required",
                )
            return ReuploadAssessment(
                ReuploadClass.MESMA_COMPETENCIA_CONTEUDO_DIFERENTE,
                previous_execution_id,
                diff,
                True,
                True,
                "same competência with different content; review aggregate diff",
            )

        if structural_signature not in sig_hits and sig_hits:
            # Known client has other layouts; this one is new structure
            # Only LAYOUT_ALTERADO if we know prior profile for same name — else NOVO
            pass

        if structural_signature in sig_hits:
            # same layout seen before but new content/competência path already handled
            return ReuploadAssessment(
                ReuploadClass.NOVO_ARQUIVO,
                previous_execution_id,
                empty_diff,
                False,
                False,
                "new file with known layout signature",
            )

        # Layout changed relative to active profile signatures for client
        if self.conn is not None:
            active_sigs = self._load_active_profile_signatures(client_id)
            if active_sigs and structural_signature not in active_sigs:
                return ReuploadAssessment(
                    ReuploadClass.LAYOUT_ALTERADO,
                    previous_execution_id,
                    empty_diff,
                    True,
                    False,
                    "structural layout differs from active client profile",
                )

        return ReuploadAssessment(
            ReuploadClass.NOVO_ARQUIVO,
            previous_execution_id,
            empty_diff,
            False,
            False,
            "no prior matching ingestion for tenant/competência",
        )

    def _load_raw_hashes(self, client_id: int) -> set[str]:
        try:
            cur = self.conn.execute(
                "SELECT sha256_raw FROM ingestion_raw_files WHERE client_id = ?",
                (client_id,),
            )
            return {r[0] for r in cur.fetchall()}
        except sqlite3.Error:
            return set()

    def _load_content_hashes(self, client_id: int, competencia: str) -> set[str]:
        try:
            cur = self.conn.execute(
                """
                SELECT content_hash_normalized FROM ingestion_executions
                WHERE client_id = ? AND competencia = ?
                  AND status IN ('succeeded', 'idempotent_hit')
                  AND content_hash_normalized IS NOT NULL
                """,
                (client_id, competencia),
            )
            return {r[0] for r in cur.fetchall() if r[0]}
        except sqlite3.Error:
            return set()

    def _load_signatures(self, client_id: int) -> set[str]:
        try:
            cur = self.conn.execute(
                """
                SELECT DISTINCT structural_signature FROM ingestion_executions
                WHERE client_id = ? AND structural_signature IS NOT NULL
                """,
                (client_id,),
            )
            return {r[0] for r in cur.fetchall() if r[0]}
        except sqlite3.Error:
            return set()

    def _load_active_profile_signatures(self, client_id: int) -> set[str]:
        try:
            cur = self.conn.execute(
                """
                SELECT structural_signature FROM ingestion_mapping_profiles
                WHERE client_id = ? AND active = 1
                """,
                (client_id,),
            )
            return {r[0] for r in cur.fetchall()}
        except sqlite3.Error:
            return set()

    def _load_previous_fingerprints(
        self, client_id: int, competencia: str
    ) -> tuple[set[str], str | None] | None:
        try:
            cur = self.conn.execute(
                """
                SELECT execution_uuid, id FROM ingestion_executions
                WHERE client_id = ? AND competencia = ?
                  AND status IN ('succeeded', 'idempotent_hit')
                ORDER BY id DESC LIMIT 1
                """,
                (client_id, competencia),
            )
            row = cur.fetchone()
            if not row:
                return None
            uuid, eid = row[0], row[1]
            fps = self.conn.execute(
                """
                SELECT line_fingerprint FROM ingestion_canonical_rows
                WHERE execution_id = ?
                """,
                (eid,),
            ).fetchall()
            return {r[0] for r in fps}, uuid
        except sqlite3.Error:
            return None
