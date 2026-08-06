"""Synthetic performance fixtures — no real tenant PII."""

from __future__ import annotations

from backend.performance.schemas import BiomedProductivity, Conditionant, MetricSnapshot


def snap(
    client_id: int = 99,
    inicio: str = "2024-01",
    fim: str = "2024-03",
    **kwargs,
) -> MetricSnapshot:
    base = dict(
        client_id=client_id,
        periodo_inicio=inicio,
        periodo_fim=fim,
        eventos=100.0,
        trabalhadores_unicos=80.0,
        dias_perdidos=200.0,
        horas_perdidas_registradas=1600.0,
        horas_perdidas_estimadas=0.0,
        duracao_media=2.0,
        frequencia=1.25,
        gravidade=2.0,
        recorrencia=0.2,
        afastamentos_longos=5.0,
        eventos_por_100=12.5,
        dias_por_trabalhador=2.5,
        horas_por_100=200.0,
        headcount=800.0,
        iqb=75.0,
        setores_criticos=["Producao"],
        grupos_cid=["J", "M"],
        meses_com_dados=3,
        cobertura_horas_registradas=1.0,
        cobertura_horas_estimadas=0.0,
        metodologia_horas="registradas_preferenciais",
        completude_periodo=1.0,
        limitacoes=[],
        fonte="synthetic_fixture",
    )
    base.update(kwargs)
    return MetricSnapshot(**base)


def baseline_ok() -> MetricSnapshot:
    return snap()


def current_severity_control() -> MetricSnapshot:
    """Events stable/up, days/hours/duration down."""
    return snap(
        inicio="2024-04",
        fim="2024-06",
        eventos=105.0,
        dias_perdidos=150.0,
        horas_perdidas_registradas=1200.0,
        duracao_media=1.4,
        gravidade=1.4,
        frequencia=1.3,
        recorrencia=0.2,
    )


def current_frequency_control() -> MetricSnapshot:
    return snap(
        inicio="2024-04",
        fim="2024-06",
        eventos=70.0,
        dias_perdidos=190.0,
        frequencia=0.9,
        recorrencia=0.1,
        gravidade=2.0,
        trabalhadores_unicos=60.0,
    )


def current_integral() -> MetricSnapshot:
    return snap(
        inicio="2024-04",
        fim="2024-06",
        eventos=60.0,
        dias_perdidos=100.0,
        horas_perdidas_registradas=800.0,
        duracao_media=1.2,
        frequencia=0.75,
        gravidade=1.2,
        recorrencia=0.08,
        iqb=80.0,
        grupos_cid=["M"],
    )


def current_worsened() -> MetricSnapshot:
    return snap(
        inicio="2024-04",
        fim="2024-06",
        eventos=130.0,
        dias_perdidos=280.0,
        frequencia=1.7,
        gravidade=2.5,
        recorrencia=0.3,
    )


def current_stable() -> MetricSnapshot:
    return snap(
        inicio="2024-04",
        fim="2024-06",
        eventos=101.0,
        dias_perdidos=202.0,
        frequencia=1.26,
        gravidade=2.01,
        recorrencia=0.2,
    )


def current_low_iqb() -> MetricSnapshot:
    return snap(inicio="2024-04", fim="2024-06", iqb=40.0, eventos=90.0, dias_perdidos=180.0)


def current_estimated_hours() -> MetricSnapshot:
    return snap(
        inicio="2024-04",
        fim="2024-06",
        horas_perdidas_registradas=100.0,
        horas_perdidas_estimadas=900.0,
        eventos=90.0,
        dias_perdidos=180.0,
    )


def current_no_headcount() -> MetricSnapshot:
    return snap(
        inicio="2024-04",
        fim="2024-06",
        headcount=None,
        eventos_por_100=None,
        eventos=90.0,
        dias_perdidos=180.0,
    )


def prod_good_coverage() -> BiomedProductivity:
    return BiomedProductivity(
        atendimentos_agendados=100,
        atendimentos_realizados=90,
        faltas=10,
        colaboradores_atendidos=80,
        retornos_realizados=20,
        entrevistas_tecnicas=15,
        acoes_coletivas=2,
        avaliacoes_ergonomicas=3,
        campanhas=1,
        encaminhamentos=5,
        planos_ativos=4,
        planos_concluidos=2,
        necessidade_estimada=100,
    )


def prod_low_coverage() -> BiomedProductivity:
    return BiomedProductivity(
        atendimentos_agendados=50,
        atendimentos_realizados=20,
        colaboradores_atendidos=15,
        necessidade_estimada=100,
    )


def conditionant_delayed() -> Conditionant:
    return Conditionant(
        recomendacao_id="REC-ERG-001",
        decisao="adiada",
        responsavel="empresa",
        status="adiada",
        barreira="orcamento",
        risco_residual="moderado",
        conclusao="ergonomia estrutural nao executada",
    )
