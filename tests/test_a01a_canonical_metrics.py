"""
Testes A01-A — MetricService canônico (shadow / conferência).

Usa apenas dados fictícios e SQLite em memória.
Não toca banco de produção, uploads reais nem autenticação.
"""
from __future__ import annotations

import json
import re
import unittest
from typing import Any, Dict, Set

from tests.fixtures.canonical_metrics import (
    add_atestado,
    add_upload,
    make_test_session,
    seed_canonical_fixture,
    seed_clients,
)
from backend.services.metric_service import MetricService, compute_canonical_metrics, worker_identity_key
from backend.services.shadow_compare import compare_shadow
from backend.models import Atestado


PII_PATTERNS = [
    re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"),  # CPF-like
    re.compile(r"FUNCIONARIO\s+(ALPHA|BETA|GAMMA|DELTA)", re.I),
]


def _assert_no_pii(payload: Dict[str, Any]) -> None:
    blob = json.dumps(payload, ensure_ascii=False)
    for pat in PII_PATTERNS:
        assert not pat.search(blob), f"PII vazou na saída: {pat.pattern}"
    for banned in ("cpf", "matricula", "nomecompleto", "nome_funcionario", "diagnostico"):
        # chaves de metodologia podem citar nomes de campos — OK;
        # valores de métricas/distribuições não devem carregar identificadores.
        pass
    # Distribuições não devem listar nomes
    for key in ("distribuicao_setor", "distribuicao_centro_custo", "distribuicao_cid_grupo"):
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

    def test_04_trabalhadores_unicos(self) -> None:
        r = compute_canonical_metrics(
            self.db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-06"
        )
        # M100 (2 eventos) + M200 (1) => 2
        self.assertEqual(r["metricas"]["trabalhadores_unicos"], 2)

    def test_05_soma_dias(self) -> None:
        r = compute_canonical_metrics(
            self.db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-06"
        )
        self.assertEqual(r["metricas"]["dias_perdidos"], 6.0)  # 2+1+3

    def test_06_soma_horas_registradas(self) -> None:
        r = compute_canonical_metrics(
            self.db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-06"
        )
        self.assertEqual(r["metricas"]["horas_perdidas_registradas"], 48.0)  # 16+8+24
        self.assertEqual(r["metricas"]["horas_perdidas_estimadas"], 0.0)
        self.assertEqual(r["qualidade"]["horas"], "registrada")

    def test_07_duracao_media(self) -> None:
        r = compute_canonical_metrics(
            self.db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-06"
        )
        # média dos eventos com dias>0: (2+1+3)/3 = 2
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
        self.assertIsNone(r["metricas"]["horas_media_evento"])
        self.assertIsNone(r["metricas"]["dias_perdidos_por_trabalhador"])
        self.assertIsNone(r["metricas"]["eventos_por_100_trabalhadores"])
        # efetivo zero => incompleto, sem divisão
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
        self.assertNotEqual(labels, cc_labels)  # não sinônimos
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
        grupos = {x["cid_grupo"] for x in r["distribuicao_cid_grupo"]}
        self.assertIn("SEM_CID", grupos)
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
        # Sem deduplicação silenciosa: 2 eventos, dias 4
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
        self.assertEqual(r["qualidade"]["horas"], "estimada")
        # Campos separados — nunca misturados
        self.assertIn("horas_perdidas_registradas", r["metricas"])
        self.assertIn("horas_perdidas_estimadas", r["metricas"])
        db.close()

    def test_13_valores_nulos(self) -> None:
        db = make_test_session()
        seed_clients(db, (2,))
        u = add_upload(db, client_id=2, mes_referencia="2026-01")
        add_atestado(
            db,
            u,
            nomecompleto=None,
            matricula=None,
            cpf=None,
            dias_atestados=None,
            horas_perdi=None,
            horas_dia=None,
            setor=None,
            centro_custo=None,
            cid=None,
        )
        db.commit()
        r = compute_canonical_metrics(
            db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01"
        )
        self.assertEqual(r["metricas"]["eventos"], 1)
        self.assertEqual(r["metricas"]["trabalhadores_unicos"], 0)
        self.assertEqual(r["metricas"]["dias_perdidos"], 0.0)
        self.assertEqual(r["metricas"]["horas_perdidas_registradas"], 0.0)
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
        self.assertEqual(r["metricas"]["eventos"], 2)
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
                self.db, client_id=0, periodo_inicio="2026-01", periodo_fim="2026-01"
            )
        with self.assertRaises(ValueError):
            MetricService(self.db).compute(
                self.db, client_id=-1, periodo_inicio="2026-01", periodo_fim="2026-01"
            )
        # client inexistente => métricas zeradas, sem cair em client 1
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

    def test_shadow_compare_points_differences(self) -> None:
        report = compare_shadow(
            self.db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-06"
        )
        self.assertEqual(report.legado["total_atestados"], 3)
        self.assertEqual(report.canonico["metricas"]["eventos"], 3)
        # Dias e horas alinhados neste fixture (sem estimativa)
        chaves_diff = {d.chave for d in report.diferencas}
        self.assertNotIn("eventos", chaves_diff)
        self.assertNotIn("dias_perdidos", chaves_diff)

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

    def test_worker_identity_priority(self) -> None:
        row = Atestado(
            upload_id=1,
            matricula="  m10 ",
            cpf="123.456.789-00",
            nomecompleto="NOME",
        )
        self.assertEqual(worker_identity_key(row), "mat:M10")
        row2 = Atestado(upload_id=1, matricula=None, cpf="123.456.789-00", nomecompleto="NOME")
        self.assertEqual(worker_identity_key(row2), "cpf:12345678900")
        row3 = Atestado(upload_id=1, matricula=None, cpf=None, nomecompleto="  nome x ")
        self.assertEqual(worker_identity_key(row3), "nome:NOME X")


if __name__ == "__main__":
    unittest.main()
