"""Per-analysis BioMed Intelligence drawer — deterministic (no LLM)."""

from __future__ import annotations

from typing import Any


def analyze_visualization(
    analysis_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Structured analysis for a chart/KPI. Never claims exclusive causality."""
    charts = {c.get("id"): c for c in (payload.get("charts") or [])}
    intel = payload.get("intelligence") or {}
    custo = payload.get("custo") or {}
    catalog = {a["id"]: a for a in (payload.get("analytics_catalog") or [])}
    spec = catalog.get(analysis_id) or {"title": analysis_id, "pergunta": "", "available": False}

    if not spec.get("available", True) and analysis_id not in {
        "custo_absenteismo",
        "evolucao_eventos",
        "pareto_cid_eventos",
        "setores_eventos",
        "recorrencia",
        "biomed_producao",
        "condicionantes",
        "iqb",
    }:
        # still try known mappings
        pass

    fato, interpretacao, impacto = _fact_block(analysis_id, charts, payload, custo)
    hipotese = [
        "Concentração pode refletir exposição ocupacional, sazonalidade ou mix de CID.",
        "Variações podem ser moduladas por cobertura assistencial e condicionantes empresariais.",
    ]
    reco = (intel.get("o_que_recomendamos") or [])[:3] or [
        "Manter vigilância dos fatores de maior participação sem ranking nominal."
    ]
    plano = (intel.get("plano_acao") or [])[:2]
    evidencias = intel.get("evidencias") or []
    limitacoes = list(intel.get("limitacoes") or [])
    limitacoes.append("Narrativa determinística; sem LLM; sem causalidade exclusiva.")

    return {
        "analysis_id": analysis_id,
        "title": spec.get("title") or analysis_id,
        "pergunta": spec.get("pergunta") or "",
        "fato_observado": fato,
        "interpretacao": interpretacao,
        "hipoteses": hipotese,
        "impacto": impacto,
        "recomendacao": reco,
        "plano_sugerido": [
            {
                "titulo": p.get("title"),
                "prioridade": p.get("priority"),
                "validacao_medica": p.get("medical_validation_required", True),
            }
            for p in plano
            if isinstance(p, dict)
        ],
        "evidencia": evidencias[:8],
        "limitacoes": limitacoes[:8],
        "confianca": intel.get("confianca") or "baixa",
        "engine": "rule_engine_deterministic_v1",
        "llm": False,
        "privacy": "aggregate",
    }


def _fact_block(aid: str, charts: dict, payload: dict, custo: dict) -> tuple[str, str, str]:
    if aid.startswith("custo") or aid == "custo_absenteismo":
        fato = custo.get("linguagem") or "Custo não calculável."
        interpretacao = (
            "Impacto laboral estimado sob premissa de custo hora explícita; "
            "não é prejuízo contábil auditado."
        )
        impacto = f"Custo estimado: {custo.get('custo_estimado')}"
        return fato, interpretacao, impacto

    if "pareto_cid" in aid or aid == "grupos_cid":
        ch = charts.get("pareto_cid")
        top = (ch or {}).get("categories", ["n/d"])[0]
        fato = f"Maior participação de eventos no grupo alfabético CID {top} (não capítulo oficial)."
        interpretacao = "Concentração de causas agregadas; exige leitura clínica contextual."
        impacto = "Priorizar investigação do grupo dominante em volume/dias."
        return fato, interpretacao, impacto

    if "setor" in aid:
        ch = charts.get("setores")
        top = (ch or {}).get("categories", ["n/d"])[0]
        fato = f"Setor de maior volume: {top}."
        interpretacao = "Concentração setorial orienta ações locais sem ranking de trabalhador."
        impacto = "Foco operacional no setor dominante."
        return fato, interpretacao, impacto

    if "evolucao" in aid or "media_movel" in aid or "tendencia" in aid:
        fato = (payload.get("hero") or {}).get("mensagem") or "Tendência descritiva do período."
        interpretacao = "Comparativo com baseline quando a janela for comparável."
        impacto = "; ".join((payload.get("intelligence") or {}).get("o_que_mudou") or []) or "n/d"
        return fato, interpretacao, impacto

    if aid == "recorrencia":
        rec = payload.get("recorrencia_agregada") or {}
        fato = (
            f"Recorrência agregada — 2+: {rec.get('n_2plus', 'n/d')}, "
            f"3+: {rec.get('n_3plus', 'n/d')}, 5+: {rec.get('n_5plus', 'n/d')}."
        )
        interpretacao = "Visão executiva agregada; sem PII. Investigação nominal só com perfil clínico autorizado."
        impacto = (
            f"Participação dos recorrentes (2+) nos eventos: "
            f"{rec.get('share_eventos_2plus', 'n/d')}."
        )
        return fato, interpretacao, impacto

    if aid.startswith("biomed") or aid == "efetividade":
        bp = payload.get("biomed_performance") or {}
        fato = bp.get("nota") or "Atuação BioMed conforme payload."
        interpretacao = "Associação temporal; sem atribuição causal exclusiva."
        impacto = str((bp.get("efetividade") or {}).get("classificacao") or "n/d")
        return fato, interpretacao, impacto

    if aid == "condicionantes":
        fato = payload.get("conditionants_summary") or "Sem condicionantes."
        interpretacao = "Pendências empresariais reduzem cobertura potencial do plano."
        impacto = "Não se estima dinheiro hipotético sem modelo contrafactual válido."
        return fato, interpretacao, impacto

    fato = "Fato agregado disponível no painel para a análise solicitada."
    interpretacao = "Leitura descritiva com base em MetricService / IQB / Performance."
    impacto = "Ver KPIs e gráficos do Command Center / Analytics."
    return fato, interpretacao, impacto
