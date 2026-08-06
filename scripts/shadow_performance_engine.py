#!/usr/bin/env python3
"""Shadow runner: canonical MetricService + IQB → BioMed Performance Engine.

Requires explicit --db-path. Opens SQLite mode=ro + PRAGMA query_only=ON.
Refuses production paths. Never prints PII.

Example:
  python scripts/shadow_performance_engine.py \\
    --db-path /tmp/synthetic.sqlite \\
    --client-id 2 \\
    --baseline-inicio 2025-05 --baseline-fim 2025-07 \\
    --atual-inicio 2026-05 --atual-fim 2026-07
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.performance import ENGINE_VERSION
from backend.performance.exceptions import (
    IntegrityCheckError,
    PerformanceError,
    ProductionPathError,
    SchemaIncompatibleError,
)
from backend.performance.performance_shadow_service import (
    SHADOW_ADAPTER_VERSION,
    PerformanceShadowService,
    load_action_counts_json,
    load_conditionants_json,
    load_productivity_json,
)
from backend.performance.privacy import assert_no_pii
from backend.performance.readonly_guard import (
    assert_query_only,
    file_fingerprint,
    fingerprints_equal,
    open_sqlite_readonly,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Shadow BioMed Performance Engine (canonical adapter)"
    )
    parser.add_argument(
        "--db-path",
        required=True,
        help="Caminho explícito do SQLite (obrigatório; sem default)",
    )
    parser.add_argument("--client-id", type=int, required=True)
    parser.add_argument("--baseline-inicio", required=True, help="YYYY-MM")
    parser.add_argument("--baseline-fim", required=True, help="YYYY-MM")
    parser.add_argument("--atual-inicio", required=True, help="YYYY-MM")
    parser.add_argument("--atual-fim", required=True, help="YYYY-MM")
    parser.add_argument("--productivity-json", default=None)
    parser.add_argument("--conditionants-json", default=None)
    parser.add_argument("--acoes-json", default=None)
    parser.add_argument("--custo-programa", type=float, default=None)
    parser.add_argument("--custo-hora", type=float, default=None)
    parser.add_argument("--efetivo-trabalhadores", type=int, default=None)
    parser.add_argument("--json-out", default=None)
    args = parser.parse_args(argv)

    try:
        before = file_fingerprint(args.db_path)
    except (ProductionPathError, FileNotFoundError, IntegrityCheckError) as exc:
        raise SystemExit(str(exc)) from exc
    except Exception as exc:
        # integrity is inside open; fingerprint only needs safe path
        if isinstance(exc, ProductionPathError):
            raise SystemExit(str(exc)) from exc
        raise SystemExit(str(exc)) from exc

    db = None
    try:
        db = open_sqlite_readonly(args.db_path)
        assert_query_only(db)

        prod = load_productivity_json(args.productivity_json)
        conds = load_conditionants_json(args.conditionants_json)
        acoes = load_action_counts_json(args.acoes_json)

        service = PerformanceShadowService(db, db_sha256=str(before["sha256"]))
        result = service.analyze(
            client_id=args.client_id,
            baseline_inicio=args.baseline_inicio,
            baseline_fim=args.baseline_fim,
            atual_inicio=args.atual_inicio,
            atual_fim=args.atual_fim,
            efetivo_trabalhadores=args.efetivo_trabalhadores,
            productivity=prod,
            conditionants=conds,
            acoes=acoes,
            custo_programa=args.custo_programa,
            custo_hora=args.custo_hora,
            fonte_custos="cli_opcional" if args.custo_programa is not None else "nao_informada",
        )
        payload = result.to_dict()
        payload["cli"] = {
            "engine_version": ENGINE_VERSION,
            "adapter_version": SHADOW_ADAPTER_VERSION,
            "db_sha256": before["sha256"],
            "db_basename": before["path_basename"],
            "periodos": {
                "baseline": [args.baseline_inicio, args.baseline_fim],
                "atual": [args.atual_inicio, args.atual_fim],
            },
            "readonly": True,
            "query_only": True,
        }
        assert_no_pii(payload)
        text = json.dumps(payload, ensure_ascii=False, indent=2)
        if args.json_out:
            Path(args.json_out).write_text(text, encoding="utf-8")
        print(text)
    except (ProductionPathError, IntegrityCheckError, SchemaIncompatibleError) as exc:
        raise SystemExit(str(exc)) from exc
    except PerformanceError as exc:
        raise SystemExit(f"{exc.code}: {exc}") from exc
    except Exception as exc:
        raise SystemExit(f"shadow_failed: {exc}") from exc
    finally:
        if db is not None:
            db.close()

    after = file_fingerprint(args.db_path)
    if not fingerprints_equal(before, after):
        raise SystemExit("readonly_violation: db fingerprint changed after analysis")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
