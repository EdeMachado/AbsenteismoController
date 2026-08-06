"""Operational limits for intelligent ingestion (fail-safe)."""

from __future__ import annotations

# Hard limits — tested; raise LimitExceededError when breached.
MAX_FILE_BYTES = 5 * 1024 * 1024  # 5 MiB experimental default
MAX_SHEETS = 20
MAX_PREVIEW_ROWS = 500
MAX_COLUMNS = 80
MAX_CELL_CHARS = 2_000
MAX_CSV_LINES_SCAN = 5_000
PREVIEW_TIMEOUT_SECONDS = 30

ALLOWED_EXTENSIONS = frozenset({".xlsx", ".csv"})
# .xls intentionally unsupported without xlrd — clear error path.
REJECTED_EXTENSIONS = frozenset({".xls", ".xlsm", ".xlsb", ".xltm", ".exe", ".zip", ".rar"})

ALLOWED_MIME_HINTS = frozenset(
    {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
        "text/csv",
        "text/plain",
        "application/csv",
        "application/octet-stream",
    }
)

EMPTY_SENTINELS = frozenset(
    {
        "",
        "null",
        "none",
        "n/a",
        "na",
        "-",
        "--",
        "nil",
        "#n/a",
        "#null!",
    }
)
