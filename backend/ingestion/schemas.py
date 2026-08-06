"""Canonical schemas and contracts for Epic 1 ingestion."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Literal


class FieldRequirement(str, Enum):
    OBRIGATORIO = "obrigatorio"
    RECOMENDADO = "recomendado"
    OPCIONAL = "opcional"
    RESTRITO = "restrito"


class ReuploadClass(str, Enum):
    NOVO_ARQUIVO = "NOVO_ARQUIVO"
    ARQUIVO_BRUTO_IDENTICO = "ARQUIVO_BRUTO_IDENTICO"
    CONTEUDO_NORMALIZADO_IDENTICO = "CONTEUDO_NORMALIZADO_IDENTICO"
    MESMA_COMPETENCIA_CONTEUDO_DIFERENTE = "MESMA_COMPETENCIA_CONTEUDO_DIFERENTE"
    POSSIVEL_COMPLEMENTAR = "POSSIVEL_COMPLEMENTAR"
    LAYOUT_ALTERADO = "LAYOUT_ALTERADO"
    INDETERMINADO = "INDETERMINADO"


class ExecutionMode(str, Enum):
    PREVIEW = "preview"
    IMPORT = "import"


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"
    IDEMPOTENT_HIT = "idempotent_hit"


# Canonical field contract — CPF is never obrigatório.
CANONICAL_FIELDS: dict[str, FieldRequirement] = {
    "nomecompleto": FieldRequirement.OBRIGATORIO,
    "matricula": FieldRequirement.RECOMENDADO,
    "cpf": FieldRequirement.RESTRITO,  # never required; mask in preview
    "setor": FieldRequirement.RECOMENDADO,
    "centro_custo": FieldRequirement.RECOMENDADO,
    "cid": FieldRequirement.RECOMENDADO,
    "data_afastamento": FieldRequirement.OBRIGATORIO,
    "data_retorno": FieldRequirement.OPCIONAL,
    "dias_atestados": FieldRequirement.OBRIGATORIO,
    "horas_dia": FieldRequirement.RECOMENDADO,
    "horas_perdi": FieldRequirement.OPCIONAL,
    "mes_referencia": FieldRequirement.RECOMENDADO,
}


@dataclass(frozen=True)
class RawFileMetadata:
    original_name: str
    safe_storage_name: str
    extension: str
    mime_type: str
    size_bytes: int
    sha256_raw: str
    received_at: str
    client_id: int
    competencia: str
    uploaded_by: str | None
    status: str
    pipeline_version: str
    storage_key: str  # relative key, never absolute public path

    def to_public_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # Never expose absolute filesystem paths.
        d.pop("storage_key", None)
        d["sha256_raw_partial"] = self.sha256_raw[:12]
        d.pop("sha256_raw", None)
        return d


@dataclass(frozen=True)
class ColumnMapping:
    coluna_origem: str
    campo_canonico: str | None
    confianca: float
    metodo: str
    necessita_confirmacao: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class HeaderDetectionResult:
    aba_sugerida: str | None
    linha_cabecalho_sugerida: int | None
    confianca: float
    alternativas: list[dict[str, Any]] = field(default_factory=list)
    necessita_confirmacao: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NormalizedValue:
    original: Any
    normalized: Any
    rule: str
    alert: str | None = None
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PreviewSummary:
    preview_id: str
    confirmation_token: str
    client_id: int
    competencia: str
    file_name: str
    sha256_raw_partial: str
    aba: str | None
    header_row: int | None
    profile_id: int | None
    profile_version: int | None
    mapping: list[dict[str, Any]]
    mapping_confidence: float
    iqb: dict[str, Any] | None
    total_rows: int
    valid_rows: int
    alert_rows: int
    invalid_rows: int
    missing_fields: list[str]
    setor_variants: list[str]
    centro_custo_variants: list[str]
    identity_coverage: float
    hours_coverage: float
    reupload: dict[str, Any]
    recommended_decision: str
    structural_signature: str
    content_hash_normalized: str
    sample_masked: list[dict[str, Any]] = field(default_factory=list)

    def to_public_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ImportResult:
    execution_id: str
    status: str
    inserted: int
    ignored: int
    alerts: int
    errors: int
    idempotent: bool
    message: str
    correlation_id: str

    def to_public_dict(self) -> dict[str, Any]:
        return asdict(self)


PII_FIELDS = frozenset({"cpf", "matricula", "nomecompleto", "nome"})
MASKED = "***"
