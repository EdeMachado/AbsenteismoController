"""Absenteeism Cost Model — EXEC-03.

Formal rules:
- Prefer recorded hours; never invent.
- Do not double-count days and hours derived from the same days.
- Hourly cost has states: REAL | ESTIMADO | NAO_INFORMADO | ILUSTRATIVO.
- Illustrative defaults are never treated as real company data.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from typing import Any, Optional


ASSUMPTION_REAL = "REAL"
ASSUMPTION_ESTIMADO = "ESTIMADO"
ASSUMPTION_NAO_INFORMADO = "NAO_INFORMADO"
ASSUMPTION_ILUSTRATIVO = "ILUSTRATIVO"

HOURS_REGISTRADAS = "registradas"
HOURS_ESTIMADAS = "estimadas"
HOURS_INDISPONIVEIS = "indisponiveis"


@dataclass
class HourlyLaborCostAssumption:
    valor: Optional[float]
    estado: str
    moeda: str = "BRL"
    rotulo: str = "Custo médio da hora de trabalho"
    disclaimer: str = ""
    fonte: str = "nao_informada"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HoursBasis:
    kind: str
    horas: Optional[float]
    dias_perdidos: float = 0.0
    jornada_diaria: Optional[float] = None
    notas: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AbsenteeismCostResult:
    calculavel: bool
    custo_estimado: Optional[float]
    hours: HoursBasis
    assumption: HourlyLaborCostAssumption
    formula: str
    linguagem: str
    limitacoes: list[str] = field(default_factory=list)
    breakdown: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "calculavel": self.calculavel,
            "custo_estimado": self.custo_estimado,
            "hours": self.hours.to_dict(),
            "assumption": self.assumption.to_dict(),
            "formula": self.formula,
            "linguagem": self.linguagem,
            "limitacoes": list(self.limitacoes),
            "breakdown": dict(self.breakdown),
        }


def resolve_hourly_assumption(
    *,
    valor_real: Optional[float] = None,
    valor_estimado: Optional[float] = None,
    allow_illustrative: bool = False,
) -> HourlyLaborCostAssumption:
    """Resolve hourly cost assumption with explicit state machine."""
    if valor_real is not None and float(valor_real) > 0:
        return HourlyLaborCostAssumption(
            valor=float(valor_real),
            estado=ASSUMPTION_REAL,
            disclaimer="Estimativa baseada no custo médio informado pela empresa.",
            fonte="empresa",
        )
    if valor_estimado is not None and float(valor_estimado) > 0:
        return HourlyLaborCostAssumption(
            valor=float(valor_estimado),
            estado=ASSUMPTION_ESTIMADO,
            disclaimer="Estimativa baseada em custo médio estimado informado (não salarial bruto).",
            fonte="empresa_estimado",
        )

    # Staging/demo only — never production default.
    if allow_illustrative:
        raw = (os.environ.get("EXECUTIVE_ILLUSTRATIVE_HOURLY_COST") or "35").strip()
        try:
            demo = float(raw)
        except ValueError:
            demo = 35.0
        if demo > 0:
            return HourlyLaborCostAssumption(
                valor=demo,
                estado=ASSUMPTION_ILUSTRATIVO,
                disclaimer=(
                    f"Premissa ilustrativa — substitua pelo custo hora real da empresa "
                    f"(R$ {demo:.2f}/h). Não utilizar como dado real."
                ),
                fonte="staging_demo",
            )

    return HourlyLaborCostAssumption(
        valor=None,
        estado=ASSUMPTION_NAO_INFORMADO,
        disclaimer="Custo hora não informado — impacto financeiro não calculável.",
        fonte="nao_informada",
    )


def resolve_hours_basis(
    *,
    horas_registradas: Optional[float],
    horas_estimadas: Optional[float] = None,
    dias_perdidos: float = 0.0,
    jornada_diaria: Optional[float] = None,
    allow_estimate_from_days: bool = True,
) -> HoursBasis:
    """Prefer recorded hours; estimate from days×jornada only when explicit and valid.

    Never add days-derived hours on top of recorded hours (no double counting).
    """
    notes: list[str] = []
    if horas_registradas is not None and float(horas_registradas) > 0:
        notes.append("Base = horas registradas; dias não convertidos adicionalmente.")
        return HoursBasis(
            kind=HOURS_REGISTRADAS,
            horas=round(float(horas_registradas), 4),
            dias_perdidos=float(dias_perdidos or 0),
            jornada_diaria=jornada_diaria,
            notas=notes,
        )

    # Explicit estimated hours from MetricService (already computed upstream)
    if horas_estimadas is not None and float(horas_estimadas) > 0:
        notes.append("Base = horas estimadas pelo MetricService; não somar dias de novo.")
        return HoursBasis(
            kind=HOURS_ESTIMADAS,
            horas=round(float(horas_estimadas), 4),
            dias_perdidos=float(dias_perdidos or 0),
            jornada_diaria=jornada_diaria,
            notas=notes,
        )

    if (
        allow_estimate_from_days
        and jornada_diaria is not None
        and float(jornada_diaria) > 0
        and float(dias_perdidos or 0) > 0
    ):
        horas = float(dias_perdidos) * float(jornada_diaria)
        notes.append(
            "Horas estimadas = dias_perdidos × jornada_diária "
            "(somente porque horas registradas indisponíveis)."
        )
        return HoursBasis(
            kind=HOURS_ESTIMADAS,
            horas=round(horas, 4),
            dias_perdidos=float(dias_perdidos),
            jornada_diaria=float(jornada_diaria),
            notas=notes,
        )

    notes.append("Horas indisponíveis — sem estimativa válida.")
    return HoursBasis(
        kind=HOURS_INDISPONIVEIS,
        horas=None,
        dias_perdidos=float(dias_perdidos or 0),
        jornada_diaria=jornada_diaria,
        notas=notes,
    )


def compute_absenteeism_cost(
    *,
    horas_registradas: Optional[float],
    horas_estimadas: Optional[float] = None,
    dias_perdidos: float = 0.0,
    jornada_diaria: Optional[float] = None,
    custo_hora_real: Optional[float] = None,
    custo_hora_estimado: Optional[float] = None,
    allow_illustrative: bool = False,
    breakdown_seed: Optional[dict[str, Any]] = None,
) -> AbsenteeismCostResult:
    """CUSTO_ESTIMADO = HORAS × CUSTO_HORA when both valid."""
    hours = resolve_hours_basis(
        horas_registradas=horas_registradas,
        horas_estimadas=horas_estimadas,
        dias_perdidos=dias_perdidos,
        jornada_diaria=jornada_diaria,
    )
    assumption = resolve_hourly_assumption(
        valor_real=custo_hora_real,
        valor_estimado=custo_hora_estimado,
        allow_illustrative=allow_illustrative,
    )
    limitations = list(hours.notas)
    limitations.append(assumption.disclaimer)

    formula = "CUSTO_ESTIMADO = HORAS_PERDIDAS × CUSTO_HORA"
    if (
        hours.horas is not None
        and hours.horas > 0
        and assumption.valor is not None
        and assumption.valor > 0
    ):
        custo = round(float(hours.horas) * float(assumption.valor), 2)
        if assumption.estado == ASSUMPTION_ILUSTRATIVO:
            linguagem = (
                f"O volume de {hours.horas:.1f} horas perdidas ({hours.kind}) corresponde a "
                f"impacto laboral estimado de R$ {custo:,.2f} sob a premissa ilustrativa "
                f"de R$ {assumption.valor:.2f}/h. Premissa ilustrativa — substitua pelo "
                f"custo hora real da empresa."
            )
        elif assumption.estado == ASSUMPTION_REAL:
            linguagem = (
                f"O volume de {hours.horas:.1f} horas perdidas ({hours.kind}) corresponde a "
                f"impacto laboral estimado de R$ {custo:,.2f} sob a premissa de custo hora "
                f"informada pela empresa (R$ {assumption.valor:.2f}/h)."
            )
        else:
            linguagem = (
                f"O volume de {hours.horas:.1f} horas perdidas ({hours.kind}) corresponde a "
                f"impacto laboral estimado de R$ {custo:,.2f} sob custo médio estimado "
                f"de R$ {assumption.valor:.2f}/h."
            )
        limitations.append(
            "Não incorpora, nesta versão, custos indiretos (substituição, horas extras, "
            "turnover, presenteísmo ou produtividade secundária)."
        )
        return AbsenteeismCostResult(
            calculavel=True,
            custo_estimado=custo,
            hours=hours,
            assumption=assumption,
            formula=formula,
            linguagem=linguagem,
            limitacoes=limitations,
            breakdown=breakdown_seed or {},
        )

    if hours.horas is None:
        linguagem = "Impacto financeiro não calculável: horas perdidas indisponíveis."
    else:
        linguagem = "Impacto financeiro não calculável: custo hora não informado."
    return AbsenteeismCostResult(
        calculavel=False,
        custo_estimado=None,
        hours=hours,
        assumption=assumption,
        formula=formula,
        linguagem=linguagem,
        limitacoes=limitations,
        breakdown=breakdown_seed or {},
    )


def allocate_cost_by_share(
    total_cost: Optional[float],
    rows: list[dict[str, Any]],
    *,
    value_key: str = "horas",
    label_key: str = "label",
) -> list[dict[str, Any]]:
    """Allocate total cost proportionally by share of hours (or events/days)."""
    if total_cost is None or total_cost <= 0 or not rows:
        return []
    total_v = sum(float(r.get(value_key) or 0) for r in rows)
    if total_v <= 0:
        return []
    out = []
    for r in rows:
        v = float(r.get(value_key) or 0)
        share = v / total_v
        out.append(
            {
                label_key: r.get(label_key) or r.get("nome") or "—",
                value_key: v,
                "participacao": round(share * 100, 2),
                "custo_estimado": round(total_cost * share, 2),
            }
        )
    out.sort(key=lambda x: x["custo_estimado"], reverse=True)
    return out
