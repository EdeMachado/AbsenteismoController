"""
Testes A01-A — MetricService canônico endurecido (shadow / conferência).

Usa apenas dados fictícios e SQLite em memória.
Não toca banco de produção, uploads reais nem autenticação.
"""
from __future__ import annotations

import io
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from tests.fixtures.canonical_metrics import (
    add_atestado,
    add_upload,
    make_test_session,
    seed_canonical_fixture,
    seed_clients,
)
from backend.database import Base
from backend.models import Atestado, Upload
from backend.services.metric_service import (
    MetricService,
    cid_letra_inicial,
    compute_canonical_metrics,
    validate_period_range,
    worker_identity_key,
    worker_identity_parts,
)
from backend.services.shadow_compare import (
    _PRODUCTION_DB_HINT,
    PiiGuardError,
    assert_no_pii_in_payload,
    compare_shadow,
    cpf_check_digits_valid,
    find_pii_issues,
    open_sqlite_readonly,
)


PII_PATTERNS = [
    re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"),
    re.compile(r"FUNCIONARIO\s+(ALPHA|BETA|GAMMA|DELTA)", re.I),
    re.compile(r"\bmat:"),
    re.compile(r"\bcpf:"),
]


def _assert_no_pii(payload: dict) -> None:
    blob = json.dumps(payload, ensure_ascii=False)
    for pat in PII_PATTERNS:
        assert not pat.search(blob), f"PII vazou na saída: {pat.pattern}"
    for key in (
        "distribuicao_setor",
        "distribuicao_centro_custo",
        "distribuicao_grupo_alfabetico_cid",
    ):
        for item in payload.get(key, []):
            assert "nome" not in item
            assert "cpf" not in item
            assert "matricula" not in item


