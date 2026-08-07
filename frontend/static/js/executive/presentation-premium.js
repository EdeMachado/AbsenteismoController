/**
 * RC-1.4 — Executive Presentation Premium renderer (screen + preview).
 * Fullscreen-capable. Keyboard / buttons / touch. One question per slide.
 */
(function (global) {
  "use strict";

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function money(v) {
    if (v == null || isNaN(Number(v))) return "—";
    return (
      "R$ " +
      Number(v).toLocaleString("pt-BR", {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      })
    );
  }

  function num(v) {
    if (v == null || isNaN(Number(v))) return "—";
    return Number(v).toLocaleString("pt-BR", { maximumFractionDigits: 1 });
  }

  function confBadge(label) {
    var cls = "bm-rc14-conf";
    if (/alta/i.test(label || "")) cls += " is-high";
    else if (/moderada/i.test(label || "")) cls += " is-mid";
    else cls += " is-low";
    return '<span class="' + cls + '">' + esc(label || "Evidência insuficiente") + "</span>";
  }

  function insight(s) {
    if (!s.insight && !s.leitura) return "";
    return (
      '<p class="bm-rc14-insight"><strong>Executive Insight.</strong> ' +
      esc(s.insight || s.leitura) +
      "</p>"
    );
  }

  function miniBars(chart) {
    if (!chart) return "";
    var cats = (chart.categories || []).slice(0, 6);
    var series = chart.series || [];
    var vals = (series[0] && series[0].data) || [];
    if (!cats.length) return '<p class="bm-rc14-muted">Dados insuficientes para esta visualização.</p>';
    var max = Math.max.apply(null, vals.map(Number).concat([1]));
    return (
      '<div class="bm-rc14-bars">' +
      cats
        .map(function (c, i) {
          var v = Number(vals[i] || 0);
          var pct = Math.max(4, Math.round((v / max) * 100));
          return (
            '<div class="bm-rc14-bar"><span class="bm-rc14-bar__l">' +
            esc(c) +
            '</span><span class="bm-rc14-bar__t"><i style="width:' +
            pct +
            '%"></i></span><span class="bm-rc14-bar__v">' +
            esc(num(v)) +
            "</span></div>"
          );
        })
        .join("") +
      "</div>"
    );
  }

  function renderSlideHtml(s) {
    var q = s.question
      ? '<p class="bm-rc14-q">' + esc(s.question) + "</p>"
      : "";
    var head =
      '<header class="bm-rc14-head">' +
      q +
      "<h1>" +
      esc(s.title) +
      "</h1>" +
      confBadge(s.confianca_label) +
      "</header>";

    if (s.kind === "cover" || s.id === "cover") {
      var c = s.cover || {};
      return (
        '<section class="bm-rc14-slide bm-rc14-cover" data-id="cover">' +
        '<div class="bm-rc14-cover__veil"></div>' +
        '<div class="bm-rc14-cover__inner">' +
        '<p class="bm-rc14-eyebrow">' +
        esc(c.eyebrow || "BioMed Executive Intelligence") +
        "</p>" +
        "<h1>" +
        esc(c.company || "") +
        "</h1>" +
        '<p class="bm-rc14-cover__period">' +
        esc(c.period || "") +
        "</p>" +
        "</div></section>"
      );
    }

    if (s.kind === "state" || s.id === "state") {
      return (
        '<section class="bm-rc14-slide bm-rc14-state" data-id="state">' +
        head +
        '<p class="bm-rc14-state__phrase">' +
        esc(s.state_phrase || s.leitura || "") +
        "</p></section>"
      );
    }

    if (s.kind === "financial" || s.id === "financial") {
      var f = s.financial || {};
      var premissa = f.premissa || "NÃO INFORMADO";
      var custoBlock = f.calculavel
        ? '<div class="bm-rc14-fin__hero"><span>Custo estimado</span><strong>' +
          esc(money(f.custo)) +
          '</strong><em class="bm-rc14-premissa">' +
          esc(premissa) +
          "</em></div>"
        : '<div class="bm-rc14-fin__hero is-na"><span>Custo estimado</span><strong>Custo hora não informado</strong><em class="bm-rc14-premissa">' +
          esc(premissa) +
          "</em></div>";
      return (
        '<section class="bm-rc14-slide" data-id="financial">' +
        head +
        '<div class="bm-rc14-fin">' +
        custoBlock +
        '<div class="bm-rc14-fin__grid">' +
        "<div><span>Horas perdidas</span><strong>" +
        esc(num(f.horas)) +
        "</strong></div>" +
        "<div><span>Dias perdidos</span><strong>" +
        esc(num(f.dias)) +
        "</strong></div>" +
        "<div><span>Custo hora</span><strong>" +
        (f.custo_hora != null ? esc(money(f.custo_hora)) + "/h" : "—") +
        "</strong></div>" +
        "</div>" +
        '<p class="bm-rc14-muted">Cálculo: ' +
        esc(f.formula || "HORAS PERDIDAS × CUSTO HORA") +
        ". Impacto direto das horas — sem custos indiretos nesta versão.</p>" +
        insight(s) +
        "</div></section>"
      );
    }

    if (s.chart && (s.kind === "where" || s.kind === "causes" || s.kind === "changed" || s.id === "where" || s.id === "causes" || s.id === "changed" || s.id === "setores" || s.id === "cid" || s.id === "evolucao")) {
      return (
        '<section class="bm-rc14-slide" data-id="' +
        esc(s.id) +
        '">' +
        head +
        miniBars(s.chart) +
        insight(s) +
        "</section>"
      );
    }

    if (s.recorrencia || s.kind === "recurrence") {
      var r = s.recorrencia || {};
      return (
        '<section class="bm-rc14-slide" data-id="recurrence">' +
        head +
        '<div class="bm-rc14-fin__grid">' +
        "<div><span>2 ou mais eventos</span><strong>" +
        esc(r.n_2plus != null ? r.n_2plus : "—") +
        "</strong></div>" +
        "<div><span>3 ou mais</span><strong>" +
        esc(r.n_3plus != null ? r.n_3plus : "—") +
        "</strong></div>" +
        "<div><span>5 ou mais</span><strong>" +
        esc(r.n_5plus != null ? r.n_5plus : "—") +
        "</strong></div></div>" +
        insight(s) +
        "</section>"
      );
    }

    if (s.padroes || s.kind === "when") {
      var p = s.padroes || {};
      var wd = p.dia_semana || p.weekday || {};
      var rows = Object.keys(wd)
        .slice(0, 7)
        .map(function (k) {
          return "<li><strong>" + esc(k) + "</strong> · " + esc(wd[k]) + "</li>";
        })
        .join("");
      return (
        '<section class="bm-rc14-slide" data-id="when">' +
        head +
        (rows ? '<ul class="bm-rc14-list">' + rows + "</ul>" : '<p class="bm-rc14-muted">Sem padrão temporal válido.</p>') +
        insight(s) +
        "</section>"
      );
    }

    if (s.biomed || s.kind === "biomed") {
      var b = s.biomed || {};
      return (
        '<section class="bm-rc14-slide" data-id="biomed">' +
        head +
        '<div class="bm-rc14-fin__grid">' +
        "<div><span>Ações realizadas</span><strong>" +
        esc(b.realizadas != null ? b.realizadas : "—") +
        "</strong></div>" +
        "<div><span>Concluídas</span><strong>" +
        esc(b.concluidas != null ? b.concluidas : "—") +
        "</strong></div>" +
        "<div><span>Pendentes</span><strong>" +
        esc(b.pendentes != null ? b.pendentes : "—") +
        "</strong></div></div>" +
        (b.condicionantes ? "<p>" + esc(b.condicionantes) + "</p>" : "") +
        '<p class="bm-rc14-muted">' +
        esc(b.nota || "") +
        "</p>" +
        insight(s) +
        "</section>"
      );
    }

    if (s.savings || s.kind === "savings") {
      var sv = s.savings || {};
      return (
        '<section class="bm-rc14-slide" data-id="savings">' +
        head +
        '<div class="bm-rc14-fin__hero"><span>Potencial de melhoria</span><strong>' +
        esc(money(sv.valor)) +
        '</strong><em class="bm-rc14-premissa">' +
        esc(sv.premissa || "") +
        "</em></div>" +
        '<p class="bm-rc14-muted">Não é promessa de economia. Premissa explícita.</p>' +
        insight(s) +
        "</section>"
      );
    }

    if (s.inaction || s.kind === "inaction") {
      var ina = s.inaction || {};
      return (
        '<section class="bm-rc14-slide" data-id="inaction">' +
        head +
        '<div class="bm-rc14-fin__hero"><span>Custo de não agir</span><strong>' +
        esc(money(ina.valor)) +
        '</strong><em class="bm-rc14-premissa">' +
        esc(ina.premissa || "") +
        "</em></div>" +
        insight(s) +
        "</section>"
      );
    }

    if (s.priorities || s.kind === "priorities") {
      var items = s.priorities || [];
      return (
        '<section class="bm-rc14-slide" data-id="priorities">' +
        head +
        '<div class="bm-rc14-prio">' +
        items
          .map(function (a) {
            return (
              '<article><em>' +
              esc(a.prioridade) +
              "</em><h3>" +
              esc(a.acao) +
              "</h3><p>" +
              esc(a.problema) +
              '</p><dl><div><dt>Impacto</dt><dd>' +
              esc(a.impacto) +
              "</dd></div><div><dt>Prazo</dt><dd>" +
              esc(a.prazo) +
              "</dd></div></dl></article>"
            );
          })
          .join("") +
        "</div>" +
        insight(s) +
        "</section>"
      );
    }

    if (s.roadmap || s.kind === "roadmap") {
      return (
        '<section class="bm-rc14-slide" data-id="roadmap">' +
        head +
        '<div class="bm-rc14-road">' +
        (s.roadmap || [])
          .map(function (r) {
            return (
              "<div><strong>" +
              esc(r.horizon) +
              "</strong><span>" +
              esc(r.focus) +
              "</span></div>"
            );
          })
          .join("") +
        "</div>" +
        insight(s) +
        "</section>"
      );
    }

    if (s.decisions || s.kind === "decision") {
      return (
        '<section class="bm-rc14-slide" data-id="decision">' +
        head +
        '<ol class="bm-rc14-decisions">' +
        (s.decisions || [])
          .map(function (d) {
            return (
              "<li><strong>" +
              esc(d.titulo) +
              "</strong><span>" +
              esc(d.detalhe) +
              "</span></li>"
            );
          })
          .join("") +
        "</ol>" +
        insight(s) +
        "</section>"
      );
    }

    if (s.closing || s.kind === "closing") {
      var cl = s.closing || {};
      return (
        '<section class="bm-rc14-slide bm-rc14-closing" data-id="closing">' +
        '<p class="bm-rc14-eyebrow">Encerramento</p>' +
        '<div class="bm-rc14-fin__grid bm-rc14-closing__grid">' +
        "<div><span>" +
        esc(cl.perda_label || "Perda atual") +
        "</span><strong>" +
        (cl.perda != null ? esc(money(cl.perda)) : esc(num(cl.perda_alt))) +
        "</strong></div>" +
        "<div><span>Potencial de melhoria</span><strong>" +
        esc(cl.economia != null ? money(cl.economia) : "—") +
        "</strong></div>" +
        "<div><span>Prioridade nº 1</span><strong>" +
        esc(cl.prioridade || "—") +
        "</strong></div>" +
        "<div><span>Próxima revisão</span><strong>" +
        esc(cl.proxima_revisao || "—") +
        "</strong></div></div>" +
        '<footer class="bm-rc14-sign"><strong>' +
        esc(cl.signature || "BioMed Executive Signature") +
        "</strong><p>" +
        esc(cl.tagline || "Transformando evidências em decisões.") +
        "</p></footer></section>"
      );
    }

    // Fallback legacy
    return (
      '<section class="bm-rc14-slide" data-id="' +
      esc(s.id) +
      '">' +
      head +
      (s.leitura ? "<p>" + esc(s.leitura) + "</p>" : "") +
      (s.chart ? miniBars(s.chart) : "") +
      "</section>"
    );
  }

  function mount(root, deck, opts) {
    opts = opts || {};
    if (!root || !deck) return null;
    var slides = deck.slides || [];
    var idx = 0;
    var progress = root.querySelector("[data-rc14-progress]");
    var stage = root.querySelector("[data-rc14-stage]");
    var counter = root.querySelector("[data-rc14-counter]");

    function paint() {
      if (!slides.length) {
        stage.innerHTML = '<p class="bm-rc14-muted">Nenhum slide aplicável para o período.</p>';
        return;
      }
      idx = Math.max(0, Math.min(idx, slides.length - 1));
      stage.innerHTML = renderSlideHtml(slides[idx]);
      if (counter) counter.textContent = idx + 1 + " / " + slides.length;
      if (progress) {
        progress.style.width = ((idx + 1) / slides.length) * 100 + "%";
      }
      root.setAttribute("data-slide", slides[idx].id || String(idx));
      if (opts.onChange) opts.onChange(idx, slides[idx]);
    }

    function go(n) {
      idx = n;
      paint();
    }
    function next() {
      go(idx + 1);
    }
    function prev() {
      go(idx - 1);
    }

    paint();
    return { next: next, prev: prev, go: go, paint: paint, getIndex: function () { return idx; }, slides: slides };
  }

  global.BioMedPresentationPremium = {
    mount: mount,
    renderSlideHtml: renderSlideHtml,
  };
})(window);
