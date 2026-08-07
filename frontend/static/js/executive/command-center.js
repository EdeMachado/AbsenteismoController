/**
 * BioMed Executive Command Center — render from aggregated API payload.
 * No metric formulas in the browser.
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

  function renderKpis(container, kpis) {
    if (!container) return;
    container.innerHTML = "";
    (kpis || []).forEach(function (k) {
      const card = document.createElement("article");
      card.className = "bm-card bm-kpi";
      card.setAttribute("data-kpi-id", k.id || "");
      const valueText =
        k.available === false
          ? "N/D"
          : k.unit === "%"
            ? fmtNum(k.value, 1) + "%"
            : fmtNum(k.value, k.unit === "dias" || k.unit === "h" ? 1 : 0);
      card.innerHTML =
        '<div class="bm-kpi-label"></div>' +
        '<div class="bm-kpi-value"></div>' +
        '<div class="bm-kpi-meta"></div>';
      card.querySelector(".bm-kpi-label").textContent = k.label || k.id || "";
      card.querySelector(".bm-kpi-value").textContent = valueText;
      const meta = [];
      if (k.unit) meta.push(k.unit);
      if (k.unavailable_reason && k.available === false) meta.push(k.unavailable_reason);
      card.querySelector(".bm-kpi-meta").textContent = meta.join(" · ");
      if (k.trend) {
        const b = document.createElement("span");
        b.className = badgeClass(k.trend);
        b.style.marginTop = "0.5rem";
        b.textContent = k.trend;
        card.appendChild(b);
      }
      container.appendChild(card);
    });
  }

  function renderScore(el, score) {
    if (!el || !score) return;
    if (!score.available) {
      el.innerHTML =
        '<div class="bm-kpi-value">—</div>' +
        '<div class="bm-kpi-label">SCORE NÃO DISPONÍVEL</div>' +
        '<p class="bm-muted" style="margin:0.5rem 0 0;font-size:0.85rem"></p>';
      el.querySelector("p").textContent = (score.limitations || []).join(" ") || score.label || "";
      return;
    }
    const comps = (score.components || [])
      .map(function (c) {
        return (
          "<li><strong>" +
          (c.label || c.id) +
          ":</strong> " +
          (c.value == null ? "—" : fmtNum(c.value, 1)) +
          (c.note ? ' <span class="bm-muted">(' + c.note + ")</span>" : "") +
          "</li>"
        );
      })
      .join("");
    el.innerHTML =
      '<div class="bm-kpi-value"></div>' +
      '<div class="bm-kpi-label"></div>' +
      '<ul class="bm-list" style="margin-top:1rem;font-size:0.9rem"></ul>';
    el.querySelector(".bm-kpi-value").textContent = fmtNum(score.score, 1);
    el.querySelector(".bm-kpi-label").textContent = score.label || "Executive Health Score";
    el.querySelector("ul").innerHTML = comps;
  }

  function renderInsights(el, insights) {
    if (!el) return;
    el.innerHTML = "";
    (insights || []).forEach(function (ins) {
      const art = document.createElement("article");
      art.style.marginBottom = "0.85rem";
      art.innerHTML =
        '<div style="font-weight:600;margin-bottom:0.25rem"></div>' +
        '<p class="bm-muted" style="margin:0"></p>';
      art.querySelector("div").textContent = ins.title || "";
      art.querySelector("p").textContent = ins.body || "";
      el.appendChild(art);
    });
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

  function renderActions(el, actions) {
    if (!el) return;
    el.innerHTML = "";
    if (!actions || !actions.length) {
      el.innerHTML =
        '<div class="bm-empty"><h3>Sem ações propostas</h3><p>Aguardando evidências agregadas suficientes.</p></div>';
      return;
    }
    const table = document.createElement("table");
    table.className = "bm-table";
    table.innerHTML =
      "<thead><tr>" +
      "<th>Ação</th><th>Prioridade</th><th>Justificativa</th><th>Responsável</th>" +
      "<th>Status</th><th>Indicador</th><th>Validação médica</th>" +
      "</tr></thead><tbody></tbody>";
    const tb = table.querySelector("tbody");
    actions.forEach(function (a) {
      const tr = document.createElement("tr");
      [
        a.title,
        a.priority,
        a.justification,
        a.owner,
        a.status,
        a.indicator,
        a.medical_validation_required ? "obrigatória" : "n/a",
      ].forEach(function (v) {
        const td = document.createElement("td");
        td.textContent = v == null ? "—" : String(v);
        tr.appendChild(td);
      });
      tb.appendChild(tr);
    });
    el.appendChild(table);
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
    if (q.limitations && q.limitations.length) {
      const p = document.createElement("p");
      p.className = "bm-muted";
      p.style.marginTop = "0.75rem";
      p.style.fontSize = "0.85rem";
      p.textContent = q.limitations.join(" ");
      el.appendChild(p);
    }
  }

  function asList(val) {
    if (val == null) return [];
    if (Array.isArray(val)) return val;
    return [String(val)];
  }

  function renderIntelSections(el, intel) {
    if (!el || !intel) return;
    const sections = [
      ["Resumo executivo", asList(intel.resumo_executivo)],
      ["Diagnóstico situacional", asList(intel.diagnostico_situacional)],
      ["Fatores prioritários", asList(intel.fatores_prioritarios)],
      ["Alertas", asList(intel.alertas)],
      ["Hipóteses", asList(intel.hipoteses)],
      ["Recomendações", intel.recomendacoes || []],
      ["Evidências", asList(intel.evidencias)],
      ["Limitações", asList(intel.limitacoes)],
    ];
    el.innerHTML = "";
    sections.forEach(function (sec) {
      const block = document.createElement("div");
      block.className = "bm-card";
      block.style.marginBottom = "1rem";
      const h = document.createElement("h3");
      h.className = "bm-section-title";
      h.style.fontSize = "1.05rem";
      h.textContent = sec[0];
      block.appendChild(h);
      const ul = document.createElement("ul");
      ul.className = "bm-list";
      (sec[1] || []).forEach(function (item) {
        const li = document.createElement("li");
        if (typeof item === "string") li.textContent = item;
        else if (item && item.titulo) li.textContent = item.titulo + (item.categoria ? " [" + item.categoria + "]" : "");
        else li.textContent = JSON.stringify(item);
        ul.appendChild(li);
      });
      if (!ul.children.length) {
        const li = document.createElement("li");
        li.className = "bm-muted";
        li.textContent = "Sem itens neste período.";
        ul.appendChild(li);
      }
      block.appendChild(ul);
      el.appendChild(block);
    });
    const conf = document.createElement("p");
    conf.className = "bm-muted";
    conf.textContent =
      "Confiança do motor: " +
      (intel.confianca || "—") +
      " · engine=" +
      (intel.engine || "rule_engine") +
      " · Sem LLM externo. Validação humana obrigatória para ações.";
    el.appendChild(conf);
  }

  global.BioMedCommandCenter = {
    fmtNum: fmtNum,
    renderKpis: renderKpis,
    renderScore: renderScore,
    renderInsights: renderInsights,
    renderNarrative: renderNarrative,
    renderActions: renderActions,
    renderQuality: renderQuality,
    renderIntelSections: renderIntelSections,
  };
})(typeof window !== "undefined" ? window : this);
