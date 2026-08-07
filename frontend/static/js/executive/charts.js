/**
 * BioMed Executive — Chart.js helpers (no formula duplication).
 * Accepts ChartSeries payload: { categories, series:[{name,data}] }.
 */
(function (global) {
  "use strict";

  const palette = {
    primary: "#1f4b6e",
    accent: "#2f6f5e",
    muted: "#94A3B8",
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

  function paretoChart(canvas, chartSpec) {
    if (!canvas || !global.Chart) return null;
    const labels = cats(chartSpec);
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
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "bottom", labels: { boxWidth: 12, font: { family: "DM Sans" } } },
        },
        scales: {
          y: { beginAtZero: true, grid: { color: "rgba(15,23,42,0.06)" } },
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
          x: { ticks: { maxRotation: 45, font: { size: 11 } } },
        },
      },
    });
  }

  function barChart(canvas, chartSpec, color) {
    if (!canvas || !global.Chart) return null;
    const labels = cats(chartSpec);
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
        indexAxis: labels.length > 6 ? "y" : "x",
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { beginAtZero: true, grid: { color: "rgba(15,23,42,0.06)" } },
          y: { grid: { display: false } },
        },
      },
    });
  }

  global.BioMedExecutiveCharts = {
    palette: palette,
    destroyIfAny: destroyIfAny,
    paretoChart: paretoChart,
    barChart: barChart,
  };
})(typeof window !== "undefined" ? window : this);
