/**
 * EXEC-03 — Executive Presentation deck (screen mode).
 */
(function () {
  "use strict";

  const Charts = window.BioMedExecutiveCharts;
  let slides = [];
  let idx = 0;
  let chartHandle = null;

  function tokenHeaders() {
    const token = localStorage.getItem("access_token");
    const h = { Accept: "application/json" };
    if (token) h.Authorization = "Bearer " + token;
    return h;
  }

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function money(v) {
    if (v == null) return "—";
    return "R$ " + Number(v).toLocaleString("pt-BR", { minimumFractionDigits: 2 });
  }

  function destroyChart() {
    if (chartHandle) {
      Charts.destroyIfAny(chartHandle);
      chartHandle = null;
    }
  }

  function renderSlide(i) {
    const stage = document.getElementById("bm-pres-stage");
    const counter = document.getElementById("bm-pres-counter");
    if (!slides.length) {
      stage.innerHTML = "<div class='bm-chart-empty'>Nenhum slide aplicável para o período.</div>";
      return;
    }
    idx = Math.max(0, Math.min(i, slides.length - 1));
    const s = slides[idx];
    counter.textContent = idx + 1 + " / " + slides.length;
    destroyChart();

    let body = "<header class='bm-pres-slide-head'><h1>" + esc(s.title) + "</h1>";
    if (s.leitura) body += "<p class='bm-lede'>" + esc(s.leitura) + "</p>";
    body += "</header>";

    if (s.kpis && s.kpis.length) {
      body +=
        "<div class='bm-kpi-primary'>" +
        s.kpis
          .map(function (k) {
            return (
              "<div class='bm-kpi bm-kpi--primary'><div class='bm-kpi__label'>" +
              esc(k.label) +
              "</div><div class='bm-kpi__value'>" +
              esc(k.available === false ? k.empty_label || "—" : k.value) +
              (k.unit && k.available !== false ? " <small>" + esc(k.unit) + "</small>" : "") +
              "</div></div>"
            );
          })
          .join("") +
        "</div>";
    }

    if (s.custo) {
      const c = s.custo;
      const ass = c.assumption || {};
      body +=
        "<div class='bm-cost-hero'>" +
        "<div class='bm-kpi bm-kpi--primary'><div class='bm-kpi__label'>Impacto operacional estimado</div>" +
        "<div class='bm-kpi__value'>" +
        (c.calculavel ? money(c.custo_estimado) : "Não calculável") +
        "</div></div>" +
        "<ul class='bm-list'>" +
        "<li>Horas: " +
        esc((c.hours && c.hours.horas) || "n/d") +
        " h (" +
        esc((c.hours && c.hours.kind) || "") +
        ")</li>" +
        "<li>Premissa: " +
        esc(ass.estado) +
        (ass.valor != null ? " · R$ " + Number(ass.valor).toFixed(2) + "/h" : "") +
        "</li></ul>" +
        "<p class='bm-muted' style='font-size:0.85rem'>Este valor representa uma estimativa do impacto direto associado às horas de trabalho perdidas e não incorpora custos indiretos nesta versão.</p></div>";
    }

    if (s.recorrencia) {
      const r = s.recorrencia;
      body +=
        "<div class='bm-kpi-secondary'>" +
        "<div class='bm-kpi'><div class='bm-kpi__label'>2+</div><div class='bm-kpi__value'>" +
        esc(r.n_2plus) +
        "</div></div>" +
        "<div class='bm-kpi'><div class='bm-kpi__label'>3+</div><div class='bm-kpi__value'>" +
        esc(r.n_3plus) +
        "</div></div>" +
        "<div class='bm-kpi'><div class='bm-kpi__label'>5+</div><div class='bm-kpi__value'>" +
        esc(r.n_5plus) +
        "</div></div></div>";
    }

    if (s.chart) {
      body +=
        "<div class='bm-chart bm-pres-chart' id='wrap-pres-chart'><canvas id='chart-pres'></canvas></div>";
    }

    if (s.recomendacao) {
      body += "<div class='bm-callout'><strong>Recomendação:</strong> " + esc(s.recomendacao) + "</div>";
    }
    if (s.impacto_economico && s.impacto_economico.linguagem) {
      body += "<p class='bm-muted'>" + esc(s.impacto_economico.linguagem) + "</p>";
    }
    if (s.plano_acao && s.plano_acao.length) {
      body +=
        "<ul class='bm-list'>" +
        s.plano_acao
          .slice(0, 5)
          .map(function (a) {
            return "<li><strong>" + esc(a.title || a.titulo) + "</strong> — " + esc(a.priority || a.prioridade || "") + "</li>";
          })
          .join("") +
        "</ul>";
    }
    if (s.conditionants) {
      body += "<p>" + esc(s.leitura || "") + "</p>";
    }
    if (s.limitacoes) {
      body +=
        "<ul class='bm-list'>" +
        (s.limitacoes || [])
          .slice(0, 6)
          .map(function (l) {
            return "<li>" + esc(l) + "</li>";
          })
          .join("") +
        "</ul>";
    }

    body +=
      "<footer class='bm-pres-meta'>Confiança: " +
      esc(s.confianca) +
      " · " +
      esc(s.metodologia) +
      " · " +
      esc(s.fonte) +
      " · PII excluído</footer>";

    stage.innerHTML = body;

    if (s.chart) {
      const renderer =
        s.chart.chart_type === "pareto"
          ? Charts.paretoChart
          : s.chart.chart_type === "line"
            ? Charts.lineChart
            : Charts.barChart;
      chartHandle = Charts.renderOrEmpty("wrap-pres-chart", "chart-pres", s.chart, renderer);
    }

    document.querySelectorAll("#bm-pres-thumbs button").forEach(function (b, j) {
      b.classList.toggle("is-active", j === idx);
    });
  }

  function renderThumbs() {
    const nav = document.getElementById("bm-pres-thumbs");
    nav.innerHTML = slides
      .map(function (s, i) {
        return "<button type='button' data-i='" + i + "'>" + (i + 1) + ". " + esc(s.title) + "</button>";
      })
      .join("");
    nav.querySelectorAll("button").forEach(function (b) {
      b.addEventListener("click", function () {
        renderSlide(Number(b.getAttribute("data-i")));
      });
    });
  }

  async function load() {
    if (!localStorage.getItem("access_token")) {
      window.location.href = "/login";
      return;
    }
    const status = document.getElementById("bm-pres-status");
    try {
      const clientId = Number(localStorage.getItem("cliente_selecionado")) || "";
      const qs = new URLSearchParams({
        periodo_inicio: "2026-01",
        periodo_fim: "2026-03",
      });
      if (clientId) qs.set("client_id", String(clientId));
      const res = await fetch("/api/executive/presentation?" + qs.toString(), {
        credentials: "same-origin",
        headers: tokenHeaders(),
      });
      if (res.status === 401) {
        window.location.href = "/login";
        return;
      }
      if (!res.ok) throw new Error("HTTP " + res.status);
      const data = await res.json();
      slides = data.slides || [];
      status.style.display = "none";
      renderThumbs();
      renderSlide(0);
    } catch (e) {
      status.className = "bm-error";
      status.textContent =
        "Não foi possível montar a apresentação. Verifique ENABLE_EXECUTIVE_PRESENTATION e autenticação.";
    }
  }

  document.getElementById("bm-pres-prev").addEventListener("click", function () {
    renderSlide(idx - 1);
  });
  document.getElementById("bm-pres-next").addEventListener("click", function () {
    renderSlide(idx + 1);
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "ArrowRight") renderSlide(idx + 1);
    if (e.key === "ArrowLeft") renderSlide(idx - 1);
  });

  load();
})();
