/**
 * RC-1.2A — employee mobile form (standalone /f/{token}).
 */
(function () {
  "use strict";
  const token = window.__FICHA_TOKEN__;
  if (!token || token === "__TOKEN__") {
    document.getElementById("fd-employee").innerHTML =
      '<div class="bm-fd-phone"><p>Link inválido.</p></div>';
    return;
  }

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function api(path, opts) {
    opts = opts || {};
    return fetch(path, {
      method: opts.method || "GET",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      body: opts.body ? JSON.stringify(opts.body) : undefined,
    }).then(function (r) {
      return r.json().then(function (j) {
        if (!r.ok) throw new Error(j.detail || "Falha");
        return j;
      });
    });
  }

  const root = document.getElementById("fd-employee");

  api("/api/preview/ficha/f/" + encodeURIComponent(token))
    .then(function (v) {
      if (v.status === "Expirada" || v.status === "Cancelada") {
        root.innerHTML =
          '<div class="bm-fd-phone"><h2>' +
          esc(v.status) +
          "</h2><p>Este acesso não está mais disponível.</p></div>";
        return;
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
        '<button type="button" class="bm-fd-btn bm-fd-btn-primary" id="fd-start" style="width:100%;margin-top:1rem">Iniciar</button>' +
        "</div>";

      document.getElementById("fd-start").addEventListener("click", function () {
        if (!document.getElementById("fd-consent").checked) {
          alert("Marque a ciência para continuar.");
          return;
        }
        api("/api/preview/ficha/f/" + encodeURIComponent(token) + "/start", {
          method: "POST",
        }).then(function () {
          renderForm(v);
        });
      });
    })
    .catch(function () {
      root.innerHTML =
        '<div class="bm-fd-phone"><p>Não foi possível abrir a ficha.</p></div>';
    });

  function renderForm(v) {
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
    document.getElementById("fd-emp-frame").innerHTML =
      '<div class="logo">BioMed</div><h2>' +
      esc(v.title) +
      "</h2>" +
      fields +
      '<button type="button" class="bm-fd-btn bm-fd-btn-primary" id="fd-submit" style="width:100%">Enviar</button>';
    document.getElementById("fd-submit").addEventListener("click", function () {
      const answers = {};
      document.querySelectorAll("[data-fid]").forEach(function (el) {
        answers[el.getAttribute("data-fid")] = el.value;
      });
      api("/api/preview/ficha/f/" + encodeURIComponent(token) + "/submit", {
        method: "POST",
        body: { consent: true, answers: answers },
      }).then(function () {
        root.innerHTML =
          '<div class="bm-fd-phone bm-fd-success">' +
          "<h2>Enviado</h2>" +
          "<p>Obrigado. Sua resposta foi registrada.</p>" +
          '<p class="bm-fd-muted">O responsável dará continuidade com validação humana.</p></div>';
      });
    });
  }
})();
