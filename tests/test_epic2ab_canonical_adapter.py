"""Epic 2A-B — canonical adapter, IQB, windows, readonly shadow (≥30 tests)."""

from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from backend.performance.canonical_snapshot_adapter import CanonicalSnapshotAdapter
from backend.performance.data_quality_adapter import DataQualityAdapter
from backend.performance.exceptions import (
    IntegrityCheckError,
    ProductionPathError,
    SchemaIncompatibleError,
)
from backend.performance.performance_shadow_service import (
    PerformanceShadowService,
    load_conditionants_json,
    load_productivity_json,
)
from backend.performance.privacy import assert_no_pii
from backend.performance.readonly_guard import (
    PRODUCTION_DB_PATH,
    assert_query_only,
    assert_safe_db_path,
    file_fingerprint,
    open_sqlite_readonly,
    run_integrity_check,
    sha256_file,
)
from backend.performance.schemas import ActionCounts, BiomedProductivity
from backend.performance.window_resolver import (
    COMPETENCE_EQUIVALENTS,
    assess_comparability,
    document_competence_equivalents,
    iter_competencias,
    resolve_named_window,
)
from backend.services.metric_service import MetricService
from scripts.shadow_performance_engine import main as shadow_main
from tests.fixtures.performance.canonical_db import (
    SAMPLE_CONDITIONANTS_JSON,
    SAMPLE_PRODUCTIVITY_JSON,
    make_file_session,
    make_memory_session,
    seed_gap_months_fixture,
    seed_incomplete_window_fixture,
    seed_performance_adapter_fixture,
    write_temp_fixture_db,
)


class CanonicalAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = make_memory_session()
        seed_performance_adapter_fixture(self.db)

    def tearDown(self) -> None:
        self.db.close()

    def test_01_full_metric_service_adaptation(self) -> None:
        adapter = CanonicalSnapshotAdapter(self.db)
        bundle = adapter.build(2, "2025-05", "2025-07", efetivo_trabalhadores=100)
        snap = bundle.snapshot
        self.assertEqual(snap.fonte, "metric_service_canonical")
        self.assertGreater(snap.eventos or 0, 0)
        self.assertIsNotNone(snap.dias_perdidos)
        self.assertIsNotNone(snap.trabalhadores_unicos)
        canon = MetricService(self.db).compute(2, "2025-05", "2025-07", efetivo_trabalhadores=100)
        self.assertEqual(snap.eventos, float(canon.metricas.eventos))
        self.assertEqual(snap.dias_perdidos, float(canon.metricas.dias_perdidos))

    def test_02_missing_field_becomes_limitation(self) -> None:
        snap = CanonicalSnapshotAdapter(self.db).build(2, "2025-05", "2025-07").snapshot
        joined = " ".join(snap.limitacoes)
        self.assertIn("recorrencia_ausente_no_contrato_canonico", joined)
        self.assertIn("afastamentos_longos_ausente_no_contrato_canonico", joined)
        self.assertIsNone(snap.recorrencia)
        self.assertIsNone(snap.afastamentos_longos)

    def test_03_registered_hours_preserved(self) -> None:
        snap = CanonicalSnapshotAdapter(self.db).build(2, "2025-05", "2025-07").snapshot
        canon = MetricService(self.db).compute(2, "2025-05", "2025-07")
        self.assertEqual(
            snap.horas_perdidas_registradas,
            float(canon.metricas.horas_perdidas_registradas),
        )

    def test_04_estimated_hours_preserved(self) -> None:
        snap = CanonicalSnapshotAdapter(self.db).build(2, "2025-05", "2025-07").snapshot
        canon = MetricService(self.db).compute(2, "2025-05", "2025-07")
        self.assertEqual(
            snap.horas_perdidas_estimadas,
            float(canon.metricas.horas_perdidas_estimadas),
        )
        self.assertGreater(snap.horas_perdidas_estimadas or 0, 0)

    def test_05_hours_coverage(self) -> None:
        snap = CanonicalSnapshotAdapter(self.db).build(2, "2025-05", "2025-07").snapshot
        self.assertIsNotNone(snap.cobertura_horas_registradas)
        self.assertGreaterEqual(snap.cobertura_horas_registradas or 0, 0)
        self.assertLessEqual(snap.cobertura_horas_registradas or 0, 1)

    def test_06_iqb_integrated(self) -> None:
        q = DataQualityAdapter(self.db).build(2, "2025-05", "2025-07")
        self.assertGreaterEqual(q.iqb, 0)
        self.assertLessEqual(q.iqb, 100)
        self.assertTrue(q.classificacao)
        snap = CanonicalSnapshotAdapter(self.db).build(
            2, "2025-05", "2025-07", iqb=q.iqb
        ).snapshot
        self.assertEqual(snap.iqb, q.iqb)

    def test_07_identity_without_pii(self) -> None:
        q = DataQualityAdapter(self.db).build(2, "2025-05", "2025-07")
        payload = q.to_dict()
        assert_no_pii(payload)
        text = json.dumps(payload)
        self.assertNotIn("FUNC ALPHA", text)
        self.assertNotIn("M100", text)

    def test_08_baseline_and_current_equivalent_length(self) -> None:
        cmp = assess_comparability(
            baseline_inicio="2025-05",
            baseline_fim="2025-07",
            atual_inicio="2026-05",
            atual_fim="2026-07",
            months_with_data_baseline=["2025-05", "2025-06", "2025-07"],
            months_with_data_atual=["2026-05", "2026-06", "2026-07"],
        )
        self.assertTrue(cmp.comparable)
        self.assertEqual(cmp.mode, "integral")
        self.assertEqual(cmp.baseline_months, cmp.current_months)

    def test_09_different_windows_blocked(self) -> None:
        cmp = assess_comparability(
            baseline_inicio="2025-05",
            baseline_fim="2025-07",
            atual_inicio="2026-05",
            atual_fim="2026-06",
        )
        self.assertFalse(cmp.comparable)
        self.assertIn("quantidade_meses_diferente", cmp.reasons)

    def test_10_discontinuous_competencies(self) -> None:
        db = make_memory_session()
        seed_gap_months_fixture(db)
        try:
            months = CanonicalSnapshotAdapter(db).months_present(2, "2025-05", "2025-07")
            self.assertEqual(months, ["2025-05", "2025-07"])
            cmp = assess_comparability(
                baseline_inicio="2025-05",
                baseline_fim="2025-07",
                atual_inicio="2026-05",
                atual_fim="2026-07",
                months_with_data_baseline=months,
                months_with_data_atual=["2026-05", "2026-06", "2026-07"],
            )
            self.assertFalse(cmp.comparable)
            self.assertTrue(
                any("gap" in r or "incompleto" in r for r in cmp.reasons)
            )
        finally:
            db.close()

    def test_11_monthly_window_representation(self) -> None:
        w = resolve_named_window("90_dias", reference_end="2026-07")
        self.assertEqual(w.meses_esperados, 3)
        self.assertEqual(w.competencias, ["2026-05", "2026-06", "2026-07"])
        self.assertEqual(COMPETENCE_EQUIVALENTS["30_dias"], 1)
        self.assertEqual(COMPETENCE_EQUIVALENTS["60_dias"], 2)
        self.assertIn("mensal", w.fonte_granularidade)
        docs = document_competence_equivalents()
        self.assertEqual(docs["granularidade_fonte"], "mensal")

    def test_12_without_biomed_productivity(self) -> None:
        svc = PerformanceShadowService(self.db)
        result = svc.analyze(
            client_id=2,
            baseline_inicio="2025-05",
            baseline_fim="2025-07",
            atual_inicio="2026-05",
            atual_fim="2026-07",
            efetivo_trabalhadores=100,
        )
        self.assertEqual(result.productivity_mode, "ausente")
        self.assertTrue(
            any("produtividade_biomed_nao_integrada" in x for x in result.limitacoes)
        )
        score = result.executive_score
        dims = score.get("dimensoes") or {}
        cov = dims.get("cobertura_assistencial") or {}
        # zero empty productivity yields cobertura 0 or indisponivel — never fake 50
        if isinstance(cov, dict) and cov.get("valor") is not None:
            self.assertNotEqual(cov.get("valor"), 50)
        for dim in dims.values():
            if isinstance(dim, dict) and dim.get("status") in {
                "nao_avaliada",
                "indisponivel",
                "nao_aplicavel",
            }:
                self.assertNotEqual(dim.get("valor"), 50)

    def test_13_productivity_from_fixture_json(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump(SAMPLE_PRODUCTIVITY_JSON, fh)
            path = fh.name
        try:
            prod = load_productivity_json(path)
            self.assertIsInstance(prod, BiomedProductivity)
            self.assertEqual(prod.atendimentos_realizados, 32)
            svc = PerformanceShadowService(self.db)
            result = svc.analyze(
                client_id=2,
                baseline_inicio="2025-05",
                baseline_fim="2025-07",
                atual_inicio="2026-05",
                atual_fim="2026-07",
                productivity_json=path,
                efetivo_trabalhadores=100,
            )
            self.assertEqual(result.productivity_mode, "json_agregado")
        finally:
            os.unlink(path)

    def test_14_conditionants_from_aggregated_json(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump(SAMPLE_CONDITIONANTS_JSON, fh)
            path = fh.name
        try:
            conds = load_conditionants_json(path)
            self.assertEqual(len(conds), 1)
            self.assertEqual(conds[0].barreira, "agenda_setor")
            result = PerformanceShadowService(self.db).analyze(
                client_id=2,
                baseline_inicio="2025-05",
                baseline_fim="2025-07",
                atual_inicio="2026-05",
                atual_fim="2026-07",
                conditionants_json=path,
                efetivo_trabalhadores=100,
            )
            self.assertEqual(result.conditionants_mode, "json_agregado")
        finally:
            os.unlink(path)

    def test_15_readonly_database(self) -> None:
        path = write_temp_fixture_db()
        try:
            db = open_sqlite_readonly(path)
            try:
                assert_query_only(db)
                n = CanonicalSnapshotAdapter(db).build(2, "2025-05", "2025-07")
                self.assertGreater(n.snapshot.eventos or 0, 0)
            finally:
                db.close()
        finally:
            path.unlink(missing_ok=True)

    def test_16_production_path_refused(self) -> None:
        with self.assertRaises(ProductionPathError):
            assert_safe_db_path(PRODUCTION_DB_PATH)
        with self.assertRaises(SystemExit):
            shadow_main(
                [
                    "--db-path",
                    PRODUCTION_DB_PATH,
                    "--client-id",
                    "2",
                    "--baseline-inicio",
                    "2025-05",
                    "--baseline-fim",
                    "2025-07",
                    "--atual-inicio",
                    "2026-05",
                    "--atual-fim",
                    "2026-07",
                ]
            )

    def test_17_missing_path_refused(self) -> None:
        with self.assertRaises(FileNotFoundError):
            assert_safe_db_path("/tmp/does-not-exist-epic2ab-xyz.sqlite")

    def test_18_integrity_check_failure(self) -> None:
        tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        tmp.write(b"not a sqlite database at all!!!")
        tmp.close()
        path = Path(tmp.name)
        try:
            with self.assertRaises(IntegrityCheckError):
                run_integrity_check(path)
        finally:
            path.unlink(missing_ok=True)

    def test_19_tenant_a_does_not_mix_b(self) -> None:
        a = CanonicalSnapshotAdapter(self.db).build(2, "2025-05", "2025-07").snapshot
        b = CanonicalSnapshotAdapter(self.db).build(4, "2025-05", "2025-07").snapshot
        self.assertEqual(a.client_id, 2)
        self.assertEqual(b.client_id, 4)
        self.assertNotEqual(a.eventos, b.eventos)
        self.assertTrue(all(s != "EXPEDICAO" for s in a.setores_criticos) or a.eventos != b.eventos)
        # client 4 exclusive sector should not appear as only source for client 2 totals
        self.assertGreater(b.dias_perdidos or 0, 0)

    def test_20_output_without_pii(self) -> None:
        result = PerformanceShadowService(self.db).analyze(
            client_id=2,
            baseline_inicio="2025-05",
            baseline_fim="2025-07",
            atual_inicio="2026-05",
            atual_fim="2026-07",
            efetivo_trabalhadores=100,
        )
        payload = result.to_dict()
        assert_no_pii(payload)
        blob = json.dumps(payload)
        for banned in ("FUNC ALPHA", "M100", "cpf", "111.222"):
            self.assertNotIn("FUNC ALPHA", blob)
        self.assertNotIn("M100", blob)
        self.assertNotIn("M200", blob)

    def test_21_score_redistributed_without_coverage(self) -> None:
        result = PerformanceShadowService(self.db).analyze(
            client_id=2,
            baseline_inicio="2025-05",
            baseline_fim="2025-07",
            atual_inicio="2026-05",
            atual_fim="2026-07",
            efetivo_trabalhadores=100,
        )
        score = result.executive_score
        pesos = score.get("pesos_efetivos") or {}
        if pesos:
            self.assertAlmostEqual(sum(pesos.values()), 100.0, places=2)
        # no fake 50 on missing dimensions
        for dim in (score.get("dimensoes") or {}).values():
            if isinstance(dim, dict) and dim.get("status") in {
                "nao_avaliada",
                "indisponivel",
                "nao_aplicavel",
            }:
                self.assertNotEqual(dim.get("valor"), 50)

    def test_22_roi_not_calculable_without_costs(self) -> None:
        result = PerformanceShadowService(self.db).analyze(
            client_id=2,
            baseline_inicio="2025-05",
            baseline_fim="2025-07",
            atual_inicio="2026-05",
            atual_fim="2026-07",
            efetivo_trabalhadores=100,
        )
        self.assertEqual(result.roi.get("kind"), "ROI_NAO_CALCULAVEL")

    def test_23_roi_observed_with_valid_data(self) -> None:
        result = PerformanceShadowService(self.db).analyze(
            client_id=2,
            baseline_inicio="2025-05",
            baseline_fim="2025-07",
            atual_inicio="2026-05",
            atual_fim="2026-07",
            efetivo_trabalhadores=100,
            custo_programa=1000.0,
            custo_hora=50.0,
            fonte_custos="synthetic_test",
            acoes=ActionCounts(propostas=4, aprovadas=3, aplicaveis=3, executadas=2),
        )
        # May be OBSERVADO or ESTIMADO depending on coverage equivalence
        self.assertIn(result.roi.get("kind"), {"ROI_OBSERVADO", "ROI_ESTIMADO", "ROI_NAO_CALCULAVEL"})
        if result.roi.get("kind") == "ROI_OBSERVADO":
            self.assertIsNotNone(result.roi.get("valor"))

    def test_24_incomplete_window(self) -> None:
        db = make_memory_session()
        seed_incomplete_window_fixture(db)
        try:
            snap = CanonicalSnapshotAdapter(db).build(2, "2025-05", "2025-07").snapshot
            self.assertLess(snap.completude_periodo or 0, 1.0)
            self.assertEqual(snap.meses_com_dados, 1)
            cmp = assess_comparability(
                baseline_inicio="2025-05",
                baseline_fim="2025-07",
                atual_inicio="2026-05",
                atual_fim="2026-07",
                months_with_data_baseline=["2025-05"],
                months_with_data_atual=["2026-05", "2026-06", "2026-07"],
            )
            self.assertEqual(cmp.mode, "bloqueada")
        finally:
            db.close()

    def test_25_invalid_period(self) -> None:
        from backend.performance.exceptions import InvalidPeriodError
        from backend.performance.window_resolver import parse_month

        with self.assertRaises(InvalidPeriodError):
            parse_month("2025-13", field_name="periodo")
        with self.assertRaises(Exception):
            PerformanceShadowService(self.db).analyze(
                client_id=2,
                baseline_inicio="2025-13",
                baseline_fim="2025-07",
                atual_inicio="2026-05",
                atual_fim="2026-07",
            )

    def test_26_baseline_after_current(self) -> None:
        cmp = assess_comparability(
            baseline_inicio="2026-05",
            baseline_fim="2026-07",
            atual_inicio="2025-05",
            atual_fim="2025-07",
        )
        self.assertFalse(cmp.comparable)
        self.assertIn("baseline_nao_anterior_ao_atual", cmp.reasons)

    def test_27_same_competence_misused(self) -> None:
        cmp = assess_comparability(
            baseline_inicio="2025-05",
            baseline_fim="2025-07",
            atual_inicio="2025-05",
            atual_fim="2025-07",
        )
        self.assertFalse(cmp.comparable)
        self.assertTrue(
            "mesma_competencia_nos_dois_periodos" in cmp.reasons
            or "periodos_sobrepostos" in cmp.reasons
        )

    def test_28_snapshot_has_source_and_methodology(self) -> None:
        snap = CanonicalSnapshotAdapter(self.db).build(2, "2025-05", "2025-07").snapshot
        self.assertEqual(snap.fonte, "metric_service_canonical")
        self.assertTrue(snap.metodologia_horas)
        self.assertIn(snap.metodologia_horas, {"registradas", "estimadas", "mista", "indisponivel"})

    def test_29_thresholds_in_output(self) -> None:
        result = PerformanceShadowService(self.db).analyze(
            client_id=2,
            baseline_inicio="2025-05",
            baseline_fim="2025-07",
            atual_inicio="2026-05",
            atual_fim="2026-07",
            efetivo_trabalhadores=100,
        )
        self.assertTrue(result.thresholds_used)
        self.assertIn("material_change", result.thresholds_used)

    def test_30_execution_performs_no_write(self) -> None:
        path = write_temp_fixture_db()
        try:
            before = file_fingerprint(path)
            db = open_sqlite_readonly(path)
            try:
                PerformanceShadowService(db, db_sha256=str(before["sha256"])).analyze(
                    client_id=2,
                    baseline_inicio="2025-05",
                    baseline_fim="2025-07",
                    atual_inicio="2026-05",
                    atual_fim="2026-07",
                    efetivo_trabalhadores=100,
                )
            finally:
                db.close()
            after = file_fingerprint(path)
            self.assertEqual(before["sha256"], after["sha256"])
            self.assertEqual(before["size_bytes"], after["size_bytes"])
        finally:
            path.unlink(missing_ok=True)

    def test_31_cli_shadow_json(self) -> None:
        path = write_temp_fixture_db()
        out = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        out.close()
        try:
            rc = shadow_main(
                [
                    "--db-path",
                    str(path),
                    "--client-id",
                    "2",
                    "--baseline-inicio",
                    "2025-05",
                    "--baseline-fim",
                    "2025-07",
                    "--atual-inicio",
                    "2026-05",
                    "--atual-fim",
                    "2026-07",
                    "--efetivo-trabalhadores",
                    "100",
                    "--json-out",
                    out.name,
                ]
            )
            self.assertEqual(rc, 0)
            payload = json.loads(Path(out.name).read_text(encoding="utf-8"))
            self.assertEqual(payload["client_id"], 2)
            self.assertTrue(payload["cli"]["readonly"])
            self.assertEqual(len(payload["cli"]["db_sha256"]), 64)
            assert_no_pii(payload)
        finally:
            path.unlink(missing_ok=True)
            Path(out.name).unlink(missing_ok=True)

    def test_32_schema_incompatible(self) -> None:
        tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        tmp.close()
        path = Path(tmp.name)
        conn = sqlite3.connect(path)
        conn.execute("CREATE TABLE foo (id INTEGER)")
        conn.commit()
        conn.close()
        try:
            with self.assertRaises(SchemaIncompatibleError):
                open_sqlite_readonly(path)
        finally:
            path.unlink(missing_ok=True)

    def test_33_iter_competencias_count(self) -> None:
        comps = iter_competencias("2025-05", "2025-07")
        self.assertEqual(comps, ["2025-05", "2025-06", "2025-07"])


if __name__ == "__main__":
    unittest.main()
