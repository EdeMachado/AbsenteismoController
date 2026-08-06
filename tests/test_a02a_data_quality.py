"""
Testes A02-A — DataQualityService / IQB (shadow).

Dados exclusivamente sintéticos. Sem escrita em produção.
"""
from __future__ import annotations

import json
import re
import unittest
from datetime import date, timedelta

from sqlalchemy import text

from tests.fixtures.data_quality import (
    add_atestado,
    add_upload,
    make_test_session,
    seed_clients,
    seed_ideal_quality_fixture,
    seed_quality_problems_fixture,
    seed_variant_sector_fixture,
)
from backend.services.data_quality_service import (
    DEFAULT_IQB_WEIGHTS,
    DataQualityService,
    IQBWeights,
    analyze_data_quality,
    normalize_sector_key,
    propose_sector_label,
)
from backend.services.shadow_compare import assert_no_pii_in_payload, PiiGuardError


class TestDataQualityService(unittest.TestCase):
    def test_01_tenant_isolation(self) -> None:
        db = make_test_session()
        seed_ideal_quality_fixture(db)
        a = analyze_data_quality(db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-12")
        b = analyze_data_quality(db, client_id=4, periodo_inicio="2026-01", periodo_fim="2026-12")
        self.assertEqual(a["client_id"], 2)
        self.assertEqual(b["client_id"], 4)
        self.assertEqual(a["eventos_analisados"], 5)
        self.assertEqual(b["eventos_analisados"], 1)
        db.close()

    def test_02_missing_client_id(self) -> None:
        db = make_test_session()
        seed_ideal_quality_fixture(db)
        with self.assertRaises(ValueError):
            DataQualityService(db).analyze(client_id=None)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            DataQualityService(db).analyze(client_id=0)
        db.close()

    def test_03_invalid_period(self) -> None:
        db = make_test_session()
        seed_ideal_quality_fixture(db)
        svc = DataQualityService(db)
        with self.assertRaises(ValueError):
            svc.analyze(client_id=2, periodo_inicio="2026-6", periodo_fim="2026-06")
        with self.assertRaises(ValueError):
            svc.analyze(client_id=2, periodo_inicio="2026-06", periodo_fim="2026-01")
        db.close()

    def test_04_sector_case_variants(self) -> None:
        db = make_test_session()
        seed_variant_sector_fixture(db)
        r = analyze_data_quality(db, client_id=2, periodo_inicio="2026-02", periodo_fim="2026-02")
        keys = {x["chave_normalizada"] for x in r["padronizacao_setor"]["setores_variantes"]}
        self.assertIn("MONTAGEM", keys)
        mont = next(x for x in r["padronizacao_setor"]["setores_variantes"] if x["chave_normalizada"] == "MONTAGEM")
        self.assertGreaterEqual(mont["quantidade_variantes"], 2)
        self.assertEqual(mont["eventos"], 25)
        db.close()

    def test_05_sector_extra_spaces(self) -> None:
        self.assertEqual(normalize_sector_key("  montagem  "), "MONTAGEM")
        self.assertEqual(normalize_sector_key("Montagem"), "MONTAGEM")

    def test_06_sector_accentuation(self) -> None:
        # NFKC; comparação case-insensitive — "Líder" e "LÍDER" na mesma chave se texto igual
        self.assertEqual(
            normalize_sector_key("Pintura (Líder)"),
            normalize_sector_key("pintura (líder)"),
        )
        label = propose_sector_label("ALMOXARIFADO")
        self.assertEqual(label, "Almoxarifado")

    def test_07_semantic_sectors_not_merged(self) -> None:
        db = make_test_session()
        seed_variant_sector_fixture(db)
        r = analyze_data_quality(db, client_id=2, periodo_inicio="2026-02", periodo_fim="2026-02")
        chaves = set(r["padronizacao_setor"]["setores_variantes"] and []) 
        # Pintura vs Pintura (Líder) são chaves distintas — podem não aparecer em variantes
        # (cada uma com 1 forma). Conferir chaves_distintas >= montagem + 2 pinturas
        self.assertGreaterEqual(r["padronizacao_setor"]["chaves_distintas"], 3)
        k1 = normalize_sector_key("Pintura")
        k2 = normalize_sector_key("Pintura (Líder)")
        self.assertNotEqual(k1, k2)
        db.close()

    def test_08_centro_custo_absent(self) -> None:
        db = make_test_session()
        seed_clients(db, (2,))
        u = add_upload(db, client_id=2, mes_referencia="2026-01")
        add_atestado(db, u, centro_custo=None, matricula="M1")
        add_atestado(db, u, centro_custo=None, matricula="M2")
        db.commit()
        r = analyze_data_quality(db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01")
        self.assertEqual(r["centro_custo"]["status"], "indisponivel")
        self.assertEqual(r["centro_custo"]["preenchido"], 0)
        db.close()

    def test_09_centro_custo_filled(self) -> None:
        db = make_test_session()
        seed_ideal_quality_fixture(db)
        r = analyze_data_quality(db, client_id=2, periodo_inicio="2026-03", periodo_fim="2026-03")
        self.assertEqual(r["centro_custo"]["status"], "disponivel")
        self.assertEqual(r["centro_custo"]["cobertura_pct"], 100.0)
        self.assertGreaterEqual(r["centro_custo"]["valores_distintos"], 1)
        db.close()

    def test_10_identity_matricula(self) -> None:
        db = make_test_session()
        seed_ideal_quality_fixture(db)
        r = analyze_data_quality(db, client_id=2, periodo_inicio="2026-03", periodo_fim="2026-03")
        self.assertEqual(r["identidade"]["por_matricula"], 5)
        self.assertEqual(r["identidade"]["risco"], "baixo")
        db.close()

    def test_11_identity_cpf(self) -> None:
        db = make_test_session()
        seed_quality_problems_fixture(db)
        r = analyze_data_quality(db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01")
        self.assertGreaterEqual(r["identidade"]["por_cpf"], 1)
        db.close()

    def test_12_identity_nome(self) -> None:
        db = make_test_session()
        seed_quality_problems_fixture(db)
        r = analyze_data_quality(db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01")
        self.assertGreaterEqual(r["identidade"]["somente_por_nome"], 1)
        db.close()

    def test_13_identity_absent(self) -> None:
        db = make_test_session()
        seed_quality_problems_fixture(db)
        r = analyze_data_quality(db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01")
        self.assertGreaterEqual(r["identidade"]["sem_identificador"], 1)
        db.close()

    def test_14_hours_registered(self) -> None:
        db = make_test_session()
        seed_quality_problems_fixture(db)
        r = analyze_data_quality(db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01")
        self.assertGreaterEqual(r["horas"]["eventos_com_horas_registradas"], 1)
        db.close()

    def test_15_hours_estimable(self) -> None:
        db = make_test_session()
        seed_quality_problems_fixture(db)
        r = analyze_data_quality(db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01")
        self.assertGreaterEqual(r["horas"]["eventos_com_horas_estimaveis"], 1)
        db.close()

    def test_16_hours_unavailable(self) -> None:
        db = make_test_session()
        seed_quality_problems_fixture(db)
        r = analyze_data_quality(db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01")
        self.assertGreaterEqual(r["horas"]["eventos_sem_possibilidade_estimativa"], 1)
        self.assertIn(r["horas"]["classificacao"], ("parcial", "estimada", "insuficiente", "cobertura_completa"))
        db.close()

    def test_17_invalid_jornada(self) -> None:
        db = make_test_session()
        seed_quality_problems_fixture(db)
        r = analyze_data_quality(db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01")
        self.assertGreaterEqual(r["horas"]["jornada_invalida"], 1)
        db.close()

    def test_18_negative_days(self) -> None:
        db = make_test_session()
        seed_quality_problems_fixture(db)
        r = analyze_data_quality(db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01")
        self.assertGreaterEqual(r["dias_datas"]["dias_negativos"], 1)
        db.close()

    def test_19_null_days(self) -> None:
        db = make_test_session()
        seed_clients(db, (2,))
        u = add_upload(db, client_id=2, mes_referencia="2026-01")
        db.flush()
        db.execute(
            text(
                "INSERT INTO atestados (upload_id, matricula, dias_atestados, horas_perdi, setor) "
                "VALUES (:uid, 'MN', NULL, 8, 'X')"
            ),
            {"uid": u.id},
        )
        db.commit()
        r = analyze_data_quality(db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01")
        self.assertGreaterEqual(r["dias_datas"]["dias_nulos"], 1)
        db.close()

    def test_20_zero_days(self) -> None:
        db = make_test_session()
        seed_quality_problems_fixture(db)
        r = analyze_data_quality(db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01")
        self.assertGreaterEqual(r["dias_datas"]["dias_zero"], 1)
        db.close()

    def test_21_end_before_start(self) -> None:
        db = make_test_session()
        seed_quality_problems_fixture(db)
        r = analyze_data_quality(db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01")
        self.assertGreaterEqual(r["dias_datas"]["data_final_anterior_inicial"], 1)
        db.close()

    def test_22_future_date(self) -> None:
        db = make_test_session()
        seed_quality_problems_fixture(db)
        r = analyze_data_quality(db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01")
        self.assertGreaterEqual(r["dias_datas"]["data_futura"], 1)
        db.close()

    def test_23_cid_absent(self) -> None:
        db = make_test_session()
        seed_quality_problems_fixture(db)
        r = analyze_data_quality(db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01")
        self.assertGreaterEqual(r["cid"]["ausentes"], 1)
        db.close()

    def test_24_cid_malformed(self) -> None:
        db = make_test_session()
        seed_quality_problems_fixture(db)
        r = analyze_data_quality(db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01")
        self.assertGreaterEqual(r["cid"]["mal_formatados"], 1)
        db.close()

    def test_25_multiple_uploads_same_competence(self) -> None:
        db = make_test_session()
        seed_quality_problems_fixture(db)
        r = analyze_data_quality(db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01")
        self.assertGreaterEqual(
            r["rastreabilidade"]["uploads_por_competencia"]["competencias_com_mais_de_um_upload"],
            1,
        )
        db.close()

    def test_26_upload_without_period(self) -> None:
        db = make_test_session()
        seed_clients(db, (2,))
        db.execute(
            text(
                "INSERT INTO uploads (client_id, filename, mes_referencia, total_registros) "
                "VALUES (2, 'nop.xlsx', '', 0)"
            )
        )
        db.flush()
        uid = db.execute(text("SELECT id FROM uploads WHERE filename='nop.xlsx'")).scalar()
        db.execute(
            text(
                "INSERT INTO atestados (upload_id, matricula, dias_atestados, horas_perdi, setor) "
                "VALUES (:uid, 'M1', 1, 8, 'X')"
            ),
            {"uid": uid},
        )
        db.commit()
        # Sem filtro de período: inclui upload vazio e conta
        r = analyze_data_quality(db, client_id=2)
        self.assertGreaterEqual(r["completude"]["sem_periodo_referencia"]["count"], 1)
        db.close()

    def test_27_iqb_ideal_near_100(self) -> None:
        db = make_test_session()
        seed_ideal_quality_fixture(db)
        r = analyze_data_quality(
            db,
            client_id=2,
            periodo_inicio="2026-03",
            periodo_fim="2026-03",
            reference_date=date(2026, 6, 20),
        )
        self.assertGreaterEqual(r["iqb"], 85.0)
        self.assertIn(r["classificacao"], ("excelente", "boa"))
        db.close()

    def test_28_iqb_reduced_by_absence(self) -> None:
        db = make_test_session()
        seed_quality_problems_fixture(db)
        ideal = make_test_session()
        seed_ideal_quality_fixture(ideal)
        r_bad = analyze_data_quality(db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01")
        r_good = analyze_data_quality(
            ideal, client_id=2, periodo_inicio="2026-03", periodo_fim="2026-03",
            reference_date=date(2026, 6, 20),
        )
        self.assertLess(r_bad["iqb"], r_good["iqb"])
        db.close()
        ideal.close()

    def test_29_weights_sum_100(self) -> None:
        self.assertAlmostEqual(sum(DEFAULT_IQB_WEIGHTS.values()), 100.0)
        IQBWeights().validate()
        with self.assertRaises(ValueError):
            IQBWeights(completude=50, consistencia=50, padronizacao=50).validate()

    def test_30_no_pii_in_output(self) -> None:
        db = make_test_session()
        seed_quality_problems_fixture(db)
        r = analyze_data_quality(db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01")
        assert_no_pii_in_payload(r)
        blob = json.dumps(r, ensure_ascii=False)
        self.assertNotIn("mat:", blob)
        self.assertNotIn("cpf:", blob)
        for banned in ("SO NOME", "COM CPF", "529.982.247-25", "INVDATE", "FUNCIONARIO"):
            self.assertNotIn(banned, blob)
        db.close()

    def test_31_aggregates_preserve_event_totals(self) -> None:
        db = make_test_session()
        seed_variant_sector_fixture(db)
        r = analyze_data_quality(db, client_id=2, periodo_inicio="2026-02", periodo_fim="2026-02")
        n = r["eventos_analisados"]
        self.assertEqual(r["completude"]["eventos"], n)
        # fixture: 25 montagem + 1 pintura + 1 pintura líder = 27
        self.assertEqual(n, 27)
        mont = next(
            x
            for x in r["padronizacao_setor"]["setores_variantes"]
            if x["chave_normalizada"] == "MONTAGEM"
        )
        self.assertEqual(mont["eventos"], 25)
        db.close()

    def test_32_read_only_session(self) -> None:
        db = make_test_session()
        seed_ideal_quality_fixture(db)
        svc = DataQualityService(db)
        original = svc.db
        before = db.execute(text("SELECT COUNT(*) FROM atestados")).scalar()
        svc.analyze(client_id=2, periodo_inicio="2026-03", periodo_fim="2026-03")
        after = db.execute(text("SELECT COUNT(*) FROM atestados")).scalar()
        self.assertIs(svc.db, original)
        self.assertEqual(before, after)
        db.close()

    def test_sugestoes_without_sensitive_values(self) -> None:
        db = make_test_session()
        seed_variant_sector_fixture(db)
        r = analyze_data_quality(db, client_id=2, periodo_inicio="2026-02", periodo_fim="2026-02")
        self.assertTrue(any(s["tipo"] == "SETOR_VARIANTE" for s in r["sugestoes"]))
        for s in r["sugestoes"]:
            self.assertFalse(s["aplicacao_automatica"])
            self.assertNotIn("sql", json.dumps(s).lower())
        db.close()

    def test_cid_suppression_small_groups(self) -> None:
        db = make_test_session()
        seed_clients(db, (2,))
        u = add_upload(db, client_id=2, mes_referencia="2026-01")
        for i in range(5):
            add_atestado(db, u, matricula=f"J{i}", cid="J00", nomecompleto=f"J{i}")
        add_atestado(db, u, matricula="M1", cid="M54", nomecompleto="M1")
        db.commit()
        r = analyze_data_quality(db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01")
        labels = {x["grupo_alfabetico_cid"] for x in r["cid"]["distribuicao_grupo_alfabetico"]}
        self.assertIn("J", labels)
        self.assertIn("GRUPO_SUPRIMIDO", labels)
        self.assertNotIn("M", labels)
        db.close()


if __name__ == "__main__":
    unittest.main()
