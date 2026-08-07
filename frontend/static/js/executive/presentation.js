/**
 * EXEC-03 / RC-1.4 — Executive Presentation (authenticated screen mode).
 * Uses premium renderer when available; same /api/executive/presentation contract.
 */
(function () {
  "use strict";

  let ctrl = null;

  function tokenHeaders() {
    const token = localStorage.getItem("access_token");
    const h = { Accept: "application/json" };
    if (token) h.Authorization = "Bearer " + token;
    return h;
  }

  async function load() {
    if (!localStorage.getItem("access_token")) {
      window.location.href = "/login";
      return;
    }
    const status = document.getElementById("bm-pres-status");
    try {
      const clientId = Number(localStorage.getItem("cliente_selecionado")) || "";
      const qs = new URLSearchParams({
        periodo_inicio: "2026-01",
        periodo_fim: "2026-03",
      });
      if (clientId) qs.set("client_id", String(clientId));
      const res = await fetch("/api/executive/presentation?" + qs.toString(), {
        credentials: "same-origin",
        headers: tokenHeaders(),
      });
      if (res.status === 401) {
        window.location.href = "/login";
        return;
      }
      if (!res.ok) throw new Error("http");
      const data = await res.json();
      status.style.display = "none";

      const shell = document.querySelector(".bm-pres-shell") || document.body;
      // Prefer premium mount into dedicated stage if present
      let root = document.getElementById("bm-rc14-root");
      if (!root && window.BioMedPresentationPremium) {
        root = document.createElement("div");
        root.id = "bm-rc14-root";
        root.className = "bm-rc14-shell";
        root.innerHTML =
          '<div class="bm-rc14-progress"><i data-rc14-progress></i></div>' +
          '<main class="bm-rc14-stage" data-rc14-stage></main>' +
          '<div class="bm-rc14-actions" style="justify-content:center;padding:0.75rem">' +
          '<span class="bm-rc14-muted" style="color:#5a6b7a" data-rc14-counter>—</span></div>';
        const stage = document.getElementById("bm-pres-stage");
        if (stage) {
          stage.replaceWith(root);
        } else {
          shell.appendChild(root);
        }
        document.body.classList.add("bm-rc14-body");
        // load premium CSS if missing
        if (!document.querySelector('link[href*="biomed-presentation-premium"]')) {
          const link = document.createElement("link");
          link.rel = "stylesheet";
          link.href = "/static/css/biomed-presentation-premium.css";
          document.head.appendChild(link);
        }
      }
      if (window.BioMedPresentationPremium && root) {
        ctrl = window.BioMedPresentationPremium.mount(root, data);
      } else {
        status.className = "bm-error";
        status.textContent = "Não foi possível montar a apresentação.";
        status.style.display = "block";
      }
    } catch (e) {
      status.className = "bm-error";
      status.style.display = "block";
      status.textContent =
        "Não foi possível concluir esta ação. Tente novamente. Se o problema persistir, entre em contato com o administrador.";
    }
  }

  const prev = document.getElementById("bm-pres-prev");
  const next = document.getElementById("bm-pres-next");
  if (prev) prev.addEventListener("click", function () { if (ctrl) ctrl.prev(); });
  if (next) next.addEventListener("click", function () { if (ctrl) ctrl.next(); });
  document.addEventListener("keydown", function (e) {
    if (!ctrl) return;
    if (e.key === "ArrowRight" || e.key === "PageDown") ctrl.next();
    if (e.key === "ArrowLeft" || e.key === "PageUp") ctrl.prev();
  });

  load();
})();
