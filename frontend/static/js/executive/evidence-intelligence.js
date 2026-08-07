/**
 * EXEC-10 — BioMed Evidence Intelligence™ renderer.
 * Answers: "Como sabemos disso?" — no new analysis, no commercial CTA.
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

  function fmtNum(n) {
    if (n == null || isNaN(Number(n))) return "—";
    return Number(n).toLocaleString("pt-BR", { maximumFractionDigits: 1 });
  }

  function miniBars(categories, values) {
    const cats = categories || [];
    const vals = values || [];
    const max = Math.max.apply(null, vals.map(Number).concat([1]));
    if (!cats.length) {
      return '<p class="bm-ei-empty">Comparação indisponível para este período.</p>';
    }
    return cats
      .map(function (c, i) {
        const v = Number(vals[i] || 0);
        const pct = Math.max(4, Math.round((v / max) * 100));
        return (
          '<div class="bm-dx-bar">' +
          '<div class="bm-dx-bar__label">' +
          esc(c) +
          "</div>" +
          '<div class="bm-dx-bar__track"><span style="width:' +
          pct +
          '%"></span></div>' +
          '<div class="bm-dx-bar__val">' +
          esc(fmtNum(v)) +
          "</div></div>"
        );
      })
      .join("");
  }

  function render(root, ei, handlers) {
    if (!root || !ei) return;
    handlers = handlers || {};
    const h = ei.header || {};
    const q = ei.quality || {};
    const conf = ei.confidence || {};
    const tv = ei.timeline_visual || {};

    const summaryHtml = (ei.summary || [])
      .slice(0, 3)
      .map(function (s) {
        return "<p>" + esc(s) + "</p>";
      })
      .join("");

    const sourcesHtml = (ei.sources || [])
      .map(function (s) {
        return (
          '<article class="bm-ei-source"><h3>' +
          esc(s.label) +
          "</h3><p>" +
          esc(s.role) +
          "</p></article>"
        );
      })
      .join("");

    const chartSrcHtml = (ei.chart_sources || [])
      .map(function (c) {
        return '<li>' + esc(c.label) + "</li>";
      })
      .join("");

    const dimsHtml = (q.dimensions || [])
      .map(function (d) {
        return (
          '<div class="bm-dx-chip"><span>' +
          esc(d.label) +
          "</span><strong>" +
          esc(d.score != null ? fmtNum(d.score) : "—") +
          "</strong></div>"
        );
      })
      .join("");

    const limHtml = (ei.limitations || [])
      .map(function (l) {
        return "<li>" + esc(l) + "</li>";
      })
      .join("");

    const needHtml = (ei.still_need || [])
      .map(function (n) {
        return "<li>" + esc(n) + "</li>";
      })
      .join("");

    const conclHtml = (ei.conclusion || [])
      .slice(0, 3)
      .map(function (c) {
        return "<p>" + esc(c) + "</p>";
      })
      .join("");

    root.innerHTML =
      '<div class="bm-ei">' +
      '<header class="bm-dx-top">' +
      '<button type="button" class="bm-btn bm-btn-ghost" id="bm-ei-back">' +
      esc(ei.cta_back || "Voltar à decisão") +
      "</button>" +
      '<p class="bm-dx-kicker">' +
      esc(h.kicker || "BioMed · Evidências") +
      "</p></header>" +
      '<section class="bm-dx-block bm-ei-hero">' +
      "<h1>" +
      esc(h.title || "Como sabemos disso?") +
      "</h1>" +
      '<p class="bm-ei-sub">' +
      esc(h.subtitle || "") +
      "</p>" +
      '<p class="bm-dx-six"><strong>Decisão:</strong> ' +
      esc(h.decision_title || "") +
      "</p></section>" +
      // 1
      '<section class="bm-dx-block">' +
      '<h2 class="bm-fx-section-title">Síntese da evidência</h2>' +
      '<div class="bm-fx-summary__body bm-dx-why">' +
      summaryHtml +
      "</div></section>" +
      // 2
      '<section class="bm-dx-block">' +
      '<h2 class="bm-fx-section-title">Fontes da evidência</h2>' +
      '<p class="bm-dx-sub">Dados que já sustentam a decisão — sem nova análise.</p>' +
      '<div class="bm-ei-sources">' +
      sourcesHtml +
      "</div>" +
      (chartSrcHtml
        ? '<ul class="bm-ei-list bm-ei-list--charts">' + chartSrcHtml + "</ul>"
        : "") +
      "</section>" +
      // 3
      '<section class="bm-dx-block">' +
      '<h2 class="bm-fx-section-title">Evolução no período</h2>' +
      '<p class="bm-dx-sub">' +
      esc(ei.timeline_note || "") +
      "</p>" +
      '<div class="bm-dx-evidence-card"><div class="bm-dx-bars">' +
      miniBars(tv.categories, tv.values) +
      "</div></div></section>" +
      // 4
      '<section class="bm-dx-block">' +
      '<h2 class="bm-fx-section-title">Qualidade da evidência</h2>' +
      '<div class="bm-ei-quality">' +
      '<div class="bm-ei-quality__score">' +
      '<div class="bm-ei-quality__label">IQB</div>' +
      '<div class="bm-ei-quality__value">' +
      esc(q.iqb != null ? fmtNum(q.iqb) : "—") +
      "</div>" +
      '<div class="bm-dx-state">' +
      esc(q.label || "Não informado") +
      "</div></div>" +
      '<div class="bm-ei-quality__meta">' +
      "<div><span>Comparabilidade</span><strong>" +
      esc(q.comparability || "—") +
      "</strong></div>" +
      "<div><span>Cobertura de horas</span><strong>" +
      esc(q.hours_coverage || "—") +
      "</strong></div>" +
      '<p class="bm-ei-note">' +
      esc(q.note || "") +
      "</p></div></div>" +
      (dimsHtml ? '<div class="bm-dx-chips">' + dimsHtml + "</div>" : "") +
      "</section>" +
      // 5
      '<section class="bm-dx-block">' +
      '<h2 class="bm-fx-section-title">Confiança da evidência</h2>' +
      '<div class="bm-dx-conf">' +
      '<div class="bm-dx-conf__level">' +
      esc(conf.level || "Baixa") +
      "</div><p>" +
      esc(conf.reason || "") +
      "</p></div></section>" +
      // 6
      '<section class="bm-dx-block">' +
      '<h2 class="bm-fx-section-title">Limitações</h2>' +
      '<ul class="bm-ei-list">' +
      limHtml +
      "</ul></section>" +
      // 7
      '<section class="bm-dx-block">' +
      '<h2 class="bm-fx-section-title">O que ainda falta</h2>' +
      '<ul class="bm-ei-list">' +
      needHtml +
      "</ul></section>" +
      // 8
      '<section class="bm-dx-block">' +
      '<h2 class="bm-fx-section-title">Conclusão executiva</h2>' +
      '<div class="bm-fx-summary__body bm-dx-why bm-ei-conclusion">' +
      conclHtml +
      "</div></section>" +
      "</div>";

    const back = root.querySelector("#bm-ei-back");
    if (back && handlers.onBack) back.addEventListener("click", handlers.onBack);
  }

  global.BioMedEvidenceIntelligence = { render: render };
})(window);
