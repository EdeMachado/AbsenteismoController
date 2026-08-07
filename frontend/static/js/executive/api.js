/**
 * BioMed Executive Intelligence — API client (aggregated data only).
 */
(function (global) {
  "use strict";

  async function fetchJson(url) {
    const res = await fetch(url, {
      credentials: "same-origin",
      headers: { Accept: "application/json" },
    });
    if (!res.ok) {
      const err = new Error("HTTP " + res.status);
      err.status = res.status;
      throw err;
    }
    return res.json();
  }

  function qs(params) {
    const p = new URLSearchParams();
    Object.keys(params || {}).forEach(function (k) {
      if (params[k] != null && params[k] !== "") p.set(k, params[k]);
    });
    const s = p.toString();
    return s ? "?" + s : "";
  }

  const ExecutiveApi = {
    commandCenter: function (opts) {
      return fetchJson("/api/executive/command-center" + qs(opts));
    },
    intelligence: function (opts) {
      return fetchJson("/api/executive/intelligence" + qs(opts));
    },
    actionPlan: function (opts) {
      return fetchJson("/api/executive/action-plan" + qs(opts));
    },
    performance: function (opts) {
      return fetchJson("/api/executive/performance" + qs(opts));
    },
    meta: function () {
      return fetchJson("/api/executive/meta");
    },
  };

  global.BioMedExecutiveApi = ExecutiveApi;
})(typeof window !== "undefined" ? window : this);
