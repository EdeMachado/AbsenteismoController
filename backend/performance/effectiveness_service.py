"""Deterministic effectiveness classification — no generative AI."""

from __future__ import annotations

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
        return None  # division by zero / undefined relative change
    return (current - baseline) / abs(baseline)


def _improved(d: float | None, thr: ThresholdConfig) -> bool:
    return d is not None and d <= -thr.material_change


def _worsened(d: float | None, thr: ThresholdConfig) -> bool:
    return d is not None and d >= thr.material_change


def _stable(d: float | None, thr: ThresholdConfig) -> bool:
    return d is not None and abs(d) <= thr.stability_band


def _strong_improved(d: float | None, thr: ThresholdConfig) -> bool:
    return d is not None and d <= -thr.strong_improvement


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

        # Evidence gates
        iqb = current.iqb if current.iqb is not None else baseline.iqb
        if iqb is not None and iqb < thr.min_iqb:
            lims.append("iqb_baixo")
        if baseline.headcount is None and current.headcount is None:
            lims.append("headcount_ausente")
        est = current.horas_perdidas_estimadas or 0.0
        reg = current.horas_perdidas_registradas or 0.0
        total_h = est + reg
        if total_h > 0 and (est / total_h) > thr.max_estimated_hours_share:
            lims.append("horas_majoritariamente_estimadas")
        if any(x.startswith("periodo_") or "incompleto" in x or "indisponivel" in x for x in lims):
            pass  # already flagged

        d_evt = _delta(current.eventos, baseline.eventos)
        d_dias = _delta(current.dias_perdidos, baseline.dias_perdidos)
        d_horas = _delta(
            (current.horas_perdidas_registradas or 0) + (current.horas_perdidas_estimadas or 0)
            if current.horas_perdidas_registradas is not None or current.horas_perdidas_estimadas is not None
            else None,
            (baseline.horas_perdidas_registradas or 0) + (baseline.horas_perdidas_estimadas or 0)
            if baseline.horas_perdidas_registradas is not None or baseline.horas_perdidas_estimadas is not None
            else None,
        )
        d_dur = _delta(current.duracao_media, baseline.duracao_media)
        d_freq = _delta(current.frequencia, baseline.frequencia)
        d_rec = _delta(current.recorrencia, baseline.recorrencia)
        d_grav = _delta(current.gravidade, baseline.gravidade)

        # Insufficient evidence
        hard_blocks = {
            "iqb_baixo",
            "headcount_ausente",
            "horas_majoritariamente_estimadas",
        }
        soft_period = any("incompleto" in x or "indisponivel" in x for x in lims)
        small_change = all(
            d is None or abs(d) < thr.material_change
            for d in (d_evt, d_dias, d_freq, d_rec, d_grav)
        )
        if soft_period or (hard_blocks & set(lims)) or (
            small_change and (iqb is None or iqb < thr.min_iqb)
        ):
            if soft_period or (hard_blocks & set(lims)):
                return self._result(
                    EffectivenessCode.SEM_EVIDENCIA_SUFICIENTE,
                    ["gate_evidencia"],
                    [f"limitacao:{x}" for x in sorted(set(lims))],
                    lims,
                    confianca=0.25,
                )

        # Severity control: events stable/up, days/hours/duration down
        sev_control = (
            (d_evt is not None and ( _stable(d_evt, thr) or _worsened(d_evt, thr)))
            and _improved(d_dias, thr)
            and (_improved(d_horas, thr) or d_horas is None)
            and (_improved(d_dur, thr) or d_dur is None)
        )
        if sev_control:
            criterios.append("eventos_estaveis_ou_maiores")
            criterios.append("dias_menores")
            evidencias.append(f"delta_eventos={d_evt}")
            evidencias.append(f"delta_dias={d_dias}")

        # Frequency control
        freq_control = (
            _improved(d_evt, thr)
            and (_improved(d_rec, thr) or d_rec is None)
            and (_stable(d_grav, thr) or d_grav is None or not _worsened(d_grav, thr))
        )
        if freq_control:
            criterios.append("eventos_menores")
            if _improved(d_rec, thr):
                criterios.append("recorrencia_menor")
            evidencias.append(f"delta_frequencia_proxy_eventos={d_evt}")

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

        # Integral efficacy (may be downgraded by conditionants below)
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
            conf = 0.85
        elif sev_control and not freq_control:
            code = EffectivenessCode.CONTROLE_SEVERIDADE
            conf = 0.7
        elif freq_control and not sev_control:
            code = EffectivenessCode.CONTROLE_FREQUENCIA
            conf = 0.7
        elif freq_control and sev_control:
            code = EffectivenessCode.EFICACIA_POSITIVA_PARCIAL
            conf = 0.75
        elif all(_stable(d, thr) for d in (d_evt, d_dias, d_freq) if d is not None) and any(
            d is not None for d in (d_evt, d_dias, d_freq)
        ):
            if self._was_worsening_trend_averted(baseline, current, thr):
                code = EffectivenessCode.PREVENCAO_DE_PIORA
                criterios.append("piora_evitada_vs_projecao_simples")
                conf = 0.55
            else:
                code = EffectivenessCode.ESTABILIDADE
                criterios.append("variacao_dentro_banda")
                conf = 0.6
        elif _worsened(d_dias, thr) or _worsened(d_evt, thr) or _worsened(d_freq, thr):
            code = EffectivenessCode.RESULTADO_DESFAVORAVEL
            criterios.append("piora_material")
            evidencias.append(f"delta_eventos={d_evt}")
            evidencias.append(f"delta_dias={d_dias}")
            conf = 0.65
        else:
            code = EffectivenessCode.RESULTADO_INCONCLUSIVO
            criterios.append("padrao_nao_classificado")
            conf = 0.4

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
                "resultado_parcial_condicionado_a_decisoes_empresariais_pendentes"
            )
            conf = max(0.35, conf - 0.15)

        return self._result(code, criterios, evidencias, lims, confianca=conf)

    def _was_worsening_trend_averted(
        self, baseline: MetricSnapshot, current: MetricSnapshot, thr: ThresholdConfig
    ) -> bool:
        """
        Simple deterministic heuristic: if baseline already showed elevated
        long-leave share and current held flat, treat as prevention signal.
        Not causal — flagged as hypothesis upstream.
        """
        if baseline.afastamentos_longos is None or current.afastamentos_longos is None:
            return False
        if baseline.eventos and baseline.eventos > 0:
            base_share = baseline.afastamentos_longos / baseline.eventos
            cur_share = (
                current.afastamentos_longos / current.eventos if current.eventos else 0
            )
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
    ) -> EffectivenessResult:
        return EffectivenessResult(
            codigo=code.value,
            rotulo=_LABELS[code],
            criterios_acionados=list(dict.fromkeys(criterios)),
            evidencias=evidencias,
            limitacoes=list(dict.fromkeys(lims)),
            confianca=round(confianca, self.thresholds.round_digits),
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
        }
