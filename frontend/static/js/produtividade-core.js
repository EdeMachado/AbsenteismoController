(function () {
  "use strict";
  var BC = window.BioMedCore;
  if (!BC || !BC.requireAuth("/produtividade")) return;
  document.getElementById("bc-company").textContent = BC.clientName();

  async function load() {
    var cid = BC.clientId();
    if (!cid) return;
    var dashR = await BC.api("/api/dashboard?client_id=" + encodeURIComponent(cid));
    var prodR = await BC.api("/api/produtividade?client_id=" + encodeURIComponent(cid));
    var evolR = await BC.api("/api/produtividade/evolucao?client_id=" + encodeURIComponent(cid));

    if (dashR.ok) {
      var dash = await dashR.json();
      var m = BC.mapDashboardMetrics(dash.metricas || {});
      document.getElementById("p-horas").textContent = BC.fmtNum(m.horas, 1);
      document.getElementById("p-dias").textContent = BC.fmtNum(m.dias, 1);
      BC.barChart(
        document.getElementById("chartSetores"),
        (dash.top_setores || []).map(function (r) { return r.setor || r.nome || ""; }),
        (dash.top_setores || []).map(function (r) {
          return Number(r.total || r.total_dias || r.quantidade || 0);
        }),
        "rgba(196, 92, 38, 0.85)"
      );
      window.__RC25_PROD_LAST__ = { metricas: dash.metricas || {}, mapped: m };
    }

    if (prodR.ok) {
      var prod = await prodR.json();
      var list = Array.isArray(prod) ? prod : prod.items || prod.dados || [];
      document.getElementById("p-regs").textContent = BC.fmtNum(list.length, 0);
      var total = list.reduce(function (s, r) { return s + Number(r.total || 0); }, 0);
      document.getElementById("p-total").textContent = BC.fmtNum(total, 0);
      BC.barChart(
        document.getElementById("chartTipos"),
        list.slice(0, 12).map(function (r) {
          return r.tipo_consulta || r.categoria || r.mes_referencia || "";
        }),
        list.slice(0, 12).map(function (r) { return Number(r.total || 0); })
      );
    }

    if (evolR.ok) {
      var evol = await evolR.json();
      var series = Array.isArray(evol) ? evol : evol.evolucao || evol.items || [];
      BC.lineChart(
        document.getElementById("chartEvol"),
        series.map(function (r) { return r.mes || r.mes_referencia || r.label || ""; }),
        [
          {
            label: "Total",
            data: series.map(function (r) { return Number(r.total || r.valor || 0); }),
          },
        ]
      );
    }
  }

  load().catch(console.error);
})();
