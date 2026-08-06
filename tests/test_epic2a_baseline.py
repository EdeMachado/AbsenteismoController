"""Epic 2A — baseline window tests."""

from __future__ import annotations

import pytest

from backend.performance.baseline_service import (
    BaselineService,
    months_between_inclusive,
    shift_ym,
)
from backend.performance.exceptions import InvalidPeriodError, TenantRequiredError
from backend.performance.schemas import ThresholdConfig, WindowStatus


def test_months_between_inclusive():
    assert months_between_inclusive("2024-01", "2024-03") == 3


def test_months_between_invalid():
    with pytest.raises(InvalidPeriodError):
        months_between_inclusive("2024-05", "2024-01")


def test_shift_ym():
    assert shift_ym("2024-01", 2) == "2024-03"
    assert shift_ym("2024-01", -1) == "2023-12"


def test_windows_ending_at_complete():
    svc = BaselineService()
    windows = svc.windows_ending_at(reference_end="2024-06")
    names = {w.nome for w in windows}
    assert "30_dias" in names
    assert "60_dias" in names
    assert "90_dias" in names
    assert "180_dias" in names
    assert "12_meses" in names
    assert "pre_intervencao" in names
    w90 = next(w for w in windows if w.nome == "90_dias")
    assert w90.meses_esperados == 3
    assert w90.status == WindowStatus.COMPLETO.value
    assert w90.completude == 1.0
    assert w90.inicio == "2024-04"
    assert w90.fim == "2024-06"


def test_window_incomplete_signaled():
    svc = BaselineService(ThresholdConfig(min_window_completeness=0.8))
    w = svc.build_window(
        nome="90_dias",
        inicio="2024-04",
        fim="2024-06",
        meses_esperados=3,
        meses_encontrados=1,
    )
    assert w.status == WindowStatus.INCOMPLETO.value
    assert w.completude < 0.8


def test_window_indisponivel():
    svc = BaselineService()
    w = svc.build_window(
        nome="x", inicio=None, fim=None, meses_esperados=3, meses_encontrados=0
    )
    assert w.status == WindowStatus.INDISPONIVEL.value


def test_assert_comparable_flags_mismatch():
    svc = BaselineService()
    a = svc.build_window(nome="a", inicio="2024-01", fim="2024-03", meses_esperados=3, meses_encontrados=3)
    b = svc.build_window(nome="b", inicio="2024-04", fim="2024-04", meses_esperados=1, meses_encontrados=1)
    lims = svc.assert_comparable(a, b)
    assert "window_duration_mismatch_without_normalization" in lims


def test_tenant_required():
    with pytest.raises(TenantRequiredError):
        BaselineService().validate_tenant(None)
    with pytest.raises(TenantRequiredError):
        BaselineService().validate_tenant(0)


def test_found_months_override():
    svc = BaselineService()
    windows = svc.windows_ending_at(
        reference_end="2024-06",
        months_found_by_window={"90_dias": 1, "30_dias": 1},
    )
    w90 = next(w for w in windows if w.nome == "90_dias")
    assert w90.status == WindowStatus.INCOMPLETO.value
