/**
 * EXEC-08 — bootstrap for first CEO experience only.
 */
(function () {
  "use strict";

  const FX = window.BioMedFirstExperience;

  function tokenHeaders() {
    const token = localStorage.getItem("access_token");
    const h = { Accept: "application/json" };
    if (token) h.Authorization = "Bearer " + token;
    return h;
  }

  function filterOpts() {
    const clientId = Number(localStorage.getItem("cliente_selecionado")) || undefined;
    return {
      client_id: clientId,
      periodo_inicio: document.getElementById("periodo_inicio").value || undefined,
      periodo_fim: document.getElementById("periodo_fim").value || undefined,
    };
  }

  function fetchJson(path, opts) {
    const params = new URLSearchParams();
    Object.keys(opts || {}).forEach(function (k) {
      if (opts[k] != null && opts[k] !== "") params.set(k, opts[k]);
    });
    const url = path + (params.toString() ? "?" + params.toString() : "");
    return fetch(url, { credentials: "same-origin", headers: tokenHeaders() }).then(function (res) {
      if (res.status === 401) {
        window.location.href = "/login";
        throw new Error("Não autenticado");
      }
      if (!res.ok) throw new Error("HTTP " + res.status);
      return res.json();
    });
  }

  function setStatus(msg, isError) {
    const el = document.getElementById("bm-status");
    if (!el) return;
    if (!msg) {
      el.style.display = "none";
      el.textContent = "";
      return;
    }
    el.style.display = "block";
    el.className = isError ? "bm-error" : "bm-loading";
    el.textContent = msg;
  }

  function openDecision(decision) {
    const modal = document.getElementById("bm-decision-modal");
    const body = document.getElementById("bm-decision-body");
    if (!modal || !body) return;
    body.innerHTML =
      "<p><strong>" +
      (decision.title || "") +
      "</strong></p>" +
      "<p>" +
      (decision.description || "") +
      "</p>" +
      "<p><em>Impacto esperado:</em> " +
      (decision.expected_impact || "—") +
      "</p>" +
      "<p><em>Prazo:</em> " +
      (decision.deadline || "—") +
      "</p>" +
      "<p class='bm-muted' style='margin-top:1rem'>Validação humana obrigatória. Sem autoexecução.</p>";
    modal.classList.add("is-open");
  }

  function renderAll(payload) {
    const fx = payload.first_experience;
    if (!fx || !FX) {
      setStatus("Primeira experiência indisponível neste payload.", true);
      return;
    }
    FX.render(document.getElementById("bm-first-experience"), fx, openDecision);
  }

  async function load() {
    if (!localStorage.getItem("access_token")) {
      window.location.href = "/login";
      return;
    }
    setStatus("Preparando leitura executiva…");
    try {
      const payload = await fetchJson("/api/executive/command-center", filterOpts());
      renderAll(payload);
      setStatus("");
    } catch (err) {
      setStatus(
        "Não foi possível carregar a abertura executiva. Verifique autenticação e ENABLE_EXECUTIVE_UI.",
        true
      );
    }
  }

  document.getElementById("bm-filters").addEventListener("submit", function (e) {
    e.preventDefault();
    load();
  });

  document.getElementById("bm-nav-toggle").addEventListener("click", function () {
    const nav = document.getElementById("bm-nav");
    const open = nav.classList.toggle("is-open");
    this.setAttribute("aria-expanded", open ? "true" : "false");
  });

  document.getElementById("bm-decision-close").addEventListener("click", function () {
    document.getElementById("bm-decision-modal").classList.remove("is-open");
  });
  document.getElementById("bm-decision-modal").addEventListener("click", function (e) {
    if (e.target === this) this.classList.remove("is-open");
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      document.getElementById("bm-decision-modal").classList.remove("is-open");
    }
  });

  (function initDates() {
    document.getElementById("periodo_inicio").value = "2026-01";
    document.getElementById("periodo_fim").value = "2026-03";
  })();

  load();
})();
