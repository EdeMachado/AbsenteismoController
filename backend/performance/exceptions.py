"""Exceptions for BioMed Performance Engine."""

from __future__ import annotations


class PerformanceError(Exception):
    code: str = "PERFORMANCE_ERROR"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        if code:
            self.code = code
        self.message = message


class FeatureDisabledError(PerformanceError):
    code = "FEATURE_DISABLED"


class InsufficientEvidenceError(PerformanceError):
    code = "INSUFFICIENT_EVIDENCE"


class InvalidPeriodError(PerformanceError):
    code = "INVALID_PERIOD"


class PrivacyViolationError(PerformanceError):
    code = "PRIVACY_VIOLATION"


class TenantRequiredError(PerformanceError):
    code = "TENANT_REQUIRED"


class ReadonlyViolationError(PerformanceError):
    code = "READONLY_VIOLATION"
