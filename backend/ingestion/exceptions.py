"""Typed exceptions for the intelligent ingestion pipeline."""

from __future__ import annotations


class IngestionError(Exception):
    """Base ingestion error (safe message; no PII)."""

    code: str = "INGESTION_ERROR"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        if code:
            self.code = code
        self.message = message


class FeatureDisabledError(IngestionError):
    code = "FEATURE_DISABLED"


class UnsupportedFormatError(IngestionError):
    code = "UNSUPPORTED_FORMAT"


class FileTooLargeError(IngestionError):
    code = "FILE_TOO_LARGE"


class PathTraversalError(IngestionError):
    code = "PATH_TRAVERSAL"


class EmptyFileError(IngestionError):
    code = "EMPTY_FILE"


class AmbiguousStructureError(IngestionError):
    code = "AMBIGUOUS_STRUCTURE"


class LowConfidenceMappingError(IngestionError):
    code = "LOW_CONFIDENCE_MAPPING"


class PreviewRequiredError(IngestionError):
    code = "PREVIEW_REQUIRED"


class ConfirmationError(IngestionError):
    code = "CONFIRMATION_INVALID"


class IdempotencyConflictError(IngestionError):
    code = "IDEMPOTENCY_CONFLICT"


class ReuploadBlockedError(IngestionError):
    code = "REUPLOAD_BLOCKED"


class TenantGuardError(IngestionError):
    code = "TENANT_GUARD"


class AuthRequiredError(IngestionError):
    code = "AUTH_REQUIRED"


class LimitExceededError(IngestionError):
    code = "LIMIT_EXCEEDED"


class FormulaRejectedError(IngestionError):
    code = "FORMULA_REJECTED"


class MigrationNotAllowedError(IngestionError):
    code = "MIGRATION_NOT_ALLOWED"
