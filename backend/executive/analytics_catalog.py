"""Executive Analytics catalog — EXEC-03.

Each analysis answers an objective question and declares field requirements.
Analyses are marked available/unavailable based on data presence — never invented.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass
class AnalysisSpec:
    id: str
    title: str
    question: str  # QUEM / O QUE / QUANDO / ONDE / QUANTO / E AGORA
    pergunta: str
    chart_type: str
    required_fields: list[str] = field(default_factory=list)
    available: bool = False
    unavailable_reason: Optional[str] = None
    privacy: str = "aggregate"  # aggregate | clinical_authorized
    slide_id: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


CATALOG: list[AnalysisSpec] = [
    AnalysisSpec("evolucao_eventos", "Evolução mensal de eventos", "QUANDO", "Como evoluem os eventos no tempo?", "line", ["serie_temporal"], slide_id="evolucao"),
    AnalysisSpec("evolucao_dias", "Evolução mensal de dias perdidos", "QUANDO", "Como evoluem os dias perdidos?", "line", ["serie_temporal"], slide_id="impacto_dias_horas"),
    AnalysisSpec("evolucao_horas", "Evolução mensal de horas perdidas", "QUANDO", "Como evoluem as horas perdidas?", "line", ["serie_temporal_horas"], slide_id="impacto_dias_horas"),
    AnalysisSpec("media_movel", "Média móvel", "QUANDO", "Qual a tendência suavizada?", "line", ["serie_temporal"]),
    AnalysisSpec("tendencia_baseline", "Tendência vs baseline", "QUANTO", "O período atual melhorou ou piorou vs baseline?", "compare", ["baseline"], slide_id="resumo"),
    AnalysisSpec("pareto_cid_eventos", "Pareto CID por eventos", "O QUE", "Quais grupos CID concentram eventos?", "pareto", ["distribuicao_cid"], slide_id="cid"),
    AnalysisSpec("pareto_cid_dias", "Pareto CID por dias", "O QUE", "Quais grupos CID concentram dias perdidos?", "pareto", ["distribuicao_cid"], slide_id="cid"),
    AnalysisSpec("pareto_cid_horas", "Pareto CID por horas", "O QUE", "Quais grupos CID concentram horas?", "pareto", ["distribuicao_cid_horas"]),
    AnalysisSpec("grupos_cid", "Distribuição por grupos CID", "O QUE", "Qual a composição alfabética CID?", "bar", ["distribuicao_cid"], slide_id="cid"),
    AnalysisSpec("setores_eventos", "Setores por eventos", "ONDE", "Qual setor concentra eventos?", "bar", ["distribuicao_setor"], slide_id="setores"),
    AnalysisSpec("setores_dias", "Setores por dias", "ONDE", "Qual setor concentra dias perdidos?", "bar", ["distribuicao_setor"], slide_id="setores"),
    AnalysisSpec("setores_horas", "Setores por horas", "ONDE", "Qual setor concentra horas?", "bar", ["distribuicao_setor_horas"]),
    AnalysisSpec("freq_sev_setor", "Frequência × severidade por setor", "ONDE", "Onde há alto volume e alta severidade?", "scatter", ["distribuicao_setor"]),
    AnalysisSpec("heatmap_setor_mes", "Heatmap setor × mês", "ONDE/QUANDO", "Onde e quando concentra?", "heatmap", ["heatmap_setor_mes"]),
    AnalysisSpec("centro_custo", "Centro de custo", "ONDE", "Qual centro de custo concentra impacto?", "bar", ["distribuicao_centro_custo"]),
    AnalysisSpec("cargo", "Cargo", "ONDE", "Qual cargo concentra impacto?", "bar", ["distribuicao_cargo"]),
    AnalysisSpec("dia_semana", "Dia da semana", "QUANDO", "Em quais dias da semana ocorre mais?", "bar", ["distribuicao_dia_semana"], slide_id="padroes_temporais"),
    AnalysisSpec("faixa_horaria", "Faixa horária", "QUANDO", "Há faixa horária crítica?", "bar", ["distribuicao_faixa_horaria"], slide_id="padroes_temporais"),
    AnalysisSpec("duracao", "Duração dos afastamentos", "O QUE", "Qual o perfil de duração?", "bar", ["distribuicao_duracao"], slide_id="afastamentos"),
    AnalysisSpec("afastamentos_prolongados", "Afastamentos prolongados", "O QUE", "Qual o impacto dos afastamentos longos?", "kpi", ["afastamentos_longos"], slide_id="afastamentos"),
    AnalysisSpec("recorrencia", "Recorrência (agregada)", "QUEM", "Quantos trabalhadores são recorrentes?", "bar", ["recorrencia_agregada"], privacy="aggregate", slide_id="recorrencia"),
    AnalysisSpec("genero", "Distribuição por gênero", "QUEM", "Há diferença por gênero?", "bar", ["distribuicao_genero"]),
    AnalysisSpec("faixa_etaria", "Faixas etárias", "QUEM", "Há concentração etária?", "bar", ["distribuicao_faixa_etaria"]),
    AnalysisSpec("comparativo_baseline", "Comparativo atual × baseline", "QUANTO", "Qual a magnitude da mudança?", "compare", ["baseline"], slide_id="resumo"),
    AnalysisSpec("antes_depois", "Antes × depois de intervenção", "QUANTO", "Houve mudança pós-intervenção?", "compare", ["janela_intervencao"]),
    AnalysisSpec("biomed_producao", "Produção BioMed", "E AGORA", "O que a BioMed planejou/aprovou/executou?", "kpi", ["biomed_performance"], slide_id="atuacao_biomed"),
    AnalysisSpec("biomed_cobertura", "Cobertura BioMed", "E AGORA", "Qual a cobertura operacional?", "kpi", ["biomed_performance"], slide_id="atuacao_biomed"),
    AnalysisSpec("biomed_execucao", "Execução das ações", "E AGORA", "Qual a taxa de execução?", "kpi", ["biomed_performance"], slide_id="atuacao_biomed"),
    AnalysisSpec("efetividade", "Efetividade", "E AGORA", "O resultado é compatível com melhora?", "kpi", ["biomed_performance"], slide_id="resultado"),
    AnalysisSpec("iqb", "Qualidade / IQB", "QUANTO", "Qual a confiabilidade da base?", "kpi", ["iqb"], slide_id="qualidade"),
    AnalysisSpec("completude", "Completude", "QUANTO", "Quão completa está a base?", "kpi", ["iqb_dimensoes"], slide_id="qualidade"),
    AnalysisSpec("cobertura_horas", "Cobertura de horas", "QUANTO", "Horas são registradas, estimadas ou indisponíveis?", "kpi", ["cobertura_horas"], slide_id="qualidade"),
    AnalysisSpec("condicionantes", "Condicionantes empresariais", "E AGORA", "O que permanece pendente na empresa?", "table", ["conditionants"], slide_id="condicionantes"),
    AnalysisSpec("custo_absenteismo", "Custo do absenteísmo", "QUANTO", "Qual o impacto laboral estimado?", "kpi", ["custo"], slide_id="custo"),
    AnalysisSpec("custo_evolucao", "Evolução do custo no tempo", "QUANTO", "Como evolui o impacto estimado?", "line", ["custo", "serie_temporal"], slide_id="custo"),
    AnalysisSpec("custo_cid", "Custo por CID", "QUANTO", "Quais causas concentram custo?", "pareto", ["custo", "distribuicao_cid"], slide_id="custo"),
    AnalysisSpec("custo_setor", "Custo por setor", "QUANTO", "Quais setores concentram custo?", "bar", ["custo", "distribuicao_setor"], slide_id="custo"),
]


def evaluate_catalog(availability: dict[str, bool], reasons: dict[str, str] | None = None) -> list[dict[str, Any]]:
    """Mark each catalog item available based on required field flags."""
    reasons = reasons or {}
    out = []
    for spec in CATALOG:
        ok = all(availability.get(f, False) for f in spec.required_fields) if spec.required_fields else False
        missing = [f for f in spec.required_fields if not availability.get(f, False)]
        item = AnalysisSpec(
            id=spec.id,
            title=spec.title,
            question=spec.question,
            pergunta=spec.pergunta,
            chart_type=spec.chart_type,
            required_fields=list(spec.required_fields),
            available=ok,
            unavailable_reason=None
            if ok
            else reasons.get(spec.id)
            or (
                "Campos indisponíveis: " + ", ".join(missing)
                if missing
                else "Dados insuficientes"
            ),
            privacy=spec.privacy,
            slide_id=spec.slide_id,
        )
        out.append(item.to_dict())
    return out
