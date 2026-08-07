(function () {
  "use strict";
  var BC = window.BioMedCore;
  if (!BC || !BC.requireAuth("/upload")) return;
  document.getElementById("bc-company").textContent = BC.clientName();

  function setStep(n) {
    document.querySelectorAll(".bc-step").forEach(function (el) {
      el.classList.toggle("is-active", Number(el.getAttribute("data-step")) <= n);
    });
  }

  async function loadHist() {
    var cid = BC.clientId();
    var body = document.getElementById("bc-hist");
    if (!cid) {
      body.innerHTML = '<tr><td colspan="4">Selecione uma empresa.</td></tr>';
      return;
    }
    var res = await BC.api("/api/uploads?client_id=" + encodeURIComponent(cid));
    if (!res.ok) {
      body.innerHTML = '<tr><td colspan="4">Falha ao carregar histórico.</td></tr>';
      return;
    }
    var ups = await res.json();
    if (!Array.isArray(ups) || !ups.length) {
      body.innerHTML = '<tr><td colspan="4">Nenhum upload ainda.</td></tr>';
      return;
    }
    body.innerHTML = ups
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
    setStep(6);
  }

  document.getElementById("bc-file").addEventListener("change", function () {
    setStep(2);
  });

  document.getElementById("bc-send").addEventListener("click", async function () {
    var cid = BC.clientId();
    var file = document.getElementById("bc-file").files[0];
    var mes = document.getElementById("bc-mes").value;
    var out = document.getElementById("bc-result");
    if (!cid) {
      out.innerHTML = '<div class="bc-empty"><strong>Empresa obrigatória</strong></div>';
      return;
    }
    if (!file || !mes) {
      out.innerHTML = '<div class="bc-empty"><strong>Arquivo e mês obrigatórios</strong></div>';
      return;
    }
    setStep(3);
    out.innerHTML = '<div class="bc-loading"><strong>Processando</strong>Enviando para a API existente…</div>';
    var fd = new FormData();
    fd.append("file", file);
    fd.append("client_id", String(cid));
    fd.append("mes_referencia", mes);
    try {
      var res = await BC.api("/api/upload", { method: "POST", body: fd });
      var text = await res.text();
      var data = {};
      try { data = JSON.parse(text); } catch (e) { data = { detail: text }; }
      if (!res.ok) {
        setStep(5);
        out.innerHTML =
          '<div class="bc-empty"><strong>Erro no processamento</strong>' +
          (data.detail || res.status) +
          "</div>";
        return;
      }
      setStep(4);
      out.innerHTML =
        '<div class="bc-empty"><strong>Processado</strong>' +
        (data.message || data.detail || "Upload concluído com a API existente.") +
        " Registros: " +
        (data.total_registros != null ? data.total_registros : "—") +
        "</div>";
      loadHist();
    } catch (e) {
      setStep(5);
      out.innerHTML = '<div class="bc-empty"><strong>Falha de rede</strong></div>';
    }
  });

  loadHist().catch(console.error);
})();
