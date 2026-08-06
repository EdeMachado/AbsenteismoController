"""IQB adapter for pre-persist preview — reuses A02 weights/classification; does not gate import alone."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from backend.services.data_quality_service import (
    DEFAULT_IQB_WEIGHTS,
    DataQualityProfile,
    IQBWeights,
    classify_iqb,
    identity_risk,
    normalize_sector_key,
    redistribute_weights,
)


def _g(row: dict[str, Any], field: str) -> Any:
    v = row.get(field)
    if isinstance(v, dict) and "normalized" in v:
        return v["normalized"]
    return v


class IngestionIQBAdapter:
    """
    Estimate IQB from in-memory normalized rows before persistence.

    Reuses A02: IQBWeights, DEFAULT_IQB_WEIGHTS, classify_iqb, redistribute_weights,
    normalize_sector_key, identity_risk. Does not query production DB.
    Rastreabilidade/atualidade are limited pre-persist (documented in limitacoes).
    """

    def evaluate(
        self,
        *,
        client_id: int,
        competencia: str,
        normalized_rows: list[dict[str, Any]],
        profile: DataQualityProfile | None = None,
        weights: IQBWeights | None = None,
    ) -> dict[str, Any]:
        if client_id is None or int(client_id) <= 0:
            raise ValueError("client_id obrigatório")
        prof = profile or DataQualityProfile()
        w = weights or IQBWeights(**DEFAULT_IQB_WEIGHTS)
        w.validate()
        n = len(normalized_rows)
        limitacoes = [
            "preview_pre_persist",
            "rastreabilidade_parcial_sem_upload_persistido",
            "atualidade_nao_aplicavel_pre_import",
        ]

        if n == 0:
            pesos = w.as_dict()
            nao = {"atualidade", "rastreabilidade"}
            efetivos, metodo = redistribute_weights(pesos, nao)
            scores = {k: 0.0 for k in pesos}
            return {
                "iqb": 0.0,
                "classificacao": classify_iqb(0.0),
                "dimensoes": scores,
                "pesos": pesos,
                "pesos_efetivos": efetivos,
                "metodo_redistribuicao": metodo,
                "limitacoes": limitacoes + ["zero_eventos"],
                "alertas": ["nenhum_evento_normalizado"],
                "sugestoes": [],
                "advisory_only": True,
                "does_not_gate_import_alone": True,
                "client_id": int(client_id),
                "competencia": competencia,
                "n_events": 0,
            }

        sem_setor = sem_cc = sem_cid = sem_jornada = 0
        sem_dias = sem_data = sem_periodo = sem_ident = 0
        horas_sem = 0
        dias_neg = data_fim_antes = jornada_invalida = 0
        cc_preenchido = cid_preenchido = 0

        setor_map: dict[str, dict[str, Any]] = {}
        workers: dict[str, str] = {}  # key -> strength

        for row in normalized_rows:
            setor = _g(row, "setor")
            cc = _g(row, "centro_custo")
            cid = _g(row, "cid")
            dias = _g(row, "dias_atestados")
            horas = _g(row, "horas_dia")
            hp = _g(row, "horas_perdi")
            d0 = _g(row, "data_afastamento")
            d1 = _g(row, "data_retorno")
            mes = _g(row, "mes_referencia") or competencia
            mat = _g(row, "matricula")
            nome = _g(row, "nomecompleto")
            # cpf intentionally ignored in preview quality path (masked upstream)

            if not setor:
                sem_setor += 1
            else:
                key = normalize_sector_key(str(setor))
                bucket = setor_map.setdefault(key, {"eventos": 0, "rotulos": set()})
                bucket["eventos"] += 1
                bucket["rotulos"].add(str(setor))

            if cc:
                cc_preenchido += 1
            else:
                sem_cc += 1
            if cid:
                cid_preenchido += 1
            else:
                sem_cid += 1
            if horas is None:
                sem_jornada += 1
            elif isinstance(horas, (int, float)) and (horas <= 0 or horas > 24):
                jornada_invalida += 1
            if dias is None:
                sem_dias += 1
            elif isinstance(dias, (int, float)) and dias < 0:
                dias_neg += 1
            if hp is None and horas is not None and dias is not None:
                horas_sem += 1
            if not d0:
                sem_data += 1
            if d0 and d1 and str(d1) < str(d0):
                data_fim_antes += 1
            if not mes:
                sem_periodo += 1
            if mat:
                workers[f"m:{mat}"] = "matricula"
            elif nome:
                workers[f"n:{nome}"] = "nome"
            else:
                sem_ident += 1

        # Completude (same field set spirit as A02)
        campos_frac = [
            1 - sem_setor / n,
            1 - sem_dias / n,
            1 - sem_ident / n,
            1.0,  # upload vínculo N/A pre-persist → treat neutral
            1 - sem_periodo / n,
            1 - sem_jornada / n,
            1 - (horas_sem / n),
            1 - sem_data / n,
        ]
        if prof.centro_custo_aplicavel:
            campos_frac.append(cc_preenchido / n)
        if prof.cid_aplicavel:
            campos_frac.append(cid_preenchido / n)
        scores_completude = 100.0 * (sum(campos_frac) / len(campos_frac))

        inconsistencias = dias_neg + data_fim_antes + jornada_invalida
        scores_cons = max(0.0, 100.0 - 100.0 * inconsistencias / max(n, 1))

        variantes = [s for s in setor_map.values() if len(s["rotulos"]) > 1]
        if not setor_map:
            scores_pad = 50.0
        else:
            eventos_variante = sum(s["eventos"] for s in variantes)
            scores_pad = max(0.0, 100.0 - 100.0 * eventos_variante / n)

        tw_mat = sum(1 for v in workers.values() if v == "matricula")
        tw_nome = sum(1 for v in workers.values() if v == "nome")
        tw_total = len(workers) or 1
        scores_id = 100.0 * (1.0 * tw_mat + 0.25 * tw_nome) / tw_total

        # Pre-persist: rastreabilidade/atualidade not fully applicable
        nao_aplicaveis = {"atualidade"}
        pesos_originais = w.as_dict()
        # Partial rastreabilidade: file hash available in pipeline → mid score
        scores_rast = 70.0
        scores_atual = 0.0

        scores = {
            "completude": round(scores_completude, 4),
            "consistencia": round(scores_cons, 4),
            "padronizacao": round(scores_pad, 4),
            "identidade": round(scores_id, 4),
            "rastreabilidade": round(scores_rast, 4),
            "atualidade": round(scores_atual, 4),
        }
        pesos_efetivos, metodo = redistribute_weights(pesos_originais, nao_aplicaveis)
        scores_used = {k: v for k, v in scores.items() if k not in nao_aplicaveis}
        iqb = round(
            sum(scores_used.get(k, 0.0) * (pesos_efetivos.get(k, 0.0) / 100.0) for k in pesos_efetivos),
            4,
        )
        risco = identity_risk(tw_mat, 0, tw_nome, sem_ident)

        alertas = []
        if scores_completude < 70:
            alertas.append("completude_baixa")
        if variantes:
            alertas.append("setores_variantes")
        if risco in {"alto", "critico"}:
            alertas.append(f"identidade_{risco}")

        sugestoes = []
        for item in variantes:
            sugestoes.append(
                {
                    "tipo": "SETOR_VARIANTE",
                    "prioridade": "media",
                    "impacto_eventos": item["eventos"],
                    "acao": "Padronizar rótulos futuros no upload",
                    "aplicacao_automatica": False,
                }
            )

        return {
            "iqb": iqb,
            "classificacao": classify_iqb(iqb),
            "dimensoes": scores,
            "pesos": pesos_originais,
            "pesos_efetivos": pesos_efetivos,
            "metodo_redistribuicao": metodo,
            "limitacoes": limitacoes,
            "alertas": alertas,
            "sugestoes": sugestoes,
            "identity_risk": risco,
            "advisory_only": True,
            "does_not_gate_import_alone": True,
            "client_id": int(client_id),
            "competencia": competencia,
            "n_events": n,
        }
