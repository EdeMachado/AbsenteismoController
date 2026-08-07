# RC23 — Product Experience Rebuild

**Branch:** `cursor/rc23-product-experience-rebuild-f8f5`  
**Scope:** Experience only — no DB / API / business-rule changes. Do not merge/deploy from agent.

## Critical fix — login security

**Bug:** Landing → Entrar could skip login (token resume) and skip company list (`cliente_selecionado` → `/`).

**Fix:**
- Login always shows the form (no auto-resume)
- After auth → always `/clientes`
- Clear company keys on login success and logout

Mandatory flow: **Landing → Login → Auth → Empresas → Sistema**

## Visual audit (before → after intent)

| Surface | Before | After intent |
|---------|--------|--------------|
| Landing | 7.5 | Premium BioMed entry |
| Login | 8 | Always authenticates |
| Home | 6.5 | Hub + experience layer |
| Executive | 8.5 | Reference (kept) |
| Dashboard | 2 | BI Premium grid/spacing |
| Analytics | 6.5 | Organizer in shell |
| Clientes | 3 | BioMed hero, modern cards |
| Funcionários | 2.5 | Shell + experience tables |
| Uploads | 3 | Modern dropzone |
| Produtividade | 1.5 | Purple scrubbed |
| Comparativos | 2.5 | Breathing charts |
| Power BI | 2 | Cyan scrubbed |
| Apresentação | 2 | Immersive deck in shell |
| Configurações | 2 | Calm settings surface |

## Experience layer

`frontend/static/css/biomed-experience.css` (+ shell `rc23` loads it):
- Wide content stage, modern cards/buttons/filters
- Dashboard chart grids with breathing room
- Apresentação full-bleed deck inside shell (no indigo admin margins)
- Responsive breakpoints for notebook/tablet/mobile

## Delivery checklist

- LOGIN_SECURITY_FIXED=yes
- PRESENTATION_REBUILT=yes (visual)
- DASHBOARD_REBUILT=yes (visual/layout)
- RESPONSIVE_FIXED=yes (CSS layer)
- No API/DB/migration/flag changes
