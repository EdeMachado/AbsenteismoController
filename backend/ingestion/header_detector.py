"""Deterministic sheet/header detection with confidence scoring."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from backend.ingestion.schemas import HeaderDetectionResult
from backend.ingestion.spreadsheet_reader import SheetPreview, SpreadsheetContent

# Expected header tokens (normalized)
EXPECTED_TOKENS = {
    "nome",
    "nomecompleto",
    "funcionario",
    "colaborador",
    "matricula",
    "chapa",
    "cpf",
    "setor",
    "departamento",
    "centrodecusto",
    "cid",
    "dataafastamento",
    "dataretorno",
    "dias",
    "diasatestados",
    "horasdia",
    "jornada",
    "mesreferencia",
}


def _norm_token(value: Any) -> str:
    if value is None:
        return ""
    s = str(value).strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s


def _row_score(row: list[Any], following: list[list[Any]]) -> float:
    tokens = [_norm_token(c) for c in row if _norm_token(c)]
    if not tokens:
        return 0.0
    recognized = sum(1 for t in tokens if t in EXPECTED_TOKENS or any(t.startswith(e) or e in t for e in EXPECTED_TOKENS))
    fill = len(tokens) / max(len(row), 1)
    uniq = len(set(tokens)) / max(len(tokens), 1)
    # Density of following non-empty rows
    dens = 0.0
    if following:
        non_empty = sum(
            1
            for r in following[:10]
            if any(_norm_token(c) for c in r)
        )
        dens = non_empty / min(10, len(following))
    # Title rows often have 1–2 cells; headers have more
    breadth = min(len(tokens) / 4.0, 1.0)
    score = (
        0.35 * (recognized / max(len(tokens), 1))
        + 0.20 * fill
        + 0.15 * uniq
        + 0.20 * dens
        + 0.10 * breadth
    )
    return round(min(score, 1.0), 4)


class HeaderDetector:
    def detect(self, content: SpreadsheetContent) -> HeaderDetectionResult:
        candidates: list[dict[str, Any]] = []
        for sheet in content.sheets:
            if sheet.empty:
                continue
            for idx, row in enumerate(sheet.rows[:30]):
                following = sheet.rows[idx + 1 :]
                score = _row_score(row, following)
                if score < 0.15:
                    continue
                candidates.append(
                    {
                        "aba": sheet.name,
                        "linha_cabecalho": idx,  # 0-based
                        "confianca": score,
                    }
                )

        if not candidates:
            return HeaderDetectionResult(
                aba_sugerida=content.sheets[0].name if content.sheets else None,
                linha_cabecalho_sugerida=None,
                confianca=0.0,
                alternativas=[],
                necessita_confirmacao=True,
            )

        candidates.sort(key=lambda c: c["confianca"], reverse=True)
        best = candidates[0]
        alts = candidates[1:5]
        # Ambiguity if second is close
        ambiguous = bool(alts) and (best["confianca"] - alts[0]["confianca"] < 0.08)
        needs = ambiguous or best["confianca"] < 0.55
        return HeaderDetectionResult(
            aba_sugerida=best["aba"],
            linha_cabecalho_sugerida=best["linha_cabecalho"],
            confianca=best["confianca"],
            alternativas=alts,
            necessita_confirmacao=needs,
        )

    def extract_headers_and_data(
        self,
        sheet: SheetPreview,
        header_row: int,
    ) -> tuple[list[str], list[list[Any]]]:
        if header_row < 0 or header_row >= len(sheet.rows):
            return [], []
        headers = [str(c).strip() if c is not None else f"col_{i}" for i, c in enumerate(sheet.rows[header_row])]
        data = sheet.rows[header_row + 1 :]
        return headers, data
