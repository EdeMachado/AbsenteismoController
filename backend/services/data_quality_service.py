"""
Motor de qualidade e normalização em modo shadow (A02-A).

Analisa inconsistências, agrega alertas, propõe normalizações e calcula IQB.
Nunca altera dados originais. Nunca escreve no banco. Nunca expõe PII.
Independente de HTTP.
"""
from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from sqlalchemy.orm import Session

from backend.models import Atestado, Upload
from backend.services.metric_service import (
    _MES_REF_RE,
    _norm_text,
    cid_letra_inicial,
    validate_period_range,
    worker_identity_parts,
)
from backend.services.shadow_compare import assert_no_pii_in_payload


# ---------------------------------------------------------------------------
# Pesos IQB (configuráveis; devem somar 100)
# ---------------------------------------------------------------------------

DEFAULT_IQB_WEIGHTS: Dict[str, float] = {
    "completude": 25.0,
    "consistencia": 20.0,
    "padronizacao": 20.0,
    "identidade": 20.0,
    "rastreabilidade": 10.0,
    "atualidade": 5.0,
}

IQB_CLASSIFICACAO = (
    (90.0, "excelente"),
    (80.0, "boa"),
    (65.0, "regular"),
    (50.0, "baixa"),
    (0.0, "critica"),
)

_CID_FORMAT_RE = re.compile(r"^[A-Za-z]\d{2}(\.\d{1,2})?$")
_DEFAULT_DURACAO_EXCEPCIONAL_DIAS = 30.0
_HORAS_DIVERGENCIA_TOLERANCIA = 0.5  # horas


