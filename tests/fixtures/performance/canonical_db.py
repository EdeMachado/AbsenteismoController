"""Synthetic SQLite fixtures for Epic 2A-B canonical → performance adapters.

Fictional aggregates only. No real tenant PII. Never points at production.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Optional, Sequence

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.database import Base
from tests.fixtures.canonical_metrics import add_atestado, add_upload, seed_clients


def make_file_session(path: str | Path) -> Session:
    """Create schema on an on-disk SQLite file and return a session."""
    engine = create_engine(
        f"sqlite:///{path}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def make_memory_session() -> Session:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def _seed_month(
    db: Session,
    *,
    client_id: int,
    mes: str,
    rows: Sequence[dict],
) -> None:
    upload = add_upload(db, client_id=client_id, mes_referencia=mes)
    for row in rows:
        add_atestado(db, upload, **row)


def seed_performance_adapter_fixture(db: Session) -> None:
    """
    Dual-tenant, dual-window synthetic dataset:

    Client 2:
      baseline 2025-05..2025-07 — higher severity (more days/hours)
      current  2026-05..2026-07 — lower severity (severity control shape)
    Client 4:
      baseline/current with different magnitudes (tenant isolation)
    """
    seed_clients(db, (2, 4))

    # --- Client 2 baseline (worse severity) ---
    _seed_month(
        db,
        client_id=2,
        mes="2025-05",
        rows=[
            dict(
                nomecompleto="FUNC ALPHA",
                matricula="M100",
                dias_atestados=3.0,
                horas_perdi=24.0,
                horas_dia=8.0,
                setor="PRODUCAO",
                centro_custo="CC-01",
                cid="M54.5",
            ),
            dict(
                nomecompleto="FUNC BETA",
                matricula="M200",
                dias_atestados=2.0,
                horas_perdi=16.0,
                horas_dia=8.0,
                setor="PRODUCAO",
                centro_custo="CC-01",
                cid="J06.9",
            ),
        ],
    )
    _seed_month(
        db,
        client_id=2,
        mes="2025-06",
        rows=[
            dict(
                nomecompleto="FUNC ALPHA",
                matricula="M100",
                dias_atestados=4.0,
                horas_perdi=32.0,
                horas_dia=8.0,
                setor="PRODUCAO",
                centro_custo="CC-01",
                cid="M54.5",
            ),
            dict(
                nomecompleto="FUNC GAMMA",
                matricula="M300",
                dias_atestados=1.0,
                horas_perdi=8.0,
                horas_dia=8.0,
                setor="ADMIN",
                centro_custo="CC-99",
                cid="J00",
            ),
        ],
    )
    _seed_month(
        db,
        client_id=2,
        mes="2025-07",
        rows=[
            dict(
                nomecompleto="FUNC BETA",
                matricula="M200",
                dias_atestados=2.0,
                horas_perdi=16.0,
                horas_dia=8.0,
                setor="PRODUCAO",
                centro_custo="CC-01",
                cid="J06.9",
            ),
            dict(
                nomecompleto="FUNC DELTA",
                matricula="M400",
                dias_atestados=5.0,
                horas_perdi=0.0,  # forces estimated hours path
                horas_dia=8.0,
                setor="LOGISTICA",
                centro_custo="CC-X",
                cid="A09",
            ),
        ],
    )

    # --- Client 2 current (improved severity) ---
    _seed_month(
        db,
        client_id=2,
        mes="2026-05",
        rows=[
            dict(
                nomecompleto="FUNC ALPHA",
                matricula="M100",
                dias_atestados=1.0,
                horas_perdi=8.0,
                horas_dia=8.0,
                setor="PRODUCAO",
                centro_custo="CC-01",
                cid="M54.5",
            ),
            dict(
                nomecompleto="FUNC BETA",
                matricula="M200",
                dias_atestados=1.0,
                horas_perdi=8.0,
                horas_dia=8.0,
                setor="PRODUCAO",
                centro_custo="CC-01",
                cid="J00",
            ),
        ],
    )
    _seed_month(
        db,
        client_id=2,
        mes="2026-06",
        rows=[
            dict(
                nomecompleto="FUNC ALPHA",
                matricula="M100",
                dias_atestados=1.0,
                horas_perdi=8.0,
                horas_dia=8.0,
                setor="PRODUCAO",
                centro_custo="CC-01",
                cid="M54.5",
            ),
            dict(
                nomecompleto="FUNC EPSILON",
                matricula="M500",
                dias_atestados=2.0,
                horas_perdi=16.0,
                horas_dia=8.0,
                setor="ADMIN",
                centro_custo="CC-99",
                cid="J06.9",
            ),
        ],
    )
    _seed_month(
        db,
        client_id=2,
        mes="2026-07",
        rows=[
            dict(
                nomecompleto="FUNC BETA",
                matricula="M200",
                dias_atestados=1.0,
                horas_perdi=8.0,
                horas_dia=8.0,
                setor="PRODUCAO",
                centro_custo="CC-01",
                cid="J00",
            ),
        ],
    )

    # --- Client 4 (isolation) ---
    _seed_month(
        db,
        client_id=4,
        mes="2025-05",
        rows=[
            dict(
                nomecompleto="FUNC TENANT4",
                matricula="T900",
                dias_atestados=10.0,
                horas_perdi=80.0,
                horas_dia=8.0,
                setor="EXPEDICAO",
                centro_custo="CC-T4",
                cid="S33",
            ),
        ],
    )
    _seed_month(
        db,
        client_id=4,
        mes="2025-06",
        rows=[
            dict(
                nomecompleto="FUNC TENANT4B",
                matricula="T901",
                dias_atestados=8.0,
                horas_perdi=64.0,
                horas_dia=8.0,
                setor="EXPEDICAO",
                centro_custo="CC-T4",
                cid="S33",
            ),
        ],
    )
    _seed_month(
        db,
        client_id=4,
        mes="2025-07",
        rows=[
            dict(
                nomecompleto="FUNC TENANT4",
                matricula="T900",
                dias_atestados=6.0,
                horas_perdi=48.0,
                horas_dia=8.0,
                setor="EXPEDICAO",
                centro_custo="CC-T4",
                cid="S33",
            ),
        ],
    )
    _seed_month(
        db,
        client_id=4,
        mes="2026-05",
        rows=[
            dict(
                nomecompleto="FUNC TENANT4",
                matricula="T900",
                dias_atestados=4.0,
                horas_perdi=32.0,
                horas_dia=8.0,
                setor="EXPEDICAO",
                centro_custo="CC-T4",
                cid="S33",
            ),
        ],
    )
    _seed_month(
        db,
        client_id=4,
        mes="2026-06",
        rows=[
            dict(
                nomecompleto="FUNC TENANT4B",
                matricula="T901",
                dias_atestados=3.0,
                horas_perdi=24.0,
                horas_dia=8.0,
                setor="EXPEDICAO",
                centro_custo="CC-T4",
                cid="S33",
            ),
        ],
    )
    _seed_month(
        db,
        client_id=4,
        mes="2026-07",
        rows=[
            dict(
                nomecompleto="FUNC TENANT4",
                matricula="T900",
                dias_atestados=2.0,
                horas_perdi=16.0,
                horas_dia=8.0,
                setor="EXPEDICAO",
                centro_custo="CC-T4",
                cid="S33",
            ),
        ],
    )

    db.commit()


def seed_gap_months_fixture(db: Session) -> None:
    """Client 2 with discontinuous competencies (gap in middle)."""
    seed_clients(db, (2,))
    _seed_month(
        db,
        client_id=2,
        mes="2025-05",
        rows=[
            dict(
                nomecompleto="FUNC GAP",
                matricula="G1",
                dias_atestados=1.0,
                horas_perdi=8.0,
                horas_dia=8.0,
                setor="PRODUCAO",
                cid="J00",
            )
        ],
    )
    # skip 2025-06 intentionally
    _seed_month(
        db,
        client_id=2,
        mes="2025-07",
        rows=[
            dict(
                nomecompleto="FUNC GAP",
                matricula="G1",
                dias_atestados=1.0,
                horas_perdi=8.0,
                horas_dia=8.0,
                setor="PRODUCAO",
                cid="J00",
            )
        ],
    )
    db.commit()


def seed_incomplete_window_fixture(db: Session) -> None:
    """Only one of three expected months present."""
    seed_clients(db, (2,))
    _seed_month(
        db,
        client_id=2,
        mes="2025-05",
        rows=[
            dict(
                nomecompleto="FUNC INC",
                matricula="I1",
                dias_atestados=2.0,
                horas_perdi=16.0,
                horas_dia=8.0,
                setor="ADMIN",
                cid="A09",
            )
        ],
    )
    db.commit()


def write_temp_fixture_db(
    seeder=seed_performance_adapter_fixture,
) -> Path:
    """Write a disposable on-disk SQLite for CLI / readonly tests."""
    tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
    tmp.close()
    path = Path(tmp.name)
    db = make_file_session(path)
    try:
        seeder(db)
    finally:
        db.close()
    return path


SAMPLE_CONDITIONANTS_JSON = {
    "conditionants": [
        {
            "recomendacao_id": "rec-shadow-1",
            "decisao": "aceita",
            "status": "executada",
            "prazo": "2026-06-30",
            "barreira": "agenda_setor",
            "risco_residual": "medio",
        }
    ]
}

SAMPLE_PRODUCTIVITY_JSON = {
    "atendimentos_agendados": 40,
    "atendimentos_realizados": 32,
    "faltas": 4,
    "colaboradores_atendidos": 28,
    "retornos_realizados": 6,
    "entrevistas_tecnicas": 5,
    "acoes_coletivas": 2,
    "avaliacoes_ergonomicas": 3,
    "campanhas": 1,
    "encaminhamentos": 4,
    "planos_ativos": 3,
    "planos_concluidos": 2,
    "necessidade_estimada": 40,
}


__all__ = [
    "make_file_session",
    "make_memory_session",
    "seed_performance_adapter_fixture",
    "seed_gap_months_fixture",
    "seed_incomplete_window_fixture",
    "write_temp_fixture_db",
    "SAMPLE_CONDITIONANTS_JSON",
    "SAMPLE_PRODUCTIVITY_JSON",
]
