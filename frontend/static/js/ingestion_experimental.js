/**
 * Experimental intelligent ingestion UI.
 * Auth comes from session cookies (PR #4) — never from identity headers.
 * All quality / reupload decisions come from the API — no client-side metrics.
 */
(function () {
  "use strict";

  const state = {
    step: 1,
    clientId: null,
    competencia: null,
    preview: null,
    abort: null,
  };

  const $ = (id) => document.getElementById(id);
  const statusEl = $("status");
  const bar = $("bar");

  function setStatus(msg, kind) {
    statusEl.textContent = msg || "";
    statusEl.className =
      "ing-meta" + (kind === "err" ? " ing-err" : kind === "warn" ? " ing-warn" : "");
  }

  function showStep(n) {
    state.step = n;
    document.querySelectorAll(".ing-step").forEach((el) => {
      el.classList.toggle("active", Number(el.dataset.step) === n);
    });
    bar.style.width = `${(n / 4) * 100}%`;
  }

  function esc(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  $("next1").addEventListener("click", () => {
    state.clientId = Number($("clientId").value);
    state.competencia = $("competencia").value;
    if (!state.clientId || !state.competencia) {
      setStatus("Preencha cliente e competência.", "err");
      return;
    }
    if (state.competencia.includes("-")) {
      state.competencia = state.competencia.slice(0, 7);
    }
    setStatus("");
    showStep(2);
  });

  $("back2").addEventListener("click", () => showStep(1));
  $("cancelBtn").addEventListener("click", () => {
    if (state.abort) state.abort.abort();
    state.preview = null;
    setStatus("Cancelado.");
    showStep(1);
  });

  $("uploadBtn").addEventListener("click", async () => {
    const file = $("file").files && $("file").files[0];
    if (!file) {
      setStatus("Selecione um arquivo.", "err");
      return;
    }
    const btn = $("uploadBtn");
    btn.disabled = true;
    setStatus("Analisando…");
    state.abort = new AbortController();
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("client_id", String(state.clientId));
      fd.append("competencia", state.competencia);
      const res = await fetch("/api/ingestion/preview", {
        method: "POST",
        body: fd,
        credentials: "same-origin",
        signal: state.abort.signal,
      });
      const body = await res.json().catch(() => ({}));
      if (res.status === 503) {
        throw new Error(
          "Ingestão indisponível: autenticação (PR #4) ou persistência não configuradas."
        );
      }
      if (!res.ok) {
        throw new Error(body.detail?.message || body.detail || "Falha na prévia");
      }
      state.preview = body;
      renderReview(body);
      showStep(3);
      setStatus("Prévia pronta — revise antes de confirmar.");
    } catch (err) {
      if (err.name === "AbortError") setStatus("Cancelado.");
      else setStatus(err.message || "Erro", "err");
    } finally {
      btn.disabled = false;
    }
  });

  function renderReview(p) {
    const iqb = p.iqb || {};
    const reup = p.reupload || {};
    $("review").innerHTML = `
      <p><strong>Arquivo:</strong> ${esc(p.file_name)} · hash ${esc(p.sha256_raw_partial)}…</p>
      <p><strong>Aba / cabeçalho:</strong> ${esc(p.aba)} / linha ${esc(p.header_row)}</p>
      <p><strong>Linhas:</strong> ${esc(p.total_rows)} (válidas ${esc(p.valid_rows)}, alertas ${esc(p.alert_rows)}, inválidas ${esc(p.invalid_rows)})</p>
      <p><strong>IQB (consultivo):</strong> ${esc(iqb.iqb)} · ${esc(iqb.classificacao)}</p>
      <p><strong>Reupload:</strong> ${esc(reup.classification)} — ${esc(reup.message)}</p>
      <p><strong>Decisão recomendada:</strong> ${esc(p.recommended_decision)}</p>
      <p class="ing-meta">Amostra mascarada: ${esc(JSON.stringify(p.sample_masked || []).slice(0, 280))}…</p>
    `;
    $("importBtn").disabled = true;
  }

  $("confirmBtn").addEventListener("click", async () => {
    if (!state.preview) return;
    const fd = new FormData();
    fd.append("client_id", String(state.clientId));
    fd.append("token", state.preview.confirmation_token);
    const just = ($("justification").value || "").trim();
    if (just) fd.append("admin_justification", just);
    setStatus("Confirmando…");
    try {
      const res = await fetch(`/api/ingestion/previews/${state.preview.preview_id}/confirm`, {
        method: "POST",
        body: fd,
        credentials: "same-origin",
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(body.detail || "Confirmação falhou");
      $("importBtn").disabled = false;
      setStatus("Confirmado. Pode importar.");
    } catch (err) {
      setStatus(err.message || "Erro", "err");
    }
  });

  $("importBtn").addEventListener("click", async () => {
    if (!state.preview) return;
    const fd = new FormData();
    fd.append("client_id", String(state.clientId));
    fd.append("competencia", state.competencia);
    fd.append("token", state.preview.confirmation_token);
    fd.append("content_hash", state.preview.content_hash_normalized);
    setStatus("Importando…");
    $("importBtn").disabled = true;
    try {
      const res = await fetch(`/api/ingestion/previews/${state.preview.preview_id}/import`, {
        method: "POST",
        body: fd,
        credentials: "same-origin",
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(body.detail || "Importação falhou");
      $("result").innerHTML = `<pre class="ing-meta">${esc(JSON.stringify(body, null, 2))}</pre>`;
      showStep(4);
      setStatus("Importação concluída (camada canônica experimental).");
    } catch (err) {
      setStatus(err.message || "Erro", "err");
      $("importBtn").disabled = false;
    }
  });

  $("restart").addEventListener("click", () => {
    state.preview = null;
    $("file").value = "";
    showStep(1);
    setStatus("");
  });
})();
