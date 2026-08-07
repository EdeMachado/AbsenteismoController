"""In-memory normalization — preserve original + rule + alerts."""

from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime
from typing import Any

from backend.ingestion.limits import EMPTY_SENTINELS
from backend.ingestion.schemas import NormalizedValue


def fold_accents(text: str) -> str:
    s = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in s if not unicodedata.combining(ch))


def is_empty(value: Any) -> bool:
    if value is None:
        return True
    s = str(value).strip().lower()
    return s in EMPTY_SENTINELS


class NormalizationService:
    def normalize_field(self, field: str, value: Any) -> NormalizedValue:
        if is_empty(value):
            return NormalizedValue(value, None, "empty_sentinel", None, 1.0)

        if field in {"setor", "centro_custo"}:
            return self._norm_label(value)
        if field == "cid":
            return self._norm_cid(value)
        if field in {"data_afastamento", "data_retorno"}:
            return self._norm_date(value)
        if field in {"dias_atestados", "horas_dia", "horas_perdi"}:
            return self._norm_number(value, jornada=(field == "horas_dia"))
        if field == "mes_referencia":
            return self._norm_competencia(value)
        if field in {"nomecompleto", "matricula"}:
            # Trim only — never fuzzy-correct person names
            s = " ".join(str(value).split())
            return NormalizedValue(value, s, "trim_spaces", None, 1.0)
        if field == "cpf":
            digits = re.sub(r"\D", "", str(value))
            alert = "cpf_invalid_length" if digits and len(digits) not in (11,) else None
            return NormalizedValue(value, digits or None, "digits_only", alert, 0.9 if digits else 0.5)
        s = " ".join(str(value).split())
        return NormalizedValue(value, s, "trim_spaces", None, 1.0)

    def _norm_label(self, value: Any) -> NormalizedValue:
        raw = " ".join(str(value).split())
        # Preserve display form; comparison key folds accents/case
        return NormalizedValue(value, raw, "trim_label", None, 1.0)

    def comparison_key(self, value: str | None) -> str | None:
        if value is None:
            return None
        return re.sub(r"\s+", " ", fold_accents(value).lower()).strip()

    def _norm_cid(self, value: Any) -> NormalizedValue:
        s = str(value).strip().upper().replace(" ", "")
        s = s.replace(",", ".")
        m = re.match(r"^([A-Z]\d{2})(\.?\d{0,2})?$", s)
        if not m:
            return NormalizedValue(value, s, "cid_passthrough", "cid_format_alert", 0.6)
        base, rest = m.group(1), m.group(2) or ""
        if rest and not rest.startswith("."):
            rest = f".{rest}"
        return NormalizedValue(value, f"{base}{rest}", "cid_normalize", None, 0.95)

    def _norm_date(self, value: Any) -> NormalizedValue:
        if isinstance(value, datetime):
            return NormalizedValue(value, value.date().isoformat(), "datetime_to_date", None, 1.0)
        if isinstance(value, date):
            return NormalizedValue(value, value.isoformat(), "date_iso", None, 1.0)
        s = str(value).strip()
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%Y/%m/%d"):
            try:
                d = datetime.strptime(s, fmt).date()
                return NormalizedValue(value, d.isoformat(), f"parse_{fmt}", None, 0.95)
            except ValueError:
                continue
        return NormalizedValue(value, None, "date_parse_failed", "invalid_date", 0.2)

    def _norm_number(self, value: Any, *, jornada: bool = False) -> NormalizedValue:
        if isinstance(value, (int, float)):
            num = float(value)
            alert = None
            if jornada and (num <= 0 or num > 24):
                alert = "jornada_out_of_range"
            return NormalizedValue(value, num, "numeric", alert, 0.9 if alert else 1.0)
        s = str(value).strip().replace(" ", "")
        # Brazilian decimal comma
        if "," in s and "." in s:
            s = s.replace(".", "").replace(",", ".")
        elif "," in s:
            s = s.replace(",", ".")
        try:
            num = float(s)
        except ValueError:
            return NormalizedValue(value, None, "number_parse_failed", "invalid_number", 0.2)
        alert = None
        if jornada and (num <= 0 or num > 24):
            alert = "jornada_out_of_range"
        return NormalizedValue(value, num, "decimal_comma", alert, 0.9 if alert else 0.95)

    def _norm_competencia(self, value: Any) -> NormalizedValue:
        s = str(value).strip()
        m = re.match(r"^(\d{4})[-/](\d{1,2})$", s)
        if m:
            y, mo = int(m.group(1)), int(m.group(2))
            if 1 <= mo <= 12:
                return NormalizedValue(value, f"{y:04d}-{mo:02d}", "competencia_ym", None, 1.0)
        m = re.match(r"^(\d{1,2})[-/](\d{4})$", s)
        if m:
            mo, y = int(m.group(1)), int(m.group(2))
            if 1 <= mo <= 12:
                return NormalizedValue(value, f"{y:04d}-{mo:02d}", "competencia_my", None, 1.0)
        return NormalizedValue(value, None, "competencia_failed", "invalid_competencia", 0.2)

    def normalize_row(self, mapped: dict[str, Any]) -> dict[str, NormalizedValue]:
        return {k: self.normalize_field(k, v) for k, v in mapped.items()}
