"""Synthetic ingestion fixtures — no real PII / no real tenant data."""

from __future__ import annotations

import csv
import io
from pathlib import Path

from openpyxl import Workbook

FIXTURE_DIR = Path(__file__).resolve().parent


def make_csv_bytes(
    rows: list[list[str]],
    *,
    delimiter: str = ",",
    encoding: str = "utf-8",
) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=delimiter)
    for row in rows:
        writer.writerow(row)
    return buf.getvalue().encode(encoding)


def sample_atestado_rows() -> list[list[str]]:
    """Synthetic workers — fictional names/ids only."""
    return [
        ["Nome Completo", "Matricula", "Setor", "Centro de Custo", "CID", "Data Afastamento", "Dias", "Horas Dia"],
        ["Ana Teste", "T1001", "Producao", "CC-01", "J06.9", "2024-01-10", "2", "8"],
        ["Bruno Exemplo", "T1002", "Administrativo", "CC-02", "M54.5", "2024-01-12", "1", "8,5"],
        ["Carla Demo", "T1003", "Producao", "CC-01", "J00", "2024-01-15", "3", "8"],
    ]


def csv_standard() -> bytes:
    return make_csv_bytes(sample_atestado_rows())


def csv_semicolon() -> bytes:
    return make_csv_bytes(sample_atestado_rows(), delimiter=";")


def csv_with_title_rows() -> bytes:
    rows = [
        ["Relatorio Mensal Sintetico"],
        ["Competencia 2024-01"],
        [],
        *sample_atestado_rows(),
    ]
    return make_csv_bytes(rows)


def csv_aliases_accents() -> bytes:
    rows = [
        ["Funcionário", "Chapa", "Área", "CC", "Código CID", "Data Início", "Qtd Dias", "Jornada"],
        ["Diego Fixture", "T2001", "Logística", "CC-09", "S93.4", "15/01/2024", "2", "8"],
    ]
    return make_csv_bytes(rows)


def xlsx_bytes(sheets: dict[str, list[list[object]]] | None = None) -> bytes:
    wb = Workbook()
    wb.remove(wb.active)
    sheets = sheets or {"Atestados": sample_atestado_rows()}
    for name, rows in sheets.items():
        ws = wb.create_sheet(name)
        for r in rows:
            ws.append(list(r))
    bio = io.BytesIO()
    wb.save(bio)
    return bio.getvalue()


def xlsx_with_empty_and_title() -> bytes:
    return xlsx_bytes(
        {
            "Vazia": [],
            "Capa": [["Titulo Interno"], ["Ignorar"]],
            "Atestados": [
                ["Empresa Sintetica"],
                [],
                *sample_atestado_rows(),
            ],
        }
    )


def write_fixture_files() -> None:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    (FIXTURE_DIR / "sample_standard.csv").write_bytes(csv_standard())
    (FIXTURE_DIR / "sample_semicolon.csv").write_bytes(csv_semicolon())
    (FIXTURE_DIR / "sample_title_rows.csv").write_bytes(csv_with_title_rows())
    (FIXTURE_DIR / "sample_aliases.csv").write_bytes(csv_aliases_accents())
    (FIXTURE_DIR / "sample_atestados.xlsx").write_bytes(xlsx_bytes())
    (FIXTURE_DIR / "sample_multi_sheet.xlsx").write_bytes(xlsx_with_empty_and_title())


if __name__ == "__main__":
    write_fixture_files()
