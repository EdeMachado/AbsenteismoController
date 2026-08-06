"""Feature-flagged FastAPI router for intelligent ingestion.

Dual lock to expose mutable HTTP routes:
1. ENABLE_INTELLIGENT_INGESTION=true
2. PR #4 tenant guard factory connected (or explicit test deps)

No browser identity headers. No automatic /tmp SQLite. No auto-migration.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse

from backend.ingestion import is_intelligent_ingestion_enabled
from backend.ingestion.exceptions import (
    AuthRequiredError,
    ConfirmationError,
    FeatureDisabledError,
    IngestionError,
    ReuploadBlockedError,
    TenantGuardError,
)
from backend.ingestion.import_service import ImportService
from backend.ingestion.limits import MAX_FILE_BYTES
from backend.ingestion.logging_utils import safe_log
from backend.ingestion.mapping_profile_service import MappingProfileService
from backend.ingestion.preview_service import PreviewService
from backend.ingestion.repository import (
    IngestionPersistenceError,
    IngestionRepository,
    get_ingestion_repository,
)
from backend.ingestion.tenant_adapter import (
    TenantContext,
    get_pr4_tenant_guard_factory,
    is_ingestion_auth_available,
    require_ingestion_tenant,
)

logger = logging.getLogger("ingestion.api")

router = APIRouter(prefix="/api/ingestion", tags=["ingestion-experimental"])


def _resolve_tenant(request: Request, requested_client_id: int | None) -> TenantContext:
    """Tenant from PR #4 (or test factory). Form client_id is never the identity source."""
    try:
        return require_ingestion_tenant(request, requested_client_id)
    except AuthRequiredError as exc:
        # Fail-closed: auth integration missing or user unauthenticated
        if get_pr4_tenant_guard_factory() is None:
            raise HTTPException(
                status_code=503,
                detail="ingestion authentication unavailable",
            ) from exc
        raise HTTPException(status_code=401, detail="authentication required") from exc
    except TenantGuardError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


def _repo() -> IngestionRepository:
    try:
        return get_ingestion_repository()
    except IngestionPersistenceError as exc:
        raise HTTPException(status_code=503, detail="ingestion persistence unavailable") from exc
    except IngestionError as exc:
        raise HTTPException(status_code=503, detail=exc.message) from exc


def _http_from_ingestion(exc: Exception) -> HTTPException:
    if isinstance(exc, FeatureDisabledError):
        return HTTPException(status_code=404, detail="not found")
    if isinstance(exc, AuthRequiredError):
        if get_pr4_tenant_guard_factory() is None:
            return HTTPException(status_code=503, detail="ingestion authentication unavailable")
        return HTTPException(status_code=401, detail=str(exc))
    if isinstance(exc, TenantGuardError):
        return HTTPException(status_code=403, detail=str(exc))
    if isinstance(exc, IngestionPersistenceError):
        return HTTPException(status_code=503, detail="ingestion persistence unavailable")
    if isinstance(exc, (ConfirmationError, ReuploadBlockedError)):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, IngestionError):
        return HTTPException(status_code=400, detail={"code": exc.code, "message": exc.message})
    return HTTPException(status_code=500, detail="ingestion error")


@router.post("/preview")
async def create_preview(
    request: Request,
    file: UploadFile = File(...),
    client_id: int = Form(...),
    competencia: str = Form(...),
) -> dict[str, Any]:
    try:
        ctx = _resolve_tenant(request, client_id)
        data = await file.read()
        if len(data) > MAX_FILE_BYTES:
            raise HTTPException(status_code=413, detail="file too large")
        repo = _repo()
        svc = PreviewService(repo.conn, require_flag=True)
        summary = svc.preview(
            data=data,
            original_name=file.filename or "upload.csv",
            client_id=ctx.client_id,
            competencia=competencia,
            uploaded_by=ctx.username,
        )
        return summary.to_public_dict()
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise _http_from_ingestion(exc) from exc


@router.get("/previews/{preview_id}")
async def get_preview(
    request: Request,
    preview_id: str,
    client_id: int,
) -> dict[str, Any]:
    try:
        ctx = _resolve_tenant(request, client_id)
        svc = PreviewService(_repo().conn, require_flag=True)
        data = svc.get_preview(preview_id)
        if data["client_id"] != ctx.client_id:
            raise TenantGuardError("cross-tenant preview access blocked")
        return data
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise _http_from_ingestion(exc) from exc


