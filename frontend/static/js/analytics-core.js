/**
 * RC25 Analytics core page — NEW DOM composition.
 * SOURCE_API=/api/dashboard — field mapping only, no recalculation.
 */
(function () {
  "use strict";
  var BC = window.BioMedCore;
  if (!BC || !BC.requireAuth("/dashboard")) return;

  var elCompany = document.getElementById("bc-company");
  var globalEmpty = document.getElementById("bc-global-empty");
  var abortCtrl = null;

  function setMetric(id, value, digits) {
    var node = document.getElementById(id);
    if (node) node.textContent = BC.fmtNum(value, digits);
  }

  function labelsFrom(rows, keys) {
    return (rows || []).map(function (r) {
      for (var i = 0; i < keys.length; i++) {
        if (r[keys[i]] != null && r[keys[i]] !== "") return String(r[keys[i]]);
      }
      return "—";
    });
  }

  function valuesFrom(rows, keys) {
    return (rows || []).map(function (r) {
      for (var i = 0; i < keys.length; i++) {
        var n = Number(r[keys[i]]);
        if (Number.isFinite(n)) return n;
      }
      return 0;
    });
  }

  function paintHeatmap(hm) {
    var root = document.getElementById("heatmapRoot");
    var empty = document.getElementById("empty-heatmap");
    if (!root) return;
    var setores = (hm && hm.setores) || [];
    var meses = (hm && hm.meses) || [];
    var dados = (hm && hm.dados) || [];
    if (!setores.length || !meses.length || !dados.length) {
      root.innerHTML = "";
      if (empty) empty.hidden = false;
      return;
    }
    if (empty) empty.hidden = true;
    var max = 0;
    dados.forEach(function (row) {
      (row || []).forEach(function (v) {
        var n = Number(v) || 0;
        if (n > max) max = n;
      });
    });
    var html = '<table class="bc-heatmap"><thead><tr><th>Setor</th>';
    meses.forEach(function (m) {
      html += "<th>" + m + "</th>";
    });
    html += "</tr></thead><tbody>";
    setores.forEach(function (setor, i) {
      html += "<tr><td>" + setor + "</td>";
      (dados[i] || []).forEach(function (v) {
        var n = Number(v) || 0;
        var t = max > 0 ? n / max : 0;
        var bg =
          "rgba(26, 69, 102, " + (0.08 + t * 0.72).toFixed(2) + ")";
        var color = t > 0.55 ? "#fff" : "#132033";
        html +=
          '<td style="background:' +
          bg +
          ";color:" +
          color +
          '">' +
          (n ? BC.fmtNum(n, 1) : "·") +
          "</td>";
      });
      html += "</tr>";
    });
    html += "</tbody></table>";
    root.innerHTML = html;
  }

  async function load() {
    elCompany.textContent = BC.clientName();
    var cid = BC.clientId();
    if (!cid) {
      globalEmpty.hidden = false;
      return;
    }
    globalEmpty.hidden = true;

    if (abortCtrl) abortCtrl.abort();
    abortCtrl = typeof AbortController !== "undefined" ? new AbortController() : null;

    var mesInicio = document.getElementById("mesInicio").value;
    var mesFim = document.getElementById("mesFim").value;
    var url = "/api/dashboard?client_id=" + encodeURIComponent(cid);
    if (mesInicio) url += "&mes_inicio=" + encodeURIComponent(mesInicio);
    if (mesFim) url += "&mes_fim=" + encodeURIComponent(mesFim);

    var res = await BC.api(
      url,
      abortCtrl ? { signal: abortCtrl.signal } : undefined
    );
    if (!res.ok) throw new Error("dashboard " + res.status);
    var data = await res.json();
    var m = BC.mapDashboardMetrics(data.metricas || {});

    setMetric("m-colab", m.colaboradores, 0);
    setMetric("m-atest", m.atestados, 0);
    setMetric("m-dias", m.dias, 1);
    setMetric("m-horas", m.horas, 1);
    setMetric("m-freq", m.frequencia, 2);
    setMetric("m-dur", m.duracao_media, 2);

    var custo = Number(
      (data.metricas || {}).custo_estimado != null
        ? data.metricas.custo_estimado
        : (data.metricas || {}).custo
    );
    var custoWrap = document.getElementById("m-custo-wrap");
    if (custoWrap) {
      if (Number.isFinite(custo) && custo > 0) {
        custoWrap.hidden = false;
        setMetric("m-custo", custo, 0);
      } else {
        custoWrap.hidden = true;
      }
    }

    var evol = data.evolucao_mensal || [];
    document.getElementById("empty-evolucao").hidden = evol.length > 0;
    if (evol.length) {
      BC.lineChart(
        document.getElementById("chartEvolucao"),
        labelsFrom(evol, ["mes", "periodo", "label"]),
        [
          {
            label: "Dias",
            data: valuesFrom(evol, ["total_dias", "dias", "dias_perdidos", "valor"]),
          },
          {
            label: "Atestados",
            data: valuesFrom(evol, ["total_atestados", "atestados", "quantidade", "total"]),
          },
        ]
      );
      BC.barChart(
        document.getElementById("chartSazonal"),
        labelsFrom(evol, ["mes", "periodo", "label"]),
        valuesFrom(evol, ["total_atestados", "atestados", "quantidade", "total"]),
        "rgba(42, 107, 90, 0.78)"
      );
    }

    BC.barChart(
      document.getElementById("chartSetores"),
      labelsFrom(data.top_setores, ["setor", "nome", "label"]),
      valuesFrom(data.top_setores, ["total", "total_dias", "dias", "quantidade"])
    );
    BC.barChart(
      document.getElementById("chartCentro"),
      labelsFrom(data.dias_centro_custo, ["centro_custo", "nome", "label"]),
      valuesFrom(data.dias_centro_custo, ["total_dias", "dias", "total"]),
      "rgba(42, 107, 90, 0.8)"
    );

    var escalas = data.top_escalas || [];
    document.getElementById("empty-escalas").hidden = escalas.length > 0;
    if (escalas.length) {
      BC.barChart(
        document.getElementById("chartEscalas"),
        labelsFrom(escalas, ["escala", "nome", "label", "turno"]),
        valuesFrom(escalas, ["total", "total_dias", "dias", "quantidade"]),
        "rgba(166, 124, 42, 0.85)"
      );
    }

    BC.barChart(
      document.getElementById("chartCids"),
      labelsFrom(data.top_cids, ["diagnostico", "descricao", "cid", "nome"]),
      valuesFrom(data.top_cids, ["total", "quantidade", "total_dias"])
    );
    BC.barChart(
      document.getElementById("chartMotivos"),
      labelsFrom(data.top_motivos, ["motivo", "motivo_atestado", "nome"]),
      valuesFrom(data.top_motivos, ["total", "quantidade", "total_dias"]),
      "rgba(196, 92, 38, 0.8)"
    );
    BC.doughnutChart(
      document.getElementById("chartDias"),
      labelsFrom(data.distribuicao_dias, ["faixa", "label", "dias"]),
      valuesFrom(data.distribuicao_dias, ["total", "quantidade", "valor"])
    );
    BC.doughnutChart(
      document.getElementById("chartGenero"),
      labelsFrom(data.distribuicao_genero, ["genero", "label", "nome"]),
      valuesFrom(data.distribuicao_genero, ["total", "quantidade", "valor"])
    );

    var freq = data.frequencia_atestados || [];
    BC.barChart(
      document.getElementById("chartRecorrencia"),
      labelsFrom(freq.slice(0, 10), ["nome", "funcionario", "nomecompleto", "label"]),
      valuesFrom(freq.slice(0, 10), ["total", "quantidade", "atestados", "frequencia"]),
      "rgba(143, 47, 42, 0.78)"
    );

    paintHeatmap(data.heatmap_setores_meses || {});

    var prod = data.produtividade || [];
    document.getElementById("empty-prod").hidden = prod.length > 0;
    if (prod.length) {
      BC.barChart(
        document.getElementById("chartProd"),
        labelsFrom(prod, ["tipo_consulta", "categoria", "mes_referencia", "label"]),
        valuesFrom(prod, ["total", "valor", "horas"])
      );
    }

    window.__RC25_ANALYTICS_LAST__ = {
      metricas: data.metricas || {},
      mapped: m,
      SOURCE_API: "/api/dashboard",
    };
  }

  document.getElementById("bc-apply").addEventListener("click", function () {
    load().catch(function (e) {
      if (e && e.name === "AbortError") return;
      console.error(e);
    });
  });
  document.getElementById("bc-reload").addEventListener("click", function () {
    load().catch(function (e) {
      if (e && e.name === "AbortError") return;
      console.error(e);
    });
  });

  load().catch(function (e) {
    if (e && e.name === "AbortError") return;
    console.error(e);
    globalEmpty.hidden = false;
    globalEmpty.innerHTML =
      "<strong>Não foi possível carregar</strong>Verifique empresa ativa e autenticação.";
  });
})();
