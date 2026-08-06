"""Confidence scoring for effectiveness / ROI — quality-weighted, documented."""

from __future__ import annotations

from typing import Any

from backend.performance.schemas import Conditionant, MetricSnapshot, ThresholdConfig

# Confidence formula (documented):
# conf = clamp01(
#   0.25 * iqb_norm
# + 0.20 * completude_media
# + 0.15 * cobertura_horas_media
# + 0.10 * headcount_flag
# + 0.15 * fracao_metricas_disponiveis
# + 0.10 * equivalencia_janelas
# + 0.05 * (1 - penalidade_condicionantes)
# )
# iqb_norm = iqb/100 when available else 0.4 (neutral-low, not fake 0.5 score dim)
# headcount_flag = 1 if either period has headcount else 0.6 (partial — absolute metrics still ok)
# equivalencia_janelas = 1 if no period incompleteness else 0.3
# penalidade_condicionantes = min(1, n_adiadas_recusadas / 3)


def compute_confidence(
    *,
    baseline: MetricSnapshot,
    current: MetricSnapshot,
    window_limitations: list[str] | None = None,
    conditionants: list[Conditionant] | None = None,
    thresholds: ThresholdConfig | None = None,
    metric_keys: list[str] | None = None,
) -> tuple[float, dict[str, float]]:
    thr = thresholds or ThresholdConfig()
    keys = metric_keys or [
        "eventos",
        "dias_perdidos",
        "horas_perdidas_registradas",
        "duracao_media",
        "recorrencia",
        "gravidade",
        "afastamentos_longos",
    ]
    available = 0
    for k in keys:
        if getattr(current, k, None) is not None and getattr(baseline, k, None) is not None:
            available += 1
    frac_metrics = available / float(len(keys)) if keys else 0.0

    iqb = current.iqb if current.iqb is not None else baseline.iqb
    iqb_norm = (float(iqb) / 100.0) if iqb is not None else 0.4

    comp_b = baseline.completude_periodo
    comp_c = current.completude_periodo
    if comp_b is None and baseline.meses_com_dados and thr.min_months_for_integral:
        # soft estimate from months if explicit completeness absent
        comp_b = min(1.0, baseline.meses_com_dados / float(thr.min_months_for_integral))
    if comp_c is None and current.meses_com_dados and thr.min_months_for_integral:
        comp_c = min(1.0, current.meses_com_dados / float(thr.min_months_for_integral))
    comps = [c for c in (comp_b, comp_c) if c is not None]
    completude = sum(comps) / len(comps) if comps else 0.5

    cov_regs = [
        c
        for c in (
            baseline.cobertura_horas_registradas,
            current.cobertura_horas_registradas,
        )
        if c is not None
    ]
    cobertura_horas = sum(cov_regs) / len(cov_regs) if cov_regs else 0.4

    headcount_flag = (
        1.0
        if (baseline.headcount is not None or current.headcount is not None)
        else 0.6
    )

    lims = window_limitations or []
    equiv = (
        0.3
        if any("incompleto" in x or "indisponivel" in x for x in lims)
        else 1.0
    )

    delayed = sum(
        1
        for c in (conditionants or [])
        if c.decisao in {"adiada", "recusada"}
    )
    pen_cond = min(1.0, delayed / 3.0)

    components = {
        "iqb_norm": round(iqb_norm, 4),
        "completude_media": round(completude, 4),
        "cobertura_horas_media": round(cobertura_horas, 4),
        "headcount_flag": headcount_flag,
        "fracao_metricas_disponiveis": round(frac_metrics, 4),
        "equivalencia_janelas": equiv,
        "penalidade_condicionantes": round(pen_cond, 4),
    }
    conf = (
        0.25 * iqb_norm
        + 0.20 * completude
        + 0.15 * cobertura_horas
        + 0.10 * headcount_flag
        + 0.15 * frac_metrics
        + 0.10 * equiv
        + 0.05 * (1.0 - pen_cond)
    )
    conf = max(0.0, min(1.0, conf))
    return round(conf, thr.round_digits), components


def redistribute_score_weights(
    original: dict[str, float],
    unavailable: set[str],
) -> tuple[dict[str, float], str]:
    """Proportional redistribution; effective weights sum to 100."""
    if not unavailable:
        return dict(original), "sem_redistribuicao"
    remaining = {k: v for k, v in original.items() if k not in unavailable}
    removed = sum(original[k] for k in unavailable if k in original)
    base = sum(remaining.values())
    if base <= 0:
        n = len(remaining) or 1
        return {k: round(100.0 / n, 4) for k in remaining}, "redistribuicao_uniforme_fallback"
    efetivos = {k: round(v + removed * (v / base), 4) for k, v in remaining.items()}
    drift = round(100.0 - sum(efetivos.values()), 4)
    if efetivos and abs(drift) > 1e-9:
        first = next(iter(efetivos))
        efetivos[first] = round(efetivos[first] + drift, 4)
    return (
        efetivos,
        f"pesos de {sorted(unavailable)} redistribuídos proporcionalmente (soma=100)",
    )
