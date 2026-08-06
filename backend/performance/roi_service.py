"""ROI structure — observed / estimated / not calculable with comparability gates."""

from __future__ import annotations

from typing import Any

from backend.performance.confidence import compute_confidence
from backend.performance.schemas import MetricSnapshot, RoiKind, RoiResult, ThresholdConfig

ROI_FORMULA = (
    "((custo_evitado_ou_adicional - custo_total_programa) / custo_total_programa) * 100"
)
CUSTO_TOTAL_DEF = "custo_total_programa = custo_programa + custos_implementacao"
CUSTO_DELTA_DEF = (
    "delta_custo_horas = (horas_baseline - horas_atuais) * custo_hora_ajustado; "
    "se positivo → custo_evitado; se negativo → custo_adicional_estimado"
)


class RoiService:
    def __init__(self, thresholds: ThresholdConfig | None = None) -> None:
        self.thresholds = thresholds or ThresholdConfig()

    def compute(
        self,
        *,
        baseline: MetricSnapshot,
        current: MetricSnapshot,
        custo_programa: float | None,
        custo_hora: float | None,
        encargos_factor: float = 1.0,
        custos_implementacao: float = 0.0,
        usar_horas_estimadas: bool = False,
        fonte_custos: str = "nao_informada",
        periodos_equivalentes: bool = True,
        janelas_completas: bool = True,
    ) -> RoiResult:
        thr = self.thresholds
        premissas: dict[str, Any] = {
            "formula": ROI_FORMULA,
            "definicao_custo_total": CUSTO_TOTAL_DEF,
            "definicao_delta_horas": CUSTO_DELTA_DEF,
            "custo_hora": custo_hora,
            "encargos_factor": encargos_factor,
            "custos_implementacao": custos_implementacao,
            "custo_programa": custo_programa,
            "usar_horas_estimadas": usar_horas_estimadas,
            "fonte_custos": fonte_custos,
            "metodologia_horas_baseline": baseline.metodologia_horas,
            "metodologia_horas_atual": current.metodologia_horas,
            "cobertura_horas_registradas_baseline": baseline.cobertura_horas_registradas,
            "cobertura_horas_registradas_atual": current.cobertura_horas_registradas,
            "cobertura_horas_estimadas_baseline": baseline.cobertura_horas_estimadas,
            "cobertura_horas_estimadas_atual": current.cobertura_horas_estimadas,
            "completude_periodo_baseline": baseline.completude_periodo,
            "completude_periodo_atual": current.completude_periodo,
            "periodos_equivalentes": periodos_equivalentes,
            "janelas_completas": janelas_completas,
        }
        lims: list[str] = []

        if custo_programa is None or custo_programa <= 0:
            return RoiResult(
                kind=RoiKind.ROI_NAO_CALCULAVEL.value,
                valor=None,
                premissas=premissas,
                confianca=0.0,
                limitacoes=["custo_programa_zero_ou_ausente"],
            )
        if custo_hora is None or custo_hora < 0:
            return RoiResult(
                kind=RoiKind.ROI_NAO_CALCULAVEL.value,
                valor=None,
                premissas=premissas,
                confianca=0.0,
                limitacoes=["custo_hora_ausente"],
            )

        custo_total_programa = custo_programa + custos_implementacao
        premissas["custo_total_programa"] = custo_total_programa
        if custo_total_programa <= 0:
            return RoiResult(
                kind=RoiKind.ROI_NAO_CALCULAVEL.value,
                valor=None,
                premissas=premissas,
                confianca=0.0,
                limitacoes=["custo_total_programa_zero"],
            )

        base_reg = baseline.horas_perdidas_registradas
        cur_reg = current.horas_perdidas_registradas
        base_est = baseline.horas_perdidas_estimadas
        cur_est = current.horas_perdidas_estimadas

        observed_ok = self._observed_comparable(
            baseline, current, thr, periodos_equivalentes, janelas_completas, lims
        )

        if not usar_horas_estimadas and observed_ok and base_reg is not None and cur_reg is not None:
            h_base, h_cur = base_reg, cur_reg
            kind = RoiKind.ROI_OBSERVADO
        elif usar_horas_estimadas or not observed_ok:
            if base_reg is None and base_est is None:
                return RoiResult(
                    kind=RoiKind.ROI_NAO_CALCULAVEL.value,
                    valor=None,
                    premissas=premissas,
                    confianca=0.0,
                    limitacoes=lims + ["horas_ausentes"],
                )
            if not observed_ok and not usar_horas_estimadas:
                # Downgrade path: try estimated if data exists, else non-calculable
                if (base_reg is not None or base_est is not None) and (
                    cur_reg is not None or cur_est is not None
                ):
                    kind = RoiKind.ROI_ESTIMADO
                    lims.append("rebaixado_de_observado_por_comparabilidade")
                    premissas["aviso"] = "ROI estimado — não afirmar economia real"
                    h_base = (base_reg or 0.0) + (base_est or 0.0)
                    h_cur = (cur_reg or 0.0) + (cur_est or 0.0)
                else:
                    return RoiResult(
                        kind=RoiKind.ROI_NAO_CALCULAVEL.value,
                        valor=None,
                        premissas=premissas,
                        confianca=0.0,
                        limitacoes=lims + ["comparabilidade_insuficiente"],
                    )
            else:
                kind = RoiKind.ROI_ESTIMADO
                lims.append("economia_estimada_nao_confundir_com_real")
                premissas["aviso"] = "ROI estimado — não afirmar economia real"
                h_base = (base_reg or 0.0) + (base_est or 0.0)
                h_cur = (cur_reg or 0.0) + (cur_est or 0.0)
        else:
            return RoiResult(
                kind=RoiKind.ROI_NAO_CALCULAVEL.value,
                valor=None,
                premissas=premissas,
                confianca=0.0,
                limitacoes=lims + ["horas_registradas_ausentes"],
            )

        custo_hora_adj = custo_hora * encargos_factor
        delta_custo = (h_base - h_cur) * custo_hora_adj
        if delta_custo >= 0:
            premissas["custo_evitado"] = round(delta_custo, 4)
            premissas["custo_adicional_estimado"] = None
        else:
            premissas["custo_evitado"] = None
            premissas["custo_adicional_estimado"] = round(abs(delta_custo), 4)
            lims.append("horas_atuais_maiores_que_baseline")

        # Formula uses signed delta as "custo_evitado_ou_adicional"
        roi = ((delta_custo - custo_total_programa) / custo_total_programa) * 100.0
        premissas["horas_baseline"] = h_base
        premissas["horas_atuais"] = h_cur
        premissas["delta_custo_horas_assinado"] = round(delta_custo, 4)
        premissas["roi_sinal"] = "negativo" if roi < 0 else ("zero" if roi == 0 else "positivo")

        conf, comps = compute_confidence(
            baseline=baseline, current=current, thresholds=thr
        )
        if kind == RoiKind.ROI_ESTIMADO:
            conf = min(conf, 0.55)
        premissas["confianca_componentes"] = comps

        return RoiResult(
            kind=kind.value,
            valor=round(roi, thr.round_digits),
            premissas=premissas,
            confianca=conf,
            limitacoes=list(dict.fromkeys(lims)),
        )

    def _observed_comparable(
        self,
        baseline: MetricSnapshot,
        current: MetricSnapshot,
        thr: ThresholdConfig,
        periodos_equivalentes: bool,
        janelas_completas: bool,
        lims: list[str],
    ) -> bool:
        ok = True
        if baseline.horas_perdidas_registradas is None or current.horas_perdidas_registradas is None:
            lims.append("horas_registradas_ausentes_em_um_periodo")
            return False
        if not periodos_equivalentes:
            lims.append("periodos_nao_equivalentes")
            ok = False
        if not janelas_completas:
            lims.append("janelas_incompletas")
            ok = False
        if baseline.metodologia_horas != current.metodologia_horas:
            lims.append("metodologia_horas_divergente")
            ok = False
        cov_b = baseline.cobertura_horas_registradas
        cov_c = current.cobertura_horas_registradas
        if cov_b is None or cov_c is None:
            lims.append("cobertura_horas_registradas_ausente")
            ok = False
        else:
            if cov_b < thr.min_hours_coverage_observed or cov_c < thr.min_hours_coverage_observed:
                lims.append("cobertura_horas_abaixo_minimo")
                ok = False
            if abs(cov_b - cov_c) > thr.max_hours_coverage_diff:
                lims.append("cobertura_horas_divergente")
                ok = False
        for snap, label in ((baseline, "baseline"), (current, "atual")):
            if snap.completude_periodo is not None and snap.completude_periodo < thr.min_window_completeness:
                lims.append(f"completude_periodo_{label}_insuficiente")
                ok = False
        return ok
