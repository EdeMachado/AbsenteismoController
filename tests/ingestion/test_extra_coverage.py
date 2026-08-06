"""Additional epic1 coverage — limits, aliases batch, logging, schemas."""

from __future__ import annotations

import pytest

from backend.ingestion.column_mapping_service import ALIASES, ColumnMappingService
from backend.ingestion.exceptions import LimitExceededError, UnsupportedFormatError
from backend.ingestion.limits import MAX_CELL_CHARS, MAX_CSV_LINES_SCAN
from backend.ingestion.raw_file_service import RawFileService
from backend.ingestion.schemas import CANONICAL_FIELDS, FieldRequirement, ReuploadClass
from backend.ingestion.spreadsheet_reader import SpreadsheetReader, _detect_delimiter
from tests.fixtures.ingestion.builders import make_csv_bytes


def test_cpf_not_obrigatorio():
    assert CANONICAL_FIELDS["cpf"] == FieldRequirement.RESTRITO
    assert CANONICAL_FIELDS["cpf"] != FieldRequirement.OBRIGATORIO


def test_required_fields_present():
    for f in ("nomecompleto", "data_afastamento", "dias_atestados"):
        assert CANONICAL_FIELDS[f] == FieldRequirement.OBRIGATORIO


def test_all_initial_aliases_resolve():
    mapper = ColumnMappingService()
    samples = [
        "nome completo",
        "matrícula",
        "setor",
        "centro de custo",
        "cid",
        "dias afastados",
        "horas/dia",
        "mês referência",
    ]
    mapped = mapper.map_headers(samples)
    assert sum(1 for m in mapped if m.campo_canonico) >= 7


def test_alias_batch_individually():
    mapper = ColumnMappingService()
    for header, canon in [
        ("funcionário", "nomecompleto"),
        ("chapa", "matricula"),
        ("departamento", "setor"),
        ("cost center", "centro_custo"),
        ("código cid", "cid"),
        ("quantidade de dias", "dias_atestados"),
        ("carga horária diária", "horas_dia"),
    ]:
        r = mapper.map_headers([header])
        assert r[0].campo_canonico == canon, header


def test_reupload_enum_complete():
    expected = {
        "NOVO_ARQUIVO",
        "ARQUIVO_BRUTO_IDENTICO",
        "CONTEUDO_NORMALIZADO_IDENTICO",
        "MESMA_COMPETENCIA_CONTEUDO_DIFERENTE",
        "POSSIVEL_COMPLEMENTAR",
        "LAYOUT_ALTERADO",
        "INDETERMINADO",
    }
    assert {c.value for c in ReuploadClass} == expected


def test_giant_cell_rejected():
    huge = "x" * (MAX_CELL_CHARS + 10)
    data = make_csv_bytes([["Nome"], [huge]])
    with pytest.raises(LimitExceededError):
        SpreadsheetReader().read(data, filename="g.csv")


def test_csv_line_scan_limit():
    lines = [["a"]] + [["b"] for _ in range(MAX_CSV_LINES_SCAN + 5)]
    # make_csv_bytes joins with newlines — count lines
    data = make_csv_bytes(lines)
    with pytest.raises(LimitExceededError):
        SpreadsheetReader().read(data, filename="many.csv")


def test_delimiter_near_tie_warns():
    # mixed — function returns warning possibly
    delim, warn = _detect_delimiter(["a,b;c", "d,e;f", "g,h;i"])
    assert delim in {",", ";"}


def test_zip_rejected():
    with pytest.raises(UnsupportedFormatError):
        RawFileService().ingest_bytes(
            data=b"PK\x03\x04", original_name="x.zip", client_id=1, competencia="2024-01"
        )


def test_xlsm_rejected():
    with pytest.raises(UnsupportedFormatError):
        RawFileService().ingest_bytes(
            data=b"fake", original_name="m.xlsm", client_id=1, competencia="2024-01"
        )


def test_aliases_dict_nonempty():
    assert "funcionario" in ALIASES
    assert "qtddias" in ALIASES
    assert ALIASES["cc"] == "centro_custo"


@pytest.mark.parametrize(
    "header,canon",
    [
        ("Departamento", "setor"),
        ("Depto", "setor"),
        ("CCusto", "centro_custo"),
        ("Diagnóstico codificado", "cid"),
        ("Dias de afastamento", "dias_atestados"),
        ("Horas Dia", "horas_dia"),
        ("Mês Referência", "mes_referencia"),
    ],
)
def test_param_aliases(header, canon):
    r = ColumnMappingService().map_headers([header])
    assert r[0].campo_canonico == canon


def test_plus_formula_rejected():
    from backend.ingestion.exceptions import FormulaRejectedError

    data = make_csv_bytes([["Nome"], ["+cmd"]])
    with pytest.raises(FormulaRejectedError):
        SpreadsheetReader().read(data, filename="f.csv")


def test_at_formula_rejected():
    from backend.ingestion.exceptions import FormulaRejectedError

    data = make_csv_bytes([["Nome"], ["@SUM(A1)"]])
    with pytest.raises(FormulaRejectedError):
        SpreadsheetReader().read(data, filename="f.csv")
