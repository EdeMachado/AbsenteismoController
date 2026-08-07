/**
 * EXEC-09 — BioMed Executive Decision Experience™ renderer.
 * Full-view visual conversation (not a modal). Answers six questions only.
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

  function fmtMoney(n) {
    if (n == null || isNaN(Number(n))) return null;
    return (
      "R$ " +
      Number(n).toLocaleString("pt-BR", {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      })
    );
  }

  function fmtNum(n) {
    if (n == null || isNaN(Number(n))) return "—";
    return Number(n).toLocaleString("pt-BR", { maximumFractionDigits: 1 });
  }

  function miniBars(categories, values) {
    const cats = categories || [];
    const vals = values || [];
    const max = Math.max.apply(null, vals.map(Number).concat([1]));
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

  function impactCard(block) {
    const money = fmtMoney(block.value);
    const available = block.available && money;
    return (
      '<article class="bm-dx-impact">' +
      '<div class="bm-dx-impact__label">' +
      esc(block.label) +
      "</div>" +
      '<div class="bm-dx-impact__value' +
      (available ? "" : " is-na") +
      '">' +
      esc(available ? money : "Não calculável") +
      "</div>" +
      '<div class="bm-dx-state">Premissa · ' +
      esc(block.assumption_state || "NÃO INFORMADO") +
      "</div>" +
      '<p class="bm-dx-impact__note">' +
      esc(block.note || "") +
      "</p>" +
      (block.caveat ? '<p class="bm-dx-caveat">' + esc(block.caveat) + "</p>" : "") +
      "</article>"
    );
  }

  function render(root, dx, onBack, onEvidence) {
    if (!root || !dx) return;
    const h = dx.header || {};
    const bi = dx.business_impact || {};
    const evidence = dx.evidence || {};
    const charts = evidence.charts || [];
    const indicators = evidence.indicators || [];
    const why = dx.why || [];
    const recs = dx.recommendations || [];
    const roadmap = dx.roadmap || [];
    const er = dx.expected_results || {};
    const conf = dx.confidence || {};
    const six = dx.six_answers || {};

    const indHtml = indicators
      .map(function (k) {
        return (
          '<div class="bm-dx-chip' +
          (k.available ? "" : " is-na") +
          '"><span>' +
          esc(k.label) +
          "</span><strong>" +
          esc(k.available ? fmtNum(k.value) : "—") +
          (k.available && k.unit ? " " + esc(k.unit) : "") +
          "</strong></div>"
        );
      })
      .join("");

    const chartsHtml = charts
      .map(function (c) {
        return (
          '<article class="bm-dx-evidence-card">' +
          "<h3>" +
          esc(c.label) +
          "</h3>" +
          '<div class="bm-dx-bars">' +
          miniBars(c.categories, c.values) +
          "</div></article>"
        );
      })
      .join("");

    const whyHtml = why
      .slice(0, 3)
      .map(function (w) {
        return "<p>" + esc(w) + "</p>";
      })
      .join("");

    const recHtml = recs
      .slice(0, 3)
      .map(function (r, i) {
        return (
          '<article class="bm-dx-rec">' +
          '<div class="bm-dx-rec__n">' +
          (i + 1) +
          "</div>" +
          "<div><h3>" +
          esc(r.title) +
          "</h3>" +
          '<dl class="bm-dx-rec__meta">' +
          "<div><dt>Impacto</dt><dd>" +
          esc(r.impact) +
          "</dd></div>" +
          "<div><dt>Prazo</dt><dd>" +
          esc(r.deadline) +
          "</dd></div>" +
          "<div><dt>Complexidade</dt><dd>" +
          esc(r.complexity) +
          "</dd></div>" +
          "<div><dt>Área</dt><dd>" +
          esc(r.owner) +
          "</dd></div></dl></div></article>"
        );
      })
      .join("");

    const roadHtml = roadmap
      .map(function (r) {
        return (
          '<div class="bm-dx-road__step"><div class="bm-dx-road__h">' +
          esc(r.horizon) +
          '</div><div class="bm-dx-road__f">' +
          esc(r.focus) +
          "</div></div>"
        );
      })
      .join("");

    root.innerHTML =
      '<div class="bm-dx">' +
      '<header class="bm-dx-top">' +
      '<button type="button" class="bm-btn bm-btn-ghost" id="bm-dx-back">' +
      esc(dx.cta_back || "Voltar à abertura") +
      "</button>" +
      '<p class="bm-dx-kicker">BioMed · Decisão</p>' +
      "</header>" +
      // 1 header
      '<section class="bm-dx-block bm-dx-hero-dec">' +
      '<div class="bm-dx-pri">' +
      esc(h.priority_label || "") +
      "</div>" +
      "<h1>" +
      esc(h.title || "") +
      "</h1>" +
      '<div class="bm-dx-hero-dec__facts">' +
      "<div><span>Impacto</span><strong>" +
      esc(h.impact || "—") +
      "</strong></div>" +
      "<div><span>Tempo estimado</span><strong>" +
      esc(h.estimated_time || "—") +
      "</strong></div></div>" +
      '<p class="bm-dx-six"><strong>Problema:</strong> ' +
      esc(six.problem || "") +
      "</p>" +
      '<div class="bm-dx-cta-row">' +
      '<button type="button" class="bm-btn bm-btn-ghost" id="bm-dx-evidence">' +
      "Como sabemos disso?" +
      "</button></div>" +
      "</section>" +
      // 2 evidence
      '<section class="bm-dx-block">' +
      '<h2 class="bm-fx-section-title">Evidências</h2>' +
      '<p class="bm-dx-sub">Como sabemos disso — apenas evidência visual.</p>' +
      '<div class="bm-dx-chips">' +
      indHtml +
      "</div>" +
      '<div class="bm-dx-evidence-grid">' +
      chartsHtml +
      "</div></section>" +
      // 3 business impact
      '<section class="bm-dx-block">' +
      '<h2 class="bm-fx-section-title">Impacto para o negócio</h2>' +
      '<div class="bm-dx-impact-grid">' +
      impactCard(bi.cost_today || {}) +
      impactCard(bi.cost_if_nothing || {}) +
      impactCard(bi.savings_potential || {}) +
      "</div></section>" +
      // 4 why
      '<section class="bm-dx-block">' +
      '<h2 class="bm-fx-section-title">Por quê</h2>' +
      '<div class="bm-fx-summary__body bm-dx-why">' +
      whyHtml +
      "</div></section>" +
      // 5 recommendations
      '<section class="bm-dx-block">' +
      '<h2 class="bm-fx-section-title">Recomendação BioMed</h2>' +
      '<p class="bm-dx-sub">No máximo três. Necessária validação humana.</p>' +
      '<div class="bm-dx-recs">' +
      recHtml +
      "</div>" +
      '<p class="bm-dx-six"><strong>Próximo passo:</strong> ' +
      esc(six.first_step || "") +
      "</p></section>" +
      // 6 roadmap
      '<section class="bm-dx-block">' +
      '<h2 class="bm-fx-section-title">Roteiro de implementação</h2>' +
      '<div class="bm-dx-road">' +
      roadHtml +
      "</div></section>" +
      // 7 expected results
      '<section class="bm-dx-block">' +
      '<h2 class="bm-fx-section-title">Resultados esperados</h2>' +
      '<div class="bm-dx-results">' +
      "<div><h3>Financeiro</h3><p>" +
      esc(er.financial || "") +
      "</p></div>" +
      "<div><h3>Operacional</h3><p>" +
      esc(er.operational || "") +
      "</p></div>" +
      "<div><h3>Saúde</h3><p>" +
      esc(er.health || "") +
      "</p></div>" +
      "<div><h3>Governança</h3><p>" +
      esc(er.governance || "") +
      "</p></div></div></section>" +
      // 8 confidence
      '<section class="bm-dx-block">' +
      '<h2 class="bm-fx-section-title">Confiança da evidência</h2>' +
      '<div class="bm-dx-conf">' +
      '<div class="bm-dx-conf__level">' +
      esc(conf.level || "Baixa") +
      "</div>" +
      "<p>" +
      esc(conf.reason || "") +
      "</p></div></section>" +
      // footer ORBIT note — discreet, no CTA
      '<footer class="bm-dx-foot">' +
      esc(dx.footer_note || "") +
      "</footer></div>";

    const back = root.querySelector("#bm-dx-back");
    if (back && onBack) back.addEventListener("click", onBack);
    const ev = root.querySelector("#bm-dx-evidence");
    if (ev && onEvidence) ev.addEventListener("click", onEvidence);
  }

  global.BioMedDecisionExperience = { render: render };
})(window);
