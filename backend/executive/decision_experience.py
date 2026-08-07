"""EXEC-09 — BioMed Executive Decision Experience™ composer.

Transforms the first recommended decision into a visual conversation
answering exactly six questions. Never invents financial figures.
"""

from __future__ import annotations

import re
from typing import Any, Optional


ASSUMPTION_LABELS = {
    "REAL": "REAL",
    "ESTIMADO": "ESTIMADO",
    "ILUSTRATIVO": "ILUSTRATIVO",
    "NAO_INFORMADO": "NÃO INFORMADO",
}

# Privacy / quality placeholders — never surface as CEO-facing labels.
_SUPPRESSED_LABELS = frozenset(
    {
        "GRUPO_SUPRIMIDO",
        "?",
        "N/A",
        "NA",
        "NONE",
        "NULL",
        "DESCONHECIDO",
        "UNKNOWN",
    }
)


def _is_displayable_label(label: Optional[str]) -> bool:
    if label is None:
        return False
    s = str(label).strip()
    if not s:
        return False
    return s.upper() not in _SUPPRESSED_LABELS


def _humanize_category(label: Any) -> str:
    s = str(label or "").strip()
    if not _is_displayable_label(s):
        return "Grupo agregado (privacidade)"
    return s


def _setor_from_text(*texts: Any) -> Optional[str]:
    for t in texts:
        if not t:
            continue
        m = re.search(r"setor\s+([A-Za-zÀ-ÿ0-9][\wÀ-ÿ/\-]*)", str(t), re.IGNORECASE)
        if m and _is_displayable_label(m.group(1)):
            return m.group(1)
    return None


def _chart(payload: dict[str, Any], cid: str) -> Optional[dict[str, Any]]:
    for c in payload.get("charts") or []:
        if c.get("id") == cid and (c.get("categories") or []):
            return c
    return None


def _top_from_chart(chart: Optional[dict[str, Any]], series_idx: int = 0) -> tuple[Optional[str], Optional[float], Optional[float]]:
    if not chart:
        return None, None, None
    cats = chart.get("categories") or []
    series = chart.get("series") or []
    if not cats or not series:
        return None, None, None
    data = series[min(series_idx, len(series) - 1)].get("data") or []
    if not data:
        return None, None, None
    total = sum(float(x or 0) for x in data) or 0.0
    i = max(range(len(data)), key=lambda k: float(data[k] or 0))
    share = round(100.0 * float(data[i] or 0) / total, 1) if total else None
    raw = str(cats[i])
    label = raw if _is_displayable_label(raw) else None
    return label, float(data[i] or 0), share


def _fmt_brl(v: float, *, cents: bool = False) -> str:
    if cents:
        s = f"{v:,.2f}"
    else:
        s = f"{v:,.0f}"
    # US -> pt-BR
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


def _money(v: Any) -> Optional[float]:
    if v is None:
        return None
    try:
        return round(float(v), 2)
    except (TypeError, ValueError):
        return None


def _complexity_from_priority(pri: str) -> str:
    p = (pri or "media").lower()
    if p == "alta":
        return "Média–Alta"
    if p == "baixa":
        return "Baixa"
    return "Média"


def _owner_from_category(cat: Optional[str]) -> str:
    c = (cat or "").lower()
    if "ergo" in c:
        return "SESMT / Operação"
    if "vigil" in c or "cid" in c:
        return "SESMT / Centro Médico"
    if "gest" in c or "condic" in c:
        return "Diretoria / RH"
    return "BioMed + Empresa"


