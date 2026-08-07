"""Executive aggregate payload builder — uses MetricService + DataQualityService.

Never invents headcount denominators. Suppresses small groups. No PII.
"""

from __future__ import annotations

import os
from datetime import date
from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.executive import ENGINE_VERSION, SMALL_GROUP_THRESHOLD
from backend.executive.exec03_enrichment import (
    biomed_economic_impact,
    build_availability_flags,
    build_cost_block,
    cargo_distribution,
    catalog_availability,
    compute_recurrence_aggregate,
    cost_kpi,
    weekday_distribution,
)
from backend.executive.first_experience import compose_first_experience
from backend.executive.decision_experience import compose_decision_experience
from backend.executive.intelligence import ExecutiveIntelligenceEngine
from backend.executive.presentation import compose_presentation
from backend.executive.questions import QUESTIONS, answer_question
from backend.executive.schemas import ChartSeries, ExecutiveScoreView, KpiCard
from backend.models import Client
from backend.performance.effectiveness_service import _delta
from backend.performance.performance_service import PerformanceService
from backend.performance.schemas import ActionCounts, Conditionant
from backend.services.data_quality_service import DataQualityService
from backend.services.metric_service import MetricService
from backend.services.shadow_compare import assert_no_pii_in_payload


def _month_add(ym: str, delta: int) -> str:
    y, m = int(ym[:4]), int(ym[5:7])
    m += delta
    while m <= 0:
        y -= 1
        m += 12
    while m > 12:
        y += 1
        m -= 12
    return f"{y:04d}-{m:02d}"


def _default_period() -> tuple[str, str]:
    today = date.today()
    fim = f"{today.year:04d}-{today.month:02d}"
    inicio = _month_add(fim, -5)
    return inicio, fim


def _metrics_to_dict(m: Any, client_id: int, p0: str, p1: str) -> dict[str, Any]:
    # CanonicalMetricsResult nests numbers under .metricas
    met = getattr(m, "metricas", m)
    dist_setor = getattr(m, "distribuicao_setor", None) or []
    dist_cid = getattr(m, "distribuicao_grupo_alfabetico_cid", None) or []
    limitacoes = list(getattr(m, "limitacoes", None) or [])

    setores = []
    for item in dist_setor:
        if isinstance(item, dict):
            name = item.get("setor") or item.get("nome")
            if name:
                setores.append(str(name))

    cids = []
    for item in dist_cid:
        if isinstance(item, dict):
            g = item.get("grupo") or item.get("letra") or item.get("grupo_alfabetico")
            if g:
                cids.append(str(g)[:1].upper())

    dist_cc = getattr(m, "distribuicao_centro_custo", None) or []
    horas_reg = getattr(met, "horas_perdidas_registradas", None)
    horas_est = getattr(met, "horas_perdidas_estimadas", None)
    # Normalize zeros from MetricService to None when literally no coverage
    if horas_reg is not None and float(horas_reg) <= 0:
        horas_reg = None
    if horas_est is not None and float(horas_est) <= 0:
        horas_est = None

    return {
        "client_id": client_id,
        "periodo_inicio": p0,
        "periodo_fim": p1,
        "eventos": getattr(met, "eventos", None) or getattr(met, "eventos_brutos", 0) or 0,
        "trabalhadores_afetados": getattr(met, "trabalhadores_unicos", None),
        "dias_perdidos": float(getattr(met, "dias_perdidos", 0) or 0),
        "horas_perdidas": horas_reg,
        "horas_estimadas": horas_est,
        "duracao_media": getattr(met, "duracao_media_dias", None)
        or getattr(met, "duracao_media", None),
        "eventos_por_100": getattr(met, "eventos_por_100_trabalhadores", None),
        "gravidade": None,  # derived downstream when days/events allow
        "recorrencia": None,
        "afastamentos_longos": None,
        "grupos_cid": sorted(set(cids)),
        "setores_criticos": setores[:8],
        "limitacoes": limitacoes,
        "distribuicao_setor": _as_list(dist_setor),
        "distribuicao_cid": _as_list(dist_cid),
        "distribuicao_centro_custo": _as_list(dist_cc),
        "serie_temporal": [],
    }


def _as_list(obj: Any) -> list[Any]:
    if obj is None:
        return []
    if isinstance(obj, list):
        out = []
        for x in obj:
            if hasattr(x, "__dict__") and not isinstance(x, dict):
                d = {k: v for k, v in vars(x).items() if not k.startswith("_")}
                # drop worker identity sets
                for k in list(d.keys()):
                    if isinstance(d[k], set):
                        d[k] = len(d[k])
                out.append(d)
            else:
                out.append(x)
        return out
    return []


