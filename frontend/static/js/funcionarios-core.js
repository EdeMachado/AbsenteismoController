(function () {
  "use strict";
  var BC = window.BioMedCore;
  if (!BC || !BC.requireAuth("/funcionarios")) return;
  document.getElementById("bc-company").textContent = BC.clientName();

  var rows = [];

  function aggregate(list) {
    var map = {};
    (list || []).forEach(function (a) {
      var name = a.nomecompleto || a.nome_funcionario || a.nome || "—";
      var setor = a.setor || "—";
      var key = name + "||" + setor;
      if (!map[key]) {
        map[key] = { nome: name, setor: setor, atestados: 0, dias: 0, horas: 0 };
      }
      map[key].atestados += 1;
      map[key].dias += Number(a.dias_atestados || 0);
      map[key].horas += Number(a.horas_perdi || a.horas_perdidas || 0);
    });
    return Object.keys(map)
      .map(function (k) { return map[k]; })
      .sort(function (a, b) { return b.dias - a.dias; });
  }

  function render() {
    var q = (document.getElementById("bc-q").value || "").toLowerCase();
    var setor = document.getElementById("bc-setor").value;
    var view = rows.filter(function (r) {
      return (!q || r.nome.toLowerCase().indexOf(q) >= 0) && (!setor || r.setor === setor);
    });
    document.getElementById("f-total").textContent = BC.fmtNum(view.length, 0);
    document.getElementById("f-atest").textContent = BC.fmtNum(
      view.reduce(function (s, r) { return s + r.atestados; }, 0),
      0
    );
    document.getElementById("f-dias").textContent = BC.fmtNum(
      view.reduce(function (s, r) { return s + r.dias; }, 0),
      1
    );
    var body = document.getElementById("bc-body");
    if (!view.length) {
      body.innerHTML = '<tr><td colspan="6">Nenhum colaborador no filtro.</td></tr>';
      return;
    }
    body.innerHTML = view
      .slice(0, 200)
      .map(function (r) {
        var href =
          "/perfil_funcionario?nome=" + encodeURIComponent(r.nome);
        return (
          "<tr><td><strong>" +
          r.nome +
          "</strong></td><td>" +
          r.setor +
          "</td><td>" +
          BC.fmtNum(r.atestados, 0) +
          "</td><td>" +
          BC.fmtNum(r.dias, 1) +
          "</td><td>" +
          BC.fmtNum(r.horas, 1) +
          '</td><td><a class="bc-btn bc-btn-secondary bc-btn-sm" href="' +
          href +
          '">Perfil</a></td></tr>'
        );
      })
      .join("");
  }

  async function load() {
    var cid = BC.clientId();
    if (!cid) {
      document.getElementById("bc-body").innerHTML =
        '<tr><td colspan="6">Selecione uma empresa.</td></tr>';
      return;
    }
    // Prefer dashboard top_funcionarios + dados/todos for detail
    var dash = await BC.api("/api/dashboard?client_id=" + encodeURIComponent(cid));
    var detalhe = await BC.api("/api/dados/todos?client_id=" + encodeURIComponent(cid));
    var raw = [];
    if (detalhe.ok) {
      var payload = await detalhe.json();
      raw = Array.isArray(payload) ? payload : payload.dados || payload.items || [];
    }
    if ((!raw || !raw.length) && dash.ok) {
      var d = await dash.json();
      raw = (d.top_funcionarios || []).map(function (f) {
        return {
          nomecompleto: f.nome || f.nomecompleto || f.funcionario,
          setor: f.setor || "—",
          dias_atestados: f.total_dias || f.dias || 0,
          horas_perdi: f.total_horas || f.horas || 0,
          _synthetic: true,
        };
      });
      // expand synthetic counts poorly — keep as single rows
    }
    rows = aggregate(raw);
    var setores = {};
    rows.forEach(function (r) { setores[r.setor] = true; });
    var sel = document.getElementById("bc-setor");
    sel.innerHTML =
      '<option value="">Todos</option>' +
      Object.keys(setores)
        .sort()
        .map(function (s) {
          return '<option value="' + s + '">' + s + "</option>";
        })
        .join("");
    render();
    window.__RC25_FUNCIONARIOS_LAST__ = { count: rows.length };
  }

  document.getElementById("bc-q").addEventListener("input", render);
  document.getElementById("bc-setor").addEventListener("change", render);
  load().catch(console.error);
})();
