"""HTTP routes for EXEC-01→03 Executive Intelligence (feature-flagged)."""

from __future__ import annotations

import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from backend.auth import get_current_active_user
from backend.database import get_db
from backend.executive import (
    ENGINE_VERSION,
    FEATURE_FLAG_ENV,
    PRESENTATION_FLAG_ENV,
    is_executive_presentation_enabled,
    is_executive_ui_enabled,
)
from backend.executive.aggregate_service import ExecutiveAggregateService
from backend.executive.questions import QUESTIONS
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
            "presentation_flag": PRESENTATION_FLAG_ENV,
            "presentation_enabled": is_executive_presentation_enabled(),
            "engine_version": ENGINE_VERSION,
            "llm": False,
            "intelligence_engine": "rule_engine_deterministic_v1",
            "privacy": {
                "small_group_threshold": 5,
                "pii_excluded": True,
                "worker_ranking": False,
                "presentation_default": "aggregate",
            },
            "levels": ["command_center", "analytics", "presentation"],
        }

    @router.get("/health")
    def executive_health():
        return {
            "status": "ok",
            "flag": FEATURE_FLAG_ENV,
            "enabled": True,
            "presentation_enabled": is_executive_presentation_enabled(),
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

    @router.get("/analytics")
    def analytics(
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
            "catalog": payload.get("analytics_catalog"),
            "charts": payload.get("charts"),
            "custo": payload.get("custo"),
            "recorrencia_agregada": payload.get("recorrencia_agregada"),
            "padroes_temporais": payload.get("padroes_temporais"),
            "afastamentos_longos": payload.get("afastamentos_longos"),
            "privacy": payload.get("privacy"),
            "engine_version": payload.get("engine_version"),
        }

    @router.get("/cost")
    def cost(
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
            "custo": payload.get("custo"),
            "impacto_economico_biomed": payload.get("impacto_economico_biomed"),
            "condicionantes_financeiras": payload.get("condicionantes_financeiras"),
            "privacy": payload.get("privacy"),
        }

    @router.get("/questions")
    def questions_list(current_user: User = Depends(get_current_active_user)):
        return {"questions": QUESTIONS}

    @router.get("/questions/{qid}")
    def question_answer(
        qid: str,
        periodo_inicio: Optional[str] = Query(None),
        periodo_fim: Optional[str] = Query(None),
        client_id: Optional[int] = Query(None),
        efetivo_trabalhadores: Optional[int] = Query(None),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
    ):
        cid = _resolve_client_id(db, current_user, client_id)
        return ExecutiveAggregateService(db).answer_executive_question(
            qid,
            client_id=cid,
            periodo_inicio=periodo_inicio,
            periodo_fim=periodo_fim,
            efetivo_trabalhadores=efetivo_trabalhadores,
        )

    @router.get("/analyze/{analysis_id}")
    def analyze(
        analysis_id: str,
        periodo_inicio: Optional[str] = Query(None),
        periodo_fim: Optional[str] = Query(None),
        client_id: Optional[int] = Query(None),
        efetivo_trabalhadores: Optional[int] = Query(None),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
    ):
        cid = _resolve_client_id(db, current_user, client_id)
        return ExecutiveAggregateService(db).analyze(
            analysis_id,
            client_id=cid,
            periodo_inicio=periodo_inicio,
            periodo_fim=periodo_fim,
            efetivo_trabalhadores=efetivo_trabalhadores,
        )

    @router.get("/presentation")
    def presentation_api(
        periodo_inicio: Optional[str] = Query(None),
        periodo_fim: Optional[str] = Query(None),
        client_id: Optional[int] = Query(None),
        efetivo_trabalhadores: Optional[int] = Query(None),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
    ):
        if not is_executive_presentation_enabled():
            raise HTTPException(
                status_code=404,
                detail=f"{PRESENTATION_FLAG_ENV} desabilitada",
            )
        cid = _resolve_client_id(db, current_user, client_id)
        return ExecutiveAggregateService(db).build_presentation(
            client_id=cid,
            periodo_inicio=periodo_inicio,
            periodo_fim=periodo_fim,
            efetivo_trabalhadores=efetivo_trabalhadores,
        )

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
            "impacto_economico_biomed": payload.get("impacto_economico_biomed"),
            "roi": payload.get("roi"),
            "executive_score": payload.get("executive_score"),
            "narrative": (payload.get("intelligence") or {}).get("resumo_executivo"),
            "privacy": payload.get("privacy"),
        }

    app.include_router(router)

    @app.get("/executive", response_class=HTMLResponse)
    async def executive_page():
        path = os.path.join(frontend_dir, "executive.html")
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="executive.html não encontrado")
        with open(path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())

    if is_executive_presentation_enabled():

        @app.get("/executive/presentation", response_class=HTMLResponse)
        async def executive_presentation_page():
            path = os.path.join(frontend_dir, "executive_presentation.html")
            if not os.path.exists(path):
                raise HTTPException(
                    status_code=404, detail="executive_presentation.html não encontrado"
                )
            with open(path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
