(function () {
  "use strict";
  var BC = window.BioMedCore;
  if (!BC || !BC.requireAuth("/comparativos")) return;
  document.getElementById("bc-company").textContent = BC.clientName();

  function pick(obj, keys) {
    obj = obj || {};
    for (var i = 0; i < keys.length; i++) {
      if (obj[keys[i]] != null && obj[keys[i]] !== "") return obj[keys[i]];
    }
    return 0;
  }

  async function run() {
    var cid = BC.clientId();
    if (!cid) {
      alert("Selecione uma empresa.");
      return;
    }
    var p1i = document.getElementById("p1i").value;
    var p1f = document.getElementById("p1f").value;
    var p2i = document.getElementById("p2i").value;
    var p2f = document.getElementById("p2f").value;
    if (!p1i || !p1f || !p2i || !p2f) {
      alert("Preencha os quatro meses.");
      return;
    }
    var url =
      "/api/relatorios/comparativo?client_id=" +
      encodeURIComponent(cid) +
      "&periodo1_inicio=" +
      encodeURIComponent(p1i) +
      "&periodo1_fim=" +
      encodeURIComponent(p1f) +
      "&periodo2_inicio=" +
      encodeURIComponent(p2i) +
      "&periodo2_fim=" +
      encodeURIComponent(p2f);
    var res = await BC.api(url);
    if (!res.ok) throw new Error("comparativo " + res.status);
    var data = await res.json();
    var p1 = data.periodo1 || data.periodo_1 || data.p1 || {};
    var p2 = data.periodo2 || data.periodo_2 || data.p2 || {};
    var d1 = Number(pick(p1, ["total_dias_perdidos", "dias", "total_dias"]));
    var d2 = Number(pick(p2, ["total_dias_perdidos", "dias", "total_dias"]));
    var a1 = Number(pick(p1, ["total_atestados", "atestados", "total_registros"]));
    var a2 = Number(pick(p2, ["total_atestados", "atestados", "total_registros"]));
    document.getElementById("c-d1").textContent = BC.fmtNum(d1, 1);
    document.getElementById("c-d2").textContent = BC.fmtNum(d2, 1);
    document.getElementById("c-dv").textContent = BC.fmtNum(d2 - d1, 1);
    document.getElementById("c-a1").textContent = BC.fmtNum(a1, 0);
    document.getElementById("c-a2").textContent = BC.fmtNum(a2, 0);
    document.getElementById("c-av").textContent = BC.fmtNum(a2 - a1, 0);
    BC.barChart(
      document.getElementById("chartComp"),
      ["Dias P1", "Dias P2", "Atestados P1", "Atestados P2"],
      [d1, d2, a1, a2]
    );
    window.__RC25_COMPARATIVOS_LAST__ = { raw: data, d1: d1, d2: d2, a1: a1, a2: a2 };
  }

  // defaults: last month vs previous
  var now = new Date();
  var m2 = new Date(now.getFullYear(), now.getMonth() - 1, 1);
  var m1 = new Date(now.getFullYear(), now.getMonth() - 2, 1);
  function ym(d) {
    return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0");
  }
  document.getElementById("p1i").value = ym(m1);
  document.getElementById("p1f").value = ym(m1);
  document.getElementById("p2i").value = ym(m2);
  document.getElementById("p2f").value = ym(m2);
  document.getElementById("bc-run").addEventListener("click", function () {
    run().catch(console.error);
  });
  if (BC.clientId()) run().catch(console.error);
})();
