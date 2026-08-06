"""Feature-flagged FastAPI router for intelligent ingestion.

Registered only when ENABLE_INTELLIGENT_INGESTION is true.
Compatible with PR #4 tenant guard via ExplicitTenantGuard / PR4 factory hook.
"""

from __future__ import annotations

import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile
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
from backend.ingestion.mapping_profile_service import MappingProfileService
from backend.ingestion.preview_service import PreviewService
from backend.ingestion.schema_sql import apply_epic1_schema
from backend.ingestion.tenant_adapter import (
    ExplicitTenantGuard,
    PR4_TENANT_GUARD_FACTORY,
    TenantContext,
)

router = APIRouter(prefix="/api/ingestion", tags=["ingestion-experimental"])

# Process-local temp DB for experimental epic1 tables (never production path)
_EPIC1_DB: sqlite3.Connection | None = None
_EPIC1_DB_PATH: str | None = None


def _get_epic1_conn() -> sqlite3.Connection:
    global _EPIC1_DB, _EPIC1_DB_PATH
    if _EPIC1_DB is None:
        tmp = Path(tempfile.gettempdir()) / "absenteismo_epic1_experimental.db"
        _EPIC1_DB_PATH = str(tmp)
        _EPIC1_DB = sqlite3.connect(_EPIC1_DB_PATH, check_same_thread=False)
        apply_epic1_schema(_EPIC1_DB, db_path=_EPIC1_DB_PATH)
    return _EPIC1_DB


def _guard_from_headers(
    x_ingestion_user: Optional[str],
    x_ingestion_client_id: Optional[str],
    request_client_id: Optional[int],
) -> TenantContext:
    """
    Temporary auth bridge until PR #4 is merged.
    Does NOT invent a parallel login system — requires explicit authenticated headers
    injected by a future PR #4 dependency, or test harness.
    In production with flag on but without PR #4, refuse unsigned requests.
    """
    if PR4_TENANT_GUARD_FACTORY is not None:
        # Future: return PR4_TENANT_GUARD_FACTORY(request).require_tenant(...)
        pass

    if not x_ingestion_user or not x_ingestion_client_id:
        raise AuthRequiredError("authentication required (PR #4 tenant guard pending)")
    try:
        cid = int(x_ingestion_client_id)
    except ValueError as exc:
        raise AuthRequiredError("invalid tenant header") from exc
    ctx = TenantContext(user_id=None, username=x_ingestion_user, client_id=cid)
    return ExplicitTenantGuard(ctx).require_tenant(request_client_id)


def _http_from_ingestion(exc: Exception) -> HTTPException:
    if isinstance(exc, FeatureDisabledError):
        return HTTPException(status_code=404, detail="not found")
    if isinstance(exc, AuthRequiredError):
        return HTTPException(status_code=401, detail=str(exc))
    if isinstance(exc, TenantGuardError):
        return HTTPException(status_code=403, detail=str(exc))
    if isinstance(exc, (ConfirmationError, ReuploadBlockedError)):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, IngestionError):
        return HTTPException(status_code=400, detail={"code": exc.code, "message": exc.message})
    return HTTPException(status_code=500, detail="ingestion error")


@router.post("/preview")
async def create_preview(
    file: UploadFile = File(...),
    client_id: int = Form(...),
    competencia: str = Form(...),
    x_ingestion_user: Optional[str] = Header(None),
    x_ingestion_client_id: Optional[str] = Header(None),
) -> dict[str, Any]:
    try:
        ctx = _guard_from_headers(x_ingestion_user, x_ingestion_client_id, client_id)
        data = await file.read()
        if len(data) > MAX_FILE_BYTES:
            raise HTTPException(status_code=413, detail="file too large")
        svc = PreviewService(_get_epic1_conn())
        summary = svc.preview(
            data=data,
            original_name=file.filename or "upload.csv",
            client_id=ctx.client_id,
            competencia=competencia,
            uploaded_by=ctx.username,
        )
        public = summary.to_public_dict()
        # confirmation token only returned once at create
        return public
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise _http_from_ingestion(exc) from exc


@router.get("/previews/{preview_id}")
async def get_preview(
    preview_id: str,
    client_id: int,
    x_ingestion_user: Optional[str] = Header(None),
    x_ingestion_client_id: Optional[str] = Header(None),
) -> dict[str, Any]:
    try:
        ctx = _guard_from_headers(x_ingestion_user, x_ingestion_client_id, client_id)
        svc = PreviewService(_get_epic1_conn())
        data = svc.get_preview(preview_id)
        if data["client_id"] != ctx.client_id:
            raise TenantGuardError("cross-tenant preview access blocked")
        return data
    except Exception as exc:  # noqa: BLE001
        raise _http_from_ingestion(exc) from exc


