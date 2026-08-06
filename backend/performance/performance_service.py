"""Orchestrator: baseline → effectiveness → productivity → ROI → score → narrative."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from backend.performance import ENGINE_VERSION, is_performance_engine_enabled
from backend.performance.baseline_service import BaselineService
from backend.performance.confidence import redistribute_score_weights
from backend.performance.effectiveness_service import EffectivenessService, _first_not_none
from backend.performance.exceptions import FeatureDisabledError, TenantRequiredError
from backend.performance.privacy import assert_no_pii
from backend.performance.productivity_service import ProductivityService
from backend.performance.recommendation_engine import RecommendationEngine
from backend.performance.roi_service import RoiService
from backend.performance.schemas import (
    ActionCounts,
    BiomedProductivity,
    Conditionant,
    DimensionStatus,
    IndicatorValue,
    MetricSnapshot,
    PerformanceAnalysis,
    QualityLabel,
    ThresholdConfig,
)


class PerformanceService:
    """Shadow-capable BioMed Performance Engine facade."""

    def __init__(
        self,
        thresholds: ThresholdConfig | None = None,
        *,
        require_flag: bool = False,
    ) -> None:
        self.thresholds = thresholds or ThresholdConfig()
        self.thresholds.validate()
        self.require_flag = require_flag
        self.baseline_svc = BaselineService(self.thresholds)
        self.effect_svc = EffectivenessService(self.thresholds)
        self.prod_svc = ProductivityService(self.thresholds)
        self.roi_svc = RoiService(self.thresholds)
        self.rec_engine = RecommendationEngine(self.thresholds)

    def analyze(
        self,
        *,
        client_id: int,
        baseline: MetricSnapshot,
        current: MetricSnapshot,
        productivity: BiomedProductivity | None = None,
        conditionants: list[Conditionant] | None = None,
        reference_end: str | None = None,
        months_found_by_window: dict[str, int] | None = None,
        custo_programa: float | None = None,
        custo_hora: float | None = None,
        usar_horas_estimadas: bool = False,
        fonte_custos: str = "nao_informada",
        acoes: ActionCounts | None = None,
        acoes_propostas: int = 0,
        acoes_aprovadas: int = 0,
        acoes_executadas: int = 0,
        acoes_pendentes: int = 0,
        metas_atingidas: float | None = None,
        barreiras: int = 0,
        recomendacoes_recusadas_ou_adiadas: int = 0,
    ) -> PerformanceAnalysis:
        if self.require_flag and not is_performance_engine_enabled():
            raise FeatureDisabledError("ENABLE_BIOMED_PERFORMANCE_ENGINE is false")
        if client_id is None or int(client_id) <= 0:
            raise TenantRequiredError("client_id obrigatório")
        if baseline.client_id != client_id or current.client_id != client_id:
            raise TenantRequiredError("tenant mismatch between snapshots")

        prod = productivity or BiomedProductivity()
        conds = conditionants or []
        action_counts = acoes or ActionCounts(
            propostas=acoes_propostas,
            aprovadas=acoes_aprovadas,
            executadas=acoes_executadas,
            pendentes=acoes_pendentes,
            recusadas=recomendacoes_recusadas_ou_adiadas,
        )
        end = reference_end or current.periodo_fim
        windows = self.baseline_svc.windows_ending_at(
            reference_end=end,
            months_found_by_window=months_found_by_window,
        )
        w90 = next((w for w in windows if w.nome == "90_dias"), windows[0])
        w_lims: list[str] = []
        janelas_completas = w90.status == "completo"
        if not janelas_completas:
            w_lims.append(f"periodo_{w90.status}")

        cov_ind = self.prod_svc.coverage(prod)
        cov_val = cov_ind.valor if isinstance(cov_ind.valor, (int, float)) else None

        eff = self.effect_svc.classify(
            baseline=baseline,
            current=current,
            window_limitations=w_lims,
            conditionants=conds,
            assistential_coverage=float(cov_val) if cov_val is not None else None,
        )
        deltas = self.effect_svc.deltas(baseline, current)
        recs = self.rec_engine.recommend(
            baseline=baseline,
            current=current,
            assistential_coverage=float(cov_val) if cov_val is not None else None,
        )
        roi = self.roi_svc.compute(
            baseline=baseline,
            current=current,
            custo_programa=custo_programa,
            custo_hora=custo_hora,
            usar_horas_estimadas=usar_horas_estimadas,
            fonte_custos=fonte_custos,
            periodos_equivalentes=True,
            janelas_completas=janelas_completas,
        )
        layers = self.prod_svc.separate_layers(prod, outcome_summary=eff.rotulo)
        indicators = self._build_indicators(
            baseline,
            current,
            prod,
            cov_ind,
            action_counts=action_counts,
            metas_atingidas=metas_atingidas,
            barreiras=barreiras,
        )
        score = self.executive_score(
            deltas=deltas,
            effectiveness_code=eff.codigo,
            coverage=float(cov_val) if cov_val is not None else None,
            iqb=current.iqb,
            action_counts=action_counts,
            metas_atingidas=metas_atingidas,
            conditionants=conds,
            headcount_missing=baseline.headcount is None and current.headcount is None,
        )
        narrative = self._narrative(eff, deltas, conds, recs, w_lims, baseline, current)

        result = PerformanceAnalysis(
            client_id=client_id,
            engine_version=ENGINE_VERSION,
            baseline_windows=[w.to_dict() for w in windows],
            baseline_metrics=baseline.to_dict(),
            current_metrics=current.to_dict(),
            deltas=deltas,
            indicators=[i.to_dict() for i in indicators],
            productivity=layers["producao"],
            coverage=layers["cobertura"],
            effectiveness=eff.to_dict(),
            conditionants=[c.to_dict() for c in conds],
            recommendations=[r.to_dict() for r in recs],
            roi=roi.to_dict(),
            executive_score=score,
            narrative=narrative,
            thresholds_used=asdict(self.thresholds),
            limitations=list(dict.fromkeys(eff.limitacoes + w_lims + list(roi.limitacoes))),
        )
        assert_no_pii(result.to_dict())
        return result

    def executive_score(
        self,
        *,
        deltas: dict[str, float | None],
        effectiveness_code: str,
        coverage: float | None,
        iqb: float | None,
        action_counts: ActionCounts,
        metas_atingidas: float | None,
        conditionants: list[Conditionant],
        headcount_missing: bool = False,
    ) -> dict[str, Any]:
        """Score with evaluated/unavailable dimensions and effective weight redistribution."""
        thr = self.thresholds
        original = thr.weight_map()
        status: dict[str, str] = {}
        values: dict[str, float | None] = {}

        def dim_from_delta(d: float | None) -> float | None:
            if d is None:
                return None
            if d <= -thr.strong_improvement:
                return 90.0
            if d <= -thr.material_change:
                return 75.0
            if abs(d) <= thr.stability_band:
                return 60.0
            if d >= thr.strong_improvement:
                return 20.0
            if d >= thr.material_change:
                return 35.0
            return 55.0

        # Frequency: prefer eventos (absolute); population frequencia only if present
        d_freq = _first_not_none(deltas.get("eventos"), deltas.get("frequencia"))
        if headcount_missing and deltas.get("eventos") is None:
            values["evolucao_frequencia"] = None
            status["evolucao_frequencia"] = DimensionStatus.INDISPONIVEL.value
        else:
            values["evolucao_frequencia"] = dim_from_delta(d_freq)
            status["evolucao_frequencia"] = (
                DimensionStatus.AVALIADA.value
                if values["evolucao_frequencia"] is not None
                else DimensionStatus.NAO_AVALIADA.value
            )

        d_sev = _first_not_none(deltas.get("dias_perdidos"), deltas.get("gravidade"))
        values["evolucao_severidade"] = dim_from_delta(d_sev)
        status["evolucao_severidade"] = (
            DimensionStatus.AVALIADA.value
            if values["evolucao_severidade"] is not None
            else DimensionStatus.NAO_AVALIADA.value
        )

        values["recorrencia"] = dim_from_delta(deltas.get("recorrencia"))
        status["recorrencia"] = (
            DimensionStatus.AVALIADA.value
            if values["recorrencia"] is not None
            else DimensionStatus.NAO_AVALIADA.value
        )

        if coverage is None:
            values["cobertura_assistencial"] = None
            status["cobertura_assistencial"] = DimensionStatus.INDISPONIVEL.value
        else:
            values["cobertura_assistencial"] = max(0.0, min(100.0, coverage * 100.0))
            status["cobertura_assistencial"] = DimensionStatus.AVALIADA.value

        denom = action_counts.aprovadas_aplicaveis()
        if denom <= 0:
            values["execucao_acoes"] = None
            status["execucao_acoes"] = DimensionStatus.NAO_AVALIADA.value
        else:
            values["execucao_acoes"] = 100.0 * (
                action_counts.executadas / float(denom)
            )
            status["execucao_acoes"] = DimensionStatus.AVALIADA.value

        if metas_atingidas is None:
            values["atingimento_metas"] = None
            status["atingimento_metas"] = DimensionStatus.INDISPONIVEL.value
        else:
            values["atingimento_metas"] = max(0.0, min(100.0, metas_atingidas * 100.0))
            status["atingimento_metas"] = DimensionStatus.AVALIADA.value

        if iqb is None:
            values["qualidade_dados"] = None
            status["qualidade_dados"] = DimensionStatus.INDISPONIVEL.value
        else:
            values["qualidade_dados"] = max(0.0, min(100.0, float(iqb)))
            status["qualidade_dados"] = DimensionStatus.AVALIADA.value

        if not conditionants:
            values["condicionantes_empresa"] = None
            status["condicionantes_empresa"] = DimensionStatus.NAO_APLICAVEL.value
        else:
            delayed = sum(1 for c in conditionants if c.decisao in {"adiada", "recusada"})
            values["condicionantes_empresa"] = max(20.0, 100.0 - 20.0 * delayed)
            status["condicionantes_empresa"] = DimensionStatus.AVALIADA.value

        unavailable = {
            k
            for k, st in status.items()
            if st
            in {
                DimensionStatus.NAO_AVALIADA.value,
                DimensionStatus.INDISPONIVEL.value,
                DimensionStatus.NAO_APLICAVEL.value,
            }
        }
        evaluated = [k for k in original if k not in unavailable]
        not_evaluated = sorted(unavailable)
        efetivos, metodo = redistribute_score_weights(original, unavailable)
        weight_coverage = (
            sum(original[k] for k in evaluated) / 100.0 if original else 0.0
        )

        if weight_coverage + 1e-9 < thr.min_score_coverage or not evaluated:
            return {
                "score": None,
                "status": "INSUFICIENTE",
                "cobertura_score": round(weight_coverage, thr.round_digits),
                "dimensoes": {
                    k: {
                        "valor": None
                        if values[k] is None
                        else round(values[k], thr.round_digits),
                        "status": status[k],
                    }
                    for k in original
                },
                "pesos_originais": original,
                "pesos_efetivos": efetivos,
                "dimensoes_avaliadas": evaluated,
                "dimensoes_nao_avaliadas": not_evaluated,
                "metodologia_redistribuicao": metodo,
                "effectiveness_code": effectiveness_code,
                "ranking_trabalhadores": False,
                "uso": "visao_executiva_agregada",
                "execucao_denominador": "aprovadas_aplicaveis",
                "acoes": action_counts.to_dict(),
            }

        total = sum(
            (values[k] or 0.0) * (efetivos.get(k, 0.0) / 100.0) for k in evaluated
        )
        return {
            "score": round(total, thr.round_digits),
            "status": "OK",
            "cobertura_score": round(weight_coverage, thr.round_digits),
            "dimensoes": {
                k: {
                    "valor": None
                    if values[k] is None
                    else round(values[k], thr.round_digits),
                    "status": status[k],
                }
                for k in original
            },
            "pesos_originais": original,
            "pesos_efetivos": efetivos,
            "dimensoes_avaliadas": evaluated,
            "dimensoes_nao_avaliadas": not_evaluated,
            "metodologia_redistribuicao": metodo,
            "effectiveness_code": effectiveness_code,
            "ranking_trabalhadores": False,
            "uso": "visao_executiva_agregada",
            "execucao_denominador": "aprovadas_aplicaveis",
            "acoes": action_counts.to_dict(),
        }

    def _build_indicators(
        self,
        baseline: MetricSnapshot,
        current: MetricSnapshot,
        prod: BiomedProductivity,
        cov_ind: IndicatorValue,
        *,
        action_counts: ActionCounts,
        metas_atingidas: float | None,
        barreiras: int,
    ) -> list[IndicatorValue]:
        def snap_ind(
            sid: str,
            val: Any,
            unidade: str,
            periodo: str,
            lims: list[str] | None = None,
            qualidade: str | None = None,
        ):
            q = qualidade or (
                QualityLabel.DISPONIVEL.value
                if val is not None
                else QualityLabel.INDISPONIVEL.value
            )
            if sid.startswith("horas_perdidas_estimadas") and val is not None:
                q = QualityLabel.ESTIMADO.value
            return IndicatorValue(
                id=sid,
                valor=val,
                unidade=unidade,
                fonte=current.fonte,
                metodologia="canonical_or_fixture_snapshot",
                qualidade=q,
                periodo=periodo,
                limitacoes=lims or [],
            )

        periodo = f"{current.periodo_inicio}:{current.periodo_fim}"
        hc_missing = current.headcount is None
        pop_lims = ["requer_headcount", "metrica_dependente_headcount"] if hc_missing else []
        inds = [
            snap_ind("eventos", current.eventos, "count", periodo),
            snap_ind("trabalhadores_unicos", current.trabalhadores_unicos, "count", periodo),
            snap_ind("dias_perdidos", current.dias_perdidos, "dias", periodo),
            snap_ind(
                "horas_perdidas_registradas",
                current.horas_perdidas_registradas,
                "horas",
                periodo,
            ),
            snap_ind(
                "horas_perdidas_estimadas",
                current.horas_perdidas_estimadas,
                "horas",
                periodo,
            ),
            snap_ind("duracao_media", current.duracao_media, "dias", periodo),
            snap_ind(
                "frequencia",
                None if hc_missing else current.frequencia,
                "ratio",
                periodo,
                pop_lims,
                QualityLabel.INDISPONIVEL.value if hc_missing else None,
            ),
            snap_ind("gravidade", current.gravidade, "index", periodo),
            snap_ind("recorrencia", current.recorrencia, "ratio", periodo),
            snap_ind("afastamentos_longos", current.afastamentos_longos, "count", periodo),
            snap_ind(
                "eventos_por_100",
                None if hc_missing else current.eventos_por_100,
                "por_100",
                periodo,
                pop_lims,
                QualityLabel.INDISPONIVEL.value if hc_missing else None,
            ),
            snap_ind("dias_por_trabalhador", current.dias_por_trabalhador, "dias", periodo),
            snap_ind(
                "horas_por_100",
                None if hc_missing else current.horas_por_100,
                "horas_por_100",
                periodo,
                pop_lims,
                QualityLabel.INDISPONIVEL.value if hc_missing else None,
            ),
            snap_ind("iqb", current.iqb, "score", periodo),
            snap_ind("setores_criticos_n", len(current.setores_criticos), "count", periodo),
            snap_ind("grupos_cid_n", len(current.grupos_cid), "count", periodo),
            cov_ind,
            snap_ind("acoes_propostas", action_counts.propostas, "count", periodo),
            snap_ind("acoes_aprovadas", action_counts.aprovadas, "count", periodo),
            snap_ind(
                "acoes_aprovadas_aplicaveis",
                action_counts.aprovadas_aplicaveis(),
                "count",
                periodo,
            ),
            snap_ind("acoes_executadas", action_counts.executadas, "count", periodo),
            snap_ind("acoes_concluidas", action_counts.concluidas, "count", periodo),
            snap_ind("acoes_canceladas", action_counts.canceladas, "count", periodo),
            snap_ind("acoes_recusadas", action_counts.recusadas, "count", periodo),
            snap_ind("acoes_adiadas", action_counts.adiadas, "count", periodo),
            snap_ind("acoes_pendentes", action_counts.pendentes, "count", periodo),
            snap_ind("metas_atingidas", metas_atingidas, "ratio", periodo),
            snap_ind("barreiras_registradas", barreiras, "count", periodo),
            self.prod_svc.attendance_rate(prod),
        ]
        return inds

    def _narrative(
        self, eff, deltas, conds, recs, w_lims, baseline, current
    ) -> dict[str, list[str]]:
        # Facts: observed numbers only — not classification labels as "facts of causality"
        fatos = [
            f"eventos_baseline={baseline.eventos}",
            f"eventos_atual={current.eventos}",
            f"dias_baseline={baseline.dias_perdidos}",
            f"dias_atual={current.dias_perdidos}",
            *[f"delta_{k}={v}" for k, v in deltas.items() if v is not None],
            f"codigo_classificacao_tecnica={eff.codigo}",
        ]
        interpretacoes = [
            f"leitura_tecnica:{eff.rotulo}",
            *[f"criterio:{c}" for c in eff.criterios_acionados],
            "interpretacao_nao_afirma_causalidade",
        ]
        hipoteses = [
            "hipotese:mudancas_podem_refletir_sazonalidade_ou_decisoes_externas",
            "hipotese:producao_biomed_nao_implica_causalidade_automatica",
            *[f"hipotese:{h}" for h in (eff.hipoteses or [])],
        ]
        if conds:
            delayed = [c for c in conds if c.decisao in {"adiada", "recusada"}]
            if delayed:
                interpretacoes.append(
                    "leitura_condicionada_a_recomendacoes_estruturais_adiadas_ou_recusadas"
                )
                hipoteses.append(
                    "hipotese:se_recomendacoes_estruturais_fossem_executadas_resultado_poderia_diferir"
                )
        limitacoes = list(dict.fromkeys(list(eff.limitacoes) + list(w_lims)))
        recomendacoes = [
            f"{r.id}:{r.descricao}:requer_validacao_humana"
            for r in recs
        ]
        return {
            "fatos": fatos,
            "interpretacoes": interpretacoes,
            "hipoteses": hipoteses,
            "limitacoes": limitacoes,
            "recomendacoes": recomendacoes,
        }