def compose_decision_experience(
    payload: dict[str, Any],
    *,
    seed_decision: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Build Decision Experience contract from canonical executive payload."""
    intel = payload.get("intelligence") or {}
    custo = payload.get("custo") or {}
    assumption = custo.get("assumption") or {}
    estado = assumption.get("estado") or "NAO_INFORMADO"
    estado_label = ASSUMPTION_LABELS.get(estado, estado)
    conf = (payload.get("hero") or {}).get("confianca") or intel.get("confianca") or "baixa"
    impacto_bio = payload.get("impacto_economico_biomed") or {}

    # --- seed decision from first_experience or intelligence ---
    fx = payload.get("first_experience") or {}
    decision = seed_decision or fx.get("decision") or {}
    if not decision.get("title"):
        plano = intel.get("plano_acao") or []
        if plano and isinstance(plano[0], dict):
            a = plano[0]
            decision = {
                "priority": (a.get("priority") or "alta").lower(),
                "title": a.get("title") or a.get("titulo"),
                "description": a.get("justification") or a.get("justificativa") or "",
                "expected_impact": a.get("meta") or a.get("result") or "",
                "deadline": a.get("deadline") or "Próximo ciclo",
            }

    title = decision.get("title") or "Priorizar o fator dominante do período"
    priority = (decision.get("priority") or "alta").lower()
    pri_label = {
        "alta": "Prioridade Alta",
        "media": "Prioridade Média",
        "baixa": "Prioridade Baixa",
    }.get(priority, f"Prioridade {priority}")

    # --- problem focus from evidence ---
    setores = _chart(payload, "setores")
    pareto = _chart(payload, "pareto_cid")
    top_setor, _, share_setor = _top_from_chart(setores, 1 if setores and len((setores.get("series") or [])) > 1 else 0)
    # prefer days series if present
    if setores and len(setores.get("series") or []) > 1:
        top_setor, _, share_setor = _top_from_chart(setores, 1)
    top_cid, _, share_cid = _top_from_chart(pareto, 0)

    # Prefer named sector from decision copy when chart labels were suppressed.
    if not top_setor:
        top_setor = _setor_from_text(
            title,
            decision.get("title"),
            decision.get("description"),
            decision.get("expected_impact"),
        )

    if top_setor and share_setor:
        problem = f"Concentração de perdas no setor {top_setor} ({share_setor}% do volume em dias)."
    elif top_setor:
        problem = f"Concentração de perdas no setor {top_setor}."
    elif top_cid and share_cid:
        problem = f"Concentração de causas no grupo CID {top_cid} ({share_cid}% dos eventos)."
    else:
        problem = (
            decision.get("description")
            or (payload.get("hero") or {}).get("mensagem")
            or "Há um fator prioritário na janela analisada que merece decisão."
        )

    # --- evidence blocks (visual only, short labels) ---
    evidence_items = []
    if setores:
        series = setores.get("series") or []
        # Prefer days series when present (index 1)
        vals = []
        if len(series) > 1:
            vals = (series[1].get("data") or [])[:6]
        elif series:
            vals = (series[0].get("data") or [])[:6]
        cats = [_humanize_category(c) for c in (setores.get("categories") or [])[:6]]
        evidence_items.append(
            {
                "id": "setores",
                "label": "Setores — dias perdidos",
                "kind": "bar",
                "categories": cats,
                "values": vals,
                "unit": "dias",
            }
        )
    if pareto:
        evidence_items.append(
            {
                "id": "pareto_cid",
                "label": "Grupos CID — eventos",
                "kind": "bar",
                "categories": [
                    _humanize_category(c) for c in (pareto.get("categories") or [])[:6]
                ],
                "values": ((pareto.get("series") or [{}])[0].get("data") or [])[:6],
                "unit": "eventos",
            }
        )
    evo = _chart(payload, "evolucao_temporal")
    if evo:
        evidence_items.append(
            {
                "id": "evolucao_temporal",
                "label": "Evolução — eventos",
                "kind": "line",
                "categories": (evo.get("categories") or [])[:8],
                "values": ((evo.get("series") or [{}])[0].get("data") or [])[:8],
                "unit": "eventos",
            }
        )
    # KPIs as indicator chips
    indicators = []
    for k in (fx.get("kpis") or payload.get("kpis_primary") or [])[:4]:
        if isinstance(k, dict):
            indicators.append(
                {
                    "id": k.get("id"),
                    "label": k.get("label"),
                    "value": k.get("value") if k.get("available") is not False else None,
                    "unit": k.get("unit"),
                    "available": k.get("available") is not False and k.get("value") is not None,
                }
            )

    # --- business impact (never invent) ---
    cost_today = None
    if custo.get("calculavel"):
        cost_today = _money(custo.get("custo_estimado"))
    hours = (custo.get("hours") or {}).get("horas")
    hourly = assumption.get("valor")

    cost_if_nothing = None
    cost_if_nothing_note = "Projeção futura não calculada — sem modelo contrafactual nesta versão."
    # Do not invent escalation; only show if we have explicit comparable worsening signal
    trend = (payload.get("hero") or {}).get("tendencia")
    if cost_today is not None and trend == "piora":
        cost_if_nothing_note = (
            "Tendência de piora na janela; impacto futuro depende da trajetória — "
            "sem projeção numérica inventada."
        )
    else:
        cost_if_nothing = None

    savings = _money(impacto_bio.get("custo_evitado_estimado"))
    savings_note = None
    if savings is not None:
        savings_note = (
            impacto_bio.get("linguagem")
            or "Margem estimada sob premissa de custo hora; sem causalidade exclusiva."
        )
    elif cost_today is not None:
        savings_note = (
            "Economia potencial não calculável sem redução observada de horas "
            "na janela comparável e premissa válida."
        )
    else:
        savings_note = "Economia potencial indisponível — custo hora ou horas não informados."

    business_impact = {
        "cost_today": {
            "label": "Quanto custa hoje?",
            "value": cost_today,
            "assumption_state": estado_label,
            "available": cost_today is not None,
            "note": custo.get("linguagem")
            if cost_today is not None
            else "Impacto financeiro não calculável com as premissas atuais.",
            "hours": hours,
            "hourly_rate": hourly if estado != "NAO_INFORMADO" else None,
        },
        "cost_if_nothing": {
            "label": "Quanto poderá custar?",
            "value": cost_if_nothing,
            "assumption_state": estado_label if cost_today is not None else "NÃO INFORMADO",
            "available": False,
            "note": cost_if_nothing_note,
        },
        "savings_potential": {
            "label": "Quanto pode economizar?",
            "value": savings,
            "assumption_state": estado_label if savings is not None else (
                estado_label if cost_today is not None else "NÃO INFORMADO"
            ),
            "available": savings is not None,
            "note": savings_note,
            "caveat": "Não implica atribuição causal exclusiva à BioMed.",
        },
    }

    # --- why ≤ 3 sentences ---
    why = []
    why.append(problem if isinstance(problem, str) else str(problem))
    risco = (intel.get("onde_esta_o_risco") or [None])[0]
    if risco:
        risco_s = str(risco)
        if any(bad in risco_s for bad in ("GRUPO_SUPRIMIDO",)):
            risco_s = f"Concentração setorial: {top_setor}" if top_setor else ""
        if risco_s and risco_s not in why:
            why.append(risco_s)
    cond = payload.get("conditionants_summary")
    if cond and len(why) < 3:
        why.append(str(cond))
    elif decision.get("description") and len(why) < 3:
        desc = str(decision["description"])
        if desc not in why:
            why.append(desc)
    why = why[:3]

    # --- recommendations ≤ 3 ---
    recs = []
    for a in (intel.get("plano_acao") or [])[:3]:
        if not isinstance(a, dict):
            continue
        recs.append(
            {
                "title": a.get("title") or a.get("titulo"),
                "impact": a.get("meta") or a.get("result") or a.get("justification") or "Impacto a validar",
                "deadline": a.get("deadline") or a.get("prazo") or "Próximo ciclo",
                "complexity": _complexity_from_priority(a.get("priority") or a.get("prioridade") or priority),
                "owner": _owner_from_category(a.get("category") or a.get("categoria")),
                "priority": (a.get("priority") or a.get("prioridade") or priority),
            }
        )
    if not recs:
        for t in (intel.get("o_que_recomendamos") or [])[:3]:
            recs.append(
                {
                    "title": t,
                    "impact": "Redução do fator prioritário, se executada",
                    "deadline": "Próximo ciclo",
                    "complexity": _complexity_from_priority(priority),
                    "owner": "BioMed + Empresa",
                    "priority": priority,
                }
            )
    if not recs:
        recs = [
            {
                "title": title,
                "impact": decision.get("expected_impact") or "Melhora do fator prioritário",
                "deadline": decision.get("deadline") or "Próximo ciclo",
                "complexity": _complexity_from_priority(priority),
                "owner": "BioMed + Empresa",
                "priority": priority,
            }
        ]
    recs = recs[:3]
    first_step = recs[0]["title"] if recs else title

    # --- roadmap visual ---
    roadmap = [
        {"horizon": "30 dias", "focus": f"Validar e iniciar: {first_step}"},
        {
            "horizon": "90 dias",
            "focus": "Executar ações prioritárias e remover condicionantes bloqueantes",
        },
        {
            "horizon": "180 dias",
            "focus": "Medir redução de dias/horas no cluster prioritário",
        },
        {
            "horizon": "365 dias",
            "focus": "Consolidar protocolo e revisar maturidade da evidência",
        },
    ]

    # --- expected results (qualitative, no invented money) ---
    expected_results = {
        "financial": (
            f"Impacto laboral estimado atual de {_fmt_brl(cost_today)} sob premissa {estado_label}."
            if cost_today is not None
            else "Impacto financeiro só após premissa de custo hora e horas válidas."
        ),
        "operational": (
            f"Foco operacional no setor {top_setor}."
            if top_setor
            else "Redução de fricção no fator prioritário identificado."
        ),
        "health": (
            f"Vigilância do grupo CID {top_cid} (alfabético, não capítulo oficial)."
            if top_cid and _is_displayable_label(top_cid)
            else "Melhor alinhamento prevenção ↔ padrão observado."
        ),
        "governance": (
            payload.get("conditionants_summary")
            or "Decisão explícita com validação humana e sem autoexecução."
        ),
    }

    # --- confidence ---
    conf_l = str(conf).lower()
    if conf_l in {"alta", "high"}:
        conf_level = "Alta"
        conf_reason = "Série e concentrações estáveis o bastante para priorizar."
    elif conf_l in {"media", "moderada", "medium"}:
        conf_level = "Média"
        conf_reason = "Sinal útil, com limitações de cobertura ou comparabilidade."
    else:
        conf_level = "Baixa"
        conf_reason = "Evidência parcial — decidir com cautela e reforçar a base."

    if estado == "ILUSTRATIVO" and conf_level == "Alta":
        conf_level = "Média"
        conf_reason = "Premissa de custo ilustrativa reduz a confiança financeira."

    how_to_solve = "; ".join(r["title"] for r in recs[:3])

    return {
        "engine": "exec09-decision-experience-v1",
        "header": {
            "title": title,
            "priority": priority,
            "priority_label": pri_label,
            "impact": decision.get("expected_impact")
            or (f"Atuar sobre {top_setor}" if top_setor else "Reduzir o fator prioritário"),
            "estimated_time": decision.get("deadline") or "30–90 dias para primeiro ciclo",
        },
        "evidence": {
            "charts": evidence_items[:3],
            "indicators": indicators,
        },
        "business_impact": business_impact,
        "why": why,
        "recommendations": recs,
        "roadmap": roadmap,
        "expected_results": expected_results,
        "confidence": {"level": conf_level, "reason": conf_reason},
        "footer_note": (
            "Caso a organização deseje aprofundar esta iniciativa, "
            "ela poderá estruturá-la utilizando a metodologia BioMed ORBIT™."
        ),
        "six_answers": {
            "problem": problem,
            "how_we_know": (
                "Evidências agregadas de setor/CID/tendência no período — sem identificação nominal."
            ),
            "cost": (
                f"{_fmt_brl(cost_today, cents=True)} ({estado_label})"
                if cost_today is not None
                else f"Não calculável ({estado_label})"
            ),
            "save": (
                f"{_fmt_brl(savings, cents=True)} estimado sob premissa — sem causalidade exclusiva"
                if savings is not None
                else "Não calculável com a evidência atual"
            ),
            "how": how_to_solve,
            "first_step": first_step,
        },
        "privacy": {"pii_excluded": True, "worker_ranking": False},
        "cta_back": "Voltar à abertura",
    }
