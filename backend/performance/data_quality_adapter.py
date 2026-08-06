"""Adapt DataQualityService (PR #6) into performance-facing quality payload.

Does not reimplement IQB formulas.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.services.data_quality_service import DataQualityResult, DataQualityService


@dataclass
class QualityBundle:
    client_id: int
    periodo_inicio: str | None
    periodo_fim: str | None
    iqb: float
    classificacao: str
    dimensoes: dict[str, float]
    status_dimensoes: dict[str, str]
    pesos_originais: dict[str, float]
    pesos_efetivos: dict[str, float]
    metodologia_redistribuicao: str
    limitacoes: list[str]
    qualidade_horas: dict[str, Any]
    qualidade_identidade: dict[str, Any]
    periodos_invalidos: dict[str, Any]
    possiveis_multiplos_uploads: list[dict[str, Any]] = field(default_factory=list)
    dimensoes_nao_aplicaveis: list[str] = field(default_factory=list)
    eventos_analisados: int = 0
    raw_summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d


def _identity_public(identidade: dict[str, Any]) -> dict[str, Any]:
    """Aggregated identity quality only — strip any accidental key material."""

    def _counts_only(obj: Any) -> dict[str, Any]:
        if not isinstance(obj, dict):
            return {}
        out: dict[str, Any] = {}
        for k, v in obj.items():
            key = str(k)
            if key.lower() in {"detalhes", "amostras", "chaves", "exemplos"}:
                continue
            if isinstance(v, (int, float, bool)) or v is None:
                out[key] = v
            elif isinstance(v, str) and len(v) < 120:
                out[key] = v
        return out

    src = identidade or {}
    return {
        "metodo": src.get("metodo"),
        "risco": src.get("risco"),
        "nota": src.get("nota"),
        "por_matricula": src.get("por_matricula"),
        "por_cpf": src.get("por_cpf"),
        "somente_por_nome": src.get("somente_por_nome"),
        "sem_identificador": src.get("sem_identificador"),
        "por_evento": _counts_only(src.get("por_evento") or {}),
        "por_trabalhador_aproximado": _counts_only(
            src.get("por_trabalhador_aproximado") or {}
        ),
    }


def _multi_upload_signals(alertas: list[dict[str, Any]], result: DataQualityResult) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for a in alertas or []:
        tipo = str(a.get("tipo") or "").upper()
        if "UPLOAD" in tipo or "DUPLIC" in tipo or "REUPLOAD" in tipo:
            out.append(
                {
                    "tipo": a.get("tipo"),
                    "count": a.get("count"),
                    "periodo": a.get("periodo") or a.get("mes"),
                }
            )
    # rastreabilidade may mention multiple uploads without PII
    rast = result.rastreabilidade or {}
    if rast.get("possivel_multiplo_upload") or rast.get("uploads_por_mes"):
        out.append(
            {
                "tipo": "RASTREABILIDADE_UPLOADS",
                "uploads_por_mes": rast.get("uploads_por_mes"),
                "possivel_multiplo_upload": rast.get("possivel_multiplo_upload"),
            }
        )
    return out


class DataQualityAdapter:
    """Thin wrapper: DataQualityService.analyze → QualityBundle for snapshots."""

    def __init__(self, db: Session) -> None:
        if db is None:
            raise ValueError("db é obrigatório")
        self.db = db
        self.service = DataQualityService(db)

    def build(
        self,
        client_id: int,
        periodo_inicio: Optional[str] = None,
        periodo_fim: Optional[str] = None,
    ) -> QualityBundle:
        result = self.service.analyze(
            client_id=client_id,
            periodo_inicio=periodo_inicio,
            periodo_fim=periodo_fim,
        )
        return self.from_result(result)

    def from_result(self, result: DataQualityResult) -> QualityBundle:
        periodo = result.periodo or {}
        lims = list(result.limitacoes or [])
        lims.append(f"iqb_classificacao={result.classificacao}")
        if result.dimensoes_nao_aplicaveis:
            lims.append(
                "dimensoes_nao_aplicaveis="
                + ",".join(result.dimensoes_nao_aplicaveis)
            )

        return QualityBundle(
            client_id=int(result.client_id),
            periodo_inicio=periodo.get("inicio"),
            periodo_fim=periodo.get("fim"),
            iqb=float(result.iqb),
            classificacao=str(result.classificacao),
            dimensoes=dict(result.dimensoes or {}),
            status_dimensoes=dict(result.status_dimensoes or {}),
            pesos_originais=dict(result.pesos_originais or {}),
            pesos_efetivos=dict(result.pesos_efetivos or {}),
            metodologia_redistribuicao=str(result.metodologia_redistribuicao or ""),
            limitacoes=lims,
            qualidade_horas=dict(result.horas or {}),
            qualidade_identidade=_identity_public(result.identidade or {}),
            periodos_invalidos=dict(result.periodos_invalidos or {}),
            possiveis_multiplos_uploads=_multi_upload_signals(
                result.alertas or [], result
            ),
            dimensoes_nao_aplicaveis=list(result.dimensoes_nao_aplicaveis or []),
            eventos_analisados=int(result.eventos_analisados or 0),
            raw_summary={
                "completude": result.completude,
                "atualidade": result.atualidade,
                "alertas_tipos": [a.get("tipo") for a in (result.alertas or [])],
                "eventos_excluidos_janela": result.eventos_excluidos_janela,
            },
        )


__all__ = ["DataQualityAdapter", "QualityBundle"]
