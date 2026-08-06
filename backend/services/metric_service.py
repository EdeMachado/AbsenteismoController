"""
Serviço canônico de métricas (A01-A) — modo conferência / shadow.

Não substitui analytics.py nem as telas. Independente de HTTP.
Não usa fallback client_id=1. Não expõe PII.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy.orm import Query, Session

from ..models import Atestado, Upload


# ---------------------------------------------------------------------------
# Identidade de trabalhador (somente uso interno; nunca na saída)
# ---------------------------------------------------------------------------

WORKER_IDENTITY_METHOD = (
    "aproximado — melhor chave disponível: matricula (trim) se presente; "
    "senão cpf (dígitos) se presente; senão nomecompleto normalizado. "
    "Não é identidade canônica estável. Sem fuzzy matching neste lote. "
    "Fragmentação possível quando a mesma pessoa aparece com campos distintos "
    "em registros diferentes (ex.: um com matrícula e outro só com nome)."
)

_PERIOD_RE = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")
_MES_REF_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def _norm_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text


def validate_period_month(value: Optional[str], *, field_name: str) -> Optional[str]:
    """
    Valida período YYYY-MM. None/ausente é permitido.
    Não normaliza formatos ambíguos (ex.: 2026-6).
    """
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} deve ser string YYYY-MM ou None")
    text = value.strip()
    if text == "":
        raise ValueError(f"{field_name} vazio é inválido; use None para omitir")
    if not _PERIOD_RE.fullmatch(text):
        raise ValueError(
            f"{field_name} inválido: exige YYYY-MM com mês 01-12 "
            f"(sem normalização de formatos ambíguos); recebido={value!r}"
        )
    return text


def validate_period_range(
    periodo_inicio: Optional[str],
    periodo_fim: Optional[str],
) -> Tuple[Optional[str], Optional[str]]:
    inicio = validate_period_month(periodo_inicio, field_name="periodo_inicio")
    fim = validate_period_month(periodo_fim, field_name="periodo_fim")
    if inicio is not None and fim is not None and inicio > fim:
        raise ValueError(
            f"periodo_inicio ({inicio}) não pode ser posterior a periodo_fim ({fim})"
        )
    return inicio, fim


def worker_identity_key(atestado: Atestado) -> Optional[str]:
    """
    Melhor chave atualmente disponível (aproximada).
    Nunca deve ser exposta na saída serializada.
    """
    kind, key = worker_identity_parts(atestado)
    return key


def worker_identity_parts(atestado: Atestado) -> Tuple[str, Optional[str]]:
    """
    Retorna (metodo, chave_interna).
    metodo: matricula | cpf | nome | nenhum
    """
    matricula = _norm_text(getattr(atestado, "matricula", None))
    if matricula:
        return "matricula", f"mat:{matricula.upper()}"

    cpf = _norm_text(getattr(atestado, "cpf", None))
    if cpf:
        digits = "".join(ch for ch in cpf if ch.isdigit())
        if digits:
            return "cpf", f"cpf:{digits}"

    nome = _norm_text(getattr(atestado, "nomecompleto", None)) or _norm_text(
        getattr(atestado, "nome_funcionario", None)
    )
    if nome:
        return "nome", f"nome:{nome.upper()}"
    return "nenhum", None


def cid_letra_inicial(cid: Optional[str]) -> str:
    """
    Grupo alfabético por letra inicial do CID (A–Z).
    NÃO é capítulo CID oficial da OMS/CID-10.
    """
    raw = _norm_text(cid)
    if not raw:
        return "SEM_CID"
    letter = raw[0].upper()
    if "A" <= letter <= "Z":
        return letter
    return "OUTROS"


# Alias explícito — evita uso do termo "capítulo"
grupo_alfabetico_cid = cid_letra_inicial


def _safe_float(value: Any) -> Optional[float]:
    """Converte número; None/não-numérico → None (inválido/ausente, não zero silencioso)."""
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _is_valid_non_negative(value: Optional[float]) -> bool:
    """Zero é válido; None e negativos não."""
    return value is not None and value >= 0


def _identity_reliability(
    por_matricula: int,
    por_cpf: int,
    somente_por_nome: int,
    sem_identificador: int,
) -> str:
    total = por_matricula + por_cpf + somente_por_nome + sem_identificador
    if total == 0:
        return "baixa"
    frac_mat = por_matricula / total
    frac_fraca = (somente_por_nome + sem_identificador) / total
    if frac_mat >= 0.7 and frac_fraca <= 0.2:
        return "alta"
    if frac_fraca >= 0.5 or por_matricula == 0:
        return "baixa"
    return "media"


# ---------------------------------------------------------------------------
# Contrato de saída
# ---------------------------------------------------------------------------

@dataclass
class PeriodoCanonico:
    inicio: Optional[str]
    fim: Optional[str]


@dataclass
class MetricasCanonicas:
    eventos_brutos: int = 0
    eventos: int = 0  # alias de eventos_brutos (compatibilidade shadow)
    eventos_validos_para_dias: int = 0
    eventos_com_dias_invalidos: int = 0
    eventos_com_horas_invalidas: int = 0
    eventos_sem_identidade: int = 0
    trabalhadores_unicos: int = 0
    dias_perdidos: float = 0.0
    horas_perdidas_registradas: float = 0.0
    horas_perdidas_estimadas: float = 0.0
    duracao_media_dias: Optional[float] = None
    horas_registradas_media_por_evento: Optional[float] = None
    eventos_com_horas_registradas: int = 0
    horas_estimadas_media_por_evento: Optional[float] = None
    eventos_com_horas_estimadas: int = 0
    eventos_sem_horas: int = 0
    eventos_por_100_trabalhadores: Optional[float] = None
    dias_perdidos_por_trabalhador: Optional[float] = None


@dataclass
class MetodologiaCanonicas:
    fonte_tenant: str = "Upload.client_id"
    campo_dias: str = "dias_atestados"
    campo_horas: str = "horas_perdi"
    campo_horas_estimativa: str = (
        "dias_atestados * horas_dia (somente se horas_perdi ausente/zero/inválida)"
    )
    identidade_trabalhador: str = WORKER_IDENTITY_METHOD
    setor_campo: str = "setor"
    centro_custo_campo: str = "centro_custo"
    cid_agrupamento: str = (
        "grupo_alfabetico_cid / cid_letra_inicial (1ª letra A–Z). "
        "NÃO é capítulo CID oficial; agrupamento oficial por capítulo é evolução futura."
    )
    observacao_setor_cc: str = (
        "setor e centro_custo são campos distintos; "
        "não são tratados como sinônimos neste serviço "
        "(nota: analytics legado às vezes documenta CC≈setor)."
    )
    valores_invalidos: str = (
        "dias/horas: nulo ou não-numérico = inválido (não vira 0 silencioso no total "
        "sem contagem); negativo = inválido; zero = válido e contabilizado como zero."
    )


@dataclass
class QualidadeIdentidade:
    metodo: str = "aproximado"
    por_matricula: int = 0
    por_cpf: int = 0
    somente_por_nome: int = 0
    sem_identificador: int = 0
    confiabilidade: str = "baixa"


@dataclass
class QualidadeCanonicas:
    horas: str = "indisponivel"  # registrada | estimada | mista | indisponivel
    denominador_efetivo: str = "indisponivel"  # valido | incompleto | indisponivel
    notas: List[str] = field(default_factory=list)
    grupos_suprimidos_setor: int = 0
    grupos_suprimidos_centro_custo: int = 0
    grupos_suprimidos_cid: int = 0


@dataclass
class CanonicalMetricsResult:
    client_id: int
    periodo: PeriodoCanonico
    metricas: MetricasCanonicas
    metodologia: MetodologiaCanonicas = field(default_factory=MetodologiaCanonicas)
    qualidade: QualidadeCanonicas = field(default_factory=QualidadeCanonicas)
    qualidade_identidade: QualidadeIdentidade = field(default_factory=QualidadeIdentidade)
    distribuicao_setor: List[Dict[str, Any]] = field(default_factory=list)
    distribuicao_centro_custo: List[Dict[str, Any]] = field(default_factory=list)
    distribuicao_grupo_alfabetico_cid: List[Dict[str, Any]] = field(default_factory=list)
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

    def _validate_threshold(self, threshold: int) -> int:
        try:
            value = int(threshold)
        except (TypeError, ValueError) as exc:
            raise ValueError("small_group_threshold deve ser inteiro > 0") from exc
        if value <= 0:
            raise ValueError("small_group_threshold deve ser > 0")
        return value

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
        if periodo_inicio is not None or periodo_fim is not None:
            # Exclui nulos/vazios na SQL; formato inválido é rejeitado no pós-filtro.
            q = q.filter(Upload.mes_referencia.isnot(None))
            q = q.filter(Upload.mes_referencia != "")
        if periodo_inicio is not None:
            q = q.filter(Upload.mes_referencia >= periodo_inicio)
        if periodo_fim is not None:
            q = q.filter(Upload.mes_referencia <= periodo_fim)
        if setor:
            q = q.filter(Atestado.setor == setor)
        if centro_custo:
            q = q.filter(Atestado.centro_custo == centro_custo)
        return q

    @staticmethod
    def _row_mes_valido(mes: Optional[str]) -> bool:
        if mes is None:
            return False
        return bool(_MES_REF_RE.fullmatch(str(mes).strip()))

    def _mes_referencia_of(self, row: Atestado) -> Optional[str]:
        if getattr(row, "upload", None) is not None:
            return row.upload.mes_referencia
        return (
            self.db.query(Upload.mes_referencia)
            .filter(Upload.id == row.upload_id)
            .scalar()
        )

    def compute(
        self,
        client_id: int,
        periodo_inicio: Optional[str] = None,
        periodo_fim: Optional[str] = None,
        setor: Optional[str] = None,
        centro_custo: Optional[str] = None,
        *,
        efetivo_trabalhadores: Optional[int] = None,
        suppress_small_groups: bool = False,
        small_group_threshold: int = 5,
    ) -> CanonicalMetricsResult:
        """
        Calcula métricas canônicas usando self.db (não altera a sessão).

        efetivo_trabalhadores: denominador opcional externo (headcount).
        """
        cid = self._validate_client_id(client_id)
        periodo_inicio, periodo_fim = validate_period_range(periodo_inicio, periodo_fim)
        threshold = self._validate_threshold(small_group_threshold)

        rows_raw: List[Atestado] = self._base_query(
            cid, periodo_inicio, periodo_fim, setor, centro_custo
        ).all()

        # Pós-filtro rigoroso: referência nula/malformada não entra no intervalo.
        if periodo_inicio is not None or periodo_fim is not None:
            rows = []
            for r in rows_raw:
                mes = self._mes_referencia_of(r)
                if not self._row_mes_valido(mes):
                    continue
                if periodo_inicio is not None and mes < periodo_inicio:
                    continue
                if periodo_fim is not None and mes > periodo_fim:
                    continue
                rows.append(r)
        else:
            rows = rows_raw

        limitacoes: List[str] = [
            "Sem deduplicação: reuploads/linhas duplicadas permanecem visíveis e somam.",
            WORKER_IDENTITY_METHOD,
            "grupo_alfabetico_cid não é capítulo CID oficial (evolução futura).",
        ]
        qualidade_notas: List[str] = []

        eventos_brutos = 0
        eventos_validos_para_dias = 0
        eventos_com_dias_invalidos = 0
        eventos_com_horas_invalidas = 0
        eventos_sem_identidade = 0
        dias_sum = 0.0
        horas_reg_sum = 0.0
        horas_est_sum = 0.0
        dias_valid_for_avg = 0
        dias_valid_sum = 0.0
        horas_reg_events = 0
        horas_est_events = 0
        eventos_sem_horas = 0
        worker_keys: Set[str] = set()

        por_matricula = 0
        por_cpf = 0
        somente_por_nome = 0
        sem_identificador = 0

        # Detecção de fragmentação: mesmo nome → múltiplas chaves (sem unificar)
        nome_para_chaves: Dict[str, Set[str]] = {}

        setor_map: Dict[str, Dict[str, Any]] = {}
        cc_map: Dict[str, Dict[str, Any]] = {}
        cid_map: Dict[str, Dict[str, Any]] = {}

        for row in rows:
            eventos_brutos += 1
            kind, key = worker_identity_parts(row)
            if kind == "matricula":
                por_matricula += 1
            elif kind == "cpf":
                por_cpf += 1
            elif kind == "nome":
                somente_por_nome += 1
            else:
                sem_identificador += 1
                eventos_sem_identidade += 1

            if key:
                worker_keys.add(key)

            nome_ref = _norm_text(getattr(row, "nomecompleto", None)) or _norm_text(
                getattr(row, "nome_funcionario", None)
            )
            if nome_ref and key:
                nome_para_chaves.setdefault(nome_ref.upper(), set()).add(key)

            # --- dias ---
            raw_dias = row.dias_atestados
            dias = _safe_float(raw_dias)
            if dias is None or dias < 0:
                # nulo, não-numérico ou negativo → inválido; não entra no total
                eventos_com_dias_invalidos += 1
                dias_contrib = 0.0
            else:
                # zero é válido
                eventos_validos_para_dias += 1
                dias_contrib = dias
                dias_sum += dias
                if dias > 0:
                    dias_valid_for_avg += 1
                    dias_valid_sum += dias

            # --- horas ---
            raw_horas = row.horas_perdi
            horas = _safe_float(raw_horas)
            horas_invalidas = False
            if raw_horas is not None and horas is None:
                # texto não numérico
                horas_invalidas = True
            elif horas is not None and horas < 0:
                horas_invalidas = True

            if horas_invalidas:
                eventos_com_horas_invalidas += 1
                horas = 0.0
            elif horas is None:
                horas = 0.0

            if horas > 0:
                horas_reg_sum += horas
                horas_reg_events += 1
            else:
                horas_dia = _safe_float(row.horas_dia)
                if (
                    not horas_invalidas
                    and dias_contrib > 0
                    and horas_dia is not None
                    and horas_dia > 0
                ):
                    est = dias_contrib * horas_dia
                    horas_est_sum += est
                    horas_est_events += 1
                else:
                    eventos_sem_horas += 1

            setor_label = _norm_text(row.setor) or "SEM_SETOR"
            bucket = setor_map.setdefault(
                setor_label, {"eventos": 0.0, "dias_perdidos": 0.0, "trabalhadores": set()}
            )
            bucket["eventos"] += 1
            bucket["dias_perdidos"] += dias_contrib
            if key:
                bucket["trabalhadores"].add(key)

            cc_label = _norm_text(row.centro_custo) or "SEM_CENTRO_CUSTO"
            ccb = cc_map.setdefault(
                cc_label, {"eventos": 0.0, "dias_perdidos": 0.0, "trabalhadores": set()}
            )
            ccb["eventos"] += 1
            ccb["dias_perdidos"] += dias_contrib
            if key:
                ccb["trabalhadores"].add(key)

            letra = cid_letra_inicial(row.cid)
            cb = cid_map.setdefault(
                letra, {"eventos": 0.0, "dias_perdidos": 0.0, "trabalhadores": set()}
            )
            cb["eventos"] += 1
            cb["dias_perdidos"] += dias_contrib
            if key:
                cb["trabalhadores"].add(key)

        # Fragmentação por nome compartilhado com chaves distintas
        fragmentados = sum(1 for keys in nome_para_chaves.values() if len(keys) > 1)
        if fragmentados:
            limitacoes.append(
                f"Possível fragmentação de identidade: {fragmentados} nome(s) "
                "aparecem sob chaves internas distintas (matrícula/CPF/nome). "
                "Sem unificação fuzzy neste lote — contagem não deduplica."
            )
            qualidade_notas.append(
                f"nomes_com_chaves_distintas={fragmentados}"
            )

        trabalhadores = len(worker_keys)
        duracao_media = (
            round(dias_valid_sum / dias_valid_for_avg, 4) if dias_valid_for_avg else None
        )
        horas_reg_media = (
            round(horas_reg_sum / horas_reg_events, 4) if horas_reg_events else None
        )
        horas_est_media = (
            round(horas_est_sum / horas_est_events, 4) if horas_est_events else None
        )

        eventos_por_100 = None
        if efetivo_trabalhadores is not None:
            try:
                efetivo = int(efetivo_trabalhadores)
            except (TypeError, ValueError):
                efetivo = 0
            if efetivo > 0:
                eventos_por_100 = round(100.0 * eventos_brutos / efetivo, 4)
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

        if horas_reg_sum > 0 and horas_est_sum > 0:
            horas_qualidade = "mista"
        elif horas_reg_sum > 0:
            horas_qualidade = "registrada"
        elif horas_est_sum > 0:
            horas_qualidade = "estimada"
        else:
            horas_qualidade = "indisponivel"

        if eventos_com_dias_invalidos:
            qualidade_notas.append(
                f"eventos_com_dias_invalidos={eventos_com_dias_invalidos}"
            )
        if eventos_com_horas_invalidas:
            qualidade_notas.append(
                f"eventos_com_horas_invalidas={eventos_com_horas_invalidas}"
            )
        if eventos_sem_horas:
            qualidade_notas.append(f"eventos_sem_horas={eventos_sem_horas}")

        def _dist(
            mapa: Dict[str, Dict[str, Any]],
            label_key: str,
        ) -> Tuple[List[Dict[str, Any]], int]:
            out: List[Dict[str, Any]] = []
            suppressed_eventos = 0.0
            suppressed_dias = 0.0
            suppressed_workers: Set[str] = set()
            grupos_suprimidos = 0

            for label, data in mapa.items():
                n_trab = len(data["trabalhadores"])
                if suppress_small_groups and 0 < n_trab < threshold:
                    grupos_suprimidos += 1
                    suppressed_eventos += float(data["eventos"])
                    suppressed_dias += float(data["dias_perdidos"])
                    suppressed_workers |= set(data["trabalhadores"])
                    continue
                out.append(
                    {
                        label_key: label,
                        "eventos": int(data["eventos"]),
                        "dias_perdidos": round(float(data["dias_perdidos"]), 4),
                        "trabalhadores_unicos": n_trab,
                    }
                )

            if grupos_suprimidos:
                out.append(
                    {
                        label_key: "GRUPO_SUPRIMIDO",
                        "eventos": int(suppressed_eventos),
                        "dias_perdidos": round(float(suppressed_dias), 4),
                        "trabalhadores_unicos": len(suppressed_workers),
                        "grupos_suprimidos": grupos_suprimidos,
                    }
                )

            out.sort(
                key=lambda x: (
                    x[label_key] == "GRUPO_SUPRIMIDO",
                    -x["dias_perdidos"],
                    -x["eventos"],
                    x[label_key],
                )
            )
            return out, grupos_suprimidos

        dist_setor, sup_setor = _dist(setor_map, "setor")
        dist_cc, sup_cc = _dist(cc_map, "centro_custo")
        dist_cid, sup_cid = _dist(cid_map, "grupo_alfabetico_cid")

        conf = _identity_reliability(
            por_matricula, por_cpf, somente_por_nome, sem_identificador
        )

        return CanonicalMetricsResult(
            client_id=cid,
            periodo=PeriodoCanonico(inicio=periodo_inicio, fim=periodo_fim),
            metricas=MetricasCanonicas(
                eventos_brutos=eventos_brutos,
                eventos=eventos_brutos,
                eventos_validos_para_dias=eventos_validos_para_dias,
                eventos_com_dias_invalidos=eventos_com_dias_invalidos,
                eventos_com_horas_invalidas=eventos_com_horas_invalidas,
                eventos_sem_identidade=eventos_sem_identidade,
                trabalhadores_unicos=trabalhadores,
                dias_perdidos=round(dias_sum, 4),
                horas_perdidas_registradas=round(horas_reg_sum, 4),
                horas_perdidas_estimadas=round(horas_est_sum, 4),
                duracao_media_dias=duracao_media,
                horas_registradas_media_por_evento=horas_reg_media,
                eventos_com_horas_registradas=horas_reg_events,
                horas_estimadas_media_por_evento=horas_est_media,
                eventos_com_horas_estimadas=horas_est_events,
                eventos_sem_horas=eventos_sem_horas,
                eventos_por_100_trabalhadores=eventos_por_100,
                dias_perdidos_por_trabalhador=dias_por_trab,
            ),
            qualidade=QualidadeCanonicas(
                horas=horas_qualidade,
                denominador_efetivo=denom_status,
                notas=qualidade_notas,
                grupos_suprimidos_setor=sup_setor,
                grupos_suprimidos_centro_custo=sup_cc,
                grupos_suprimidos_cid=sup_cid,
            ),
            qualidade_identidade=QualidadeIdentidade(
                metodo="aproximado",
                por_matricula=por_matricula,
                por_cpf=por_cpf,
                somente_por_nome=somente_por_nome,
                sem_identificador=sem_identificador,
                confiabilidade=conf,
            ),
            distribuicao_setor=dist_setor,
            distribuicao_centro_custo=dist_cc,
            distribuicao_grupo_alfabetico_cid=dist_cid,
            limitacoes=limitacoes,
        )


def compute_canonical_metrics(
    db: Session,
    client_id: int,
    periodo_inicio: Optional[str] = None,
    periodo_fim: Optional[str] = None,
    **filters: Any,
) -> Dict[str, Any]:
    """Atalho funcional: instancia MetricService(db) e chama compute() sem re-passar db."""
    service = MetricService(db)
    return service.compute(
        client_id=client_id,
        periodo_inicio=periodo_inicio,
        periodo_fim=periodo_fim,
        **filters,
    ).to_dict()
