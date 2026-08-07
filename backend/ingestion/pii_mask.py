"""PII masking for preview payloads — never expose full CPF/matricula/names in managerial views."""

from __future__ import annotations

from typing import Any

from backend.ingestion.schemas import MASKED, PII_FIELDS


def mask_value(field: str, value: Any) -> Any:
    if value is None:
        return None
    fl = field.lower()
    if fl == "cpf":
        s = str(value)
        digits = "".join(ch for ch in s if ch.isdigit())
        if len(digits) >= 4:
            return f"***.***.***-{digits[-2:]}"
        return MASKED
    if fl in {"matricula", "nomecompleto", "nome"}:
        s = str(value)
        if len(s) <= 2:
            return MASKED
        return s[0] + MASKED + s[-1]
    return value


def mask_row(row: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in row.items():
        if k.lower() in PII_FIELDS or k.lower() in {"cpf", "matricula", "nomecompleto"}:
            if isinstance(v, dict) and "normalized" in v:
                nv = dict(v)
                nv["normalized"] = mask_value(k, v.get("normalized"))
                nv["original"] = MASKED
                out[k] = nv
            else:
                out[k] = mask_value(k, v)
        else:
            out[k] = v
    return out


def assert_no_raw_cpf(payload: Any) -> None:
    """Test helper / runtime guard for structured payloads."""
    import re

    cpf_re = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")

    def walk(obj: Any) -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                if str(k).lower() == "cpf" and v and str(v) not in {MASKED} and not str(v).startswith("***"):
                    # allow masked forms only
                    if cpf_re.search(str(v)) and "***" not in str(v):
                        raise AssertionError("raw CPF exposed")
                walk(v)
        elif isinstance(obj, list):
            for i in obj:
                walk(i)
        elif isinstance(obj, str):
            # full unmasked CPF pattern without mask markers
            if cpf_re.fullmatch(obj.replace(" ", "")) and "***" not in obj:
                raise AssertionError("raw CPF string exposed")

    walk(payload)
