"""Executive Presentation Premium — RC-1.4.

CEO meeting deck: short, visual, financial, evidence-based.
Each slide answers one executive question. Auto-omits when evidence is insufficient.
Legacy /apresentacao untouched. Business APIs unchanged (same /api/executive/presentation).
"""

from __future__ import annotations

from typing import Any, Optional


# Premium CEO structure (RC-1.4). Max ~15; omitted when evidence insufficient.
SLIDE_DEFS: list[dict[str, Any]] = [
    {"id": "cover", "title": "Capa", "question": None, "required": ["hero"]},
    {"id": "state", "title": "Estado da empresa", "question": "Como está a empresa agora?", "required": ["hero"]},
    {
        "id": "financial",
        "title": "Impacto financeiro",
        "question": "Quanto estamos perdendo?",
        "required": ["impacto_operacional"],
    },
    {
        "id": "where",
        "title": "Onde está o problema?",
        "question": "Onde está o problema?",
        "required": ["chart:setores"],
    },
    {
        "id": "causes",
        "title": "O que mais afasta?",
        "question": "Por que estamos perdendo?",
        "required": ["chart:pareto_cid"],
    },
    {
        "id": "recurrence",
        "title": "Como o problema se repete?",
        "question": "Por que estamos perdendo?",
        "required": ["recorrencia_agregada"],
    },
    {
        "id": "when",
        "title": "Quando acontece?",
        "question": "Por que estamos perdendo?",
        "required": ["padroes_temporais"],
    },
    {
        "id": "changed",
        "title": "O que mudou?",
        "question": "O que mudou no período?",
        "required": ["chart:evolucao_temporal"],
    },
    {
        "id": "biomed",
        "title": "Atuação BioMed",
        "question": "O que já foi feito?",
        "required": ["biomed_performance"],
    },
    {
        "id": "savings",
        "title": "Quanto podemos melhorar?",
        "question": "Quanto podemos melhorar/economizar?",
        "required": ["savings_valid"],
    },
    {
        "id": "inaction",
        "title": "E se nada mudar?",
        "question": "Quanto podemos melhorar/economizar?",
        "required": ["inaction_valid"],
    },
    {
        "id": "priorities",
        "title": "As 3 prioridades",
        "question": "O que precisamos decidir agora?",
        "required": ["plano_acao"],
    },
    {
        "id": "roadmap",
        "title": "Roteiro",
        "question": "O que precisamos decidir agora?",
        "required": ["plano_acao"],
    },
    {
        "id": "decision",
        "title": "Decisão executiva",
        "question": "O que precisa ser decidido hoje?",
        "required": ["decision_valid"],
    },
    {
        "id": "closing",
        "title": "Encerramento",
        "question": None,
        "required": ["hero"],
    },
]

# Kept for regression callers that still import the symbol name
LEGACY_SLIDE_COUNT = 18
PREMIUM_SLIDE_COUNT = len(SLIDE_DEFS)


def _has(payload: dict[str, Any], key: str) -> bool:
    if key == "custo_calculavel":
        return bool((payload.get("custo") or {}).get("calculavel"))
    if key == "impacto_operacional":
        # Hours/days KPIs always allow the financial slide; cost may be NÃO INFORMADO
        kpis = payload.get("kpis_primary") or payload.get("kpis") or []
        ids = {k.get("id") for k in kpis}
        return bool(ids & {"horas", "dias", "eventos"}) or bool(payload.get("custo"))
    if key == "plano_acao":
        return bool(((payload.get("intelligence") or {}).get("plano_acao") or []))
    if key == "afastamentos_longos":
        return payload.get("afastamentos_longos") is not None
    if key == "padroes_temporais":
        return bool(payload.get("padroes_temporais"))
    if key == "recorrencia_agregada":
        return bool(payload.get("recorrencia_agregada"))
    if key == "conditionants":
        return bool(payload.get("conditionants"))
    if key == "savings_valid":
        eco = payload.get("impacto_economico_biomed") or {}
        dx = payload.get("decision_experience") or {}
        bi = (dx.get("business_impact") or {}).get("savings_potential") or {}
        return bool(eco.get("economia_potencial") is not None or (bi.get("available") and bi.get("value") is not None))
    if key == "inaction_valid":
        dx = payload.get("decision_experience") or {}
        bi = (dx.get("business_impact") or {}).get("cost_if_nothing") or {}
        return bool(bi.get("available") and bi.get("value") is not None)
    if key == "roadmap_valid":
        dx = payload.get("decision_experience") or {}
        return bool(dx.get("roadmap"))
    if key == "decision_valid":
        dx = payload.get("decision_experience") or {}
        fx = payload.get("first_experience") or {}
        return bool(dx.get("header") or fx.get("decision") or ((payload.get("intelligence") or {}).get("plano_acao")))
    if key.startswith("chart:"):
        cid = key.split(":", 1)[1]
        return any(
            c.get("id") == cid and (c.get("categories") or not c.get("empty_reason"))
            for c in (payload.get("charts") or [])
        )
    val = payload.get(key)
    if val is None:
        return False
    if isinstance(val, (list, dict)):
        return bool(val)
    return True


