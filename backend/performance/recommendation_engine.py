"""Deterministic recommendation engine — no generative AI."""

from __future__ import annotations

from backend.performance.action_library import ACTION_LIBRARY
from backend.performance.effectiveness_service import _delta
from backend.performance.schemas import (
    MetricSnapshot,
    Recommendation,
    ThresholdConfig,
)


class RecommendationEngine:
    def __init__(self, thresholds: ThresholdConfig | None = None) -> None:
        self.thresholds = thresholds or ThresholdConfig()

    def recommend(
        self,
        *,
        baseline: MetricSnapshot,
        current: MetricSnapshot,
        assistential_coverage: float | None = None,
    ) -> list[Recommendation]:
        thr = self.thresholds
        out: list[Recommendation] = []
        tags: list[str] = []

        d_rec = _delta(current.recorrencia, baseline.recorrencia)
        d_evt = _delta(current.eventos, baseline.eventos)
        d_dias = _delta(current.dias_perdidos, baseline.dias_perdidos)
        d_grav = _delta(current.gravidade, baseline.gravidade)

        if d_rec is not None and d_rec >= thr.material_change:
            tags.append("alta_recorrencia")
        if current.recorrencia is not None and baseline.recorrencia is not None:
            if current.recorrencia >= (baseline.recorrencia or 0) and (
                current.recorrencia or 0
            ) > 0:
                if d_rec is not None and d_rec > 0:
                    tags.append("alta_recorrencia")

        # Osteomuscular severity
        cid_groups = set(current.grupos_cid or []) | set(baseline.grupos_cid or [])
        if "M" in cid_groups and (
            (d_dias is not None and d_dias >= thr.material_change)
            or (d_grav is not None and d_grav >= thr.material_change)
            or (current.duracao_media or 0) > (baseline.duracao_media or 0)
        ):
            tags.append("alta_severidade_osteomuscular")
            tags.append("cid_grupo_M")

        if "J" in cid_groups and d_evt is not None and d_evt >= thr.material_change:
            tags.append("aumento_respiratorio")

        if "S" in cid_groups or "T" in cid_groups:
            if d_evt is not None and d_evt >= thr.material_change:
                tags.append("aumento_acidentes")

        if "F" in cid_groups and d_evt is not None and d_evt >= thr.material_change:
            tags.append("aumento_saude_mental")

        if current.setores_criticos:
            tags.append("concentracao_setorial")

        if current.afastamentos_longos and (
            (baseline.afastamentos_longos or 0) <= (current.afastamentos_longos or 0)
        ):
            if (current.afastamentos_longos or 0) > 0:
                tags.append("afastamentos_longos")

        if d_evt is not None and d_evt >= thr.material_change:
            tags.append("alta_frequencia")

        if assistential_coverage is not None and assistential_coverage < thr.min_assistential_coverage:
            tags.append("baixa_cobertura")

        iqb = current.iqb if current.iqb is not None else baseline.iqb
        if iqb is not None and iqb < thr.min_iqb:
            tags.append("iqb_baixo")

        tags = list(dict.fromkeys(tags))

        # Map tags → actions / recommendations
        mapping = [
            ("alta_recorrencia", "REC-RET-001", "RETORNO", "ACT-RET-001", "alta"),
            ("alta_recorrencia", "REC-RET-002", "RETORNO", "ACT-RET-002", "alta"),
            ("alta_severidade_osteomuscular", "REC-ERG-001", "ERGONOMIA", "ACT-ERG-001", "alta"),
            ("alta_severidade_osteomuscular", "REC-ERG-002", "ERGONOMIA", "ACT-ERG-002", "media"),
            ("aumento_respiratorio", "REC-RESP-001", "RESPIRATORIO", "ACT-RESP-001", "media"),
            ("aumento_respiratorio", "REC-RESP-002", "RESPIRATORIO", "ACT-AMB-001", "media"),
            ("aumento_acidentes", "REC-SEG-001", "SEGURANCA", "ACT-SEG-001", "alta"),
            ("aumento_acidentes", "REC-SEG-002", "SEGURANCA", "ACT-SEG-002", "media"),
            ("aumento_acidentes", "REC-SEG-003", "SEGURANCA", "ACT-SEG-003", "media"),
            ("afastamentos_longos", "REC-LONG-001", "RETORNO", "ACT-LONG-001", "alta"),
            ("aumento_saude_mental", "REC-SM-001", "SAUDE_MENTAL", "ACT-SM-001", "alta"),
            ("baixa_cobertura", "REC-COV-001", "COBERTURA", "ACT-COV-001", "alta"),
            ("iqb_baixo", "REC-QUAL-001", "QUALIDADE_DADOS", "ACT-QUAL-001", "alta"),
            ("alta_frequencia", "REC-JOR-001", "ORGANIZACIONAL", "ACT-JOR-001", "media"),
        ]

        seen: set[str] = set()
        for tag, rec_id, cat, act_id, crit in mapping:
            if tag not in tags or rec_id in seen:
                continue
            act = ACTION_LIBRARY.get(act_id, {})
            conf = 0.55
            if tag in {"alta_recorrencia", "alta_severidade_osteomuscular", "aumento_acidentes"}:
                conf = 0.7
            out.append(
                Recommendation(
                    id=rec_id,
                    categoria=cat,
                    criticidade=crit,
                    confianca=conf,
                    evidencias=[f"tag:{tag}", f"acao_catalogo:{act_id}"],
                    necessita_validacao_humana=True,
                    restricoes=list(act.get("contraindicacoes") or [])
                    + ["nao_afirma_causalidade"],
                    descricao=act.get("nome", rec_id),
                )
            )
            seen.add(rec_id)

        return out
