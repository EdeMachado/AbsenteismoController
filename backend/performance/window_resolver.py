"""Deterministic competence-window resolution and comparability checks.

Monthly source data: named day windows map to whole competencies.
30 days ≈ 1 competência; never pretend daily precision on monthly uploads.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Sequence

from backend.performance.exceptions import InvalidPeriodError
from backend.services.metric_service import validate_period_month, validate_period_range

# Named windows → expected competencies when source grain is monthly.
COMPETENCE_EQUIVALENTS: dict[str, int] = {
    "30_dias": 1,
    "60_dias": 2,
    "90_dias": 3,
    "180_dias": 6,
    "12_meses": 12,
}


@dataclass(frozen=True)
class ResolvedWindow:
    nome: str
    inicio: str
    fim: str
    meses_esperados: int
    competencias: list[str]
    fonte_granularidade: str = "mensal"
    nota: str = (
        "fonte mensal: janela nominada em dias equivale a N competências inteiras; "
        "não há precisão diária"
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WindowComparability:
    comparable: bool
    mode: str  # integral | descritiva | bloqueada
    reasons: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    baseline_months: int = 0
    current_months: int = 0
    baseline_competencias: list[str] = field(default_factory=list)
    current_competencias: list[str] = field(default_factory=list)
    overlap: bool = False
    contiguous_baseline: bool = False
    contiguous_current: bool = False
    metodologia_horas_equivalente: bool | None = None
    cobertura_horas_comparavel: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def parse_month(value: str, *, field_name: str = "periodo") -> str:
    try:
        out = validate_period_month(value, field_name=field_name)
    except ValueError as exc:
        raise InvalidPeriodError(str(exc)) from exc
    if out is None:
        raise InvalidPeriodError(f"{field_name} é obrigatório")
    return out


def month_to_index(ym: str) -> int:
    y, m = ym.split("-")
    return int(y) * 12 + (int(m) - 1)


def index_to_month(idx: int) -> str:
    y, m0 = divmod(idx, 12)
    return f"{y:04d}-{m0 + 1:02d}"


def iter_competencias(inicio: str, fim: str) -> list[str]:
    inicio, fim = validate_period_range(inicio, fim)
    if inicio is None or fim is None:
        raise InvalidPeriodError("inicio e fim são obrigatórios")
    a = month_to_index(inicio)
    b = month_to_index(fim)
    if a > b:
        raise InvalidPeriodError(f"inicio ({inicio}) posterior a fim ({fim})")
    return [index_to_month(i) for i in range(a, b + 1)]


def count_expected_months(inicio: str, fim: str) -> int:
    return len(iter_competencias(inicio, fim))


def add_months(ym: str, delta: int) -> str:
    return index_to_month(month_to_index(ym) + delta)


def resolve_named_window(nome: str, *, reference_end: str) -> ResolvedWindow:
    """Resolve a named window ending at reference_end (inclusive YYYY-MM)."""
    end = parse_month(reference_end, field_name="reference_end")
    key = nome.strip().lower()
    if key not in COMPETENCE_EQUIVALENTS:
        raise InvalidPeriodError(
            f"janela desconhecida: {nome}; "
            f"suportadas={sorted(COMPETENCE_EQUIVALENTS)}"
        )
    n = COMPETENCE_EQUIVALENTS[key]
    inicio = add_months(end, -(n - 1))
    comps = iter_competencias(inicio, end)
    return ResolvedWindow(
        nome=key,
        inicio=inicio,
        fim=end,
        meses_esperados=n,
        competencias=comps,
    )


def resolve_same_period_previous_year(inicio: str, fim: str) -> ResolvedWindow:
    ini = parse_month(inicio, field_name="periodo_inicio")
    end = parse_month(fim, field_name="periodo_fim")
    comps = iter_competencias(ini, end)
    prev_ini = add_months(ini, -12)
    prev_fim = add_months(end, -12)
    prev_comps = iter_competencias(prev_ini, prev_fim)
    return ResolvedWindow(
        nome="mesmo_periodo_ano_anterior",
        inicio=prev_ini,
        fim=prev_fim,
        meses_esperados=len(prev_comps),
        competencias=prev_comps,
        nota=(
            "mesmo período do ano anterior em competências mensais "
            f"({len(comps)} meses deslocados -12)"
        ),
    )


def resolve_equivalent_quarter(reference_end: str) -> ResolvedWindow:
    end = parse_month(reference_end, field_name="reference_end")
    y, m = int(end[:4]), int(end[5:7])
    q_start_m = ((m - 1) // 3) * 3 + 1
    inicio = f"{y:04d}-{q_start_m:02d}"
    fim = add_months(inicio, 2)
    return ResolvedWindow(
        nome="trimestre_equivalente",
        inicio=inicio,
        fim=fim,
        meses_esperados=3,
        competencias=iter_competencias(inicio, fim),
        nota="trimestre civil contendo reference_end (3 competências)",
    )


def resolve_equivalent_semester(reference_end: str) -> ResolvedWindow:
    end = parse_month(reference_end, field_name="reference_end")
    y, m = int(end[:4]), int(end[5:7])
    s_start_m = 1 if m <= 6 else 7
    inicio = f"{y:04d}-{s_start_m:02d}"
    fim = add_months(inicio, 5)
    return ResolvedWindow(
        nome="semestre_equivalente",
        inicio=inicio,
        fim=fim,
        meses_esperados=6,
        competencias=iter_competencias(inicio, fim),
        nota="semestre civil contendo reference_end (6 competências)",
    )


def are_contiguous(months: Sequence[str]) -> bool:
    if not months:
        return False
    ordered = sorted(months)
    expected = iter_competencias(ordered[0], ordered[-1])
    return list(ordered) == expected


def months_overlap(a: Sequence[str], b: Sequence[str]) -> bool:
    return bool(set(a) & set(b))


def assess_comparability(
    *,
    baseline_inicio: str,
    baseline_fim: str,
    atual_inicio: str,
    atual_fim: str,
    months_with_data_baseline: Sequence[str] | None = None,
    months_with_data_atual: Sequence[str] | None = None,
    metodologia_horas_baseline: str | None = None,
    metodologia_horas_atual: str | None = None,
    cobertura_horas_baseline: float | None = None,
    cobertura_horas_atual: float | None = None,
    max_coverage_diff: float = 0.15,
    require_non_overlap: bool = True,
) -> WindowComparability:
    """Validate window comparability before integral effectiveness."""
    b_ini = parse_month(baseline_inicio, field_name="baseline_inicio")
    b_fim = parse_month(baseline_fim, field_name="baseline_fim")
    a_ini = parse_month(atual_inicio, field_name="atual_inicio")
    a_fim = parse_month(atual_fim, field_name="atual_fim")

    reasons: list[str] = []
    limitations: list[str] = []

    if b_ini > a_ini or b_fim > a_fim:
        # baseline entirely after current is invalid for before/after
        if b_ini >= a_ini:
            reasons.append("baseline_nao_anterior_ao_atual")
            limitations.append("baseline posterior ou não anterior ao período atual")

    b_comps = iter_competencias(b_ini, b_fim)
    a_comps = iter_competencias(a_ini, a_fim)

    if len(b_comps) != len(a_comps):
        reasons.append("quantidade_meses_diferente")
        limitations.append(
            f"baseline tem {len(b_comps)} competências; atual tem {len(a_comps)}"
        )

    overlap = months_overlap(b_comps, a_comps)
    if require_non_overlap and overlap:
        reasons.append("periodos_sobrepostos")
        limitations.append("baseline e atual compartilham competências")

    if set(b_comps) == set(a_comps):
        reasons.append("mesma_competencia_nos_dois_periodos")
        limitations.append("mesma competência indevidamente usada nos dois períodos")

    b_data = list(months_with_data_baseline) if months_with_data_baseline is not None else list(b_comps)
    a_data = list(months_with_data_atual) if months_with_data_atual is not None else list(a_comps)

    contig_b = are_contiguous(b_data) if b_data else False
    contig_a = are_contiguous(a_data) if a_data else False
    if months_with_data_baseline is not None:
        if sorted(b_data) != b_comps:
            reasons.append("baseline_meses_incompletos_ou_gap")
            limitations.append("baseline sem competências contíguas/completas na fonte")
        elif not contig_b:
            reasons.append("baseline_nao_contigua")
    if months_with_data_atual is not None:
        if sorted(a_data) != a_comps:
            reasons.append("atual_meses_incompletos_ou_gap")
            limitations.append("atual sem competências contíguas/completas na fonte")
        elif not contig_a:
            reasons.append("atual_nao_contigua")

    if not b_data:
        reasons.append("baseline_sem_dados")
        limitations.append("baseline sem dados na janela")
    if not a_data:
        reasons.append("atual_sem_dados")
        limitations.append("atual sem dados na janela")

    met_eq: bool | None = None
    if metodologia_horas_baseline is not None and metodologia_horas_atual is not None:
        met_eq = metodologia_horas_baseline == metodologia_horas_atual
        if not met_eq:
            reasons.append("metodologia_horas_diferente")
            limitations.append(
                f"metodologia horas baseline={metodologia_horas_baseline} "
                f"atual={metodologia_horas_atual}"
            )

    cov_ok: bool | None = None
    if cobertura_horas_baseline is not None and cobertura_horas_atual is not None:
        cov_ok = abs(cobertura_horas_baseline - cobertura_horas_atual) <= max_coverage_diff
        if not cov_ok:
            reasons.append("cobertura_horas_divergente")
            limitations.append(
                "diferença de cobertura de horas acima do limiar de comparabilidade"
            )

    blocking = {
        "quantidade_meses_diferente",
        "periodos_sobrepostos",
        "mesma_competencia_nos_dois_periodos",
        "baseline_nao_anterior_ao_atual",
        "baseline_sem_dados",
        "atual_sem_dados",
        "baseline_meses_incompletos_ou_gap",
        "atual_meses_incompletos_ou_gap",
    }
    hard = bool(blocking & set(reasons))
    soft_only = bool(reasons) and not hard

    if hard:
        comparable = False
        mode = "bloqueada"
    elif soft_only:
        comparable = False
        mode = "descritiva"
        limitations.append(
            "janelas não integralmente comparáveis — apenas leitura descritiva segura"
        )
    else:
        comparable = True
        mode = "integral"

    return WindowComparability(
        comparable=comparable,
        mode=mode,
        reasons=reasons,
        limitations=limitations,
        baseline_months=len(b_comps),
        current_months=len(a_comps),
        baseline_competencias=b_comps,
        current_competencias=a_comps,
        overlap=overlap,
        contiguous_baseline=contig_b,
        contiguous_current=contig_a,
        metodologia_horas_equivalente=met_eq,
        cobertura_horas_comparavel=cov_ok,
    )


def document_competence_equivalents() -> dict[str, Any]:
    return {
        "granularidade_fonte": "mensal",
        "equivalencias": {
            k: {"competencias": v, "nota": f"{k} ≈ {v} competência(s) mensal(is)"}
            for k, v in COMPETENCE_EQUIVALENTS.items()
        },
        "aviso": (
            "Não fingir precisão diária quando uploads são por competência mensal."
        ),
    }


__all__ = [
    "COMPETENCE_EQUIVALENTS",
    "ResolvedWindow",
    "WindowComparability",
    "parse_month",
    "iter_competencias",
    "count_expected_months",
    "add_months",
    "resolve_named_window",
    "resolve_same_period_previous_year",
    "resolve_equivalent_quarter",
    "resolve_equivalent_semester",
    "are_contiguous",
    "assess_comparability",
    "document_competence_equivalents",
]
