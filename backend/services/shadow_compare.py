"""
Comparação local (shadow) entre métricas legadas e o MetricService canônico.

Uso previsto:
- scripts/testes locais com banco temporário + fixtures sintéticas;
- NÃO registrar como rota pública de produção;
- NÃO importar no startup da aplicação;
- NÃO executar automaticamente.

Não altera telas, uploads, schema ou dados reais.
Não aponta para caminhos de produção por padrão.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.services.metric_service import MetricService

# Caminho conhecido de produção — nunca é default; exige path explícito.
_PRODUCTION_DB_HINT = "/var/www/absenteismo/database/absenteismo.db"

_SUSPICIOUS_KEYS = frozenset(
    {
        "cpf",
        "matricula",
        "nome",
        "nomecompleto",
        "nome_funcionario",
        "email",
        "telefone",
        "documento",
        "worker_key",
        "identity_key",
    }
)

_INTERNAL_KEY_PREFIXES = ("cpf:", "mat:", "nome:")

# CPF formatado ou 11 dígitos contínuos (candidatos textuais)
_CPF_FORMAT_RE = re.compile(
    r"(?<!\d)(\d{3}\.?\d{3}\.?\d{3}-?\d{2})(?!\d)"
)


@dataclass(frozen=True)
class PiiFinding:
    """Achado anti-PII sem expor o valor bruto."""

    path: str
    value_type: str
    category: str
    masked: str = "***"

    def as_message(self) -> str:
        return (
            f"possivel_pii_detectado_em={self.path} "
            f"tipo={self.value_type} "
            f"categoria={self.category} "
            f"valor_mascarado={self.masked}"
        )


class PiiGuardError(ValueError):
    """Erro de guard anti-PII com metadados seguros (sem valor bruto)."""

    def __init__(self, finding: PiiFinding):
        self.finding = finding
        super().__init__(finding.as_message())


def _mask_cpf_shape() -> str:
    return "***.***.***-**"


def _mask_internal(prefix: str) -> str:
    return f"{prefix}***"


def _digits_only(text: str) -> str:
    return "".join(ch for ch in text if ch.isdigit())


def is_repeated_digit_sequence(digits: str) -> bool:
    return len(digits) > 0 and digits == digits[0] * len(digits)


def cpf_check_digits_valid(digits: str) -> bool:
    """Valida os dois dígitos verificadores do CPF (11 dígitos)."""
    if len(digits) != 11 or not digits.isdigit():
        return False
    if is_repeated_digit_sequence(digits):
        return False

    def _digit(slice_digits: str, weight_start: int) -> str:
        total = sum(
            int(d) * w
            for d, w in zip(slice_digits, range(weight_start, 1, -1))
        )
        rest = total % 11
        return "0" if rest < 2 else str(11 - rest)

    d1 = _digit(digits[:9], 10)
    d2 = _digit(digits[:10], 11)
    return digits[-2:] == d1 + d2


def _looks_unequivocal_cpf_format(text: str) -> bool:
    """Formato com pontuação típica de CPF: 000.000.000-00."""
    return bool(re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", text.strip()))


def _cpf_textual_should_block(text: str, *, suspicious_field: bool) -> bool:
    """
    Decide se uma string candidata a CPF deve ser bloqueada.
    Não trata qualquer sequência de 11 dígitos como PII automaticamente.
    """
    stripped = text.strip()
    if not stripped:
        return False

    for match in _CPF_FORMAT_RE.finditer(stripped):
        raw = match.group(1)
        digits = _digits_only(raw)
        if len(digits) != 11:
            continue
        if is_repeated_digit_sequence(digits):
            continue
        unequivocal = _looks_unequivocal_cpf_format(raw)
        valid = cpf_check_digits_valid(digits)
        if suspicious_field or unequivocal or valid:
            return True
    return False


def _has_internal_identity_prefix(text: str) -> Optional[str]:
    lower = text.lstrip().lower()
    for prefix in _INTERNAL_KEY_PREFIXES:
        if lower.startswith(prefix):
            return prefix
    return None


def _is_suspicious_key(key: Any) -> bool:
    if not isinstance(key, str):
        return False
    return key.strip().lower() in _SUSPICIOUS_KEYS


def _type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, dict):
        return "dict"
    if isinstance(value, (list, tuple)):
        return "list"
    return type(value).__name__


def iter_pii_findings(
    obj: Any,
    *,
    path: str = "$",
    parent_key: Optional[str] = None,
) -> Iterator[PiiFinding]:
    """
    Travessia recursiva estruturada.
    int/float agregados NÃO são convertidos em string para regex de CPF.
    """
    suspicious = _is_suspicious_key(parent_key) if parent_key is not None else False

    if isinstance(obj, dict):
        for key, value in obj.items():
            child_path = f"{path}.{key}" if path != "$" else str(key)
            # Chave suspeita com qualquer valor (exceto ausência total) → bloqueio
            if _is_suspicious_key(key):
                if value is not None and value != "":
                    yield PiiFinding(
                        path=child_path,
                        value_type=_type_name(value),
                        category="campo_suspeito",
                        masked=_mask_cpf_shape()
                        if str(key).lower() == "cpf"
                        else "***",
                    )
                    continue
            yield from iter_pii_findings(
                value, path=child_path, parent_key=str(key) if key is not None else None
            )
        return

    if isinstance(obj, (list, tuple)):
        for idx, item in enumerate(obj):
            yield from iter_pii_findings(
                item, path=f"{path}[{idx}]", parent_key=parent_key
            )
        return

    # Números agregados: nunca aplicar regex de CPF
    if isinstance(obj, bool):
        return
    if isinstance(obj, (int, float)):
        if suspicious:
            yield PiiFinding(
                path=path,
                value_type=_type_name(obj),
                category="campo_suspeito",
                masked="***",
            )
        return

    if obj is None:
        return

    if not isinstance(obj, str):
        # Tipos não escalares já tratados; demais ignorados com segurança
        return

    text = obj
    prefix = _has_internal_identity_prefix(text)
    if prefix:
        yield PiiFinding(
            path=path,
            value_type="str",
            category="chave_interna",
            masked=_mask_internal(prefix),
        )
        return

    if suspicious:
        # Qualquer valor textual em campo suspeito
        yield PiiFinding(
            path=path,
            value_type="str",
            category="campo_suspeito",
            masked="***",
        )
        return

    if _cpf_textual_should_block(text, suspicious_field=False):
        digits = _digits_only(text)
        category = "cpf_formatado" if _looks_unequivocal_cpf_format(text.strip()) else "cpf_valido"
        if len(digits) == 11 and cpf_check_digits_valid(digits):
            category = "cpf_valido"
        elif _looks_unequivocal_cpf_format(text.strip()):
            category = "cpf_formatado"
        yield PiiFinding(
            path=path,
            value_type="str",
            category=category,
            masked=_mask_cpf_shape(),
        )


def find_pii_issues(payload: Any) -> List[PiiFinding]:
    return list(iter_pii_findings(payload))


def assert_no_pii_in_payload(payload: Dict[str, Any]) -> None:
    """
    Guard anti-PII estruturado.
    Em falha, informa apenas caminho, tipo, categoria e valor mascarado.
    """
    findings = find_pii_issues(payload)
    if findings:
        raise PiiGuardError(findings[0])


@dataclass
class ShadowDiff:
    chave: str
    legado: Any
    canonico: Any
    delta: Optional[float] = None
    nota: str = ""


@dataclass
class ShadowCompareReport:
    client_id: int
    periodo_inicio: Optional[str]
    periodo_fim: Optional[str]
    legado: Dict[str, Any]
    canonico: Dict[str, Any]
    diferencas: List[ShadowDiff] = field(default_factory=list)
    avisos: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "client_id": self.client_id,
            "periodo": {"inicio": self.periodo_inicio, "fim": self.periodo_fim},
            "legado": self.legado,
            "canonico": self.canonico,
            "diferencas": [
                {
                    "chave": d.chave,
                    "legado": d.legado,
                    "canonico": d.canonico,
                    "delta": d.delta,
                    "nota": d.nota,
                }
                for d in self.diferencas
            ],
            "avisos": list(self.avisos),
        }


def open_sqlite_readonly(db_path: str) -> Session:
    """
    Abre SQLite em modo leitura. Exige caminho explícito.
    Não usa /var/www/... como default.
    """
    import sqlite3

    if not db_path or not str(db_path).strip():
        raise ValueError("db_path explícito é obrigatório (sem default de produção)")
    path = str(Path(db_path).expanduser())

    def _connect():
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True, check_same_thread=False)
        try:
            conn.execute("PRAGMA query_only = ON")
        except Exception:
            pass
        return conn

    engine = create_engine("sqlite://", creator=_connect)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def _legacy_metricas_gerais(
    db: Session,
    client_id: int,
    mes_inicio: Optional[str],
    mes_fim: Optional[str],
) -> Dict[str, Any]:
    """Espelha a lógica atual de Analytics.metricas_gerais (somente leitura)."""
    from backend.models import Atestado, Upload
    from sqlalchemy import and_, func

    query = (
        db.query(Atestado)
        .join(Upload)
        .filter(Upload.client_id == client_id)
    )
    if mes_inicio and mes_fim:
        query = query.filter(
            and_(
                Upload.mes_referencia >= mes_inicio,
                Upload.mes_referencia <= mes_fim,
            )
        )

    total_atestados = query.count()
    total_dias = (
        query.with_entities(func.sum(Atestado.dias_atestados)).scalar() or 0
    )
    total_horas = (
        query.with_entities(func.sum(Atestado.horas_perdi)).scalar() or 0
    )
    funcionarios_unicos = (
        query.with_entities(func.count(func.distinct(Atestado.nomecompleto))).scalar()
        or 0
    )
    return {
        "total_atestados": total_atestados,
        "total_dias_perdidos": float(total_dias),
        "total_horas_perdidas": float(total_horas),
        "funcionarios_unicos": funcionarios_unicos,
        "taxa_absenteismo": 0,
        "identidade_legado": "distinct(nomecompleto)",
    }


def compare_shadow(
    db: Session,
    *,
    client_id: int,
    periodo_inicio: Optional[str],
    periodo_fim: Optional[str],
    efetivo_trabalhadores: Optional[int] = None,
) -> ShadowCompareReport:
    """
    Compara métricas legadas vs canônicas no mesmo escopo.

    Aceita sessão já aberta (testes/fixtures ou readonly explícito).
    Não cria endpoint HTTP. Não imprime PII.
    """
    if client_id is None:
        raise ValueError("client_id é obrigatório")

    legado = _legacy_metricas_gerais(db, client_id, periodo_inicio, periodo_fim)
    canonico = MetricService(db).compute(
        client_id=client_id,
        periodo_inicio=periodo_inicio,
        periodo_fim=periodo_fim,
        efetivo_trabalhadores=efetivo_trabalhadores,
    ).to_dict()
    m = canonico["metricas"]

    # Guard estruturado (sem json.dumps + regex cego)
    assert_no_pii_in_payload(canonico)

    diffs: List[ShadowDiff] = []
    avisos: List[str] = [
        "Legado identifica trabalhador por nomecompleto; canônico usa identidade aproximada matricula→cpf→nome.",
        "Legado total_horas_perdidas soma horas_perdi; canônico separa registrada vs estimada e médias distintas.",
        "Taxa de absenteísmo legado não é comparada aqui.",
        "Somente agregados — sem nomes, CPF ou matrícula.",
    ]

    pairs = [
        ("eventos", legado["total_atestados"], m["eventos"], "alias de eventos_brutos"),
        (
            "trabalhadores_unicos",
            legado["funcionarios_unicos"],
            m["trabalhadores_unicos"],
            "pode divergir por identidade aproximada",
        ),
        (
            "dias_perdidos",
            legado["total_dias_perdidos"],
            m["dias_perdidos"],
            "canônico ignora dias inválidos no total",
        ),
        (
            "horas_perdidas_registradas",
            legado["total_horas_perdidas"],
            m["horas_perdidas_registradas"],
            "ambos somam horas_perdi > 0",
        ),
    ]

    for chave, leg, can, nota in pairs:
        try:
            delta = float(can) - float(leg)
        except (TypeError, ValueError):
            delta = None
        if leg != can:
            diffs.append(
                ShadowDiff(chave=chave, legado=leg, canonico=can, delta=delta, nota=nota)
            )

    report = ShadowCompareReport(
        client_id=client_id,
        periodo_inicio=periodo_inicio,
        periodo_fim=periodo_fim,
        legado=legado,
        canonico=canonico,
        diferencas=diffs,
        avisos=avisos,
    )
    assert_no_pii_in_payload(report.to_dict())
    return report


__all__ = [
    "ShadowDiff",
    "ShadowCompareReport",
    "compare_shadow",
    "open_sqlite_readonly",
    "assert_no_pii_in_payload",
    "find_pii_issues",
    "iter_pii_findings",
    "PiiFinding",
    "PiiGuardError",
    "cpf_check_digits_valid",
    "_PRODUCTION_DB_HINT",
]
