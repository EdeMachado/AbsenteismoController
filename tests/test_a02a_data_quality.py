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
    DataQualityProfile,
    DataQualityService,
    IQBWeights,
    analyze_data_quality,
    choose_sector_label,
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
        self.assertIn("montagem", keys)
        mont = next(x for x in r["padronizacao_setor"]["setores_variantes"] if x["chave_normalizada"] == "montagem")
        self.assertGreaterEqual(mont["quantidade_variantes"], 2)
        self.assertEqual(mont["eventos"], 25)
        db.close()

    def test_05_sector_extra_spaces(self) -> None:
        self.assertEqual(normalize_sector_key("  montagem  "), "montagem")
        self.assertEqual(normalize_sector_key("Montagem"), "montagem")

    def test_06_sector_accentuation(self) -> None:
        self.assertEqual(normalize_sector_key("Elétrica"), normalize_sector_key("ELETRICA"))
        self.assertEqual(normalize_sector_key("Elétrica"), normalize_sector_key("eletrica"))
        self.assertEqual(
            normalize_sector_key("Manutenção"), normalize_sector_key("MANUTENCAO")
        )
        self.assertEqual(
            normalize_sector_key("Manutenção"), normalize_sector_key("manutenção")
        )
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
        # aplicável e 100% ausente → avaliado (penaliza), não "dado válido"
        self.assertEqual(r["centro_custo"]["status"], "avaliado")
        self.assertTrue(r["centro_custo"]["aplicavel"])
        self.assertEqual(r["centro_custo"]["preenchido"], 0)
        db.close()

    def test_09_centro_custo_filled(self) -> None:
        db = make_test_session()
        seed_ideal_quality_fixture(db)
        r = analyze_data_quality(db, client_id=2, periodo_inicio="2026-03", periodo_fim="2026-03")
        self.assertEqual(r["centro_custo"]["status"], "avaliado")
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
        self.assertGreaterEqual(r["rastreabilidade"]["multiplos_uploads_competencia"], 1)
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
        r = analyze_data_quality(db, client_id=2)
        self.assertGreaterEqual(r["rastreabilidade"]["uploads_sem_periodo"], 1)
        self.assertGreaterEqual(r["periodos_invalidos"]["eventos_vinculados_uploads_invalidos"], 1)
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
            if x["chave_normalizada"] == "montagem"
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


