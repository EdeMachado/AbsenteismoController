/**
 * BioMed Executive Intelligence — page bootstrap.
 */
(function () {
  "use strict";

  const Api = window.BioMedExecutiveApi;
  const CC = window.BioMedCommandCenter;
  const Charts = window.BioMedExecutiveCharts;

  let chartHandles = [];
  let lastPayload = null;

  function tokenHeaders() {
    const token = localStorage.getItem("access_token");
    const h = { Accept: "application/json" };
    if (token) h.Authorization = "Bearer " + token;
    return h;
  }

  // Patch API fetch to include Bearer when present
  const _origFetch = window.fetch.bind(window);
  // api.js uses fetch directly; wrap via monkeypatch on module helper by overriding fetchJson pattern:
  // Re-bind ExecutiveApi methods to include auth.
  function withAuth(fn) {
    return function (opts) {
      const params = new URLSearchParams();
      Object.keys(opts || {}).forEach(function (k) {
        if (opts[k] != null && opts[k] !== "") params.set(k, opts[k]);
      });
      const path = fn.path + (params.toString() ? "?" + params.toString() : "");
      return _origFetch(path, { credentials: "same-origin", headers: tokenHeaders() }).then(
        function (res) {
          if (res.status === 401) {
            window.location.href = "/login";
            throw new Error("Não autenticado");
          }
          if (!res.ok) throw new Error("HTTP " + res.status);
          return res.json();
        }
      );
    };
  }

  const authApi = {
    commandCenter: withAuth({ path: "/api/executive/command-center" }),
    intelligence: withAuth({ path: "/api/executive/intelligence" }),
    actionPlan: withAuth({ path: "/api/executive/action-plan" }),
    performance: withAuth({ path: "/api/executive/performance" }),
    meta: withAuth({ path: "/api/executive/meta" }),
  };

  function destroyCharts() {
    chartHandles.forEach(function (c) {
      Charts.destroyIfAny(c);
    });
    chartHandles = [];
  }

  function findChart(charts, id) {
    return (charts || []).find(function (c) {
      return c.id === id;
    });
  }

  function renderNav(items) {
    const nav = document.getElementById("bm-nav-links");
    if (!nav) return;
    nav.innerHTML = "";
    (items || []).forEach(function (it) {
      const a = document.createElement("a");
      a.href = it.path || "#" + it.id;
      a.textContent = it.label || it.id;
      a.dataset.module = it.id;
      a.addEventListener("click", function (e) {
        e.preventDefault();
        showModule(it.id);
        history.replaceState(null, "", "#" + it.id);
      });
      nav.appendChild(a);
    });
  }

  function showModule(id) {
    document.querySelectorAll(".bm-module").forEach(function (el) {
      el.classList.toggle("is-visible", el.id === id || el.dataset.module === id);
    });
    document.querySelectorAll("#bm-nav-links a").forEach(function (a) {
      a.classList.toggle("is-active", a.dataset.module === id);
    });
    const title = document.querySelector(".bm-title");
    const active = (lastPayload && lastPayload.navigation || []).find(function (n) {
      return n.id === id;
    });
    if (title && active) title.textContent = active.label;
  }

  function renderCharts(charts) {
    destroyCharts();
    const pareto = findChart(charts, "pareto_cid");
    const setores = findChart(charts, "setores");
    const c1 = document.getElementById("chart-pareto");
    const c2 = document.getElementById("chart-setores");
    const c3 = document.getElementById("chart-epi");
    const c4 = document.getElementById("chart-sectors-mod");
    if (pareto && c1) chartHandles.push(Charts.paretoChart(c1, pareto));
    if (setores && c2) chartHandles.push(Charts.barChart(c2, setores));
    if (pareto && c3) chartHandles.push(Charts.paretoChart(c3, pareto));
    if (setores && c4) chartHandles.push(Charts.barChart(c4, setores, Charts.palette.accent));
  }

  function renderPerformance(bp, cond, roi) {
    const el = document.getElementById("bm-performance");
    const elC = document.getElementById("bm-conditionants");
    const elR = document.getElementById("bm-roi");
    if (el) {
      const p = (bp && bp.producao) || {};
      el.innerHTML =
        '<div class="bm-kpi-grid">' +
        kpiMini("Planejadas", p.planejadas) +
        kpiMini("Aprovadas", p.aprovadas) +
        kpiMini("Executadas", p.executadas) +
        kpiMini("Cobertura", bp && bp.cobertura != null ? (bp.cobertura * 100).toFixed(0) + "%" : null) +
        kpiMini("Execução", bp && bp.execucao != null ? (bp.execucao * 100).toFixed(1) + "%" : null) +
        "</div>" +
        '<p class="bm-muted">' +
        (bp && bp.nota ? bp.nota : "") +
        "</p>" +
        "<h3 class=\"bm-section-title\">Resultado observado</h3>" +
        '<ul class="bm-list">' +
        "<li>Eventos: " +
        ((bp && bp.resultado_observado && bp.resultado_observado.eventos) != null
          ? bp.resultado_observado.eventos
          : "—") +
        "</li>" +
        "<li>Dias: " +
        ((bp && bp.resultado_observado && bp.resultado_observado.dias) != null
          ? bp.resultado_observado.dias
          : "—") +
        "</li>" +
        "</ul>";
    }
    if (elC) {
      if (!cond || !cond.length) {
        elC.innerHTML =
          '<p class="bm-muted">Nenhum condicionante empresarial registrado neste payload. Status possíveis: recomendada, aprovada, executada, parcialmente executada, adiada, recusada, impedida.</p>';
      } else {
        elC.innerHTML =
          '<table class="bm-table"><thead><tr><th>ID</th><th>Status</th><th>Nota</th></tr></thead><tbody></tbody></table>';
        const tb = elC.querySelector("tbody");
        cond.forEach(function (c) {
          const tr = document.createElement("tr");
          tr.innerHTML = "<td></td><td></td><td></td>";
          tr.children[0].textContent = c.id || c.recomendacao_id || "—";
          tr.children[1].textContent = c.status || c.decisao || "—";
          tr.children[2].textContent = c.barreira || c.nota || "";
          tb.appendChild(tr);
        });
      }
    }
    if (elR) {
      elR.innerHTML =
        '<span class="bm-badge bm-badge-na">' +
        ((roi && roi.kind) || "ROI_NAO_CALCULAVEL") +
        "</span>" +
        '<p class="bm-muted" style="margin-top:0.75rem"></p>';
      elR.querySelector("p").textContent = ((roi && roi.limitacoes) || []).join(" ");
    }
  }

  function kpiMini(label, value) {
    return (
      '<article class="bm-card bm-kpi"><div class="bm-kpi-label">' +
      label +
      '</div><div class="bm-kpi-value">' +
      (value == null || value === "" ? "N/D" : value) +
      "</div></article>"
    );
  }

  function renderContext(payload) {
    const row = document.getElementById("bm-context-pills");
    if (!row) return;
    row.innerHTML = "";
    const pills = [
      ["Empresa", payload.client && payload.client.label],
      [
        "Período",
        payload.periodo &&
          payload.periodo.atual &&
          payload.periodo.atual.inicio + " → " + payload.periodo.atual.fim,
      ],
      ["Comparativo", payload.periodo && payload.periodo.comparabilidade],
      [
        "IQB",
        payload.qualidade && payload.qualidade.iqb != null
          ? String(payload.qualidade.iqb)
          : "n/d",
      ],
    ];
    pills.forEach(function (p) {
      const s = document.createElement("span");
      s.className = "bm-badge bm-badge-na";
      s.textContent = p[0] + ": " + (p[1] || "—");
      row.appendChild(s);
    });
  }

  function renderAll(payload) {
    lastPayload = payload;
    renderNav(payload.navigation);
    renderContext(payload);
    CC.renderKpis(document.getElementById("bm-kpis"), payload.kpis);
    CC.renderKpis(document.getElementById("bm-abs-kpis"), (payload.kpis || []).slice(0, 6));
    CC.renderScore(document.getElementById("bm-score"), payload.executive_score);
    CC.renderQuality(document.getElementById("bm-quality"), payload.qualidade);
    CC.renderQuality(document.getElementById("bm-quality-full"), payload.qualidade);
    CC.renderNarrative(document.getElementById("bm-narrative"), payload.narrative_lines);
    CC.renderInsights(document.getElementById("bm-insights"), payload.insights);
    const actions =
      (payload.intelligence && payload.intelligence.plano_acao) || [];
    CC.renderActions(document.getElementById("bm-actions"), actions);
    CC.renderIntelSections(document.getElementById("bm-intel"), payload.intelligence);
    renderPerformance(payload.biomed_performance, payload.conditionants, payload.roi);
    renderCharts(payload.charts);
    const hash = (location.hash || "#command").replace("#", "") || "command";
    showModule(hash);
  }

  function filterOpts() {
    const clientId = Number(localStorage.getItem("cliente_selecionado")) || undefined;
    const efetivo = document.getElementById("efetivo").value;
    return {
      client_id: clientId,
      periodo_inicio: document.getElementById("periodo_inicio").value || undefined,
      periodo_fim: document.getElementById("periodo_fim").value || undefined,
      efetivo_trabalhadores: efetivo ? Number(efetivo) : undefined,
    };
  }

  function setStatus(msg, isError) {
    const el = document.getElementById("bm-status");
    if (!el) return;
    if (!msg) {
      el.style.display = "none";
      el.textContent = "";
      return;
    }
    el.style.display = "block";
    el.className = isError ? "bm-error" : "bm-loading";
    el.textContent = msg;
  }

  async function load() {
    if (!localStorage.getItem("access_token")) {
      window.location.href = "/login";
      return;
    }
    setStatus("Carregando painel executivo…");
    try {
      const payload = await authApi.commandCenter(filterOpts());
      renderAll(payload);
      setStatus("");
    } catch (err) {
      setStatus(
        "Não foi possível carregar o Command Center. Verifique autenticação, tenant e flag ENABLE_EXECUTIVE_UI.",
        true
      );
    }
  }

  document.getElementById("bm-filters").addEventListener("submit", function (e) {
    e.preventDefault();
    load();
  });

  // default period: last 6 months
  (function initDates() {
    const now = new Date();
    const fim = now.toISOString().slice(0, 7);
    const start = new Date(now.getFullYear(), now.getMonth() - 5, 1);
    const inicio = start.toISOString().slice(0, 7);
    document.getElementById("periodo_fim").value = fim;
    document.getElementById("periodo_inicio").value = inicio;
  })();

  load();
})();
