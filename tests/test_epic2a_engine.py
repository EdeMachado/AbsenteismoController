"""Epic 2A — productivity, ROI, recommendations, score, privacy, orchestrator."""

from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import replace
from pathlib import Path

import pytest

from backend.performance import is_performance_engine_enabled
from backend.performance.action_library import get_action, list_actions
from backend.performance.exceptions import FeatureDisabledError, PrivacyViolationError, TenantRequiredError
from backend.performance.performance_service import PerformanceService
from backend.performance.privacy import assert_no_pii
from backend.performance.productivity_service import ProductivityService
from backend.performance.recommendation_engine import RecommendationEngine
from backend.performance.roi_service import RoiService
from backend.performance.schemas import RoiKind, ThresholdConfig
from tests.fixtures.performance.builders import (
    baseline_ok,
    conditionant_delayed,
    current_frequency_control,
    current_integral,
    current_severity_control,
    current_worsened,
    prod_good_coverage,
    prod_low_coverage,
    snap,
)


def test_flag_default_false(monkeypatch):
    monkeypatch.delenv("ENABLE_BIOMED_PERFORMANCE_ENGINE", raising=False)
    assert is_performance_engine_enabled() is False


def test_flag_blocks_when_required(monkeypatch):
    monkeypatch.setenv("ENABLE_BIOMED_PERFORMANCE_ENGINE", "false")
    svc = PerformanceService(require_flag=True)
    with pytest.raises(FeatureDisabledError):
        svc.analyze(client_id=99, baseline=baseline_ok(), current=current_severity_control())


def test_productivity_attendance():
    ind = ProductivityService().attendance_rate(prod_good_coverage())
    assert ind.valor == pytest.approx(0.9)


def test_productivity_attendance_zero_scheduled():
    from backend.performance.schemas import BiomedProductivity

    ind = ProductivityService().attendance_rate(BiomedProductivity())
    assert ind.valor is None
    assert ind.qualidade == "indisponivel"


def test_coverage_layers_no_causality():
    layers = ProductivityService().separate_layers(prod_good_coverage(), "ok")
    assert layers["resultado"]["causalidade_automatica"] is False
    assert layers["producao"]["tipo"] == "producao"
    assert layers["cobertura"]["tipo"] == "cobertura"


def test_low_coverage_value():
    cov = ProductivityService().coverage(prod_low_coverage())
    assert cov.valor == pytest.approx(0.15)


def test_roi_observado():
    r = RoiService().compute(
        baseline=baseline_ok(),
        current=current_severity_control(),
        custo_programa=10000,
        custo_hora=50,
        usar_horas_estimadas=False,
        fonte_custos="fixture",
    )
    assert r.kind == RoiKind.ROI_OBSERVADO.value
    assert r.valor is not None
    assert "formula" in r.premissas


def test_roi_estimado():
    base = replace(baseline_ok(), horas_perdidas_registradas=None, horas_perdidas_estimadas=1600)
    cur = replace(
        current_severity_control(),
        horas_perdidas_registradas=None,
        horas_perdidas_estimadas=1200,
    )
    r = RoiService().compute(
        baseline=base,
        current=cur,
        custo_programa=10000,
        custo_hora=50,
        usar_horas_estimadas=True,
    )
    assert r.kind == RoiKind.ROI_ESTIMADO.value
    assert any("estimada" in x for x in r.limitacoes)


def test_roi_nao_calculavel_custo_zero():
    r = RoiService().compute(
        baseline=baseline_ok(),
        current=current_severity_control(),
        custo_programa=0,
        custo_hora=50,
    )
    assert r.kind == RoiKind.ROI_NAO_CALCULAVEL.value


def test_roi_nao_calculavel_sem_hora():
    r = RoiService().compute(
        baseline=baseline_ok(),
        current=current_severity_control(),
        custo_programa=100,
        custo_hora=None,
    )
    assert r.kind == RoiKind.ROI_NAO_CALCULAVEL.value


def test_recommendations_recorrencia():
    base = baseline_ok()
    cur = replace(current_worsened(), recorrencia=0.5, grupos_cid=["M"])
    recs = RecommendationEngine().recommend(baseline=base, current=cur)
    ids = {r.id for r in recs}
    assert any(i.startswith("REC-RET") for i in ids) or any(i.startswith("REC-ERG") for i in ids)
    assert all(r.necessita_validacao_humana for r in recs)


def test_recommendations_respiratorio():
    base = baseline_ok()
    cur = replace(current_worsened(), grupos_cid=["J"], eventos=150)
    recs = RecommendationEngine().recommend(baseline=base, current=cur)
    assert any(r.categoria == "RESPIRATORIO" for r in recs)


