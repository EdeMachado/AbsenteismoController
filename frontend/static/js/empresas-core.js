(function () {
  "use strict";
  var BC = window.BioMedCore;
  if (!BC || !BC.requireAuth("/clientes")) return;

  var all = [];
  document.getElementById("bc-active").textContent = "Ativa: " + BC.clientName();

  function statusOf(c) {
    var sit = String(c.situacao || c.status || "ativo").toLowerCase();
    var uploads = Number(c.total_uploads != null ? c.total_uploads : c.uploads_count != null ? c.uploads_count : -1);
    if (sit.indexOf("arquiv") >= 0 || sit.indexOf("baixad") >= 0 || sit.indexOf("inativ") >= 0) return "arquivado";
    if (uploads === 0) return "sem_dados";
    return "ativo";
  }

  function render() {
    var q = (document.getElementById("bc-q").value || "").toLowerCase().trim();
    var st = document.getElementById("bc-status").value;
    var filtered = all.filter(function (c) {
      var name = String(c.nome_fantasia || c.nome || "").toLowerCase();
      var cnpj = String(c.cnpj || "");
      var okQ = !q || name.indexOf(q) >= 0 || cnpj.indexOf(q) >= 0;
      var s = statusOf(c);
      var okS = st === "all" || s === st;
      return okQ && okS;
    });

    var ativos = all.filter(function (c) { return statusOf(c) === "ativo"; }).length;
    var empty = all.filter(function (c) { return statusOf(c) === "sem_dados"; }).length;
    var arch = all.filter(function (c) { return statusOf(c) === "arquivado"; }).length;
    document.getElementById("s-total").textContent = BC.fmtNum(all.length, 0);
    document.getElementById("s-ativos").textContent = BC.fmtNum(ativos, 0);
    document.getElementById("s-empty").textContent = BC.fmtNum(empty, 0);
    document.getElementById("s-arch").textContent = BC.fmtNum(arch, 0);

    var root = document.getElementById("bc-companies");
    if (!filtered.length) {
      root.innerHTML = '<div class="bc-empty"><strong>Nenhuma empresa</strong>Ajuste a busca ou o filtro.</div>';
      return;
    }

    var activeId = String(BC.clientId() || "");
    root.innerHTML = filtered
      .map(function (c) {
        var name = c.nome_fantasia || c.nome || "Empresa";
        var s = statusOf(c);
        var label = s === "ativo" ? "Ativa" : s === "sem_dados" ? "Sem dados" : "Arquivada";
        var cls = s === "ativo" ? "is-active" : s === "sem_dados" ? "is-empty" : "is-archived";
        var uploads = c.total_uploads != null ? c.total_uploads : c.uploads_count != null ? c.uploads_count : "—";
        var regs = c.total_registros != null ? c.total_registros : c.registros != null ? c.registros : "—";
        var funcs =
          c.total_funcionarios != null
            ? c.total_funcionarios
            : c.qtd_funcionarios != null
              ? c.qtd_funcionarios
              : c.funcionarios != null
                ? c.funcionarios
                : "—";
        var last =
          c.ultimo_processamento ||
          c.ultimo_upload ||
          c.last_upload ||
          c.updated_at ||
          "—";
        if (last && last !== "—") last = String(last).slice(0, 10);
        var isActive = String(c.id) === activeId;
        return (
          '<article class="bc-company">' +
          '<div class="bc-company-top">' +
          '<div class="bc-avatar">' +
          BC.initials(name) +
          "</div><div style='flex:1;min-width:0'>" +
          "<h3>" +
          name +
          (isActive ? ' <span class="bc-chip is-brand" style="font-size:0.7rem">Em uso</span>' : "") +
          "</h3>" +
          '<span class="bc-status ' +
          cls +
          '">' +
          label +
          "</span>" +
          '<div style="color:var(--bc-muted);font-size:0.85rem;margin-top:0.35rem">' +
          (c.cnpj || "CNPJ não informado") +
          "</div></div></div>" +
          '<div class="bc-company-stats">' +
          "<div><small>Colaboradores</small><strong>" +
          funcs +
          "</strong></div>" +
          "<div><small>Registros</small><strong>" +
          regs +
          "</strong></div>" +
          "<div><small>Uploads</small><strong>" +
          uploads +
          "</strong></div>" +
          "<div><small>Último processamento</small><strong style='font-size:0.85rem'>" +
          last +
          "</strong></div></div>" +
          '<button type="button" class="bc-btn" data-enter="' +
          c.id +
          '">Acessar empresa</button>' +
          "</article>"
        );
      })
      .join("");

    root.querySelectorAll("[data-enter]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var id = Number(btn.getAttribute("data-enter"));
        var c = all.find(function (x) { return Number(x.id) === id; });
        if (!c) return;
        localStorage.setItem("cliente_selecionado", String(c.id));
        localStorage.setItem("cliente_selecionado_nome", c.nome_fantasia || c.nome || "");
        localStorage.setItem("cliente_nome", c.nome_fantasia || c.nome || "");
        location.href = "/";
      });
    });
  }

  async function load() {
    var res = await BC.api("/api/clientes");
    if (!res.ok) throw new Error("clientes " + res.status);
    all = await res.json();
    if (!Array.isArray(all)) all = [];
    render();
  }

  document.getElementById("bc-q").addEventListener("input", render);
  document.getElementById("bc-status").addEventListener("change", render);
  load().catch(function (e) {
    console.error(e);
    document.getElementById("bc-companies").innerHTML =
      '<div class="bc-empty"><strong>Falha ao carregar</strong>Não foi possível listar empresas.</div>';
  });
})();
