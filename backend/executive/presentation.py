"""Executive Presentation deck composer — EXEC-03.

Builds sequential slides from aggregate payload. Omits unavailable slides.
No PII. Legacy /apresentacao remains untouched.
"""

from __future__ import annotations

from typing import Any


SLIDE_DEFS: list[dict[str, Any]] = [
    {"id": "resumo", "title": "Resumo executivo", "required": ["hero"]},
    {"id": "kpis", "title": "KPIs principais", "required": ["kpis_primary"]},
    {"id": "evolucao", "title": "Evolução do absenteísmo", "required": ["chart:evolucao_temporal"]},
    {"id": "impacto_dias_horas", "title": "Impacto em dias e horas", "required": ["kpis_primary"]},
    {"id": "custo", "title": "Custo do absenteísmo", "required": ["custo_calculavel"]},
    {"id": "cid", "title": "Principais causas / CID", "required": ["chart:pareto_cid"]},
    {"id": "setores", "title": "Setores críticos", "required": ["chart:setores"]},
    {"id": "recorrencia", "title": "Recorrência", "required": ["recorrencia_agregada"]},
    {"id": "afastamentos", "title": "Afastamentos prolongados", "required": ["afastamentos_longos"]},
    {"id": "padroes_temporais", "title": "Padrões temporais", "required": ["padroes_temporais"]},
    {"id": "qualidade", "title": "Qualidade dos dados", "required": ["qualidade"]},
    {"id": "atuacao_biomed", "title": "Atuação BioMed", "required": ["biomed_performance"]},
    {"id": "resultado", "title": "Resultado observado", "required": ["biomed_performance"]},
    {"id": "condicionantes", "title": "Condicionantes empresariais", "required": ["conditionants"]},
    {"id": "intelligence", "title": "BioMed Intelligence", "required": ["intelligence"]},
    {"id": "plano_acao", "title": "Plano de Ação", "required": ["plano_acao"]},
    {"id": "prioridades", "title": "Prioridades para próximo ciclo", "required": ["plano_acao"]},
    {"id": "metodologia", "title": "Metodologia / limitações", "required": ["methodology"]},
]


def _has(payload: dict[str, Any], key: str) -> bool:
    if key == "custo_calculavel":
        return bool((payload.get("custo") or {}).get("calculavel"))
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
    if key.startswith("chart:"):
        cid = key.split(":", 1)[1]
        return any(c.get("id") == cid and (c.get("categories") or not c.get("empty_reason")) for c in (payload.get("charts") or []))
    val = payload.get(key)
    if val is None:
        return False
    if isinstance(val, (list, dict)):
        return bool(val)
    return True


