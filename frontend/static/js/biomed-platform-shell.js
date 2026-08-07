/**
 * BioMed One Platform shell — RC-20 Phase 1
 * Injects unified navigation; does not alter business APIs.
 */
(function () {
  "use strict";

  var CACHE = "rc20p1";

  function companyLabel() {
    try {
      var raw = localStorage.getItem("cliente_selecionado_nome") || localStorage.getItem("cliente_nome");
      if (raw) return raw;
      var id = localStorage.getItem("cliente_selecionado");
      return id ? "Empresa #" + id : "Nenhuma empresa selecionada";
    } catch (e) {
      return "Empresa";
    }
  }

  function userLabel() {
    try {
      var u = JSON.parse(localStorage.getItem("user") || "null");
      if (u && (u.nome || u.username || u.email)) return u.nome || u.username || u.email;
    } catch (e) {}
    return "Usuário";
  }

  function activeKey() {
    var p = (location.pathname || "/").replace(/\/$/, "") || "/";
    if (p === "/executive" || p.indexOf("/executive") === 0) return "executive";
    if (p === "/apresentacao") return "presentation";
    if (p === "/configuracoes") return "config";
    if (
      p === "/analises" ||
      p === "/tendencias" ||
      p === "/comparativos" ||
      p === "/dados_powerbi" ||
      p === "/dashboard_powerbi" ||
      p === "/dashboard"
    )
      return "analytics";
    if (
      p === "/clientes" ||
      p === "/funcionarios" ||
      p === "/upload" ||
      p === "/produtividade" ||
      p === "/perfil_funcionario" ||
      p === "/preview"
    )
      return "ops";
    if (p === "/" || p === "/index.html") return "home";
    return "";
  }

  function link(href, label, key, opts) {
    opts = opts || {};
    var cls = activeKey() === key ? "is-active" : "";
    if (opts.disabled) cls += " bm-plat-disabled";
    if (opts.sub) cls += " bm-plat-sub";
    var title = opts.disabled ? ' title="Em breve"' : "";
    return (
      '<a href="' +
      href +
      '" class="' +
      cls.trim() +
      '"' +
      title +
      ">" +
      label +
      "</a>"
    );
  }

  function ensureStyles() {
    if (document.querySelector('link[data-bm-plat]')) return;
    var l = document.createElement("link");
    l.rel = "stylesheet";
    l.href = "/static/css/biomed-platform.css?v=" + CACHE;
    l.setAttribute("data-bm-plat", "1");
    document.head.appendChild(l);
  }

  function buildNavHtml() {
    return (
      '<aside class="bm-plat-nav" id="bm-plat-nav" aria-label="Navegação BioMed">' +
      '<div class="bm-plat-brand"><strong>BioMed</strong><span>Inteligência em Saúde Corporativa</span></div>' +
      '<div class="bm-plat-company"><small>Empresa ativa</small>' +
      companyLabel() +
      "</div>" +
      '<nav class="bm-plat-links">' +
      link("/", "Início", "home") +
      link("/executive", "Visão Executiva", "executive") +
      link("/analises", "Analytics", "analytics") +
      link("/dashboard", "Dashboard", "analytics", { sub: true }) +
      link("/dados_powerbi", "Meus Dados", "analytics", { sub: true }) +
      link("/clientes", "Operacional", "ops") +
      link("/upload", "Upload", "ops", { sub: true }) +
      link("/funcionarios", "Funcionários", "ops", { sub: true }) +
      link("/produtividade", "Produtividade", "ops", { sub: true }) +
      link("/apresentacao", "Apresentação", "presentation") +
      link("#", "Fichas", "fichas", { disabled: true }) +
      link("/configuracoes", "Configurações", "config") +
      "</nav>" +
      '<div class="bm-plat-user">' +
      userLabel() +
      "</div>" +
      "</aside>"
    );
  }

  function mountFullShell(mainSelector) {
    ensureStyles();
    document.body.classList.add("bm-plat-body");
    if (document.getElementById("bm-plat-shell")) return;

    var main = document.querySelector(mainSelector || "#bm-plat-content");
    if (!main) {
      main = document.createElement("div");
      main.id = "bm-plat-content";
      while (document.body.firstChild) main.appendChild(document.body.firstChild);
      document.body.appendChild(main);
    }

    var shell = document.createElement("div");
    shell.className = "bm-plat-shell";
    shell.id = "bm-plat-shell";
    shell.innerHTML =
      '<button type="button" class="bm-plat-toggle" id="bm-plat-toggle" aria-expanded="false">Menu</button>' +
      buildNavHtml() +
      '<div class="bm-plat-main" id="bm-plat-main-slot"></div>';
    document.body.appendChild(shell);
    shell.querySelector("#bm-plat-main-slot").appendChild(main);

    var btn = document.getElementById("bm-plat-toggle");
    if (btn) {
      btn.addEventListener("click", function () {
        var open = shell.classList.toggle("is-nav-open");
        btn.setAttribute("aria-expanded", open ? "true" : "false");
      });
    }
  }

  function mountLegacyOverlay() {
    ensureStyles();
    document.body.classList.add("bm-plat-body", "bm-plat-legacy");
    if (document.getElementById("bm-plat-nav")) return;

    var wrap = document.createElement("div");
    wrap.className = "bm-plat-shell";
    wrap.id = "bm-plat-shell";
    wrap.innerHTML =
      '<button type="button" class="bm-plat-toggle" id="bm-plat-toggle" aria-expanded="false">Menu</button>' +
      buildNavHtml() +
      '<div class="bm-plat-main" id="bm-plat-legacy-slot"></div>';

    var legacyRoot =
      document.querySelector(".main-content") ||
      document.querySelector(".content-wrapper") ||
      document.querySelector(".app-container") ||
      document.body;

    var parent = legacyRoot.parentNode;
    if (legacyRoot === document.body) {
      var slotContent = document.createElement("div");
      while (document.body.firstChild) slotContent.appendChild(document.body.firstChild);
      document.body.appendChild(wrap);
      wrap.querySelector("#bm-plat-legacy-slot").appendChild(slotContent);
    } else {
      parent.insertBefore(wrap, legacyRoot);
      wrap.querySelector("#bm-plat-legacy-slot").appendChild(legacyRoot);
    }

    var btn = document.getElementById("bm-plat-toggle");
    if (btn) {
      btn.addEventListener("click", function () {
        var open = wrap.classList.toggle("is-nav-open");
        btn.setAttribute("aria-expanded", open ? "true" : "false");
      });
    }
  }

  window.BioMedPlatform = {
    mountHub: function () {
      mountFullShell("#bm-plat-content");
    },
    mountLegacy: mountLegacyOverlay,
    cache: CACHE,
  };

  document.addEventListener("DOMContentLoaded", function () {
    var mode = document.body.getAttribute("data-bm-shell");
    if (mode === "hub") window.BioMedPlatform.mountHub();
    else if (mode === "legacy") window.BioMedPlatform.mountLegacy();
    else if (mode === "nav-only") {
      ensureStyles();
      document.body.classList.add("bm-plat-body");
    }
  });
})();
