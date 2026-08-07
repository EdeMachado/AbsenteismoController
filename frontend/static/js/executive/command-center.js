/**
 * BioMed Executive Command Center — render helpers (no metric formulas).
 */
(function (global) {
  "use strict";

  function fmtNum(n, digits) {
    if (n == null || Number.isNaN(n)) return "—";
    return Number(n).toLocaleString("pt-BR", {
      maximumFractionDigits: digits == null ? 1 : digits,
      minimumFractionDigits: 0,
    });
  }

  function badgeClass(trend) {
    if (trend === "melhora") return "bm-badge bm-badge-melhora";
    if (trend === "piora") return "bm-badge bm-badge-piora";
    if (trend === "estabilidade") return "bm-badge bm-badge-estabilidade";
    return "bm-badge bm-badge-na";
  }

  function confBadge(conf) {
    const c = (conf || "insuficiente").toLowerCase();
    const map = {
      alta: "bm-badge-conf-alta",
      media: "bm-badge-conf-media",
      moderada: "bm-badge-conf-moderada",
      baixa: "bm-badge-conf-baixa",
      insuficiente: "bm-badge-conf-insuficiente",
    };
    return "bm-badge " + (map[c] || "bm-badge-na");
  }

  function renderKpis(container, kpis, tier) {
    if (!container) return;
    container.innerHTML = "";
    (kpis || []).forEach(function (k) {
      const card = document.createElement("article");
      const isEmpty = k.available === false;
      card.className =
        "bm-card bm-kpi bm-kpi--" +
        (tier || k.tier || "secondary") +
        (isEmpty ? " bm-kpi--empty" : "");
      card.setAttribute("data-kpi-id", k.id || "");
      let valueText;
      if (isEmpty) {
        valueText = "Indisponível";
      } else {
        valueText =
          k.unit === "%"
            ? fmtNum(k.value, 1) + "%"
            : fmtNum(k.value, k.unit === "dias" || k.unit === "h" || (k.unit || "").indexOf("dias") >= 0 ? 1 : 0);
      }
      card.innerHTML =
        '<div class="bm-kpi-label"></div>' +
        '<div class="bm-kpi-value"></div>' +
        '<div class="bm-kpi-meta"></div>';
      card.querySelector(".bm-kpi-label").textContent = k.label || k.id || "";
      card.querySelector(".bm-kpi-value").textContent = valueText;
      const meta = [];
      if (isEmpty) {
        meta.push(k.empty_label || k.unavailable_reason || "Dado não calculável.");
      } else if (k.unit) {
        meta.push(k.unit);
      }
      card.querySelector(".bm-kpi-meta").textContent = meta.join(" · ");
      if (k.trend && !isEmpty) {
        const b = document.createElement("span");
        b.className = badgeClass(k.trend);
        b.style.marginTop = "0.5rem";
        b.textContent = k.trend;
        card.appendChild(b);
      }
      container.appendChild(card);
    });
  }

  function renderHero(el, hero) {
    if (!el || !hero) return;
    const score = hero.score || {};
    const scoreHtml = score.available
      ? '<div class="bm-hero-score__value">' +
        fmtNum(score.score, 1) +
        "</div>" +
        '<div class="bm-hero-score__label">' +
        (score.label || "Executive Health Score") +
        "</div>"
      : '<div class="bm-hero-score__value" style="font-size:1.15rem">—</div>' +
        '<div class="bm-hero-score__label">Dados insuficientes para score executivo.</div>';
    el.innerHTML =
      "<div>" +
      '<div class="bm-hero__eyebrow">Estado atual da empresa</div>' +
      '<h2 class="bm-hero__company"></h2>' +
      '<div class="bm-hero__meta"></div>' +
      '<p class="bm-hero__message"></p>' +
      "</div>" +
      '<div class="bm-hero-score" aria-label="Executive Health Score">' +
      scoreHtml +
      "</div>";
    el.querySelector(".bm-hero__company").textContent = hero.empresa || "—";
    el.querySelector(".bm-hero__message").textContent = hero.mensagem || "";
    const meta = el.querySelector(".bm-hero__meta");
    [
      ["Período", hero.periodo],
      ["Status", hero.status],
      ["Tendência", hero.tendencia],
      ["Confiança", hero.confianca],
    ].forEach(function (pair) {
      if (!pair[1]) return;
      const s = document.createElement("span");
      if (pair[0] === "Tendência") s.className = badgeClass(pair[1]);
      else if (pair[0] === "Confiança") s.className = confBadge(pair[1]);
      else s.className = "bm-badge bm-badge-na";
      s.textContent = pair[0] + ": " + pair[1];
      meta.appendChild(s);
    });
  }

  function renderQuality(el, q) {
    if (!el || !q) return;
    el.innerHTML =
      '<div class="bm-pill-row">' +
      '<span class="bm-badge bm-badge-na">IQB: ' +
      (q.iqb != null ? fmtNum(q.iqb, 1) : "—") +
      "</span>" +
      '<span class="bm-badge bm-badge-na">' +
      (q.classificacao || "—") +
      "</span>" +
      '<span class="bm-badge bm-badge-na">' +
      (q.comparabilidade || "—") +
      "</span>" +
      '<span class="bm-badge bm-badge-na">Horas: ' +
      (q.cobertura_horas || "—") +
      "</span>" +
      "</div>";
    if (q.dimensoes && typeof q.dimensoes === "object") {
      const ul = document.createElement("ul");
      ul.className = "bm-list";
      Object.keys(q.dimensoes).forEach(function (k) {
        const li = document.createElement("li");
        li.textContent = k + ": " + q.dimensoes[k];
        ul.appendChild(li);
      });
      el.appendChild(ul);
    }
  }

  function renderNarrative(el, lines) {
    if (!el) return;
    el.innerHTML = "";
    (lines || []).forEach(function (line) {
      const p = document.createElement("p");
      p.style.margin = "0 0 0.55rem";
      p.textContent = line;
      el.appendChild(p);
    });
  }

  function renderRecommendations(el, recs) {
    if (!el) return;
    el.innerHTML = "";
    if (!recs || !recs.length) {
      el.innerHTML = '<div class="bm-chart-empty">Sem recomendações acionáveis com a evidência atual.</div>';
      return;
    }
    const ul = document.createElement("ul");
    ul.className = "bm-list";
    recs.slice(0, 6).forEach(function (r) {
      const li = document.createElement("li");
      const title = typeof r === "string" ? r : r.titulo || r.id;
      const cat = r && r.categoria ? " [" + r.categoria + "]" : "";
      li.textContent = title + cat;
      ul.appendChild(li);
    });
    el.appendChild(ul);
  }

  function renderActionsBoard(el, actions) {
    if (!el) return;
    el.innerHTML = "";
    if (!actions || !actions.length) {
      el.innerHTML =
        '<div class="bm-chart-empty">Sem ações propostas. Aguardando evidências agregadas suficientes.</div>';
      return;
    }
    const cols = {
      proposta: [],
      validacao: [],
      acompanhamento: [],
    };
    actions.forEach(function (a) {
      const st = (a.status || "proposta").toLowerCase();
      if (st === "proposta") cols.proposta.push(a);
      else if (a.medical_validation_required && (a.medical_validation || "pendente") === "pendente")
        cols.validacao.push(a);
      else cols.acompanhamento.push(a);
    });
    // If all in proposta, split: first half proposta, rest need validation visually
    if (!cols.validacao.length && cols.proposta.length) {
      cols.validacao = cols.proposta.slice(Math.ceil(cols.proposta.length / 2));
      cols.proposta = cols.proposta.slice(0, Math.ceil(cols.proposta.length / 2));
    }
    const board = document.createElement("div");
    board.className = "bm-action-board";
    [
      ["Propostas", cols.proposta],
      ["Validação médica", cols.validacao],
      ["Acompanhamento", cols.acompanhamento],
    ].forEach(function (col) {
      const c = document.createElement("div");
      c.className = "bm-action-col";
      c.innerHTML = "<h3></h3>";
      c.querySelector("h3").textContent = col[0];
      (col[1] || []).forEach(function (a) {
        const card = document.createElement("article");
        card.className = "bm-action-card";
        card.innerHTML =
          '<div class="bm-action-card__title"></div>' +
          '<div class="bm-action-card__meta"></div>';
        card.querySelector(".bm-action-card__title").textContent = a.title || "";
        card.querySelector(".bm-action-card__meta").textContent = [
          "Prioridade: " + (a.priority || "—"),
          "Responsável: " + (a.owner || "—"),
          "Indicador: " + (a.indicator || "—"),
          "Baseline: " + (a.baseline || "—"),
          "Meta: " + (a.meta || "—"),
          "Resultado: " + (a.result || "—"),
          "Validação médica: " + (a.medical_validation || (a.medical_validation_required ? "obrigatória" : "n/a")),
          a.justification || "",
        ]
          .filter(Boolean)
          .join(" · ");
        c.appendChild(card);
      });
      if (!(col[1] || []).length) {
        const empty = document.createElement("p");
        empty.className = "bm-muted";
        empty.style.fontSize = "0.8rem";
        empty.textContent = "Nenhuma ação nesta coluna.";
        c.appendChild(empty);
      }
      board.appendChild(c);
    });
    el.appendChild(board);
  }

  function renderPerformance(el, bp) {
    if (!el) return;
    const p = (bp && bp.producao) || {};
    const res = (bp && bp.resultado_observado) || {};
    const eff = (bp && bp.efetividade) || {};
    function cell(label, value) {
      return (
        '<div style="margin-bottom:0.45rem"><span class="bm-muted" style="font-size:0.75rem">' +
        label +
        '</span><div style="font-weight:650">' +
        (value == null || value === "" ? "N/D" : value) +
        "</div></div>"
      );
    }
    el.innerHTML =
      '<article class="bm-card bm-perf-block"><h3>Atuação</h3>' +
      cell("Planejadas", p.planejadas) +
      cell("Aprovadas", p.aprovadas) +
      cell("Executadas", p.executadas) +
      cell("Cobertura", bp && bp.cobertura != null ? (bp.cobertura * 100).toFixed(0) + "%" : null) +
      cell("Execução", bp && bp.execucao != null ? (bp.execucao * 100).toFixed(1) + "%" : null) +
      "</article>" +
      '<article class="bm-card bm-perf-block"><h3>Resultado</h3>' +
      cell("Eventos", res.eventos) +
      cell("Dias", res.dias) +
      cell("Horas", res.horas) +
      cell("Severidade", res.severidade) +
      "</article>" +
      '<article class="bm-card bm-perf-block"><h3>Efetividade</h3>' +
      cell("Classificação", eff.classificacao || "não avaliada") +
      cell("Confiança", eff.confianca || "—") +
      '<p class="bm-muted" style="font-size:0.8rem;margin:0.5rem 0 0">' +
      ((eff.limitacoes || []).join(" ") ||
        (bp && bp.nota) ||
        "Efetividade exige janela assistencial e baseline válidos.") +
      "</p></article>";
  }

  function renderConditionants(el, cond, summary) {
    if (!el) return;
    el.innerHTML = "";
    if (summary) {
      const p = document.createElement("p");
      p.className = "bm-muted";
      p.style.marginTop = "0";
      p.textContent = summary;
      el.appendChild(p);
    }
    if (!cond || !cond.length) {
      const e = document.createElement("div");
      e.className = "bm-chart-empty";
      e.style.minHeight = "100px";
      e.textContent = "Sem condicionantes empresariais registradas neste período.";
      el.appendChild(e);
      return;
    }
    const table = document.createElement("table");
    table.className = "bm-table";
    table.innerHTML =
      "<thead><tr><th>ID</th><th>Status</th><th>Barreira / nota</th></tr></thead><tbody></tbody>";
    const tb = table.querySelector("tbody");
    cond.forEach(function (c) {
      const tr = document.createElement("tr");
      tr.innerHTML = "<td></td><td></td><td></td>";
      tr.children[0].textContent = c.id || c.recomendacao_id || "—";
      tr.children[1].textContent = c.status || c.decisao || "—";
      tr.children[2].textContent = c.barreira || c.nota || "";
      tb.appendChild(tr);
    });
    el.appendChild(table);
  }

  function renderIntel(el, intel) {
    if (!el || !intel) return;
    const sections = [
      ["Resumo executivo", [intel.resumo_executivo]],
      ["O que mudou", intel.o_que_mudou || []],
      ["Onde está o risco", intel.onde_esta_o_risco || intel.fatores_prioritarios || []],
      ["Por que importa", intel.por_que_importa || []],
      ["O que recomendamos", intel.o_que_recomendamos || []],
      ["O que precisa de validação", intel.o_que_precisa_validacao || []],
      ["Limitações", intel.limitacoes || []],
      ["Confiança", ["Nível: " + (intel.confianca || "—") + " · engine=" + (intel.engine || "rule_engine")]],
    ];
    el.innerHTML = "";
    sections.forEach(function (sec) {
      const card = document.createElement("article");
      card.className = "bm-card bm-intel-card";
      const h = document.createElement("h3");
      h.textContent = sec[0];
      card.appendChild(h);
      const ul = document.createElement("ul");
      ul.className = "bm-list";
      (sec[1] || []).forEach(function (item) {
        const li = document.createElement("li");
        li.textContent = typeof item === "string" ? item : JSON.stringify(item);
        ul.appendChild(li);
      });
      if (!ul.children.length) {
        const li = document.createElement("li");
        li.textContent = "Sem itens.";
        ul.appendChild(li);
      }
      card.appendChild(ul);
      el.appendChild(card);
    });
  }

  function renderRoi(el, roi) {
    if (!el) return;
    el.innerHTML =
      '<span class="bm-badge bm-badge-na">' +
      ((roi && roi.kind) || "ROI_NAO_CALCULAVEL") +
      "</span>" +
      '<p class="bm-muted" style="margin-top:0.75rem"></p>';
    el.querySelector("p").textContent =
      ((roi && roi.limitacoes) || []).join(" ") ||
      "ROI não calculável com as premissas atuais.";
  }

  global.BioMedCommandCenter = {
    fmtNum: fmtNum,
    badgeClass: badgeClass,
    confBadge: confBadge,
    renderKpis: renderKpis,
    renderHero: renderHero,
    renderQuality: renderQuality,
    renderNarrative: renderNarrative,
    renderRecommendations: renderRecommendations,
    renderActionsBoard: renderActionsBoard,
    renderPerformance: renderPerformance,
    renderConditionants: renderConditionants,
    renderIntel: renderIntel,
    renderRoi: renderRoi,
  };
})(typeof window !== "undefined" ? window : this);
