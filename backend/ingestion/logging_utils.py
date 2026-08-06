"""Structured logging helpers without PII."""

from __future__ import annotations

import logging
import time
import uuid
from contextlib import contextmanager
from typing import Any, Iterator

logger = logging.getLogger("ingestion")


def new_correlation_id() -> str:
    return uuid.uuid4().hex


def partial_hash(full_hash: str, n: int = 12) -> str:
    return (full_hash or "")[:n]


def safe_log(event: str, **fields: Any) -> None:
    """Log structured fields; callers must never pass PII keys."""
    banned = {"nome", "cpf", "matricula", "cid", "token", "password", "senha", "content", "bytes"}
    clean = {k: v for k, v in fields.items() if k.lower() not in banned}
    logger.info("ingestion_event=%s %s", event, " ".join(f"{k}={v}" for k, v in clean.items()))


@contextmanager
def timed_step(correlation_id: str, step: str, **extra: Any) -> Iterator[dict[str, Any]]:
    started = time.perf_counter()
    payload: dict[str, Any] = {"correlation_id": correlation_id, "step": step, **extra}
    try:
        yield payload
        payload["status"] = "ok"
    except Exception as exc:  # noqa: BLE001 — categorized at boundary
        payload["status"] = "error"
        payload["error_type"] = type(exc).__name__
        raise
    finally:
        payload["duration_ms"] = round((time.perf_counter() - started) * 1000, 2)
        safe_log("step", **payload)
