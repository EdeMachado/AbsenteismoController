"""
Comparação local (shadow) entre métricas legadas e o MetricService canônico.

Uso previsto:
- scripts/testes locais com banco temporário + fixtures sintéticas;
- NÃO registrar como rota pública de produção.

Não altera telas, uploads, schema ou dados reais.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from backend.services.metric_service import compute_canonical_metrics


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
    periodo_inicio: str
    periodo_fim: str
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
        "taxa_absenteismo": 0,  # legado usa efetivo; shadow não força denominador
        "identidade_legado": "distinct(nomecompleto)",
    }


def compare_shadow(
    db: Session,
    *,
    client_id: int,
    periodo_inicio: str,
    periodo_fim: str,
    efetivo_trabalhadores: Optional[int] = None,
) -> ShadowCompareReport:
    """
    Compara métricas legadas vs canônicas no mesmo escopo.

    Aceita banco temporário de testes e fixtures sintéticas.
    Não cria endpoint HTTP.
    """
    if client_id is None:
        raise ValueError("client_id é obrigatório")

    legado = _legacy_metricas_gerais(db, client_id, periodo_inicio, periodo_fim)
    canonico = compute_canonical_metrics(
        db,
        client_id=client_id,
        periodo_inicio=periodo_inicio,
        periodo_fim=periodo_fim,
        efetivo_trabalhadores=efetivo_trabalhadores,
    )
    m = canonico["metricas"]

    diffs: List[ShadowDiff] = []
    avisos: List[str] = [
        "Legado identifica trabalhador por nomecompleto; canônico usa matricula→cpf→nome.",
        "Legado total_horas_perdidas soma apenas horas_perdi; canônico separa registrada vs estimada.",
        "Taxa de absenteísmo legado não é comparada aqui (denominador de horas previstas não oficial neste lote).",
    ]

    pairs = [
        ("eventos", legado["total_atestados"], m["eventos"], "contagem de linhas Atestado"),
        (
            "trabalhadores_unicos",
            legado["funcionarios_unicos"],
            m["trabalhadores_unicos"],
            "pode divergir se houver matrícula/CPF distintos com mesmo nome",
        ),
        (
            "dias_perdidos",
            legado["total_dias_perdidos"],
            m["dias_perdidos"],
            "ambos usam dias_atestados",
        ),
        (
            "horas_perdidas_registradas",
            legado["total_horas_perdidas"],
            m["horas_perdidas_registradas"],
            "ambos somam horas_perdi > 0; legado também soma zeros como 0",
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

    return ShadowCompareReport(
        client_id=client_id,
        periodo_inicio=periodo_inicio,
        periodo_fim=periodo_fim,
        legado=legado,
        canonico=canonico,
        diferencas=diffs,
        avisos=avisos,
    )


__all__ = [
    "ShadowDiff",
    "ShadowCompareReport",
    "compare_shadow",
]
