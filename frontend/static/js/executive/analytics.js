/**
 * EXEC-03 — Analytics catalog, cost block, questions, analyze drawer.
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
    if (v == null || isNaN(v)) return "—";
    return "R$ " + Number(v).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function renderCatalog(el, catalog, onAnalyze) {
    if (!el) return;
    if (!catalog || !catalog.length) {
      el.innerHTML = "<p class='bm-muted'>Catálogo indisponível.</p>";
      return;
    }
    const groups = {};
    catalog.forEach(function (a) {
      const q = a.question || "OUTRO";
      (groups[q] = groups[q] || []).push(a);
    });
    el.innerHTML = Object.keys(groups)
      .map(function (q) {
        const cards = groups[q]
          .map(function (a) {
            const avail = a.available
              ? "<span class='bm-pill bm-pill-ok'>disponível</span>"
              : "<span class='bm-pill bm-pill-off'>indisponível</span>";
            const reason = a.available
              ? ""
              : "<p class='bm-muted' style='margin:0.35rem 0 0;font-size:0.78rem'>" +
                esc(a.unavailable_reason || "") +
                "</p>";
            const btn = a.available
              ? "<button type='button' class='bm-btn bm-btn-ghost bm-analyze-btn' data-analysis='" +
                esc(a.id) +
                "'>Analisar</button>"
              : "";
            return (
              "<article class='bm-analytics-card' data-id='" +
              esc(a.id) +
              "'>" +
              "<div class='bm-analytics-card__head'><strong>" +
              esc(a.title) +
              "</strong>" +
              avail +
              "</div>" +
              "<p class='bm-muted' style='margin:0.35rem 0'>" +
              esc(a.pergunta) +
              "</p>" +
              reason +
              "<div class='bm-analytics-card__foot'>" +
              btn +
              "</div></article>"
            );
          })
          .join("");
        return (
          "<div class='bm-analytics-group'><h3 class='bm-section-title'>" +
          esc(q) +
          "</h3><div class='bm-analytics-cards'>" +
          cards +
          "</div></div>"
        );
      })
      .join("");
    el.querySelectorAll(".bm-analyze-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        if (onAnalyze) onAnalyze(btn.getAttribute("data-analysis"));
      });
    });
  }

  function renderRecurrence(el, rec) {
    if (!el) return;
    if (!rec) {
      el.innerHTML =
        "<div class='bm-chart-empty'>Recorrência agregada indisponível. Sem ranking nominal na visão executiva.</div>";
      return;
    }
    el.innerHTML =
      "<div class='bm-kpi-secondary'>" +
      [
        ["2+ eventos", rec.n_2plus],
        ["3+ eventos", rec.n_3plus],
        ["5+ eventos", rec.n_5plus],
        ["Part. eventos (2+)", rec.share_eventos_2plus != null ? rec.share_eventos_2plus + "%" : "—"],
      ]
        .map(function (pair) {
          return (
            "<div class='bm-kpi bm-kpi--secondary'><div class='bm-kpi__label'>" +
            esc(pair[0]) +
            "</div><div class='bm-kpi__value'>" +
            esc(pair[1]) +
            "</div></div>"
          );
        })
        .join("") +
      "</div><p class='bm-muted' style='margin-top:0.75rem'>" +
      esc(rec.nota || "Agregado — sem PII.") +
      "</p>";
  }

  function renderCost(el, custo, condicionantesFin) {
    if (!el) return;
    if (!custo) {
      el.innerHTML = "<div class='bm-chart-empty'>Impacto financeiro indisponível com as premissas atuais.</div>";
      return;
    }
    const ass = custo.assumption || {};
    const hours = custo.hours || {};
    const estado = ass.estado || "NAO_INFORMADO";
    let html =
      "<div class='bm-cost-hero'>" +
      "<div class='bm-kpi bm-kpi--primary'><div class='bm-kpi__label'>Impacto laboral estimado</div>" +
      "<div class='bm-kpi__value'>" +
      (custo.calculavel ? money(custo.custo_estimado) : "Não calculável") +
      "</div></div>" +
      "<p class='bm-lede'>" +
      esc(custo.linguagem || "") +
      "</p>" +
      "<ul class='bm-list'>" +
      "<li>Base de horas: <strong>" +
      esc(hours.kind || "—") +
      "</strong> (" +
      esc(hours.horas != null ? hours.horas + " h" : "n/d") +
      ")</li>" +
      "<li>Premissa: <strong>" +
      esc(estado) +
      "</strong> — " +
      esc(ass.rotulo || "Custo médio da hora de trabalho") +
      (ass.valor != null ? " R$ " + Number(ass.valor).toFixed(2) + "/h" : "") +
      "</li>" +
      "<li>" +
      esc(ass.disclaimer || "") +
      "</li>" +
      "</ul>";
    if (estado === "ILUSTRATIVO") {
      html +=
        "<div class='bm-callout'>Premissa ilustrativa — substitua pelo custo hora real da empresa.</div>";
    }
    html +=
      "<p class='bm-muted' style='margin-top:0.75rem;font-size:0.85rem'>Este valor representa uma estimativa do impacto direto associado às horas de trabalho perdidas e não incorpora, nesta versão, custos indiretos como substituição, horas extras, perda de produtividade, turnover ou impacto operacional secundário.</p>";
    if (condicionantesFin) {
      html += "<div class='bm-callout' style='margin-top:0.75rem'>" + esc(condicionantesFin) + "</div>";
    }
    html += "</div>";
    el.innerHTML = html;
  }

  function renderQuestions(el, questions, onAsk) {
    if (!el) return;
    el.innerHTML = (questions || [])
      .map(function (q) {
        return (
          "<button type='button' class='bm-q-btn' data-qid='" +
          esc(q.id) +
          "'>" +
          esc(q.label) +
          "</button>"
        );
      })
      .join("");
    el.querySelectorAll(".bm-q-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        if (onAsk) onAsk(btn.getAttribute("data-qid"));
      });
    });
  }

  function renderAnalyze(el, data) {
    if (!el || !data) return;
    function block(title, body) {
      if (Array.isArray(body)) {
        body = "<ul class='bm-list'>" + body.map(function (x) {
          if (typeof x === "object") return "<li>" + esc(x.titulo || "Informação não disponível em texto.") + "</li>";
          return "<li>" + esc(x) + "</li>";
        }).join("") + "</ul>";
      } else {
        body = "<p>" + esc(body) + "</p>";
      }
      return "<div class='bm-analyze-block'><h3>" + esc(title) + "</h3>" + body + "</div>";
    }
    el.innerHTML =
      "<p class='bm-muted'>" +
      esc(data.pergunta || "") +
      "</p>" +
      block("Fato observado", data.fato_observado) +
      block("Interpretação", data.interpretacao) +
      block("Hipóteses", data.hipoteses) +
      block("Impacto", data.impacto) +
      block("Recomendação", data.recomendacao) +
      block("Plano sugerido", data.plano_sugerido) +
      block("Evidência", data.evidencia) +
      block("Limitações", data.limitacoes) +
      "<p class='bm-muted'>Confiança: <strong>" +
      esc(data.confianca) +
      "</strong>. Necessária validação humana.</p>";
  }

  global.BioMedExecutiveAnalytics = {
    renderCatalog: renderCatalog,
    renderRecurrence: renderRecurrence,
    renderCost: renderCost,
    renderQuestions: renderQuestions,
    renderAnalyze: renderAnalyze,
  };
})(window);