class ExecutiveAggregateService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.metrics = MetricService(db)
        self.dq = DataQualityService(db)
        self.intel = ExecutiveIntelligenceEngine()

    def build_command_center(
        self,
        *,
        client_id: int,
        periodo_inicio: Optional[str] = None,
        periodo_fim: Optional[str] = None,
        efetivo_trabalhadores: Optional[int] = None,
        conditionants: Optional[list[dict[str, Any]]] = None,
        biomed_performance: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise ValueError("client_not_found")

        if not periodo_inicio or not periodo_fim:
            periodo_inicio, periodo_fim = _default_period()

        # Baseline: janela imediatamente anterior de mesma duração (meses)
        y0, m0 = int(periodo_inicio[:4]), int(periodo_inicio[5:7])
        y1, m1 = int(periodo_fim[:4]), int(periodo_fim[5:7])
        span = (y1 - y0) * 12 + (m1 - m0) + 1
        base_fim = _month_add(periodo_inicio, -1)
        base_inicio = _month_add(base_fim, -(span - 1))

        cur = self.metrics.compute(
            client_id,
            periodo_inicio,
            periodo_fim,
            efetivo_trabalhadores=efetivo_trabalhadores,
            suppress_small_groups=True,
            small_group_threshold=SMALL_GROUP_THRESHOLD,
        )
        try:
            base = self.metrics.compute(
                client_id,
                base_inicio,
                base_fim,
                efetivo_trabalhadores=efetivo_trabalhadores,
                suppress_small_groups=True,
                small_group_threshold=SMALL_GROUP_THRESHOLD,
            )
            base_dict = _metrics_to_dict(base, client_id, base_inicio, base_fim)
            comparable = True
        except Exception:
            base_dict = None
            comparable = False

        cur_dict = _metrics_to_dict(cur, client_id, periodo_inicio, periodo_fim)
        cur_dict["serie_temporal"] = self._build_temporal_series(
            client_id, periodo_inicio, periodo_fim, efetivo_trabalhadores
        )

        # Staging-only demo enrichment (never production). Explicit env gate.
        staging_demo = (os.environ.get("EXECUTIVE_STAGING_DEMO") or "").strip().lower() in {
            "1", "true", "yes", "on"
        }
        if staging_demo and biomed_performance is None:
            biomed_performance = {
                "producao": {"planejadas": 38, "aprovadas": 34, "executadas": 31},
                "cobertura": 0.91,
                "execucao": 0.816,
                "resultado_observado": {
                    "eventos": cur_dict.get("eventos"),
                    "dias": cur_dict.get("dias_perdidos"),
                    "horas": cur_dict.get("horas_perdidas"),
                    "severidade": cur_dict.get("gravidade"),
                },
                "efetividade": {
                    "classificacao": "compativel_com_melhora",
                    "confianca": "moderada",
                    "limitacoes": [
                        "Associação temporal; sem causalidade exclusiva.",
                        "Staging demo — valores de atuação são fixtures explícitas.",
                    ],
                },
                "nota": "Fixture de staging (EXECUTIVE_STAGING_DEMO). Não usar em produção.",
            }
        if staging_demo and not conditionants:
            conditionants = [
                {
                    "id": "cond-1",
                    "recomendacao_id": "erg-01",
                    "status": "executada",
                    "decisao": "executada",
                    "nota": "Adequação ergonômica no setor operacional",
                },
                {
                    "id": "cond-2",
                    "recomendacao_id": "sm-02",
                    "status": "adiada",
                    "decisao": "adiada",
                    "barreira": "Priorização operacional da empresa",
                    "nota": "Programa de saúde mental adiado",
                },
                {
                    "id": "cond-3",
                    "recomendacao_id": "vig-03",
                    "status": "impedida",
                    "decisao": "impedida",
                    "barreira": "Janela de parada não autorizada",
                    "nota": "Vigilância reforçada em turno noturno",
                },
            ]


        iqb_val = None
        iqb_label = None
        iqb_dims: dict[str, Any] = {}
        try:
            iqb_res = self.dq.analyze(
                client_id, periodo_inicio=periodo_inicio, periodo_fim=periodo_fim
            )
            iqb_val = getattr(iqb_res, "iqb", None)
            iqb_label = getattr(iqb_res, "classificacao", None)
            # expose dimensional scores without PII
            for attr in (
                "completude",
                "identidade",
                "horas",
                "cid",
                "rastreabilidade",
                "atualidade",
            ):
                block = getattr(iqb_res, attr, None)
                if isinstance(block, dict) and "score" in block:
                    iqb_dims[attr] = block.get("score")
                elif isinstance(block, dict) and "iqb_parcial" in block:
                    iqb_dims[attr] = block.get("iqb_parcial")
        except Exception:
            pass

        # Gravidade simples: dias/eventos quando ambos > 0
        if cur_dict.get("eventos") and float(cur_dict["eventos"]) > 0:
            cur_dict["gravidade"] = round(
                float(cur_dict["dias_perdidos"]) / float(cur_dict["eventos"]), 4
            )
        if base_dict and base_dict.get("eventos") and float(base_dict["eventos"]) > 0:
            base_dict["gravidade"] = round(
                float(base_dict["dias_perdidos"]) / float(base_dict["eventos"]), 4
            )
        kpis = self._kpis(cur_dict, base_dict if comparable else None, iqb_val, iqb_label)
        charts = self._charts(cur_dict)

        # BioMed performance placeholders — never invent ROI or fake coverage.
        biomed = biomed_performance or {
            "producao": {"planejadas": None, "aprovadas": None, "executadas": None},
            "cobertura": None,
            "execucao": None,
            "resultado_observado": {
                "eventos": cur_dict.get("eventos"),
                "dias": cur_dict.get("dias_perdidos"),
            },
            "nota": "Performance Engine shadow; valores de produção/cobertura só com registro explícito.",
        }
        score = self._score_view(
            cur_dict,
            base_dict if comparable else None,
            iqb_val,
            comparable,
            conditionants or [],
            biomed,
        )

        intel = self.intel.build(
            client_name=client.nome_fantasia or client.nome,
            current=cur_dict,
            baseline=base_dict if comparable else None,
            iqb=float(iqb_val) if iqb_val is not None else None,
            iqb_label=iqb_label,
            conditionants=conditionants or [],
            biomed_performance=biomed,
        )

        # Staging: ensure action plan visible for homologation when engine is silent on improvement
        if staging_demo and not (intel.plano_acao or []):
            from backend.executive.schemas import ActionItem
            demo_actions = [
                ActionItem(
                    id="act-demo-1",
                    title="Revisão ergonômica no setor Operacional",
                    priority="alta",
                    justification="Concentração persistente de impacto setorial apesar de tendência de melhora.",
                    category="ergonomia",
                    status="proposta",
                    indicator="dias_perdidos|eventos",
                    baseline="baseline setorial do período anterior",
                    meta="redução material da concentração setorial",
                    result="aguardando validação médica",
                    medical_validation="pendente",
                ),
                ActionItem(
                    id="act-demo-2",
                    title="Vigilância de grupos alfabéticos CID de maior participação",
                    priority="media",
                    justification="Pareto CID indica concentração; grupo alfabético ≠ capítulo oficial.",
                    category="vigilancia",
                    status="proposta",
                    indicator="eventos",
                    baseline="participação acumulada atual",
                    meta="monitorar top causas sem ranking nominal",
                    result="aguardando validação médica",
                    medical_validation="pendente",
                ),
                ActionItem(
                    id="act-demo-3",
                    title="Destravar condicionantes empresariais pendentes",
                    priority="alta",
                    justification="2 intervenções prioritárias adiada/impedida reduzem cobertura potencial.",
                    category="gestao",
                    status="proposta",
                    indicator="cobertura|execucao",
                    baseline="cobertura atual",
                    meta="reativar plano aprovado pendente",
                    result="condicionado à decisão empresarial",
                    medical_validation="pendente",
                ),
            ]
            intel.plano_acao = [a.to_dict() for a in demo_actions]
            intel.o_que_recomendamos = [a.title for a in demo_actions]
            intel.recomendacoes = [
                {
                    "id": a.id,
                    "titulo": a.title,
                    "categoria": a.category,
                    "prioridade": a.priority,
                    "justificativa": a.justification,
                }
                for a in demo_actions
            ]

        # Keep resultado aligned after gravidade is known
        if isinstance(biomed.get("resultado_observado"), dict):
            biomed["resultado_observado"]["severidade"] = cur_dict.get("gravidade")
            biomed["resultado_observado"]["eventos"] = cur_dict.get("eventos")
            biomed["resultado_observado"]["dias"] = cur_dict.get("dias_perdidos")
            biomed["resultado_observado"]["horas"] = cur_dict.get("horas_perdidas")

        payload = {
            "engine_version": ENGINE_VERSION,
            "client": {
                "id": client.id,
                "label": client.nome_fantasia or client.nome,
            },
            "periodo": {
                "atual": {"inicio": periodo_inicio, "fim": periodo_fim},
                "baseline": {"inicio": base_inicio, "fim": base_fim}
                if comparable
                else None,
                "comparabilidade": "integral" if comparable else "bloqueada",
            },
            "qualidade": {
                "iqb": iqb_val,
                "classificacao": iqb_label,
                "dimensoes": iqb_dims,
                "comparabilidade": "integral" if comparable else "bloqueada",
                "cobertura_horas": (
                    "registrada"
                    if cur_dict.get("horas_perdidas") is not None
                    else (
                        "estimada"
                        if cur_dict.get("horas_estimadas") is not None
                        else "indisponivel"
                    )
                ),
                "limitations": [
                    "IQB e dimensões via DataQualityService; sem inventário de denominador.",
                ],
            },
            "kpis": [k.to_dict() for k in kpis],
            "executive_score": score.to_dict(),
            "charts": [c.to_dict() for c in charts],
            "biomed_performance": biomed,
            "conditionants": conditionants or [],
            "roi": {
                "kind": "ROI_NAO_CALCULAVEL",
                "valor": None,
                "premissas": {},
                "limitacoes": [
                    "ROI só com cobertura de horas e custos explícitos; não inventado."
                ],
            },
            "intelligence": intel.to_dict(),
            "insights": [
                {
                    "title": "Resumo executivo",
                    "body": intel.resumo_executivo,
                    "limitations": intel.limitacoes[:2],
                },
                {
                    "title": "Diagnóstico situacional",
                    "body": intel.diagnostico_situacional,
                    "limitations": [],
                },
            ],
            "narrative_lines": [
                line.strip()
                for line in intel.resumo_executivo.replace(". ", ".\n").split("\n")
                if line.strip()
            ],
            "navigation": [
                {"id": "command", "label": "Command Center", "path": "#command"},
                {"id": "analytics", "label": "Executive Analytics", "path": "#analytics"},
                {"id": "presentation", "label": "Apresentação", "path": "/executive/presentation"},
                {"id": "absenteeism", "label": "Absenteísmo", "path": "#absenteeism"},
                {"id": "epidemiology", "label": "Epidemiologia", "path": "#epidemiology"},
                {"id": "sectors", "label": "Setores e Risco", "path": "#sectors"},
                {"id": "cost", "label": "Custo", "path": "#cost"},
                {"id": "performance", "label": "Performance BioMed", "path": "#performance"},
                {"id": "actions", "label": "Plano de Ação", "path": "#actions"},
                {"id": "intelligence", "label": "Inteligência / IA", "path": "#intelligence"},
                {"id": "questions", "label": "Perguntas", "path": "#questions"},
                {"id": "productivity", "label": "Produtividade", "path": "#productivity"},
                {"id": "quality", "label": "Dados / Qualidade", "path": "#quality"},
                {"id": "admin", "label": "Administração", "path": "#admin"},
            ],
            "privacy": {
                "small_group_threshold": SMALL_GROUP_THRESHOLD,
                "pii_excluded": True,
                "worker_ranking": False,
                "presentation_default": "aggregate",
                "clinical_nominal": "perfil_autorizado_apenas",
            },
            "limitations": cur_dict.get("limitacoes") or [],
            "methodology": {
                "metrics": "MetricService",
                "quality": "DataQualityService",
                "score": "PerformanceService.executive_score",
                "intelligence": "rule_engine_deterministic_v1",
                "cost": "AbsenteeismCostModel",
                "llm": False,
                "how": [
                    "KPIs e distribuições: MetricService (canônico).",
                    "IQB: DataQualityService.analyze.",
                    "Executive Health Score: PerformanceService.executive_score.",
                    "Narrativa/ações: rule engine determinístico (sem LLM).",
                    "Custo: HORAS × CUSTO_HORA com estados REAL/ESTIMADO/ILUSTRATIVO/NÃO INFORMADO.",
                    "Denominadores (headcount) nunca inventados.",
                    "Sem double-counting de dias convertidos + horas registradas.",
                ],
            },
            "hero": {
                "empresa": client.nome_fantasia or client.nome,
                "periodo": f"{periodo_inicio} → {periodo_fim}",
                "status": "comparavel" if comparable else "descritivo",
                "tendencia": None,
                "score": score.to_dict(),
                "confianca": intel.confianca,
                "mensagem": intel.mensagem_executiva,
            },
            "kpis_primary": [k.to_dict() for k in kpis if k.tier == "primary"],
            "kpis_secondary": [k.to_dict() for k in kpis if k.tier == "secondary"],
            "conditionants_summary": None,
        }
        # Fill hero trend from dias KPI
        dias_kpi = next((k for k in kpis if k.id == "dias"), None)
        payload["hero"]["tendencia"] = dias_kpi.trend if dias_kpi else None
        conds = payload.get("conditionants") or []
        pending = [
            c
            for c in conds
            if str(c.get("status", "")).lower()
            in {"adiada", "recusada", "impedida", "parcialmente_executada", "pendente"}
        ]
        if pending:
            payload["conditionants_summary"] = (
                f"{len(pending)} intervenção(ões) prioritária(s) permaneceram pendentes "
                "por decisão operacional da empresa, reduzindo a cobertura potencial do plano."
            )
        elif conds:
            payload["conditionants_summary"] = (
                "Condicionantes empresariais registradas; sem pendências bloqueantes neste payload."
            )
        else:
            payload["conditionants_summary"] = (
                "Sem condicionantes empresariais registradas neste período."
            )

        # --- EXEC-03: cost, recurrence, temporal patterns, catalog ---
        payload["custo"] = build_cost_block(
            cur_dict, client, cur_dict.get("serie_temporal") or []
        )
        ck = cost_kpi(payload["custo"])
        payload["kpis"].append(ck.to_dict())
        if ck.available:
            payload["kpis_primary"].append(ck.to_dict())
        # Attach cost evolution chart when present
        evo_chart = (payload["custo"].get("breakdown") or {}).get("evolucao_chart")
        if evo_chart:
            payload["charts"].append(evo_chart)
        # Cost-by charts
        for key, cid, title in (
            ("por_cid", "custo_cid", "Custo estimado por grupo CID"),
            ("por_setor", "custo_setor", "Custo estimado por setor"),
            ("por_centro_custo", "custo_centro_custo", "Custo estimado por centro de custo"),
        ):
            rows = (payload["custo"].get("breakdown") or {}).get(key) or []
            if rows:
                payload["charts"].append(
                    ChartSeries(
                        id=cid,
                        title=title,
                        chart_type="bar",
                        categories=[r.get("label", "—") for r in rows[:12]],
                        series=[
                            {
                                "name": "Custo estimado (R$)",
                                "data": [r.get("custo_estimado") or 0 for r in rows[:12]],
                            }
                        ],
                        notes=[
                            payload["custo"].get("linguagem") or "",
                            "Alocação proporcional por participação em dias (proxy).",
                        ],
                    ).to_dict()
                )

        payload["recorrencia_agregada"] = compute_recurrence_aggregate(
            self.db, client_id, periodo_inicio, periodo_fim
        )
        # Prolonged absences: events with dias >= 15 when measurable
        long_n = 0
        long_days = 0.0
        try:
            from backend.models import Atestado, Upload

            for row in (
                self.db.query(Atestado)
                .join(Upload, Atestado.upload_id == Upload.id)
                .filter(Upload.client_id == client_id)
                .all()
            ):
                d = float(row.dias_perdidos or row.dias_atestados or 0) or 0.0
                if d >= 15:
                    long_n += 1
                    long_days += d
            if long_n:
                payload["afastamentos_longos"] = {
                    "n_eventos": long_n,
                    "dias_totais": round(long_days, 2),
                    "limiar_dias": 15,
                    "nota": "Limiar operacional 15 dias; não é classificação INSS.",
                }
            else:
                payload["afastamentos_longos"] = {
                    "n_eventos": 0,
                    "dias_totais": 0,
                    "limiar_dias": 15,
                    "nota": "Nenhum afastamento ≥15 dias no recorte.",
                }
        except Exception:
            payload["afastamentos_longos"] = None

        wd = weekday_distribution(self.db, client_id, periodo_inicio, periodo_fim)
        cargo = cargo_distribution(
            self.db,
            client_id,
            periodo_inicio,
            periodo_fim,
            threshold=SMALL_GROUP_THRESHOLD,
        )
        payload["distribuicao_cargo"] = cargo
        payload["padroes_temporais"] = {"dia_semana": wd} if wd else None
        if wd:
            payload["charts"].append(
                ChartSeries(
                    id="dia_semana",
                    title="Eventos por dia da semana",
                    chart_type="bar",
                    categories=[x["dia"] for x in wd],
                    series=[{"name": "Eventos", "data": [x["eventos"] for x in wd]}],
                    notes=["Baseado em data_afastamento quando válida."],
                ).to_dict()
            )
        if cargo:
            payload["charts"].append(
                ChartSeries(
                    id="cargo",
                    title="Impacto por cargo (agregado)",
                    chart_type="bar",
                    categories=[c["cargo"] for c in cargo[:12]],
                    series=[
                        {"name": "Eventos", "data": [c["eventos"] for c in cargo[:12]]},
                        {
                            "name": "Dias",
                            "data": [c["dias_perdidos"] for c in cargo[:12]],
                        },
                    ],
                    notes=["Grupos pequenos suprimidos. Sem PII."],
                ).to_dict()
            )

        payload["impacto_economico_biomed"] = biomed_economic_impact(
            cur_dict, base_dict if comparable else None, payload["custo"]
        )
        # Financial narrative for conditionants (no hypothetical money)
        if pending:
            payload["condicionantes_financeiras"] = (
                f"O potencial de redução permaneceu parcialmente limitado pela não "
                f"implementação de {len(pending)} ação(ões) prioritária(s). "
                "Não se estima dinheiro hipoteticamente perdido sem modelo contrafactual válido."
            )
        else:
            payload["condicionantes_financeiras"] = None

        flags = build_availability_flags(payload, cur_dict)
        payload["analytics_catalog"] = catalog_availability(flags)
        payload["decision_questions"] = QUESTIONS
        payload["exec_level"] = {
            "command_center": True,
            "analytics": True,
            "presentation": True,
        }
        # EXEC-08 — first CEO experience (premium opening screen)
        payload["first_experience"] = compose_first_experience(payload)
        # EXEC-09 — decision experience (visual conversation, not a modal)
        payload["decision_experience"] = compose_decision_experience(payload)

        assert_no_pii_in_payload(payload)
        return payload

    def build_presentation(
        self,
        *,
        client_id: int,
        periodo_inicio: Optional[str] = None,
        periodo_fim: Optional[str] = None,
        efetivo_trabalhadores: Optional[int] = None,
    ) -> dict[str, Any]:
        payload = self.build_command_center(
            client_id=client_id,
            periodo_inicio=periodo_inicio,
            periodo_fim=periodo_fim,
            efetivo_trabalhadores=efetivo_trabalhadores,
        )
        deck = compose_presentation(payload)
        deck["client"] = payload.get("client")
        deck["periodo"] = payload.get("periodo")
        deck["privacy"] = payload.get("privacy")
        assert_no_pii_in_payload(deck)
        return deck

    def answer_executive_question(
        self,
        qid: str,
        *,
        client_id: int,
        periodo_inicio: Optional[str] = None,
        periodo_fim: Optional[str] = None,
        efetivo_trabalhadores: Optional[int] = None,
    ) -> dict[str, Any]:
        payload = self.build_command_center(
            client_id=client_id,
            periodo_inicio=periodo_inicio,
            periodo_fim=periodo_fim,
            efetivo_trabalhadores=efetivo_trabalhadores,
        )
        return answer_question(qid, payload)

    def analyze(
        self,
        analysis_id: str,
        *,
        client_id: int,
        periodo_inicio: Optional[str] = None,
        periodo_fim: Optional[str] = None,
        efetivo_trabalhadores: Optional[int] = None,
    ) -> dict[str, Any]:
        from backend.executive.analysis_intelligence import analyze_visualization

        payload = self.build_command_center(
            client_id=client_id,
            periodo_inicio=periodo_inicio,
            periodo_fim=periodo_fim,
            efetivo_trabalhadores=efetivo_trabalhadores,
        )
        return analyze_visualization(analysis_id, payload)

    def _kpis(
        self,
        cur: dict[str, Any],
        base: dict[str, Any] | None,
        iqb: Any,
        iqb_label: str | None,
    ) -> list[KpiCard]:
        def trend(key: str) -> str | None:
            if not base or base.get(key) is None or cur.get(key) is None:
                return None
            b, c = float(base[key]), float(cur[key])
            if b == 0:
                return None
            d = (c - b) / abs(b)
            if d <= -0.05:
                return "melhora"
            if d >= 0.05:
                return "piora"
            return "estabilidade"

        cards = [
            KpiCard(
                "dias",
                "Dias perdidos",
                cur.get("dias_perdidos"),
                "dias",
                True,
                trend=trend("dias_perdidos"),
                tier="primary",
            ),
            KpiCard(
                "horas",
                "Horas perdidas (registradas)",
                cur.get("horas_perdidas"),
                "h",
                cur.get("horas_perdidas") is not None,
                unavailable_reason=None
                if cur.get("horas_perdidas") is not None
                else "Cobertura de horas registrada insuficiente",
                empty_label="Horas registradas indisponíveis — sem zero artificial.",
                tier="primary",
            ),
            KpiCard(
                "eventos",
                "Eventos",
                cur.get("eventos"),
                "",
                True,
                trend=trend("eventos"),
                tier="primary",
            ),
            KpiCard(
                "trabalhadores",
                "Trabalhadores afetados",
                cur.get("trabalhadores_afetados"),
                "",
                cur.get("trabalhadores_afetados") is not None,
                unavailable_reason=None
                if cur.get("trabalhadores_afetados") is not None
                else "Identidade agregada insuficiente",
                empty_label="Identidade agregada insuficiente.",
                tier="primary",
            ),
            KpiCard(
                "duracao",
                "Duração média",
                cur.get("duracao_media"),
                "dias",
                cur.get("duracao_media") is not None,
                empty_label="Duração média indisponível.",
                tier="secondary",
            ),
            KpiCard(
                "freq100",
                "Frequência /100",
                cur.get("eventos_por_100"),
                "",
                cur.get("eventos_por_100") is not None,
                unavailable_reason=None
                if cur.get("eventos_por_100") is not None
                else "Headcount não informado — frequência por 100 indisponível.",
                empty_label="Headcount não informado — frequência por 100 indisponível.",
                tier="secondary",
            ),
            KpiCard(
                "severidade",
                "Severidade",
                cur.get("gravidade"),
                "dias/evento",
                cur.get("gravidade") is not None,
                unavailable_reason=None
                if cur.get("gravidade") is not None
                else "Severidade não calculável neste período",
                empty_label="Severidade não calculável neste período.",
                tier="secondary",
            ),
            KpiCard(
                "iqb",
                "IQB",
                iqb,
                iqb_label or "",
                iqb is not None,
                unavailable_reason=None if iqb is not None else "IQB indisponível",
                empty_label="IQB indisponível para o período.",
                tier="secondary",
            ),
        ]
        return cards


    def _build_temporal_series(
        self,
        client_id: int,
        periodo_inicio: str,
        periodo_fim: str,
        efetivo_trabalhadores: int | None,
    ) -> list[dict]:
        """Month-by-month events/days via MetricService (no JS formulas)."""
        out = []
        cur = periodo_inicio
        while cur <= periodo_fim:
            try:
                m = self.metrics.compute(
                    client_id,
                    cur,
                    cur,
                    efetivo_trabalhadores=efetivo_trabalhadores,
                    suppress_small_groups=True,
                    small_group_threshold=SMALL_GROUP_THRESHOLD,
                )
                met = getattr(m, "metricas", m)
                h_reg = getattr(met, "horas_perdidas_registradas", None)
                h_est = getattr(met, "horas_perdidas_estimadas", None)
                horas = None
                if h_reg is not None and float(h_reg) > 0:
                    horas = float(h_reg)
                elif h_est is not None and float(h_est) > 0:
                    horas = float(h_est)
                out.append(
                    {
                        "mes": cur,
                        "eventos": getattr(met, "eventos", None)
                        or getattr(met, "eventos_brutos", 0)
                        or 0,
                        "dias": float(getattr(met, "dias_perdidos", 0) or 0),
                        "horas": horas,
                    }
                )
            except Exception:
                out.append({"mes": cur, "eventos": 0, "dias": 0})
            cur = _month_add(cur, 1)
        return out

    def _charts(self, cur: dict[str, Any]) -> list[ChartSeries]:
        charts: list[ChartSeries] = []

        # Temporal: atual + média móvel simples (3) quando n>=3
        serie = cur.get("serie_temporal") or []
        cats, vals, dias_vals = [], [], []
        for item in serie:
            if isinstance(item, dict):
                cats.append(str(item.get("mes") or item.get("periodo") or ""))
                vals.append(float(item.get("eventos") or item.get("valor") or 0))
                dias_vals.append(float(item.get("dias") or 0))
        if len(cats) >= 2:
            ma = []
            for i in range(len(vals)):
                window = vals[max(0, i - 2) : i + 1]
                ma.append(round(sum(window) / len(window), 2))
            charts.append(
                ChartSeries(
                    id="evolucao_temporal",
                    title="Evolução temporal de eventos",
                    chart_type="line",
                    categories=cats,
                    series=[
                        {"name": "Atual", "data": vals},
                        {"name": "Média móvel (3)", "data": ma},
                        {"name": "Dias perdidos", "data": dias_vals},
                    ],
                    notes=[
                        "Linha principal = eventos do mês.",
                        "Média móvel de 3 períodos quando série suficiente.",
                        "Baseline de período completo no comparativo do hero.",
                    ],
                )
            )
        else:
            charts.append(
                ChartSeries(
                    id="evolucao_temporal",
                    title="Evolução temporal de eventos",
                    chart_type="line",
                    categories=[],
                    series=[],
                    empty_reason="Série temporal insuficiente para tendência.",
                    notes=["Requer ao menos 2 meses com dados."],
                )
            )

        # Pareto CID (grupo alfabético — NÃO capítulo oficial)
        cid = cur.get("distribuicao_cid") or []
        rows = []
        for item in cid:
            if isinstance(item, dict):
                rows.append(
                    (
                        str(item.get("grupo") or item.get("letra") or item.get("cid") or "?"),
                        float(item.get("eventos") or item.get("valor") or 0),
                        float(item.get("dias_perdidos") or item.get("dias") or 0),
                    )
                )
        rows.sort(key=lambda x: x[1], reverse=True)
        if rows:
            total = sum(r[1] for r in rows) or 1.0
            acc = 0.0
            cum = []
            for _, v, _ in rows:
                acc += v
                cum.append(round(100.0 * acc / total, 2))
            charts.append(
                ChartSeries(
                    id="pareto_cid",
                    title="Pareto — grupos alfabéticos CID (não capítulo oficial)",
                    chart_type="pareto",
                    categories=[r[0] for r in rows],
                    series=[
                        {"name": "Eventos", "data": [r[1] for r in rows]},
                        {"name": "Acumulado %", "data": cum},
                        {"name": "Dias", "data": [r[2] for r in rows]},
                    ],
                    notes=[
                        "grupo_alfabetico_cid não é capítulo CID oficial.",
                        f"Supressão de grupos com n < {SMALL_GROUP_THRESHOLD} aplicada na origem quando habilitada.",
                    ],
                )
            )

        # Setores
        setores = cur.get("distribuicao_setor") or []
        scats, sevt, sdias = [], [], []
        for item in setores:
            if isinstance(item, dict):
                n = item.get("setor") or item.get("nome")
                if not n:
                    continue
                scats.append(str(n))
                sevt.append(float(item.get("eventos") or 0))
                sdias.append(float(item.get("dias_perdidos") or item.get("dias") or 0))
        if scats:
            charts.append(
                ChartSeries(
                    id="setores",
                    title="Setores — volume e severidade (dias)",
                    chart_type="bar",
                    categories=scats[:12],
                    series=[
                        {"name": "Eventos", "data": sevt[:12]},
                        {"name": "Dias perdidos", "data": sdias[:12]},
                    ],
                    notes=["Centro de custo permanece separado em módulo dedicado."],
                )
            )

        # Centro de custo (campo distinto de setor)
        ccs = cur.get("distribuicao_centro_custo") or []
        cc_cats, cc_evt, cc_dias = [], [], []
        for item in ccs:
            if isinstance(item, dict):
                n = item.get("centro_custo") or item.get("nome")
                if not n or n == "GRUPO_SUPRIMIDO":
                    continue
                cc_cats.append(str(n))
                cc_evt.append(float(item.get("eventos") or 0))
                cc_dias.append(float(item.get("dias_perdidos") or item.get("dias") or 0))
        if cc_cats:
            charts.append(
                ChartSeries(
                    id="centro_custo",
                    title="Centro de custo — volume e dias",
                    chart_type="bar",
                    categories=cc_cats[:12],
                    series=[
                        {"name": "Eventos", "data": cc_evt[:12]},
                        {"name": "Dias perdidos", "data": cc_dias[:12]},
                    ],
                    notes=["Campo centro_custo distinto de setor."],
                )
            )

        return charts

    def _score_view(
        self,
        cur: dict[str, Any],
        base: dict[str, Any] | None,
        iqb: Any,
        comparable: bool,
        conditionants: list[dict[str, Any]] | None,
        biomed: dict[str, Any] | None,
    ) -> ExecutiveScoreView:
        """Delegate to Performance Engine — never invent a parallel formula or neutral 50."""
        biomed = biomed or {}
        prod = biomed.get("producao") or {}
        actions = ActionCounts(
            propostas=int(prod.get("planejadas") or 0),
            aprovadas=int(prod.get("aprovadas") or 0),
            executadas=int(prod.get("executadas") or 0),
        )
        cond_objs: list[Conditionant] = []
        for c in conditionants or []:
            if not isinstance(c, dict):
                continue
            cond_objs.append(
                Conditionant(
                    recomendacao_id=str(c.get("id") or c.get("recomendacao_id") or "cond"),
                    decisao=str(c.get("status") or c.get("decisao") or "pendente"),
                    status=str(c.get("status") or "pendente"),
                    barreira=c.get("barreira"),
                )
            )

        deltas = {
            "eventos": _delta(cur.get("eventos"), (base or {}).get("eventos"))
            if comparable and base
            else None,
            "dias_perdidos": _delta(
                cur.get("dias_perdidos"), (base or {}).get("dias_perdidos")
            )
            if comparable and base
            else None,
            "gravidade": _delta(cur.get("gravidade"), (base or {}).get("gravidade"))
            if comparable and base
            else None,
            "recorrencia": _delta(
                cur.get("recorrencia"), (base or {}).get("recorrencia")
            )
            if comparable and base
            else None,
        }
        coverage = biomed.get("cobertura")
        # PerformanceService.analyze is flag-gated; executive_score method itself is pure.
        raw = PerformanceService(require_flag=False).executive_score(
            deltas=deltas,
            effectiveness_code="NAO_AVALIAVEL",
            coverage=float(coverage) if coverage is not None else None,
            iqb=float(iqb) if iqb is not None else None,
            action_counts=actions,
            metas_atingidas=None,
            conditionants=cond_objs,
            headcount_missing=cur.get("eventos_por_100") is None,
        )
        dims = raw.get("dimensoes") or {}
        components = []
        label_map = {
            "evolucao_frequencia": "Frequência",
            "evolucao_severidade": "Severidade",
            "recorrencia": "Recorrência",
            "cobertura_assistencial": "Cobertura",
            "execucao_acoes": "Execução",
            "atingimento_metas": "Metas",
            "qualidade_dados": "Qualidade",
            "condicionantes_empresa": "Condicionantes",
        }
        for key, meta in dims.items():
            components.append(
                {
                    "id": key,
                    "label": label_map.get(key, key),
                    "value": (meta or {}).get("valor"),
                    "note": (meta or {}).get("status"),
                    "status": (meta or {}).get("status"),
                }
            )
        # Map conceptual EXEC-01 dimensions for UI transparency
        components.extend(
            [
                {
                    "id": "tendencia",
                    "label": "Tendência",
                    "value": None,
                    "note": "avaliada" if comparable else "indisponivel",
                    "status": "avaliada" if comparable else "indisponivel",
                },
                {
                    "id": "concentracao",
                    "label": "Concentração",
                    "value": None,
                    "note": "avaliada" if cur.get("setores_criticos") else "nao_avaliada",
                    "status": "avaliada" if cur.get("setores_criticos") else "nao_avaliada",
                },
                {
                    "id": "efetividade",
                    "label": "Efetividade",
                    "value": None,
                    "note": "indisponivel",
                    "status": "indisponivel",
                },
            ]
        )

        if raw.get("status") != "OK" or raw.get("score") is None:
            return ExecutiveScoreView(
                available=False,
                score=None,
                label="SCORE NÃO DISPONÍVEL",
                components=components,
                limitations=[
                    "Cobertura de dimensões insuficiente no Performance Engine.",
                    "Não se utiliza 50 neutro artificial.",
                    f"cobertura_score={raw.get('cobertura_score')}",
                ],
            )
        return ExecutiveScoreView(
            available=True,
            score=raw.get("score"),
            label="Executive Health Score",
            components=components,
            limitations=[
                "Score via PerformanceService.executive_score (sem fórmula paralela).",
                "Não é ranking de trabalhador nem veredito clínico individual.",
            ],
        )
