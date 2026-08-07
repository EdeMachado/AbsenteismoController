/**
 * BioMed Executive Intelligence — page bootstrap (EXEC-02).
 * Single command-center fetch; no redundant API calls.
 */
(function () {
  "use strict";

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

  function fetchJson(path, opts) {
    const params = new URLSearchParams();
    Object.keys(opts || {}).forEach(function (k) {
      if (opts[k] != null && opts[k] !== "") params.set(k, opts[k]);
    });
    const url = path + (params.toString() ? "?" + params.toString() : "");
    return fetch(url, { credentials: "same-origin", headers: tokenHeaders() }).then(function (res) {
      if (res.status === 401) {
        window.location.href = "/login";
        throw new Error("Não autenticado");
      }
      if (!res.ok) throw new Error("HTTP " + res.status);
      return res.json();
    });
  }

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
        document.getElementById("bm-nav").classList.remove("is-open");
        document.getElementById("bm-nav-toggle").setAttribute("aria-expanded", "false");
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
    const title = document.getElementById("bm-page-title");
    const active = ((lastPayload && lastPayload.navigation) || []).find(function (n) {
      return n.id === id;
    });
    if (title && active) title.textContent = active.label;
  }

  function chartSummary(spec) {
    if (!spec || spec.empty_reason) return spec && spec.empty_reason ? spec.empty_reason : "";
    const cats = spec.categories || [];
    return (spec.title || "") + ": " + cats.length + " categorias.";
  }

  function renderCharts(charts) {
    destroyCharts();
    const temporal = findChart(charts, "evolucao_temporal");
    const pareto = findChart(charts, "pareto_cid");
    const setores = findChart(charts, "setores");

    const tSum = document.getElementById("chart-temporal-summary");
    const pSum = document.getElementById("chart-pareto-summary");
    const sSum = document.getElementById("chart-setores-summary");
    if (tSum) tSum.textContent = chartSummary(temporal);
    if (pSum) pSum.textContent = chartSummary(pareto);
    if (sSum) sSum.textContent = chartSummary(setores);

    chartHandles.push(
      Charts.renderOrEmpty("wrap-temporal", "chart-temporal", temporal, Charts.lineChart)
    );
    chartHandles.push(
      Charts.renderOrEmpty("wrap-pareto", "chart-pareto", pareto, Charts.paretoChart)
    );
    chartHandles.push(
      Charts.renderOrEmpty("wrap-setores", "chart-setores", setores, Charts.barChart)
    );
    chartHandles.push(
      Charts.renderOrEmpty("wrap-abs-temporal", "chart-abs-temporal", temporal, Charts.lineChart)
    );
    chartHandles.push(
      Charts.renderOrEmpty("wrap-epi", "chart-epi", pareto, Charts.paretoChart)
    );
    chartHandles.push(
      Charts.renderOrEmpty("wrap-sectors-mod", "chart-sectors-mod", setores, function (c, s) {
        return Charts.barChart(c, s, Charts.palette.accent);
      })
    );
    chartHandles = chartHandles.filter(Boolean);
  }

  function setBanner(id, text) {
    const el = document.getElementById(id);
    if (!el) return;
    if (!text) {
      el.hidden = true;
      el.textContent = "";
      return;
    }
    el.hidden = false;
    el.textContent = text;
  }

  function renderAll(payload) {
    lastPayload = payload;
    renderNav(payload.navigation);
    CC.renderHero(document.getElementById("bm-hero"), payload.hero);
    CC.renderKpis(
      document.getElementById("bm-kpis-primary"),
      payload.kpis_primary || (payload.kpis || []).filter(function (k) {
        return k.tier === "primary";
      }),
      "primary"
    );
    CC.renderKpis(
      document.getElementById("bm-kpis-secondary"),
      payload.kpis_secondary || (payload.kpis || []).filter(function (k) {
        return k.tier !== "primary";
      }),
      "secondary"
    );
    CC.renderKpis(
      document.getElementById("bm-abs-kpis"),
      payload.kpis_primary || (payload.kpis || []).slice(0, 4),
      "primary"
    );
    CC.renderQuality(document.getElementById("bm-quality"), payload.qualidade);
    CC.renderQuality(document.getElementById("bm-quality-full"), payload.qualidade);
    CC.renderNarrative(document.getElementById("bm-narrative"), payload.narrative_lines);
    CC.renderRecommendations(
      document.getElementById("bm-recommendations"),
      (payload.intelligence && payload.intelligence.recomendacoes) || []
    );
    const actions = (payload.intelligence && payload.intelligence.plano_acao) || [];
    CC.renderActionsBoard(document.getElementById("bm-actions-preview"), actions.slice(0, 4));
    CC.renderActionsBoard(document.getElementById("bm-actions"), actions);
    CC.renderPerformance(document.getElementById("bm-performance"), payload.biomed_performance);
    CC.renderPerformance(document.getElementById("bm-performance-brief"), payload.biomed_performance);
    CC.renderConditionants(
      document.getElementById("bm-conditionants"),
      payload.conditionants,
      payload.conditionants_summary
    );
    setBanner("bm-conditionants-banner", payload.conditionants_summary);
    setBanner("bm-conditionants-banner-2", payload.conditionants_summary);
    CC.renderIntel(document.getElementById("bm-intel"), payload.intelligence);
    CC.renderRoi(document.getElementById("bm-roi"), payload.roi);
    renderCharts(payload.charts);

    const methodBody = document.getElementById("bm-method-body");
    if (methodBody) {
      const how = (payload.methodology && payload.methodology.how) || [];
      methodBody.innerHTML = "<ul class='bm-list'>" + how.map(function (h) {
        return "<li>" + h + "</li>";
      }).join("") + "</ul>";
    }

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
      const payload = await fetchJson("/api/executive/command-center", filterOpts());
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

  document.getElementById("bm-nav-toggle").addEventListener("click", function () {
    const nav = document.getElementById("bm-nav");
    const open = nav.classList.toggle("is-open");
    this.setAttribute("aria-expanded", open ? "true" : "false");
  });

  document.getElementById("bm-how").addEventListener("click", function () {
    document.getElementById("bm-method-modal").classList.add("is-open");
  });
  document.getElementById("bm-method-close").addEventListener("click", function () {
    document.getElementById("bm-method-modal").classList.remove("is-open");
  });
  document.getElementById("bm-method-modal").addEventListener("click", function (e) {
    if (e.target === this) this.classList.remove("is-open");
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      document.getElementById("bm-method-modal").classList.remove("is-open");
    }
  });
  document.querySelectorAll("[data-goto]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      showModule(btn.getAttribute("data-goto"));
      history.replaceState(null, "", "#" + btn.getAttribute("data-goto"));
    });
  });

  (function initDates() {
    document.getElementById("periodo_inicio").value = "2026-01";
    document.getElementById("periodo_fim").value = "2026-03";
  })();

  load();
})();
