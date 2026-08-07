/**
 * RC25 Presentation v2.1 surface — new composition.
 * Uses /api/dashboard metrics (same calculations). Not Presentation Premium.
 */
(function () {
  "use strict";
  var BC = window.BioMedCore;
  if (!BC || !BC.requireAuth("/apresentacao")) return;

  var slides = [];
  var idx = 0;
  var stage = document.getElementById("bc-stage");
  var indicator = document.getElementById("bc-indicator");

  function render() {
    if (!slides.length) {
      stage.innerHTML =
        '<div class="bc-empty" style="color:#fff"><strong>Sem conteúdo</strong>Não há dados para montar a apresentação desta empresa.</div>';
      indicator.textContent = "— / —";
      return;
    }
    stage.innerHTML = slides[idx].html;
    indicator.textContent = idx + 1 + " / " + slides.length;
    if (slides[idx].paint) slides[idx].paint();
  }

  function buildSlides(data) {
    var m = BC.mapDashboardMetrics(data.metricas || {});
    var company = BC.clientName();
    var list = [];

    list.push({
      html:
        "<div><p style='letter-spacing:0.08em;text-transform:uppercase;opacity:0.7;font-size:0.8rem;font-weight:700'>BioMed Platform</p>" +
        "<h2>" +
        company +
        "</h2><p>Leitura de absenteísmo para decisão — indicadores da base operacional existente.</p></div>",
    });

    list.push({
      html:
        "<div><h2>Indicadores principais</h2><p>Leitura consolidada da base operacional</p>" +
        '<div class="bc-metrics" style="margin-top:1.5rem">' +
        metric("Atestados", m.atestados, 0) +
        metric("Dias perdidos", m.dias, 1) +
        metric("Horas perdidas", m.horas, 1) +
        metric("Colaboradores", m.colaboradores, 0) +
        "</div></div>",
    });

    list.push({
      html:
        "<div><h2>Evolução</h2><p>Tendência mensal de dias perdidos</p><div class='bc-card' style='background:rgba(255,255,255,0.06);border-color:rgba(255,255,255,0.12);margin-top:1rem'><div class='bc-chart is-tall'><canvas id='deckEvol'></canvas></div></div></div>",
      paint: function () {
        var evol = data.evolucao_mensal || [];
        BC.lineChart(
          document.getElementById("deckEvol"),
          evol.map(function (r) { return r.mes || r.periodo || r.label || ""; }),
          [
            {
              label: "Dias",
              data: evol.map(function (r) {
                return Number(r.total_dias || r.dias || r.dias_perdidos || 0);
              }),
            },
          ]
        );
      },
    });

    list.push({
      html:
        "<div><h2>Principais causas</h2><p>CID e diagnósticos de maior concentração</p><div class='bc-card' style='background:rgba(255,255,255,0.06);border-color:rgba(255,255,255,0.12);margin-top:1rem'><div class='bc-chart is-tall'><canvas id='deckCid'></canvas></div></div></div>",
      paint: function () {
        var rows = data.top_cids || [];
        BC.barChart(
          document.getElementById("deckCid"),
          rows.map(function (r) { return r.diagnostico || r.cid || r.nome || ""; }),
          rows.map(function (r) { return Number(r.total || r.quantidade || r.total_dias || 0); }),
          "rgba(255,255,255,0.75)"
        );
      },
    });

    list.push({
      html:
        "<div><h2>Setores críticos</h2><p>Onde o absenteísmo se concentra</p><div class='bc-card' style='background:rgba(255,255,255,0.06);border-color:rgba(255,255,255,0.12);margin-top:1rem'><div class='bc-chart is-tall'><canvas id='deckSetor'></canvas></div></div></div>",
      paint: function () {
        var rows = data.top_setores || [];
        BC.barChart(
          document.getElementById("deckSetor"),
          rows.map(function (r) { return r.setor || r.nome || ""; }),
          rows.map(function (r) { return Number(r.total || r.total_dias || r.quantidade || 0); }),
          "rgba(42, 107, 90, 0.9)"
        );
      },
    });

    list.push({
      html:
        "<div><h2>Impacto</h2><p>Mesmos campos de métricas — leitura executiva</p>" +
        '<div class="bc-metrics" style="margin-top:1.5rem">' +
        metric("Frequência", m.frequencia, 2) +
        metric("Duração média (dias)", m.duracao_media, 2) +
        metric("Horas perdidas", m.horas, 1) +
        "</div></div>",
    });

    list.push({
      html:
        "<div><h2>Conclusão</h2><p>Os números desta apresentação vêm da mesma API operacional (`/api/dashboard`). Próximo passo: priorizar setores e causas com maior concentração.</p></div>",
    });

    return list;
  }

  function metric(label, value, digits) {
    return (
      '<div class="bc-metric"><small>' +
      label +
      "</small><strong>" +
      BC.fmtNum(value, digits) +
      "</strong></div>"
    );
  }

  async function load() {
    var cid = BC.clientId();
    if (!cid) {
      stage.innerHTML =
        '<div class="bc-empty" style="color:#fff"><strong>Selecione uma empresa</strong></div>';
      return;
    }
    var res = await BC.api("/api/dashboard?client_id=" + encodeURIComponent(cid));
    if (!res.ok) throw new Error("dashboard " + res.status);
    var data = await res.json();
    slides = buildSlides(data);
    idx = 0;
    render();
    window.__RC25_PRESENTATION_LAST__ = {
      metricas: data.metricas || {},
      mapped: BC.mapDashboardMetrics(data.metricas || {}),
    };
  }

  document.getElementById("bc-prev").addEventListener("click", function () {
    if (idx > 0) {
      idx -= 1;
      render();
    }
  });
  document.getElementById("bc-next").addEventListener("click", function () {
    if (idx < slides.length - 1) {
      idx += 1;
      render();
    }
  });
  document.getElementById("bc-fs").addEventListener("click", function () {
    var deck = document.getElementById("bc-deck");
    if (!document.fullscreenElement) deck.requestFullscreen().catch(function () {});
    else document.exitFullscreen().catch(function () {});
  });

  load().catch(function (e) {
    console.error(e);
    stage.innerHTML =
      '<div class="bc-empty" style="color:#fff"><strong>Falha ao carregar</strong></div>';
  });
})();
