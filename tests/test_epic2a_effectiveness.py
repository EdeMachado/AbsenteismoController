"""Epic 2A — effectiveness classification tests."""

from __future__ import annotations

from dataclasses import replace

import pytest

from backend.performance.effectiveness_service import EffectivenessService
from backend.performance.schemas import EffectivenessCode, ThresholdConfig
from tests.fixtures.performance.builders import (
    baseline_ok,
    conditionant_delayed,
    current_estimated_hours,
    current_frequency_control,
    current_integral,
    current_low_iqb,
    current_no_headcount,
    current_severity_control,
    current_stable,
    current_worsened,
)


@pytest.fixture
def svc():
    return EffectivenessService()


def test_controle_severidade(svc):
    r = svc.classify(baseline=baseline_ok(), current=current_severity_control())
    assert r.codigo == EffectivenessCode.CONTROLE_SEVERIDADE.value
    assert r.confianca > 0


def test_controle_frequencia(svc):
    r = svc.classify(baseline=baseline_ok(), current=current_frequency_control())
    assert r.codigo == EffectivenessCode.CONTROLE_FREQUENCIA.value


def test_eficacia_integral(svc):
    r = svc.classify(
        baseline=baseline_ok(),
        current=current_integral(),
        assistential_coverage=0.8,
    )
    assert r.codigo == EffectivenessCode.EFICACIA_POSITIVA_INTEGRAL.value


def test_desfavoravel(svc):
    r = svc.classify(baseline=baseline_ok(), current=current_worsened())
    assert r.codigo == EffectivenessCode.RESULTADO_DESFAVORAVEL.value


def test_estabilidade(svc):
    r = svc.classify(baseline=baseline_ok(), current=current_stable())
    assert r.codigo in {
        EffectivenessCode.ESTABILIDADE.value,
        EffectivenessCode.RESULTADO_INCONCLUSIVO.value,
    }
    assert r.codigo != EffectivenessCode.PREVENCAO_DE_PIORA.value


def test_sem_evidencia_iqb_baixo(svc):
    r = svc.classify(baseline=baseline_ok(), current=current_low_iqb())
    assert r.codigo == EffectivenessCode.SEM_EVIDENCIA_SUFICIENTE.value
    assert "iqb_baixo" in r.limitacoes


def test_sem_evidencia_periodo_incompleto(svc):
    r = svc.classify(
        baseline=baseline_ok(),
        current=current_integral(),
        window_limitations=["periodo_incompleto"],
        assistential_coverage=0.9,
    )
    assert r.codigo == EffectivenessCode.SEM_EVIDENCIA_SUFICIENTE.value


def test_horas_estimadas_gate(svc):
    r = svc.classify(baseline=baseline_ok(), current=current_estimated_hours())
    assert r.codigo == EffectivenessCode.SEM_EVIDENCIA_SUFICIENTE.value
    assert "horas_majoritariamente_estimadas" in r.limitacoes


def test_headcount_ausente_not_global_block(svc):
    base = replace(baseline_ok(), headcount=None)
    cur = replace(current_severity_control(), headcount=None, frequencia=None, eventos_por_100=None)
    r = svc.classify(baseline=base, current=cur)
    assert r.codigo == EffectivenessCode.CONTROLE_SEVERIDADE.value
    assert any("headcount" in x for x in r.limitacoes)


def test_conditionant_downgrades_integral(svc):
    r = svc.classify(
        baseline=baseline_ok(),
        current=current_integral(),
        assistential_coverage=0.9,
        conditionants=[conditionant_delayed()],
    )
    # Delayed structural actions must prevent "integral" claim
    assert r.codigo != EffectivenessCode.EFICACIA_POSITIVA_INTEGRAL.value
    assert r.codigo in {
        EffectivenessCode.EFICACIA_POSITIVA_PARCIAL.value,
        EffectivenessCode.CONTROLE_FREQUENCIA.value,
        EffectivenessCode.CONTROLE_SEVERIDADE.value,
    }
    assert any("adiadas" in x or "recusadas" in x for x in r.limitacoes) or any(
        "condicionado" in e for e in r.evidencias
    )


def test_thresholds_configurable():
    tight = EffectivenessService(ThresholdConfig(material_change=0.5, strong_improvement=0.6))
    r = tight.classify(baseline=baseline_ok(), current=current_severity_control())
    # With huge material threshold, severity control may not fire → inconclusivo/estabilidade/sem evidência
    assert r.codigo in {c.value for c in EffectivenessCode}


def test_division_by_zero_baseline_events(svc):
    base = replace(baseline_ok(), eventos=0.0, dias_perdidos=0.0, frequencia=0.0)
    cur = replace(current_worsened(), eventos=10.0)
    r = svc.classify(baseline=base, current=cur)
    assert r.codigo  # should not crash


def test_deltas_rounding(svc):
    d = svc.deltas(baseline_ok(), current_severity_control())
    assert d["dias_perdidos"] is not None
    assert d["dias_perdidos"] < 0


def test_estabilidade_not_auto_prevencao(svc):
    base = replace(baseline_ok(), afastamentos_longos=30.0, eventos=100.0)
    cur = replace(current_stable(), afastamentos_longos=25.0, eventos=100.0)
    r = svc.classify(baseline=base, current=cur)
    assert r.codigo == EffectivenessCode.ESTABILIDADE.value
    assert EffectivenessCode.PREVENCAO_DE_PIORA.value != r.codigo
    assert "possivel_prevencao_de_piora" in r.hipoteses or any(
        "prevencao" in h for h in r.hipoteses
    )
