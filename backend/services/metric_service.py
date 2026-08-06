"""
Serviço canônico de métricas (A01-A) — modo conferência / shadow.

Não substitui analytics.py nem as telas. Independente de HTTP.
Não usa fallback client_id=1. Não expõe PII.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session, Query
from sqlalchemy import func, or_

from ..models import Atestado, Upload


# ---------------------------------------------------------------------------
# Identidade de trabalhador (somente uso interno; nunca na saída)
# ---------------------------------------------------------------------------

WORKER_IDENTITY_METHOD = (
    "melhor_chave_disponivel: matricula (trim) se presente; "
    "senão cpf (trim) se presente; "
    "senão nomecompleto normalizado (upper/strip). "
    "Limitação: sem cadastro estável; nome fragmenta identidade."
)


def _norm_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text


def worker_identity_key(atestado: Atestado) -> Optional[str]:
    """
    Melhor chave atualmente disponível para contar trabalhadores únicos.
    Não altera banco; não cria identificador persistente.
    """
    matricula = _norm_text(getattr(atestado, "matricula", None))
    if matricula:
        return f"mat:{matricula.upper()}"

    cpf = _norm_text(getattr(atestado, "cpf", None))
    if cpf:
        digits = "".join(ch for ch in cpf if ch.isdigit())
        if digits:
            return f"cpf:{digits}"

    nome = _norm_text(getattr(atestado, "nomecompleto", None)) or _norm_text(
        getattr(atestado, "nome_funcionario", None)
    )
    if nome:
        return f"nome:{nome.upper()}"
    return None


def cid_chapter(cid: Optional[str]) -> str:
    """Grupo/capítulo CID gerencial (letra inicial A–Z). Sem PII."""
    raw = _norm_text(cid)
    if not raw:
        return "SEM_CID"
    letter = raw[0].upper()
    if "A" <= letter <= "Z":
        return letter
    return "OUTROS"


def _safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _is_valid_non_negative(value: Optional[float]) -> bool:
    return value is not None and value >= 0


# ---------------------------------------------------------------------------
# Contrato de saída
# ---------------------------------------------------------------------------

@dataclass
class PeriodoCanonico:
    inicio: Optional[str]
    fim: Optional[str]


@dataclass
class MetricasCanonicas:
    eventos: int = 0
    trabalhadores_unicos: int = 0
    dias_perdidos: float = 0.0
    horas_perdidas_registradas: float = 0.0
    horas_perdidas_estimadas: float = 0.0
    duracao_media_dias: Optional[float] = None
    horas_media_evento: Optional[float] = None
    eventos_por_100_trabalhadores: Optional[float] = None
    dias_perdidos_por_trabalhador: Optional[float] = None


@dataclass
class MetodologiaCanonicas:
    fonte_tenant: str = "Upload.client_id"
    campo_dias: str = "dias_atestados"
    campo_horas: str = "horas_perdi"
    campo_horas_estimativa: str = "dias_atestados * horas_dia (somente se horas_perdi ausente/zero)"
    identidade_trabalhador: str = WORKER_IDENTITY_METHOD
    setor_campo: str = "setor"
    centro_custo_campo: str = "centro_custo"
    cid_agrupamento: str = "capitulo (1ª letra do CID) para visão gerencial"
    observacao_setor_cc: str = (
        "setor e centro_custo são campos distintos; "
        "não são tratados como sinônimos neste serviço "
        "(nota: analytics legado às vezes documenta CC≈setor)."
    )


@dataclass
class QualidadeCanonicas:
    horas: str = "registrada"  # registrada | estimada | mista | indisponivel
    denominador_efetivo: str = "indisponivel"  # valido | incompleto | indisponivel
    notas: List[str] = field(default_factory=list)


@dataclass
class CanonicalMetricsResult:
    client_id: int
    periodo: PeriodoCanonico
    metricas: MetricasCanonicas
    metodologia: MetodologiaCanonicas = field(default_factory=MetodologiaCanonicas)
    qualidade: QualidadeCanonicas = field(default_factory=QualidadeCanonicas)
    distribuicao_setor: List[Dict[str, Any]] = field(default_factory=list)
    distribuicao_centro_custo: List[Dict[str, Any]] = field(default_factory=list)
    distribuicao_cid_grupo: List[Dict[str, Any]] = field(default_factory=list)
    limitacoes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Serviço
# ---------------------------------------------------------------------------

class MetricService:
    """Cálculo canônico de métricas em modo shadow/conferência."""

    def __init__(self, db: Session):
        if db is None:
            raise ValueError("db é obrigatório")
        self.db = db

    def _validate_client_id(self, client_id: Optional[int]) -> int:
        if client_id is None:
            raise ValueError("client_id é obrigatório (sem fallback)")
        try:
            cid = int(client_id)
        except (TypeError, ValueError) as exc:
            raise ValueError("client_id deve ser inteiro") from exc
        if cid <= 0:
            raise ValueError("client_id deve ser > 0 (sem fallback para 1)")
        return cid

    def _base_query(
        self,
        client_id: int,
        periodo_inicio: Optional[str],
        periodo_fim: Optional[str],
        setor: Optional[str] = None,
        centro_custo: Optional[str] = None,
    ) -> Query:
        q = (
            self.db.query(Atestado)
            .join(Upload)
            .filter(Upload.client_id == client_id)
        )
        if periodo_inicio:
            q = q.filter(Upload.mes_referencia >= periodo_inicio)
        if periodo_fim:
            q = q.filter(Upload.mes_referencia <= periodo_fim)
        if setor:
            q = q.filter(Atestado.setor == setor)
        if centro_custo:
            q = q.filter(Atestado.centro_custo == centro_custo)
        return q

    def compute(
        self,
        db: Session,
        client_id: int,
        periodo_inicio: Optional[str],
        periodo_fim: Optional[str],
        setor: Optional[str] = None,
        centro_custo: Optional[str] = None,
        *,
        efetivo_trabalhadores: Optional[int] = None,
        suppress_small_groups: bool = False,
        small_group_threshold: int = 5,
    ) -> CanonicalMetricsResult:
        """
        Calcula métricas canônicas.

        efetivo_trabalhadores: denominador opcional externo (headcount).
        Se ausente, eventos_por_100 fica None e qualidade.denominador_efetivo=indisponivel.
        """
        if db is not None:
            self.db = db
        cid = self._validate_client_id(client_id)

        rows: List[Atestado] = self._base_query(
            cid, periodo_inicio, periodo_fim, setor, centro_custo
        ).all()

        limitacoes: List[str] = [
            "Sem deduplicação: reuploads/linhas duplicadas permanecem visíveis e somam.",
            WORKER_IDENTITY_METHOD,
        ]
        qualidade_notas: List[str] = []

        eventos = 0
        dias_sum = 0.0
        horas_reg_sum = 0.0
        horas_est_sum = 0.0
        dias_valid_for_avg = 0
        dias_valid_sum = 0.0
        horas_reg_events = 0
        worker_keys = set()
        invalid_dias = 0
        invalid_horas = 0
        missing_horas = 0

        setor_map: Dict[str, Dict[str, float]] = {}
        cc_map: Dict[str, Dict[str, float]] = {}
        cid_map: Dict[str, Dict[str, float]] = {}

        for row in rows:
            eventos += 1
            key = worker_identity_key(row)
            if key:
                worker_keys.add(key)

            dias = _safe_float(row.dias_atestados)
            if not _is_valid_non_negative(dias):
                invalid_dias += 1
                dias = 0.0
            else:
                dias_sum += dias
                if dias > 0:
                    dias_valid_for_avg += 1
                    dias_valid_sum += dias

            horas = _safe_float(row.horas_perdi)
            if horas is not None and horas < 0:
                invalid_horas += 1
                horas = 0.0
            if horas is None:
                horas = 0.0

            if horas > 0:
                horas_reg_sum += horas
                horas_reg_events += 1
            else:
                # Estimativa isolada — nunca misturada no campo registrado
                horas_dia = _safe_float(row.horas_dia)
                if dias > 0 and horas_dia is not None and horas_dia > 0:
                    horas_est_sum += dias * horas_dia
                else:
                    missing_horas += 1

            setor_label = _norm_text(row.setor) or "SEM_SETOR"
            bucket = setor_map.setdefault(
                setor_label, {"eventos": 0.0, "dias_perdidos": 0.0, "trabalhadores": set()}
            )
            bucket["eventos"] += 1
            bucket["dias_perdidos"] += dias
            if key:
                bucket["trabalhadores"].add(key)

            cc_label = _norm_text(row.centro_custo) or "SEM_CENTRO_CUSTO"
            ccb = cc_map.setdefault(
                cc_label, {"eventos": 0.0, "dias_perdidos": 0.0, "trabalhadores": set()}
            )
            ccb["eventos"] += 1
            ccb["dias_perdidos"] += dias
            if key:
                ccb["trabalhadores"].add(key)

            cap = cid_chapter(row.cid)
            cb = cid_map.setdefault(
                cap, {"eventos": 0.0, "dias_perdidos": 0.0, "trabalhadores": set()}
            )
            cb["eventos"] += 1
            cb["dias_perdidos"] += dias
            if key:
                cb["trabalhadores"].add(key)

        trabalhadores = len(worker_keys)
        duracao_media = (
            round(dias_valid_sum / dias_valid_for_avg, 4) if dias_valid_for_avg else None
        )
        horas_media = (
            round(horas_reg_sum / horas_reg_events, 4) if horas_reg_events else None
        )

        # Denominador efetivo (headcount) — só se fornecido e válido
        eventos_por_100 = None
        if efetivo_trabalhadores is not None:
            try:
                efetivo = int(efetivo_trabalhadores)
            except (TypeError, ValueError):
                efetivo = 0
            if efetivo > 0:
                eventos_por_100 = round(100.0 * eventos / efetivo, 4)
                denom_status = "valido"
            else:
                denom_status = "incompleto"
                qualidade_notas.append("efetivo_trabalhadores inválido (<=0)")
        else:
            denom_status = "indisponivel"
            qualidade_notas.append(
                "Headcount/efetivo não fornecido; eventos_por_100 indisponível"
            )

        dias_por_trab = (
            round(dias_sum / trabalhadores, 4) if trabalhadores > 0 else None
        )
        if trabalhadores == 0 and eventos > 0:
            qualidade_notas.append(
                "Eventos sem chave de trabalhador utilizável"
            )

        if horas_reg_sum > 0 and horas_est_sum > 0:
            horas_qualidade = "mista"
        elif horas_reg_sum > 0:
            horas_qualidade = "registrada"
        elif horas_est_sum > 0:
            horas_qualidade = "estimada"
        else:
            horas_qualidade = "indisponivel"

        if invalid_dias:
            qualidade_notas.append(f"registros_com_dias_invalidos={invalid_dias}")
        if invalid_horas:
            qualidade_notas.append(f"registros_com_horas_negativas={invalid_horas}")
        if missing_horas:
            qualidade_notas.append(
                f"registros_sem_horas_registradas_ou_estimaveis≈{missing_horas}"
            )

        def _dist(mapa: Dict[str, Dict[str, Any]], label_key: str) -> List[Dict[str, Any]]:
            out = []
            for label, data in mapa.items():
                n_trab = len(data["trabalhadores"])
                if suppress_small_groups and 0 < n_trab < small_group_threshold:
                    continue
                out.append(
                    {
                        label_key: label,
                        "eventos": int(data["eventos"]),
                        "dias_perdidos": round(float(data["dias_perdidos"]), 4),
                        "trabalhadores_unicos": n_trab,
                    }
                )
            out.sort(key=lambda x: (-x["dias_perdidos"], -x["eventos"], x[label_key]))
            return out

        result = CanonicalMetricsResult(
            client_id=cid,
            periodo=PeriodoCanonico(inicio=periodo_inicio, fim=periodo_fim),
            metricas=MetricasCanonicas(
                eventos=eventos,
                trabalhadores_unicos=trabalhadores,
                dias_perdidos=round(dias_sum, 4),
                horas_perdidas_registradas=round(horas_reg_sum, 4),
                horas_perdidas_estimadas=round(horas_est_sum, 4),
                duracao_media_dias=duracao_media,
                horas_media_evento=horas_media,
                eventos_por_100_trabalhadores=eventos_por_100,
                dias_perdidos_por_trabalhador=dias_por_trab,
            ),
            qualidade=QualidadeCanonicas(
                horas=horas_qualidade,
                denominador_efetivo=denom_status,
                notas=qualidade_notas,
            ),
            distribuicao_setor=_dist(setor_map, "setor"),
            distribuicao_centro_custo=_dist(cc_map, "centro_custo"),
            distribuicao_cid_grupo=_dist(cid_map, "cid_grupo"),
            limitacoes=limitacoes,
        )
        return result


def compute_canonical_metrics(
    db: Session,
    client_id: int,
    periodo_inicio: Optional[str] = None,
    periodo_fim: Optional[str] = None,
    **filters: Any,
) -> Dict[str, Any]:
    """Atalho funcional retornando dict serializável."""
    service = MetricService(db)
    return service.compute(
        db,
        client_id,
        periodo_inicio,
        periodo_fim,
        **filters,
    ).to_dict()
