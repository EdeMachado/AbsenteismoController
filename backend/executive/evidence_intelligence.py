"""EXEC-10 — BioMed Evidence Intelligence™ composer.

Explains *why* the executive recommendation deserves trust.
Does not invent new analyses — only re-presents existing evidence.
Never sells, never suggests consultancy, never adds commercial CTAs.
"""

from __future__ import annotations

from typing import Any, Optional


_SUPPRESSED = frozenset(
    {"GRUPO_SUPRIMIDO", "?", "N/A", "NA", "NONE", "NULL", "DESCONHECIDO", "UNKNOWN"}
)


def _displayable(label: Optional[str]) -> bool:
    if label is None:
        return False
    s = str(label).strip()
    return bool(s) and s.upper() not in _SUPPRESSED


def _humanize(label: Any) -> str:
    s = str(label or "").strip()
    if not _displayable(s):
        return "Grupo agregado (privacidade)"
    return s


def _chart(payload: dict[str, Any], cid: str) -> Optional[dict[str, Any]]:
    for c in payload.get("charts") or []:
        if c.get("id") == cid and (c.get("categories") or []):
            return c
    return None


def _conf_level(raw: Any, *, cost_estado: Optional[str] = None) -> tuple[str, str]:
    conf_l = str(raw or "baixa").lower()
    if conf_l in {"alta", "high"}:
        level, reason = "Alta", "Série e concentrações estáveis o bastante para priorizar."
    elif conf_l in {"media", "moderada", "medium"}:
        level, reason = "Média", "Sinal útil, com limitações de cobertura ou comparabilidade."
    else:
        level, reason = "Baixa", "Evidência parcial — decidir com cautela e reforçar a base."

    if cost_estado == "ILUSTRATIVO" and level == "Alta":
        level = "Média"
        reason = "Premissa de custo ilustrativa reduz a confiança financeira."
    elif cost_estado == "NAO_INFORMADO" and level == "Alta":
        level = "Média"
        reason = "Custo hora não informado — confiança operacional preservada, financeira limitada."
    return level, reason


def _quality_label(iqb: Any, classificacao: Any) -> str:
    if classificacao:
        return str(classificacao)
    if iqb is None:
        return "Não informado"
    try:
        v = float(iqb)
    except (TypeError, ValueError):
        return "Não informado"
    if v >= 80:
        return "Alta"
    if v >= 60:
        return "Moderada"
    if v >= 40:
        return "Atenção"
    return "Crítica"


