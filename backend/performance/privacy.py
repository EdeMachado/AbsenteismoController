"""Anti-PII guard for performance engine outputs."""

from __future__ import annotations

import re
from typing import Any

from backend.performance.exceptions import PrivacyViolationError

_BANNED_KEYS = frozenset(
    {
        "nomecompleto",
        "nome_completo",
        "nomefuncionario",
        "cpf",
        "matricula",
        "telefone",
        "phone",
        "email",
        "e-mail",
        "prontuario",
        "exame",
        "exames",
        "documento",
        "documentos",
        "texto_clinico",
        "anexo",
        "anexos",
    }
)

_CPF_RE = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")


def assert_no_pii(payload: Any, *, path: str = "$") -> None:
    """Raise PrivacyViolationError if banned keys or obvious PII patterns appear."""
    if isinstance(payload, dict):
        for k, v in payload.items():
            lk = str(k).lower().replace(" ", "").replace("-", "_")
            if lk in _BANNED_KEYS:
                raise PrivacyViolationError(f"banned key at {path}.{k}")
            # Person-name keys only when clearly identity fields (not window "nome")
            if lk in {"nome", "name"} and path.endswith((".trabalhador", ".pessoa", ".colaborador")):
                raise PrivacyViolationError(f"banned key at {path}.{k}")
            assert_no_pii(v, path=f"{path}.{k}")
    elif isinstance(payload, list):
        for i, item in enumerate(payload):
            assert_no_pii(item, path=f"{path}[{i}]")
    elif isinstance(payload, str):
        if _CPF_RE.search(payload) and "***" not in payload:
            raise PrivacyViolationError(f"cpf-like string at {path}")
        if _EMAIL_RE.search(payload):
            raise PrivacyViolationError(f"email-like string at {path}")
