"""RC-1.2A — Digital Employee Form (in-memory preview store).

No database. No migration. Opaque tokens only.
Never put CPF, matrícula, CID, or clinical content in URLs.
"""

from __future__ import annotations

import secrets
import time
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from urllib.parse import quote

STATUSES = (
    "Criada",
    "Enviada",
    "Visualizada",
    "Em preenchimento",
    "Respondida",
    "Analisada",
    "Aguardando validação",
    "Validada",
    "Expirada",
    "Cancelada",
)

FORM_TEMPLATES = [
    {
        "id": "bem-estar-basico",
        "title": "Ficha de bem-estar (básica)",
        "orientation": "Responda com sinceridade. Leva poucos minutos.",
        "fields": [
            {"id": "sono", "label": "Como tem sido seu sono nas últimas semanas?", "type": "choice", "options": ["Bom", "Regular", "Ruim"]},
            {"id": "dor", "label": "Tem sentido desconforto físico relacionado ao trabalho?", "type": "choice", "options": ["Não", "Às vezes", "Frequentemente"]},
            {"id": "carga", "label": "Como avalia a carga de trabalho atual?", "type": "choice", "options": ["Adequada", "Elevada", "Excessiva"]},
            {"id": "obs", "label": "Algo que deseja compartilhar com o responsável? (opcional)", "type": "text"},
        ],
    },
    {
        "id": "retorno-trabalho",
        "title": "Ficha de retorno ao trabalho",
        "orientation": "Ajude a equipe a preparar um retorno seguro.",
        "fields": [
            {"id": "pronto", "label": "Sente-se pronto para retomar as atividades?", "type": "choice", "options": ["Sim", "Parcialmente", "Ainda não"]},
            {"id": "apoio", "label": "Precisa de algum apoio no retorno?", "type": "choice", "options": ["Não", "Sim, ergonômico", "Sim, de jornada"]},
            {"id": "obs", "label": "Observações (opcional)", "type": "text"},
        ],
    },
]

# Synthetic collaborators — display names only (no CPF/matrícula in tokens or URLs)
SYNTH_COLLABORATORS = [
    {"id": "c1", "label": "Colaborador A · Operacional"},
    {"id": "c2", "label": "Colaborador B · Administrativo"},
    {"id": "c3", "label": "Colaborador C · Manutenção"},
]