def compose_evidence_intelligence(payload: dict[str, Any]) -> dict[str, Any]:
    """Build Evidence Intelligence contract from canonical executive payload."""
    hero = payload.get("hero") or {}
    intel = payload.get("intelligence") or {}
    qualidade = payload.get("qualidade") or {}
    periodo = payload.get("periodo") or {}
    custo = payload.get("custo") or {}
    assumption = custo.get("assumption") or {}
    estado = assumption.get("estado") or "NAO_INFORMADO"
    dx = payload.get("decision_experience") or {}
    dx_header = dx.get("header") or {}
    six = dx.get("six_answers") or {}
    privacy = payload.get("privacy") or {}
    methodology = payload.get("methodology") or {}

    decision_title = dx_header.get("title") or "Decisão prioritária do período"
    problem = six.get("problem") or hero.get("mensagem") or "Fator prioritário na janela analisada."

    conf_level, conf_reason = _conf_level(
        hero.get("confianca") or intel.get("confianca"),
        cost_estado=estado,
    )
    # Prefer decision_experience confidence when already composed
    if isinstance(dx.get("confidence"), dict) and dx["confidence"].get("level"):
        conf_level = dx["confidence"]["level"]
        conf_reason = dx["confidence"].get("reason") or conf_reason

    iqb = qualidade.get("iqb")
    iqb_label = _quality_label(iqb, qualidade.get("classificacao"))
    comparabilidade = qualidade.get("comparabilidade") or periodo.get("comparabilidade") or "bloqueada"
    cobertura_horas = qualidade.get("cobertura_horas") or "indisponivel"

    # --- 1 Summary ---
    summary_bits = [
        problem,
        f"Confiança da evidência: {conf_level}.",
    ]
    if iqb is not None:
        summary_bits.append(f"Qualidade dos dados (IQB): {iqb_label}.")
    else:
        summary_bits.append("IQB não disponível nesta janela.")
    summary = summary_bits[:3]

    # --- 2 Sources (existing methodology + charts — no new analysis) ---
    def _source_label(raw: str | None, human: str) -> str:
        """Map legacy technical labels to institutional language (display only)."""
        tech = {
            "MetricService": "Métricas agregadas",
            "DataQualityService": "Qualidade dos dados",
            "PerformanceService.executive_score": "Score executivo de saúde",
            "rule_engine_deterministic": "Priorização determinística",
            "rule_engine_deterministic_v1": "Priorização determinística",
            "AbsenteeismCostModel": "Modelo de custo laboral",
            "Executive Health Score": "Score executivo de saúde",
        }
        key = (raw or "").strip()
        return tech.get(key, key or human)

    sources: list[dict[str, str]] = [
        {
            "id": "metrics",
            "label": _source_label(methodology.get("metrics"), "Métricas agregadas"),
            "role": "Indicadores e distribuições agregadas do período.",
        },
        {
            "id": "quality",
            "label": _source_label(methodology.get("quality"), "Qualidade dos dados"),
            "role": "Índice de qualidade (IQB) e cobertura.",
        },
        {
            "id": "score",
            "label": _source_label(None, "Score executivo de saúde"),
            "role": "Score descritivo — não preditivo.",
        },
        {
            "id": "intelligence",
            "label": _source_label(methodology.get("intelligence"), "Priorização determinística"),
            "role": "Priorização determinística — necessária validação humana.",
        },
        {
            "id": "cost",
            "label": _source_label(methodology.get("cost"), "Modelo de custo laboral"),
            "role": "Custo laboral com premissa explícita (nunca inventada).",
        },
    ]
    sources = sources[:5]

    charts_present = []
    for cid, label in (
        ("setores", "Distribuição por setor"),
        ("pareto_cid", "Grupos CID (alfabéticos)"),
        ("evolucao_temporal", "Evolução temporal"),
    ):
        if _chart(payload, cid):
            charts_present.append({"id": cid, "label": label})

    # --- 3 Timeline ---
    evo = _chart(payload, "evolucao_temporal")
    timeline = []
    if evo:
        cats = evo.get("categories") or []
        series = evo.get("series") or []
        vals = (series[0].get("data") or []) if series else []
        for i, cat in enumerate(cats[:8]):
            timeline.append(
                {
                    "period": str(cat),
                    "value": float(vals[i]) if i < len(vals) and vals[i] is not None else None,
                    "unit": "eventos",
                }
            )
    tendencia = hero.get("tendencia")
    timeline_note = None
    if tendencia == "melhora":
        timeline_note = "Tendência de melhora na janela — concentração residual ainda prioriza ação."
    elif tendencia == "piora":
        timeline_note = "Tendência de piora na janela — reforça a urgência da decisão."
    elif timeline:
        timeline_note = "Evolução descritiva do volume de eventos no período."
    else:
        timeline_note = "Série temporal insuficiente para leitura de trajetória."

    # --- 4 Quality ---
    dims = qualidade.get("dimensoes") or {}
    quality_dims = []
    for k, v in list(dims.items())[:6]:
        quality_dims.append({"id": str(k), "label": str(k).replace("_", " ").title(), "score": v})
    quality = {
        "iqb": iqb,
        "label": iqb_label,
        "comparability": comparabilidade,
        "hours_coverage": cobertura_horas,
        "dimensions": quality_dims,
        "note": (
            "IQB e dimensões de qualidade — sem inventar denominadores."
            if iqb is not None
            else "Qualidade não quantificada nesta janela."
        ),
    }

    # --- 5 Confidence ---
    confidence = {"level": conf_level, "reason": conf_reason}

    # --- 6 Limitations (executive language — no vendor jargon dump) ---
    limitations: list[str] = []

    def _add_lim(msg: str) -> None:
        msg = str(msg).strip()
        if not msg or msg in limitations:
            return
        # Skip raw engineering dumps unsuitable for CEO reading
        low = msg.lower()
        if any(
            x in low
            for x in (
                "matricula",
                "cpf",
                "nomecompleto",
                "fuzzy",
                "re-upload",
                "deduplic",
                "grupo_alfabetico",
                "dataqualityservice",
                "inventário de denominador",
                "inventario de denominador",
            )
        ):
            return
        limitations.append(msg)

    if comparabilidade != "integral":
        _add_lim("Comparabilidade de baseline bloqueada ou parcial nesta janela.")
    if cobertura_horas == "indisponivel":
        _add_lim("Horas perdidas não registradas — impacto financeiro limitado.")
    if estado == "ILUSTRATIVO":
        _add_lim("Premissa de custo hora ilustrativa — números financeiros não são REAL.")
    elif estado == "NAO_INFORMADO":
        _add_lim("Custo hora não informado — impacto financeiro não calculável.")
    if privacy.get("pii_excluded"):
        _add_lim("Dados nominais e ranking de trabalhadores excluídos por privacidade.")
    for item in (intel.get("limitacoes") or [])[:3]:
        _add_lim(str(item))
    for item in (payload.get("limitations") or [])[:2]:
        _add_lim(str(item))
    _add_lim("Toda leitura é descritiva — causalidade exclusiva não é afirmada.")
    limitations = limitations[:4]
    if not limitations:
        limitations = ["Toda leitura é descritiva — causalidade exclusiva não é afirmada."]

    # --- 7 What we still need ---
    still_need: list[str] = []
    if estado in {"ILUSTRATIVO", "NAO_INFORMADO"}:
        still_need.append("Custo hora real da empresa para elevar a premissa financeira.")
    if cobertura_horas != "registrada":
        still_need.append("Cobertura completa de horas perdidas registradas.")
    if comparabilidade != "integral":
        still_need.append("Baseline comparável integral para fortalecer a tendência.")
    if iqb is None or (isinstance(iqb, (int, float)) and float(iqb) < 70):
        still_need.append("Melhor preenchimento de campos críticos (CID, setor, datas).")
    if not charts_present:
        still_need.append("Distribuições setoriais/CID estáveis na janela.")
    still_need = still_need[:4]
    if not still_need:
        still_need = ["Validação humana do primeiro passo com a área responsável."]

    # --- 8 Executive conclusion ≤ 3 ---
    conclusion = [
        f"A recomendação “{decision_title}” apoia-se em evidência agregada do período.",
        f"Confiança {conf_level.lower()}: {conf_reason}",
    ]
    if limitations:
        conclusion.append(f"Limite principal: {limitations[0]}")
    conclusion = conclusion[:3]

    # Mini bars for timeline visual (reuse categories)
    timeline_visual = {
        "categories": [_humanize(t["period"]) for t in timeline],
        "values": [t["value"] if t["value"] is not None else 0 for t in timeline],
        "unit": "eventos",
    }

    return {
        "engine": "exec10-evidence-intelligence-v1",
        "header": {
            "kicker": "BioMed · Evidências",
            "title": "Como sabemos disso?",
            "decision_title": decision_title,
            "subtitle": "Sustentação da recomendação — sem nova análise.",
        },
        "summary": summary,
        "sources": sources,
        "chart_sources": charts_present,
        "timeline": timeline,
        "timeline_visual": timeline_visual,
        "timeline_note": timeline_note,
        "quality": quality,
        "confidence": confidence,
        "limitations": limitations,
        "still_need": still_need,
        "conclusion": conclusion,
        "privacy": {
            "pii_excluded": bool(privacy.get("pii_excluded", True)),
            "worker_ranking": False,
        },
        "cta_back": "Voltar à decisão",
        "cta_decision": "Voltar à decisão",
        # No commercial footer / no ORBIT sell CTA
    }
