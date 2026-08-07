/**
 * BioMed Core — RC25 shared helpers (API + format + charts).
 * No calculation changes: maps existing API fields only.
 */
(function (global) {
  "use strict";

  var CACHE = "rc25";
  var CHART_DEFAULTS = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { boxWidth: 12, font: { family: "BM Sans, Segoe UI, sans-serif" } } },
    },
    scales: {
      x: { grid: { color: "rgba(19,32,51,0.06)" }, ticks: { color: "#5a6474" } },
      y: { grid: { color: "rgba(19,32,51,0.06)" }, ticks: { color: "#5a6474" }, beginAtZero: true },
    },
  };

  function token() {
    try {
      return localStorage.getItem("access_token") || "";
    } catch (e) {
      return "";
    }
  }

  function clientId() {
    if (typeof global.getCurrentClientId === "function") {
      return global.getCurrentClientId(null);
    }
    var n = Number(localStorage.getItem("cliente_selecionado"));
    return Number.isFinite(n) && n > 0 ? n : null;
  }

  function clientName() {
    try {
      return (
        localStorage.getItem("cliente_selecionado_nome") ||
        localStorage.getItem("cliente_nome") ||
        (clientId() ? "Empresa #" + clientId() : "Nenhuma empresa")
      );
    } catch (e) {
      return "Empresa";
    }
  }

  function userName() {
    try {
      var u = JSON.parse(localStorage.getItem("user") || "null");
      if (u && (u.nome || u.nome_completo || u.username)) return u.nome || u.nome_completo || u.username;
    } catch (e) {}
    return "Usuário";
  }

  function requireAuth(nextPath) {
    if (!token()) {
      location.href = "/login?next=" + encodeURIComponent(nextPath || location.pathname);
      return false;
    }
    return true;
  }

  async function api(path, opts) {
    opts = opts || {};
    var headers = Object.assign({ Accept: "application/json" }, opts.headers || {});
    var t = token();
    if (t) headers.Authorization = "Bearer " + t;
    var res = await fetch(path, Object.assign({}, opts, { headers: headers }));
    if (res.status === 401) {
      location.href = "/login?next=" + encodeURIComponent(location.pathname);
      throw new Error("unauthorized");
    }
    return res;
  }

  function fmtNum(v, digits) {
    var n = Number(v);
    if (!Number.isFinite(n)) return "—";
    return n.toLocaleString("pt-BR", {
      maximumFractionDigits: digits == null ? 1 : digits,
      minimumFractionDigits: 0,
    });
  }

  function initials(name) {
    var parts = String(name || "?").trim().split(/\s+/).filter(Boolean);
    if (!parts.length) return "?";
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }

  function destroyChart(ref) {
    if (ref && typeof ref.destroy === "function") {
      try {
        ref.destroy();
      } catch (e) {}
    }
  }

  function barChart(canvas, labels, values, color) {
    if (!global.Chart || !canvas) return null;
    destroyChart(canvas._bcChart);
    canvas._bcChart = new global.Chart(canvas.getContext("2d"), {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            data: values,
            backgroundColor: color || "rgba(26, 69, 102, 0.78)",
            borderRadius: 8,
            maxBarThickness: 36,
          },
        ],
      },
      options: Object.assign({}, CHART_DEFAULTS, { plugins: { legend: { display: false } } }),
    });
    return canvas._bcChart;
  }

  function lineChart(canvas, labels, series) {
    if (!global.Chart || !canvas) return null;
    destroyChart(canvas._bcChart);
    var colors = ["#1a4566", "#2a6b5a", "#c45c26"];
    canvas._bcChart = new global.Chart(canvas.getContext("2d"), {
      type: "line",
      data: {
        labels: labels,
        datasets: (series || []).map(function (s, i) {
          return {
            label: s.label,
            data: s.data,
            borderColor: colors[i % colors.length],
            backgroundColor: "transparent",
            tension: 0.3,
            pointRadius: 3,
            borderWidth: 2.5,
          };
        }),
      },
      options: CHART_DEFAULTS,
    });
    return canvas._bcChart;
  }

  function doughnutChart(canvas, labels, values) {
    if (!global.Chart || !canvas) return null;
    destroyChart(canvas._bcChart);
    var palette = ["#1a4566", "#2a6b5a", "#c45c26", "#5a8aa8", "#8f2f2a", "#a67c2a"];
    canvas._bcChart = new global.Chart(canvas.getContext("2d"), {
      type: "doughnut",
      data: {
        labels: labels,
        datasets: [
          {
            data: values,
            backgroundColor: labels.map(function (_, i) {
              return palette[i % palette.length];
            }),
            borderWidth: 0,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: "bottom", labels: { boxWidth: 10 } } },
      },
    });
    return canvas._bcChart;
  }

  /** Metric field map — SOURCE=/api/dashboard metricas.* */
  function mapDashboardMetrics(metricas) {
    metricas = metricas || {};
    var dias = Number(metricas.total_dias_perdidos || metricas.total_atestados_dias || 0);
    var horas = Number(metricas.total_horas_perdidas || 0);
    var atestados = Number(metricas.total_atestados || metricas.total_registros || 0);
    var funcs = Number(metricas.funcionarios_afetados || 0);
    var freq = funcs > 0 ? atestados / funcs : 0;
    var dur = atestados > 0 ? dias / atestados : 0;
    return {
      colaboradores: funcs,
      atestados: atestados,
      dias: dias,
      horas: horas,
      frequencia: freq,
      duracao_media: dur,
      /* derived display helpers — not new business formulas beyond ratio of existing fields */
      SOURCE_API: "/api/dashboard",
      SOURCE_FIELDS: {
        colaboradores: "metricas.funcionarios_afetados",
        atestados: "metricas.total_atestados|total_registros",
        dias: "metricas.total_dias_perdidos",
        horas: "metricas.total_horas_perdidas",
        frequencia: "atestados/funcionarios_afetados",
        duracao_media: "dias/atestados",
      },
    };
  }

  global.BioMedCore = {
    CACHE: CACHE,
    token: token,
    clientId: clientId,
    clientName: clientName,
    userName: userName,
    requireAuth: requireAuth,
    api: api,
    fmtNum: fmtNum,
    initials: initials,
    barChart: barChart,
    lineChart: lineChart,
    doughnutChart: doughnutChart,
    mapDashboardMetrics: mapDashboardMetrics,
    destroyChart: destroyChart,
  };
})(window);