class DigitalFormStore:
    """Process-local store for preview/staging. Not production persistence."""

    def __init__(self) -> None:
        self._invites: dict[str, dict[str, Any]] = {}
        self._alerts: list[dict[str, Any]] = []

    def reset_demo(self) -> None:
        self._invites.clear()
        self._alerts.clear()

    def list_templates(self) -> list[dict[str, Any]]:
        return deepcopy(FORM_TEMPLATES)

    def list_collaborators(self) -> list[dict[str, str]]:
        return deepcopy(SYNTH_COLLABORATORS)

    def create_invite(
        self,
        *,
        collaborator_id: str,
        template_id: str,
        channel: str,
        company_label: str = "Alpha Industrial",
        ttl_hours: int = 72,
        tenant_key: str = "preview-tenant",
    ) -> dict[str, Any]:
        collab = next((c for c in SYNTH_COLLABORATORS if c["id"] == collaborator_id), None)
        tmpl = next((t for t in FORM_TEMPLATES if t["id"] == template_id), None)
        if not collab or not tmpl:
            raise ValueError("Colaborador ou ficha inválidos")
        ch = (channel or "").lower()
        if ch not in {"whatsapp", "email"}:
            raise ValueError("Canal deve ser whatsapp ou email")

        token = secrets.token_urlsafe(32)  # opaque — no PII
        now = datetime.now(timezone.utc)
        invite = {
            "token": token,
            "tenant_key": tenant_key,
            "company_label": company_label,
            "collaborator_id": collaborator_id,
            "collaborator_label": collab["label"],
            "template_id": template_id,
            "template_title": tmpl["title"],
            "orientation": tmpl["orientation"],
            "fields": deepcopy(tmpl["fields"]),
            "channel": ch,
            "status": "Criada",
            "created_at": now.isoformat(),
            "expires_at": (now + timedelta(hours=ttl_hours)).isoformat(),
            "timeline": [{"at": now.isoformat(), "event": "Criada"}],
            "answers": None,
            "analysis": None,
            "consent": False,
            "cancelled": False,
        }
        self._invites[token] = invite
        return self._public_invite(invite)

    def mark_sent(self, token: str) -> dict[str, Any]:
        inv = self._require(token)
        self._transition(inv, "Enviada")
        self._alert("Convite enviado", "Uma ficha foi enviada ao colaborador.", "info", token)
        return self._public_invite(inv)

    def get_employee_view(self, token: str) -> dict[str, Any]:
        inv = self._require(token)
        self._expire_if_needed(inv)
        if inv["status"] == "Enviada":
            self._transition(inv, "Visualizada")
        # Never expose clinical answers in employee bootstrap beyond fields schema
        return {
            "company_label": inv["company_label"],
            "title": inv["template_title"],
            "orientation": inv["orientation"],
            "privacy": (
                "Este acesso é individual, temporário e destinado ao preenchimento da ficha. "
                "Não compartilhe o link. Seus dados serão tratados conforme a política de privacidade da empresa."
            ),
            "status": inv["status"],
            "expires_at": inv["expires_at"],
            "fields": inv["fields"] if inv["status"] not in {"Expirada", "Cancelada", "Validada"} else [],
            "consent_required": True,
        }

    def start_fill(self, token: str) -> dict[str, Any]:
        inv = self._require(token)
        self._expire_if_needed(inv)
        if inv["status"] in {"Expirada", "Cancelada"}:
            raise ValueError(inv["status"])
        if inv["status"] in {"Visualizada", "Enviada"}:
            self._transition(inv, "Em preenchimento")
        return {"status": inv["status"]}

    def submit_answers(self, token: str, *, consent: bool, answers: dict[str, Any]) -> dict[str, Any]:
        inv = self._require(token)
        self._expire_if_needed(inv)
        if inv["status"] in {"Expirada", "Cancelada"}:
            raise ValueError(inv["status"])
        if not consent:
            raise ValueError("É necessário aceitar a ciência para continuar.")
        inv["consent"] = True
        inv["answers"] = {k: answers.get(k) for k in [f["id"] for f in inv["fields"]]}
        self._transition(inv, "Respondida")
        self._alert("Nova ficha recebida", "Uma resposta de ficha está disponível para análise.", "media", token)

        analysis = self._analyze(inv)
        inv["analysis"] = analysis
        self._transition(inv, "Analisada")
        self._transition(inv, "Aguardando validação")
        self._alert("Nova análise disponível", "Há uma análise sugerida aguardando validação humana.", "media", token)
        self._alert("Necessita validação", "Uma ficha requer revisão do responsável.", "alta", token)
        return {
            "status": inv["status"],
            "message": "Resposta enviada. Obrigado.",
            # employee never receives clinical analysis payload
        }

    def validate(self, token: str, *, note: str = "") -> dict[str, Any]:
        inv = self._require(token)
        if inv["status"] not in {"Aguardando validação", "Analisada"}:
            raise ValueError("Status não permite validação")
        inv["validation_note"] = (note or "")[:200]
        self._transition(inv, "Validada")
        self._alert("Ficha validada", "A validação humana foi registrada.", "info", token)
        return self._staff_invite(inv)

    def cancel(self, token: str) -> dict[str, Any]:
        inv = self._require(token)
        inv["cancelled"] = True
        self._transition(inv, "Cancelada")
        self._alert("Ficha cancelada", "Um convite de ficha foi cancelado.", "baixa", token)
        return self._public_invite(inv)

    def list_invites(self) -> list[dict[str, Any]]:
        return [self._public_invite(i) for i in self._invites.values()]

    def get_staff(self, token: str) -> dict[str, Any]:
        return self._staff_invite(self._require(token))

    def metrics(self) -> dict[str, Any]:
        items = list(self._invites.values())
        sent = sum(1 for i in items if i["status"] not in {"Criada", "Cancelada"})
        answered = sum(1 for i in items if i["status"] in {"Respondida", "Analisada", "Aguardando validação", "Validada"})
        pending_val = sum(1 for i in items if i["status"] == "Aguardando validação")
        pending = sum(
            1
            for i in items
            if i["status"] in {"Enviada", "Visualizada", "Em preenchimento"}
        )
        return {
            "fichas_enviadas": sent,
            "fichas_respondidas": answered,
            "tempo_medio_resposta": "— (demo)",
            "pendentes": pending,
            "validacao_pendente": pending_val,
        }

    def alerts(self) -> list[dict[str, Any]]:
        # No clinical content in dropdown
        return deepcopy(self._alerts[-20:][::-1])

    def channel_payload(self, token: str, *, base_url: str) -> dict[str, Any]:
        inv = self._require(token)
        link = f"{base_url.rstrip('/')}/f/{token}"
        # Never include clinical/PII content — link + institutional copy only
        out: dict[str, Any] = {"link": link, "channel": inv["channel"]}
        if inv["channel"] == "whatsapp":
            msg = (
                "Olá.\n"
                "A empresa disponibilizou uma ficha para seu preenchimento.\n"
                "O acesso é individual e possui prazo de validade.\n"
                f"Acesse:\n{link}\n"
                "Em caso de dúvidas procure o responsável."
            )
            out["whatsapp_url"] = "https://wa.me/?text=" + quote(msg)
            out["whatsapp_message"] = msg
        else:
            out["email"] = {
                "subject": "Ficha para preenchimento",
                "body": (
                    f"Olá,\n\n"
                    f"{inv['company_label']} disponibilizou uma ficha para preenchimento.\n"
                    f"O acesso é individual e possui prazo de validade.\n\n"
                    f"{link}\n\n"
                    f"Em caso de dúvidas, procure o responsável."
                ),
            }
        return out

    # --- internals ---
    def _require(self, token: str) -> dict[str, Any]:
        inv = self._invites.get(token)
        if not inv:
            raise KeyError("Convite não encontrado")
        return inv

    def _expire_if_needed(self, inv: dict[str, Any]) -> None:
        if inv["status"] in {"Expirada", "Cancelada", "Validada"}:
            return
        exp = datetime.fromisoformat(inv["expires_at"])
        if datetime.now(timezone.utc) > exp:
            self._transition(inv, "Expirada")
            self._alert("Convite expirado", "Um convite de ficha expirou.", "baixa", inv["token"])

    def _transition(self, inv: dict[str, Any], status: str) -> None:
        if status not in STATUSES:
            raise ValueError("Status inválido")
        inv["status"] = status
        inv["timeline"].append({"at": datetime.now(timezone.utc).isoformat(), "event": status})

    def _alert(self, title: str, message: str, severidade: str, token: str) -> None:
        self._alerts.append(
            {
                "id": f"a{int(time.time()*1000)}{len(self._alerts)}",
                "title": title,
                "message": message,  # never clinical
                "severidade": severidade,
                "tipo": "ficha_digital",
                "token_ref": token[:8] + "…",  # truncated ref only
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    def _analyze(self, inv: dict[str, Any]) -> dict[str, Any]:
        """Rule-engine style triage. Never diagnoses. Suggestive language only."""
        answers = inv.get("answers") or {}
        themes = []
        critical = []
        priority = "baixa"
        suggestions = []

        if answers.get("dor") in {"Às vezes", "Frequentemente"}:
            themes.append("Desconforto físico referido")
            critical.append("Campo de desconforto físico")
            priority = "media"
            suggestions.append("Sugere revisão ergonômica com validação do responsável.")
        if answers.get("carga") in {"Elevada", "Excessiva"}:
            themes.append("Percepção de carga elevada")
            if priority == "baixa":
                priority = "media"
            suggestions.append("Possível necessidade de diálogo sobre organização do trabalho.")
        if answers.get("sono") == "Ruim":
            themes.append("Sono referido como ruim")
            suggestions.append("Sugere atenção ao bem-estar — necessária validação humana.")
        if answers.get("pronto") == "Ainda não":
            themes.append("Retorno ainda não sentido como pleno")
            priority = "alta"
            critical.append("Prontidão para retorno")
            suggestions.append("Sugere avaliação do plano de retorno antes da liberação plena.")
        if answers.get("apoio", "").startswith("Sim"):
            themes.append("Pedido de apoio no retorno")
            suggestions.append("Possível adaptação de posto ou jornada — necessária validação.")

        if not themes:
            themes.append("Sem temas críticos evidentes nas respostas")
            suggestions.append("Sugere arquivamento após validação de rotina.")

        return {
            "engine": "rule_engine_deterministic_preview",
            "temas_predominantes": themes,
            "recorrencias": ["Demo: recorrência não calculada sem histórico"],
            "campos_criticos": critical or ["Nenhum campo crítico automático"],
            "prioridade": priority,
            "sugestoes": suggestions,
            "disclaimer": "Análise sugestiva. Não é diagnóstico. Necessária validação humana.",
        }

    def _public_invite(self, inv: dict[str, Any]) -> dict[str, Any]:
        return {
            "token": inv["token"],
            "status": inv["status"],
            "template_title": inv["template_title"],
            "collaborator_label": inv["collaborator_label"],
            "channel": inv["channel"],
            "created_at": inv["created_at"],
            "expires_at": inv["expires_at"],
            "timeline": deepcopy(inv["timeline"]),
        }

    def _staff_invite(self, inv: dict[str, Any]) -> dict[str, Any]:
        data = self._public_invite(inv)
        data["analysis"] = deepcopy(inv.get("analysis"))
        data["has_answers"] = inv.get("answers") is not None
        # Do not return raw clinical answers to generic list UIs; staff detail may need gated access in prod.
        data["answers_summary"] = "Respostas recebidas" if inv.get("answers") else "Sem respostas"
        return data


STORE = DigitalFormStore()
