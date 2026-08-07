# EXEC-11A — Product Audit Preview

**Branch:** `cursor/exec11a-product-audit-preview-f8f5`  
**Status:** Draft · sem merge · sem deploy · sem produção

## Objetivo

Consolidar EXEC-08→11 em **um** preview navegável para auditoria crítica integral.  
Sem novas funcionalidades, análises, APIs ou ORBIT.

## URL

http://127.0.0.1:18083/preview/product-audit

Sem login. Dataset 100% sintético. Valores **ILUSTRATIVOS**.

## Como abrir

```bash
cd /workspace
PYTHONPATH=/workspace SECRET_KEY=audit-preview \
  ABSENTEISMO_SQLITE_PATH=/workspace/database/exec02_synth.sqlite \
  python3 -m uvicorn backend.main:app --host 127.0.0.1 --port 18083
```

Abrir: http://127.0.0.1:18083/preview/product-audit

HTML: `frontend/preview/product-audit.html`

## Screenshots (links diretos)

- [`audit_cover_1440x900.png`](../../tests/artifacts/product_audit/audit_cover_1440x900.png)
- [`audit_opening_1440x900.png`](../../tests/artifacts/product_audit/audit_opening_1440x900.png)
- [`audit_kpis_1440x900.png`](../../tests/artifacts/product_audit/audit_kpis_1440x900.png)
- [`audit_decision_1440x900.png`](../../tests/artifacts/product_audit/audit_decision_1440x900.png)
- [`audit_evidence_1440x900.png`](../../tests/artifacts/product_audit/audit_evidence_1440x900.png)
- [`audit_financial_1440x900.png`](../../tests/artifacts/product_audit/audit_financial_1440x900.png)
- [`audit_closing_1440x900.png`](../../tests/artifacts/product_audit/audit_closing_1440x900.png)
- [`audit_full_1440x900.png`](../../tests/artifacts/product_audit/audit_full_1440x900.png)
- [`audit_mobile_390x844.png`](../../tests/artifacts/product_audit/audit_mobile_390x844.png)

## PDF

[`tests/artifacts/product_audit/BIOMED_PRODUCT_AUDIT.pdf`](../../tests/artifacts/product_audit/BIOMED_PRODUCT_AUDIT.pdf)

## Fluxo

Cover → Opening → 4 KPIs → Decision → Decision Experience → Evidence → Financial → Closing → Signature  

**Modo Apresentação:** botão no chrome (tela cheia sequencial; Esc sai).

## Controles

- Sem merge · sem deploy · sem produção · sem migration  
- Não inicia EXEC-12