def test_recommendations_acidentes():
    base = baseline_ok()
    cur = replace(current_worsened(), grupos_cid=["S"], eventos=150)
    recs = RecommendationEngine().recommend(baseline=base, current=cur)
    assert any(r.categoria == "SEGURANCA" for r in recs)


def test_action_library_nonempty():
    actions = list_actions()
    assert len(actions) >= 15
    assert get_action("ACT-ERG-001")["validacao_humana"] is True


def test_orchestrator_full_analysis():
    svc = PerformanceService()
    result = svc.analyze(
        client_id=99,
        baseline=baseline_ok(),
        current=current_severity_control(),
        productivity=prod_good_coverage(),
        conditionants=[conditionant_delayed()],
        reference_end="2024-06",
        custo_programa=10000,
        custo_hora=50,
        acoes_propostas=5,
        acoes_aprovadas=3,
        acoes_executadas=2,
        acoes_pendentes=2,
        metas_atingidas=0.5,
        barreiras=1,
        recomendacoes_recusadas_ou_adiadas=1,
    )
    d = result.to_dict()
    assert d["effectiveness"]["codigo"]
    assert d["narrative"]["fatos"]
    assert d["narrative"]["hipoteses"]
    assert d["executive_score"]["ranking_trabalhadores"] is False
    assert d["roi"]["kind"]
    assert len(d["indicators"]) >= 10
    assert_no_pii(d)


def test_orchestrator_tenant_mismatch():
    with pytest.raises(TenantRequiredError):
        PerformanceService().analyze(
            client_id=99,
            baseline=baseline_ok(),
            current=replace(current_integral(), client_id=100),
        )


def test_privacy_blocks_nome():
    with pytest.raises(PrivacyViolationError):
        assert_no_pii({"trabalhador": {"nome": "Ana"}})


def test_privacy_allows_window_nome():
    assert_no_pii({"baseline_windows": [{"nome": "90_dias", "status": "completo"}]})


def test_privacy_blocks_cpf_string():
    with pytest.raises(PrivacyViolationError):
        assert_no_pii({"x": "529.982.247-25"})


def test_privacy_blocks_email():
    with pytest.raises(PrivacyViolationError):
        assert_no_pii({"x": "a@b.com"})


def test_executive_score_weights_validate():
    with pytest.raises(ValueError):
        ThresholdConfig(w_freq=0).validate()


def test_score_transparent():
    svc = PerformanceService()
    score = svc.executive_score(
        deltas={"eventos": -0.2, "dias_perdidos": -0.2, "recorrencia": -0.1},
        effectiveness_code="EFICACIA_POSITIVA_PARCIAL",
        coverage=0.8,
        iqb=70,
        acoes_executadas=4,
        acoes_propostas=5,
        metas_atingidas=0.6,
        conditionants=[],
    )
    assert 0 <= score["score"] <= 100
    assert "pesos" in score


def test_no_causality_in_narrative():
    result = PerformanceService().analyze(
        client_id=99,
        baseline=baseline_ok(),
        current=current_frequency_control(),
        productivity=prod_good_coverage(),
    )
    assert any("causalidade" in h for h in result.narrative["hipoteses"])


def test_shadow_script_runs(tmp_path):
    import subprocess
    import sys

    out = tmp_path / "out.json"
    proc = subprocess.run(
        [
            sys.executable,
            "scripts/shadow_performance_engine.py",
            "--fixture",
            "integral",
            "--client-id",
            "99",
            "--json-out",
            str(out),
        ],
        cwd="/workspace",
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    data = json.loads(out.read_text())
    assert data["effectiveness"]["codigo"]
    assert_no_pii(data)


def test_shadow_refuses_prod_db():
    import subprocess
    import sys

    proc = subprocess.run(
        [
            sys.executable,
            "scripts/shadow_performance_engine.py",
            "--db",
            "/var/www/absenteismo/database/absenteismo.db",
            "--readonly",
        ],
        cwd="/workspace",
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0


def test_shadow_readonly_temp_db(tmp_path):
    import subprocess
    import sys

    db = tmp_path / "tmp.db"
    sqlite3.connect(db).close()
    proc = subprocess.run(
        [
            sys.executable,
            "scripts/shadow_performance_engine.py",
            "--db",
            str(db),
            "--readonly",
            "--fixture",
            "severity",
        ],
        cwd="/workspace",
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr


def test_indicators_include_actions_and_iqb():
    result = PerformanceService().analyze(
        client_id=99,
        baseline=baseline_ok(),
        current=current_integral(),
        productivity=prod_good_coverage(),
        acoes_propostas=2,
        acoes_executadas=1,
    )
    ids = {i["id"] for i in result.indicators}
    assert "iqb" in ids
    assert "acoes_propostas" in ids
    assert "cobertura_assistencial" in ids
