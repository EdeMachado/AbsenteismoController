#!/usr/bin/env python3
"""
Ferramenta local de comparação shadow (A01-A).

Usa banco temporário + fixtures sintéticas.
NÃO é endpoint de produção. NÃO altera telas nem dados reais.

Uso:
  PYTHONPATH=. python scripts/shadow_compare_metrics.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.fixtures.canonical_metrics import make_test_session, seed_canonical_fixture
from backend.services.shadow_compare import compare_shadow


def main() -> int:
    db = make_test_session()
    try:
        seed_canonical_fixture(db)
        report = compare_shadow(
            db,
            client_id=2,
            periodo_inicio="2026-01",
            periodo_fim="2026-06",
            efetivo_trabalhadores=100,
        )
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
