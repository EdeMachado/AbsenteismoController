/**
 * RC-1.2A — Ficha Digital preview client (staff + employee views).
 */
(function () {
  "use strict";

  const state = {
    templates: [],
    collaborators: [],
    currentToken: null,
    employeeToken: null,
  };

  function $(id) { return document.getElementById(id); }

  function showPanel(id) {
    document.querySelectorAll(".bm-fd-panel").forEach(function (p) {
      p.classList.toggle("is-on", p.id === id);
    });
    document.querySelectorAll(".bm-fd-tab").forEach(function (t) {
      t.classList.toggle("is-on", t.dataset.panel === id);
    });
  }

  function api(path, opts) {
    opts = opts || {};
    return fetch(path, {
      method: opts.method || "GET",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      body: opts.body ? JSON.stringify(opts.body) : undefined,
    }).then(function (r) {
      return r.json().then(function (j) {
        if (!r.ok) throw new Error(j.detail || "Falha na operação");
        return j;
      });
    });
  }

  function renderMetrics(m) {
    $("fd-metrics").innerHTML =
      metric("Fichas enviadas", m.fichas_enviadas) +
      metric("Respondidas", m.fichas_respondidas) +
      metric("Tempo médio", m.tempo_medio_resposta) +
      metric("Pendentes", m.pendentes) +
      metric("Validação pendente", m.validacao_pendente);
  }
  function metric(label, value) {
    return '<div class="bm-fd-metric"><span>' + label + "</span><strong>" + value + "</strong></div>";
  }

  function refreshLists() {
    return Promise.all([
      api("/api/preview/ficha/invites"),
      api("/api/preview/ficha/metrics"),
      api("/api/preview/ficha/alerts"),
    ]).then(function (res) {
      const invites = res[0].items || [];
      renderMetrics(res[1]);
      renderTracking(invites);
      renderAlerts(res[2].items || []);
      if (state.currentToken) {
        return api("/api/preview/ficha/invites/" + state.currentToken).then(renderStaffDetail);
      }
    });
  }

  function renderTracking(invites) {
    const el = $("fd-tracking");
    if (!invites.length) {
      el.innerHTML = '<p class="bm-fd-muted">Nenhuma ficha ainda. Envie a primeira.</p>';
      return;
    }
    el.innerHTML = invites
      .map(function (i) {
        return (
          '<button type="button" class="bm-fd-card" data-token="' +
          i.token +
          '" style="width:100%;text-align:left;cursor:pointer">' +
          "<h3>" +
          esc(i.template_title) +
          "</h3>" +
          '<p class="bm-fd-muted">' +
          esc(i.collaborator_label) +
          " · " +
          esc(i.channel) +
          " · <strong>" +
          esc(i.status) +
          "</strong></p></button>"
        );
      })
      .join("");
    el.querySelectorAll("[data-token]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        state.currentToken = btn.getAttribute("data-token");
        api("/api/preview/ficha/invites/" + state.currentToken).then(function (d) {
          renderStaffDetail(d);
          showPanel("panel-timeline");
        });
      });
    });
  }

  function renderAlerts(items) {
    const el = $("fd-alerts");
    if (!items.length) {
      el.innerHTML = '<p class="bm-fd-muted">Nenhum alerta de ficha.</p>';
      return;
    }
    el.innerHTML = items
      .map(function (a) {
        return (
          '<div class="bm-fd-alert"><strong>' +
          esc(a.title) +
          "</strong><p>" +
          esc(a.message) +
          "</p><p class="bm-fd-note">" +
          esc(a.timestamp) +
          " · sem conteúdo clínico</p></div>"
        );
      })
      .join("");
    // Integrate with existing bell data shape (non-clinical)
    window.alertasData = (window.alertasData || []).filter(function (x) {
      return x.tipo !== "ficha_digital";
    }).concat(
      items.map(function (a) {
        return {
          tipo: "ficha_digital",
          severidade: a.severidade === "alta" ? "alta" : a.severidade === "media" ? "media" : "baixa",
          titulo: a.title,
          mensagem: a.message,
          dados: {},
        };
      })
    );
    const badge = document.getElementById("alertasBadge");
    const count = document.getElementById("alertasCount");
    if (count) count.textContent = String((window.alertasData || []).length);
    if (badge) {
      badge.style.display = (window.alertasData || []).length ? "flex" : "none";
      badge.textContent = String((window.alertasData || []).length);
    }
  }

  function renderStaffDetail(d) {
    $("fd-analysis").innerHTML = d.analysis
      ? "<h3>Análise sugerida</h3>" +
        "<p class=\"bm-fd-muted\">" +
        esc(d.analysis.disclaimer) +
        "</p>" +
        "<p><strong>Prioridade:</strong> " +
        esc(d.analysis.prioridade) +
        "</p>" +
        "<p><strong>Temas:</strong> " +
        esc((d.analysis.temas_predominantes || []).join("; ")) +
        "</p>" +
        "<p><strong>Campos críticos:</strong> " +
        esc((d.analysis.campos_criticos || []).join("; ")) +
        "</p>" +
        "<ul>" +
        (d.analysis.sugestoes || [])
          .map(function (s) {
            return "<li>" + esc(s) + "</li>";
          })
          .join("") +
        "</ul>" +
        '<div class="bm-fd-row"><button type="button" class="bm-fd-btn bm-fd-btn-primary" id="fd-validate">Validar</button></div>'
      : '<p class="bm-fd-muted">Sem análise ainda.</p>';

    const tl = $("fd-timeline");
    tl.innerHTML = (d.timeline || [])
      .map(function (t) {
        return (
          "<li><strong>" +
          esc(t.event) +
          "</strong><span>" +
          esc(t.at) +
          "</span></li>"
        );
      })
      .join("");

    const v = $("fd-validate");
    if (v) {
      v.addEventListener("click", function () {
        api("/api/preview/ficha/invites/" + state.currentToken + "/validate", {
          method: "POST",
          body: { note: "Validação humana (demo)" },
        }).then(function () {
          return refreshLists();
        });
      });
    }
  }

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function bootSendForm() {
    Promise.all([
      api("/api/preview/ficha/templates"),
      api("/api/preview/ficha/collaborators"),
    ]).then(function (res) {
      state.templates = res[0].items || [];
      state.collaborators = res[1].items || [];
      const c = $("fd-collab");
      const t = $("fd-template");
      c.innerHTML = state.collaborators
        .map(function (x) {
          return '<option value="' + esc(x.id) + '">' + esc(x.label) + "</option>";
        })
        .join("");
      t.innerHTML = state.templates
        .map(function (x) {
          return '<option value="' + esc(x.id) + '">' + esc(x.title) + "</option>";
        })
        .join("");
    });
  }

  function createAndSend() {
    const body = {
      collaborator_id: $("fd-collab").value,
      template_id: $("fd-template").value,
      channel: document.querySelector('input[name="fd-channel"]:checked').value,
    };
    api("/api/preview/ficha/invites", { method: "POST", body: body })
      .then(function (inv) {
        state.currentToken = inv.token;
        return api("/api/preview/ficha/invites/" + inv.token + "/send", { method: "POST" });
      })
      .then(function () {
        return api("/api/preview/ficha/invites/" + state.currentToken + "/channel");
      })
      .then(function (ch) {
        $("fd-channel-out").innerHTML =
          "<h3>Link seguro gerado</h3>" +
          '<p class="bm-fd-muted">Token opaco · sem CPF · sem matrícula · sem CID na URL</p>' +
          '<div class="bm-fd-code">' +
          esc(ch.link) +
          "</div>" +
          (ch.whatsapp_url
            ? '<div class="bm-fd-row" style="margin-top:0.75rem"><a class="bm-fd-btn bm-fd-btn-primary" target="_blank" rel="noopener" href="' +
              esc(ch.whatsapp_url) +
              '">Abrir WhatsApp</a></div><div class="bm-fd-code" style="margin-top:0.75rem">' +
              esc(ch.whatsapp_message) +
              "</div>"
            : "") +
          (ch.email
            ? "<h3 style=\"margin-top:1rem\">E-mail</h3><p><strong>Assunto:</strong> " +
              esc(ch.email.subject) +
              '</p><div class="bm-fd-code">' +
              esc(ch.email.body) +
              "</div>"
            : "") +
          '<div class="bm-fd-row" style="margin-top:0.75rem"><button type="button" class="bm-fd-btn bm-fd-btn-ghost" id="fd-open-employee">Simular colaborador</button></div>';
        const btn = $("fd-open-employee");
        if (btn) {
          btn.addEventListener("click", function () {
            state.employeeToken = state.currentToken;
            openEmployee();
            showPanel("panel-employee");
          });
        }
        return refreshLists();
      })
      .catch(function (e) {
        alert(e.message || "Erro");
      });
  }

  function openEmployee() {
    const token = state.employeeToken || state.currentToken;
    if (!token) return;
    api("/api/preview/ficha/f/" + token)
      .then(function (v) {
        const root = $("fd-employee");
        if (v.status === "Expirada" || v.status === "Cancelada") {
          root.innerHTML = "<div class=\"bm-fd-phone\"><h2>" + esc(v.status) + "</h2><p>Este acesso não está mais disponível.</p></div>";
          return;
        }
        if (v.status === "Validada" || v.status === "Aguardando validação" || v.status === "Analisada" || v.status === "Respondida") {
          // after submit we show success separately
        }
        root.innerHTML =
          '<div class="bm-fd-phone" id="fd-emp-frame">' +
          '<div class="logo">BioMed</div>' +
          '<p class="bm-fd-muted">' +
          esc(v.company_label) +
          "</p>" +
          "<h2>" +
          esc(v.title) +
          "</h2>" +
          "<p>" +
          esc(v.orientation) +
          "</p>" +
          '<p class="bm-fd-muted">' +
          esc(v.privacy) +
          "</p>" +
          '<label class="bm-fd-check"><input type="checkbox" id="fd-consent" /> <span>Li e compreendi as informações.</span></label>' +
          '<button type="button" class="bm-fd-btn bm-fd-btn-primary" id="fd-start" style="width:100%">Iniciar</button>' +
          "</div>";

        $("fd-start").addEventListener("click", function () {
          if (!$("fd-consent").checked) {
            alert("Marque a ciência para continuar.");
            return;
          }
          api("/api/preview/ficha/f/" + token + "/start", { method: "POST" }).then(function () {
            renderEmployeeForm(v, token);
          });
        });
      })
      .catch(function () {
        $("fd-employee").innerHTML = '<div class="bm-fd-phone"><p>Não foi possível abrir a ficha.</p></div>';
      });
  }

  function renderEmployeeForm(v, token) {
    const fields = (v.fields || [])
      .map(function (f) {
        if (f.type === "choice") {
          return (
            '<div class="bm-fd-field"><label>' +
            esc(f.label) +
            '</label><select data-fid="' +
            esc(f.id) +
            '"><option value="">Selecione</option>' +
            (f.options || [])
              .map(function (o) {
                return "<option>" + esc(o) + "</option>";
              })
              .join("") +
            "</select></div>"
          );
        }
        return (
          '<div class="bm-fd-field"><label>' +
          esc(f.label) +
          '</label><textarea data-fid="' +
          esc(f.id) +
          '" rows="3"></textarea></div>'
        );
      })
      .join("");
    $("fd-emp-frame").innerHTML =
      '<div class="logo">BioMed</div><h2>' +
      esc(v.title) +
      "</h2>" +
      fields +
      '<button type="button" class="bm-fd-btn bm-fd-btn-primary" id="fd-submit" style="width:100%">Enviar</button>';
    $("fd-submit").addEventListener("click", function () {
      const answers = {};
      $("fd-emp-frame").querySelectorAll("[data-fid]").forEach(function (el) {
        answers[el.getAttribute("data-fid")] = el.value;
      });
      api("/api/preview/ficha/f/" + token + "/submit", {
        method: "POST",
        body: { consent: true, answers: answers },
      }).then(function () {
        $("fd-employee").innerHTML =
          '<div class="bm-fd-phone bm-fd-success" id="fd-emp-success">' +
          "<h2>Enviado</h2>" +
          "<p>Obrigado. Sua resposta foi registrada.</p>" +
          '<p class="bm-fd-muted">O responsável dará continuidade com validação humana.</p></div>';
        return refreshLists();
      });
    });
  }

  document.querySelectorAll(".bm-fd-tab").forEach(function (tab) {
    tab.addEventListener("click", function () {
      showPanel(tab.dataset.panel);
      if (tab.dataset.panel === "panel-employee") openEmployee();
    });
  });

  $("fd-send").addEventListener("click", createAndSend);
  $("fd-reset").addEventListener("click", function () {
    api("/api/preview/ficha/reset", { method: "POST" }).then(function () {
      state.currentToken = null;
      $("fd-channel-out").innerHTML = "";
      refreshLists();
    });
  });

  bootSendForm();
  refreshLists();
  showPanel("panel-send");
})();