def _safe_float(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
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


def normalize_sector_key(raw: Optional[str]) -> Optional[str]:
    """
    Chave de comparação (memória): NFKC + trim + espaços compactados + upper.
    Não faz fuzzy merge semântico.
    """
    if raw is None:
        return None
    text = unicodedata.normalize("NFKC", str(raw)).strip()
    if not text:
        return None
    text = re.sub(r"\s+", " ", text)
    return text.upper()


def propose_sector_label(raw: Optional[str]) -> Optional[str]:
    """Rótulo de apresentação proposto (Title Case após normalização visual)."""
    if raw is None:
        return None
    text = unicodedata.normalize("NFKC", str(raw)).strip()
    if not text:
        return None
    text = re.sub(r"\s+", " ", text)
    # Preserva conteúdo entre parênteses; Title Case nas palavras
    parts = []
    for token in text.split(" "):
        if not token:
            continue
        if token.startswith("(") and len(token) > 1:
            inner = token[1:]
            if inner.endswith(")"):
                parts.append("(" + inner[:-1].capitalize() + ")")
            else:
                parts.append("(" + inner.capitalize())
        elif token.endswith(")") and len(token) > 1:
            parts.append(token[:-1].capitalize() + ")")
        else:
            parts.append(token.capitalize())
    return " ".join(parts) if parts else None


def classify_iqb(score: float) -> str:
    for threshold, label in IQB_CLASSIFICACAO:
        if score >= threshold:
            return label
    return "critica"


def identity_risk(
    por_matricula: int,
    por_cpf: int,
    somente_por_nome: int,
    sem_identificador: int,
) -> str:
    total = por_matricula + por_cpf + somente_por_nome + sem_identificador
    if total == 0:
        return "critico"
    frac_mat = por_matricula / total
    frac_fraca = (somente_por_nome + sem_identificador) / total
    if frac_mat >= 0.8 and frac_fraca <= 0.1:
        return "baixo"
    if frac_fraca >= 0.5 or por_matricula == 0:
        return "critico" if frac_fraca >= 0.7 else "alto"
    if frac_mat >= 0.5:
        return "moderado"
    return "alto"


@dataclass
class IQBWeights:
    completude: float = 25.0
    consistencia: float = 20.0
    padronizacao: float = 20.0
    identidade: float = 20.0
    rastreabilidade: float = 10.0
    atualidade: float = 5.0

    def as_dict(self) -> Dict[str, float]:
        return asdict(self)

    def validate(self) -> None:
        total = sum(self.as_dict().values())
        if abs(total - 100.0) > 1e-6:
            raise ValueError(f"pesos IQB devem somar 100; obtido={total}")
        for name, value in self.as_dict().items():
            if value < 0:
                raise ValueError(f"peso {name} não pode ser negativo")


@dataclass
class DataQualityResult:
    client_id: int
    periodo: Dict[str, Optional[str]]
    iqb: float
    classificacao: str
    dimensoes: Dict[str, float]
    pesos: Dict[str, float]
    completude: Dict[str, Any]
    padronizacao_setor: Dict[str, Any]
    centro_custo: Dict[str, Any]
    identidade: Dict[str, Any]
    horas: Dict[str, Any]
    dias_datas: Dict[str, Any]
    cid: Dict[str, Any]
    rastreabilidade: Dict[str, Any]
    atualidade: Dict[str, Any]
    sugestoes: List[Dict[str, Any]]
    alertas: List[Dict[str, Any]]
    limitacoes: List[str]
    estrategia_identidade_futura: List[str]
    eventos_analisados: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DataQualityService:
    """Análise de qualidade em modo shadow — somente leitura."""

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
            raise ValueError("client_id deve ser > 0 (sem fallback)")
        return cid

    def _load_rows(
        self,
        client_id: int,
        periodo_inicio: Optional[str],
        periodo_fim: Optional[str],
    ) -> Tuple[List[Atestado], List[Upload]]:
        q = (
            self.db.query(Atestado)
            .join(Upload)
            .filter(Upload.client_id == client_id)
        )
        if periodo_inicio is not None or periodo_fim is not None:
            q = q.filter(Upload.mes_referencia.isnot(None))
            q = q.filter(Upload.mes_referencia != "")
        if periodo_inicio is not None:
            q = q.filter(Upload.mes_referencia >= periodo_inicio)
        if periodo_fim is not None:
            q = q.filter(Upload.mes_referencia <= periodo_fim)

        rows = q.all()
        if periodo_inicio is not None or periodo_fim is not None:
            filtered: List[Atestado] = []
            for row in rows:
                mes = row.upload.mes_referencia if row.upload else None
                if mes is None or not _MES_REF_RE.fullmatch(str(mes).strip()):
                    continue
                if periodo_inicio is not None and mes < periodo_inicio:
                    continue
                if periodo_fim is not None and mes > periodo_fim:
                    continue
                filtered.append(row)
            rows = filtered

        upload_ids = {r.upload_id for r in rows}
        uploads = []
        if upload_ids:
            uploads = (
                self.db.query(Upload)
                .filter(Upload.client_id == client_id, Upload.id.in_(upload_ids))
                .all()
            )
        return rows, uploads

    def analyze(
        self,
        client_id: int,
        periodo_inicio: Optional[str] = None,
        periodo_fim: Optional[str] = None,
        *,
        weights: Optional[IQBWeights] = None,
        duracao_excepcional_dias: float = _DEFAULT_DURACAO_EXCEPCIONAL_DIAS,
        suppress_cid_groups_below: int = 5,
        reference_date: Optional[date] = None,
    ) -> DataQualityResult:
        """
        Analisa qualidade do escopo. Não muta self.db nem persiste alterações.
        """
        session_ref = self.db
        cid = self._validate_client_id(client_id)
        periodo_inicio, periodo_fim = validate_period_range(periodo_inicio, periodo_fim)
        w = weights or IQBWeights(**DEFAULT_IQB_WEIGHTS)
        w.validate()

        rows, uploads = self._load_rows(cid, periodo_inicio, periodo_fim)
        n = len(rows)
        ref_day = reference_date or date.today()

        # --- contadores ---
        sem_setor = 0
        sem_cc = 0
        sem_cid = 0
        sem_jornada = 0
        sem_dias = 0
        sem_horas_reg = 0
        sem_data = 0
        sem_periodo = 0
        sem_ident = 0
        sem_upload = 0
        # cliente sempre filtrado; contar órfãos se upload.client_id divergir (não deve)
        sem_cliente = 0

        dias_neg = 0
        dias_nulos = 0
        dias_zero = 0
        duracao_exc = 0
        data_fim_antes = 0
        data_futura = 0
        periodo_incompativel = 0
        # sobreposição potencial: mesmo trabalhador-chave + intervalos sobrepostos (agregado)
        overlap_pairs = 0

        horas_reg = 0
        horas_est = 0
        horas_sem = 0
        jornada_ausente = 0
        jornada_invalida = 0
        divergencia_horas = 0

        por_mat = 0
        por_cpf = 0
        por_nome = 0
        por_nenhum = 0

        cid_preenchido = 0
        cid_formato_ok = 0
        cid_mal = 0
        cid_grupos: Dict[str, Set[str]] = {}

        # setor variantes: chave -> {originais_count via set of raw forms, eventos, proposed}
        setor_map: Dict[str, Dict[str, Any]] = {}
        cc_values: Set[str] = set()
        cc_preenchido = 0

        worker_intervals: Dict[str, List[Tuple[date, date]]] = {}

        for row in rows:
            upload = row.upload
            mes = upload.mes_referencia if upload else None

            if not upload or not row.upload_id:
                sem_upload += 1
            if upload is not None and upload.client_id != cid:
                sem_cliente += 1
            if not mes or not str(mes).strip():
                sem_periodo += 1

            setor_raw = row.setor
            key = normalize_sector_key(setor_raw)
            if key is None:
                sem_setor += 1
            else:
                bucket = setor_map.setdefault(
                    key,
                    {
                        "variantes": set(),
                        "eventos": 0,
                        "rotulo_proposto": propose_sector_label(setor_raw),
                    },
                )
                bucket["variantes"].add(str(setor_raw).strip())
                bucket["eventos"] += 1

            cc = _norm_text(row.centro_custo)
            if cc is None:
                sem_cc += 1
            else:
                cc_preenchido += 1
                cc_values.add(cc)

            cid_raw = _norm_text(row.cid)
            if cid_raw is None:
                sem_cid += 1
            else:
                cid_preenchido += 1
                if _CID_FORMAT_RE.fullmatch(cid_raw):
                    cid_formato_ok += 1
                else:
                    cid_mal += 1

            kind, wkey = worker_identity_parts(row)
            if kind == "matricula":
                por_mat += 1
            elif kind == "cpf":
                por_cpf += 1
            elif kind == "nome":
                por_nome += 1
            else:
                por_nenhum += 1
                sem_ident += 1

            letra = cid_letra_inicial(row.cid)
            if wkey:
                cid_grupos.setdefault(letra, set()).add(wkey)

            dias = _safe_float(row.dias_atestados)
            if dias is None:
                dias_nulos += 1
                sem_dias += 1
            elif dias < 0:
                dias_neg += 1
            elif dias == 0:
                dias_zero += 1
            elif dias > duracao_excepcional_dias:
                duracao_exc += 1

            horas = _safe_float(row.horas_perdi)
            jornada = _safe_float(row.horas_dia)
            if jornada is None or jornada == 0:
                jornada_ausente += 1
                sem_jornada += 1
            elif jornada < 0:
                jornada_invalida += 1
                jornada_ausente += 0  # já inválida
                sem_jornada += 1

            if horas is not None and horas > 0:
                horas_reg += 1
                if (
                    dias is not None
                    and dias > 0
                    and jornada is not None
                    and jornada > 0
                ):
                    esperado = dias * jornada
                    if abs(esperado - horas) > _HORAS_DIVERGENCIA_TOLERANCIA:
                        divergencia_horas += 1
            else:
                sem_horas_reg += 1
                if (
                    dias is not None
                    and dias > 0
                    and jornada is not None
                    and jornada > 0
                ):
                    horas_est += 1
                else:
                    horas_sem += 1

            d0 = row.data_afastamento
            d1 = row.data_retorno
            if d0 is None and d1 is None:
                sem_data += 1
            if d0 is not None and d1 is not None and d1 < d0:
                data_fim_antes += 1
            if d0 is not None and d0 > ref_day:
                data_futura += 1
            if d0 is not None and mes and _MES_REF_RE.fullmatch(str(mes).strip()):
                event_ym = f"{d0.year:04d}-{d0.month:02d}"
                # incompatível se mês do evento distar > 1 mês do mes_referencia
                if abs((d0.year * 12 + d0.month) - (
                    int(mes[:4]) * 12 + int(mes[5:7])
                )) > 1:
                    periodo_incompativel += 1

            if wkey and d0 is not None:
                end = d1 if d1 is not None else d0
                if end >= d0:
                    intervals = worker_intervals.setdefault(wkey, [])
                    for a, b in intervals:
                        if d0 <= b and end >= a:
                            overlap_pairs += 1
                            break
                    intervals.append((d0, end))

        # --- agregados ---
        def pct(part: int, whole: int = n) -> float:
            if whole <= 0:
                return 0.0
            return round(100.0 * part / whole, 4)

        completude = {
            "eventos": n,
            "sem_setor": {"count": sem_setor, "pct": pct(sem_setor)},
            "sem_centro_custo": {"count": sem_cc, "pct": pct(sem_cc)},
            "sem_cid": {"count": sem_cid, "pct": pct(sem_cid)},
            "sem_jornada": {"count": sem_jornada, "pct": pct(sem_jornada)},
            "sem_dias": {"count": sem_dias, "pct": pct(sem_dias)},
            "sem_horas_registradas": {"count": sem_horas_reg, "pct": pct(sem_horas_reg)},
            "sem_data": {"count": sem_data, "pct": pct(sem_data)},
            "sem_periodo_referencia": {"count": sem_periodo, "pct": pct(sem_periodo)},
            "sem_identificador_util": {"count": sem_ident, "pct": pct(sem_ident)},
            "sem_vinculo_upload": {"count": sem_upload, "pct": pct(sem_upload)},
            "sem_vinculo_cliente": {"count": sem_cliente, "pct": pct(sem_cliente)},
        }

        setores_variantes = []
        for key, data in setor_map.items():
            n_var = len(data["variantes"])
            if n_var > 1:
                setores_variantes.append(
                    {
                        "chave_normalizada": key,
                        "rotulo_proposto": data["rotulo_proposto"],
                        "quantidade_variantes": n_var,
                        "eventos": int(data["eventos"]),
                    }
                )
        setores_variantes.sort(key=lambda x: (-x["eventos"], x["chave_normalizada"]))

        padronizacao_setor = {
            "chaves_distintas": len(setor_map),
            "setores_com_variantes": len(setores_variantes),
            "setores_variantes": setores_variantes,
            "nota": (
                "Normalização apenas em memória; sem fuzzy merge semântico "
                "(ex.: Pintura ≠ Pintura (Líder))."
            ),
        }

        cobertura_cc = pct(cc_preenchido)
        if n == 0:
            cc_status = "indisponivel"
        elif cc_preenchido == 0:
            cc_status = "indisponivel"
        else:
            cc_status = "disponivel"
        # Variações de forma do CC (mesma lógica de chave)
        cc_form_map: Dict[str, Set[str]] = {}
        for row in rows:
            raw = row.centro_custo
            k = normalize_sector_key(raw)
            if k:
                cc_form_map.setdefault(k, set()).add(str(raw).strip())
        cc_variantes_forma = sum(1 for s in cc_form_map.values() if len(s) > 1)

        centro_custo = {
            "status": cc_status,
            "preenchido": cc_preenchido,
            "ausente": sem_cc,
            "cobertura_pct": cobertura_cc if cc_status != "indisponivel" or n == 0 else 0.0,
            "valores_distintos": len(cc_values) if cc_status == "disponivel" else 0,
            "variacoes_apenas_forma": cc_variantes_forma if cc_status == "disponivel" else 0,
            "nota": (
                "Não se inventa centro de custo a partir do setor. "
                "100% ausente ⇒ dimensão indisponível (não equivale a SEM_CENTRO_CUSTO válido)."
            ),
        }

        risco = identity_risk(por_mat, por_cpf, por_nome, por_nenhum)
        identidade = {
            "metodo": "aproximado",
            "por_matricula": por_mat,
            "por_cpf": por_cpf,
            "somente_por_nome": por_nome,
            "sem_identificador": por_nenhum,
            "risco": risco,
            "nota": "Valores de identidade nunca são expostos.",
        }

        if n == 0:
            horas_class = "insuficiente"
        elif horas_reg == n:
            horas_class = "cobertura_completa"
        elif horas_reg > 0 and (horas_est > 0 or horas_sem > 0):
            horas_class = "parcial"
        elif horas_reg == 0 and horas_est > 0:
            horas_class = "estimada"
        else:
            horas_class = "insuficiente"

        horas = {
            "eventos_com_horas_registradas": horas_reg,
            "eventos_com_horas_estimaveis": horas_est,
            "eventos_sem_possibilidade_estimativa": horas_sem,
            "cobertura_registrada_pct": pct(horas_reg),
            "jornada_ausente": jornada_ausente,
            "jornada_invalida": jornada_invalida,
            "divergencia_dias_jornada_vs_registradas": divergencia_horas,
            "classificacao": horas_class,
            "nota": "Horas registradas e estimadas não são misturadas nem substituídas.",
        }

        dias_datas = {
            "dias_negativos": dias_neg,
            "dias_nulos": dias_nulos,
            "dias_zero": dias_zero,
            "duracao_excepcional": {
                "count": duracao_exc,
                "limiar_dias": duracao_excepcional_dias,
                "nota": "Sinalização apenas; não afirma erro médico ou fraude.",
            },
            "data_final_anterior_inicial": data_fim_antes,
            "data_futura": data_futura,
            "periodo_incompativel_com_data": periodo_incompativel,
            "sobreposicao_potencial_intervalos": overlap_pairs,
        }

        # CID gerencial com supressão
        cid_dist = []
        cid_suprimidos = 0
        cid_sup_eventos_proxy = 0
        for letra, workers in cid_grupos.items():
            n_w = len(workers)
            if 0 < n_w < suppress_cid_groups_below:
                cid_suprimidos += 1
                cid_sup_eventos_proxy += n_w
                continue
            cid_dist.append(
                {
                    "grupo_alfabetico_cid": letra,
                    "trabalhadores_unicos": n_w,
                }
            )
        if cid_suprimidos:
            cid_dist.append(
                {
                    "grupo_alfabetico_cid": "GRUPO_SUPRIMIDO",
                    "trabalhadores_unicos": cid_sup_eventos_proxy,
                    "grupos_suprimidos": cid_suprimidos,
                }
            )
        cid_dist.sort(
            key=lambda x: (
                x["grupo_alfabetico_cid"] == "GRUPO_SUPRIMIDO",
                -x["trabalhadores_unicos"],
                x["grupo_alfabetico_cid"],
            )
        )

        cid_info = {
            "preenchimento_pct": pct(cid_preenchido),
            "formato_valido": cid_formato_ok,
            "mal_formatados": cid_mal,
            "ausentes": sem_cid,
            "distribuicao_grupo_alfabetico": cid_dist,
            "nota": (
                "Não valida diagnóstico clínico. Sem CID individual. "
                "Grupos com <5 trabalhadores vão para GRUPO_SUPRIMIDO."
            ),
        }

        # Rastreabilidade
        uploads_por_mes: Dict[str, int] = {}
        eventos_por_upload: Dict[int, int] = {}
        for row in rows:
            eventos_por_upload[row.upload_id] = eventos_por_upload.get(row.upload_id, 0) + 1
        for up in uploads:
            mes = up.mes_referencia or ""
            uploads_por_mes[mes] = uploads_por_mes.get(mes, 0) + 1

        competencias_multi = sum(1 for c in uploads_por_mes.values() if c > 1)
        uploads_sem_periodo = sum(
            1 for up in uploads if not up.mes_referencia or not str(up.mes_referencia).strip()
        )
        uploads_sem_cliente = sum(1 for up in uploads if not up.client_id)
        # hash de arquivo: schema atual não possui campo — indisponível
        hash_disponivel = False
        nome_original_ok = sum(1 for up in uploads if _norm_text(up.filename))
        data_proc_ok = sum(1 for up in uploads if up.data_upload is not None)

        rastreabilidade = {
            "uploads_no_escopo": len(uploads),
            "eventos_por_upload": {
                "min": min(eventos_por_upload.values()) if eventos_por_upload else 0,
                "max": max(eventos_por_upload.values()) if eventos_por_upload else 0,
                "uploads": len(eventos_por_upload),
            },
            "uploads_por_competencia": {
                "competencias": len(uploads_por_mes),
                "competencias_com_mais_de_um_upload": competencias_multi,
            },
            "uploads_sem_periodo": uploads_sem_periodo,
            "uploads_sem_cliente": uploads_sem_cliente,
            "possiveis_reuploads_mesma_competencia": competencias_multi,
            "hash_arquivo_disponivel": hash_disponivel,
            "nome_original_disponivel_pct": (
                round(100.0 * nome_original_ok / len(uploads), 4) if uploads else 0.0
            ),
            "data_processamento_disponivel_pct": (
                round(100.0 * data_proc_ok / len(uploads), 4) if uploads else 0.0
            ),
            "nota": "Sem deduplicação nem exclusão de reuploads neste lote.",
        }

        # Atualidade: baseado na data_upload mais recente vs reference_date
        if uploads:
            latest = max(
                (up.data_upload for up in uploads if up.data_upload),
                default=None,
            )
            if latest is None:
                atualidade_score = 0.0
                lag_dias = None
            else:
                lag_dias = (ref_day - latest.date()).days
                if lag_dias <= 30:
                    atualidade_score = 100.0
                elif lag_dias <= 90:
                    atualidade_score = 80.0
                elif lag_dias <= 180:
                    atualidade_score = 60.0
                else:
                    atualidade_score = 30.0
        else:
            atualidade_score = 0.0
            lag_dias = None

        atualidade = {
            "score": atualidade_score,
            "lag_dias_ultimo_upload": lag_dias,
            "referencia": ref_day.isoformat(),
        }

        # --- scores dimensionais 0–100 ---
        if n == 0:
            scores = {
                "completude": 0.0,
                "consistencia": 0.0,
                "padronizacao": 0.0,
                "identidade": 0.0,
                "rastreabilidade": 0.0,
                "atualidade": 0.0,
            }
        else:
            # Completude: média de campos críticos presentes
            campos = [
                1 - sem_setor / n,
                1 - sem_dias / n,
                1 - sem_ident / n,
                1 - sem_upload / n,
                1 - sem_periodo / n,
                1 - sem_jornada / n,
                1 - (horas_sem / n),  # tem registrada ou estimável
                1 - sem_data / n,
            ]
            # CC: se indisponível, não conta como falha de preenchimento inventado
            if cc_status == "disponivel":
                campos.append(cc_preenchido / n)
            if cid_preenchido:
                campos.append(cid_preenchido / n)
            scores_completude = 100.0 * (sum(campos) / len(campos))

            inconsistencias = (
                dias_neg
                + data_fim_antes
                + data_futura
                + jornada_invalida
                + divergencia_horas
                + periodo_incompativel
            )
            # penaliza até 100%
            scores_cons = max(0.0, 100.0 - 100.0 * inconsistencias / max(n, 1))

            # Padronização: quanto menos variantes de forma, melhor
            if not setor_map:
                scores_pad = 50.0
            else:
                eventos_variante = sum(s["eventos"] for s in setores_variantes)
                scores_pad = max(0.0, 100.0 - 100.0 * eventos_variante / n)

            # Identidade
            scores_id = 100.0 * (
                1.0 * por_mat + 0.6 * por_cpf + 0.25 * por_nome + 0.0 * por_nenhum
            ) / n

            # Rastreabilidade
            reup_pen = min(40.0, 15.0 * competencias_multi)
            hash_pen = 20.0 if not hash_disponivel else 0.0
            nome_score = (nome_original_ok / len(uploads) * 40.0) if uploads else 0.0
            data_score = (data_proc_ok / len(uploads) * 40.0) if uploads else 0.0
            scores_rast = max(0.0, nome_score + data_score - reup_pen - hash_pen + (20.0 if hash_disponivel else 0.0))
            # Se hash indisponível por schema, limita teto e documenta
            if not hash_disponivel:
                scores_rast = min(scores_rast, 80.0)

            scores = {
                "completude": round(scores_completude, 4),
                "consistencia": round(scores_cons, 4),
                "padronizacao": round(scores_pad, 4),
                "identidade": round(scores_id, 4),
                "rastreabilidade": round(scores_rast, 4),
                "atualidade": round(atualidade_score, 4),
            }

        wd = w.as_dict()
        iqb = round(
            sum(scores[k] * (wd[k] / 100.0) for k in scores),
            4,
        )
        classificacao = classify_iqb(iqb)

        sugestoes: List[Dict[str, Any]] = []
        for item in setores_variantes:
            sugestoes.append(
                {
                    "tipo": "SETOR_VARIANTE",
                    "prioridade": "media" if item["eventos"] < 50 else "alta",
                    "impacto_eventos": item["eventos"],
                    "acao": "Padronizar rótulos futuros no upload",
                    "aplicacao_automatica": False,
                }
            )
        if competencias_multi:
            sugestoes.append(
                {
                    "tipo": "REUPLOAD_COMPETENCIA",
                    "prioridade": "alta",
                    "impacto_eventos": n,
                    "acao": "Revisar política de reupload por competência (lote futuro)",
                    "aplicacao_automatica": False,
                }
            )
        if cc_status == "indisponivel" and n > 0:
            sugestoes.append(
                {
                    "tipo": "CENTRO_CUSTO_AUSENTE",
                    "prioridade": "media",
                    "impacto_eventos": n,
                    "acao": "Incluir centro de custo no layout de upload quando disponível",
                    "aplicacao_automatica": False,
                }
            )
        if por_nome + por_nenhum > por_mat:
            sugestoes.append(
                {
                    "tipo": "IDENTIDADE_FRAGIL",
                    "prioridade": "alta",
                    "impacto_eventos": por_nome + por_nenhum,
                    "acao": "Adotar matrícula como chave preferencial em uploads futuros",
                    "aplicacao_automatica": False,
                }
            )

        alertas: List[Dict[str, Any]] = []
        if dias_neg:
            alertas.append({"tipo": "DIAS_NEGATIVOS", "count": dias_neg})
        if data_fim_antes:
            alertas.append({"tipo": "DATA_FINAL_ANTERIOR", "count": data_fim_antes})
        if data_futura:
            alertas.append({"tipo": "DATA_FUTURA", "count": data_futura})
        if cid_mal:
            alertas.append({"tipo": "CID_MAL_FORMATADO", "count": cid_mal})
        if divergencia_horas:
            alertas.append(
                {"tipo": "DIVERGENCIA_HORAS", "count": divergencia_horas}
            )
        if competencias_multi:
            alertas.append(
                {
                    "tipo": "MULTIPLOS_UPLOADS_COMPETENCIA",
                    "count": competencias_multi,
                }
            )

        limitacoes = [
            "Análise shadow: nenhuma correção persistente aplicada.",
            "Normalização de setor apenas em memória; sem dicionário persistente.",
            "Hash de arquivo indisponível no schema atual de Upload.",
            "Identidade aproximada reutilizada do A01; sem fuzzy matching.",
            "Sobreposição de intervalos é heurística agregada, não prova clínica.",
            "IQB é indicador composto; pesos configuráveis (default soma 100).",
        ]

        estrategia = [
            "Matrícula como chave preferencial operacional.",
            "CPF somente em camada médica restrita e protegida.",
            "Identificador pseudonimizado para analytics.",
            "Nome apenas como fallback legado.",
        ]

        result = DataQualityResult(
            client_id=cid,
            periodo={"inicio": periodo_inicio, "fim": periodo_fim},
            iqb=iqb,
            classificacao=classificacao,
            dimensoes=scores,
            pesos=wd,
            completude=completude,
            padronizacao_setor=padronizacao_setor,
            centro_custo=centro_custo,
            identidade=identidade,
            horas=horas,
            dias_datas=dias_datas,
            cid=cid_info,
            rastreabilidade=rastreabilidade,
            atualidade=atualidade,
            sugestoes=sugestoes,
            alertas=alertas,
            limitacoes=limitacoes,
            estrategia_identidade_futura=estrategia,
            eventos_analisados=n,
        )

        # Garantir sessão intacta
        if self.db is not session_ref:
            raise RuntimeError("sessão foi mutada indevidamente")

        payload = result.to_dict()
        assert_no_pii_in_payload(payload)
        return result


def analyze_data_quality(
    db: Session,
    client_id: int,
    periodo_inicio: Optional[str] = None,
    periodo_fim: Optional[str] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Atalho funcional retornando dict serializável."""
    return DataQualityService(db).analyze(
        client_id=client_id,
        periodo_inicio=periodo_inicio,
        periodo_fim=periodo_fim,
        **kwargs,
    ).to_dict()
