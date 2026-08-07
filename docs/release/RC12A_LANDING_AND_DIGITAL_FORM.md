# RC-1.2A — Landing Premium + Ficha Digital do Colaborador

**Branch:** `cursor/rc12a-landing-ficha-digital-f8f5`  
**HEAD:** `(pending)`
**Status:** Draft · sem merge · sem deploy · sem produção

## Preview

- Landing: `/preview/landing`
- Ficha Digital: `/preview/ficha-digital`
- Colaborador (link seguro): `/f/{token}`

## Parte A — Landing Premium

Institucional, whitespace generoso, sem carrossel, sem linguagem comercial exagerada.

Dobras: hero (logo/produto + título + CTAs + imagem) → Como funciona → 3 pilares → peek Executive Center → encerramento.

## Parte B — Ficha Digital

Fluxo: selecionar colaborador → escolher ficha → canal (WhatsApp link / E-mail) → gerar token opaco → enviar → colaborador aceita ciência → preenche → IA (rule engine) sugere → alerta → validação humana → eventos.

Store: `backend/digital_form/` in-memory. **Sem migration. Sem schema SQL.**

### Status

Criada · Enviada · Visualizada · Em preenchimento · Respondida · Analisada · Aguardando validação · Validada · Expirada · Cancelada

### Segurança / LGPD

- Token opaco na URL (`/f/{token}`)
- Sem CPF, matrícula, CID ou conteúdo clínico na URL/mensagem
- Expiração e cancelamento
- Tenant key de preview
- Alertas sem conteúdo clínico
- Logs/alertas sem payload clínico

### WhatsApp / E-mail

- WhatsApp modo LINK (mensagem pronta + `wa.me`)
- E-mail: assunto “Ficha para preenchimento”, corpo institucional curto

### IA

Rule engine determinístico de preview. Linguagem: “Sugere” / “Possível” / “Necessária validação”. Nunca diagnostica.

### Alertas

Integração ao shape do sininho (`window.alertasData`) sem conteúdo clínico no dropdown.

### Dashboard

Indicadores integrados no preview (enviadas, respondidas, tempo médio, pendentes, validação pendente) — sem dashboard novo.

## Testes

`tests/release/test_rc12a_landing_ficha.py`

## Screenshots

`tests/artifacts/rc12a/` — landing_desktop.png, landing_mobile.png, send_form.png, employee_mobile.png, employee_success.png, analysis.png, alerts.png, timeline.png, tracking.png

## Confirmação

Sem merge · sem deploy · sem produção. Não inicia RC-1.3.
