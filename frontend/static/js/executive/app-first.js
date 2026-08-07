/**
 * EXEC-08/09 — bootstrap: first experience → Decision Experience (full view).
 */
(function () {
  "use strict";

  const FX = window.BioMedFirstExperience;
  const DX = window.BioMedDecisionExperience;
  let lastPayload = null;

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

  function showView(id) {
    document.querySelectorAll(".bm-module").forEach(function (el) {
      el.classList.toggle("is-visible", el.id === id || el.dataset.module === id);
    });
    document.querySelectorAll("#bm-nav-links a").forEach(function (a) {
      a.classList.toggle("is-active", a.dataset.module === id);
    });
    const title = document.getElementById("bm-page-title");
    const lede = document.getElementById("bm-page-lede");
    const navDec = document.getElementById("bm-nav-decision");
    if (id === "decision") {
      if (title) title.textContent = "Executive Decision";
      if (lede) lede.textContent = "Conversa visual — problema, evidência, custo, caminho e primeiro passo.";
      if (navDec) navDec.hidden = false;
      history.replaceState(null, "", "#decision");
    } else {
      if (title) title.textContent = "Abertura executiva";
      if (lede) lede.textContent = "Primeiros 30 segundos — estado, indicadores e uma decisão.";
      if (navDec) navDec.hidden = true;
      history.replaceState(null, "", "#first");
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function openDecisionExperience() {
    if (!lastPayload || !lastPayload.decision_experience || !DX) {
      setStatus("Decision Experience indisponível neste payload.", true);
      return;
    }
    DX.render(
      document.getElementById("bm-decision-experience"),
      lastPayload.decision_experience,
      function () {
        showView("first");
      }
    );
    showView("decision");
  }

  function renderAll(payload) {
    lastPayload = payload;
    const fx = payload.first_experience;
    if (!fx || !FX) {
      setStatus("Primeira experiência indisponível neste payload.", true);
      return;
    }
    FX.render(document.getElementById("bm-first-experience"), fx, openDecisionExperience);
    if ((location.hash || "").replace("#", "") === "decision") {
      openDecisionExperience();
    } else {
      showView("first");
    }
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

  document.getElementById("bm-nav-first").addEventListener("click", function (e) {
    e.preventDefault();
    showView("first");
  });
  const navDec = document.getElementById("bm-nav-decision");
  if (navDec) {
    navDec.addEventListener("click", function (e) {
      e.preventDefault();
      openDecisionExperience();
    });
  }

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") showView("first");
  });

  (function initDates() {
    document.getElementById("periodo_inicio").value = "2026-01";
    document.getElementById("periodo_fim").value = "2026-03";
  })();

  load();
})();
