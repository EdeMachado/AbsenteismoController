"""ROI structure — observed / estimated / not calculable."""

from __future__ import annotations

from typing import Any

from backend.performance.schemas import MetricSnapshot, RoiKind, RoiResult, ThresholdConfig


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
    ) -> RoiResult:
        premissas: dict[str, Any] = {
            "formula": "((custo_evitado - custo_programa) / custo_programa) * 100",
            "custo_evitado": "(horas_baseline - horas_atuais) * custo_hora_ajustado",
            "custo_hora": custo_hora,
            "encargos_factor": encargos_factor,
            "custos_implementacao": custos_implementacao,
            "custo_programa": custo_programa,
            "usar_horas_estimadas": usar_horas_estimadas,
            "fonte_custos": fonte_custos,
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

        base_reg = baseline.horas_perdidas_registradas
        cur_reg = current.horas_perdidas_registradas
        base_est = baseline.horas_perdidas_estimadas
        cur_est = current.horas_perdidas_estimadas

        if not usar_horas_estimadas:
            if base_reg is None or cur_reg is None:
                return RoiResult(
                    kind=RoiKind.ROI_NAO_CALCULAVEL.value,
                    valor=None,
                    premissas=premissas,
                    confianca=0.0,
                    limitacoes=["horas_registradas_ausentes"],
                )
            h_base, h_cur = base_reg, cur_reg
            kind = RoiKind.ROI_OBSERVADO
            conf = 0.75
        else:
            # Prefer registered; fill with estimated
            if base_reg is None and base_est is None:
                return RoiResult(
                    kind=RoiKind.ROI_NAO_CALCULAVEL.value,
                    valor=None,
                    premissas=premissas,
                    confianca=0.0,
                    limitacoes=["horas_ausentes"],
                )
            h_base = (base_reg or 0) + (base_est or 0)
            h_cur = (cur_reg or 0) + (cur_est or 0)
            kind = RoiKind.ROI_ESTIMADO
            conf = 0.45
            lims.append("economia_estimada_nao_confundir_com_real")
            premissas["aviso"] = "ROI estimado — não afirmar economia real"

        custo_hora_adj = custo_hora * encargos_factor
        custo_evitado = (h_base - h_cur) * custo_hora_adj
        custo_total = custo_programa + custos_implementacao
        if custo_total <= 0:
            return RoiResult(
                kind=RoiKind.ROI_NAO_CALCULAVEL.value,
                valor=None,
                premissas=premissas,
                confianca=0.0,
                limitacoes=["custo_total_programa_zero"],
            )
        roi = ((custo_evitado - custo_total) / custo_total) * 100.0
        premissas["horas_baseline"] = h_base
        premissas["horas_atuais"] = h_cur
        premissas["custo_evitado_calculado"] = round(custo_evitado, 4)
        premissas["custo_total_programa"] = custo_total

        return RoiResult(
            kind=kind.value,
            valor=round(roi, self.thresholds.round_digits),
            premissas=premissas,
            confianca=conf,
            limitacoes=lims,
        )
