#!/usr/bin/env python3
"""
Ferramenta local de comparação shadow (A01-A).

NÃO é endpoint de produção.
NÃO é importada pelo startup.
NÃO executa automaticamente ao importar o pacote.
NÃO aponta por padrão para /var/www/absenteismo/database/absenteismo.db.

Uso (fixtures sintéticas):
  PYTHONPATH=. python3 scripts/shadow_compare_metrics.py --fixtures \\
      --client-id 2 --inicio 2026-01 --fim 2026-06

Uso (SQLite explícito, somente leitura):
  PYTHONPATH=. python3 scripts/shadow_compare_metrics.py --db-path /caminho/arquivo.db \\
      --client-id 2 --inicio 2026-01 --fim 2026-06
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.services.shadow_compare import (
    _PRODUCTION_DB_HINT,
    assert_no_pii_in_payload,
    compare_shadow,
    open_sqlite_readonly,
)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Comparação shadow local (agregados apenas). "
            "Exige --fixtures ou --db-path explícito."
        )
    )
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument(
        "--fixtures",
        action="store_true",
        help="Usa banco temporário em memória com fixtures sintéticas",
    )
    src.add_argument(
        "--db-path",
        type=str,
        help="Caminho explícito para SQLite (aberto em modo leitura)",
    )
    p.add_argument("--client-id", type=int, required=True)
    p.add_argument("--inicio", type=str, default=None, help="YYYY-MM")
    p.add_argument("--fim", type=str, default=None, help="YYYY-MM")
    p.add_argument("--efetivo", type=int, default=None)
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    db = None
    try:
        if args.fixtures:
            from tests.fixtures.canonical_metrics import (
                make_test_session,
                seed_canonical_fixture,
            )

            db = make_test_session()
            seed_canonical_fixture(db)
        else:
            if not args.db_path:
                print("Erro: --db-path explícito é obrigatório", file=sys.stderr)
                return 2
            # Aviso se o path for o de produção — ainda assim só readonly e explícito
            if Path(args.db_path).resolve().as_posix() == _PRODUCTION_DB_HINT:
                print(
                    "Aviso: caminho de produção informado explicitamente; "
                    "abrindo somente leitura. Não é o default deste script.",
                    file=sys.stderr,
                )
            db = open_sqlite_readonly(args.db_path)

        report = compare_shadow(
            db,
            client_id=args.client_id,
            periodo_inicio=args.inicio,
            periodo_fim=args.fim,
            efetivo_trabalhadores=args.efetivo,
        )
        payload = report.to_dict()
        assert_no_pii_in_payload(payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    finally:
        if db is not None:
            db.close()


if __name__ == "__main__":
    raise SystemExit(main())
