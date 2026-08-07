"""Baseline window construction and completeness signaling."""

from __future__ import annotations

from dataclasses import replace

from backend.performance.exceptions import InvalidPeriodError, TenantRequiredError
from backend.performance.schemas import BaselineWindow, MetricSnapshot, ThresholdConfig, WindowStatus

_MONTH_RE = __import__("re").compile(r"^(\d{4})-(0[1-9]|1[0-2])$")

# Named windows → expected months
DEFAULT_WINDOWS: dict[str, int] = {
    "pre_intervencao": 3,
    "30_dias": 1,
    "60_dias": 2,
    "90_dias": 3,
    "180_dias": 6,
    "12_meses": 12,
}


def parse_ym(value: str) -> tuple[int, int]:
    if not _MONTH_RE.fullmatch(value or ""):
        raise InvalidPeriodError(f"invalid YYYY-MM: {value!r}")
    y, m = value.split("-")
    return int(y), int(m)


def ym_to_index(ym: str) -> int:
    y, m = parse_ym(ym)
    return y * 12 + (m - 1)


def index_to_ym(idx: int) -> str:
    y, m0 = divmod(idx, 12)
    return f"{y:04d}-{m0 + 1:02d}"


def months_between_inclusive(inicio: str, fim: str) -> int:
    a, b = ym_to_index(inicio), ym_to_index(fim)
    if a > b:
        raise InvalidPeriodError("inicio after fim")
    return b - a + 1


def shift_ym(ym: str, delta_months: int) -> str:
    return index_to_ym(ym_to_index(ym) + delta_months)


class BaselineService:
    def __init__(self, thresholds: ThresholdConfig | None = None) -> None:
        self.thresholds = thresholds or ThresholdConfig()
        self.thresholds.validate()

    def build_window(
        self,
        *,
        nome: str,
        inicio: str | None,
        fim: str | None,
        meses_esperados: int,
        meses_encontrados: int,
    ) -> BaselineWindow:
        if inicio is None or fim is None or meses_esperados <= 0:
            return BaselineWindow(
                nome=nome,
                inicio=inicio,
                fim=fim,
                meses_esperados=meses_esperados,
                meses_encontrados=0,
                completude=0.0,
                status=WindowStatus.INDISPONIVEL.value,
            )
        try:
            months_between_inclusive(inicio, fim)
        except InvalidPeriodError:
            return BaselineWindow(
                nome=nome,
                inicio=inicio,
                fim=fim,
                meses_esperados=meses_esperados,
                meses_encontrados=0,
                completude=0.0,
                status=WindowStatus.INDISPONIVEL.value,
            )
        completude = min(1.0, meses_encontrados / float(meses_esperados))
        if meses_encontrados <= 0:
            status = WindowStatus.INDISPONIVEL.value
        elif completude + 1e-9 < self.thresholds.min_window_completeness:
            status = WindowStatus.INCOMPLETO.value
        else:
            status = WindowStatus.COMPLETO.value
        return BaselineWindow(
            nome=nome,
            inicio=inicio,
            fim=fim,
            meses_esperados=meses_esperados,
            meses_encontrados=meses_encontrados,
            completude=round(completude, self.thresholds.round_digits),
            status=status,
        )

    def windows_ending_at(
        self,
        *,
        reference_end: str,
        months_found_by_window: dict[str, int] | None = None,
    ) -> list[BaselineWindow]:
        """Build standard windows ending at reference_end (inclusive)."""
        found = months_found_by_window or {}
        out: list[BaselineWindow] = []
        for nome, expected in DEFAULT_WINDOWS.items():
            if nome == "pre_intervencao":
                # Pre-intervention: expected months before reference_end - expected
                fim = shift_ym(reference_end, -1)
                inicio = shift_ym(fim, -(expected - 1))
            else:
                fim = reference_end
                inicio = shift_ym(fim, -(expected - 1))
            out.append(
                self.build_window(
                    nome=nome,
                    inicio=inicio,
                    fim=fim,
                    meses_esperados=expected,
                    meses_encontrados=int(found.get(nome, expected)),
                )
            )
        return out

    def assert_comparable(
        self,
        baseline: BaselineWindow,
        current: BaselineWindow,
    ) -> list[str]:
        """Return limitations if windows are not safely comparable."""
        limitations: list[str] = []
        if baseline.status != WindowStatus.COMPLETO.value:
            limitations.append(f"baseline_{baseline.nome}_{baseline.status}")
        if current.status != WindowStatus.COMPLETO.value:
            limitations.append(f"current_{current.nome}_{current.status}")
        if baseline.meses_esperados != current.meses_esperados:
            limitations.append("window_duration_mismatch_without_normalization")
        return limitations

    def validate_tenant(self, client_id: int | None) -> int:
        if client_id is None or int(client_id) <= 0:
            raise TenantRequiredError("client_id obrigatório (sem fallback)")
        return int(client_id)

    def annotate_incomplete_snapshot(self, snap: MetricSnapshot, window: BaselineWindow) -> MetricSnapshot:
        lims = list(snap.limitacoes)
        if window.status != WindowStatus.COMPLETO.value:
            lims.append(f"periodo_{window.status}")
        return replace(snap, limitacoes=lims, meses_com_dados=window.meses_encontrados)
