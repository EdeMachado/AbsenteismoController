"""Schemas and configurable thresholds for BioMed Performance Engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class QualityLabel(str, Enum):
    DISPONIVEL = "disponivel"
    INDISPONIVEL = "indisponivel"
    INCOMPLETO = "incompleto"
    ESTIMADO = "estimado"
    NAO_APLICAVEL = "nao_aplicavel"
    NAO_CONFIAVEL = "nao_confiavel"


class DimensionStatus(str, Enum):
    AVALIADA = "avaliada"
    NAO_AVALIADA = "nao_avaliada"
    INDISPONIVEL = "indisponivel"
    NAO_APLICAVEL = "nao_aplicavel"


class WindowStatus(str, Enum):
    COMPLETO = "completo"
    INCOMPLETO = "incompleto"
    INDISPONIVEL = "indisponivel"


class EffectivenessCode(str, Enum):
    EFICACIA_POSITIVA_INTEGRAL = "EFICACIA_POSITIVA_INTEGRAL"
    EFICACIA_POSITIVA_PARCIAL = "EFICACIA_POSITIVA_PARCIAL"
    CONTROLE_SEVERIDADE = "CONTROLE_SEVERIDADE"
    CONTROLE_FREQUENCIA = "CONTROLE_FREQUENCIA"
    ESTABILIDADE = "ESTABILIDADE"
    PREVENCAO_DE_PIORA = "PREVENCAO_DE_PIORA"  # reserved for future formal method
    SEM_EVIDENCIA_SUFICIENTE = "SEM_EVIDENCIA_SUFICIENTE"
    RESULTADO_INCONCLUSIVO = "RESULTADO_INCONCLUSIVO"
    RESULTADO_DESFAVORAVEL = "RESULTADO_DESFAVORAVEL"


class RoiKind(str, Enum):
    ROI_OBSERVADO = "ROI_OBSERVADO"
    ROI_ESTIMADO = "ROI_ESTIMADO"
    ROI_NAO_CALCULAVEL = "ROI_NAO_CALCULAVEL"


class DecisionStatus(str, Enum):
    APRESENTADA = "apresentada"
    ACEITA = "aceita"
    ACEITA_COM_AJUSTES = "aceita_com_ajustes"
    ADIADA = "adiada"
    RECUSADA = "recusada"
    EXECUTADA = "executada"
    PENDENTE = "pendente"
    CANCELADA = "cancelada"
    CONCLUIDA = "concluida"


@dataclass(frozen=True)
class ThresholdConfig:
    """All interpretation thresholds — documented and testable; never hardcoded silently."""

    material_change: float = 0.05
    strong_improvement: float = 0.10
    stability_band: float = 0.03
    min_iqb: float = 60.0
    min_window_completeness: float = 0.8
    min_months_for_integral: int = 3
    min_assistential_coverage: float = 0.5
    max_estimated_hours_share: float = 0.5
    # ROI comparability
    min_hours_coverage_observed: float = 0.8
    max_hours_coverage_diff: float = 0.15
    # Executive score
    min_score_coverage: float = 0.5  # fraction of original weight evaluated
    round_digits: int = 4
    w_freq: float = 20.0
    w_sev: float = 20.0
    w_rec: float = 15.0
    w_cov: float = 10.0
    w_exec: float = 10.0
    w_goals: float = 10.0
    w_quality: float = 10.0
    w_cond: float = 5.0

    def validate(self) -> None:
        weights = (
            self.w_freq
            + self.w_sev
            + self.w_rec
            + self.w_cov
            + self.w_exec
            + self.w_goals
            + self.w_quality
            + self.w_cond
        )
        if abs(weights - 100.0) > 1e-6:
            raise ValueError(f"score weights must sum to 100; got {weights}")

    def weight_map(self) -> dict[str, float]:
        return {
            "evolucao_frequencia": self.w_freq,
            "evolucao_severidade": self.w_sev,
            "recorrencia": self.w_rec,
            "cobertura_assistencial": self.w_cov,
            "execucao_acoes": self.w_exec,
            "atingimento_metas": self.w_goals,
            "qualidade_dados": self.w_quality,
            "condicionantes_empresa": self.w_cond,
        }


@dataclass(frozen=True)
class IndicatorValue:
    id: str
    valor: Any
    unidade: str
    fonte: str
    metodologia: str
    qualidade: str
    periodo: str | None
    limitacoes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BaselineWindow:
    nome: str
    inicio: str | None
    fim: str | None
    meses_esperados: int
    meses_encontrados: int
    completude: float
    status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MetricSnapshot:
    """Aggregated absenteeism metrics for a period — no PII."""

    client_id: int
    periodo_inicio: str
    periodo_fim: str
    eventos: float | None = None
    trabalhadores_unicos: float | None = None
    dias_perdidos: float | None = None
    horas_perdidas_registradas: float | None = None
    horas_perdidas_estimadas: float | None = None
    duracao_media: float | None = None
    frequencia: float | None = None  # population frequency — requires headcount
    gravidade: float | None = None
    recorrencia: float | None = None
    afastamentos_longos: float | None = None
    eventos_por_100: float | None = None
    dias_por_trabalhador: float | None = None
    horas_por_100: float | None = None
    headcount: float | None = None
    iqb: float | None = None
    setores_criticos: list[str] = field(default_factory=list)
    grupos_cid: list[str] = field(default_factory=list)
    meses_com_dados: int = 0
    # Hours / period comparability metadata
    cobertura_horas_registradas: float | None = None  # 0..1
    cobertura_horas_estimadas: float | None = None  # 0..1
    metodologia_horas: str = "registradas_preferenciais"
    completude_periodo: float | None = None  # 0..1
    limitacoes: list[str] = field(default_factory=list)
    fonte: str = "fixture_or_canonical"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ActionCounts:
    propostas: int = 0
    aprovadas: int = 0
    aplicaveis: int | None = None  # defaults to aprovadas when None
    executadas: int = 0
    concluidas: int = 0
    canceladas: int = 0
    recusadas: int = 0
    adiadas: int = 0
    pendentes: int = 0

    def aprovadas_aplicaveis(self) -> int:
        if self.aplicaveis is not None:
            return max(0, int(self.aplicaveis))
        return max(0, int(self.aprovadas))

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["aprovadas_aplicaveis"] = self.aprovadas_aplicaveis()
        return d


@dataclass(frozen=True)
class BiomedProductivity:
    atendimentos_agendados: int = 0
    atendimentos_realizados: int = 0
    faltas: int = 0
    colaboradores_atendidos: int = 0
    retornos_realizados: int = 0
    entrevistas_tecnicas: int = 0
    acoes_coletivas: int = 0
    avaliacoes_ergonomicas: int = 0
    campanhas: int = 0
    encaminhamentos: int = 0
    planos_ativos: int = 0
    planos_concluidos: int = 0
    necessidade_estimada: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Conditionant:
    recomendacao_id: str
    decisao: str
    responsavel: str | None = None
    prazo: str | None = None
    status: str = DecisionStatus.PENDENTE.value
    barreira: str | None = None
    risco_residual: str | None = None
    evidencia: str | None = None
    conclusao: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EffectivenessResult:
    codigo: str
    rotulo: str
    criterios_acionados: list[str]
    evidencias: list[str]
    limitacoes: list[str]
    confianca: float
    hipoteses: list[str] = field(default_factory=list)
    confianca_componentes: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Recommendation:
    id: str
    categoria: str
    criticidade: str
    confianca: float
    evidencias: list[str]
    necessita_validacao_humana: bool
    restricoes: list[str]
    descricao: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RoiResult:
    kind: str
    valor: float | None
    premissas: dict[str, Any]
    confianca: float
    limitacoes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TechnicalNarrative:
    fatos: list[str]
    interpretacoes: list[str]
    hipoteses: list[str]
    limitacoes: list[str]
    recomendacoes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PerformanceAnalysis:
    client_id: int
    engine_version: str
    baseline_windows: list[dict[str, Any]]
    baseline_metrics: dict[str, Any]
    current_metrics: dict[str, Any]
    deltas: dict[str, Any]
    indicators: list[dict[str, Any]]
    productivity: dict[str, Any]
    coverage: dict[str, Any]
    effectiveness: dict[str, Any]
    conditionants: list[dict[str, Any]]
    recommendations: list[dict[str, Any]]
    roi: dict[str, Any]
    executive_score: dict[str, Any]
    narrative: dict[str, Any]
    thresholds_used: dict[str, Any]
    limitations: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