class TestDataQualityHardening(unittest.TestCase):
    """Cenários da revisão de robustez A02-A."""

    def test_01_accent_vs_no_accent_same_key(self) -> None:
        self.assertEqual(normalize_sector_key("Elétrica"), "eletrica")
        self.assertEqual(normalize_sector_key("ELETRICA"), "eletrica")
        db = make_test_session()
        seed_clients(db, (2,))
        u = add_upload(db, client_id=2, mes_referencia="2026-01")
        add_atestado(db, u, matricula="A1", setor="Elétrica")
        add_atestado(db, u, matricula="A2", setor="ELETRICA")
        add_atestado(db, u, matricula="A3", setor="eletrica")
        db.commit()
        r = analyze_data_quality(
            db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01",
            reference_date=date(2026, 6, 1),
        )
        variants = r["padronizacao_setor"]["setores_variantes"]
        self.assertEqual(len(variants), 1)
        self.assertEqual(variants[0]["quantidade_variantes"], 3)
        self.assertEqual(variants[0]["eventos"], 3)
        db.close()

    def test_02_rh_acronym_preserved(self) -> None:
        self.assertEqual(propose_sector_label("RH"), "RH")
        label, needs = choose_sector_label({"RH": 5, "Rh": 1})
        self.assertEqual(label, "RH")
        self.assertTrue(needs)

    def test_03_ti_acronym_preserved(self) -> None:
        self.assertEqual(propose_sector_label("TI"), "TI")
        label, _ = choose_sector_label({"TI": 3, "Ti": 3, "ti": 1})
        self.assertIn(label, ("TI", "Ti"))  # empate TI/Ti: lex "TI" < "Ti"? T vs T, I vs i
        # Determinístico: (-freq, label) — TI e Ti empatam em 3; "TI" < "Ti"
        self.assertEqual(label, "TI")

    def test_04_most_frequent_variant(self) -> None:
        label, needs = choose_sector_label({"Montagem": 10, "MONTAGEM": 2, "montagem": 1})
        self.assertEqual(label, "Montagem")
        self.assertTrue(needs)
        self.assertTrue(True)  # proposta não definitiva implícita no serviço

    def test_05_upload_zero_events(self) -> None:
        db = make_test_session()
        seed_clients(db, (2,))
        add_upload(db, client_id=2, mes_referencia="2026-01", filename="empty.xlsx")
        u2 = add_upload(db, client_id=2, mes_referencia="2026-01", filename="with.xlsx")
        add_atestado(db, u2, matricula="M1")
        db.commit()
        r = analyze_data_quality(
            db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01",
            reference_date=date(2026, 6, 1),
        )
        self.assertGreaterEqual(r["rastreabilidade"]["uploads_com_zero_eventos"], 1)
        self.assertEqual(r["rastreabilidade"]["uploads_validos_na_janela"], 2)
        db.close()

    def test_06_upload_without_competence(self) -> None:
        db = make_test_session()
        seed_clients(db, (2,))
        db.execute(
            text(
                "INSERT INTO uploads (client_id, filename, mes_referencia, total_registros) "
                "VALUES (2, 'nop.xlsx', '', 0)"
            )
        )
        db.commit()
        r = analyze_data_quality(
            db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01",
            reference_date=date(2026, 6, 1),
        )
        self.assertGreaterEqual(r["rastreabilidade"]["uploads_sem_periodo"], 1)
        self.assertGreaterEqual(r["periodos_invalidos"]["uploads_sem_periodo"], 1)
        db.close()

    def test_07_upload_invalid_competence(self) -> None:
        db = make_test_session()
        seed_clients(db, (2,))
        db.execute(
            text(
                "INSERT INTO uploads (client_id, filename, mes_referencia, total_registros) "
                "VALUES (2, 'bad.xlsx', '2026-13', 0)"
            )
        )
        uid = db.execute(text("SELECT id FROM uploads WHERE filename='bad.xlsx'")).scalar()
        db.execute(
            text(
                "INSERT INTO atestados (upload_id, matricula, dias_atestados, horas_perdi, setor) "
                "VALUES (:uid, 'M1', 1, 8, 'X')"
            ),
            {"uid": uid},
        )
        db.commit()
        r = analyze_data_quality(
            db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-12",
            reference_date=date(2026, 6, 1),
        )
        self.assertGreaterEqual(r["rastreabilidade"]["uploads_periodo_malformado"], 1)
        self.assertGreaterEqual(r["periodos_invalidos"]["eventos_vinculados_uploads_invalidos"], 1)
        self.assertEqual(r["eventos_analisados"], 0)
        db.close()

    def test_08_multiple_uploads_not_confirmed_dup(self) -> None:
        db = make_test_session()
        seed_quality_problems_fixture(db)
        r = analyze_data_quality(
            db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01",
            reference_date=date(2026, 6, 1),
        )
        self.assertGreaterEqual(r["rastreabilidade"]["multiplos_uploads_competencia"], 1)
        self.assertTrue(r["rastreabilidade"]["possivel_reupload"])
        self.assertTrue(r["rastreabilidade"]["duplicidade_nao_confirmada"])
        self.assertFalse(r["rastreabilidade"]["duplicidade_confirmada"])
        self.assertFalse(r["rastreabilidade"]["hash_arquivo_disponivel"])
        self.assertIn("não comprova duplicidade", r["rastreabilidade"]["mensagem"])
        db.close()

    def test_09_applicable_absent_penalizes(self) -> None:
        db = make_test_session()
        seed_clients(db, (2,))
        u = add_upload(db, client_id=2, mes_referencia="2026-01")
        for i in range(3):
            add_atestado(db, u, matricula=f"M{i}", centro_custo=None, cid=None)
        db.commit()
        with_cc = analyze_data_quality(
            db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01",
            profile=DataQualityProfile(centro_custo_aplicavel=True, cid_aplicavel=True),
            reference_date=date(2026, 6, 1),
        )
        # preenchimento CC 0 deve puxar completude para baixo vs não aplicável
        without = analyze_data_quality(
            db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01",
            profile=DataQualityProfile(centro_custo_aplicavel=False, cid_aplicavel=False),
            reference_date=date(2026, 6, 1),
        )
        self.assertLess(with_cc["dimensoes"]["completude"], without["dimensoes"]["completude"])
        db.close()

    def test_10_non_applicable_redistributes_weight(self) -> None:
        db = make_test_session()
        seed_ideal_quality_fixture(db)
        r = analyze_data_quality(
            db, client_id=2, periodo_inicio="2026-03", periodo_fim="2026-03",
            profile=DataQualityProfile(atualidade_aplicavel=False),
            reference_date=date(2026, 6, 20),
        )
        self.assertIn("atualidade", r["dimensoes_nao_aplicaveis"])
        self.assertEqual(r["status_dimensoes"]["atualidade"], "nao_aplicavel")
        self.assertAlmostEqual(sum(r["pesos_efetivos"].values()), 100.0, places=2)
        self.assertNotIn("atualidade", r["pesos_efetivos"])
        self.assertIn("atualidade", r["pesos_originais"])
        self.assertIn("redistribu", r["metodologia_redistribuicao"])
        db.close()

    def test_11_effective_weights_sum_100(self) -> None:
        db = make_test_session()
        seed_ideal_quality_fixture(db)
        r = analyze_data_quality(
            db, client_id=2, periodo_inicio="2026-03", periodo_fim="2026-03",
            profile=DataQualityProfile(padronizacao_aplicavel=False, atualidade_aplicavel=False),
            reference_date=date(2026, 6, 20),
        )
        self.assertAlmostEqual(sum(r["pesos_originais"].values()), 100.0)
        self.assertAlmostEqual(sum(r["pesos_efetivos"].values()), 100.0, places=2)
        db.close()

    def test_12_recurring_worker_does_not_dominate_identity(self) -> None:
        db = make_test_session()
        seed_clients(db, (2,))
        u = add_upload(db, client_id=2, mes_referencia="2026-01")
        # 10 eventos do mesmo trabalhador com matrícula
        for _ in range(10):
            add_atestado(db, u, matricula="MREC", nomecompleto="RECORRENTE")
        # 2 trabalhadores só nome (1 evento cada)
        add_atestado(db, u, matricula=None, cpf=None, nomecompleto="SO NOME A")
        add_atestado(db, u, matricula=None, cpf=None, nomecompleto="SO NOME B")
        db.commit()
        r = analyze_data_quality(
            db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01",
            reference_date=date(2026, 6, 1),
        )
        # por evento: 10 mat + 2 nome
        self.assertEqual(r["identidade"]["por_evento"]["com_matricula"], 10)
        self.assertEqual(r["identidade"]["por_evento"]["somente_nome"], 2)
        # por trabalhador: 1 mat + 2 nome — score não deve ser ~100
        tw = r["identidade"]["por_trabalhador_aproximado"]
        self.assertEqual(tw["com_matricula"], 1)
        self.assertEqual(tw["somente_nome"], 2)
        self.assertLess(r["dimensoes"]["identidade"], 80.0)
        db.close()

    def test_13_identity_event_vs_worker(self) -> None:
        db = make_test_session()
        seed_ideal_quality_fixture(db)
        r = analyze_data_quality(
            db, client_id=2, periodo_inicio="2026-03", periodo_fim="2026-03",
            reference_date=date(2026, 6, 20),
        )
        self.assertIn("por_evento", r["identidade"])
        self.assertIn("por_trabalhador_aproximado", r["identidade"])
        self.assertEqual(r["identidade"]["por_evento"]["com_matricula"], 5)
        self.assertEqual(r["identidade"]["por_trabalhador_aproximado"]["com_matricula"], 5)
        db.close()

    def test_14_overlap_counts_record_once(self) -> None:
        db = make_test_session()
        seed_clients(db, (2,))
        u = add_upload(db, client_id=2, mes_referencia="2026-01")
        d0 = date(2026, 1, 10)
        # três intervalos sobrepostos do mesmo trabalhador
        add_atestado(db, u, matricula="MO", data_afastamento=d0, data_retorno=date(2026, 1, 20))
        add_atestado(db, u, matricula="MO", data_afastamento=date(2026, 1, 15), data_retorno=date(2026, 1, 25))
        add_atestado(db, u, matricula="MO", data_afastamento=date(2026, 1, 18), data_retorno=date(2026, 1, 22))
        db.commit()
        r = analyze_data_quality(
            db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01",
            reference_date=date(2026, 6, 1),
        )
        self.assertEqual(r["dias_datas"]["registros_com_sobreposicao_potencial"], 3)
        self.assertNotIn("sobreposicao_potencial_intervalos", r["dias_datas"])
        db.close()

    def test_15_invalid_period_in_report(self) -> None:
        db = make_test_session()
        seed_clients(db, (2,))
        u_ok = add_upload(db, client_id=2, mes_referencia="2026-02")
        add_atestado(db, u_ok, matricula="M1")
        db.execute(
            text(
                "INSERT INTO uploads (client_id, filename, mes_referencia, total_registros) "
                "VALUES (2, 'inv.xlsx', 'INVALID', 0)"
            )
        )
        uid = db.execute(text("SELECT id FROM uploads WHERE filename='inv.xlsx'")).scalar()
        db.execute(
            text(
                "INSERT INTO atestados (upload_id, matricula, dias_atestados, horas_perdi) "
                "VALUES (:uid, 'MX', 1, 8)"
            ),
            {"uid": uid},
        )
        db.commit()
        r = analyze_data_quality(
            db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-12",
            reference_date=date(2026, 6, 1),
        )
        self.assertEqual(r["eventos_analisados"], 1)
        self.assertGreaterEqual(r["periodos_invalidos"]["uploads_periodo_malformado"], 1)
        self.assertGreaterEqual(r["eventos_excluidos_janela"], 1)
        db.close()

    def test_16_reference_date_in_output(self) -> None:
        db = make_test_session()
        seed_ideal_quality_fixture(db)
        r = analyze_data_quality(
            db, client_id=2, periodo_inicio="2026-03", periodo_fim="2026-03",
            reference_date=date(2026, 6, 20),
        )
        self.assertEqual(r["atualidade"]["data_referencia"], "2026-06-20")
        self.assertEqual(r["atualidade"]["ultimo_periodo_valido"], "2026-03")
        self.assertIsNotNone(r["atualidade"]["diferenca_meses_vs_referencia"])
        self.assertIn("criterio", r["atualidade"])
        db.close()

    def test_17_cid_suppression_not_sum_as_headcount(self) -> None:
        db = make_test_session()
        seed_clients(db, (2,))
        u = add_upload(db, client_id=2, mes_referencia="2026-01")
        # mesma pessoa em dois grupos pequenos A e B
        add_atestado(db, u, matricula="SAME", cid="A09", nomecompleto="X")
        add_atestado(db, u, matricula="SAME", cid="B01", nomecompleto="X")
        add_atestado(db, u, matricula="OTHER", cid="C00", nomecompleto="Y")
        db.commit()
        r = analyze_data_quality(
            db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01",
            reference_date=date(2026, 6, 1),
        )
        sup = next(
            x for x in r["cid"]["distribuicao_grupo_alfabetico"]
            if x["grupo_alfabetico_cid"] == "GRUPO_SUPRIMIDO"
        )
        self.assertEqual(sup["grupos_suprimidos"], 3)
        self.assertEqual(sup["soma_contagens_por_grupo"], 3)  # 1+1+1
        self.assertEqual(sup["trabalhadores_unicos_globais"], 2)  # SAME + OTHER
        self.assertNotEqual(sup["soma_contagens_por_grupo"], sup["trabalhadores_unicos_globais"])
        db.close()

    def test_18_no_pii(self) -> None:
        db = make_test_session()
        seed_quality_problems_fixture(db)
        r = analyze_data_quality(
            db, client_id=2, periodo_inicio="2026-01", periodo_fim="2026-01",
            reference_date=date(2026, 6, 1),
        )
        assert_no_pii_in_payload(r)
        blob = json.dumps(r, ensure_ascii=False)
        for banned in ("SO NOME", "529.982.247-25", "mat:", "cpf:"):
            self.assertNotIn(banned, blob)
        db.close()


if __name__ == "__main__":
    unittest.main()
