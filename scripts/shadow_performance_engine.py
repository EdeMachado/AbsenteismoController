#!/usr/bin/env python3
"""Shadow runner for BioMed Performance Engine — readonly, explicit DB path, fixtures OK.

Usage examples:
  python scripts/shadow_performance_engine.py --fixture severity
  python scripts/shadow_performance_engine.py --db /path/to/temp.db --client-id 99 \\
      --readonly

Never defaults to production paths. Never prints PII.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.performance.performance_service import PerformanceService
from backend.performance.privacy import assert_no_pii
from tests.fixtures.performance.builders import (
    baseline_ok,
    conditionant_delayed,
    current_frequency_control,
    current_integral,
    current_severity_control,
    current_worsened,
    prod_good_coverage,
)


_FORBIDDEN = ("/var/www/absenteismo", "absenteismo.db")


def _refuse_prod_path(path: str | None) -> None:
    if not path:
        return
    norm = path.replace("\\", "/").lower()
    for frag in _FORBIDDEN:
        if frag in norm:
            raise SystemExit(f"refusing production-like path: {path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Shadow BioMed Performance Engine")
    parser.add_argument("--db", default=None, help="Explicit SQLite path (optional)")
    parser.add_argument("--readonly", action="store_true", help="Open DB readonly if --db set")
    parser.add_argument("--client-id", type=int, default=99)
    parser.add_argument(
        "--fixture",
        choices=["severity", "frequency", "integral", "worsened"],
        default="severity",
    )
    parser.add_argument("--json-out", default=None)
    args = parser.parse_args(argv)

    _refuse_prod_path(args.db)
    if args.db:
        # Readonly open — no writes. MetricService integration optional future.
        uri = f"file:{args.db}?mode=ro" if args.readonly else args.db
        import sqlite3

        try:
            conn = sqlite3.connect(uri, uri=True) if args.readonly else sqlite3.connect(args.db)
            conn.close()
        except sqlite3.Error as exc:
            raise SystemExit(f"cannot open db readonly/explicit: {exc}") from exc
        print(
            json.dumps(
                {
                    "warning": "db path accepted for connectivity check only; "
                    "this shadow run uses synthetic fixtures for aggregates",
                    "db": os.path.basename(args.db),
                }
            )
        )

    cur_map = {
        "severity": current_severity_control,
        "frequency": current_frequency_control,
        "integral": current_integral,
        "worsened": current_worsened,
    }
    baseline = baseline_ok()
    # Force tenant on fixtures
    from dataclasses import replace

    baseline = replace(baseline, client_id=args.client_id)
    current = replace(cur_map[args.fixture](), client_id=args.client_id)

    svc = PerformanceService(require_flag=False)
    analysis = svc.analyze(
        client_id=args.client_id,
        baseline=baseline,
        current=current,
        productivity=prod_good_coverage(),
        conditionants=[conditionant_delayed()] if args.fixture == "severity" else [],
        reference_end=current.periodo_fim,
        custo_programa=10000.0,
        custo_hora=50.0,
        fonte_custos="synthetic",
        acoes_propostas=5,
        acoes_aprovadas=3,
        acoes_executadas=2,
        acoes_pendentes=2,
        metas_atingidas=0.4,
    )
    payload = analysis.to_dict()
    assert_no_pii(payload)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.json_out:
        Path(args.json_out).write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
