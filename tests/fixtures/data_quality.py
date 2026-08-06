"""
Fixtures sintéticas para o motor de qualidade A02-A (IQB).

Somente dados fictícios. Sem PII real. Sem escrita em produção.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional, Sequence

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.database import Base
from backend.models import Atestado, Client, Upload


def make_test_session() -> Session:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)()


def seed_clients(db: Session, client_ids: Sequence[int] = (2, 4)) -> None:
    for cid in client_ids:
        db.add(Client(id=cid, nome=f"Cliente Ficticio {cid}", nome_fantasia=f"Ficticio {cid}"))
    db.flush()


def add_upload(
    db: Session,
    *,
    client_id: int,
    mes_referencia: str,
    filename: str = "fixture.xlsx",
    data_upload: Optional[datetime] = None,
) -> Upload:
    upload = Upload(
        client_id=client_id,
        filename=filename,
        mes_referencia=mes_referencia,
        total_registros=0,
        data_upload=data_upload or datetime(2026, 6, 15, 12, 0, 0),
    )
    db.add(upload)
    db.flush()
    return upload


def add_atestado(
    db: Session,
    upload: Upload,
    *,
    nomecompleto: Optional[str] = "FUNCIONARIO SYNTH",
    matricula: Optional[str] = "M001",
    cpf: Optional[str] = None,
    dias_atestados: Optional[float] = 1.0,
    horas_perdi: Optional[float] = 8.0,
    horas_dia: Optional[float] = 8.0,
    setor: Optional[str] = "Montagem",
    centro_custo: Optional[str] = "CC-01",
    cid: Optional[str] = "J06.9",
    data_afastamento: Optional[date] = None,
    data_retorno: Optional[date] = None,
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
        data_afastamento=data_afastamento or date(2026, 3, 10),
        data_retorno=data_retorno or date(2026, 3, 11),
    )
    db.add(row)
    return row


def seed_ideal_quality_fixture(db: Session) -> None:
    """Fixture com qualidade alta (IQB próximo de 100) para client_id=2."""
    seed_clients(db, (2, 4))
    u = add_upload(db, client_id=2, mes_referencia="2026-03", filename="ideal.xlsx")
    for i in range(5):
        add_atestado(
            db,
            u,
            nomecompleto=f"FUNCIONARIO IDEAL {i}",
            matricula=f"MID{i:03d}",
            dias_atestados=1.0,
            horas_perdi=8.0,
            horas_dia=8.0,
            setor="Montagem",
            centro_custo="CC-01",
            cid="J06.9",
            data_afastamento=date(2026, 3, 10 + i),
            data_retorno=date(2026, 3, 11 + i),
        )
    # Tenant B isolado
    u4 = add_upload(db, client_id=4, mes_referencia="2026-03", filename="other.xlsx")
    add_atestado(
        db,
        u4,
        nomecompleto="OUTRO TENANT",
        matricula="MX999",
        setor="Logistica",
        centro_custo="CC-X",
        cid="A09",
    )
    db.commit()


def seed_variant_sector_fixture(db: Session) -> None:
    """Variantes de setor (caixa/espaços) + setores semanticamente distintos."""
    seed_clients(db, (2,))
    u = add_upload(db, client_id=2, mes_referencia="2026-02")
    for label, n in (("Montagem", 10), ("MONTAGEM", 10), ("  montagem  ", 5)):
        for i in range(n):
            add_atestado(
                db,
                u,
                nomecompleto=f"VAR {label} {i}",
                matricula=f"V{label[:3]}{i}",
                setor=label,
                centro_custo="CC-01",
            )
    add_atestado(db, u, nomecompleto="PINT", matricula="P1", setor="Pintura", centro_custo="CC-02")
    add_atestado(
        db, u, nomecompleto="PINTL", matricula="P2", setor="Pintura (Líder)", centro_custo="CC-02"
    )
    db.commit()


def seed_quality_problems_fixture(db: Session) -> None:
    """Diversas inconsistências agregáveis para IQB reduzido."""
    seed_clients(db, (2,))
    u1 = add_upload(db, client_id=2, mes_referencia="2026-01", filename="a.xlsx")
    u2 = add_upload(db, client_id=2, mes_referencia="2026-01", filename="b.xlsx")  # reupload
    today = date.today()

    add_atestado(  # horas registradas ok
        db, u1, nomecompleto="OK", matricula="M1", setor="Soldagem", horas_perdi=8, horas_dia=8
    )
    add_atestado(  # só estimável
        db,
        u1,
        nomecompleto="EST",
        matricula="M2",
        setor="SOLDAGEM",
        horas_perdi=0,
        horas_dia=8,
        dias_atestados=2,
    )
    add_atestado(  # sem horas
        db,
        u1,
        nomecompleto="SEMH",
        matricula="M3",
        setor=None,
        centro_custo=None,
        horas_perdi=0,
        horas_dia=0,
        cid=None,
    )
    add_atestado(  # jornada inválida
        db,
        u1,
        nomecompleto="JORN",
        matricula="M4",
        horas_perdi=0,
        horas_dia=-4,
        dias_atestados=1,
    )
    add_atestado(  # dias negativos
        db,
        u1,
        nomecompleto="NEG",
        matricula="M5",
        dias_atestados=-2,
        horas_perdi=8,
    )
    add_atestado(  # dias zero
        db,
        u1,
        nomecompleto="ZERO",
        matricula="M6",
        dias_atestados=0,
        horas_perdi=0,
        horas_dia=8,
    )
    add_atestado(  # data final anterior
        db,
        u1,
        nomecompleto="INVDATE",
        matricula="M7",
        data_afastamento=date(2026, 4, 10),
        data_retorno=date(2026, 4, 1),
    )
    add_atestado(  # data futura
        db,
        u1,
        nomecompleto="FUT",
        matricula="M8",
        data_afastamento=today + timedelta(days=30),
        data_retorno=today + timedelta(days=31),
    )
    add_atestado(  # CID mal formatado
        db, u1, nomecompleto="CIDB", matricula="M9", cid="99XX"
    )
    add_atestado(  # identidade só nome
        db,
        u1,
        nomecompleto="SO NOME",
        matricula=None,
        cpf=None,
        setor="Portaria",
    )
    add_atestado(  # sem identidade
        db,
        u1,
        nomecompleto=None,
        matricula=None,
        cpf=None,
        setor="PORTARIA",
    )
    add_atestado(  # CPF
        db,
        u2,
        nomecompleto="COM CPF",
        matricula=None,
        cpf="529.982.247-25",
        setor="Almoxarifado",
    )
    add_atestado(  # divergência dias*jornada vs horas
        db,
        u2,
        nomecompleto="DIV",
        matricula="M10",
        dias_atestados=2,
        horas_dia=8,
        horas_perdi=8,  # esperado 16
        setor="ALMOXARIFADO",
    )
    db.commit()


__all__ = [
    "make_test_session",
    "seed_clients",
    "add_upload",
    "add_atestado",
    "seed_ideal_quality_fixture",
    "seed_variant_sector_fixture",
    "seed_quality_problems_fixture",
]