def _kpi(payload: dict[str, Any], kid: str) -> Optional[dict[str, Any]]:
    for k in payload.get("kpis_primary") or payload.get("kpis") or []:
        if k.get("id") == kid:
            return k
    return None


def _conf_label(raw: Any) -> str:
    s = str(raw or "baixa").lower()
    if s in {"alta", "high"}:
        return "Confiança alta"
    if s in {"media", "média", "moderada", "medium"}:
        return "Confiança moderada"
    return "Evidência insuficiente"


def _assumption_label(estado: Optional[str]) -> str:
    m = {
        "REAL": "REAL",
        "ESTIMADO": "ESTIMADO",
        "ILUSTRATIVO": "ILUSTRATIVO",
        "NAO_INFORMADO": "NÃO INFORMADO",
        "NÃO INFORMADO": "NÃO INFORMADO",
    }
    return m.get(str(estado or "NAO_INFORMADO"), str(estado or "NÃO INFORMADO"))


def compose_presentation(payload: dict[str, Any]) -> dict[str, Any]:
    """Compose RC-1.4 premium CEO deck from aggregate payload."""
    charts = {c.get("id"): c for c in (payload.get("charts") or [])}
    intel = payload.get("intelligence") or {}
    custo = payload.get("custo") or {}
    hero = payload.get("hero") or {}
    dx = payload.get("decision_experience") or {}
    fx = payload.get("first_experience") or {}
    client = payload.get("client") or {}
    periodo = payload.get("periodo") or {}
    slides: list[dict[str, Any]] = []
    omitted: list[dict[str, Any]] = []

    company = (
        hero.get("empresa")
        or client.get("nome_fantasia")
        or client.get("nome")
        or "Empresa"
    )
    period_label = hero.get("periodo") or (
        f"{periodo.get('inicio') or ''} → {periodo.get('fim') or ''}".strip(" →")
        or "Período selecionado"
    )
    conf = _conf_label(intel.get("confianca") or hero.get("confianca"))

    for defn in SLIDE_DEFS:
        ok = all(_has(payload, r) for r in defn["required"])
        if not ok:
            omitted.append(
                {
                    "id": defn["id"],
                    "title": defn["title"],
                    "reason": "evidência insuficiente — slide omitido",
                }
            )
            continue

        slide: dict[str, Any] = {
            "id": defn["id"],
            "title": defn["title"],
            "question": defn.get("question"),
            "kind": defn["id"],
            "insight": None,
            "confianca_label": conf,
            "privacy": {"pii_excluded": True, "worker_ranking": False},
            # legacy keys for older renderer compatibility
            "leitura": "",
            "recomendacao": None,
            "chart": None,
            "confianca": intel.get("confianca") or "baixa",
            "metodologia": "Métricas agregadas · Qualidade dos dados · Modelo de custo · Priorização determinística",
            "fonte": "Agregados canônicos — sem identificação nominal",
        }

        if defn["id"] == "cover":
            slide["cover"] = {
                "eyebrow": "BioMed Executive Intelligence",
                "company": company,
                "period": period_label,
                "context": "Reunião executiva",
            }
            slide["leitura"] = company

        elif defn["id"] == "state":
            phrase = (
                (fx.get("hero") or {}).get("opening_phrase")
                or hero.get("mensagem")
                or intel.get("resumo_executivo")
                or "Leitura descritiva do período disponível."
            )
            slide["state_phrase"] = phrase
            slide["insight"] = None
            slide["leitura"] = phrase

        elif defn["id"] == "financial":
            horas = _kpi(payload, "horas")
            dias = _kpi(payload, "dias")
            ass = custo.get("assumption") or {}
            estado = _assumption_label(ass.get("estado"))
            calculavel = bool(custo.get("calculavel"))
            slide["financial"] = {
                "horas": (horas or {}).get("value") if horas and horas.get("available") is not False else None,
                "dias": (dias or {}).get("value") if dias and dias.get("available") is not False else None,
                "custo": custo.get("custo_estimado") if calculavel else None,
                "calculavel": calculavel,
                "custo_hora": ass.get("valor"),
                "premissa": estado,
                "formula": "HORAS PERDIDAS × CUSTO HORA",
                "custo_hora_nao_informado": estado == "NÃO INFORMADO" or not calculavel,
            }
            if calculavel:
                slide["insight"] = custo.get("linguagem") or (
                    "O custo estimado concentra o impacto direto das horas perdidas no período."
                )
            else:
                slide["insight"] = "Custo hora não informado. Horas e dias permanecem visíveis sem inventar valor financeiro."
            slide["custo"] = custo if calculavel else None
            slide["kpis"] = [k for k in (horas, dias) if k]
            slide["leitura"] = slide["insight"]

        elif defn["id"] == "where":
            slide["chart"] = charts.get("setores")
            slide["insight"] = "Concentração setorial — priorizar o ponto de maior impacto."
            slide["leitura"] = slide["insight"]

        elif defn["id"] == "causes":
            slide["chart"] = charts.get("pareto_cid")
            slide["insight"] = "Principais grupos de causas concentrados — lista reduzida ao essencial."
            slide["leitura"] = slide["insight"]

        elif defn["id"] == "recurrence":
            slide["recorrencia"] = payload.get("recorrencia_agregada")
            slide["insight"] = "Recorrência agregada — sem nomes, sem identificação individual."
            slide["leitura"] = slide["insight"]

        elif defn["id"] == "when":
            slide["padroes"] = payload.get("padroes_temporais")
            slide["insight"] = "Padrão temporal observado na base — sem fabricar análise."
            slide["leitura"] = slide["insight"]

        elif defn["id"] == "changed":
            slide["chart"] = charts.get("evolucao_temporal")
            mudou = intel.get("o_que_mudou") or []
            slide["insight"] = (mudou[0] if mudou else "Evolução descritiva do período selecionado.")
            slide["leitura"] = slide["insight"]

        elif defn["id"] == "biomed":
            bp = payload.get("biomed_performance") or {}
            counts = bp.get("action_counts") or bp.get("acoes") or {}
            pend = payload.get("conditionants") or []
            slide["biomed"] = {
                "realizadas": counts.get("realizadas") or counts.get("iniciadas") or counts.get("total"),
                "concluidas": counts.get("concluidas") or counts.get("concluido"),
                "pendentes": counts.get("pendentes") or len(pend) or None,
                "condicionantes": payload.get("conditionants_summary"),
                "nota": "Associação temporal — sem causalidade exclusiva à BioMed.",
            }
            slide["biomed_performance"] = bp
            slide["conditionants"] = pend
            slide["insight"] = payload.get("conditionants_summary") or (
                "Atuação, resultado observado e efetividade — sem autopromoção."
            )
            slide["leitura"] = slide["insight"]

        elif defn["id"] == "savings":
            eco = payload.get("impacto_economico_biomed") or {}
            bi = ((dx.get("business_impact") or {}).get("savings_potential") or {})
            val = eco.get("economia_potencial")
            if val is None:
                val = bi.get("value")
            slide["savings"] = {
                "valor": val,
                "premissa": _assumption_label(
                    ((custo.get("assumption") or {}).get("estado")) or bi.get("assumption_state")
                ),
                "nota": eco.get("linguagem")
                or bi.get("note")
                or "Estimativa sob premissa explícita — não é promessa de economia.",
            }
            slide["insight"] = slide["savings"]["nota"]
            slide["leitura"] = slide["insight"]
            slide["impacto_economico"] = eco

        elif defn["id"] == "inaction":
            bi = ((dx.get("business_impact") or {}).get("cost_if_nothing") or {})
            slide["inaction"] = {
                "valor": bi.get("value"),
                "premissa": _assumption_label(bi.get("assumption_state")),
                "nota": bi.get("note")
                or bi.get("caveat")
                or "Custo de não agir somente com modelo válido — sem projeção para impressionar.",
            }
            slide["insight"] = slide["inaction"]["nota"]
            slide["leitura"] = slide["insight"]

        elif defn["id"] == "priorities":
            plan = (intel.get("plano_acao") or [])[:3]
            slide["priorities"] = [
                {
                    "prioridade": a.get("priority") or a.get("prioridade") or f"P{i+1}",
                    "problema": a.get("problem") or a.get("problema") or a.get("contexto") or "",
                    "acao": a.get("title") or a.get("titulo") or "",
                    "impacto": a.get("impact") or a.get("impacto") or "—",
                    "prazo": a.get("deadline") or a.get("prazo") or "—",
                }
                for i, a in enumerate(plan)
            ]
            slide["plano_acao"] = plan
            slide["insight"] = "No máximo três prioridades — validação humana obrigatória."
            slide["leitura"] = slide["insight"]
            slide["recomendacao"] = "Sem autoexecução."

        elif defn["id"] == "roadmap":
            road = dx.get("roadmap") or []
            # Keep only 30 / 90 / 180
            filtered = []
            for r in road:
                h = str(r.get("horizon") or r.get("prazo") or "")
                if any(x in h for x in ("30", "90", "180")):
                    filtered.append(
                        {
                            "horizon": h,
                            "focus": r.get("focus") or r.get("foco") or r.get("acao") or "",
                        }
                    )
            if not filtered:
                filtered = [
                    {"horizon": "30 dias", "focus": "Validar e iniciar a prioridade nº 1"},
                    {"horizon": "90 dias", "focus": "Acompanhar evidência e ajustar plano"},
                    {"horizon": "180 dias", "focus": "Revisar impacto e próxima decisão"},
                ]
            slide["roadmap"] = filtered[:3]
            slide["insight"] = "Roteiro executivo — 30, 90 e 180 dias."
            slide["leitura"] = slide["insight"]

        elif defn["id"] == "decision":
            decisions = []
            if dx.get("header"):
                decisions.append(
                    {
                        "titulo": (dx.get("header") or {}).get("title") or "Decisão prioritária",
                        "detalhe": (dx.get("six_answers") or {}).get("first_step")
                        or (dx.get("six_answers") or {}).get("problem")
                        or "",
                    }
                )
            for a in (intel.get("plano_acao") or [])[:2]:
                decisions.append(
                    {
                        "titulo": a.get("title") or a.get("titulo") or "Ação",
                        "detalhe": a.get("deadline") or a.get("prazo") or "",
                    }
                )
            slide["decisions"] = decisions[:3]
            slide["insight"] = "O que precisa ser decidido hoje — no máximo três decisões."
            slide["leitura"] = slide["insight"]

        elif defn["id"] == "closing":
            horas = _kpi(payload, "horas")
            ass = custo.get("assumption") or {}
            eco = payload.get("impacto_economico_biomed") or {}
            p1 = ((intel.get("plano_acao") or [{}])[0].get("title") if intel.get("plano_acao") else None) or (
                (dx.get("header") or {}).get("title")
            )
            slide["closing"] = {
                "perda": custo.get("custo_estimado") if custo.get("calculavel") else None,
                "perda_label": "Custo estimado" if custo.get("calculavel") else "Horas perdidas",
                "perda_alt": (horas or {}).get("value") if not custo.get("calculavel") else None,
                "economia": eco.get("economia_potencial"),
                "prioridade": p1 or "Validar prioridade nº 1",
                "proxima_revisao": "Em 30 dias",
                "premissa": _assumption_label(ass.get("estado")),
                "signature": "BioMed Executive Signature",
                "tagline": "Transformando evidências em decisões.",
            }
            slide["leitura"] = slide["closing"]["tagline"]

        slides.append(slide)

    minutes = max(3, min(5, 1 + len(slides) // 3))
    return {
        "engine_version": "rc14-executive-presentation-premium-v1",
        "mode": "ceo",
        "estimated_minutes": minutes,
        "slides": slides,
        "omitted": omitted,
        "questions": [
            "Quanto estamos perdendo?",
            "Por que estamos perdendo?",
            "Quanto podemos melhorar/economizar?",
            "O que precisamos decidir agora?",
        ],
        "export": {
            "tela": True,
            "pdf": "premium",
            "pptx": "arquitetura preservada — reutilizar exportadores legados quando possível",
        },
        "privacy": {
            "pii_excluded": True,
            "worker_ranking": False,
            "presentation_default": "aggregate",
        },
        "legacy_note": "Módulo /apresentacao legado preservado; esta é a experiência executiva premium RC-1.4.",
    }
