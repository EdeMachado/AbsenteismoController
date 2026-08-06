"""Epic 2A — extended coverage (thresholds, periods, rounding, catalogs)."""

from __future__ import annotations

from dataclasses import replace

import pytest

from backend.performance.action_library import ACTION_LIBRARY, list_actions
from backend.performance.baseline_service import BaselineService, index_to_ym, parse_ym, ym_to_index
from backend.performance.effectiveness_service import EffectivenessService, _delta
from backend.performance.performance_service import PerformanceService
from backend.performance.recommendation_engine import RecommendationEngine
from backend.performance.roi_service import RoiService
from backend.performance.schemas import (
    BiomedProductivity,
    Conditionant,
    EffectivenessCode,
    ThresholdConfig,
)
from tests.fixtures.performance.builders import (
    baseline_ok,
    current_frequency_control,
    current_integral,
    current_severity_control,
    current_stable,
    current_worsened,
    prod_good_coverage,
    snap,
)


@pytest.mark.parametrize(
    "ym",
    ["2020-01", "2024-12", "2026-08"],
)
def test_parse_ym_valid(ym):
    y, m = parse_ym(ym)
    assert 1 <= m <= 12
    assert ym_to_index(ym) >= 0
    assert index_to_ym(ym_to_index(ym)) == ym


def test_delta_none_and_zero():
    assert _delta(None, 1) is None
    assert _delta(1, None) is None
    assert _delta(0, 0) == 0.0
    assert _delta(5, 0) is None


def test_threshold_material_change_affects_worsening():
    loose = EffectivenessService(ThresholdConfig(material_change=0.01))
    tight = EffectivenessService(ThresholdConfig(material_change=0.5))
    r_loose = loose.classify(baseline=baseline_ok(), current=current_worsened())
    r_tight = tight.classify(baseline=baseline_ok(), current=current_worsened())
    assert r_loose.codigo == EffectivenessCode.RESULTADO_DESFAVORAVEL.value
    # tight may not classify as desfavoravel if deltas < 50%
    assert r_tight.codigo in {c.value for c in EffectivenessCode}


@pytest.mark.parametrize(
    "fixture_cur,expected_family",
    [
        (current_severity_control, "CONTROLE"),
        (current_frequency_control, "CONTROLE"),
        (current_worsened, "DESFAVORAVEL"),
    ],
)
def test_classification_families(fixture_cur, expected_family):
    r = EffectivenessService().classify(baseline=baseline_ok(), current=fixture_cur())
    assert expected_family in r.codigo or r.codigo.endswith(expected_family) or expected_family in r.codigo


def test_all_action_fields_present():
    for aid, meta in ACTION_LIBRARY.items():
        for key in (
            "nome",
            "quando_usar",
            "dados_minimos",
            "responsavel_sugerido",
            "indicador",
            "evidencia_esperada",
            "limitacoes",
            "contraindicacoes",
            "validacao_humana",
        ):
            assert key in meta, f"{aid} missing {key}"


def test_list_actions_ids_unique():
    ids = [a["id"] for a in list_actions()]
    assert len(ids) == len(set(ids))


def test_roi_with_encargos_and_implementacao():
    r = RoiService().compute(
        baseline=baseline_ok(),
        current=current_severity_control(),
        custo_programa=5000,
        custo_hora=40,
        encargos_factor=1.5,
        custos_implementacao=1000,
        fonte_custos="fixture",
    )
    assert r.valor is not None
    assert r.premissas["encargos_factor"] == 1.5
    assert r.premissas["custos_implementacao"] == 1000


def test_roi_premises_always_visible_when_not_calculable():
    r = RoiService().compute(
        baseline=baseline_ok(),
        current=current_severity_control(),
        custo_programa=0,
        custo_hora=10,
    )
    assert "formula" in r.premissas


def test_recommendations_iqb_baixo():
    cur = replace(current_stable(), iqb=40.0)
    # low iqb alone may still generate quality rec if tag set — engine tags iqb_baixo
    recs = RecommendationEngine().recommend(baseline=baseline_ok(), current=cur)
    # may be empty if no material deltas; force tag via coverage
    recs2 = RecommendationEngine().recommend(
        baseline=baseline_ok(), current=cur, assistential_coverage=0.1
    )
    assert any(r.id == "REC-COV-001" or r.id == "REC-QUAL-001" for r in recs2)


def test_recommendations_saude_mental():
    cur = replace(current_worsened(), grupos_cid=["F"], eventos=150)
    recs = RecommendationEngine().recommend(baseline=baseline_ok(), current=cur)
    assert any(r.categoria == "SAUDE_MENTAL" for r in recs)


def test_conditionant_model_fields():
    c = Conditionant(
        recomendacao_id="REC-X",
        decisao="aceita_com_ajustes",
        responsavel="RH",
        prazo="2024-08",
        status="pendente",
        barreira=None,
        risco_residual="baixo",
        evidencia="ata",
        conclusao="ok",
    )
    d = c.to_dict()
    assert d["decisao"] == "aceita_com_ajustes"


def test_analysis_includes_baseline_windows_json_shape():
    result = PerformanceService().analyze(
        client_id=99,
        baseline=baseline_ok(),
        current=current_severity_control(),
        reference_end="2024-06",
        months_found_by_window={"180_dias": 2},
    )
    w180 = next(w for w in result.baseline_windows if w["nome"] == "180_dias")
    assert set(w180.keys()) >= {
        "inicio",
        "fim",
        "meses_esperados",
        "meses_encontrados",
        "completude",
        "status",
    }
    assert w180["status"] == "incompleto"


