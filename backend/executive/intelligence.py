"""Deterministic BioMed Intelligence rule engine (no external LLM)."""

from __future__ import annotations

from typing import Any

from backend.executive.schemas import ActionItem, IntelligenceBundle
from backend.performance.recommendation_engine import RecommendationEngine
from backend.performance.schemas import MetricSnapshot, ThresholdConfig


def _trend_label(delta: float | None, thr: float = 0.05) -> str:
    if delta is None:
        return "indisponivel"
    if delta <= -thr:
        return "melhora"
    if delta >= thr:
        return "piora"
    return "estabilidade"


def _pct(a: float | None, b: float | None) -> float | None:
    if a is None or b is None or b == 0:
        return None
    return (a - b) / abs(b)


class ExecutiveIntelligenceEngine:
    """Produces structured executive narrative from aggregates only."""

    def __init__(self, thresholds: ThresholdConfig | None = None) -> None:
        self.thresholds = thresholds or ThresholdConfig()
        self.reco = RecommendationEngine(self.thresholds)

    def build(
        self,
        *,
        client_name: str,
        current: dict[str, Any],
        baseline: dict[str, Any] | None,
        iqb: float | None,
        iqb_label: str | None,
        conditionants: list[dict[str, Any]] | None = None,
        biomed_performance: dict[str, Any] | None = None,
    ) -> IntelligenceBundle:
        cur_evt = float(current.get("eventos") or 0)
        cur_dias = float(current.get("dias_perdidos") or 0)
        cur_horas = current.get("horas_perdidas")
        cur_trab = current.get("trabalhadores_afetados")
        base = baseline or {}
        d_evt = _pct(cur_evt, float(base["eventos"])) if base.get("eventos") is not None else None
        d_dias = (
            _pct(cur_dias, float(base["dias_perdidos"]))
            if base.get("dias_perdidos") is not None
            else None
        )
        trend_evt = _trend_label(d_evt, self.thresholds.material_change)
        trend_dias = _trend_label(d_dias, self.thresholds.material_change)

        conf = "media"
        limitations = list(current.get("limitacoes") or [])
        limitations.append(
            "Narrativa gerada por motor de regras determinístico; sem LLM externo."
        )
        limitations.append(
            "Não estabelece causalidade exclusiva entre ações BioMed e desfecho."
        )
        if iqb is not None and iqb < self.thresholds.min_iqb:
            conf = "baixa"
            limitations.append(
                f"IQB={iqb:.1f} abaixo do limiar {self.thresholds.min_iqb}; interpretação cautelosa."
            )
        elif iqb is not None and iqb >= 80:
            conf = "alta"

        # Snapshot-like objects for RecommendationEngine
        snap_cur = MetricSnapshot(
            client_id=int(current.get("client_id") or 0),
            periodo_inicio=str(current.get("periodo_inicio") or ""),
            periodo_fim=str(current.get("periodo_fim") or ""),
            eventos=float(cur_evt),
            dias_perdidos=cur_dias,
            gravidade=current.get("gravidade"),
            recorrencia=current.get("recorrencia"),
            duracao_media=current.get("duracao_media"),
            iqb=iqb,
            grupos_cid=list(current.get("grupos_cid") or []),
            setores_criticos=list(current.get("setores_criticos") or []),
            afastamentos_longos=current.get("afastamentos_longos"),
        )
        snap_base = MetricSnapshot(
            client_id=int(current.get("client_id") or 0),
            periodo_inicio=str(base.get("periodo_inicio") or current.get("periodo_inicio") or ""),
            periodo_fim=str(base.get("periodo_fim") or current.get("periodo_fim") or ""),
            eventos=float(base.get("eventos") or cur_evt),
            dias_perdidos=float(base.get("dias_perdidos") or cur_dias),
            gravidade=base.get("gravidade"),
            recorrencia=base.get("recorrencia"),
            duracao_media=base.get("duracao_media"),
            iqb=iqb,
            grupos_cid=list(base.get("grupos_cid") or current.get("grupos_cid") or []),
            setores_criticos=list(
                base.get("setores_criticos") or current.get("setores_criticos") or []
            ),
            afastamentos_longos=base.get("afastamentos_longos"),
        )
        recs = self.reco.recommend(baseline=snap_base, current=snap_cur)
        reco_dicts = []
        for i, r in enumerate(recs[:8]):
            d = r.to_dict() if hasattr(r, "to_dict") else {}
            reco_dicts.append(
                {
                    "id": d.get("id", f"r{i}"),
                    "titulo": d.get("descricao") or d.get("id") or f"Recomendação {i+1}",
                    "categoria": d.get("categoria", "gestao"),
                    "prioridade": d.get("criticidade", "media"),
                    "justificativa": "; ".join(d.get("evidencias") or [])
                    or d.get("descricao", ""),
                }
            )

        actions: list[ActionItem] = []
        for i, rd in enumerate(reco_dicts[:6]):
            actions.append(
                ActionItem(
                    id=f"act-{i+1}",
                    title=str(rd.get("titulo") or "Ação proposta"),
                    priority=str(rd.get("prioridade") or "media"),
                    justification=str(rd.get("justificativa") or ""),
                    category=str(rd.get("categoria") or "gestao"),
                    status="proposta",
                    indicator="eventos|dias_perdidos",
                    medical_validation_required=True,
                )
            )

        cond = conditionants or []
        not_exec = [
            c
            for c in cond
            if str(c.get("status", "")).lower()
            in {"recusada", "adiada", "impedida", "parcialmente_executada"}
        ]

        dias_txt = (
            f"A variação observada de dias perdidos foi de {d_dias*100:.1f}% em janela comparável."
            if d_dias is not None
            else "Não há baseline comparável suficiente para quantificar variação de dias perdidos."
        )
        evt_txt = (
            f"A variação observada de eventos foi de {d_evt*100:.1f}%."
            if d_evt is not None
            else "Comparativo de eventos indisponível sem baseline válido."
        )

        biomed = biomed_performance or {}
        cov = biomed.get("cobertura")
        exe = biomed.get("execucao")
        biomed_lines = []
        if cov is not None:
            biomed_lines.append(f"A cobertura operacional atingiu {float(cov)*100:.0f}%.")
        if exe is not None:
            biomed_lines.append(
                f"A execução das ações aprovadas foi de {float(exe)*100:.1f}%."
            )
        if not biomed_lines:
            biomed_lines.append(
                "Indicadores de produção/cobertura BioMed ainda não foram informados neste payload."
            )

        if not_exec:
            cond_txt = (
                "O potencial de intervenção foi parcialmente limitado pela não execução "
                "de ações empresariais previamente recomendadas."
            )
        else:
            cond_txt = (
                "Não há condicionantes empresariais bloqueantes registradas neste período."
            )

        resumo = (
            f"{client_name}: {int(cur_evt)} eventos e {cur_dias:.1f} dias perdidos no período. "
            f"{evt_txt} {dias_txt} IQB={iqb if iqb is not None else 'n/d'}"
            f"{' ('+iqb_label+')' if iqb_label else ''}. "
            f"{' '.join(biomed_lines)} {cond_txt} "
            "O resultado é compatível com leitura operacional do período; "
            "não é possível estabelecer causalidade exclusiva."
        )

        diagnostico = (
            f"Tendência de eventos: {trend_evt}. Tendência de dias: {trend_dias}. "
            f"Trabalhadores afetados (identidade agregada): {cur_trab if cur_trab is not None else 'n/d'}. "
            f"Horas perdidas: {cur_horas if cur_horas is not None else 'indisponível/parcial'}."
        )

        fatores = []
        for s in (current.get("setores_criticos") or [])[:5]:
            fatores.append(f"Concentração setorial: {s}")
        for g in (current.get("grupos_cid") or [])[:5]:
            fatores.append(f"Grupo alfabético CID (não capítulo oficial): {g}")
        if not fatores:
            fatores.append("Sem concentração setorial/CID destacada acima do limiar.")

        alertas = []
        if trend_evt == "piora":
            alertas.append("Aumento material de frequência de eventos versus baseline.")
        if trend_dias == "piora":
            alertas.append("Aumento material de dias perdidos versus baseline.")
        if conf == "baixa":
            alertas.append("Confiança reduzida pela qualidade/cobertura dos dados.")
        if not alertas:
            alertas.append("Sem alerta material adicional no motor de regras.")

        hipoteses = [
            "Hipótese: concentração setorial pode explicar parte da frequência observada.",
            "Hipótese: variação de severidade pode refletir mix de CID/duração, não só volume.",
            "Hipótese: desfechos podem ser modulados por condicionantes empresariais.",
        ]

        evidencias = [
            f"eventos_atual={int(cur_evt)}",
            f"dias_perdidos_atual={cur_dias}",
            f"iqb={iqb}",
            f"trend_eventos={trend_evt}",
            f"trend_dias={trend_dias}",
        ]
        if base:
            evidencias.append(f"baseline_eventos={base.get('eventos')}")
            evidencias.append(f"baseline_dias={base.get('dias_perdidos')}")


        # EXEC-02 structured narrative (technical BioMed tone)
        o_que_mudou = []
        if d_dias is not None:
            o_que_mudou.append(
                f"Dias perdidos: variação de {d_dias*100:.1f}% versus baseline comparável ({trend_dias})."
            )
        else:
            o_que_mudou.append("Série/baseline insuficiente para quantificar variação de dias perdidos.")
        if d_evt is not None:
            o_que_mudou.append(
                f"Eventos: variação de {d_evt*100:.1f}% versus baseline ({trend_evt})."
            )
        else:
            o_que_mudou.append("Comparativo de eventos indisponível sem baseline válido.")

        onde_risco = list(fatores)
        por_que = [
            "Impacto operacional concentra-se onde volume e severidade se sobrepõem.",
            "Leitura agregada orienta priorização; não substitui avaliação clínica individual.",
        ]
        recomendamos = [
            str(r.get("titulo") or r.get("id"))
            for r in reco_dicts[:5]
        ] or ["Sem recomendações acionáveis com a evidência atual."]
        precisa_validacao = [
            "Toda ação proposta requer validação médica antes de aprovação empresarial.",
            "Não há execução automática de recomendações.",
        ]
        if not_exec:
            precisa_validacao.append(
                f"{len(not_exec)} condicionante(s) empresarial(is) permanece(m) "
                "pendente(s)/parcial(is), reduzindo a cobertura potencial do plano."
            )

        # Short executive message (no marketing)
        if trend_dias == "melhora" and current.get("setores_criticos"):
            mensagem = (
                f"Absenteísmo em tendência de melhora, com concentração persistente "
                f"de impacto no setor {current['setores_criticos'][0]}."
            )
        elif trend_dias == "piora":
            mensagem = (
                "Absenteísmo em tendência de piora na janela comparável; "
                "priorizar fatores de concentração setorial e CID."
            )
        elif trend_dias == "estabilidade":
            mensagem = (
                "Absenteísmo estável na janela comparável; monitorar concentração de risco."
            )
        else:
            mensagem = (
                "Leitura descritiva do período; tendência formal indisponível "
                "por insuficiência de baseline/série."
            )

        # Favorable BioMed lines only when data sustains
        if cov is not None and exe is not None and d_dias is not None and d_dias < 0:
            biomed_lines.append(
                f"A BioMed executou {float(exe)*100:.0f}% das ações aprovadas no período. "
                f"Observou-se redução de {abs(d_dias)*100:.0f}% nos dias perdidos em janela comparável."
            )
            biomed_lines.append(
                "A associação temporal é compatível com melhora operacional, "
                "sem permitir atribuição causal exclusiva."
            )

        resumo = (
            f"{client_name}: {int(cur_evt)} eventos e {cur_dias:.1f} dias perdidos no período. "
            f"{evt_txt} {dias_txt} "
            f"{' '.join(biomed_lines)} {cond_txt} "
            "Não é possível estabelecer causalidade exclusiva."
        )

        for i, a in enumerate(actions):
            a.baseline = (
                f"eventos={base.get('eventos')}" if base else "baseline n/d"
            )
            a.meta = "redução material vs baseline"
            a.result = "aguardando ciclo de monitoramento"
            a.deadline = None
            a.medical_validation = "pendente"

        return IntelligenceBundle(
            resumo_executivo=resumo,
            diagnostico_situacional=diagnostico,
            fatores_prioritarios=fatores,
            alertas=alertas,
            hipoteses=hipoteses,
            recomendacoes=reco_dicts,
            plano_acao=[a.to_dict() for a in actions],
            evidencias=evidencias,
            limitacoes=limitations,
            confianca=conf,
            o_que_mudou=o_que_mudou,
            onde_esta_o_risco=onde_risco,
            por_que_importa=por_que,
            o_que_recomendamos=recomendamos,
            o_que_precisa_validacao=precisa_validacao,
            mensagem_executiva=mensagem,
        )
