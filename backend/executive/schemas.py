"""Schemas for EXEC-01 executive aggregate and intelligence payloads."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass
class KpiCard:
    id: str
    label: str
    value: Any
    unit: str = ""
    available: bool = True
    unavailable_reason: Optional[str] = None
    trend: Optional[str] = None  # melhora | estabilidade | piora | None
    confidence: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ChartSeries:
    id: str
    title: str
    chart_type: str  # line | bar | pareto | heatmap | stacked
    categories: list[str] = field(default_factory=list)
    series: list[dict[str, Any]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    suppressed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExecutiveScoreView:
    available: bool
    score: Optional[float] = None
    label: str = "SCORE NÃO DISPONÍVEL"
    components: list[dict[str, Any]] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ActionItem:
    id: str
    title: str
    priority: str
    justification: str
    category: str
    status: str = "proposta"
    owner: str = "Médico BioMed"
    deadline: Optional[str] = None
    indicator: Optional[str] = None
    baseline: Optional[str] = None
    meta: Optional[str] = None
    medical_validation_required: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class IntelligenceBundle:
    resumo_executivo: str
    diagnostico_situacional: str
    fatores_prioritarios: list[str]
    alertas: list[str]
    hipoteses: list[str]
    recomendacoes: list[dict[str, Any]]
    plano_acao: list[dict[str, Any]]
    evidencias: list[str]
    limitacoes: list[str]
    confianca: str
    engine: str = "rule_engine_deterministic_v1"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
