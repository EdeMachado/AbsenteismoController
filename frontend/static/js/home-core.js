(function () {
  "use strict";
  var BC = window.BioMedCore;
  if (!BC || !BC.requireAuth("/")) return;

  document.getElementById("bc-hello").textContent = "Olá, " + BC.userName();
  document.getElementById("bc-company").textContent = BC.clientName();
  document.getElementById("bc-hello-sub").textContent =
    "Empresa atual e atalhos de entrada — sem repetir o dashboard completo.";

  async function load() {
    var cid = BC.clientId();
    if (!cid) {
      document.getElementById("bc-alerts").innerHTML =
        '<div class="bc-empty"><strong>Sem empresa</strong>Selecione uma empresa em Operação.</div>';
      document.getElementById("bc-activity-body").innerHTML =
        '<tr><td colspan="4">Selecione uma empresa para ver uploads.</td></tr>';
      return;
    }

    var dash = await BC.api("/api/dashboard?client_id=" + encodeURIComponent(cid));
    if (dash.ok) {
      var data = await dash.json();
      var m = BC.mapDashboardMetrics(data.metricas || {});
      document.getElementById("h-dias").textContent = BC.fmtNum(m.dias, 1);
      document.getElementById("h-horas").textContent = BC.fmtNum(m.horas, 1);
      document.getElementById("h-atest").textContent = BC.fmtNum(m.atestados, 0);
      document.getElementById("h-colab").textContent = BC.fmtNum(m.colaboradores, 0);
      window.__RC25_HOME_LAST__ = { metricas: data.metricas || {}, mapped: m };
    }

    var alertsBox = document.getElementById("bc-alerts");
    try {
      var ar = await BC.api("/api/alertas?client_id=" + encodeURIComponent(cid));
      if (ar.ok) {
        var payload = await ar.json();
        var list = Array.isArray(payload) ? payload : payload.alertas || [];
        if (!list.length) {
          alertsBox.innerHTML =
            '<div class="bc-empty"><strong>Nenhum alerta crítico</strong>Nada urgente no momento.</div>';
        } else {
          alertsBox.innerHTML = list
            .slice(0, 5)
            .map(function (a) {
              return (
                '<div style="padding:0.65rem 0;border-bottom:1px solid var(--bc-line)">' +
                "<strong>" +
                (a.titulo || a.tipo || "Alerta") +
                "</strong><div style='color:var(--bc-muted);font-size:0.9rem'>" +
                (a.mensagem || a.descricao || "") +
                "</div></div>"
              );
            })
            .join("");
        }
      }
    } catch (e) {
      alertsBox.innerHTML = '<div class="bc-empty"><strong>Alertas indisponíveis</strong></div>';
    }

    try {
      var ur = await BC.api("/api/uploads?client_id=" + encodeURIComponent(cid));
      var body = document.getElementById("bc-activity-body");
      if (ur.ok) {
        var ups = await ur.json();
        if (!Array.isArray(ups) || !ups.length) {
          body.innerHTML = '<tr><td colspan="4">Nenhum upload recente.</td></tr>';
        } else {
          body.innerHTML = ups
            .slice(0, 8)
            .map(function (u) {
              return (
                "<tr><td>" +
                (u.filename || "—") +
                "</td><td>" +
                (u.mes_referencia || "—") +
                "</td><td>" +
                (u.total_registros != null ? u.total_registros : "—") +
                "</td><td>" +
                (u.data_upload ? String(u.data_upload).slice(0, 16).replace("T", " ") : "—") +
                "</td></tr>"
              );
            })
            .join("");
        }
      }
    } catch (e) {}
  }

  load().catch(console.error);
})();
