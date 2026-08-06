"""Hashes, structural signatures, and line fingerprints (no CPF plaintext)."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from backend.ingestion.normalization_service import NormalizationService


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class FileFingerprintService:
    def __init__(self) -> None:
        self.norm = NormalizationService()

    def structural_signature(
        self,
        *,
        columns_normalized: list[str],
        inferred_types: list[str],
        aba: str | None,
        header_row: int | None,
    ) -> str:
        payload = {
            "columns": columns_normalized,
            "types": inferred_types,
            "aba": aba,
            "header_row": header_row,
        }
        return sha256_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))

    def content_hash_normalized(self, rows: list[dict[str, Any]]) -> str:
        """Stable content hash from canonical normalized values (no volatile metadata)."""
        ordered_fields = [
            "matricula",
            "nomecompleto",
            "setor",
            "centro_custo",
            "cid",
            "data_afastamento",
            "data_retorno",
            "dias_atestados",
            "horas_dia",
            "horas_perdi",
            "mes_referencia",
        ]
        lines: list[str] = []
        for row in rows:
            parts = []
            for f in ordered_fields:
                v = row.get(f)
                if isinstance(v, dict) and "normalized" in v:
                    v = v["normalized"]
                # Never include raw CPF; include only hashed digits if present
                if f == "cpf":
                    continue
                parts.append(f"{f}={'' if v is None else v}")
            # optional identity hash from cpf digits without storing plaintext
            cpf_val = row.get("cpf")
            if isinstance(cpf_val, dict):
                cpf_val = cpf_val.get("normalized")
            if cpf_val:
                parts.append(f"cpf_hash={sha256_text(str(cpf_val))[:16]}")
            lines.append("|".join(parts))
        lines.sort()
        return sha256_text("\n".join(lines))

    def line_fingerprint(self, row: dict[str, Any]) -> str:
        """Deterministic line fingerprint using allowed fields; CPF only as hash."""
        fields = [
            "matricula",
            "data_afastamento",
            "dias_atestados",
            "cid",
            "setor",
            "centro_custo",
        ]
        parts = []
        for f in fields:
            v = row.get(f)
            if isinstance(v, dict) and "normalized" in v:
                v = v["normalized"]
            parts.append(f"{f}={'' if v is None else v}")
        cpf_val = row.get("cpf")
        if isinstance(cpf_val, dict):
            cpf_val = cpf_val.get("normalized")
        if cpf_val:
            parts.append(f"cpf_h={sha256_text(str(cpf_val))}")
        nome = row.get("nomecompleto")
        if isinstance(nome, dict):
            nome = nome.get("normalized")
        if nome:
            # hash name — never store plaintext in fingerprint string beyond hash
            parts.append(f"nome_h={sha256_text(str(nome))}")
        return sha256_text("|".join(parts))

    def idempotency_key(
        self,
        *,
        client_id: int,
        competencia: str,
        content_hash: str,
        profile_version: int | None,
        pipeline_version: str,
    ) -> str:
        raw = f"{client_id}|{competencia}|{content_hash}|{profile_version}|{pipeline_version}"
        return sha256_text(raw)
