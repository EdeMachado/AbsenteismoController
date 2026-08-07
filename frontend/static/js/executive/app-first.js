/**
 * EXEC-08/09/10 + RC-1.2 — bootstrap with micro-UX consolidation.
 * No business-rule changes. Human language. Clear back/escape. Focus after view.
 */
(function () {
  "use strict";

  const FX = window.BioMedFirstExperience;
  const DX = window.BioMedDecisionExperience;
  const EI = window.BioMedEvidenceIntelligence;
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
        throw new Error("session");
      }
      if (res.status === 403) {
        throw new Error("forbidden");
      }
      if (!res.ok) throw new Error("http");
      return res.json();
    });
  }

  function setStatus(msg, isError, withRetry) {
    const el = document.getElementById("bm-status");
    if (!el) return;
    if (!msg) {
      el.style.display = "none";
      el.innerHTML = "";
      el.className = "";
      return;
    }
    el.style.display = "block";
    el.className = isError ? "bm-error" : "bm-loading";
    el.textContent = msg;
    if (withRetry && isError) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "bm-btn bm-btn-ghost";
      btn.style.marginLeft = "0.75rem";
      btn.textContent = "Tentar novamente";
      btn.addEventListener("click", function () {
        load();
      });
      el.appendChild(btn);
    }
  }

  function setLoadingSkeleton(on) {
    const main = document.getElementById("bm-main");
    if (!main) return;
    main.classList.toggle("is-loading", !!on);
  }

  function focusMain() {
    const main = document.getElementById("bm-main");
    if (!main) return;
    if (!main.hasAttribute("tabindex")) main.setAttribute("tabindex", "-1");
    try {
      main.focus({ preventScroll: true });
    } catch (e) {
      main.focus();
    }
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
    const navEv = document.getElementById("bm-nav-evidence");

    if (id === "evidence") {
      if (title) title.textContent = "Evidências";
      if (lede) lede.textContent = "Por que podemos confiar nesta recomendação.";
      if (navDec) navDec.hidden = false;
      if (navEv) navEv.hidden = false;
      history.replaceState(null, "", "#evidence");
    } else if (id === "decision") {
      if (title) title.textContent = "Decisão";
      if (lede) lede.textContent = "O que fazer — impacto, caminho e próximo passo.";
      if (navDec) navDec.hidden = false;
      if (navEv) navEv.hidden = false;
      history.replaceState(null, "", "#decision");
    } else {
      if (title) title.textContent = "Abertura executiva";
      if (lede) lede.textContent = "Estado, indicadores e uma decisão.";
      if (navDec) navDec.hidden = true;
      if (navEv) navEv.hidden = true;
      history.replaceState(null, "", "#first");
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
    focusMain();
  }

  function openEvidenceIntelligence() {
    if (!lastPayload || !lastPayload.evidence_intelligence || !EI) {
      setStatus("Não há evidência suficiente para esta leitura.", true, true);
      return;
    }
    EI.render(document.getElementById("bm-evidence-intelligence"), lastPayload.evidence_intelligence, {
      onBack: function () {
        openDecisionExperience();
      },
    });
    showView("evidence");
  }

  function openDecisionExperience() {
    if (!lastPayload || !lastPayload.decision_experience || !DX) {
      setStatus("Não foi possível abrir esta decisão.", true, true);
      return;
    }
    DX.render(
      document.getElementById("bm-decision-experience"),
      lastPayload.decision_experience,
      function () {
        showView("first");
      },
      openEvidenceIntelligence
    );
    showView("decision");
  }

  function renderAll(payload) {
    lastPayload = payload;
    const fx = payload.first_experience;
    if (!fx || !FX) {
      setStatus("Dados insuficientes para esta análise.", true, true);
      return;
    }
    FX.render(document.getElementById("bm-first-experience"), fx, openDecisionExperience);
    const hash = (location.hash || "").replace("#", "");
    if (hash === "evidence") {
      openEvidenceIntelligence();
    } else if (hash === "decision") {
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
    setLoadingSkeleton(true);
    try {
      const payload = await fetchJson("/api/executive/command-center", filterOpts());
      renderAll(payload);
      setStatus("");
    } catch (err) {
      const msg =
        err && err.message === "forbidden"
          ? "Você não tem permissão para esta análise."
          : err && err.message === "session"
            ? "Sessão expirada. Faça login novamente."
            : "Não foi possível carregar esta análise.";
      setStatus(msg, true, err && err.message !== "session");
    } finally {
      setLoadingSkeleton(false);
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
  const navEv = document.getElementById("bm-nav-evidence");
  if (navEv) {
    navEv.addEventListener("click", function (e) {
      e.preventDefault();
      openEvidenceIntelligence();
    });
  }

  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    const hash = (location.hash || "").replace("#", "");
    if (hash === "evidence") openDecisionExperience();
    else if (hash === "decision") showView("first");
    else showView("first");
  });

  window.addEventListener("hashchange", function () {
    const hash = (location.hash || "").replace("#", "");
    if (hash === "evidence") openEvidenceIntelligence();
    else if (hash === "decision") openDecisionExperience();
    else showView("first");
  });

  (function initDates() {
    document.getElementById("periodo_inicio").value = "2026-01";
    document.getElementById("periodo_fim").value = "2026-03";
  })();

  load();
})();
