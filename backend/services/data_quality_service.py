"""
Motor de qualidade e normalização em modo shadow (A02-A).

Analisa inconsistências, agrega alertas, propõe normalizações e calcula IQB.
Nunca altera dados originais. Nunca escreve no banco. Nunca expõe PII.
Independente de HTTP.
"""
from __future__ import annotations

import re
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Set, Tuple

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
_HORAS_DIVERGENCIA_TOLERANCIA = 0.5
_ACRONYM_RE = re.compile(r"^[A-Z0-9]{2,6}$")

_MULTIPLOS_UPLOADS_MSG = (
    "A presença de mais de um upload na mesma competência exige revisão, "
    "mas não comprova duplicidade sem hash ou assinatura do conteúdo."
)


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


def _strip_diacritics(text: str) -> str:
    """Remove marcas diacríticas após NFKD (comparação de forma)."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))


def normalize_sector_key(raw: Optional[str]) -> Optional[str]:
    """
    Chave comparável (memória): NFKC→NFKD, trim, espaços, casefold,
    remoção de diacríticos. Não faz fuzzy merge semântico.
    """
    if raw is None:
        return None
    text = unicodedata.normalize("NFKC", str(raw)).strip()
    if not text:
        return None
    text = re.sub(r"\s+", " ", text)
    text = _strip_diacritics(text)
    return text.casefold()


def _is_acronym_token(token: str) -> bool:
    letters = re.sub(r"[^A-Za-z0-9]", "", token)
    return bool(letters) and _ACRONYM_RE.fullmatch(letters.upper()) and letters.upper() == letters


def choose_sector_label(variant_counts: Dict[str, int]) -> Tuple[str, bool]:
    """
    Escolhe variante mais frequente; empate determinístico (lexicográfico).
    Preserva siglas predominantes. Sempre marca necessidade de validação humana.
    """
    if not variant_counts:
        return "", True
    # Ordena por (-freq, rótulo) para determinismo
    ordered = sorted(variant_counts.items(), key=lambda kv: (-kv[1], kv[0]))
    chosen = ordered[0][0]
    # Se a variante escolhida parece title-case forçado sobre sigla, preferir
    # forma all-caps curta se empatada em frequência com outra.
    tokens = chosen.split()
    if any(_is_acronym_token(t) is False and t.isupper() and 2 <= len(t) <= 6 for t in tokens):
        # já all-caps curto — ok
        pass
    # Preferir variante all-caps de sigla pura se for a mais frequente entre siglas
    for cand, _freq in ordered:
        parts = cand.split()
        if len(parts) == 1 and _is_acronym_token(parts[0]):
            # se cand empatado no top freq band
            if variant_counts[cand] == ordered[0][1]:
                chosen = cand
                break
    return chosen, True


def propose_sector_label(raw: Optional[str]) -> Optional[str]:
    """
    Compat: rótulo a partir de um único raw — preserva siglas (RH, TI, PCP).
    Preferir choose_sector_label com contagens quando houver variantes.
    """
    if raw is None:
        return None
    text = unicodedata.normalize("NFKC", str(raw)).strip()
    if not text:
        return None
    text = re.sub(r"\s+", " ", text)
    parts: List[str] = []
    for token in text.split(" "):
        bare = token.strip("()")
        if _is_acronym_token(bare) or (bare.isupper() and 2 <= len(bare) <= 6):
            parts.append(token)  # preserva
        elif token.startswith("(") and token.endswith(")"):
            inner = token[1:-1]
            if _is_acronym_token(inner) or (inner.isupper() and 2 <= len(inner) <= 6):
                parts.append(token)
            else:
                parts.append("(" + inner[:1].upper() + inner[1:].lower() + ")" if inner else token)
        else:
            parts.append(token[:1].upper() + token[1:].lower() if token else token)
    return " ".join(parts)


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


def _ym_to_months(ym: str) -> int:
    return int(ym[:4]) * 12 + int(ym[5:7])


def redistribute_weights(
    original: Dict[str, float],
    nao_aplicaveis: Set[str],
) -> Tuple[Dict[str, float], str]:
    """
    Redistribui pesos de dimensões não aplicáveis proporcionalmente
    entre as restantes. Pesos efetivos somam 100.
    """
    if not nao_aplicaveis:
        return dict(original), "sem_redistribuicao"

    remaining = {k: v for k, v in original.items() if k not in nao_aplicaveis}
    removed = sum(original[k] for k in nao_aplicaveis if k in original)
    base = sum(remaining.values())
    if base <= 0:
        # fallback uniforme
        n = len(remaining) or 1
        efetivos = {k: round(100.0 / n, 4) for k in remaining}
        return efetivos, "redistribuicao_uniforme_fallback"

    efetivos = {
        k: round(v + removed * (v / base), 4) for k, v in remaining.items()
    }
    # Ajuste de arredondamento para somar 100
    drift = round(100.0 - sum(efetivos.values()), 4)
    if efetivos and abs(drift) > 1e-9:
        first = next(iter(efetivos))
        efetivos[first] = round(efetivos[first] + drift, 4)
    method = (
        f"pesos de {sorted(nao_aplicaveis)} redistribuídos proporcionalmente "
        f"entre dimensões aplicáveis (soma efetiva=100)"
    )
    return efetivos, method


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
class DataQualityProfile:
    """Perfil explícito de aplicabilidade de campos/dimensões."""

    centro_custo_aplicavel: bool = True
    cid_aplicavel: bool = True
    # Dimensões IQB (False ⇒ não aplicável + redistribuição de peso)
    completude_aplicavel: bool = True
    consistencia_aplicavel: bool = True
    padronizacao_aplicavel: bool = True
    identidade_aplicavel: bool = True
    rastreabilidade_aplicavel: bool = True
    atualidade_aplicavel: bool = True


@dataclass
class DataQualityResult:
    client_id: int
    periodo: Dict[str, Optional[str]]
    iqb: float
    classificacao: str
    dimensoes: Dict[str, float]
    status_dimensoes: Dict[str, str]
    pesos_originais: Dict[str, float]
    pesos_efetivos: Dict[str, float]
    dimensoes_nao_aplicaveis: List[str]
    metodologia_redistribuicao: str
    pesos: Dict[str, float]  # alias de pesos_efetivos (compat)
    completude: Dict[str, Any]
    padronizacao_setor: Dict[str, Any]
    centro_custo: Dict[str, Any]
    identidade: Dict[str, Any]
    horas: Dict[str, Any]
    dias_datas: Dict[str, Any]
    cid: Dict[str, Any]
    rastreabilidade: Dict[str, Any]
    atualidade: Dict[str, Any]
    periodos_invalidos: Dict[str, Any]
    sugestoes: List[Dict[str, Any]]
    alertas: List[Dict[str, Any]]
    limitacoes: List[str]
    estrategia_identidade_futura: List[str]
    eventos_analisados: int
    eventos_excluidos_janela: int

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

    def _mes_valido(self, mes: Optional[str]) -> bool:
        if mes is None:
            return False
        return bool(_MES_REF_RE.fullmatch(str(mes).strip()))

    def _in_window(
        self,
        mes: Optional[str],
        periodo_inicio: Optional[str],
        periodo_fim: Optional[str],
    ) -> bool:
        if not self._mes_valido(mes):
            return False
        assert mes is not None
        mes = str(mes).strip()
        if periodo_inicio is not None and mes < periodo_inicio:
            return False
        if periodo_fim is not None and mes > periodo_fim:
            return False
        return True

    def _audit_uploads(
        self,
        client_id: int,
        periodo_inicio: Optional[str],
        periodo_fim: Optional[str],
    ) -> Dict[str, Any]:
        """Auditoria independente: todos os uploads do cliente, não só os com eventos."""
        all_uploads: List[Upload] = (
            self.db.query(Upload).filter(Upload.client_id == client_id).all()
        )
        orphan_uploads: List[Upload] = []
        try:
            orphan_uploads = (
                self.db.query(Upload).filter(Upload.client_id.is_(None)).all()
            )
        except Exception:
            orphan_uploads = []

        valid_window: List[Upload] = []
        sem_periodo: List[Upload] = []
        malformado: List[Upload] = []
        fora_janela_validos: List[Upload] = []
        excluidos_periodo_invalido: List[Upload] = []

        has_window = periodo_inicio is not None or periodo_fim is not None

        for up in all_uploads:
            mes = up.mes_referencia
            if mes is None or not str(mes).strip():
                sem_periodo.append(up)
                excluidos_periodo_invalido.append(up)
                continue
            if not self._mes_valido(mes):
                malformado.append(up)
                excluidos_periodo_invalido.append(up)
                continue
            if has_window and not self._in_window(mes, periodo_inicio, periodo_fim):
                fora_janela_validos.append(up)
                continue
            valid_window.append(up)

        return {
            "all": all_uploads,
            "valid_window": valid_window,
            "sem_periodo": sem_periodo,
            "malformado": malformado,
            "fora_janela_validos": fora_janela_validos,
            "excluidos_periodo_invalido": excluidos_periodo_invalido,
            "sem_cliente": orphan_uploads,
        }

    def analyze(
        self,
        client_id: int,
        periodo_inicio: Optional[str] = None,
        periodo_fim: Optional[str] = None,
        *,
        weights: Optional[IQBWeights] = None,
        profile: Optional[DataQualityProfile] = None,
        duracao_excepcional_dias: float = _DEFAULT_DURACAO_EXCEPCIONAL_DIAS,
        suppress_cid_groups_below: int = 5,
        reference_date: Optional[date] = None,
    ) -> DataQualityResult:
        session_ref = self.db
        cid = self._validate_client_id(client_id)
        periodo_inicio, periodo_fim = validate_period_range(periodo_inicio, periodo_fim)
        w = weights or IQBWeights(**DEFAULT_IQB_WEIGHTS)
        w.validate()
        prof = profile or DataQualityProfile()
        ref_day = reference_date or date.today()

        upload_audit = self._audit_uploads(cid, periodo_inicio, periodo_fim)
        has_window = periodo_inicio is not None or periodo_fim is not None

        all_uploads: List[Upload] = upload_audit["all"]
        if has_window:
            valid_uploads = list(upload_audit["valid_window"])
        else:
            valid_uploads = [
                u for u in all_uploads if self._mes_valido(u.mes_referencia)
            ]
        valid_upload_ids = {u.id for u in valid_uploads}

        all_client_rows: List[Atestado] = (
            self.db.query(Atestado)
            .join(Upload)
            .filter(Upload.client_id == cid)
            .all()
        )
        rows: List[Atestado] = []
        excluded_invalid_period = 0
        for row in all_client_rows:
            mes = row.upload.mes_referencia if row.upload else None
            if row.upload_id in valid_upload_ids:
                rows.append(row)
            elif not self._mes_valido(mes):
                excluded_invalid_period += 1
            # período válido fora da janela: não entra e não conta como inválido

        n = len(rows)

        # Contagens de eventos por upload (inclui zero)
        eventos_por_upload: Dict[int, int] = {u.id: 0 for u in valid_uploads}
        for row in rows:
            eventos_por_upload[row.upload_id] = eventos_por_upload.get(row.upload_id, 0) + 1
        uploads_zero = sum(1 for _uid, c in eventos_por_upload.items() if c == 0)

        # --- contadores de qualidade nos eventos válidos da janela ---
        sem_setor = sem_cc = sem_cid = sem_jornada = 0
        sem_dias = sem_horas_reg = sem_data = sem_periodo = 0
        sem_ident = sem_upload = sem_cliente = 0

        dias_neg = dias_nulos = dias_zero = duracao_exc = 0
        data_fim_antes = data_futura = periodo_incompativel = 0

        horas_reg = horas_est = horas_sem = 0
        jornada_ausente = jornada_invalida = divergencia_horas = 0

        # identidade por evento
        ev_mat = ev_cpf = ev_nome = ev_nenhum = 0
        # identidade por trabalhador aproximado: key -> best kind rank
        _KIND_RANK = {"matricula": 3, "cpf": 2, "nome": 1, "nenhum": 0}
        worker_best: Dict[str, str] = {}
        workers_sem_key_events = 0

        cid_preenchido = cid_formato_ok = cid_mal = 0
        cid_grupos: Dict[str, Set[str]] = {}

        # setor: chave -> variant_counts, eventos
        setor_map: Dict[str, Dict[str, Any]] = {}
        cc_values: Set[str] = set()
        cc_preenchido = 0
        cc_form_map: Dict[str, Set[str]] = {}

        # sobreposição: cada registro no máximo uma vez
        worker_intervals: Dict[str, List[Tuple[date, date, int]]] = {}
        registros_com_sobreposicao: Set[int] = set()

        for idx, row in enumerate(rows):
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
                    key, {"variant_counts": Counter(), "eventos": 0}
                )
                raw_label = str(setor_raw).strip()
                bucket["variant_counts"][raw_label] += 1
                bucket["eventos"] += 1

            cc = _norm_text(row.centro_custo)
            if cc is None:
                sem_cc += 1
            else:
                cc_preenchido += 1
                cc_values.add(cc)
                ck = normalize_sector_key(row.centro_custo)
                if ck:
                    cc_form_map.setdefault(ck, set()).add(str(row.centro_custo).strip())

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
                ev_mat += 1
            elif kind == "cpf":
                ev_cpf += 1
            elif kind == "nome":
                ev_nome += 1
            else:
                ev_nenhum += 1
                sem_ident += 1
                workers_sem_key_events += 1

            if wkey:
                prev = worker_best.get(wkey)
                if prev is None or _KIND_RANK[kind] > _KIND_RANK[prev]:
                    worker_best[wkey] = kind

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
                sem_jornada += 1

            if horas is not None and horas > 0:
                horas_reg += 1
                if dias is not None and dias > 0 and jornada is not None and jornada > 0:
                    if abs(dias * jornada - horas) > _HORAS_DIVERGENCIA_TOLERANCIA:
                        divergencia_horas += 1
            else:
                sem_horas_reg += 1
                if dias is not None and dias > 0 and jornada is not None and jornada > 0:
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
            if d0 is not None and mes and self._mes_valido(mes):
                if abs(_ym_to_months(f"{d0.year:04d}-{d0.month:02d}") - _ym_to_months(str(mes).strip())) > 1:
                    periodo_incompativel += 1

            if wkey and d0 is not None:
                end = d1 if d1 is not None else d0
                if end >= d0:
                    intervals = worker_intervals.setdefault(wkey, [])
                    overlapped = False
                    for a, b, other_idx in intervals:
                        if d0 <= b and end >= a:
                            registros_com_sobreposicao.add(idx)
                            registros_com_sobreposicao.add(other_idx)
                            overlapped = True
                    intervals.append((d0, end, idx))

        def pct(part: int, whole: int = n) -> float:
            if whole <= 0:
                return 0.0
            return round(100.0 * part / whole, 4)

        # --- identidade trabalhador ---
        tw_mat = sum(1 for k, kind in worker_best.items() if kind == "matricula")
        tw_cpf = sum(1 for k, kind in worker_best.items() if kind == "cpf")
        tw_nome = sum(1 for k, kind in worker_best.items() if kind == "nome")
        tw_total = len(worker_best)
        # eventos sem chave não formam trabalhador aproximado mensurável
        risco = identity_risk(tw_mat, tw_cpf, tw_nome, 0 if tw_total else ev_nenhum)

        identidade = {
            "metodo": "aproximado",
            "por_evento": {
                "com_matricula": ev_mat,
                "com_cpf": ev_cpf,
                "somente_nome": ev_nome,
                "sem_identificacao": ev_nenhum,
            },
            "por_trabalhador_aproximado": {
                "com_matricula": tw_mat,
                "com_cpf": tw_cpf,
                "somente_nome": tw_nome,
                "trabalhadores_aproximados": tw_total,
                "eventos_sem_chave_util": workers_sem_key_events,
            },
            # compat campos planos = por evento (legado A02 inicial)
            "por_matricula": ev_mat,
            "por_cpf": ev_cpf,
            "somente_por_nome": ev_nome,
            "sem_identificador": ev_nenhum,
            "risco": risco,
            "nota": (
                "IQB usa cobertura por trabalhador aproximado. "
                "Fragmentação possível quando a mesma pessoa gera chaves distintas. "
                "Valores nunca são expostos."
            ),
        }

        # --- setores ---
        setores_variantes = []
        for key, data in setor_map.items():
            counts: Counter = data["variant_counts"]
            n_var = len(counts)
            if n_var > 1:
                label, needs = choose_sector_label(dict(counts))
                variantes_agg = [
                    {"rotulo": rot, "eventos": cnt}
                    for rot, cnt in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
                ]
                setores_variantes.append(
                    {
                        "chave_normalizada": key,
                        "rotulo_proposto": label,
                        "necessita_validacao_humana": needs,
                        "proposta_definitiva": False,
                        "quantidade_variantes": n_var,
                        "eventos": int(data["eventos"]),
                        "variantes": variantes_agg,
                    }
                )
        setores_variantes.sort(key=lambda x: (-x["eventos"], x["chave_normalizada"]))

        padronizacao_setor = {
            "chaves_distintas": len(setor_map),
            "setores_com_variantes": len(setores_variantes),
            "setores_variantes": setores_variantes,
            "nota": (
                "Chave comparável remove diacríticos (Elétrica=ELETRICA). "
                "Sem fuzzy semântico (Pintura ≠ Pintura (Líder)). "
                "Rótulo = variante mais frequente; siglas preservadas; validação humana."
            ),
        }

        # --- centro de custo ---
        if not prof.centro_custo_aplicavel:
            cc_status = "nao_aplicavel"
        elif n == 0:
            cc_status = "nao_avaliado"
        elif cc_preenchido == 0:
            cc_status = "avaliado"  # aplicável e ausente — penaliza
        else:
            cc_status = "avaliado"

        cc_variantes_forma = (
            sum(1 for s in cc_form_map.values() if len(s) > 1)
            if cc_status == "avaliado" and cc_preenchido > 0
            else 0
        )
        centro_custo = {
            "status": cc_status,
            "aplicavel": prof.centro_custo_aplicavel,
            "preenchido": cc_preenchido,
            "ausente": sem_cc,
            "cobertura_pct": pct(cc_preenchido) if n else 0.0,
            "valores_distintos": len(cc_values) if cc_preenchido else 0,
            "variacoes_apenas_forma": cc_variantes_forma,
            "nota": (
                "Não se inventa CC a partir do setor. "
                "Aplicável e 100% ausente penaliza. "
                "Não aplicável explicitamente não penaliza (redistribui peso)."
            ),
        }

        # --- horas / dias ---
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
            "registros_com_sobreposicao_potencial": len(registros_com_sobreposicao),
            "nota_sobreposicao": (
                "Cada registro conta no máximo uma vez. "
                "Não infere fraude, erro ou nexo."
            ),
        }

        # --- CID ---
        cid_dist = []
        cid_suprimidos = 0
        soma_contagens_grupos_suprimidos = 0
        workers_suprimidos_unicos: Set[str] = set()
        for letra, workers in cid_grupos.items():
            n_w = len(workers)
            if 0 < n_w < suppress_cid_groups_below:
                cid_suprimidos += 1
                soma_contagens_grupos_suprimidos += n_w
                workers_suprimidos_unicos |= workers
                continue
            cid_dist.append(
                {"grupo_alfabetico_cid": letra, "trabalhadores_unicos": n_w}
            )
        if cid_suprimidos:
            cid_dist.append(
                {
                    "grupo_alfabetico_cid": "GRUPO_SUPRIMIDO",
                    "grupos_suprimidos": cid_suprimidos,
                    "soma_contagens_por_grupo": soma_contagens_grupos_suprimidos,
                    "trabalhadores_unicos_globais": len(workers_suprimidos_unicos),
                    "nota": (
                        "soma_contagens_por_grupo pode contar a mesma pessoa em "
                        "mais de um grupo; use trabalhadores_unicos_globais."
                    ),
                }
            )
        cid_dist.sort(
            key=lambda x: (
                x["grupo_alfabetico_cid"] == "GRUPO_SUPRIMIDO",
                -x.get("trabalhadores_unicos", x.get("trabalhadores_unicos_globais", 0)),
                x["grupo_alfabetico_cid"],
            )
        )

        if not prof.cid_aplicavel:
            cid_dim_status = "nao_aplicavel"
        elif n == 0:
            cid_dim_status = "nao_avaliado"
        else:
            cid_dim_status = "avaliado"

        cid_info = {
            "status": cid_dim_status,
            "aplicavel": prof.cid_aplicavel,
            "preenchimento_pct": pct(cid_preenchido),
            "formato_valido": cid_formato_ok,
            "mal_formatados": cid_mal,
            "ausentes": sem_cid,
            "distribuicao_grupo_alfabetico": cid_dist,
            "nota": (
                "Não valida diagnóstico clínico. Sem CID individual. "
                "GRUPO_SUPRIMIDO distingue soma por grupo vs únicos globais."
            ),
        }

        # --- rastreabilidade / múltiplos uploads ---
        uploads_por_mes: Dict[str, int] = {}
        for up in valid_uploads:
            mes = str(up.mes_referencia).strip()
            uploads_por_mes[mes] = uploads_por_mes.get(mes, 0) + 1
        competencias_multi = sum(1 for c in uploads_por_mes.values() if c > 1)

        hash_disponivel = False  # schema Upload sem campo de hash
        nome_original_ok = sum(1 for up in valid_uploads if _norm_text(up.filename))
        data_proc_ok = sum(1 for up in valid_uploads if up.data_upload is not None)

        rastreabilidade = {
            "uploads_validos_na_janela": len(valid_uploads),
            "uploads_com_zero_eventos": uploads_zero,
            "uploads_sem_periodo": len(upload_audit["sem_periodo"]),
            "uploads_periodo_malformado": len(upload_audit["malformado"]),
            "uploads_sem_cliente": len(upload_audit["sem_cliente"]),
            "uploads_fora_da_janela_com_periodo_valido": len(upload_audit["fora_janela_validos"]),
            "eventos_por_upload": {
                "min": min(eventos_por_upload.values()) if eventos_por_upload else 0,
                "max": max(eventos_por_upload.values()) if eventos_por_upload else 0,
                "uploads": len(eventos_por_upload),
            },
            "multiplos_uploads_competencia": competencias_multi,
            "possivel_reupload": competencias_multi > 0,
            "duplicidade_nao_confirmada": True,
            "duplicidade_confirmada": False,
            "duplicidade_confirmada_disponivel": False,
            "hash_arquivo_disponivel": hash_disponivel,
            "nome_original_disponivel_pct": (
                round(100.0 * nome_original_ok / len(valid_uploads), 4) if valid_uploads else 0.0
            ),
            "data_processamento_disponivel_pct": (
                round(100.0 * data_proc_ok / len(valid_uploads), 4) if valid_uploads else 0.0
            ),
            "mensagem": _MULTIPLOS_UPLOADS_MSG,
            "nota": (
                "Múltiplos uploads ≠ duplicidade confirmada. "
                "Não afirma KPI duplicado sem hash/assinatura."
            ),
        }

        periodos_invalidos = {
            "uploads_sem_periodo": len(upload_audit["sem_periodo"]),
            "uploads_periodo_malformado": len(upload_audit["malformado"]),
            "eventos_vinculados_uploads_invalidos": excluded_invalid_period,
            "eventos_excluidos_do_calculo_da_janela": excluded_invalid_period,
            "razao_exclusao": (
                "período ausente ou malformado (não YYYY-MM); "
                "não misturados nas métricas válidas da janela"
            ),
        }

        # --- atualidade ---
        valid_meses = sorted(
            {str(u.mes_referencia).strip() for u in valid_uploads if self._mes_valido(u.mes_referencia)}
        )
        ultimo_periodo_valido = valid_meses[-1] if valid_meses else None
        if ultimo_periodo_valido:
            ref_ym = f"{ref_day.year:04d}-{ref_day.month:02d}"
            diff_meses = _ym_to_months(ref_ym) - _ym_to_months(ultimo_periodo_valido)
        else:
            diff_meses = None

        if valid_uploads:
            latest = max(
                (up.data_upload for up in valid_uploads if up.data_upload),
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
            "data_referencia": ref_day.isoformat(),
            "ultimo_periodo_valido": ultimo_periodo_valido,
            "diferenca_meses_vs_referencia": diff_meses,
            "lag_dias_ultimo_upload": lag_dias,
            "criterio": (
                "score por lag do último data_upload vs data_referencia: "
                "≤30→100; ≤90→80; ≤180→60; >180→30"
            ),
        }

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

        # --- scores + status dimensões ---
        pesos_originais = w.as_dict()
        nao_aplicaveis: Set[str] = set()
        # Não removemos dimensão só por ausência; só por perfil explícito.
        # CC/CID "não aplicável" não cria dimensão IQB separada — afetam completude.
        # Dimensões IQB top-level: se quiséssemos marcar subcampos...
        # Profile marks field applicability inside completude scoring.

        status_dimensoes = {
            "completude": "avaliado" if n > 0 else "nao_avaliado",
            "consistencia": "avaliado" if n > 0 else "nao_avaliado",
            "padronizacao": "avaliado" if n > 0 else "nao_avaliado",
            "identidade": "avaliado" if n > 0 else "nao_avaliado",
            "rastreabilidade": "avaliado",
            "atualidade": "avaliado" if valid_uploads else "nao_avaliado",
        }

        # Campos não aplicáveis influenciam completude (não removem dimensão)
        # Mas usuário pediu dimensoes_nao_aplicaveis — usamos marcadores de campo:
        campos_nao_aplicaveis: List[str] = []
        if not prof.centro_custo_aplicavel:
            campos_nao_aplicaveis.append("centro_custo")
        if not prof.cid_aplicavel:
            campos_nao_aplicaveis.append("cid")

        # Redistribuição só se marcarmos dimensões IQB inteiras como N/A.
        # Aqui não marcamos dimensões top-level como N/A por CC/CID;
        # pesos efetivos = originais salvo extensão futura.
        # Se ambos CC e CID não aplicáveis, completude não os inclui (não melhora artificialmente
        # por "ignorar buraco" sem perfil — com perfil, exclusão é explícita).
        pesos_efetivos, metodo_redist = redistribute_weights(pesos_originais, nao_aplicaveis)

        if n == 0:
            scores = {k: 0.0 for k in pesos_originais}
        else:
            campos_frac = [
                1 - sem_setor / n,
                1 - sem_dias / n,
                1 - sem_ident / n,
                1 - sem_upload / n,
                1 - sem_periodo / n,
                1 - sem_jornada / n,
                1 - (horas_sem / n),
                1 - sem_data / n,
            ]
            if prof.centro_custo_aplicavel:
                # aplicável: ausência penaliza (mesmo 100% vazio)
                campos_frac.append(cc_preenchido / n)
            if prof.cid_aplicavel:
                campos_frac.append(cid_preenchido / n)
            scores_completude = 100.0 * (sum(campos_frac) / len(campos_frac))

            inconsistencias = (
                dias_neg + data_fim_antes + data_futura + jornada_invalida
                + divergencia_horas + periodo_incompativel
            )
            scores_cons = max(0.0, 100.0 - 100.0 * inconsistencias / max(n, 1))

            if not setor_map:
                scores_pad = 50.0
            else:
                eventos_variante = sum(s["eventos"] for s in setores_variantes)
                scores_pad = max(0.0, 100.0 - 100.0 * eventos_variante / n)

            # Identidade por trabalhador aproximado (não dominada por recorrentes)
            if tw_total > 0:
                scores_id = 100.0 * (
                    1.0 * tw_mat + 0.6 * tw_cpf + 0.25 * tw_nome
                ) / tw_total
            else:
                scores_id = 0.0

            multi_pen = min(40.0, 15.0 * competencias_multi)
            nome_score = (nome_original_ok / len(valid_uploads) * 40.0) if valid_uploads else 0.0
            data_score = (data_proc_ok / len(valid_uploads) * 40.0) if valid_uploads else 0.0
            scores_rast = max(0.0, nome_score + data_score - multi_pen)
            if not hash_disponivel:
                scores_rast = min(scores_rast, 80.0)
                status_dimensoes["rastreabilidade_hash"] = "indisponivel"  # type: ignore[index]

            scores = {
                "completude": round(scores_completude, 4),
                "consistencia": round(scores_cons, 4),
                "padronizacao": round(scores_pad, 4),
                "identidade": round(scores_id, 4),
                "rastreabilidade": round(scores_rast, 4),
                "atualidade": round(atualidade_score, 4),
            }

        # Extensão: permitir marcar dimensões IQB não aplicáveis via profile futuro.
        # Se profile desativar CC e CID, não redistribui dimensão top-level.
        # Suporte explícito: se completude_skip... Não necessário.
        # Usuário pediu exemplo centro_custo_aplicavel — já tratado na completude.
        # Para demonstrar redistribuição de pesos efetivos: se passarmos
        # dimensões N/A vazias, efetivos=originais. Testes pedem redistribuição
        # quando dimensão explicitamente não aplicável — usamos flag interna
        # opcional via profile attributes extras.

        # Allow marking IQB dimensions non-applicable through optional profile attrs
        for dim in ("completude", "consistencia", "padronizacao", "identidade", "rastreabilidade", "atualidade"):
            flag = getattr(prof, f"{dim}_aplicavel", True)
            if flag is False:
                nao_aplicaveis.add(dim)
                status_dimensoes[dim] = "nao_aplicavel"

        pesos_efetivos, metodo_redist = redistribute_weights(pesos_originais, nao_aplicaveis)
        # Remove scores N/A from IQB sum
        scores_used = {k: v for k, v in scores.items() if k not in nao_aplicaveis}
        for k in nao_aplicaveis:
            scores[k] = 0.0  # sinaliza; não entra no IQB via peso 0 efetivo

        iqb = round(
            sum(scores_used.get(k, 0.0) * (pesos_efetivos.get(k, 0.0) / 100.0) for k in pesos_efetivos),
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
                    "tipo": "MULTIPLOS_UPLOADS_COMPETENCIA",
                    "prioridade": "alta",
                    "impacto_eventos": n,
                    "acao": "Revisar múltiplos uploads na competência (duplicidade não confirmada)",
                    "aplicacao_automatica": False,
                }
            )
        if prof.centro_custo_aplicavel and cc_preenchido == 0 and n > 0:
            sugestoes.append(
                {
                    "tipo": "CENTRO_CUSTO_AUSENTE",
                    "prioridade": "media",
                    "impacto_eventos": n,
                    "acao": "Incluir centro de custo no layout de upload quando disponível",
                    "aplicacao_automatica": False,
                }
            )
        if tw_nome > tw_mat or ev_nenhum:
            sugestoes.append(
                {
                    "tipo": "IDENTIDADE_FRAGIL",
                    "prioridade": "alta",
                    "impacto_eventos": ev_nome + ev_nenhum,
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
            alertas.append({"tipo": "DIVERGENCIA_HORAS", "count": divergencia_horas})
        if competencias_multi:
            alertas.append(
                {
                    "tipo": "MULTIPLOS_UPLOADS_COMPETENCIA",
                    "count": competencias_multi,
                    "possivel_reupload": True,
                    "duplicidade_confirmada": False,
                }
            )
        if excluded_invalid_period:
            alertas.append(
                {
                    "tipo": "PERIODOS_INVALIDOS",
                    "eventos_excluidos": excluded_invalid_period,
                }
            )

        limitacoes = [
            "Análise shadow: nenhuma correção persistente aplicada.",
            "Normalização de setor apenas em memória; diacríticos removidos na chave.",
            "Hash de arquivo indisponível no schema atual de Upload.",
            "Múltiplos uploads ≠ duplicidade confirmada.",
            "Identidade aproximada; IQB por trabalhador, não por evento recorrente.",
            "Sobreposição: registros com sobreposição potencial (máx. 1 contagem/registro).",
            "Soma de grupos CID suprimidos ≠ efetivo único global.",
        ]

        estrategia = [
            "Matrícula como chave preferencial operacional.",
            "CPF somente em camada médica restrita e protegida.",
            "Identificador pseudonimizado para analytics.",
            "Nome apenas como fallback legado.",
        ]

        # Limpa status auxiliar não-dimensão
        status_dimensoes_clean = {
            k: v for k, v in status_dimensoes.items()
            if k in DEFAULT_IQB_WEIGHTS
        }

        result = DataQualityResult(
            client_id=cid,
            periodo={"inicio": periodo_inicio, "fim": periodo_fim},
            iqb=iqb,
            classificacao=classificacao,
            dimensoes=scores,
            status_dimensoes=status_dimensoes_clean,
            pesos_originais=pesos_originais,
            pesos_efetivos=pesos_efetivos,
            dimensoes_nao_aplicaveis=sorted(nao_aplicaveis) + [
                f"campo:{c}" for c in campos_nao_aplicaveis
            ],
            metodologia_redistribuicao=metodo_redist,
            pesos=pesos_efetivos,
            completude=completude,
            padronizacao_setor=padronizacao_setor,
            centro_custo=centro_custo,
            identidade=identidade,
            horas=horas,
            dias_datas=dias_datas,
            cid=cid_info,
            rastreabilidade=rastreabilidade,
            atualidade=atualidade,
            periodos_invalidos=periodos_invalidos,
            sugestoes=sugestoes,
            alertas=alertas,
            limitacoes=limitacoes,
            estrategia_identidade_futura=estrategia,
            eventos_analisados=n,
            eventos_excluidos_janela=excluded_invalid_period,
        )

        if self.db is not session_ref:
            raise RuntimeError("sessão foi mutada indevidamente")

        assert_no_pii_in_payload(result.to_dict())
        return result


def analyze_data_quality(
    db: Session,
    client_id: int,
    periodo_inicio: Optional[str] = None,
    periodo_fim: Optional[str] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    return DataQualityService(db).analyze(
        client_id=client_id,
        periodo_inicio=periodo_inicio,
        periodo_fim=periodo_fim,
        **kwargs,
    ).to_dict()