@router.post("/previews/{preview_id}/confirm")
async def confirm_preview(
    request: Request,
    preview_id: str,
    client_id: int = Form(...),
    token: str = Form(...),
    admin_justification: Optional[str] = Form(None),
) -> dict[str, Any]:
    try:
        ctx = _resolve_tenant(request, client_id)
        svc = PreviewService(_repo().conn, require_flag=True)
        return svc.confirm_preview(
            preview_id,
            token=token,
            client_id=ctx.client_id,
            admin_justification=admin_justification,
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise _http_from_ingestion(exc) from exc


@router.post("/previews/{preview_id}/import")
async def import_preview(
    request: Request,
    preview_id: str,
    client_id: int = Form(...),
    competencia: str = Form(...),
    token: str = Form(...),
    content_hash: Optional[str] = Form(None),
) -> dict[str, Any]:
    try:
        ctx = _resolve_tenant(request, client_id)
        conn = _repo().conn
        preview_svc = PreviewService(conn, require_flag=True)
        imp = ImportService(conn, preview_svc)
        result = imp.import_preview(
            preview_id=preview_id,
            token=token,
            client_id=ctx.client_id,
            competencia=competencia,
            expected_content_hash=content_hash,
        )
        return result.to_public_dict()
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise _http_from_ingestion(exc) from exc


@router.get("/mapping-profiles")
async def list_profiles(request: Request, client_id: int) -> dict[str, Any]:
    try:
        ctx = _resolve_tenant(request, client_id)
        mps = MappingProfileService(_repo().conn)
        profiles = [p.to_public_dict() for p in mps.list_for_client(ctx.client_id)]
        return {"profiles": profiles}
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise _http_from_ingestion(exc) from exc


@router.post("/mapping-profiles")
async def create_profile(
    request: Request,
    client_id: int = Form(...),
    name: str = Form(...),
    structural_signature: str = Form(...),
    mapping_json: str = Form(...),
    sheet_name: Optional[str] = Form(None),
    header_row: Optional[int] = Form(None),
    observation: Optional[str] = Form(None),
) -> dict[str, Any]:
    try:
        import json

        ctx = _resolve_tenant(request, client_id)
        mapping = json.loads(mapping_json)
        mps = MappingProfileService(_repo().conn)
        profile = mps.create_version(
            client_id=ctx.client_id,
            name=name,
            structural_signature=structural_signature,
            mapping=mapping,
            sheet_name=sheet_name,
            header_row=header_row,
            created_by=ctx.username,
            observation=observation,
        )
        return profile.to_public_dict()
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise _http_from_ingestion(exc) from exc


@router.get("/executions/{execution_id}")
async def get_execution(
    request: Request,
    execution_id: str,
    client_id: int,
) -> dict[str, Any]:
    try:
        ctx = _resolve_tenant(request, client_id)
        imp = ImportService(_repo().conn)
        return imp.get_execution(execution_id, client_id=ctx.client_id)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise _http_from_ingestion(exc) from exc


def ingestion_http_ready() -> bool:
    """Both locks: feature flag + auth integration available."""
    return is_intelligent_ingestion_enabled() and is_ingestion_auth_available()


def register_ingestion_routes(app: Any, frontend_dir: str) -> bool:
    """
    Mount experimental ingestion API + page only when dual lock passes.

    If flag is on but PR #4 factory is missing (and test deps off):
    - do not register mutable API routes
    - log a safe warning (no PII)
    - return False
    """
    if not is_intelligent_ingestion_enabled():
        return False

    if not is_ingestion_auth_available():
        safe_log(
            "ingestion_routes_not_registered",
            reason="auth_integration_unavailable",
            flag=True,
            pr4_factory=False,
        )
        logger.warning(
            "ENABLE_INTELLIGENT_INGESTION is true but PR #4 tenant guard is not connected; "
            "ingestion HTTP routes were not registered (fail-closed)"
        )
        return False

    if get_pr4_tenant_guard_factory() is None:
        # Test deps path: factory must still be set by the test harness before requests
        safe_log(
            "ingestion_routes_registered_test_mode",
            reason="test_dependencies_allowed",
            flag=True,
        )

    app.include_router(router)

    @app.get("/ingestion-experimental", response_class=HTMLResponse)
    async def ingestion_experimental_page():
        path = os.path.join(frontend_dir, "ingestion_experimental.html")
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="page missing")
        with open(path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())

    return True
