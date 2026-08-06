"""Epic 2A methodological hardening tests (headcount, score, ROI, narrative)."""

from __future__ import annotations

from dataclasses import replace

import pytest

from backend.performance.confidence import compute_confidence, redistribute_score_weights
from backend.performance.effectiveness_service import EffectivenessService, _first_not_none
from backend.performance.performance_service import PerformanceService
from backend.performance.roi_service import ROI_FORMULA, RoiService
from backend.performance.schemas import (
    ActionCounts,
    EffectivenessCode,
    RoiKind,
    ThresholdConfig,
)
from tests.fixtures.performance.builders import (
    baseline_ok,
    current_severity_control,
    current_stable,
    current_worsened,
    prod_good_coverage,
)


def test_no_headcount_still_severity_control():
    base = replace(baseline_ok(), headcount=None)
    cur = replace(
        current_severity_control(),
        headcount=None,
        frequencia=None,
        eventos_por_100=None,
        horas_por_100=None,
    )
    r = EffectivenessService().classify(baseline=base, current=cur)
    assert r.codigo == EffectivenessCode.CONTROLE_SEVERIDADE.value


def test_no_headcount_blocks_eventos_por_100_indicator():
    base = replace(baseline_ok(), headcount=None)
    cur = replace(current_severity_control(), headcount=None, eventos_por_100=12.0)
    result = PerformanceService().analyze(
        client_id=99, baseline=base, current=cur, productivity=prod_good_coverage()
    )
    ind = next(i for i in result.indicators if i["id"] == "eventos_por_100")
    assert ind["valor"] is None
    assert "requer_headcount" in ind["limitacoes"]


def test_stability_not_auto_prevention():
    base = replace(baseline_ok(), afastamentos_longos=30.0, eventos=100.0)
    cur = replace(current_stable(), afastamentos_longos=25.0, eventos=100.0)
    r = EffectivenessService().classify(baseline=base, current=cur)
    assert r.codigo == EffectivenessCode.ESTABILIDADE.value
    assert "possivel_prevencao_de_piora" in r.hipoteses


def test_delta_zero_preserved_not_or_fallback():
    assert _first_not_none(0.0, 0.5) == 0.0
    assert _first_not_none(None, 0.0) == 0.0
    d = EffectivenessService().deltas(
        replace(baseline_ok(), eventos=100.0),
        replace(current_stable(), eventos=100.0),
    )
    assert d["eventos"] == 0.0


def test_missing_dimension_not_neutral_50():
    score = PerformanceService().executive_score(
        deltas={"eventos": None, "dias_perdidos": -0.2, "recorrencia": None},
        effectiveness_code="CONTROLE_SEVERIDADE",
        coverage=None,
        iqb=None,
        action_counts=ActionCounts(aprovadas=0, executadas=0),
        metas_atingidas=None,
        conditionants=[],
    )
    assert score["dimensoes"]["cobertura_assistencial"]["valor"] is None
    assert score["dimensoes"]["execucao_acoes"]["status"] == "nao_avaliada"
    assert score["dimensoes"]["qualidade_dados"]["valor"] is None


def test_effective_weights_sum_100():
    original = ThresholdConfig().weight_map()
    efetivos, _ = redistribute_score_weights(
        original, {"cobertura_assistencial", "atingimento_metas"}
    )
    assert abs(sum(efetivos.values()) - 100.0) < 1e-6


def test_insufficient_score_coverage_blocks():
    thr = ThresholdConfig(min_score_coverage=0.99)
    score = PerformanceService(thr).executive_score(
        deltas={"eventos": -0.1},
        effectiveness_code="ESTABILIDADE",
        coverage=None,
        iqb=None,
        action_counts=ActionCounts(),
        metas_atingidas=None,
        conditionants=[],
    )
    assert score["status"] == "INSUFICIENTE"
    assert score["score"] is None


def test_execution_uses_aprovadas_aplicaveis():
    score = PerformanceService().executive_score(
        deltas={"eventos": -0.1, "dias_perdidos": -0.1, "recorrencia": -0.1},
        effectiveness_code="X",
        coverage=0.8,
        iqb=70,
        action_counts=ActionCounts(propostas=100, aprovadas=4, aplicaveis=4, executadas=2),
        metas_atingidas=0.5,
        conditionants=[],
    )
    assert score["dimensoes"]["execucao_acoes"]["valor"] == pytest.approx(50.0)
    assert score["execucao_denominador"] == "aprovadas_aplicaveis"


