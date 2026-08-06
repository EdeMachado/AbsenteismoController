"""Orchestrate canonical metrics + IQB → PerformanceService in shadow mode."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.models import Client
from backend.performance import ENGINE_VERSION
from backend.performance.canonical_snapshot_adapter import CanonicalSnapshotAdapter
from backend.performance.data_quality_adapter import DataQualityAdapter, QualityBundle
from backend.performance.exceptions import (
    InvalidPeriodError,
    TenantRequiredError,
)
from backend.performance.performance_service import PerformanceService
from backend.performance.privacy import assert_no_pii
from backend.performance.schemas import (
    ActionCounts,
    BiomedProductivity,
    Conditionant,
    MetricSnapshot,
    ThresholdConfig,
)
from backend.performance.window_resolver import (
    WindowComparability,
    assess_comparability,
    document_competence_equivalents,
    parse_month,
)
from dataclasses import replace


SHADOW_ADAPTER_VERSION = "epic2ab-adapter-v1"


@dataclass
class ShadowAnalysisResult:
    client_id: int
    engine_version: str
    adapter_version: str
    baseline: dict[str, Any]
    atual: dict[str, Any]
    completude: dict[str, Any]
    comparabilidade: dict[str, Any]
    iqb: dict[str, Any]
    metrics: dict[str, Any]
    deltas: dict[str, Any]
    effectiveness: dict[str, Any]
    confidence: dict[str, Any]
    executive_score: dict[str, Any]
    recommendations: list[dict[str, Any]]
    roi: dict[str, Any]
    fatos: list[str]
    interpretacoes: list[str]
    hipoteses: list[str]
    limitacoes: list[str]
    thresholds_used: dict[str, Any]
    db_sha256: str | None = None
    productivity_mode: str = "ausente"
    conditionants_mode: str = "ausente"
    descriptive_only: bool = False
    competence_equivalents: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_productivity_json(path: str | Path | None) -> BiomedProductivity | None:
    if path is None:
        return None
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("productivity-json deve ser objeto agregado")
    # allow nested key
    payload = data.get("productivity") if "productivity" in data else data
    allowed = {f.name for f in BiomedProductivity.__dataclass_fields__.values()}  # type: ignore[attr-defined]
    kwargs = {k: v for k, v in payload.items() if k in allowed}
    return BiomedProductivity(**kwargs)


def load_conditionants_json(path: str | Path | None) -> list[Conditionant]:
    if path is None:
        return []
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    items = data.get("conditionants") if isinstance(data, dict) else data
    if not isinstance(items, list):
        raise ValueError("conditionants-json deve conter lista agregada")
    out: list[Conditionant] = []
    for raw in items:
        if not isinstance(raw, dict):
            continue
        out.append(
            Conditionant(
                recomendacao_id=str(raw.get("recomendacao_id") or raw.get("acao") or "acao"),
                decisao=str(raw.get("decisao") or "pendente"),
                status=str(raw.get("status") or "pendente"),
                prazo=raw.get("prazo"),
                barreira=raw.get("barreira"),
                risco_residual=raw.get("risco_residual"),
                responsavel=None,  # never load personal names from JSON into narrative
                evidencia=raw.get("evidencia"),
                conclusao=raw.get("conclusao"),
            )
        )
    return out


def load_action_counts_json(path: str | Path | None) -> ActionCounts | None:
    if path is None:
        return None
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    payload = data.get("acoes") if isinstance(data, dict) and "acoes" in data else data
    if not isinstance(payload, dict):
        return None
    allowed = {f.name for f in ActionCounts.__dataclass_fields__.values()}  # type: ignore[attr-defined]
    kwargs = {k: int(v) for k, v in payload.items() if k in allowed and v is not None}
    return ActionCounts(**kwargs)


class PerformanceShadowService:
    """Shadow orchestrator: validate → snapshots → IQB → compare → analyze."""

    def __init__(
        self,
        db: Session,
        *,
        thresholds: ThresholdConfig | None = None,
        db_sha256: str | None = None,
    ) -> None:
        if db is None:
            raise ValueError("db é obrigatório")
        self.db = db
        self.thresholds = thresholds or ThresholdConfig()
        self.thresholds.validate()
        self.db_sha256 = db_sha256
        self.canonical = CanonicalSnapshotAdapter(db)
        self.quality = DataQualityAdapter(db)
        self.engine = PerformanceService(self.thresholds, require_flag=False)

    def _validate_tenant(self, client_id: int) -> int:
        if client_id is None or int(client_id) <= 0:
            raise TenantRequiredError("client_id obrigatório")
        cid = int(client_id)
        exists = self.db.query(Client.id).filter(Client.id == cid).first()
        if exists is None:
            raise TenantRequiredError(f"tenant inexistente: {cid}")
        return cid

    def analyze(
        self,
        *,
        client_id: int,
        baseline_inicio: str,
        baseline_fim: str,
        atual_inicio: str,
        atual_fim: str,
        efetivo_trabalhadores: int | None = None,
        productivity: BiomedProductivity | None = None,
        productivity_json: str | Path | None = None,
        conditionants: list[Conditionant] | None = None,
        conditionants_json: str | Path | None = None,
        acoes: ActionCounts | None = None,
        custo_programa: float | None = None,
        custo_hora: float | None = None,
        fonte_custos: str = "nao_informada",
        metas_atingidas: float | None = None,
    ) -> ShadowAnalysisResult:
        cid = self._validate_tenant(client_id)
        b_ini = parse_month(baseline_inicio, field_name="baseline_inicio")
        b_fim = parse_month(baseline_fim, field_name="baseline_fim")
        a_ini = parse_month(atual_inicio, field_name="atual_inicio")
        a_fim = parse_month(atual_fim, field_name="atual_fim")
        if b_ini > b_fim or a_ini > a_fim:
            raise InvalidPeriodError("período início > fim")

        q_base = self.quality.build(cid, b_ini, b_fim)
        q_cur = self.quality.build(cid, a_ini, a_fim)

        base_bundle = self.canonical.build(
            cid,
            b_ini,
            b_fim,
            efetivo_trabalhadores=efetivo_trabalhadores,
            iqb=q_base.iqb,
        )
        cur_bundle = self.canonical.build(
            cid,
            a_ini,
            a_fim,
            efetivo_trabalhadores=efetivo_trabalhadores,
            iqb=q_cur.iqb,
        )

        # Enrich snapshots with quality limitations
        baseline = replace(
            base_bundle.snapshot,
            limitacoes=list(base_bundle.snapshot.limitacoes) + list(q_base.limitacoes),
            iqb=q_base.iqb,
        )
        current = replace(
            cur_bundle.snapshot,
            limitacoes=list(cur_bundle.snapshot.limitacoes) + list(q_cur.limitacoes),
            iqb=q_cur.iqb,
        )

        comparability = assess_comparability(
            baseline_inicio=b_ini,
            baseline_fim=b_fim,
            atual_inicio=a_ini,
            atual_fim=a_fim,
            months_with_data_baseline=base_bundle.months_with_data,
            months_with_data_atual=cur_bundle.months_with_data,
            metodologia_horas_baseline=baseline.metodologia_horas,
            metodologia_horas_atual=current.metodologia_horas,
            cobertura_horas_baseline=baseline.cobertura_horas_registradas,
            cobertura_horas_atual=current.cobertura_horas_registradas,
            max_coverage_diff=self.thresholds.max_hours_coverage_diff,
            require_non_overlap=True,
        )

        prod_mode = "ausente"
        prod = productivity
        if prod is None and productivity_json is not None:
            prod = load_productivity_json(productivity_json)
            prod_mode = "json_agregado"
        elif prod is not None:
            prod_mode = "explicito"
        else:
            # absence: performance score redistributes coverage dimension
            pass

        cond_mode = "ausente"
        conds = conditionants
        if conds is None and conditionants_json is not None:
            conds = load_conditionants_json(conditionants_json)
            cond_mode = "json_agregado"
        elif conds is not None:
            cond_mode = "explicito"
        else:
            conds = []

        window_lims = list(comparability.limitations)
        descriptive_only = comparability.mode in {"bloqueada", "descritiva"}
        if descriptive_only:
            window_lims.append(
                "comparabilidade_insuficiente — eficácia integral não classificada; "
                "modo descritivo/seguro"
            )
            # Force insufficient evidence path via limitations + incomplete completeness
            baseline = replace(
                baseline,
                completude_periodo=min(baseline.completude_periodo or 0.0, 0.5),
                limitacoes=list(baseline.limitacoes) + window_lims,
            )
            current = replace(
                current,
                completude_periodo=min(current.completude_periodo or 0.0, 0.5),
                limitacoes=list(current.limitacoes) + window_lims,
            )

        months_found = {
            "90_dias": min(current.meses_com_dados, 3),
            "baseline": baseline.meses_com_dados,
            "atual": current.meses_com_dados,
        }

        analysis = self.engine.analyze(
            client_id=cid,
            baseline=baseline,
            current=current,
            productivity=prod,
            conditionants=conds,
            reference_end=a_fim,
            months_found_by_window=months_found,
            custo_programa=custo_programa,
            custo_hora=custo_hora,
            fonte_custos=fonte_custos,
            acoes=acoes,
            metas_atingidas=metas_atingidas,
        )

        # If not comparable for integral efficacy, downgrade effectiveness code in output
        eff = dict(analysis.effectiveness)
        if descriptive_only:
            eff = {
                **eff,
                "codigo": "SEM_EVIDENCIA_SUFICIENTE",
                "rotulo": "Sem evidência suficiente (janelas não comparáveis)",
                "limitacoes": list(eff.get("limitacoes") or []) + window_lims,
                "hipoteses": list(eff.get("hipoteses") or [])
                + ["hipotese: leitura descritiva apenas — sem classificação integral"],
            }

        narrative = analysis.narrative or {}
        limitations = list(analysis.limitations or [])
        limitations.extend(window_lims)
        limitations.append(
            "produtividade_biomed_nao_integrada_ao_banco — "
            "usar ausência, fixture ou JSON agregado explícito"
        )
        limitations.append(
            "associacao_temporal_nao_comprova_causalidade"
        )
        limitations.append(
            "dado_mensal_nao_equivale_precisao_diaria"
        )

        result = ShadowAnalysisResult(
            client_id=cid,
            engine_version=analysis.engine_version or ENGINE_VERSION,
            adapter_version=SHADOW_ADAPTER_VERSION,
            baseline={
                "periodo_inicio": b_ini,
                "periodo_fim": b_fim,
                "metrics": analysis.baseline_metrics,
                "months_with_data": base_bundle.months_with_data,
            },
            atual={
                "periodo_inicio": a_ini,
                "periodo_fim": a_fim,
                "metrics": analysis.current_metrics,
                "months_with_data": cur_bundle.months_with_data,
            },
            completude={
                "baseline": baseline.completude_periodo,
                "atual": current.completude_periodo,
                "baseline_meses_com_dados": baseline.meses_com_dados,
                "atual_meses_com_dados": current.meses_com_dados,
            },
            comparabilidade=comparability.to_dict(),
            iqb={
                "baseline": _iqb_public(q_base),
                "atual": _iqb_public(q_cur),
            },
            metrics={
                "baseline": baseline.to_dict(),
                "atual": current.to_dict(),
            },
            deltas=analysis.deltas,
            effectiveness=eff,
            confidence={
                "valor": eff.get("confianca"),
                "componentes": eff.get("confianca_componentes") or {},
            },
            executive_score=analysis.executive_score,
            recommendations=analysis.recommendations,
            roi=analysis.roi,
            fatos=list(narrative.get("fatos") or []),
            interpretacoes=list(narrative.get("interpretacoes") or []),
            hipoteses=list(narrative.get("hipoteses") or []),
            limitacoes=limitations,
            thresholds_used=analysis.thresholds_used,
            db_sha256=self.db_sha256,
            productivity_mode=prod_mode,
            conditionants_mode=cond_mode,
            descriptive_only=descriptive_only,
            competence_equivalents=document_competence_equivalents(),
        )
        payload = result.to_dict()
        assert_no_pii(payload)
        return result


def _iqb_public(q: QualityBundle) -> dict[str, Any]:
    return {
        "iqb": q.iqb,
        "classificacao": q.classificacao,
        "dimensoes": q.dimensoes,
        "status_dimensoes": q.status_dimensoes,
        "pesos_originais": q.pesos_originais,
        "pesos_efetivos": q.pesos_efetivos,
        "metodologia_redistribuicao": q.metodologia_redistribuicao,
        "limitacoes": q.limitacoes,
        "qualidade_horas": {
            k: v
            for k, v in (q.qualidade_horas or {}).items()
            if k
            in {
                "eventos_com_horas_registradas",
                "eventos_com_horas_estimaveis",
                "eventos_sem_possibilidade_estimativa",
                "cobertura_registrada_pct",
                "classificacao",
                "divergencia_dias_jornada_vs_registradas",
            }
        },
        "qualidade_identidade": q.qualidade_identidade,
        "periodos_invalidos": q.periodos_invalidos,
        "possiveis_multiplos_uploads": q.possiveis_multiplos_uploads,
        "eventos_analisados": q.eventos_analisados,
    }


__all__ = [
    "SHADOW_ADAPTER_VERSION",
    "ShadowAnalysisResult",
    "PerformanceShadowService",
    "load_productivity_json",
    "load_conditionants_json",
    "load_action_counts_json",
]
