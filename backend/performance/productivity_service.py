"""BioMed productivity vs coverage vs outcome — no automatic causality."""

from __future__ import annotations

from backend.performance.schemas import BiomedProductivity, IndicatorValue, QualityLabel, ThresholdConfig


class ProductivityService:
    def __init__(self, thresholds: ThresholdConfig | None = None) -> None:
        self.thresholds = thresholds or ThresholdConfig()

    def attendance_rate(self, prod: BiomedProductivity) -> IndicatorValue:
        ag = prod.atendimentos_agendados
        if ag <= 0:
            return IndicatorValue(
                id="taxa_comparecimento",
                valor=None,
                unidade="ratio",
                fonte="biomed_productivity",
                metodologia="realizados/agendados",
                qualidade=QualityLabel.INDISPONIVEL.value,
                periodo=None,
                limitacoes=["sem_agendamentos"],
            )
        rate = prod.atendimentos_realizados / float(ag)
        return IndicatorValue(
            id="taxa_comparecimento",
            valor=round(rate, self.thresholds.round_digits),
            unidade="ratio",
            fonte="biomed_productivity",
            metodologia="realizados/agendados; faltas informadas separadamente",
            qualidade=QualityLabel.DISPONIVEL.value,
            periodo=None,
            limitacoes=[],
        )

    def coverage(self, prod: BiomedProductivity) -> IndicatorValue:
        """Coverage = attended / estimated need — not outcome."""
        need = prod.necessidade_estimada
        if need is None or need <= 0:
            return IndicatorValue(
                id="cobertura_assistencial",
                valor=None,
                unidade="ratio",
                fonte="biomed_productivity",
                metodologia="colaboradores_atendidos/necessidade_estimada",
                qualidade=QualityLabel.INDISPONIVEL.value,
                periodo=None,
                limitacoes=["necessidade_estimada_ausente"],
            )
        val = prod.colaboradores_atendidos / float(need)
        return IndicatorValue(
            id="cobertura_assistencial",
            valor=round(val, self.thresholds.round_digits),
            unidade="ratio",
            fonte="biomed_productivity",
            metodologia="colaboradores_atendidos/necessidade_estimada",
            qualidade=QualityLabel.ESTIMADO.value
            if need
            else QualityLabel.DISPONIVEL.value,
            periodo=None,
            limitacoes=["necessidade_estimada_modelo_aproximado"],
        )

    def production_block(self, prod: BiomedProductivity) -> dict:
        """What BioMed executed — production only."""
        return {
            "tipo": "producao",
            "descricao": "Atividades executadas pela BioMed (não implica causalidade)",
            "metricas": prod.to_dict(),
            "taxa_comparecimento": self.attendance_rate(prod).to_dict(),
        }

    def coverage_block(self, prod: BiomedProductivity) -> dict:
        cov = self.coverage(prod)
        return {
            "tipo": "cobertura",
            "descricao": "Proporção da necessidade atendida (estimada)",
            "cobertura_assistencial": cov.to_dict(),
        }

    def separate_layers(
        self, prod: BiomedProductivity, outcome_summary: str
    ) -> dict:
        return {
            "producao": self.production_block(prod),
            "cobertura": self.coverage_block(prod),
            "resultado": {
                "tipo": "resultado",
                "descricao": "Evolução observacional dos indicadores de absenteísmo",
                "resumo": outcome_summary,
                "causalidade_automatica": False,
                "aviso": "Não afirmar causalidade automática entre produção e resultado",
            },
        }
