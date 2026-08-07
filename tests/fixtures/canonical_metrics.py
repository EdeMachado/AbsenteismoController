"""
Fixtures sintéticas para testes do MetricService (A01-A).

Somente dados fictícios. Sem PII real.
"""
from __future__ import annotations

from typing import Iterable, List, Optional, Sequence, Tuple

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.database import Base
from backend.models import Atestado, Client, Upload


def make_test_session() -> Session:
    """Banco SQLite em memória (isolado; não toca produção)."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def seed_clients(db: Session, client_ids: Sequence[int] = (2, 4)) -> None:
    for cid in client_ids:
        db.add(
            Client(
                id=cid,
                nome=f"Cliente Ficticio {cid}",
                nome_fantasia=f"Ficticio {cid}",
            )
        )
    db.flush()


def add_upload(
    db: Session,
    *,
    client_id: int,
    mes_referencia: str,
    filename: str = "fixture.xlsx",
) -> Upload:
    upload = Upload(
        client_id=client_id,
        filename=filename,
        mes_referencia=mes_referencia,
        total_registros=0,
    )
    db.add(upload)
    db.flush()
    return upload


def add_atestado(
    db: Session,
    upload: Upload,
    *,
    nomecompleto: Optional[str] = None,
    matricula: Optional[str] = None,
    cpf: Optional[str] = None,
    dias_atestados: Optional[float] = 1.0,
    horas_perdi: Optional[float] = 8.0,
    horas_dia: Optional[float] = 8.0,
    setor: Optional[str] = None,
    centro_custo: Optional[str] = None,
    cid: Optional[str] = None,
) -> Atestado:
    row = Atestado(
        upload_id=upload.id,
        nomecompleto=nomecompleto,
        matricula=matricula,
        cpf=cpf,
        dias_atestados=dias_atestados,
        horas_perdi=horas_perdi,
        horas_dia=horas_dia,
        setor=setor,
        centro_custo=centro_custo,
        cid=cid,
    )
    db.add(row)
    return row


def seed_canonical_fixture(db: Session) -> None:
    """
    Cenário base para conferência:
    - client 2: 3 eventos em 2026-01..2026-03 (2 trabalhadores por matrícula)
    - client 4: 2 eventos (isolamento de tenant)
    """
    seed_clients(db, (2, 4))

    u2_jan = add_upload(db, client_id=2, mes_referencia="2026-01")
    u2_fev = add_upload(db, client_id=2, mes_referencia="2026-02")
    u2_mar = add_upload(db, client_id=2, mes_referencia="2026-03")
    u4_jan = add_upload(db, client_id=4, mes_referencia="2026-01")

    # Cliente 2
    add_atestado(
        db,
        u2_jan,
        nomecompleto="FUNCIONARIO ALPHA",
        matricula="M100",
        dias_atestados=2.0,
        horas_perdi=16.0,
        setor="PRODUCAO",
        centro_custo="CC-01",
        cid="J06.9",
    )
    add_atestado(
        db,
        u2_fev,
        nomecompleto="FUNCIONARIO ALPHA",
        matricula="M100",
        dias_atestados=1.0,
        horas_perdi=8.0,
        setor="PRODUCAO",
        centro_custo="CC-01",
        cid="J00",
    )
    add_atestado(
        db,
        u2_mar,
        nomecompleto="FUNCIONARIO BETA",
        matricula="M200",
        dias_atestados=3.0,
        horas_perdi=24.0,
        setor="ADMIN",
        centro_custo="CC-99",
        cid="M54.5",
    )

    # Cliente 4 (não deve vazar para client 2)
    add_atestado(
        db,
        u4_jan,
        nomecompleto="FUNCIONARIO GAMMA",
        matricula="M900",
        dias_atestados=10.0,
        horas_perdi=80.0,
        setor="LOGISTICA",
        centro_custo="CC-X",
        cid="A09",
    )
    add_atestado(
        db,
        u4_jan,
        nomecompleto="FUNCIONARIO DELTA",
        matricula="M901",
        dias_atestados=5.0,
        horas_perdi=40.0,
        setor="LOGISTICA",
        centro_custo="CC-X",
        cid="A09",
    )

    db.commit()


__all__ = [
    "make_test_session",
    "seed_clients",
    "add_upload",
    "add_atestado",
    "seed_canonical_fixture",
]