@router.post("/previews/{preview_id}/confirm")
async def confirm_preview(
    preview_id: str,
    client_id: int = Form(...),
    token: str = Form(...),
    admin_justification: Optional[str] = Form(None),
    x_ingestion_user: Optional[str] = Header(None),
    x_ingestion_client_id: Optional[str] = Header(None),
) -> dict[str, Any]:
    try:
        ctx = _guard_from_headers(x_ingestion_user, x_ingestion_client_id, client_id)
        svc = PreviewService(_get_epic1_conn())
        return svc.confirm_preview(
            preview_id,
            token=token,
            client_id=ctx.client_id,
            admin_justification=admin_justification,
        )
    except Exception as exc:  # noqa: BLE001
        raise _http_from_ingestion(exc) from exc


@router.post("/previews/{preview_id}/import")
async def import_preview(
    preview_id: str,
    client_id: int = Form(...),
    competencia: str = Form(...),
    token: str = Form(...),
    content_hash: Optional[str] = Form(None),
    x_ingestion_user: Optional[str] = Header(None),
    x_ingestion_client_id: Optional[str] = Header(None),
) -> dict[str, Any]:
    try:
        ctx = _guard_from_headers(x_ingestion_user, x_ingestion_client_id, client_id)
        conn = _get_epic1_conn()
        preview_svc = PreviewService(conn)
        imp = ImportService(conn, preview_svc)
        result = imp.import_preview(
            preview_id=preview_id,
            token=token,
            client_id=ctx.client_id,
            competencia=competencia,
            expected_content_hash=content_hash,
        )
        return result.to_public_dict()
    except Exception as exc:  # noqa: BLE001
        raise _http_from_ingestion(exc) from exc


@router.get("/mapping-profiles")
async def list_profiles(
    client_id: int,
    x_ingestion_user: Optional[str] = Header(None),
    x_ingestion_client_id: Optional[str] = Header(None),
) -> dict[str, Any]:
    try:
        ctx = _guard_from_headers(x_ingestion_user, x_ingestion_client_id, client_id)
        mps = MappingProfileService(_get_epic1_conn())
        profiles = [p.to_public_dict() for p in mps.list_for_client(ctx.client_id)]
        return {"profiles": profiles}
    except Exception as exc:  # noqa: BLE001
        raise _http_from_ingestion(exc) from exc


@router.post("/mapping-profiles")
async def create_profile(
    client_id: int = Form(...),
    name: str = Form(...),
    structural_signature: str = Form(...),
    mapping_json: str = Form(...),
    sheet_name: Optional[str] = Form(None),
    header_row: Optional[int] = Form(None),
    observation: Optional[str] = Form(None),
    x_ingestion_user: Optional[str] = Header(None),
    x_ingestion_client_id: Optional[str] = Header(None),
) -> dict[str, Any]:
    try:
        import json

        ctx = _guard_from_headers(x_ingestion_user, x_ingestion_client_id, client_id)
        mapping = json.loads(mapping_json)
        mps = MappingProfileService(_get_epic1_conn())
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
    except Exception as exc:  # noqa: BLE001
        raise _http_from_ingestion(exc) from exc


@router.get("/executions/{execution_id}")
async def get_execution(
    execution_id: str,
    client_id: int,
    x_ingestion_user: Optional[str] = Header(None),
    x_ingestion_client_id: Optional[str] = Header(None),
) -> dict[str, Any]:
    try:
        ctx = _guard_from_headers(x_ingestion_user, x_ingestion_client_id, client_id)
        imp = ImportService(_get_epic1_conn())
        return imp.get_execution(execution_id, client_id=ctx.client_id)
    except Exception as exc:  # noqa: BLE001
        raise _http_from_ingestion(exc) from exc


def register_ingestion_routes(app: Any, frontend_dir: str) -> bool:
    """
    Conditionally mount experimental ingestion API + page.
    Returns True if registered. Never runs migrations on startup beyond temp epic1 db
    when a request first needs it.
    """
    if not is_intelligent_ingestion_enabled():
        return False
    app.include_router(router)

    @app.get("/ingestion-experimental", response_class=HTMLResponse)
    async def ingestion_experimental_page():
        path = os.path.join(frontend_dir, "ingestion_experimental.html")
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="page missing")
        with open(path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())

    return True
