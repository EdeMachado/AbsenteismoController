/**
 * EXEC-08 — First CEO experience renderer.
 * Hero · Summary · 4 KPIs · One Decision. No charts. No modules beyond opening.
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

  function fmtNum(n, digits) {
    if (n == null || Number.isNaN(Number(n))) return "—";
    return Number(n).toLocaleString("pt-BR", {
      maximumFractionDigits: digits == null ? 1 : digits,
      minimumFractionDigits: 0,
    });
  }

  function fmtMoney(n) {
    if (n == null || Number.isNaN(Number(n))) return "—";
    return (
      "R$ " +
      Number(n).toLocaleString("pt-BR", {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      })
    );
  }

  function trendLabel(t) {
    if (!t) return "n/d";
    return t;
  }

  function render(root, fx, onUnderstand) {
    if (!root || !fx) return;
    const hero = fx.hero || {};
    const score = hero.score || {};
    const kpis = fx.kpis || [];
    const decision = fx.decision || {};
    const summary = fx.summary || [];

    const scoreBlock = score.available
      ? '<div class="bm-fx-score__value">' +
        esc(fmtNum(score.value, 1)) +
        "</div>" +
        '<div class="bm-fx-score__label">' +
        esc(score.label || "Executive Score") +
        "</div>"
      : '<div class="bm-fx-score__value bm-fx-score__value--na">—</div>' +
        '<div class="bm-fx-score__label">Score não disponível</div>';

    const kpiHtml = kpis
      .map(function (k) {
        var val;
        if (!k.available) val = "Indisponível";
        else if (k.id === "custo") val = fmtMoney(k.value);
        else val = fmtNum(k.value, k.id === "score" ? 1 : 1);
        return (
          '<article class="bm-fx-kpi' +
          (k.available ? "" : " bm-fx-kpi--empty") +
          '" data-kpi="' +
          esc(k.id) +
          '">' +
          '<div class="bm-fx-kpi__label">' +
          esc(k.label) +
          "</div>" +
          '<div class="bm-fx-kpi__value">' +
          esc(val) +
          "</div>" +
          '<div class="bm-fx-kpi__meta">' +
          esc(
            k.available
              ? k.unit || ""
              : k.empty_label || "Não calculável"
          ) +
          "</div></article>"
        );
      })
      .join("");

    const summaryHtml = summary
      .slice(0, 3)
      .map(function (line) {
        return "<p>" + esc(line) + "</p>";
      })
      .join("");

    const pri = (decision.priority || "alta").toLowerCase();
    const priLabel =
      pri === "alta" ? "Prioridade Alta" : pri === "media" ? "Prioridade Média" : "Prioridade " + pri;

    root.innerHTML =
      '<section class="bm-fx-hero" aria-label="Hero executivo">' +
      '<div class="bm-fx-hero__veil"></div>' +
      '<div class="bm-fx-hero__inner">' +
      '<p class="bm-fx-brand">BioMed</p>' +
      '<h1 class="bm-fx-company">' +
      esc(hero.company || "—") +
      "</h1>" +
      '<p class="bm-fx-competencia">Competência · ' +
      esc(hero.competencia || "—") +
      "</p>" +
      '<div class="bm-fx-hero__grid">' +
      '<div class="bm-fx-score" aria-label="Executive Score">' +
      scoreBlock +
      "</div>" +
      '<ul class="bm-fx-meta">' +
      "<li><span>Tendência</span><strong>" +
      esc(trendLabel(hero.trend)) +
      "</strong></li>" +
      "<li><span>Confiança</span><strong>" +
      esc(hero.confidence || "—") +
      "</strong></li>" +
      "<li><span>Status</span><strong>" +
      esc(hero.operational_status || "—") +
      "</strong></li>" +
      "<li><span>Atualizado</span><strong>" +
      esc(hero.updated_at || "—") +
      "</strong></li>" +
      "</ul></div>" +
      '<p class="bm-fx-opening">' +
      esc(hero.opening_phrase || "") +
      "</p>" +
      "</div></section>" +
      '<section class="bm-fx-summary" aria-label="Executive Summary">' +
      '<h2 class="bm-fx-section-title">Executive Summary</h2>' +
      '<div class="bm-fx-summary__body">' +
      summaryHtml +
      "</div></section>" +
      '<section class="bm-fx-kpis" aria-label="Indicadores principais">' +
      '<h2 class="bm-fx-section-title">Indicadores</h2>' +
      '<div class="bm-fx-kpi-grid">' +
      kpiHtml +
      "</div></section>" +
      '<section class="bm-fx-decision" aria-label="Executive Decision">' +
      '<h2 class="bm-fx-section-title">Executive Decision</h2>' +
      '<article class="bm-fx-decision__card">' +
      '<div class="bm-fx-decision__pri">' +
      esc(priLabel) +
      "</div>" +
      "<h3>" +
      esc(decision.title || "") +
      "</h3>" +
      '<p class="bm-fx-decision__desc">' +
      esc(decision.description || "") +
      "</p>" +
      '<dl class="bm-fx-decision__facts">' +
      "<div><dt>Impacto esperado</dt><dd>" +
      esc(decision.expected_impact || "—") +
      "</dd></div>" +
      "<div><dt>Prazo</dt><dd>" +
      esc(decision.deadline || "—") +
      "</dd></div>" +
      "</dl>" +
      '<button type="button" class="bm-btn bm-fx-cta" id="bm-fx-understand">' +
      esc(decision.cta || "Entender esta decisão") +
      "</button>" +
      "</article></section>";

    const btn = root.querySelector("#bm-fx-understand");
    if (btn && onUnderstand) {
      btn.addEventListener("click", function () {
        onUnderstand(decision);
      });
    }
  }

  global.BioMedFirstExperience = { render: render };
})(window);
