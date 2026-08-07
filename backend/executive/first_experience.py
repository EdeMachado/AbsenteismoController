"""EXEC-08 — First CEO experience composer (read-only view of existing aggregates).

No new metrics formulas. Derives a premium first-screen contract from the
command-center payload already built by MetricService / intelligence / cost.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional


def _kpi_by_id(kpis: list[dict[str, Any]], kid: str) -> Optional[dict[str, Any]]:
    for k in kpis or []:
        if k.get("id") == kid:
            return k
    return None


def _fmt_money(v: Any) -> Optional[float]:
    if v is None:
        return None
    try:
        return round(float(v), 2)
    except (TypeError, ValueError):
        return None


def compose_first_experience(payload: dict[str, Any]) -> dict[str, Any]:
    """Build the EXEC-08 first-screen contract.

    Blocks: hero · opening_phrase · summary (≤3) · score · 4 KPIs · one decision.
    """
    hero = payload.get("hero") or {}
    intel = payload.get("intelligence") or {}
    score = hero.get("score") or payload.get("executive_score") or {}
    custo = payload.get("custo") or {}
    kpis = payload.get("kpis") or []
    periodo = payload.get("periodo") or {}
    atual = periodo.get("atual") or {}
    competencia = None
    if atual.get("inicio") and atual.get("fim"):
        if atual["inicio"] == atual["fim"]:
            competencia = str(atual["inicio"])
        else:
            competencia = f"{atual['inicio']} → {atual['fim']}"
    else:
        competencia = hero.get("periodo")

    dias = _kpi_by_id(kpis, "dias")
    horas = _kpi_by_id(kpis, "horas")
    custo_kpi = _kpi_by_id(kpis, "custo")

    # Four KPIs only — hours, days, estimated cost, executive score
    four = [
        {
            "id": "horas",
            "label": "Horas perdidas",
            "value": horas.get("value") if horas and horas.get("available") else None,
            "unit": "h",
            "available": bool(horas and horas.get("available")),
            "empty_label": (horas or {}).get("empty_label")
            or "Horas registradas indisponíveis",
            "trend": (horas or {}).get("trend"),
        },
        {
            "id": "dias",
            "label": "Dias perdidos",
            "value": dias.get("value") if dias and dias.get("available") is not False else (dias or {}).get("value"),
            "unit": "dias",
            "available": dias is not None and dias.get("available") is not False,
            "empty_label": (dias or {}).get("empty_label") or "Dias indisponíveis",
            "trend": (dias or {}).get("trend"),
        },
        {
            "id": "custo",
            "label": "Custo estimado",
            "value": _fmt_money(custo.get("custo_estimado"))
            if custo.get("calculavel")
            else (custo_kpi.get("value") if custo_kpi and custo_kpi.get("available") else None),
            "unit": "R$",
            "available": bool(custo.get("calculavel")),
            "empty_label": "Custo não calculável com as premissas atuais",
            "trend": None,
            "premissa": (custo.get("assumption") or {}).get("estado"),
        },
        {
            "id": "score",
            "label": "Executive Score",
            "value": score.get("score") if score.get("available") else None,
            "unit": "",
            "available": bool(score.get("available")),
            "empty_label": "Score não disponível — cobertura insuficiente",
            "trend": None,
        },
    ]

    # Summary ≤ 3 phrases: how is the company / what needs attention / priority
    status = hero.get("status") or "descritivo"
    tendencia = hero.get("tendencia")
    conf = hero.get("confianca") or intel.get("confianca") or "baixa"

    como_esta = hero.get("mensagem") or intel.get("mensagem_executiva")
    if not como_esta:
        if tendencia == "melhora":
            como_esta = "A empresa apresenta sinal de melhora na janela analisada."
        elif tendencia == "piora":
            como_esta = "A empresa apresenta sinal de piora na janela analisada."
        else:
            como_esta = "A leitura do período está disponível em modo descritivo."

    atencao_parts = intel.get("onde_esta_o_risco") or []
    if atencao_parts:
        atencao = atencao_parts[0]
    else:
        setores = []
        for c in payload.get("charts") or []:
            if c.get("id") == "setores" and c.get("categories"):
                setores = c["categories"]
                break
        atencao = (
            f"Atenção ao setor {setores[0]}."
            if setores
            else "Atenção à qualidade da base e à cobertura de horas."
        )

    prioridade = (intel.get("o_que_recomendamos") or [None])[0]
    if not prioridade:
        plano = intel.get("plano_acao") or []
        if plano and isinstance(plano[0], dict):
            prioridade = plano[0].get("title") or plano[0].get("titulo")
        else:
            prioridade = "Priorizar validação das evidências do período."

    summary = [como_esta, atencao, f"Prioridade: {prioridade}"]
    summary = [s for s in summary if s][:3]

    opening = hero.get("mensagem") or intel.get("mensagem_executiva") or summary[0]

    # Single decision
    decision = None
    plano = intel.get("plano_acao") or []
    if plano and isinstance(plano[0], dict):
        a = plano[0]
        decision = {
            "priority": (a.get("priority") or a.get("prioridade") or "alta").lower(),
            "title": a.get("title") or a.get("titulo") or "Revisar prioridade do período",
            "description": a.get("justification")
            or a.get("justificativa")
            or a.get("title")
            or "",
            "expected_impact": a.get("meta")
            or a.get("result")
            or "Redução material do fator prioritário, sujeita a validação.",
            "deadline": a.get("deadline") or a.get("prazo") or "Próximo ciclo",
            "cta": "Entender esta decisão",
        }
    elif intel.get("o_que_recomendamos"):
        decision = {
            "priority": "alta",
            "title": intel["o_que_recomendamos"][0],
            "description": (intel.get("por_que_importa") or [""])[0]
            or "Ação derivada da leitura executiva do período.",
            "expected_impact": "Melhora do fator prioritário, se executada e medida.",
            "deadline": "Próximo ciclo",
            "cta": "Entender esta decisão",
        }
    else:
        decision = {
            "priority": "media",
            "title": "Consolidar premissas e qualidade da base",
            "description": (
                "Sem ação prioritária elegível com evidência forte; "
                "fortalecer cobertura de dados antes de intervir."
            ),
            "expected_impact": "Leitura mais confiável no próximo ciclo.",
            "deadline": "Próximo ciclo",
            "cta": "Entender esta decisão",
        }

    op_status = "Comparável" if status == "comparavel" else "Descritivo"
    if (payload.get("qualidade") or {}).get("iqb") is not None:
        iqb = payload["qualidade"]["iqb"]
        try:
            if float(iqb) < 50:
                op_status = "Atenção à qualidade dos dados"
        except (TypeError, ValueError):
            pass

    return {
        "engine": "exec08-first-experience-v1",
        "hero": {
            "company": hero.get("empresa") or (payload.get("client") or {}).get("label"),
            "competencia": competencia,
            "score": {
                "available": bool(score.get("available")),
                "value": score.get("score") if score.get("available") else None,
                "label": score.get("label") or "Executive Score",
            },
            "trend": tendencia,
            "confidence": conf,
            "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "operational_status": op_status,
            "opening_phrase": opening,
        },
        "summary": summary,
        "kpis": four,
        "decision": decision,
        "privacy": {"pii_excluded": True},
    }
