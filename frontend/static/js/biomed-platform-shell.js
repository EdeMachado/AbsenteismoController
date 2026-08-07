/**
 * BioMed Platform shell — RC-24 Final Visual Polish
 * One shell for all post-login surfaces. No new business features.
 */
(function () {
  "use strict";

  var CACHE = "rc24";

  var BREADCRUMB = {
    "/": "Início",
    "/executive": "Executive",
    "/analytics": "Analytics",
    "/analises": "Analytics",
    "/dashboard": "Analytics · Visão Geral",
    "/comparativos": "Analytics · Comparativos",
    "/dados_powerbi": "Analytics · Power BI",
    "/dashboard_powerbi": "Analytics · Dashboard Power BI",
    "/produtividade": "Analytics · Produtividade",
    "/tendencias": "Analytics · Tendências",
    "/clientes": "Operação · Clientes",
    "/funcionarios": "Operação · Funcionários",
    "/perfil_funcionario": "Operação · Perfil",
    "/upload": "Operação · Uploads",
    "/upload_inteligente": "Operação · Upload inteligente",
    "/auto_processor": "Operação · Processamento",
    "/apresentacao": "Apresentações",
    "/configuracoes": "Configurações",
    "/preview": "Operação · Preview",
  };

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

  function pathKey() {
    return (location.pathname || "/").replace(/\/$/, "") || "/";
  }

  function activeKey() {
    var p = pathKey();
    if (p === "/executive" || p.indexOf("/executive") === 0) return "executive";
    if (p === "/apresentacao") return "presentation";
    if (p === "/configuracoes") return "config";
    if (
      p === "/analytics" ||
      p === "/analises" ||
      p === "/dashboard" ||
      p === "/comparativos" ||
      p === "/dados_powerbi" ||
      p === "/dashboard_powerbi" ||
      p === "/produtividade" ||
      p === "/tendencias"
    )
      return "analytics";
    if (
      p === "/clientes" ||
      p === "/funcionarios" ||
      p === "/upload" ||
      p === "/upload_inteligente" ||
      p === "/auto_processor" ||
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
    if (!document.querySelector('link[data-bm-plat]')) {
      var l = document.createElement("link");
      l.rel = "stylesheet";
      l.href = "/static/css/biomed-platform.css?v=" + CACHE;
      l.setAttribute("data-bm-plat", "1");
      document.head.appendChild(l);
    }
    if (!document.querySelector('link[data-bm-exp]')) {
      var e = document.createElement("link");
      e.rel = "stylesheet";
      e.href = "/static/css/biomed-experience.css?v=" + CACHE;
      e.setAttribute("data-bm-exp", "1");
      document.head.appendChild(e);
    }
    if (!document.querySelector('link[data-bm-polish]')) {
      var p = document.createElement("link");
      p.rel = "stylesheet";
      p.href = "/static/css/biomed-polish.css?v=" + CACHE;
      p.setAttribute("data-bm-polish", "1");
      document.head.appendChild(p);
    }
  }

  function buildNavHtml() {
    return (
      '<aside class="bm-plat-nav" id="bm-plat-nav" aria-label="Navegação BioMed">' +
      '<div class="bm-plat-brand"><strong>BioMed</strong><span>Platform</span></div>' +
      '<div class="bm-plat-company"><small>Empresa ativa</small>' +
      companyLabel() +
      "</div>" +
      '<nav class="bm-plat-links">' +
      link("/", "Início", "home") +
      link("/executive", "Executive", "executive") +
      link("/analytics", "Analytics", "analytics") +
      link("/dashboard", "Visão Geral", "analytics", { sub: true }) +
      link("/comparativos", "Comparativos", "analytics", { sub: true }) +
      link("/dados_powerbi", "Power BI", "analytics", { sub: true }) +
      link("/produtividade", "Produtividade", "analytics", { sub: true }) +
      link("/dashboard#graficosConverplast", "Setores", "analytics", { sub: true }) +
      link("/dashboard#chartCids", "CID", "analytics", { sub: true }) +
      link("/dashboard#chartEvolucao", "Tendências", "analytics", { sub: true }) +
      link("/clientes", "Operação", "ops") +
      link("/clientes", "Clientes", "ops", { sub: true }) +
      link("/funcionarios", "Funcionários", "ops", { sub: true }) +
      link("/upload", "Uploads", "ops", { sub: true }) +
      link("/upload_inteligente", "Upload inteligente", "ops", { sub: true }) +
      link("/apresentacao", "Apresentações", "presentation") +
      link("#", "Fichas", "fichas", { disabled: true }) +
      link("/configuracoes", "Configurações", "config") +
      "</nav>" +
      '<div class="bm-plat-user">' +
      '<span>' +
      userLabel() +
      "</span>" +
      '<button type="button" class="bm-plat-logout" id="bm-plat-logout">Sair</button>' +
      "</div>" +
      "</aside>"
    );
  }

  function buildChrome(mainHtmlSlotId) {
    var crumb = BREADCRUMB[pathKey()] || "BioMed Platform";
    return (
      '<button type="button" class="bm-plat-toggle" id="bm-plat-toggle" aria-expanded="false">Menu</button>' +
      buildNavHtml() +
      '<div class="bm-plat-column">' +
      '<header class="bm-plat-top" id="bm-plat-top">' +
      '<div class="bm-plat-top-brand">BioMed Platform</div>' +
      '<div class="bm-plat-top-meta"><span>' +
      companyLabel() +
      "</span><span>" +
      userLabel() +
      "</span></div>" +
      "</header>" +
      '<div class="bm-plat-crumb" id="bm-plat-crumb">' +
      crumb +
      "</div>" +
      '<div class="bm-plat-main" id="' +
      mainHtmlSlotId +
      '"></div>' +
      '<footer class="bm-plat-foot">BioMed Platform · Inteligência em Saúde Corporativa</footer>' +
      "</div>"
    );
  }

  function wireToggle(shell) {
    var btn = document.getElementById("bm-plat-toggle");
    if (btn) {
      btn.addEventListener("click", function () {
        var open = shell.classList.toggle("is-nav-open");
        btn.setAttribute("aria-expanded", open ? "true" : "false");
      });
    }
    var logout = document.getElementById("bm-plat-logout");
    if (logout && !logout._bmBound) {
      logout._bmBound = true;
      logout.addEventListener("click", function () {
        try {
          localStorage.removeItem("access_token");
          localStorage.removeItem("user");
          localStorage.removeItem("cliente_selecionado");
          localStorage.removeItem("cliente_selecionado_nome");
          localStorage.removeItem("cliente_nome");
          localStorage.removeItem("cliente_cnpj");
          localStorage.removeItem("cliente_tema");
          localStorage.removeItem("cliente_logo_url");
        } catch (e) {}
        window.location.href = "/login";
      });
    }
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
    shell.innerHTML = buildChrome("bm-plat-main-slot");
    document.body.appendChild(shell);
    shell.querySelector("#bm-plat-main-slot").appendChild(main);
    wireToggle(shell);
  }

  function mountLegacyOverlay() {
    ensureStyles();
    document.body.classList.add("bm-plat-body", "bm-plat-legacy");
    if (document.getElementById("bm-plat-nav")) return;

    var wrap = document.createElement("div");
    wrap.className = "bm-plat-shell";
    wrap.id = "bm-plat-shell";
    wrap.innerHTML = buildChrome("bm-plat-legacy-slot");

    var legacyRoot =
      document.querySelector(".main-content") ||
      document.querySelector(".content-wrapper") ||
      document.querySelector(".app-container") ||
      document.querySelector(".powerbi-container") ||
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
    wireToggle(wrap);
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
