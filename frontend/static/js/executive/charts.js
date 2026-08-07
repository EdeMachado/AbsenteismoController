/**
 * BioMed Executive — Chart.js helpers (no formula duplication).
 */
(function (global) {
  "use strict";

  const palette = {
    primary: "#1a4566",
    accent: "#2a6b5a",
    muted: "#94A3B8",
    secondary: "#7a8fa3",
  };

  function destroyIfAny(chart) {
    if (chart && typeof chart.destroy === "function") chart.destroy();
  }

  function cats(spec) {
    return (spec && (spec.categories || spec.labels)) || [];
  }

  function seriesVals(spec, idx) {
    const s = spec && spec.series && spec.series[idx];
    if (!s) return [];
    return s.data || s.values || [];
  }

  function seriesLabel(spec, idx, fallback) {
    const s = spec && spec.series && spec.series[idx];
    return (s && (s.name || s.label)) || fallback;
  }

  function showEmpty(wrapId, reason) {
    const wrap = document.getElementById(wrapId);
    if (!wrap) return;
    wrap.innerHTML =
      '<div class="bm-chart-empty" role="status">' +
      (reason || "Dados insuficientes para esta visualização.") +
      "</div>";
  }

  function ensureCanvas(wrapId, canvasId) {
    const wrap = document.getElementById(wrapId);
    if (!wrap) return null;
    let canvas = document.getElementById(canvasId);
    if (!canvas) {
      wrap.innerHTML = "";
      canvas = document.createElement("canvas");
      canvas.id = canvasId;
      wrap.appendChild(canvas);
    }
    return canvas;
  }

  function lineChart(canvas, chartSpec) {
    if (!canvas || !global.Chart) return null;
    const labels = cats(chartSpec);
    if (!labels.length) return null;
    const datasets = (chartSpec.series || []).slice(0, 3).map(function (s, i) {
      const colors = [palette.primary, palette.accent, palette.secondary];
      return {
        label: s.name || s.label || "Série",
        data: s.data || s.values || [],
        borderColor: colors[i % colors.length],
        backgroundColor: "transparent",
        tension: 0.3,
        borderWidth: i === 0 ? 2.5 : 1.5,
        borderDash: i === 1 ? [5, 4] : [],
        pointRadius: i === 0 ? 3 : 0,
      };
    });
    return new global.Chart(canvas.getContext("2d"), {
      type: "line",
      data: { labels: labels, datasets: datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "bottom", labels: { boxWidth: 12, font: { family: "DM Sans", size: 11 } } },
        },
        scales: {
          y: { beginAtZero: true, grid: { color: "rgba(15,23,42,0.06)" } },
          x: { grid: { display: false }, ticks: { font: { size: 11 } } },
        },
      },
    });
  }

  function paretoChart(canvas, chartSpec) {
    if (!canvas || !global.Chart) return null;
    const labels = cats(chartSpec);
    if (!labels.length) return null;
    const values = seriesVals(chartSpec, 0);
    const cum = seriesVals(chartSpec, 1);
    return new global.Chart(canvas.getContext("2d"), {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            type: "bar",
            label: seriesLabel(chartSpec, 0, "Volume"),
            data: values,
            backgroundColor: palette.accent,
            yAxisID: "y",
            order: 2,
          },
          {
            type: "line",
            label: seriesLabel(chartSpec, 1, "% acumulado"),
            data: cum,
            borderColor: palette.primary,
            backgroundColor: "transparent",
            yAxisID: "y1",
            tension: 0.25,
            order: 1,
          },
        ],
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "bottom", labels: { boxWidth: 12, font: { family: "DM Sans", size: 11 } } },
        },
        scales: {
          x: { beginAtZero: true, grid: { color: "rgba(15,23,42,0.06)" } },
          y: { grid: { display: false }, ticks: { font: { size: 11 } } },
          y1: {
            position: "right",
            min: 0,
            max: 100,
            grid: { drawOnChartArea: false },
            ticks: {
              callback: function (v) {
                return v + "%";
              },
            },
          },
        },
      },
    });
  }

  function barChart(canvas, chartSpec, color) {
    if (!canvas || !global.Chart) return null;
    const labels = cats(chartSpec);
    if (!labels.length) return null;
    const values = seriesVals(chartSpec, 0);
    return new global.Chart(canvas.getContext("2d"), {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: seriesLabel(chartSpec, 0, "Valor"),
            data: values,
            backgroundColor: color || palette.primary,
          },
        ],
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { beginAtZero: true, grid: { color: "rgba(15,23,42,0.06)" } },
          y: { grid: { display: false }, ticks: { font: { size: 11 } } },
        },
      },
    });
  }

  function renderOrEmpty(wrapId, canvasId, chartSpec, factory) {
    if (!chartSpec || chartSpec.empty_reason || !(cats(chartSpec).length)) {
      showEmpty(wrapId, (chartSpec && chartSpec.empty_reason) || "Dados insuficientes para esta visualização.");
      return null;
    }
    const canvas = ensureCanvas(wrapId, canvasId);
    return factory(canvas, chartSpec);
  }

  global.BioMedExecutiveCharts = {
    palette: palette,
    destroyIfAny: destroyIfAny,
    paretoChart: paretoChart,
    barChart: barChart,
    lineChart: lineChart,
    showEmpty: showEmpty,
    renderOrEmpty: renderOrEmpty,
  };
})(typeof window !== "undefined" ? window : this);