def compose_presentation(payload: dict[str, Any]) -> dict[str, Any]:
    charts = {c.get("id"): c for c in (payload.get("charts") or [])}
    intel = payload.get("intelligence") or {}
    custo = payload.get("custo") or {}
    slides = []
    omitted = []

    for defn in SLIDE_DEFS:
        ok = all(_has(payload, r) for r in defn["required"])
        if not ok:
            omitted.append({"id": defn["id"], "title": defn["title"], "reason": "dados insuficientes"})
            continue
        slide = {
            "id": defn["id"],
            "title": defn["title"],
            "chart": None,
            "leitura": "",
            "recomendacao": None,
            "confianca": intel.get("confianca") or "baixa",
            "metodologia": "MetricService · DataQualityService · Cost Model · Rule Engine",
            "fonte": "agregados canônicos — sem PII",
            "privacy": {"pii_excluded": True, "worker_ranking": False},
        }
        if defn["id"] == "resumo":
            slide["leitura"] = (payload.get("hero") or {}).get("mensagem") or intel.get("resumo_executivo")
            slide["kpis"] = payload.get("kpis_primary")
            slide["score"] = (payload.get("hero") or {}).get("score")
        elif defn["id"] == "kpis":
            slide["kpis"] = payload.get("kpis_primary")
            slide["leitura"] = "Indicadores primários do período selecionado."
        elif defn["id"] == "evolucao":
            slide["chart"] = charts.get("evolucao_temporal")
            slide["leitura"] = "Evolução mensal de eventos com média móvel quando série suficiente."
        elif defn["id"] == "impacto_dias_horas":
            slide["kpis"] = [
                k
                for k in (payload.get("kpis_primary") or [])
                if k.get("id") in {"dias", "horas", "eventos"}
            ]
            slide["leitura"] = "; ".join(intel.get("o_que_mudou") or [])
        elif defn["id"] == "custo":
            slide["custo"] = custo
            slide["leitura"] = custo.get("linguagem")
            slide["chart"] = (custo.get("breakdown") or {}).get("evolucao_chart")
            slide["recomendacao"] = (
                "Substituir premissa ilustrativa pelo custo hora real da empresa, se ainda ilustrativa."
                if (custo.get("assumption") or {}).get("estado") == "ILUSTRATIVO"
                else None
            )
        elif defn["id"] == "cid":
            slide["chart"] = charts.get("pareto_cid")
            slide["leitura"] = "Pareto de grupos alfabéticos CID (não capítulo oficial)."
            slide["recomendacao"] = (intel.get("o_que_recomendamos") or [None])[0]
        elif defn["id"] == "setores":
            slide["chart"] = charts.get("setores")
            slide["leitura"] = "Ranking de impacto setorial (eventos/dias)."
        elif defn["id"] == "recorrencia":
            slide["recorrencia"] = payload.get("recorrencia_agregada")
            slide["leitura"] = (
                "Distribuição agregada de recorrência — sem identificação nominal."
            )
        elif defn["id"] == "afastamentos":
            slide["afastamentos_longos"] = payload.get("afastamentos_longos")
            slide["leitura"] = "Impacto de afastamentos prolongados quando mensurável."
        elif defn["id"] == "padroes_temporais":
            slide["padroes"] = payload.get("padroes_temporais")
            slide["leitura"] = "Padrões temporais disponíveis na base."
        elif defn["id"] == "qualidade":
            slide["qualidade"] = payload.get("qualidade")
            slide["leitura"] = "Confiabilidade da base (IQB e dimensões)."
        elif defn["id"] in {"atuacao_biomed", "resultado"}:
            slide["biomed_performance"] = payload.get("biomed_performance")
            slide["leitura"] = (
                "Atuação e resultado observados — associação temporal sem causalidade exclusiva."
            )
            # Economic link when hours delta + cost available
            slide["impacto_economico"] = payload.get("impacto_economico_biomed")
        elif defn["id"] == "condicionantes":
            slide["conditionants"] = payload.get("conditionants")
            slide["leitura"] = payload.get("conditionants_summary")
        elif defn["id"] == "intelligence":
            slide["intelligence"] = {
                "resumo": intel.get("resumo_executivo"),
                "o_que_mudou": intel.get("o_que_mudou"),
                "risco": intel.get("onde_esta_o_risco"),
                "recomendamos": intel.get("o_que_recomendamos"),
            }
            slide["leitura"] = intel.get("mensagem_executiva")
        elif defn["id"] in {"plano_acao", "prioridades"}:
            slide["plano_acao"] = intel.get("plano_acao")
            slide["leitura"] = "Ações propostas com validação médica obrigatória."
            slide["recomendacao"] = "Sem autoexecução."
        elif defn["id"] == "metodologia":
            slide["methodology"] = payload.get("methodology")
            slide["limitacoes"] = payload.get("limitations") or intel.get("limitacoes")
            slide["leitura"] = "Fontes canônicas e limitações explícitas."

        slides.append(slide)

    return {
        "engine_version": "exec03-presentation-v1",
        "slides": slides,
        "omitted": omitted,
        "export": {
            "tela": True,
            "pdf": "futuro",
            "pptx": "reutilizar exportadores legados quando possível",
        },
        "privacy": {
            "pii_excluded": True,
            "worker_ranking": False,
            "presentation_default": "aggregate",
        },
        "legacy_note": "Módulo /apresentacao legado preservado; esta é a experiência experimental.",
    }
