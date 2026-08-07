"""RC-1.4 — synthetic executive payload for public presentation preview.

No database. No auth. Illustrative numbers clearly marked.
"""

from __future__ import annotations

from typing import Any

from backend.executive.presentation import compose_presentation


def build_synthetic_executive_payload() -> dict[str, Any]:
    """Minimal aggregate-shaped payload for premium deck composition."""
    return {
        "client": {"nome": "Alpha Industrial", "nome_fantasia": "Alpha Industrial"},
        "periodo": {"inicio": "2026-01", "fim": "2026-03", "comparabilidade": "integral"},
        "hero": {
            "empresa": "Alpha Industrial",
            "periodo": "2026-01 → 2026-03",
            "mensagem": (
                "O absenteísmo apresentou melhora no período, "
                "mas dois pontos ainda exigem atenção executiva."
            ),
            "confianca": "media",
            "score": {"label": "Alto", "value": 78},
            "status": "comparavel",
            "tendencia": "melhora",
        },
        "kpis_primary": [
            {"id": "eventos", "label": "Eventos", "value": 142, "unit": "", "available": True},
            {"id": "dias", "label": "Dias perdidos", "value": 318, "unit": "dias", "available": True},
            {"id": "horas", "label": "Horas perdidas", "value": 2544, "unit": "h", "available": True},
            {"id": "custo", "label": "Custo estimado", "value": 89040, "unit": "R$", "available": True},
        ],
        "custo": {
            "calculavel": True,
            "custo_estimado": 89040,
            "linguagem": (
                "Impacto direto estimado das horas perdidas no período, "
                "com premissa de custo hora ilustrativa."
            ),
            "assumption": {"estado": "ILUSTRATIVO", "valor": 35.0},
            "hours": {"horas": 2544, "kind": "registradas"},
        },
        "charts": [
            {
                "id": "setores",
                "chart_type": "bar",
                "categories": ["Operacional", "Manutenção", "Administrativo", "Logística"],
                "series": [{"name": "Eventos", "data": [68, 31, 24, 19]}],
            },
            {
                "id": "pareto_cid",
                "chart_type": "pareto",
                "categories": ["Grupo M", "Grupo S", "Grupo F", "Grupo J", "Outros"],
                "series": [{"name": "Eventos", "data": [42, 28, 18, 12, 42]}],
            },
            {
                "id": "evolucao_temporal",
                "chart_type": "line",
                "categories": ["2026-01", "2026-02", "2026-03"],
                "series": [{"name": "Eventos", "data": [58, 49, 35]}],
            },
        ],
        "recorrencia_agregada": {
            "n_2plus": 37,
            "n_3plus": 14,
            "n_5plus": 4,
            "privacy": "sem identificação nominal",
        },
        "padroes_temporais": {
            "dia_semana": {
                "Seg": 28,
                "Ter": 24,
                "Qua": 22,
                "Qui": 31,
                "Sex": 37,
            }
        },
        "biomed_performance": {
            "action_counts": {"realizadas": 9, "concluidas": 6, "pendentes": 2},
        },
        "conditionants": [
            {"id": "c1", "status": "pendente", "nota": "Revisão ergonômica aguardando liberação"},
            {"id": "c2", "status": "pendente", "nota": "Ajuste de jornada em avaliação"},
        ],
        "conditionants_summary": "2 ações prioritárias permanecem pendentes de implementação.",
        "impacto_economico_biomed": {
            "economia_potencial": 26712,
            "linguagem": (
                "Potencial estimado sob a mesma premissa ilustrativa — "
                "não constitui promessa de economia."
            ),
        },
        "intelligence": {
            "confianca": "media",
            "resumo_executivo": "Melhora no trimestre com concentração residual no Operacional.",
            "mensagem_executiva": "Há margem de melhoria sob condições claras de execução.",
            "o_que_mudou": ["Redução de eventos entre janeiro e março."],
            "o_que_recomendamos": ["Priorizar revisão ergonômica no Operacional."],
            "plano_acao": [
                {
                    "title": "Revisão ergonômica no Operacional",
                    "priority": "P1",
                    "problem": "Concentração de eventos no setor",
                    "impact": "Alto",
                    "deadline": "30 dias",
                },
                {
                    "title": "Acompanhar recorrentes agregados",
                    "priority": "P2",
                    "problem": "Repetição concentrada",
                    "impact": "Médio",
                    "deadline": "90 dias",
                },
                {
                    "title": "Validar custo hora real",
                    "priority": "P3",
                    "problem": "Premissa ainda ilustrativa",
                    "impact": "Governança",
                    "deadline": "30 dias",
                },
            ],
        },
        "decision_experience": {
            "header": {
                "title": "Priorizar revisão ergonômica no Operacional",
                "priority_label": "Alta",
                "impact": "Concentração setorial",
                "estimated_time": "30 dias",
            },
            "six_answers": {
                "problem": "Maior parcela do absenteísmo permanece no Operacional.",
                "first_step": "Validar e iniciar a revisão ergonômica em 30 dias.",
            },
            "business_impact": {
                "savings_potential": {
                    "available": True,
                    "value": 26712,
                    "assumption_state": "ILUSTRATIVO",
                    "note": "Estimativa sob premissa ilustrativa.",
                },
                "cost_if_nothing": {
                    "available": True,
                    "value": 89040,
                    "assumption_state": "ILUSTRATIVO",
                    "note": "Se nada mudar, o patamar atual de impacto tende a se repetir.",
                },
            },
            "roadmap": [
                {"horizon": "30 dias", "focus": "Validar e iniciar a prioridade nº 1"},
                {"horizon": "90 dias", "focus": "Acompanhar evidência e ajustar plano"},
                {"horizon": "180 dias", "focus": "Revisar impacto e próxima decisão"},
            ],
        },
        "first_experience": {
            "hero": {
                "opening_phrase": (
                    "O absenteísmo apresentou melhora no período, "
                    "mas dois pontos ainda exigem atenção executiva."
                )
            },
            "decision": {
                "title": "Priorizar revisão ergonômica no Operacional",
                "cta": "Entender esta decisão",
            },
        },
        "methodology": {
            "metrics": "Métricas agregadas",
            "quality": "Qualidade dos dados",
            "cost": "Modelo de custo laboral",
            "llm": False,
        },
        "limitations": [
            "Custo hora ilustrativo nesta demonstração.",
            "Sem identificação nominal de colaboradores.",
        ],
        "privacy": {"pii_excluded": True, "worker_ranking": False},
    }


def build_synthetic_premium_deck() -> dict[str, Any]:
    return compose_presentation(build_synthetic_executive_payload())
