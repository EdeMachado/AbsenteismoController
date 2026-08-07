"""HTTP routes for EXEC-01 Executive Intelligence (feature-flagged)."""

from __future__ import annotations

import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from backend.auth import get_current_active_user
from backend.database import get_db
from backend.executive import ENGINE_VERSION, FEATURE_FLAG_ENV, is_executive_ui_enabled
from backend.executive.aggregate_service import ExecutiveAggregateService
from backend.models import User
from backend.tenant import resolve_authorized_client


def _resolve_client_id(
    db: Session, current_user: User, client_id: Optional[int]
) -> int:
    try:
        authorized = resolve_authorized_client(db, current_user, client_id)
        return int(authorized.id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


def register_executive_routes(app, frontend_dir: str) -> None:
    """Register /executive page + /api/executive/* only when flag is on."""
    if not is_executive_ui_enabled():
        return

    router = APIRouter(prefix="/api/executive", tags=["executive-intelligence"])

    @router.get("/meta")
    def executive_meta(current_user: User = Depends(get_current_active_user)):
        return {
            "status": "ok",
            "flag": FEATURE_FLAG_ENV,
            "enabled": True,
            "engine_version": ENGINE_VERSION,
            "llm": False,
            "intelligence_engine": "rule_engine_deterministic_v1",
            "privacy": {
                "small_group_threshold": 5,
                "pii_excluded": True,
                "worker_ranking": False,
            },
        }

    @router.get("/health")
    def executive_health():
        return {
            "status": "ok",
            "flag": FEATURE_FLAG_ENV,
            "enabled": True,
            "engine_version": ENGINE_VERSION,
        }

    @router.get("/command-center")
    def command_center(
        periodo_inicio: Optional[str] = Query(None),
        periodo_fim: Optional[str] = Query(None),
        client_id: Optional[int] = Query(None),
        efetivo_trabalhadores: Optional[int] = Query(None),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
    ):
        cid = _resolve_client_id(db, current_user, client_id)
        try:
            return ExecutiveAggregateService(db).build_command_center(
                client_id=cid,
                periodo_inicio=periodo_inicio,
                periodo_fim=periodo_fim,
                efetivo_trabalhadores=efetivo_trabalhadores,
            )
        except ValueError as exc:
            if str(exc) == "client_not_found":
                raise HTTPException(status_code=404, detail="Cliente não encontrado") from exc
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail="Falha ao montar painel executivo") from exc

    @router.get("/intelligence")
    def intelligence(
        periodo_inicio: Optional[str] = Query(None),
        periodo_fim: Optional[str] = Query(None),
        client_id: Optional[int] = Query(None),
        efetivo_trabalhadores: Optional[int] = Query(None),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
    ):
        cid = _resolve_client_id(db, current_user, client_id)
        payload = ExecutiveAggregateService(db).build_command_center(
            client_id=cid,
            periodo_inicio=periodo_inicio,
            periodo_fim=periodo_fim,
            efetivo_trabalhadores=efetivo_trabalhadores,
        )
        return {
            "client": payload.get("client"),
            "periodo": payload.get("periodo"),
            "intelligence": payload.get("intelligence"),
            "privacy": payload.get("privacy"),
            "engine_version": payload.get("engine_version"),
        }

    @router.get("/action-plan")
    def action_plan(
        periodo_inicio: Optional[str] = Query(None),
        periodo_fim: Optional[str] = Query(None),
        client_id: Optional[int] = Query(None),
        efetivo_trabalhadores: Optional[int] = Query(None),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
    ):
        cid = _resolve_client_id(db, current_user, client_id)
        payload = ExecutiveAggregateService(db).build_command_center(
            client_id=cid,
            periodo_inicio=periodo_inicio,
            periodo_fim=periodo_fim,
            efetivo_trabalhadores=efetivo_trabalhadores,
        )
        intel = payload.get("intelligence") or {}
        return {
            "client": payload.get("client"),
            "periodo": payload.get("periodo"),
            "plano_acao": intel.get("plano_acao") or [],
            "fluxo": [
                "IA propõe",
                "médico valida",
                "empresa aprova",
                "ação executada",
                "sistema monitora",
                "resultado avaliado",
            ],
            "auto_execucao": False,
            "privacy": payload.get("privacy"),
        }

    @router.get("/performance")
    def performance(
        periodo_inicio: Optional[str] = Query(None),
        periodo_fim: Optional[str] = Query(None),
        client_id: Optional[int] = Query(None),
        efetivo_trabalhadores: Optional[int] = Query(None),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
    ):
        cid = _resolve_client_id(db, current_user, client_id)
        payload = ExecutiveAggregateService(db).build_command_center(
            client_id=cid,
            periodo_inicio=periodo_inicio,
            periodo_fim=periodo_fim,
            efetivo_trabalhadores=efetivo_trabalhadores,
        )
        return {
            "client": payload.get("client"),
            "periodo": payload.get("periodo"),
            "biomed_performance": payload.get("biomed_performance"),
            "conditionants": payload.get("conditionants"),
            "roi": payload.get("roi"),
            "executive_score": payload.get("executive_score"),
            "narrative": (payload.get("intelligence") or {}).get("resumo_executivo"),
            "privacy": payload.get("privacy"),
        }

    app.include_router(router)

    # HTML served without Bearer dependency (legacy pattern); API requires auth.
    @app.get("/executive", response_class=HTMLResponse)
    async def executive_page():
        path = os.path.join(frontend_dir, "executive.html")
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="executive.html não encontrado")
        with open(path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
