"""RC-1.2A — preview routes for Digital Employee Form (in-memory, no DB)."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from backend.digital_form.store import STORE

router = APIRouter(tags=["preview-ficha-digital"])


class CreateInviteBody(BaseModel):
    collaborator_id: str
    template_id: str
    channel: str
    company_label: str = "Alpha Industrial"
    ttl_hours: int = Field(default=72, ge=1, le=168)


class SubmitBody(BaseModel):
    consent: bool
    answers: dict[str, Any] = Field(default_factory=dict)


class ValidateBody(BaseModel):
    note: str = ""


def _base_url(request: Request) -> str:
    # Prefer forwarded proto/host when present; preview is HTTP locally
    proto = request.headers.get("x-forwarded-proto") or request.url.scheme
    host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    if host:
        return f"{proto}://{host}"
    return str(request.base_url).rstrip("/")


@router.get("/api/preview/ficha/templates")
async def ficha_templates():
    return {"items": STORE.list_templates()}


@router.get("/api/preview/ficha/collaborators")
async def ficha_collaborators():
    return {"items": STORE.list_collaborators()}


@router.get("/api/preview/ficha/metrics")
async def ficha_metrics():
    return STORE.metrics()


@router.get("/api/preview/ficha/alerts")
async def ficha_alerts():
    return {"items": STORE.alerts()}


@router.get("/api/preview/ficha/invites")
async def ficha_list_invites():
    return {"items": STORE.list_invites()}


@router.post("/api/preview/ficha/invites")
async def ficha_create_invite(body: CreateInviteBody):
    try:
        return STORE.create_invite(
            collaborator_id=body.collaborator_id,
            template_id=body.template_id,
            channel=body.channel,
            company_label=body.company_label,
            ttl_hours=body.ttl_hours,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/api/preview/ficha/invites/{token}")
async def ficha_staff_invite(token: str):
    try:
        return STORE.get_staff(token)
    except KeyError as e:
        raise HTTPException(status_code=404, detail="Convite não encontrado") from e


@router.post("/api/preview/ficha/invites/{token}/send")
async def ficha_send(token: str):
    try:
        return STORE.mark_sent(token)
    except KeyError as e:
        raise HTTPException(status_code=404, detail="Convite não encontrado") from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/api/preview/ficha/invites/{token}/channel")
async def ficha_channel(token: str, request: Request):
    try:
        return STORE.channel_payload(token, base_url=_base_url(request))
    except KeyError as e:
        raise HTTPException(status_code=404, detail="Convite não encontrado") from e


@router.post("/api/preview/ficha/invites/{token}/validate")
async def ficha_validate(token: str, body: Optional[ValidateBody] = None):
    try:
        return STORE.validate(token, note=(body.note if body else ""))
    except KeyError as e:
        raise HTTPException(status_code=404, detail="Convite não encontrado") from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/api/preview/ficha/invites/{token}/cancel")
async def ficha_cancel(token: str):
    try:
        return STORE.cancel(token)
    except KeyError as e:
        raise HTTPException(status_code=404, detail="Convite não encontrado") from e


@router.get("/api/preview/ficha/f/{token}")
async def ficha_employee_view(token: str):
    try:
        return STORE.get_employee_view(token)
    except KeyError as e:
        raise HTTPException(status_code=404, detail="Convite não encontrado") from e


@router.post("/api/preview/ficha/f/{token}/start")
async def ficha_employee_start(token: str):
    try:
        return STORE.start_fill(token)
    except KeyError as e:
        raise HTTPException(status_code=404, detail="Convite não encontrado") from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/api/preview/ficha/f/{token}/submit")
async def ficha_employee_submit(token: str, body: SubmitBody):
    try:
        return STORE.submit_answers(token, consent=body.consent, answers=body.answers)
    except KeyError as e:
        raise HTTPException(status_code=404, detail="Convite não encontrado") from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/api/preview/ficha/reset")
async def ficha_reset():
    STORE.reset_demo()
    return {"ok": True}
