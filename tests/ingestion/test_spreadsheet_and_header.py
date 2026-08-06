"""Spreadsheet reader + header detection tests."""

from __future__ import annotations

import pytest

from backend.ingestion.exceptions import (
    EmptyFileError,
    FormulaRejectedError,
    LimitExceededError,
    UnsupportedFormatError,
)
from backend.ingestion.header_detector import HeaderDetector
from backend.ingestion.limits import MAX_COLUMNS, MAX_PREVIEW_ROWS
from backend.ingestion.spreadsheet_reader import SpreadsheetReader
from tests.fixtures.ingestion.builders import (
    csv_aliases_accents,
    csv_semicolon,
    csv_standard,
    csv_with_title_rows,
    make_csv_bytes,
    xlsx_bytes,
    xlsx_with_empty_and_title,
)


@pytest.fixture
def reader():
    return SpreadsheetReader()


def test_read_csv_standard(reader):
    content = reader.read(csv_standard(), filename="a.csv")
    assert content.format == "csv"
    assert content.delimiter == ","
    assert not content.sheets[0].empty
    assert content.sheets[0].col_count >= 5


def test_read_csv_semicolon(reader):
    content = reader.read(csv_semicolon(), filename="a.csv")
    assert content.delimiter == ";"


def test_read_csv_tab(reader):
    rows = [["a", "b"], ["1", "2"]]
    data = make_csv_bytes(rows, delimiter="\t")
    content = reader.read(data, filename="t.csv")
    assert content.delimiter == "\t"


def test_encoding_utf8(reader):
    data = "nome;setor\nJosé;Produção\n".encode("utf-8")
    content = reader.read(data, filename="e.csv")
    assert content.encoding in {"utf-8", "utf-8-sig"}


def test_encoding_cp1252_fallback(reader):
    data = "nome;setor\nJose;Producao\n".encode("cp1252")
    # pure ascii actually utf-8 — force latin bytes
    data = "nome\nCafé\n".encode("cp1252")
    content = reader.read(data, filename="e.csv")
    assert content.encoding in {"cp1252", "latin-1", "utf-8"}


def test_xlsx_lists_sheets(reader):
    content = reader.read(xlsx_with_empty_and_title(), filename="m.xlsx")
    names = [s.name for s in content.sheets]
    assert "Atestados" in names
    assert any(s.empty for s in content.sheets)


def test_xls_clear_error(reader):
    with pytest.raises(UnsupportedFormatError):
        reader.read(b"fake", filename="old.xls")


def test_empty_csv(reader):
    with pytest.raises(EmptyFileError):
        reader.read(b"\n\n", filename="e.csv")


def test_formula_rejected(reader):
    data = make_csv_bytes([["Nome"], ["=CMD|' /C calc'!A0"]])
    with pytest.raises(FormulaRejectedError):
        reader.read(data, filename="f.csv")


def test_too_many_columns(reader):
    row = [f"c{i}" for i in range(MAX_COLUMNS + 5)]
    data = make_csv_bytes([row, row])
    with pytest.raises(LimitExceededError):
        reader.read(data, filename="wide.csv")


def test_header_detect_standard():
    content = SpreadsheetReader().read(csv_standard(), filename="a.csv")
    det = HeaderDetector().detect(content)
    assert det.linha_cabecalho_sugerida == 0
    assert det.confianca > 0.5
    assert det.necessita_confirmacao is False or det.confianca >= 0.55


def test_header_detect_title_rows():
    content = SpreadsheetReader().read(csv_with_title_rows(), filename="a.csv")
    det = HeaderDetector().detect(content)
    assert det.linha_cabecalho_sugerida is not None
    assert det.linha_cabecalho_sugerida >= 2


def test_header_detect_xlsx_multi():
    content = SpreadsheetReader().read(xlsx_with_empty_and_title(), filename="m.xlsx")
    det = HeaderDetector().detect(content)
    assert det.aba_sugerida == "Atestados"


def test_header_aliases_sheet():
    content = SpreadsheetReader().read(csv_aliases_accents(), filename="a.csv")
    det = HeaderDetector().detect(content)
    assert det.linha_cabecalho_sugerida == 0


def test_preview_row_limit_does_not_crash():
    rows = [["Nome", "Dias"]] + [["X", "1"] for _ in range(MAX_PREVIEW_ROWS + 20)]
    data = make_csv_bytes(rows)
    content = SpreadsheetReader().read(data, filename="big.csv")
    assert len(content.sheets[0].rows) <= MAX_PREVIEW_ROWS