def test_zero_aprovadas_execution_not_evaluated():
    score = PerformanceService().executive_score(
        deltas={"eventos": -0.1, "dias_perdidos": -0.1, "recorrencia": 0.0},
        effectiveness_code="X",
        coverage=0.8,
        iqb=70,
        action_counts=ActionCounts(propostas=5, aprovadas=0, executadas=0),
        metas_atingidas=0.5,
        conditionants=[],
    )
    assert score["dimensoes"]["execucao_acoes"]["status"] == "nao_avaliada"
    assert score["dimensoes"]["execucao_acoes"]["valor"] is None


def test_roi_observado_equivalent_coverage():
    base = baseline_ok()
    cur = replace(
        current_severity_control(), cobertura_horas_registradas=1.0, completude_periodo=1.0
    )
    r = RoiService().compute(
        baseline=base,
        current=cur,
        custo_programa=10000,
        custo_hora=50,
        janelas_completas=True,
        periodos_equivalentes=True,
    )
    assert r.kind == RoiKind.ROI_OBSERVADO.value
    assert r.premissas["cobertura_horas_registradas_baseline"] == 1.0


def test_roi_divergent_coverage_downgrades():
    base = replace(baseline_ok(), cobertura_horas_registradas=1.0)
    cur = replace(
        current_severity_control(),
        cobertura_horas_registradas=0.5,
        completude_periodo=1.0,
    )
    r = RoiService().compute(
        baseline=base,
        current=cur,
        custo_programa=10000,
        custo_hora=50,
    )
    assert r.kind in {RoiKind.ROI_ESTIMADO.value, RoiKind.ROI_NAO_CALCULAVEL.value}
    assert (
        "cobertura_horas_divergente" in r.limitacoes
        or "cobertura_horas_abaixo_minimo" in r.limitacoes
    )


def test_roi_incomplete_periods_block_observed():
    base = replace(baseline_ok(), completude_periodo=0.5)
    cur = replace(current_severity_control(), completude_periodo=0.5)
    r = RoiService().compute(
        baseline=base,
        current=cur,
        custo_programa=10000,
        custo_hora=50,
        janelas_completas=False,
    )
    assert r.kind != RoiKind.ROI_OBSERVADO.value


def test_roi_formula_matches_calculation():
    assert "custo_total_programa" in ROI_FORMULA
    base = baseline_ok()
    cur = current_severity_control()
    r = RoiService().compute(
        baseline=base,
        current=cur,
        custo_programa=10000,
        custo_hora=50,
        custos_implementacao=1000,
    )
    h_base = base.horas_perdidas_registradas
    h_cur = cur.horas_perdidas_registradas
    delta = (h_base - h_cur) * 50
    expected = ((delta - 11000) / 11000) * 100
    assert r.valor == pytest.approx(expected, rel=1e-4)
    assert r.premissas["custo_total_programa"] == 11000
    assert r.premissas["formula"] == ROI_FORMULA


def test_roi_negative_when_hours_increase():
    base = replace(baseline_ok(), horas_perdidas_registradas=1000.0)
    cur = replace(
        current_worsened(),
        horas_perdidas_registradas=2000.0,
        cobertura_horas_registradas=1.0,
        completude_periodo=1.0,
    )
    r = RoiService().compute(
        baseline=base, current=cur, custo_programa=1000, custo_hora=50
    )
    assert r.valor is not None and r.valor < 0
    assert r.premissas["custo_adicional_estimado"] is not None
    assert r.premissas["custo_evitado"] is None


def test_confidence_varies_with_quality():
    good = replace(
        baseline_ok(), iqb=90.0, completude_periodo=1.0, cobertura_horas_registradas=1.0
    )
    bad = replace(
        baseline_ok(), iqb=40.0, completude_periodo=0.3, cobertura_horas_registradas=0.2
    )
    c_good, _ = compute_confidence(baseline=good, current=good)
    c_bad, _ = compute_confidence(baseline=bad, current=bad)
    assert c_good > c_bad


def test_narrative_no_causality_and_hypothesis_markers():
    result = PerformanceService().analyze(
        client_id=99,
        baseline=baseline_ok(),
        current=current_severity_control(),
        productivity=prod_good_coverage(),
    )
    assert any("nao_afirma_causalidade" in x for x in result.narrative["interpretacoes"])
    assert all("hipotese" in h for h in result.narrative["hipoteses"])
    assert not any(f.startswith("se_recomendacoes") for f in result.narrative["fatos"])