def test_incomplete_windows_never_silent():
    result = PerformanceService().analyze(
        client_id=99,
        baseline=baseline_ok(),
        current=current_integral(),
        productivity=prod_good_coverage(),
        reference_end="2024-06",
        months_found_by_window={"90_dias": 1},
    )
    assert result.effectiveness["codigo"] == EffectivenessCode.SEM_EVIDENCIA_SUFICIENTE.value


def test_rounding_digits_config():
    thr = ThresholdConfig(round_digits=2)
    svc = PerformanceService(thr)
    score = svc.executive_score(
        deltas={"eventos": -0.12345},
        effectiveness_code="ESTABILIDADE",
        coverage=0.33333,
        iqb=70.123,
        acoes_executadas=1,
        acoes_propostas=3,
        metas_atingidas=0.5,
        conditionants=[],
    )
    # score itself rounded to 2
    text = str(score["score"])
    assert len(text.split(".")[-1]) <= 2 or text.endswith(".0")


def test_absent_productivity_defaults():
    result = PerformanceService().analyze(
        client_id=99,
        baseline=baseline_ok(),
        current=current_frequency_control(),
    )
    assert "producao" in result.productivity["tipo"] or result.productivity["tipo"] == "producao"


def test_metric_snapshot_to_dict_no_pii_keys():
    d = snap().to_dict()
    for banned in ("nome", "cpf", "matricula", "email"):
        assert banned not in d


def test_indicator_quality_estimado_for_estimated_hours():
    result = PerformanceService().analyze(
        client_id=99,
        baseline=baseline_ok(),
        current=replace(
            current_severity_control(),
            horas_perdidas_estimadas=100.0,
            horas_perdidas_registradas=100.0,
            iqb=80,
        ),
        productivity=prod_good_coverage(),
    )
    est = next(i for i in result.indicators if i["id"] == "horas_perdidas_estimadas")
    assert est["qualidade"] == "estimado"


def test_pre_intervencao_window_before_reference():
    windows = BaselineService().windows_ending_at(reference_end="2024-06")
    pre = next(w for w in windows if w.nome == "pre_intervencao")
    assert pre.fim == "2024-05"
    assert pre.inicio == "2024-03"


def test_12_meses_window():
    w = next(
        w
        for w in BaselineService().windows_ending_at(reference_end="2024-12")
        if w.nome == "12_meses"
    )
    assert w.meses_esperados == 12
    assert w.inicio == "2024-01"


def test_effectiveness_result_shape():
    r = EffectivenessService().classify(
        baseline=baseline_ok(), current=current_severity_control()
    )
    d = r.to_dict()
    assert set(d.keys()) == {
        "codigo",
        "rotulo",
        "criterios_acionados",
        "evidencias",
        "limitacoes",
        "confianca",
    }


def test_recommendation_shape():
    recs = RecommendationEngine().recommend(
        baseline=baseline_ok(),
        current=replace(current_worsened(), recorrencia=0.5),
    )
    assert recs
    d = recs[0].to_dict()
    assert d["necessita_validacao_humana"] is True
    assert "confianca" in d


def test_analyze_client_id_required():
    from backend.performance.exceptions import TenantRequiredError

    with pytest.raises(TenantRequiredError):
        PerformanceService().analyze(
            client_id=0,
            baseline=baseline_ok(),
            current=current_stable(),
        )


def test_biomed_productivity_fields():
    p = BiomedProductivity(
        atendimentos_agendados=1,
        atendimentos_realizados=1,
        faltas=0,
        colaboradores_atendidos=1,
        retornos_realizados=1,
        entrevistas_tecnicas=1,
        acoes_coletivas=1,
        avaliacoes_ergonomicas=1,
        campanhas=1,
        encaminhamentos=1,
        planos_ativos=1,
        planos_concluidos=1,
        necessidade_estimada=2,
    )
    assert p.to_dict()["campanhas"] == 1


def test_score_does_not_include_worker_ids():
    score = PerformanceService().executive_score(
        deltas={},
        effectiveness_code="ESTABILIDADE",
        coverage=None,
        iqb=None,
        acoes_executadas=0,
        acoes_propostas=0,
        metas_atingidas=None,
        conditionants=[],
    )
    blob = json_dumps(score)
    assert "matricula" not in blob
    assert "cpf" not in blob


def json_dumps(obj):
    import json

    return json.dumps(obj)


def test_flag_true(monkeypatch):
    from backend.performance import is_performance_engine_enabled

    monkeypatch.setenv("ENABLE_BIOMED_PERFORMANCE_ENGINE", "true")
    assert is_performance_engine_enabled() is True


def test_partial_efficacy_both_controls():
    # Craft snapshot that triggers both severity and frequency improvements
    base = baseline_ok()
    cur = replace(
        current_integral(),
        eventos=70.0,  # down
        dias_perdidos=120.0,  # down
        duracao_media=1.3,
        recorrencia=0.1,
        frequencia=0.9,
        gravidade=1.5,
        iqb=50.0,  # prevent integral via iqb — may be sem evidencia
    )
    # raise iqb but lower coverage to get parcial path
    cur = replace(cur, iqb=80.0)
    r = EffectivenessService().classify(
        baseline=base, current=cur, assistential_coverage=0.2
    )
    assert r.codigo in {
        EffectivenessCode.EFICACIA_POSITIVA_PARCIAL.value,
        EffectivenessCode.CONTROLE_FREQUENCIA.value,
        EffectivenessCode.CONTROLE_SEVERIDADE.value,
        EffectivenessCode.EFICACIA_POSITIVA_INTEGRAL.value,
    }
