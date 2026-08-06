"""Normalization + fingerprint tests."""

from __future__ import annotations

from datetime import date

from backend.ingestion.file_fingerprint_service import FileFingerprintService
from backend.ingestion.normalization_service import NormalizationService


def test_trim_and_spaces():
    n = NormalizationService().normalize_field("nomecompleto", "  Ana   Teste ")
    assert n.normalized == "Ana Teste"
    assert n.original == "  Ana   Teste "


def test_empty_sentinels():
    n = NormalizationService()
    for v in ["", "N/A", "null", "-", "None"]:
        assert n.normalize_field("setor", v).normalized is None


def test_decimal_comma():
    n = NormalizationService().normalize_field("horas_dia", "8,5")
    assert n.normalized == 8.5


def test_jornada_out_of_range():
    n = NormalizationService().normalize_field("horas_dia", 30)
    assert n.alert == "jornada_out_of_range"


def test_date_br():
    n = NormalizationService().normalize_field("data_afastamento", "15/01/2024")
    assert n.normalized == "2024-01-15"


def test_date_iso_obj():
    n = NormalizationService().normalize_field("data_afastamento", date(2024, 1, 15))
    assert n.normalized == "2024-01-15"


def test_cid_normalize():
    n = NormalizationService().normalize_field("cid", "j06.9")
    assert n.normalized == "J06.9"


def test_competencia():
    n = NormalizationService().normalize_field("mes_referencia", "01/2024")
    assert n.normalized == "2024-01"


def test_setor_not_converted_to_cc():
    n = NormalizationService()
    s = n.normalize_field("setor", "Producao")
    assert s.normalized == "Producao"
    # separate field
    c = n.normalize_field("centro_custo", "CC-01")
    assert c.normalized == "CC-01"


def test_cpf_digits_not_required_ok():
    n = NormalizationService().normalize_field("cpf", "123.456.789-09")
    assert n.normalized == "12345678909"


def test_no_fuzzy_name_correction():
    n = NormalizationService().normalize_field("nomecompleto", "ANNA")
    assert n.normalized == "ANNA"  # no expansion/correction


def test_structural_signature_stable():
    fp = FileFingerprintService()
    a = fp.structural_signature(
        columns_normalized=["nome", "dias"],
        inferred_types=["text", "number"],
        aba="A",
        header_row=0,
    )
    b = fp.structural_signature(
        columns_normalized=["nome", "dias"],
        inferred_types=["text", "number"],
        aba="A",
        header_row=0,
    )
    assert a == b


def test_content_hash_ignores_filename_volatility():
    fp = FileFingerprintService()
    rows = [
        {
            "nomecompleto": {"normalized": "Ana"},
            "data_afastamento": {"normalized": "2024-01-10"},
            "dias_atestados": {"normalized": 2},
        }
    ]
    h1 = fp.content_hash_normalized(rows)
    h2 = fp.content_hash_normalized(rows)
    assert h1 == h2


def test_line_fingerprint_hashes_cpf():
    fp = FileFingerprintService()
    row = {
        "matricula": {"normalized": "T1"},
        "data_afastamento": {"normalized": "2024-01-10"},
        "dias_atestados": {"normalized": 1},
        "cpf": {"normalized": "12345678909"},
        "nomecompleto": {"normalized": "Ana"},
    }
    dig = fp.line_fingerprint(row)
    assert "12345678909" not in dig
    assert len(dig) == 64


def test_idempotency_key_stable():
    fp = FileFingerprintService()
    k1 = fp.idempotency_key(
        client_id=1,
        competencia="2024-01",
        content_hash="abc",
        profile_version=1,
        pipeline_version="v1",
    )
    k2 = fp.idempotency_key(
        client_id=1,
        competencia="2024-01",
        content_hash="abc",
        profile_version=1,
        pipeline_version="v1",
    )
    assert k1 == k2