class TestCanonicalMetrics(unittest.TestCase):
    def setUp(self) -> None:
        self.db = make_test_session()
        seed_canonical_fixture(self.db)
        self.svc = MetricService(self.db)

    def tearDown(self) -> None:
        self.db.close()

    def test_01_client_a_does_not_mix_client_b(self) -> None:
        a = compute_canonical_metrics(
            self.db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-06"
        )
        b = compute_canonical_metrics(
            self.db, client_id=4, periodo_inicio="2026-01", periodo_fim="2026-06"
        )
        self.assertEqual(a["metricas"]["eventos"], 3)
        self.assertEqual(b["metricas"]["eventos"], 2)
        self.assertNotEqual(a["metricas"]["dias_perdidos"], b["metricas"]["dias_perdidos"])
        self.assertEqual(a["client_id"], 2)
        self.assertEqual(b["client_id"], 4)

    def test_02_period_filters(self) -> None:
        jan = compute_canonical_metrics(
            self.db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01"
        )
        self.assertEqual(jan["metricas"]["eventos"], 1)
        self.assertEqual(jan["metricas"]["dias_perdidos"], 2.0)

        fev_mar = compute_canonical_metrics(
            self.db, client_id=2, periodo_inicio="2026-02", periodo_fim="2026-03"
        )
        self.assertEqual(fev_mar["metricas"]["eventos"], 2)

        fora = compute_canonical_metrics(
            self.db, client_id=2, periodo_inicio="2025-01", periodo_fim="2025-12"
        )
        self.assertEqual(fora["metricas"]["eventos"], 0)

    def test_03_total_eventos(self) -> None:
        r = compute_canonical_metrics(
            self.db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-06"
        )
        self.assertEqual(r["metricas"]["eventos"], 3)
        self.assertEqual(r["metricas"]["eventos_brutos"], 3)

    def test_04_trabalhadores_unicos(self) -> None:
        r = compute_canonical_metrics(
            self.db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-06"
        )
        self.assertEqual(r["metricas"]["trabalhadores_unicos"], 2)

    def test_05_soma_dias(self) -> None:
        r = compute_canonical_metrics(
            self.db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-06"
        )
        self.assertEqual(r["metricas"]["dias_perdidos"], 6.0)

    def test_06_soma_horas_registradas(self) -> None:
        r = compute_canonical_metrics(
            self.db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-06"
        )
        self.assertEqual(r["metricas"]["horas_perdidas_registradas"], 48.0)
        self.assertEqual(r["metricas"]["horas_perdidas_estimadas"], 0.0)
        self.assertEqual(r["qualidade"]["horas"], "registrada")

    def test_07_duracao_media(self) -> None:
        r = compute_canonical_metrics(
            self.db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-06"
        )
        self.assertEqual(r["metricas"]["duracao_media_dias"], 2.0)

    def test_08_divisao_por_zero(self) -> None:
        empty = make_test_session()
        seed_clients(empty, (2,))
        add_upload(empty, client_id=2, mes_referencia="2026-01")
        empty.commit()
        r = compute_canonical_metrics(
            empty, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01"
        )
        self.assertEqual(r["metricas"]["eventos"], 0)
        self.assertIsNone(r["metricas"]["duracao_media_dias"])
        self.assertIsNone(r["metricas"]["horas_registradas_media_por_evento"])
        self.assertIsNone(r["metricas"]["dias_perdidos_por_trabalhador"])
        self.assertIsNone(r["metricas"]["eventos_por_100_trabalhadores"])
        r2 = compute_canonical_metrics(
            empty,
            client_id=2,
            periodo_inicio="2026-01",
            periodo_fim="2026-01",
            efetivo_trabalhadores=0,
        )
        self.assertIsNone(r2["metricas"]["eventos_por_100_trabalhadores"])
        self.assertEqual(r2["qualidade"]["denominador_efetivo"], "incompleto")
        empty.close()

    def test_09_setor_ausente(self) -> None:
        db = make_test_session()
        seed_clients(db, (2,))
        u = add_upload(db, client_id=2, mes_referencia="2026-01")
        add_atestado(
            db,
            u,
            nomecompleto="SEM SETOR",
            matricula="M1",
            dias_atestados=1,
            horas_perdi=8,
            setor=None,
            centro_custo="CC-A",
            cid="J00",
        )
        db.commit()
        r = compute_canonical_metrics(
            db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01"
        )
        labels = {x["setor"] for x in r["distribuicao_setor"]}
        self.assertIn("SEM_SETOR", labels)
        cc_labels = {x["centro_custo"] for x in r["distribuicao_centro_custo"]}
        self.assertIn("CC-A", cc_labels)
        self.assertNotEqual(labels, cc_labels)
        db.close()

    def test_10_cid_ausente(self) -> None:
        db = make_test_session()
        seed_clients(db, (2,))
        u = add_upload(db, client_id=2, mes_referencia="2026-01")
        add_atestado(
            db,
            u,
            nomecompleto="SEM CID",
            matricula="M2",
            dias_atestados=1,
            horas_perdi=8,
            setor="X",
            cid=None,
        )
        db.commit()
        r = compute_canonical_metrics(
            db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01"
        )
        grupos = {x["grupo_alfabetico_cid"] for x in r["distribuicao_grupo_alfabetico_cid"]}
        self.assertIn("SEM_CID", grupos)
        self.assertNotIn("distribuicao_cid_grupo", r)
        db.close()

    def test_11_duplicados_permanecem_visiveis(self) -> None:
        db = make_test_session()
        seed_clients(db, (2,))
        u1 = add_upload(db, client_id=2, mes_referencia="2026-01", filename="a.xlsx")
        u2 = add_upload(db, client_id=2, mes_referencia="2026-01", filename="b.xlsx")
        for u in (u1, u2):
            add_atestado(
                db,
                u,
                nomecompleto="DUP",
                matricula="M50",
                dias_atestados=2.0,
                horas_perdi=16.0,
                setor="S",
                cid="J00",
            )
        db.commit()
        r = compute_canonical_metrics(
            db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01"
        )
        self.assertEqual(r["metricas"]["eventos"], 2)
        self.assertEqual(r["metricas"]["dias_perdidos"], 4.0)
        self.assertEqual(r["metricas"]["trabalhadores_unicos"], 1)
        self.assertTrue(
            any("deduplic" in x.lower() or "duplic" in x.lower() for x in r["limitacoes"])
        )
        db.close()

    def test_12_ausencia_horas_registradas(self) -> None:
        db = make_test_session()
        seed_clients(db, (2,))
        u = add_upload(db, client_id=2, mes_referencia="2026-01")
        add_atestado(
            db,
            u,
            nomecompleto="SEM HORAS",
            matricula="M3",
            dias_atestados=2.0,
            horas_perdi=0,
            horas_dia=8.0,
            setor="S",
            cid="J00",
        )
        db.commit()
        r = compute_canonical_metrics(
            db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01"
        )
        self.assertEqual(r["metricas"]["horas_perdidas_registradas"], 0.0)
        self.assertEqual(r["metricas"]["horas_perdidas_estimadas"], 16.0)
        self.assertEqual(r["metricas"]["eventos_com_horas_estimadas"], 1)
        self.assertEqual(r["qualidade"]["horas"], "estimada")
        db.close()

    def test_13_valores_nulos(self) -> None:
        db = make_test_session()
        seed_clients(db, (2,))
        u = add_upload(db, client_id=2, mes_referencia="2026-01")
        db.flush()
        db.execute(
            text(
                "INSERT INTO atestados (upload_id, nomecompleto, matricula, cpf, "
                "dias_atestados, horas_perdi, horas_dia, setor, centro_custo, cid) "
                "VALUES (:uid, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)"
            ),
            {"uid": u.id},
        )
        db.commit()
        r = compute_canonical_metrics(
            db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01"
        )
        self.assertEqual(r["metricas"]["eventos_brutos"], 1)
        self.assertEqual(r["metricas"]["eventos_sem_identidade"], 1)
        self.assertEqual(r["metricas"]["eventos_com_dias_invalidos"], 1)
        self.assertEqual(r["metricas"]["dias_perdidos"], 0.0)
        self.assertEqual(r["metricas"]["eventos_sem_horas"], 1)
        db.close()

    def test_14_valores_negativos_ou_invalidos(self) -> None:
        db = make_test_session()
        seed_clients(db, (2,))
        u = add_upload(db, client_id=2, mes_referencia="2026-01")
        add_atestado(
            db,
            u,
            nomecompleto="NEG",
            matricula="M4",
            dias_atestados=-2.0,
            horas_perdi=-8.0,
            setor="S",
            cid="J00",
        )
        add_atestado(
            db,
            u,
            nomecompleto="OK",
            matricula="M5",
            dias_atestados=1.0,
            horas_perdi=8.0,
            setor="S",
            cid="J00",
        )
        db.commit()
        r = compute_canonical_metrics(
            db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01"
        )
        self.assertEqual(r["metricas"]["eventos_brutos"], 2)
        self.assertEqual(r["metricas"]["eventos_com_dias_invalidos"], 1)
        self.assertEqual(r["metricas"]["eventos_com_horas_invalidas"], 1)
        self.assertEqual(r["metricas"]["eventos_validos_para_dias"], 1)
        self.assertEqual(r["metricas"]["dias_perdidos"], 1.0)
        self.assertEqual(r["metricas"]["horas_perdidas_registradas"], 8.0)
        self.assertTrue(any("invalid" in n for n in r["qualidade"]["notas"]))
        db.close()

    def test_15_nenhum_fallback_cliente(self) -> None:
        with self.assertRaises(ValueError):
            compute_canonical_metrics(
                self.db, client_id=None, periodo_inicio="2026-01", periodo_fim="2026-01"
            )
        with self.assertRaises(ValueError):
            MetricService(self.db).compute(
                client_id=0, periodo_inicio="2026-01", periodo_fim="2026-01"
            )
        with self.assertRaises(ValueError):
            MetricService(self.db).compute(
                client_id=-1, periodo_inicio="2026-01", periodo_fim="2026-01"
            )
        r = compute_canonical_metrics(
            self.db, client_id=99, periodo_inicio="2026-01", periodo_fim="2026-06"
        )
        self.assertEqual(r["client_id"], 99)
        self.assertEqual(r["metricas"]["eventos"], 0)

    def test_16_nenhuma_pii_na_saida(self) -> None:
        r = compute_canonical_metrics(
            self.db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-06"
        )
        _assert_no_pii(r)
        report = compare_shadow(
            self.db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-06"
        )
        _assert_no_pii(report.to_dict())

    # --- novos testes de robustez ---

    def test_session_not_mutated_by_compute(self) -> None:
        original = self.svc.db
        self.svc.compute(client_id=2, periodo_inicio="2026-01", periodo_fim="2026-06")
        self.assertIs(self.svc.db, original)
        # compute não aceita db como argumento
        with self.assertRaises(TypeError):
            self.svc.compute(self.db, client_id=2)  # type: ignore[misc]

    def test_period_valid(self) -> None:
        inicio, fim = validate_period_range("2026-01", "2026-06")
        self.assertEqual(inicio, "2026-01")
        self.assertEqual(fim, "2026-06")
        r = self.svc.compute(client_id=2, periodo_inicio="2026-01", periodo_fim="2026-06")
        self.assertEqual(r.periodo.inicio, "2026-01")

    def test_period_invalid_month(self) -> None:
        with self.assertRaises(ValueError):
            validate_period_range("2026-13", "2026-14")
        with self.assertRaises(ValueError):
            self.svc.compute(client_id=2, periodo_inicio="2026-00", periodo_fim="2026-01")

    def test_period_ambiguous_format_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_period_range("2026-6", "2026-07")
        with self.assertRaises(ValueError):
            self.svc.compute(client_id=2, periodo_inicio="2026-6", periodo_fim="2026-06")

    def test_period_start_after_end(self) -> None:
        with self.assertRaises(ValueError):
            validate_period_range("2026-06", "2026-01")

    def test_period_absent_allowed(self) -> None:
        r = self.svc.compute(client_id=2)
        self.assertIsNone(r.periodo.inicio)
        self.assertIsNone(r.periodo.fim)
        self.assertGreaterEqual(r.metricas.eventos_brutos, 3)

    def test_null_mes_referencia_excluded_from_range(self) -> None:
        db = make_test_session()
        seed_clients(db, (2,))
        u_ok = add_upload(db, client_id=2, mes_referencia="2026-02")
        add_atestado(
            db, u_ok, nomecompleto="OK", matricula="M1", dias_atestados=1, horas_perdi=8
        )
        # Insere upload com referência inválida (não YYYY-MM) via SQL direto
        db.execute(
            text(
                "INSERT INTO uploads (client_id, filename, mes_referencia, total_registros) "
                "VALUES (2, 'bad.xlsx', 'INVALID', 0)"
            )
        )
        db.flush()
        bad_id = db.execute(text("SELECT id FROM uploads WHERE filename='bad.xlsx'")).scalar()
        db.execute(
            text(
                "INSERT INTO atestados (upload_id, nomecompleto, matricula, dias_atestados, horas_perdi) "
                "VALUES (:uid, 'BAD', 'M9', 99, 99)"
            ),
            {"uid": bad_id},
        )
        # Também tenta vazio
        db.execute(
            text(
                "INSERT INTO uploads (client_id, filename, mes_referencia, total_registros) "
                "VALUES (2, 'empty.xlsx', '', 0)"
            )
        )
        empty_id = db.execute(text("SELECT id FROM uploads WHERE filename='empty.xlsx'")).scalar()
        db.execute(
            text(
                "INSERT INTO atestados (upload_id, nomecompleto, matricula, dias_atestados, horas_perdi) "
                "VALUES (:uid, 'EMPTY', 'M8', 50, 50)"
            ),
            {"uid": empty_id},
        )
        db.commit()
        r = MetricService(db).compute(
            client_id=2, periodo_inicio="2026-01", periodo_fim="2026-12"
        )
        self.assertEqual(r.metricas.eventos_brutos, 1)
        self.assertEqual(r.metricas.dias_perdidos, 1.0)
        db.close()

    def test_identity_matricula_cpf_nome_absent(self) -> None:
        row_m = Atestado(upload_id=1, matricula="m10", cpf="111", nomecompleto="X")
        self.assertEqual(worker_identity_parts(row_m)[0], "matricula")
        row_c = Atestado(upload_id=1, matricula=None, cpf="123.456.789-00", nomecompleto="X")
        self.assertEqual(worker_identity_parts(row_c)[0], "cpf")
        row_n = Atestado(upload_id=1, matricula=None, cpf=None, nomecompleto="  nome x ")
        self.assertEqual(worker_identity_parts(row_n)[0], "nome")
        row_a = Atestado(upload_id=1, matricula=None, cpf=None, nomecompleto=None)
        self.assertEqual(worker_identity_parts(row_a), ("nenhum", None))

        db = make_test_session()
        seed_clients(db, (2,))
        u = add_upload(db, client_id=2, mes_referencia="2026-01")
        add_atestado(db, u, nomecompleto="A", matricula="M1", dias_atestados=1, horas_perdi=1)
        add_atestado(
            db, u, nomecompleto="B", matricula=None, cpf="999.888.777-66", dias_atestados=1, horas_perdi=1
        )
        add_atestado(
            db, u, nomecompleto="C", matricula=None, cpf=None, dias_atestados=1, horas_perdi=1
        )
        add_atestado(
            db, u, nomecompleto=None, matricula=None, cpf=None, dias_atestados=1, horas_perdi=1
        )
        db.commit()
        r = MetricService(db).compute(
            client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01"
        )
        qi = r.qualidade_identidade
        self.assertEqual(qi.metodo, "aproximado")
        self.assertEqual(qi.por_matricula, 1)
        self.assertEqual(qi.por_cpf, 1)
        self.assertEqual(qi.somente_por_nome, 1)
        self.assertEqual(qi.sem_identificador, 1)
        self.assertIn(qi.confiabilidade, ("alta", "media", "baixa"))
        payload = r.to_dict()
        blob = json.dumps(payload)
        self.assertNotIn("mat:", blob)
        self.assertNotIn("cpf:999", blob)
        db.close()

    def test_identity_fragmentation_note_no_silent_merge(self) -> None:
        db = make_test_session()
        seed_clients(db, (2,))
        u = add_upload(db, client_id=2, mes_referencia="2026-01")
        # Mesmo nome, chaves distintas (matrícula vs só nome em outro registro)
        add_atestado(
            db,
            u,
            nomecompleto="MESMA PESSOA",
            matricula="M100",
            dias_atestados=1,
            horas_perdi=8,
        )
        add_atestado(
            db,
            u,
            nomecompleto="MESMA PESSOA",
            matricula=None,
            cpf=None,
            dias_atestados=1,
            horas_perdi=8,
        )
        db.commit()
        r = MetricService(db).compute(
            client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01"
        )
        # Sem unificação: 2 trabalhadores únicos
        self.assertEqual(r.metricas.trabalhadores_unicos, 2)
        self.assertTrue(any("fragmentação" in x.lower() or "fragmentacao" in x.lower() for x in r.limitacoes))
        db.close()

    def test_cid_nomenclature_not_chapter(self) -> None:
        self.assertEqual(cid_letra_inicial("J06.9"), "J")
        self.assertEqual(cid_letra_inicial(None), "SEM_CID")
        r = compute_canonical_metrics(
            self.db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-06"
        )
        self.assertIn("distribuicao_grupo_alfabetico_cid", r)
        self.assertIn("grupo_alfabetico", r["metodologia"]["cid_agrupamento"].lower())
        self.assertIn("NÃO é capítulo", r["metodologia"]["cid_agrupamento"])
        for item in r["distribuicao_grupo_alfabetico_cid"]:
            self.assertIn("grupo_alfabetico_cid", item)
            self.assertNotIn("cid_grupo", item)
            self.assertNotIn("capitulo", item)

    def test_hours_means_separated_mixed(self) -> None:
        db = make_test_session()
        seed_clients(db, (2,))
        u = add_upload(db, client_id=2, mes_referencia="2026-01")
        add_atestado(
            db, u, nomecompleto="R", matricula="M1", dias_atestados=1, horas_perdi=10, horas_dia=8
        )
        add_atestado(
            db, u, nomecompleto="E", matricula="M2", dias_atestados=2, horas_perdi=0, horas_dia=8
        )
        add_atestado(
            db,
            u,
            nomecompleto="N",
            matricula="M3",
            dias_atestados=1,
            horas_perdi=0,
            horas_dia=0,
        )
        db.commit()
        r = MetricService(db).compute(
            client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01"
        )
        m = r.metricas
        self.assertEqual(m.eventos_com_horas_registradas, 1)
        self.assertEqual(m.eventos_com_horas_estimadas, 1)
        self.assertEqual(m.eventos_sem_horas, 1)
        self.assertEqual(m.horas_registradas_media_por_evento, 10.0)
        self.assertEqual(m.horas_estimadas_media_por_evento, 16.0)
        self.assertEqual(r.qualidade.horas, "mista")
        self.assertNotIn("horas_media_evento", r.to_dict()["metricas"])
        db.close()

    def test_suppress_small_groups_bucket(self) -> None:
        db = make_test_session()
        seed_clients(db, (2,))
        u = add_upload(db, client_id=2, mes_referencia="2026-01")
        # Setor grande: 5 trabalhadores
        for i in range(5):
            add_atestado(
                db,
                u,
                nomecompleto=f"G{i}",
                matricula=f"G{i}",
                dias_atestados=1,
                horas_perdi=8,
                setor="GRANDE",
                centro_custo="CC-G",
                cid="J00",
            )
        # Setores pequenos (1 trab cada)
        add_atestado(
            db,
            u,
            nomecompleto="P1",
            matricula="P1",
            dias_atestados=2,
            horas_perdi=8,
            setor="PEQUENO_A",
            centro_custo="CC-A",
            cid="M00",
        )
        add_atestado(
            db,
            u,
            nomecompleto="P2",
            matricula="P2",
            dias_atestados=3,
            horas_perdi=8,
            setor="PEQUENO_B",
            centro_custo="CC-B",
            cid="A00",
        )
        db.commit()
        r = MetricService(db).compute(
            client_id=2,
            periodo_inicio="2026-01",
            periodo_fim="2026-01",
            suppress_small_groups=True,
            small_group_threshold=5,
        )
        labels = {x["setor"] for x in r.distribuicao_setor}
        self.assertIn("GRANDE", labels)
        self.assertIn("GRUPO_SUPRIMIDO", labels)
        self.assertNotIn("PEQUENO_A", labels)
        self.assertNotIn("PEQUENO_B", labels)
        total_ev = sum(x["eventos"] for x in r.distribuicao_setor)
        total_dias = sum(x["dias_perdidos"] for x in r.distribuicao_setor)
        self.assertEqual(total_ev, r.metricas.eventos_brutos)
        self.assertEqual(total_dias, r.metricas.dias_perdidos)
        sup = next(x for x in r.distribuicao_setor if x["setor"] == "GRUPO_SUPRIMIDO")
        self.assertEqual(sup["grupos_suprimidos"], 2)
        self.assertEqual(sup["eventos"], 2)
        self.assertEqual(sup["dias_perdidos"], 5.0)
        self.assertEqual(r.qualidade.grupos_suprimidos_setor, 2)

        with self.assertRaises(ValueError):
            MetricService(db).compute(
                client_id=2,
                periodo_inicio="2026-01",
                periodo_fim="2026-01",
                suppress_small_groups=True,
                small_group_threshold=0,
            )
        db.close()

    def test_shadow_script_requires_explicit_source_and_no_pii(self) -> None:
        # Sem argumentos de fonte → erro
        proc = subprocess.run(
            [sys.executable, "scripts/shadow_compare_metrics.py"],
            cwd="/workspace",
            capture_output=True,
            text=True,
            env={**dict(**{k: v for k, v in __import__("os").environ.items()}), "PYTHONPATH": "/workspace"},
        )
        self.assertNotEqual(proc.returncode, 0)

        proc2 = subprocess.run(
            [
                sys.executable,
                "scripts/shadow_compare_metrics.py",
                "--fixtures",
                "--client-id",
                "2",
                "--inicio",
                "2026-01",
                "--fim",
                "2026-06",
            ],
            cwd="/workspace",
            capture_output=True,
            text=True,
            env={**dict(**{k: v for k, v in __import__("os").environ.items()}), "PYTHONPATH": "/workspace"},
        )
        self.assertEqual(proc2.returncode, 0, proc2.stderr)
        for pat in PII_PATTERNS:
            self.assertIsNone(pat.search(proc2.stdout))
        script = Path("/workspace/scripts/shadow_compare_metrics.py").read_text(encoding="utf-8")
        self.assertNotIn('default="/var/www/absenteismo', script)
        self.assertNotIn("default=_PRODUCTION_DB_HINT", script)
        self.assertIn("required=True", script)

    def test_shadow_not_imported_by_startup_and_no_prod_default(self) -> None:
        main_text = Path("/workspace/backend/main.py").read_text(encoding="utf-8")
        self.assertNotIn("shadow_compare", main_text)
        self.assertNotIn("metric_service", main_text)
        # open_sqlite_readonly exige path
        with self.assertRaises(ValueError):
            open_sqlite_readonly("")
        # arquivo temp readonly
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            engine = create_engine(f"sqlite:///{tmp.name}")
            Base.metadata.create_all(bind=engine)
            engine.dispose()
            sess = open_sqlite_readonly(tmp.name)
            try:
                # leitura ok
                sess.execute(text("SELECT 1")).scalar()
            finally:
                sess.close()

    def test_eventos_por_100_com_denominador(self) -> None:
        r = compute_canonical_metrics(
            self.db,
            client_id=2,
            periodo_inicio="2026-01",
            periodo_fim="2026-06",
            efetivo_trabalhadores=100,
        )
        self.assertEqual(r["metricas"]["eventos_por_100_trabalhadores"], 3.0)
        self.assertEqual(r["qualidade"]["denominador_efetivo"], "valido")

    def test_shadow_compare_points_differences(self) -> None:
        report = compare_shadow(
            self.db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-06"
        )
        self.assertEqual(report.legado["total_atestados"], 3)
        self.assertEqual(report.canonico["metricas"]["eventos"], 3)
        chaves_diff = {d.chave for d in report.diferencas}
        self.assertNotIn("eventos", chaves_diff)
        self.assertNotIn("dias_perdidos", chaves_diff)

    def test_zero_dias_is_valid(self) -> None:
        db = make_test_session()
        seed_clients(db, (2,))
        u = add_upload(db, client_id=2, mes_referencia="2026-01")
        add_atestado(
            db, u, nomecompleto="Z", matricula="MZ", dias_atestados=0, horas_perdi=0, horas_dia=0
        )
        db.commit()
        r = MetricService(db).compute(
            client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01"
        )
        self.assertEqual(r.metricas.eventos_validos_para_dias, 1)
        self.assertEqual(r.metricas.eventos_com_dias_invalidos, 0)
        self.assertEqual(r.metricas.dias_perdidos, 0.0)
        self.assertEqual(r.metricas.eventos_sem_horas, 1)
        db.close()

    def test_non_numeric_hours_counted_invalid(self) -> None:
        db = make_test_session()
        seed_clients(db, (2,))
        u = add_upload(db, client_id=2, mes_referencia="2026-01")
        row = add_atestado(
            db, u, nomecompleto="T", matricula="MT", dias_atestados=1, horas_perdi=0
        )
        db.commit()
        # Simula valor não numérico em memória (coluna Float no SQLite pode coerir)
        row.horas_perdi = "abc"  # type: ignore[assignment]
        # Recompute via objetos já carregados: força serviço a ler atributo
        # Inserimos via raw e lemos; melhor: monkeypatch no objeto retornado
        svc = MetricService(db)
        # Patch query result
        original = svc._base_query

        def _q(*a, **k):
            class _List:
                def all(self_inner):
                    return [row]

            return _List()

        svc._base_query = _q  # type: ignore[method-assign]
        r = svc.compute(client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01")
        self.assertEqual(r.metricas.eventos_com_horas_invalidas, 1)
        db.close()


class TestShadowPiiGuard(unittest.TestCase):
    """Guard anti-PII estruturado — sem falso positivo em agregados."""

    VALID_CPF_FORMATTED = "529.982.247-25"
    VALID_CPF_DIGITS = "52998224725"
    INVALID_11 = "12345678901"

    def test_01_valid_formatted_cpf_blocked(self) -> None:
        with self.assertRaises(PiiGuardError) as ctx:
            assert_no_pii_in_payload({"obs": self.VALID_CPF_FORMATTED})
        self.assertIn("possivel_pii_detectado_em=obs", str(ctx.exception))
        self.assertNotIn(self.VALID_CPF_DIGITS, str(ctx.exception))
        self.assertNotIn(self.VALID_CPF_FORMATTED, str(ctx.exception))

    def test_02_valid_unformatted_cpf_blocked(self) -> None:
        with self.assertRaises(PiiGuardError):
            assert_no_pii_in_payload({"obs": self.VALID_CPF_DIGITS})

    def test_03_invalid_11_digits_not_false_positive(self) -> None:
        assert_no_pii_in_payload({"obs": self.INVALID_11})

    def test_04_aggregate_int_11_digits_allowed(self) -> None:
        assert_no_pii_in_payload({"metricas": {"eventos": 12345678901}})

    def test_05_aggregate_float_allowed(self) -> None:
        # Caso do falso positivo original: float serializado parece CPF no JSON cego
        assert_no_pii_in_payload(
            {"canonico": {"metricas": {"dias_perdidos": 123.45678901}}}
        )
        assert_no_pii_in_payload({"metricas": {"horas": 100.12345678}})

    def test_06_hours_days_deltas_allowed(self) -> None:
        assert_no_pii_in_payload(
            {
                "legado": {"total_dias_perdidos": 9876.5432, "total_horas_perdidas": 12345.6789},
                "diferencas": [{"delta": -1234.5678, "chave": "dias_perdidos"}],
            }
        )

    def test_07_internal_cpf_prefix_blocked(self) -> None:
        with self.assertRaises(PiiGuardError) as ctx:
            assert_no_pii_in_payload({"k": "cpf:12345678901"})
        self.assertEqual(ctx.exception.finding.category, "chave_interna")

    def test_08_internal_mat_prefix_blocked(self) -> None:
        with self.assertRaises(PiiGuardError) as ctx:
            assert_no_pii_in_payload({"k": "mat:ABC123"})
        self.assertEqual(ctx.exception.finding.category, "chave_interna")
        self.assertIn("mat:***", str(ctx.exception))

    def test_09_internal_nome_prefix_blocked(self) -> None:
        with self.assertRaises(PiiGuardError) as ctx:
            assert_no_pii_in_payload({"k": "nome:FULANO"})
        self.assertEqual(ctx.exception.finding.category, "chave_interna")

    def test_10_suspicious_cpf_field_blocked(self) -> None:
        with self.assertRaises(PiiGuardError) as ctx:
            assert_no_pii_in_payload({"cpf": "qualquer"})
        self.assertEqual(ctx.exception.finding.category, "campo_suspeito")
        self.assertIn("possivel_pii_detectado_em=cpf", str(ctx.exception))

    def test_11_methodology_mentions_cpf_column_allowed(self) -> None:
        assert_no_pii_in_payload(
            {
                "metodologia": {
                    "identidade_trabalhador": (
                        "aproximado — usa campo cpf se presente; "
                        "não expõe o valor individual."
                    ),
                    "campo_dias": "dias_atestados",
                },
                "qualidade_identidade": {"por_cpf": 3, "metodo": "aproximado"},
            }
        )

    def test_12_full_synthetic_canonical_payload_allowed(self) -> None:
        db = make_test_session()
        seed_canonical_fixture(db)
        report = compare_shadow(
            db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-06"
        )
        assert_no_pii_in_payload(report.to_dict())
        # floats que antes quebravam o guard cego
        payload = report.to_dict()
        payload["canonico"]["metricas"]["dias_perdidos"] = 123.45678901
        payload["legado"]["total_horas_perdidas"] = 100.12345678
        assert_no_pii_in_payload(payload)
        db.close()

    def test_13_distribution_with_individual_name_blocked(self) -> None:
        with self.assertRaises(PiiGuardError) as ctx:
            assert_no_pii_in_payload(
                {
                    "distribuicao_setor": [
                        {"setor": "PRODUCAO", "eventos": 1, "nome": "FULANO DE TAL"}
                    ]
                }
            )
        self.assertIn("nome", ctx.exception.finding.path)

    def test_14_detector_masks_without_revealing_pii(self) -> None:
        findings = find_pii_issues({"dado": self.VALID_CPF_FORMATTED})
        self.assertEqual(len(findings), 1)
        msg = findings[0].as_message()
        self.assertIn("possivel_pii_detectado_em=dado", msg)
        self.assertIn("categoria=", msg)
        self.assertIn("tipo=str", msg)
        self.assertIn("valor_mascarado=***.***.***-**", msg)
        self.assertNotIn("529", msg)
        self.assertNotIn(self.VALID_CPF_DIGITS, msg)
        self.assertTrue(cpf_check_digits_valid(self.VALID_CPF_DIGITS))


if __name__ == "__main__":
    unittest.main()
