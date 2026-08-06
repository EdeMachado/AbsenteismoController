"""Deterministic column → canonical field mapping with confidence."""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any

from backend.ingestion.schemas import CANONICAL_FIELDS, ColumnMapping

# Aliases (normalized keys) → canonical field
ALIASES: dict[str, str] = {
    # nome
    "nome": "nomecompleto",
    "funcionario": "nomecompleto",
    "colaborador": "nomecompleto",
    "nomecompleto": "nomecompleto",
    "empregado": "nomecompleto",
    # matricula
    "matricula": "matricula",
    "chapa": "matricula",
    "registro": "matricula",
    "codigodofuncionario": "matricula",
    "codigofuncionario": "matricula",
    # cpf
    "cpf": "cpf",
    # setor
    "setor": "setor",
    "area": "setor",
    "departamento": "setor",
    "depto": "setor",
    "secao": "setor",
    # centro de custo
    "centrodecusto": "centro_custo",
    "centrocusto": "centro_custo",
    "cc": "centro_custo",
    "ccusto": "centro_custo",
    "costcenter": "centro_custo",
    # cid
    "cid": "cid",
    "codigocid": "cid",
    "cid10": "cid",
    "diagnosticocodificado": "cid",
    # datas
    "dataafastamento": "data_afastamento",
    "datainicio": "data_afastamento",
    "inicioafastamento": "data_afastamento",
    "dataretorno": "data_retorno",
    "fimafastamento": "data_retorno",
    # dias
    "dias": "dias_atestados",
    "diasafastados": "dias_atestados",
    "diasdeafastamento": "dias_atestados",
    "quantidadededias": "dias_atestados",
    "qtddias": "dias_atestados",
    "diasatestados": "dias_atestados",
    # jornada
    "horasdia": "horas_dia",
    "jornada": "horas_dia",
    "jornadadiaria": "horas_dia",
    "cargahorariadiaria": "horas_dia",
    "horasperdi": "horas_perdi",
    "horasperdidas": "horas_perdi",
    # competencia
    "mesreferencia": "mes_referencia",
    "competencia": "mes_referencia",
    "referencia": "mes_referencia",
}

AUTO_MAP_MIN = 0.75
SIMILARITY_MIN = 0.86


def normalize_header(value: str) -> str:
    s = unicodedata.normalize("NFKD", (value or "").strip().lower())
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s


class ColumnMappingService:
    def map_headers(
        self,
        headers: list[str],
        *,
        sample_columns: list[list[Any]] | None = None,
        profile_mapping: dict[str, str] | None = None,
    ) -> list[ColumnMapping]:
        used: set[str] = set()
        results: list[ColumnMapping] = []
        sample_columns = sample_columns or []

        for idx, header in enumerate(headers):
            # Profile override first (exact origin header)
            if profile_mapping and header in profile_mapping:
                canon = profile_mapping[header]
                if canon in used:
                    results.append(
                        ColumnMapping(header, None, 0.4, "profile_conflict", True)
                    )
                    continue
                used.add(canon)
                results.append(ColumnMapping(header, canon, 1.0, "profile", False))
                continue

            norm = normalize_header(header)
            # Exact / alias
            if norm in ALIASES:
                canon = ALIASES[norm]
                conf, method = 0.98, "exact" if norm == normalize_header(canon.replace("_", "")) else "alias"
                if canon == "nomecompleto" and norm == "nomecompleto":
                    conf, method = 1.0, "exact"
                if canon in used:
                    results.append(ColumnMapping(header, None, 0.5, "duplicate_target", True))
                    continue
                if conf >= AUTO_MAP_MIN:
                    used.add(canon)
                    results.append(ColumnMapping(header, canon, conf, method, False))
                else:
                    results.append(ColumnMapping(header, canon, conf, method, True))
                continue

            # Similarity against known alias keys and canonical names
            best_key = None
            best_ratio = 0.0
            for key in list(ALIASES.keys()) + [normalize_header(f) for f in CANONICAL_FIELDS]:
                ratio = SequenceMatcher(None, norm, key).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_key = key
            if best_key and best_ratio >= SIMILARITY_MIN:
                canon = ALIASES.get(best_key, best_key if best_key in CANONICAL_FIELDS else None)
                if canon is None and best_key in {normalize_header(f) for f in CANONICAL_FIELDS}:
                    # map normalized canonical
                    for f in CANONICAL_FIELDS:
                        if normalize_header(f) == best_key:
                            canon = f
                            break
                if canon and canon not in used:
                    needs = best_ratio < 0.92
                    if not needs:
                        used.add(canon)
                    results.append(
                        ColumnMapping(header, canon if not needs else canon, round(best_ratio, 4), "similarity", needs)
                    )
                    if not needs:
                        used.add(canon)
                    continue

            # Type hint from sample
            type_hint = _infer_column_type([row[idx] if idx < len(row) else None for row in sample_columns[:20]])
            hinted = _type_to_field(type_hint, used)
            if hinted:
                results.append(ColumnMapping(header, hinted, 0.55, "type_hint", True))
            else:
                results.append(ColumnMapping(header, None, 0.0, "unmapped", True))

        return results


def _infer_column_type(values: list[Any]) -> str | None:
    non_empty = [v for v in values if v is not None and str(v).strip() != ""]
    if not non_empty:
        return None
    date_like = sum(1 for v in non_empty if _looks_date(v))
    num_like = sum(1 for v in non_empty if _looks_number(v))
    cid_like = sum(1 for v in non_empty if _looks_cid(v))
    n = len(non_empty)
    if cid_like / n >= 0.5:
        return "cid"
    if date_like / n >= 0.5:
        return "date"
    if num_like / n >= 0.7:
        return "number"
    return "text"


def _looks_date(v: Any) -> bool:
    s = str(v)
    return bool(re.search(r"\d{1,4}[/-]\d{1,2}[/-]\d{1,4}", s)) or hasattr(v, "year")


def _looks_number(v: Any) -> bool:
    if isinstance(v, (int, float)):
        return True
    s = str(v).strip().replace(",", ".")
    try:
        float(s)
        return True
    except ValueError:
        return False


def _looks_cid(v: Any) -> bool:
    s = str(v).strip().upper()
    return bool(re.match(r"^[A-Z]\d{2}(\.\d{1,2})?$", s))


def _type_to_field(type_hint: str | None, used: set[str]) -> str | None:
    order = {
        "cid": ["cid"],
        "date": ["data_afastamento", "data_retorno"],
        "number": ["dias_atestados", "horas_dia", "horas_perdi"],
        "text": ["setor", "centro_custo", "nomecompleto"],
    }
    for cand in order.get(type_hint or "", []):
        if cand not in used:
            return cand
    return None
