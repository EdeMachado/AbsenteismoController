"""Executive decision questions — EXEC-03."""

from __future__ import annotations

from typing import Any


QUESTIONS: list[dict[str, Any]] = [
    {
        "id": "maior_problema",
        "label": "Qual é o maior problema?",
        "maps_to": ["setores_dias", "pareto_cid_dias", "custo_absenteismo"],
    },
    {
        "id": "doenca_impacta",
        "label": "Qual doença mais impacta?",
        "maps_to": ["pareto_cid_dias", "pareto_cid_eventos", "custo_cid"],
    },
    {
        "id": "setor_concentra",
        "label": "Qual setor concentra o problema?",
        "maps_to": ["setores_dias", "setores_eventos", "custo_setor"],
    },
    {
        "id": "quando_ocorre",
        "label": "Quando ocorre mais?",
        "maps_to": ["evolucao_eventos", "dia_semana", "faixa_horaria"],
    },
    {
        "id": "recorrencia",
        "label": "Quem apresenta maior recorrência?",
        "maps_to": ["recorrencia"],
        "privacy": "aggregate_default",
    },
    {
        "id": "quanto_custa",
        "label": "Quanto custa?",
        "maps_to": ["custo_absenteismo", "custo_evolucao"],
    },
    {
        "id": "o_que_mudou",
        "label": "O que mudou?",
        "maps_to": ["tendencia_baseline", "comparativo_baseline"],
    },
    {
        "id": "biomed_realizou",
        "label": "O que a BioMed realizou?",
        "maps_to": ["biomed_producao", "biomed_cobertura", "biomed_execucao"],
    },
    {
        "id": "o_que_funcionou",
        "label": "O que funcionou?",
        "maps_to": ["efetividade", "antes_depois"],
    },
    {
        "id": "pendente",
        "label": "O que está pendente?",
        "maps_to": ["condicionantes"],
    },
    {
        "id": "fazer_agora",
        "label": "O que devemos fazer agora?",
        "maps_to": ["biomed_producao", "condicionantes"],
        "target": "plano_acao",
    },
]


def answer_question(qid: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Deterministic short answers from aggregate payload (no LLM)."""
    intel = payload.get("intelligence") or {}
    custo = payload.get("custo") or {}
    hero = payload.get("hero") or {}
    charts = {c.get("id"): c for c in (payload.get("charts") or [])}
    answers = {
        "maior_problema": hero.get("mensagem")
        or intel.get("mensagem_executiva")
        or "Sem síntese disponível.",
        "doenca_impacta": _top_label(charts.get("pareto_cid"), "Grupo CID com maior volume de eventos."),
        "setor_concentra": _top_label(charts.get("setores"), "Setor com maior volume de eventos."),
        "quando_ocorre": _series_peak(charts.get("evolucao_temporal")),
        "recorrencia": _recorrencia_text(payload.get("recorrencia_agregada")),
        "quanto_custa": custo.get("linguagem") or "Custo não calculável com as premissas atuais.",
        "o_que_mudou": "; ".join(intel.get("o_que_mudou") or []) or "Comparativo indisponível.",
        "biomed_realizou": _biomed_text(payload.get("biomed_performance")),
        "o_que_funcionou": (
            (payload.get("biomed_performance") or {}).get("efetividade") or {}
        ).get("classificacao")
        or "Efetividade não avaliada.",
        "pendente": payload.get("conditionants_summary") or "Sem condicionantes registradas.",
        "fazer_agora": "; ".join(intel.get("o_que_recomendamos") or [])
        or "Sem recomendações acionáveis.",
    }
    q = next((x for x in QUESTIONS if x["id"] == qid), None)
    return {
        "id": qid,
        "label": (q or {}).get("label"),
        "answer": answers.get(qid, "Pergunta não mapeada."),
        "maps_to": (q or {}).get("maps_to") or [],
        "privacy": (q or {}).get("privacy") or "aggregate",
        "confidence": intel.get("confianca") or "baixa",
        "limitations": intel.get("limitacoes") or [],
    }


def _top_label(chart: dict | None, fallback: str) -> str:
    if not chart or not chart.get("categories"):
        return fallback + " Dados insuficientes."
    return f"Maior concentração: {chart['categories'][0]}."


def _series_peak(chart: dict | None) -> str:
    if not chart or not chart.get("series"):
        return "Série temporal insuficiente."
    vals = chart["series"][0].get("data") or []
    cats = chart.get("categories") or []
    if not vals or not cats:
        return "Série temporal insuficiente."
    i = max(range(len(vals)), key=lambda k: vals[k])
    return f"Pico observado em {cats[i]} ({vals[i]} eventos)."


def _recorrencia_text(rec: dict | None) -> str:
    if not rec:
        return (
            "Recorrência agregada indisponível. "
            "Visão executiva não exibe ranking nominal."
        )
    return (
        f"Trabalhadores com 2+ eventos: {rec.get('n_2plus', 'n/d')}; "
        f"3+: {rec.get('n_3plus', 'n/d')}; 5+: {rec.get('n_5plus', 'n/d')}. "
        "Sem identificação nominal na visão executiva."
    )


def _biomed_text(bp: dict | None) -> str:
    if not bp:
        return "Produção BioMed não informada."
    p = bp.get("producao") or {}
    parts = []
    if p.get("executadas") is not None:
        parts.append(f"Executadas: {p.get('executadas')}")
    if bp.get("cobertura") is not None:
        parts.append(f"Cobertura: {float(bp['cobertura'])*100:.0f}%")
    if bp.get("execucao") is not None:
        parts.append(f"Execução: {float(bp['execucao'])*100:.1f}%")
    return "; ".join(parts) if parts else "Produção BioMed não informada."
