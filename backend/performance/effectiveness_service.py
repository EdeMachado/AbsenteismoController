"""Deterministic effectiveness classification — no generative AI."""

from __future__ import annotations

from backend.performance.confidence import compute_confidence
from backend.performance.schemas import (
    Conditionant,
    DecisionStatus,
    EffectivenessCode,
    EffectivenessResult,
    MetricSnapshot,
    ThresholdConfig,
)

_LABELS = {
    EffectivenessCode.EFICACIA_POSITIVA_INTEGRAL: "Eficácia positiva integral",
    EffectivenessCode.EFICACIA_POSITIVA_PARCIAL: "Eficácia positiva parcial",
    EffectivenessCode.CONTROLE_SEVERIDADE: "Controle da severidade",
    EffectivenessCode.CONTROLE_FREQUENCIA: "Controle da frequência",
    EffectivenessCode.ESTABILIDADE: "Estabilidade",
    EffectivenessCode.PREVENCAO_DE_PIORA: "Prevenção de piora",
    EffectivenessCode.SEM_EVIDENCIA_SUFICIENTE: "Sem evidência suficiente",
    EffectivenessCode.RESULTADO_INCONCLUSIVO: "Resultado inconclusivo",
    EffectivenessCode.RESULTADO_DESFAVORAVEL: "Resultado desfavorável",
}


def _delta(current: float | None, baseline: float | None) -> float | None:
    if current is None or baseline is None:
        return None
    if baseline == 0:
        if current == 0:
            return 0.0
        return None
    return (current - baseline) / abs(baseline)


def _improved(d: float | None, thr: ThresholdConfig) -> bool:
    return d is not None and d <= -thr.material_change


def _worsened(d: float | None, thr: ThresholdConfig) -> bool:
    return d is not None and d >= thr.material_change


def _stable(d: float | None, thr: ThresholdConfig) -> bool:
    return d is not None and abs(d) <= thr.stability_band


def _first_not_none(*values: float | None) -> float | None:
    """Explicit selection preserving 0.0 (never use `or`)."""
    for v in values:
        if v is not None:
            return v
    return None


