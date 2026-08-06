"""Orchestrator: baseline → effectiveness → productivity → ROI → score → narrative."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from backend.performance import ENGINE_VERSION, is_performance_engine_enabled
from backend.performance.baseline_service import BaselineService
from backend.performance.effectiveness_service import EffectivenessService
from backend.performance.exceptions import FeatureDisabledError, TenantRequiredError
from backend.performance.privacy import assert_no_pii
from backend.performance.productivity_service import ProductivityService
from backend.performance.recommendation_engine import RecommendationEngine
from backend.performance.roi_service import RoiService
from backend.performance.schemas import (
    BiomedProductivity,
    Conditionant,
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
        end = reference_end or current.periodo_fim
        windows = self.baseline_svc.windows_ending_at(
            reference_end=end,
            months_found_by_window=months_found_by_window,
        )
        # Compare 90-day style windows by default for limitations
        w90 = next((w for w in windows if w.nome == "90_dias"), windows[0])
        w_lims = []
        if w90.status != "completo":
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
        )
        layers = self.prod_svc.separate_layers(prod, outcome_summary=eff.rotulo)
        indicators = self._build_indicators(
            baseline,
            current,
            prod,
            cov_ind,
            acoes_propostas=acoes_propostas,
            acoes_aprovadas=acoes_aprovadas,
            acoes_executadas=acoes_executadas,
            acoes_pendentes=acoes_pendentes,
            metas_atingidas=metas_atingidas,
            barreiras=barreiras,
            recomendacoes_recusadas_ou_adiadas=recomendacoes_recusadas_ou_adiadas,
        )
        score = self.executive_score(
            deltas=deltas,
            effectiveness_code=eff.codigo,
            coverage=float(cov_val) if cov_val is not None else None,
            iqb=current.iqb,
            acoes_executadas=acoes_executadas,
            acoes_propostas=acoes_propostas,
            metas_atingidas=metas_atingidas,
            conditionants=conds,
        )
        narrative = self._narrative(eff, deltas, conds, recs, w_lims)

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
        acoes_executadas: int,
        acoes_propostas: int,
        metas_atingidas: float | None,
        conditionants: list[Conditionant],
    ) -> dict[str, Any]:
        """Composable executive score — never ranks workers."""
        thr = self.thresholds

        def dim_from_delta(d: float | None) -> float:
            if d is None:
                return 50.0
            # improvement (negative delta for bad outcomes) → higher score
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
            return 50.0

        s_freq = dim_from_delta(deltas.get("eventos") or deltas.get("frequencia"))
        s_sev = dim_from_delta(deltas.get("dias_perdidos") or deltas.get("gravidade"))
        s_rec = dim_from_delta(deltas.get("recorrencia"))
        s_cov = 50.0 if coverage is None else max(0.0, min(100.0, coverage * 100.0))
        if acoes_propostas > 0:
            s_exec = 100.0 * (acoes_executadas / float(acoes_propostas))
        else:
            s_exec = 50.0
        s_goals = 50.0 if metas_atingidas is None else max(0.0, min(100.0, metas_atingidas * 100.0))
        s_qual = 50.0 if iqb is None else max(0.0, min(100.0, float(iqb)))
        delayed = sum(
            1
            for c in conditionants
            if c.decisao in {"adiada", "recusada"}
        )
        s_cond = 80.0 if not conditionants else max(20.0, 100.0 - 20.0 * delayed)

        dims = {
            "evolucao_frequencia": round(s_freq, thr.round_digits),
            "evolucao_severidade": round(s_sev, thr.round_digits),
            "recorrencia": round(s_rec, thr.round_digits),
            "cobertura_assistencial": round(s_cov, thr.round_digits),
            "execucao_acoes": round(s_exec, thr.round_digits),
            "atingimento_metas": round(s_goals, thr.round_digits),
            "qualidade_dados": round(s_qual, thr.round_digits),
            "condicionantes_empresa": round(s_cond, thr.round_digits),
        }
        total = (
            dims["evolucao_frequencia"] * thr.w_freq
            + dims["evolucao_severidade"] * thr.w_sev
            + dims["recorrencia"] * thr.w_rec
            + dims["cobertura_assistencial"] * thr.w_cov
            + dims["execucao_acoes"] * thr.w_exec
            + dims["atingimento_metas"] * thr.w_goals
            + dims["qualidade_dados"] * thr.w_quality
            + dims["condicionantes_empresa"] * thr.w_cond
        ) / 100.0
        return {
            "score": round(total, thr.round_digits),
            "dimensoes": dims,
            "pesos": {
                "frequencia": thr.w_freq,
                "severidade": thr.w_sev,
                "recorrencia": thr.w_rec,
                "cobertura": thr.w_cov,
                "execucao": thr.w_exec,
                "metas": thr.w_goals,
                "qualidade": thr.w_quality,
                "condicionantes": thr.w_cond,
            },
            "effectiveness_code": effectiveness_code,
            "ranking_trabalhadores": False,
            "uso": "visao_executiva_agregada",
        }

    def _build_indicators(
        self,
        baseline: MetricSnapshot,
        current: MetricSnapshot,
        prod: BiomedProductivity,
        cov_ind: IndicatorValue,
        **actions: Any,
    ) -> list[IndicatorValue]:
        def snap_ind(sid: str, val: Any, unidade: str, periodo: str, lims: list[str] | None = None):
            q = QualityLabel.DISPONIVEL.value if val is not None else QualityLabel.INDISPONIVEL.value
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
        inds = [
            snap_ind("eventos", current.eventos, "count", periodo),
            snap_ind("trabalhadores_unicos", current.trabalhadores_unicos, "count", periodo),
            snap_ind("dias_perdidos", current.dias_perdidos, "dias", periodo),
            snap_ind("horas_perdidas_registradas", current.horas_perdidas_registradas, "horas", periodo),
            snap_ind("horas_perdidas_estimadas", current.horas_perdidas_estimadas, "horas", periodo),
            snap_ind("duracao_media", current.duracao_media, "dias", periodo),
            snap_ind("frequencia", current.frequencia, "ratio", periodo),
            snap_ind("gravidade", current.gravidade, "index", periodo),
            snap_ind("recorrencia", current.recorrencia, "ratio", periodo),
            snap_ind("afastamentos_longos", current.afastamentos_longos, "count", periodo),
            snap_ind("eventos_por_100", current.eventos_por_100, "por_100", periodo, ["requer_headcount"] if current.headcount is None else []),
            snap_ind("dias_por_trabalhador", current.dias_por_trabalhador, "dias", periodo),
            snap_ind("horas_por_100", current.horas_por_100, "horas_por_100", periodo),
            snap_ind("iqb", current.iqb, "score", periodo),
            snap_ind("setores_criticos_n", len(current.setores_criticos), "count", periodo),
            snap_ind("grupos_cid_n", len(current.grupos_cid), "count", periodo),
            cov_ind,
            snap_ind("acoes_propostas", actions.get("acoes_propostas"), "count", periodo),
            snap_ind("acoes_aprovadas", actions.get("acoes_aprovadas"), "count", periodo),
            snap_ind("acoes_executadas", actions.get("acoes_executadas"), "count", periodo),
            snap_ind("acoes_pendentes", actions.get("acoes_pendentes"), "count", periodo),
            snap_ind("metas_atingidas", actions.get("metas_atingidas"), "ratio", periodo),
            snap_ind("barreiras_registradas", actions.get("barreiras"), "count", periodo),
            snap_ind(
                "recomendacoes_recusadas_ou_adiadas",
                actions.get("recomendacoes_recusadas_ou_adiadas"),
                "count",
                periodo,
            ),
            self.prod_svc.attendance_rate(prod),
        ]
        return inds

    def _narrative(self, eff, deltas, conds, recs, w_lims) -> dict[str, list[str]]:
        fatos = [
            f"classificacao_observada={eff.codigo}",
            *[f"delta_{k}={v}" for k, v in deltas.items() if v is not None],
        ]
        interpretacoes = [
            eff.rotulo,
            *[f"criterio:{c}" for c in eff.criterios_acionados],
        ]
        hipoteses = [
            "mudancas_podem_refletir_sazonalidade_ou_decisoes_externas",
            "producao_biomed_nao_implica_causalidade_automatica",
        ]
        if conds:
            delayed = [c for c in conds if c.decisao in {"adiada", "recusada"}]
            if delayed:
                interpretacoes.append(
                    "resultado_parcial_possivel_porque_recomendacoes_estruturais_permaneceram_adiadas_ou_recusadas"
                )
                hipoteses.append(
                    "se_recomendacoes_estruturais_fossem_executadas_resultado_poderia_diferir"
                )
        limitacoes = list(dict.fromkeys(list(eff.limitacoes) + list(w_lims)))
        recomendacoes = [f"{r.id}:{r.descricao}" for r in recs]
        return {
            "fatos": fatos,
            "interpretacoes": interpretacoes,
            "hipoteses": hipoteses,
            "limitacoes": limitacoes,
            "recomendacoes": recomendacoes,
        }
