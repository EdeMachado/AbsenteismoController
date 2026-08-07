"""EXEC-03 enrichment helpers — cost, recurrence, catalog flags, temporal hours.

Kept separate from aggregate_service core to preserve EXEC-01/02 behavior.
"""

from __future__ import annotations

import os
from collections import Counter, defaultdict
from datetime import date
from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.executive.analytics_catalog import evaluate_catalog
from backend.executive.cost_model import (
    allocate_cost_by_share,
    compute_absenteeism_cost,
)
from backend.executive.schemas import ChartSeries, KpiCard
from backend.models import Atestado, Upload
from backend.services.metric_service import worker_identity_parts


def allow_illustrative_cost() -> bool:
    """Illustrative hourly cost only with explicit staging demo gate — never by ENVIRONMENT alone."""
    return (os.environ.get("EXECUTIVE_STAGING_DEMO") or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

def resolve_client_hourly_cost(client: Any) -> tuple[Optional[float], Optional[float]]:
    """Read optional hourly cost from client attrs / env fixture — no DB migration.

    Production persistence deferred; experimental env/fixture only.
    """
    real = getattr(client, "custo_hora_real", None)
    estimado = getattr(client, "custo_hora_estimado", None)
    # Experimental fixture (never treated as production default)
    env_real = (os.environ.get("EXECUTIVE_HOURLY_COST_REAL") or "").strip()
    env_est = (os.environ.get("EXECUTIVE_HOURLY_COST_ESTIMADO") or "").strip()
    if real is None and env_real:
        try:
            real = float(env_real)
        except ValueError:
            real = None
    if estimado is None and env_est:
        try:
            estimado = float(env_est)
        except ValueError:
            estimado = None
    return real, estimado


def compute_recurrence_aggregate(
    db: Session,
    client_id: int,
    periodo_inicio: str,
    periodo_fim: str,
) -> Optional[dict[str, Any]]:
    """Aggregate recurrence buckets — no worker names/CPF/matrícula."""
    rows = (
        db.query(Atestado)
        .join(Upload, Atestado.upload_id == Upload.id)
        .filter(Upload.client_id == client_id)
        .all()
    )
    counts: Counter[str] = Counter()
    days_by: dict[str, float] = defaultdict(float)
    hours_by: dict[str, float] = defaultdict(float)
    total_events = 0
    total_days = 0.0
    total_hours = 0.0

    for row in rows:
        mes = None
        if row.data_afastamento:
            mes = f"{row.data_afastamento.year:04d}-{row.data_afastamento.month:02d}"
        elif getattr(row, "mes_referencia", None):
            mes = str(row.mes_referencia)[:7]
        else:
            up = row.upload if hasattr(row, "upload") else None
            if up and up.mes_referencia:
                mes = str(up.mes_referencia)[:7]
        if mes and (mes < periodo_inicio or mes > periodo_fim):
            continue

        kind, key = worker_identity_parts(row)
        if not key:
            continue
        # Hash-like opaque token — never expose raw key in payload
        opaque = f"w{abs(hash(key)) % 10_000_000:07d}"
        counts[opaque] += 1
        total_events += 1
        d = float(row.dias_perdidos or row.dias_atestados or 0) or 0.0
        h = float(row.horas_perdi or row.horas_perdidas or 0) or 0.0
        days_by[opaque] += d
        hours_by[opaque] += h
        total_days += d
        total_hours += h

    if not counts:
        return None

    n_2 = sum(1 for c in counts.values() if c >= 2)
    n_3 = sum(1 for c in counts.values() if c >= 3)
    n_5 = sum(1 for c in counts.values() if c >= 5)
    ev_2 = sum(c for c in counts.values() if c >= 2)
    days_2 = sum(days_by[k] for k, c in counts.items() if c >= 2)
    hours_2 = sum(hours_by[k] for k, c in counts.items() if c >= 2)

    return {
        "n_trabalhadores_com_evento": len(counts),
        "n_2plus": n_2,
        "n_3plus": n_3,
        "n_5plus": n_5,
        "share_eventos_2plus": round(100.0 * ev_2 / total_events, 2) if total_events else None,
        "share_dias_2plus": round(100.0 * days_2 / total_days, 2) if total_days else None,
        "share_horas_2plus": round(100.0 * hours_2 / total_hours, 2) if total_hours else None,
        "privacy": "aggregate_only",
        "nota": "Sem identificação nominal. Investigação clínica autorizada é superfície separada.",
    }


def weekday_distribution(
    db: Session,
    client_id: int,
    periodo_inicio: str,
    periodo_fim: str,
) -> Optional[list[dict[str, Any]]]:
    rows = (
        db.query(Atestado)
        .join(Upload, Atestado.upload_id == Upload.id)
        .filter(Upload.client_id == client_id)
        .all()
    )
    labels = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    bucket = [0] * 7
    any_date = False
    for row in rows:
        if not row.data_afastamento:
            continue
        d: date = row.data_afastamento
        mes = f"{d.year:04d}-{d.month:02d}"
        if mes < periodo_inicio or mes > periodo_fim:
            continue
        any_date = True
        bucket[d.weekday()] += 1
    if not any_date or sum(bucket) == 0:
        return None
    return [{"dia": labels[i], "eventos": bucket[i]} for i in range(7)]


def cargo_distribution(
    db: Session,
    client_id: int,
    periodo_inicio: str,
    periodo_fim: str,
    *,
    threshold: int = 5,
) -> Optional[list[dict[str, Any]]]:
    rows = (
        db.query(Atestado)
        .join(Upload, Atestado.upload_id == Upload.id)
        .filter(Upload.client_id == client_id)
        .all()
    )
    mapa: dict[str, dict[str, Any]] = {}
    has_cargo = False
    for row in rows:
        cargo = (row.cargo or "").strip()
        if not cargo:
            continue
        has_cargo = True
        # period filter via data when available
        if row.data_afastamento:
            mes = f"{row.data_afastamento.year:04d}-{row.data_afastamento.month:02d}"
            if mes < periodo_inicio or mes > periodo_fim:
                continue
        b = mapa.setdefault(cargo, {"eventos": 0, "dias": 0.0, "workers": set()})
        b["eventos"] += 1
        b["dias"] += float(row.dias_perdidos or row.dias_atestados or 0) or 0.0
        _, key = worker_identity_parts(row)
        if key:
            b["workers"].add(f"w{abs(hash(key)) % 10_000_000:07d}")
    if not has_cargo or not mapa:
        return None
    out = []
    for label, data in mapa.items():
        n = len(data["workers"])
        if 0 < n < threshold:
            continue
        out.append(
            {
                "cargo": label,
                "eventos": data["eventos"],
                "dias_perdidos": round(data["dias"], 4),
                "trabalhadores_unicos": n,
            }
        )
    out.sort(key=lambda x: (-x["dias_perdidos"], -x["eventos"]))
    return out[:15] or None


def build_cost_block(
    cur: dict[str, Any],
    client: Any,
    serie_temporal: list[dict[str, Any]],
) -> dict[str, Any]:
    real, estimado = resolve_client_hourly_cost(client)
    result = compute_absenteeism_cost(
        horas_registradas=cur.get("horas_perdidas"),
        horas_estimadas=cur.get("horas_estimadas"),
        dias_perdidos=float(cur.get("dias_perdidos") or 0),
        jornada_diaria=None,  # only via MetricService estimates already in horas_estimadas
        custo_hora_real=real,
        custo_hora_estimado=estimado,
        allow_illustrative=allow_illustrative_cost(),
    )
    data = result.to_dict()

    # Cost by CID / sector via share of days (proxy when hours per row absent)
    cid_rows = []
    for item in cur.get("distribuicao_cid") or []:
        if isinstance(item, dict):
            cid_rows.append(
                {
                    "label": item.get("grupo")
                    or item.get("grupo_alfabetico_cid")
                    or item.get("letra")
                    or "?",
                    "horas": float(item.get("dias_perdidos") or item.get("dias") or 0),
                }
            )
    setor_rows = []
    for item in cur.get("distribuicao_setor") or []:
        if isinstance(item, dict):
            setor_rows.append(
                {
                    "label": item.get("setor") or item.get("nome") or "?",
                    "horas": float(item.get("dias_perdidos") or item.get("dias") or 0),
                }
            )
    cc_rows = []
    for item in cur.get("distribuicao_centro_custo") or []:
        if isinstance(item, dict):
            cc_rows.append(
                {
                    "label": item.get("centro_custo") or "?",
                    "horas": float(item.get("dias_perdidos") or item.get("dias") or 0),
                }
            )

    custo_total = data.get("custo_estimado")
    breakdown = {
        "por_cid": allocate_cost_by_share(custo_total, cid_rows),
        "por_setor": allocate_cost_by_share(custo_total, setor_rows),
        "por_centro_custo": allocate_cost_by_share(custo_total, cc_rows),
        "alocacao_base": "participação em dias_perdidos (proxy) — não inventa horas por linha",
        "evolucao": [],
        "evolucao_chart": None,
        "custo_evitado": None,
        "waterfall": None,
        "indiretos": {
            "disponivel": False,
            "nota": "Custos indiretos preparados na arquitetura; sem dados nesta versão.",
        },
    }

    # Monthly cost evolution when hours present in series
    evo = []
    cats, vals = [], []
    if data.get("calculavel") and (data.get("assumption") or {}).get("valor"):
        rate = float(data["assumption"]["valor"])
        for item in serie_temporal or []:
            h = item.get("horas")
            if h is None:
                # estimate from days only if hours basis is estimated globally
                if data["hours"]["kind"] == "estimadas" and item.get("dias"):
                    # proportional: use days share of total days * total hours
                    continue
                continue
            custo_m = round(float(h) * rate, 2)
            evo.append({"mes": item.get("mes"), "custo_estimado": custo_m, "horas": h})
            cats.append(str(item.get("mes")))
            vals.append(custo_m)
        # If no per-month hours, allocate total cost by event share
        if not evo and serie_temporal and custo_total:
            tot_ev = sum(float(x.get("eventos") or 0) for x in serie_temporal) or 1
            for item in serie_temporal:
                share = float(item.get("eventos") or 0) / tot_ev
                custo_m = round(float(custo_total) * share, 2)
                evo.append(
                    {
                        "mes": item.get("mes"),
                        "custo_estimado": custo_m,
                        "horas": None,
                        "metodo": "alocacao_por_eventos",
                    }
                )
                cats.append(str(item.get("mes")))
                vals.append(custo_m)
        if cats:
            breakdown["evolucao_chart"] = ChartSeries(
                id="custo_evolucao",
                title="Evolução do impacto laboral estimado (R$)",
                chart_type="line",
                categories=cats,
                series=[{"name": "Custo estimado", "data": vals}],
                notes=[
                    data.get("assumption", {}).get("disclaimer") or "",
                    "Não é prejuízo contábil auditado.",
                ],
            ).to_dict()

    breakdown["evolucao"] = evo
    data["breakdown"] = breakdown
    return data


def biomed_economic_impact(
    cur: dict[str, Any],
    base: Optional[dict[str, Any]],
    custo: dict[str, Any],
) -> Optional[dict[str, Any]]:
    if not base:
        return None
    h_cur = cur.get("horas_perdidas") or cur.get("horas_estimadas")
    h_base = base.get("horas_perdidas") or base.get("horas_estimadas")
    if h_cur is None or h_base is None:
        # fall back to days delta × implied hours only if cost hours known
        return {
            "horas_delta": None,
            "linguagem": (
                "Comparativo de horas indisponível — impacto econômico da atuação "
                "não calculado. Não implica atribuição causal exclusiva à BioMed."
            ),
            "causalidade_exclusiva": False,
        }
    delta = float(h_base) - float(h_cur)  # positive = fewer absences now
    rate = (custo.get("assumption") or {}).get("valor")
    equiv = round(delta * float(rate), 2) if rate and delta else None
    parts = [
        f"A variação observada corresponde a {abs(delta):.1f} horas "
        f"{'a menos' if delta > 0 else 'a mais'} de ausência na janela comparável."
    ]
    if equiv is not None and delta > 0:
        parts.append(
            f"Equivalente a R$ {equiv:,.2f} de impacto laboral evitado estimado "
            f"sob a premissa de custo hora informada."
        )
    parts.append("Não implica atribuição causal exclusiva à BioMed.")
    return {
        "horas_delta": round(delta, 4),
        "custo_evitado_estimado": equiv if delta > 0 else None,
        "linguagem": " ".join(parts),
        "causalidade_exclusiva": False,
    }


def catalog_availability(payload_flags: dict[str, bool]) -> list[dict[str, Any]]:
    return evaluate_catalog(payload_flags)


def cost_kpi(custo: dict[str, Any]) -> KpiCard:
    calc = bool(custo.get("calculavel"))
    return KpiCard(
        id="custo",
        label="Impacto laboral estimado",
        value=custo.get("custo_estimado") if calc else None,
        unit="R$",
        available=calc,
        unavailable_reason=None if calc else "Custo hora ou horas indisponíveis",
        empty_label=(
            custo.get("linguagem")
            or "Impacto financeiro não calculável com as premissas atuais."
        ),
        tier="primary",
        confidence=(custo.get("assumption") or {}).get("estado"),
    )


def enrich_centro_custo(metrics_result: Any) -> list[dict[str, Any]]:
    dist = getattr(metrics_result, "distribuicao_centro_custo", None) or []
    out = []
    for item in dist:
        if hasattr(item, "__dict__") and not isinstance(item, dict):
            d = {k: v for k, v in vars(item).items() if not k.startswith("_")}
            for k in list(d.keys()):
                if isinstance(d[k], set):
                    d[k] = len(d[k])
            out.append(d)
        else:
            out.append(item)
    return out


def build_availability_flags(payload: dict[str, Any], cur: dict[str, Any]) -> dict[str, bool]:
    charts = {c.get("id"): c for c in (payload.get("charts") or [])}
    custo = payload.get("custo") or {}
    iqb = payload.get("qualidade") or {}
    serie = cur.get("serie_temporal") or []
    has_serie = len(serie) >= 2
    has_horas_serie = any(x.get("horas") is not None for x in serie)
    return {
        "serie_temporal": has_serie,
        "serie_temporal_horas": has_horas_serie,
        "baseline": payload.get("periodo", {}).get("comparabilidade") == "integral",
        "distribuicao_cid": bool(cur.get("distribuicao_cid")),
        "distribuicao_cid_horas": False,  # hours per CID group not in MetricService yet
        "distribuicao_setor": bool(cur.get("distribuicao_setor")),
        "distribuicao_setor_horas": False,
        "heatmap_setor_mes": False,
        "distribuicao_centro_custo": bool(cur.get("distribuicao_centro_custo")),
        "distribuicao_cargo": bool(payload.get("distribuicao_cargo")),
        "distribuicao_dia_semana": bool(payload.get("padroes_temporais")),
        "distribuicao_faixa_horaria": False,
        "distribuicao_duracao": False,
        "afastamentos_longos": payload.get("afastamentos_longos") is not None,
        "recorrencia_agregada": bool(payload.get("recorrencia_agregada")),
        "distribuicao_genero": False,
        "distribuicao_faixa_etaria": False,
        "janela_intervencao": False,
        "biomed_performance": bool(payload.get("biomed_performance")),
        "iqb": iqb.get("iqb") is not None,
        "iqb_dimensoes": bool(iqb.get("dimensoes")),
        "cobertura_horas": True,
        "conditionants": bool(payload.get("conditionants")),
        "custo": bool(custo.get("calculavel")),
    }
