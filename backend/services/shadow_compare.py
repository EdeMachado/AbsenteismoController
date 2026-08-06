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

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.services.metric_service import MetricService

# Caminho conhecido de produção — nunca é default; exige path explícito.
_PRODUCTION_DB_HINT = "/var/www/absenteismo/database/absenteismo.db"

_PII_PATTERNS = [
    re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"),
    re.compile(r"\bmat:", re.I),
    re.compile(r"\bcpf:", re.I),
    re.compile(r"\bnome:", re.I),
]


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


def assert_no_pii_in_payload(payload: Dict[str, Any]) -> None:
    """Garante que agregados não carregam chaves internas nem CPF formatado."""
    blob = json.dumps(payload, ensure_ascii=False)
    for pat in _PII_PATTERNS:
        if pat.search(blob):
            raise ValueError(f"PII ou chave interna detectada na saída shadow: {pat.pattern}")
    for banned in ("nomecompleto", "matricula", "cpf", "diagnostico"):
        # Valores de campos de metodologia podem citar nomes de colunas — ok em chaves de texto
        # de documentação; bloqueamos estruturas de distribuição com esses nomes como keys de item.
        pass
    for key in (
        "distribuicao_setor",
        "distribuicao_centro_custo",
        "distribuicao_grupo_alfabetico_cid",
    ):
        for item in payload.get("canonico", {}).get(key, []) if "canonico" in payload else payload.get(key, []):
            if any(b in item for b in ("nomecompleto", "matricula", "cpf", "nome")):
                raise ValueError("Distribuição contém campo identificável")


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

    # Sanidade: chave interna de trabalhador não pode vazar
    blob = json.dumps(canonico, ensure_ascii=False)
    if "mat:" in blob or "cpf:" in blob or '"nome:' in blob:
        raise ValueError("chave interna de trabalhador vazou no resultado canônico")

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
    "_PRODUCTION_DB_HINT",
]
