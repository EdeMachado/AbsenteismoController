"""Adapt MetricService (PR #5) aggregates into MetricSnapshot — no formula duplication."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from sqlalchemy import distinct
from sqlalchemy.orm import Session

from backend.models import Upload
from backend.performance.schemas import MetricSnapshot
from backend.performance.window_resolver import count_expected_months, iter_competencias
from backend.services.metric_service import CanonicalMetricsResult, MetricService


_METODOLOGIA_MAP = {
    "registrada": "registradas",
    "estimada": "estimadas",
    "mista": "mista",
    "indisponivel": "indisponivel",
}


@dataclass
class CanonicalSnapshotBundle:
    snapshot: MetricSnapshot
    canonical: dict[str, Any]
    months_with_data: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot": self.snapshot.to_dict(),
            "months_with_data": list(self.months_with_data),
            "limitations": list(self.limitations),
            # canonical without PII — MetricService already aggregates
            "canonical_resumo": {
                "client_id": self.canonical.get("client_id"),
                "periodo": self.canonical.get("periodo"),
                "metricas": self.canonical.get("metricas"),
                "qualidade": self.canonical.get("qualidade"),
                "qualidade_identidade": _identity_public(
                    self.canonical.get("qualidade_identidade") or {}
                ),
                "limitacoes": self.canonical.get("limitacoes"),
            },
        }


def _identity_public(qi: dict[str, Any]) -> dict[str, Any]:
    """Transfer identity quality counts — never keys/names/CPF/matricula values."""
    return {
        "metodo": qi.get("metodo"),
        "por_matricula": qi.get("por_matricula"),
        "por_cpf": qi.get("por_cpf"),
        "somente_por_nome": qi.get("somente_por_nome"),
        "sem_identificador": qi.get("sem_identificador"),
        "confiabilidade": qi.get("confiabilidade"),
    }


def _safe_ratio(num: float | int | None, den: float | int | None) -> float | None:
    if num is None or den is None:
        return None
    if den == 0:
        return None
    return float(num) / float(den)


class CanonicalSnapshotAdapter:
    """Transforms MetricService.compute(...) into MetricSnapshot."""

    def __init__(self, db: Session) -> None:
        if db is None:
            raise ValueError("db é obrigatório")
        self.db = db
        self.metrics = MetricService(db)

    def months_present(
        self,
        client_id: int,
        periodo_inicio: str,
        periodo_fim: str,
    ) -> list[str]:
        rows = (
            self.db.query(distinct(Upload.mes_referencia))
            .filter(Upload.client_id == int(client_id))
            .filter(Upload.mes_referencia >= periodo_inicio)
            .filter(Upload.mes_referencia <= periodo_fim)
            .all()
        )
        expected = set(iter_competencias(periodo_inicio, periodo_fim))
        found = sorted(
            m
            for (m,) in rows
            if isinstance(m, str) and m in expected
        )
        return found

    def build(
        self,
        client_id: int,
        periodo_inicio: str,
        periodo_fim: str,
        *,
        efetivo_trabalhadores: Optional[int] = None,
        iqb: Optional[float] = None,
        suppress_small_groups: bool = True,
    ) -> CanonicalSnapshotBundle:
        result: CanonicalMetricsResult = self.metrics.compute(
            client_id=client_id,
            periodo_inicio=periodo_inicio,
            periodo_fim=periodo_fim,
            efetivo_trabalhadores=efetivo_trabalhadores,
            suppress_small_groups=suppress_small_groups,
        )
        return self.from_canonical(
            result,
            iqb=iqb,
            efetivo_trabalhadores=efetivo_trabalhadores,
        )

    def from_canonical(
        self,
        result: CanonicalMetricsResult,
        *,
        iqb: Optional[float] = None,
        efetivo_trabalhadores: Optional[int] = None,
    ) -> CanonicalSnapshotBundle:
        m = result.metricas
        q = result.qualidade
        lims: list[str] = list(result.limitacoes or [])
        periodo_inicio = result.periodo.inicio
        periodo_fim = result.periodo.fim
        if not periodo_inicio or not periodo_fim:
            lims.append("periodo_canonico_parcial_ou_ausente")
            # MetricService may return None bounds when omitted — require for snapshot
            raise ValueError("periodo_inicio e periodo_fim são obrigatórios no adaptador")

        months = self.months_present(result.client_id, periodo_inicio, periodo_fim)
        expected_n = count_expected_months(periodo_inicio, periodo_fim)
        found_n = len(months)
        completude = (found_n / expected_n) if expected_n else None
        if completude is not None and completude < 1.0:
            lims.append(
                f"completude_janela={completude:.4f} "
                f"({found_n}/{expected_n} competências com upload)"
            )

        eventos = float(m.eventos) if m.eventos is not None else None
        eventos_validos = m.eventos_validos_para_dias
        eventos_invalidos_dias = m.eventos_com_dias_invalidos
        eventos_invalidos_horas = m.eventos_com_horas_invalidas

        cov_reg = _safe_ratio(m.eventos_com_horas_registradas, m.eventos_brutos or None)
        cov_est = _safe_ratio(m.eventos_com_horas_estimadas, m.eventos_brutos or None)

        metodologia = _METODOLOGIA_MAP.get(q.horas, q.horas or "indisponivel")
        if q.horas == "indisponivel":
            lims.append("metodologia_horas_indisponivel_no_canonico")

        headcount = (
            float(efetivo_trabalhadores)
            if efetivo_trabalhadores is not None
            else None
        )
        if headcount is None:
            lims.append(
                "headcount_ausente — taxas populacionais (eventos_por_100, "
                "horas_por_100, frequencia) não avaliadas"
            )

        eventos_por_100 = (
            float(m.eventos_por_100_trabalhadores)
            if m.eventos_por_100_trabalhadores is not None
            else None
        )
        dias_por_trab = (
            float(m.dias_perdidos_por_trabalhador)
            if m.dias_perdidos_por_trabalhador is not None
            else None
        )

        horas_por_100: float | None = None
        if headcount is not None and headcount > 0 and m.horas_perdidas_registradas is not None:
            horas_por_100 = (float(m.horas_perdidas_registradas) / headcount) * 100.0
        elif headcount is None:
            lims.append("horas_por_100_nao_calculada_sem_headcount")

        # Frequency: use rate per 100 workers when available; else None (no silent inference)
        frequencia = eventos_por_100
        if frequencia is None:
            lims.append("frequencia_populacional_indisponivel_sem_denominador")

        # Severity proxy from average duration when available
        gravidade = (
            float(m.duracao_media_dias) if m.duracao_media_dias is not None else None
        )
        if gravidade is None:
            lims.append("gravidade_nao_disponivel_no_contrato_canonico")

        # Fields absent from canonical contract — explicit None + limitation
        recorrencia = None
        lims.append("recorrencia_ausente_no_contrato_canonico")
        afastamentos_longos = None
        lims.append("afastamentos_longos_ausente_no_contrato_canonico")

        setores = _top_labels(result.distribuicao_setor, "setor")
        grupos = _top_labels(result.distribuicao_grupo_alfabetico_cid, "grupo_alfabetico_cid")

        # Transfer invalid event counts into limitations (aggregates only)
        lims.append(
            f"eventos_validos_para_dias={eventos_validos};"
            f"eventos_com_dias_invalidos={eventos_invalidos_dias};"
            f"eventos_com_horas_invalidas={eventos_invalidos_horas};"
            f"eventos_sem_identidade={m.eventos_sem_identidade}"
        )
        qi = result.qualidade_identidade
        lims.append(
            f"qualidade_identidade_confiabilidade={qi.confiabilidade};"
            f"metodo={qi.metodo}"
        )

        snap = MetricSnapshot(
            client_id=int(result.client_id),
            periodo_inicio=periodo_inicio,
            periodo_fim=periodo_fim,
            eventos=eventos,
            trabalhadores_unicos=float(m.trabalhadores_unicos),
            dias_perdidos=float(m.dias_perdidos),
            horas_perdidas_registradas=float(m.horas_perdidas_registradas),
            horas_perdidas_estimadas=float(m.horas_perdidas_estimadas),
            duracao_media=(
                float(m.duracao_media_dias) if m.duracao_media_dias is not None else None
            ),
            frequencia=frequencia,
            gravidade=gravidade,
            recorrencia=recorrencia,
            afastamentos_longos=afastamentos_longos,
            eventos_por_100=eventos_por_100,
            dias_por_trabalhador=dias_por_trab,
            horas_por_100=horas_por_100,
            headcount=headcount,
            iqb=iqb,
            setores_criticos=setores,
            grupos_cid=grupos,
            meses_com_dados=found_n,
            cobertura_horas_registradas=cov_reg,
            cobertura_horas_estimadas=cov_est,
            metodologia_horas=metodologia,
            completude_periodo=completude,
            limitacoes=lims,
            fonte="metric_service_canonical",
        )
        return CanonicalSnapshotBundle(
            snapshot=snap,
            canonical=result.to_dict(),
            months_with_data=months,
            limitations=lims,
        )


def _top_labels(dist: list[dict[str, Any]], key: str, *, n: int = 5) -> list[str]:
    items = []
    for row in dist or []:
        label = row.get(key)
        if not label or label == "GRUPO_SUPRIMIDO":
            continue
        # labels are sector/CID group codes — not personal names
        items.append((float(row.get("dias_perdidos") or 0), str(label)))
    items.sort(key=lambda x: (-x[0], x[1]))
    return [lab for _, lab in items[:n]]


__all__ = [
    "CanonicalSnapshotAdapter",
    "CanonicalSnapshotBundle",
]