class EffectivenessService:
    def __init__(self, thresholds: ThresholdConfig | None = None) -> None:
        self.thresholds = thresholds or ThresholdConfig()
        self.thresholds.validate()

    def classify(
        self,
        *,
        baseline: MetricSnapshot,
        current: MetricSnapshot,
        window_limitations: list[str] | None = None,
        conditionants: list[Conditionant] | None = None,
        assistential_coverage: float | None = None,
    ) -> EffectivenessResult:
        thr = self.thresholds
        lims: list[str] = list(window_limitations or [])
        lims.extend(baseline.limitacoes)
        lims.extend(current.limitacoes)
        criterios: list[str] = []
        evidencias: list[str] = []
        hipoteses: list[str] = []

        iqb = current.iqb if current.iqb is not None else baseline.iqb
        if iqb is not None and iqb < thr.min_iqb:
            lims.append("iqb_baixo")

        # Headcount absence is NOT a global blocker — only population rates
        headcount_missing = baseline.headcount is None and current.headcount is None
        if headcount_missing:
            lims.append("headcount_ausente_taxas_populacionais_indisponiveis")
            lims.append("metricas_dependentes_headcount_bloqueadas")

        est = current.horas_perdidas_estimadas
        reg = current.horas_perdidas_registradas
        est_v = est if est is not None else 0.0
        reg_v = reg if reg is not None else 0.0
        total_h = est_v + reg_v
        if total_h > 0 and est is not None and (est_v / total_h) > thr.max_estimated_hours_share:
            lims.append("horas_majoritariamente_estimadas")

        soft_period = any("incompleto" in x or "indisponivel" in x for x in lims)

        d_evt = _delta(current.eventos, baseline.eventos)
        d_dias = _delta(current.dias_perdidos, baseline.dias_perdidos)
        d_horas = _delta(
            (reg_v + est_v)
            if reg is not None or est is not None
            else None,
            (
                (baseline.horas_perdidas_registradas or 0)
                + (baseline.horas_perdidas_estimadas or 0)
            )
            if baseline.horas_perdidas_registradas is not None
            or baseline.horas_perdidas_estimadas is not None
            else None,
        )
        d_dur = _delta(current.duracao_media, baseline.duracao_media)
        # Population frequency only when headcount present; else use eventos as absolute proxy
        d_freq_pop = _delta(current.frequencia, baseline.frequencia)
        if headcount_missing:
            d_freq_pop = None
            lims.append("frequencia_populacional_nao_avaliada_sem_headcount")
        d_rec = _delta(current.recorrencia, baseline.recorrencia)
        d_grav = _delta(current.gravidade, baseline.gravidade)

        # Global insufficient-evidence gates (exclude headcount)
        hard_blocks = {"iqb_baixo", "horas_majoritariamente_estimadas"}
        small_change = all(
            d is None or abs(d) < thr.material_change
            for d in (d_evt, d_dias, d_rec, d_grav)
        )
        if soft_period or (hard_blocks & set(lims)) or (
            small_change and (iqb is None or iqb < thr.min_iqb)
        ):
            if soft_period or (hard_blocks & set(lims)):
                conf, comps = compute_confidence(
                    baseline=baseline,
                    current=current,
                    window_limitations=lims,
                    conditionants=conditionants,
                    thresholds=thr,
                )
                return self._result(
                    EffectivenessCode.SEM_EVIDENCIA_SUFICIENTE,
                    ["gate_evidencia"],
                    [f"limitacao:{x}" for x in sorted(set(lims))],
                    lims,
                    confianca=min(conf, 0.35),
                    hipoteses=hipoteses,
                    confianca_componentes=comps,
                )

        sev_control = (
            (d_evt is not None and (_stable(d_evt, thr) or _worsened(d_evt, thr)))
            and _improved(d_dias, thr)
            and (_improved(d_horas, thr) or d_horas is None)
            and (_improved(d_dur, thr) or d_dur is None)
        )
        if sev_control:
            criterios.append("eventos_estaveis_ou_maiores")
            criterios.append("dias_menores")
            evidencias.append(f"delta_eventos={d_evt}")
            evidencias.append(f"delta_dias={d_dias}")

        # Frequency control uses absolute event reduction (independent of headcount)
        # plus recurrence; population frequency is optional evidence
        freq_control = (
            _improved(d_evt, thr)
            and (_improved(d_rec, thr) or d_rec is None)
            and (_stable(d_grav, thr) or d_grav is None or not _worsened(d_grav, thr))
        )
        if freq_control:
            criterios.append("eventos_menores")
            if _improved(d_rec, thr):
                criterios.append("recorrencia_menor")
            evidencias.append(f"delta_eventos={d_evt}")
            if d_freq_pop is not None:
                evidencias.append(f"delta_frequencia_populacional={d_freq_pop}")

        cov_ok = (
            assistential_coverage is not None
            and assistential_coverage >= thr.min_assistential_coverage
        )
        iqb_ok = iqb is not None and iqb >= thr.min_iqb

        delayed = [
            c
            for c in (conditionants or [])
            if c.decisao in {DecisionStatus.ADIADA.value, DecisionStatus.RECUSADA.value}
        ]

        if (
            freq_control
            and (_improved(d_dias, thr) or _improved(d_grav, thr))
            and (_improved(d_rec, thr) or d_rec is None)
            and iqb_ok
            and cov_ok
            and not soft_period
        ):
            code = EffectivenessCode.EFICACIA_POSITIVA_INTEGRAL
            criterios = criterios + ["iqb_suficiente", "cobertura_adequada"]
        elif sev_control and not freq_control:
            code = EffectivenessCode.CONTROLE_SEVERIDADE
        elif freq_control and not sev_control:
            code = EffectivenessCode.CONTROLE_FREQUENCIA
        elif freq_control and sev_control:
            code = EffectivenessCode.EFICACIA_POSITIVA_PARCIAL
        elif all(
            _stable(d, thr)
            for d in (d_evt, d_dias)
            if d is not None
        ) and any(d is not None for d in (d_evt, d_dias)):
            # Stability only — do NOT auto-classify PREVENCAO_DE_PIORA
            code = EffectivenessCode.ESTABILIDADE
            criterios.append("variacao_dentro_banda")
            if self._possible_prevention_signal(baseline, current, thr):
                hipoteses.append("possivel_prevencao_de_piora")
                hipoteses.append("sem_contrafactual_documentado")
                hipoteses.append("nao_afirmar_resultado_evitado")
                lims.append(
                    "prevencao_formal_requer_serie_tendencia_projecao_e_intervalo"
                )
        elif _worsened(d_dias, thr) or _worsened(d_evt, thr):
            code = EffectivenessCode.RESULTADO_DESFAVORAVEL
            criterios.append("piora_material")
            evidencias.append(f"delta_eventos={d_evt}")
            evidencias.append(f"delta_dias={d_dias}")
        else:
            code = EffectivenessCode.RESULTADO_INCONCLUSIVO
            criterios.append("padrao_nao_classificado")

        if delayed and code in {
            EffectivenessCode.EFICACIA_POSITIVA_INTEGRAL,
            EffectivenessCode.EFICACIA_POSITIVA_PARCIAL,
            EffectivenessCode.CONTROLE_SEVERIDADE,
            EffectivenessCode.CONTROLE_FREQUENCIA,
        }:
            lims.append("recomendacoes_estruturais_adiadas_ou_recusadas")
            if code == EffectivenessCode.EFICACIA_POSITIVA_INTEGRAL:
                code = EffectivenessCode.EFICACIA_POSITIVA_PARCIAL
            evidencias.append(
                "interpretacao_condicionada_a_decisoes_empresariais_pendentes"
            )

        conf, comps = compute_confidence(
            baseline=baseline,
            current=current,
            window_limitations=lims,
            conditionants=conditionants,
            thresholds=thr,
        )
        return self._result(
            code,
            criterios,
            evidencias,
            lims,
            confianca=conf,
            hipoteses=hipoteses,
            confianca_componentes=comps,
        )

    def _possible_prevention_signal(
        self, baseline: MetricSnapshot, current: MetricSnapshot, thr: ThresholdConfig
    ) -> bool:
        """Hypothesis helper only — never grounds PREVENCAO_DE_PIORA class in this version."""
        if baseline.afastamentos_longos is None or current.afastamentos_longos is None:
            return False
        if baseline.eventos and baseline.eventos > 0 and current.eventos:
            base_share = baseline.afastamentos_longos / baseline.eventos
            cur_share = current.afastamentos_longos / current.eventos
            return base_share >= 0.2 and cur_share <= base_share + thr.stability_band
        return False

    def _result(
        self,
        code: EffectivenessCode,
        criterios: list[str],
        evidencias: list[str],
        lims: list[str],
        *,
        confianca: float,
        hipoteses: list[str] | None = None,
        confianca_componentes: dict | None = None,
    ) -> EffectivenessResult:
        return EffectivenessResult(
            codigo=code.value,
            rotulo=_LABELS[code],
            criterios_acionados=list(dict.fromkeys(criterios)),
            evidencias=evidencias,
            limitacoes=list(dict.fromkeys(lims)),
            confianca=round(confianca, self.thresholds.round_digits),
            hipoteses=list(dict.fromkeys(hipoteses or [])),
            confianca_componentes=confianca_componentes or {},
        )

    def deltas(self, baseline: MetricSnapshot, current: MetricSnapshot) -> dict[str, float | None]:
        return {
            "eventos": _delta(current.eventos, baseline.eventos),
            "dias_perdidos": _delta(current.dias_perdidos, baseline.dias_perdidos),
            "duracao_media": _delta(current.duracao_media, baseline.duracao_media),
            "frequencia": _delta(current.frequencia, baseline.frequencia),
            "gravidade": _delta(current.gravidade, baseline.gravidade),
            "recorrencia": _delta(current.recorrencia, baseline.recorrencia),
            "trabalhadores_unicos": _delta(
                current.trabalhadores_unicos, baseline.trabalhadores_unicos
            ),
            "afastamentos_longos": _delta(
                current.afastamentos_longos, baseline.afastamentos_longos
            ),
        }
