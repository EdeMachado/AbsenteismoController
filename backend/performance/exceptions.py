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


class ProductionPathError(PerformanceError):
    code = "PRODUCTION_PATH_REFUSED"


class IntegrityCheckError(PerformanceError):
    code = "INTEGRITY_CHECK_FAILED"


class SchemaIncompatibleError(PerformanceError):
    code = "SCHEMA_INCOMPATIBLE"


class WindowComparabilityError(PerformanceError):
    code = "WINDOW_NOT_COMPARABLE"
