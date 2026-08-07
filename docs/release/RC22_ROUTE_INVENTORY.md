# RC22 — Route Inventory Matrix (BioMed Platform v2.1)

Production HEAD baseline: `59300b6d25856d88172fb1e496ae793cdf73c1af`  
Scope: UI consolidation only. No DB / API / business-rule / flag changes.

## Classification legend

| Code | Meaning |
|------|---------|
| NEW_NATIVE | Built for BioMed Platform shell / brand |
| LEGACY_CONTENT_IN_NEW_SHELL | Functional legacy page wrapped by platform shell |
| FULL_LEGACY | Old full chrome (preserved offline / not primary nav) |
| STUB | Empty or placeholder page |
| ORPHAN | File exists; not in v2.1 menu |
| FLAGGED_OFF | Feature flag keeps route unavailable |
| PREVIEW_ONLY | Homologation / preview surfaces |
| REDIRECT | Safe redirect to functional surface |

## Matrix

| ROUTE | FILE | CURRENT_VISUAL | CURRENT_SHELL | DATA_SOURCE | FUNCTION | TARGET_STATE | ACTION |
|-------|------|----------------|---------------|-------------|----------|--------------|--------|
| `/landing` | `landing.html` | NEW_NATIVE (was product-name mix) | none (public) | static | marketing entry | NEW_NATIVE BioMed Platform | Brand → BioMed Platform |
| `/login` | `login.html` | NEW_NATIVE | none (public) | `/api/auth/login` | auth | NEW_NATIVE | Keep |
| `/` | `index.html` | NEW_NATIVE hub | hub shell | REAL APIs | hub | NEW_NATIVE | Keep hub links |
| `/dashboard` | `index-legacy.html` | LEGACY_CONTENT_IN_NEW_SHELL | legacy overlay | REAL dashboard APIs | Analytics · Visão Geral | content reskin in shell | Hide legacy chrome; rename surface |
| `/executive` | `executive.html` | NEW_NATIVE premium | hub shell | REAL executive APIs | Executive Intelligence | NEW_NATIVE in same shell | Keep steps only |
| `/analytics` | `analytics.html` | NEW_NATIVE organizer | hub shell | links to REAL | Analytics index | NEW_NATIVE | Keep real links only |
| `/analises` | → `analytics.html` | NEW_NATIVE | hub shell | same | Analytics alias | NEW_NATIVE | Keep |
| `/clientes` | `clientes.html` | LEGACY_CONTENT_IN_NEW_SHELL | legacy overlay | REAL clientes | Operação · Clientes | reskin | Normalize hero/chrome |
| `/funcionarios` | `funcionarios.html` | LEGACY_CONTENT_IN_NEW_SHELL | legacy overlay | REAL | Operação · Funcionários | reskin | Normalize |
| `/perfil_funcionario` | `perfil_funcionario.html` | LEGACY_CONTENT_IN_NEW_SHELL | legacy overlay | REAL | Operação · Perfil | reskin | Normalize |
| `/upload` | `upload.html` | LEGACY_CONTENT_IN_NEW_SHELL | legacy overlay | REAL upload | Operação · Uploads | reskin | Brand scrub title |
| `/upload_inteligente` | `upload_inteligente.html` | LEGACY_CONTENT_IN_NEW_SHELL | legacy overlay | REAL | Operação · Upload inteligente | reskin | Normalize |
| `/produtividade` | `produtividade.html` | LEGACY_CONTENT_IN_NEW_SHELL | legacy overlay | REAL | Analytics · Produtividade | reskin | Normalize |
| `/comparativos` | `comparativos.html` | LEGACY_CONTENT_IN_NEW_SHELL | legacy overlay | REAL | Analytics · Comparativos | reskin | Normalize |
| `/dados_powerbi` | `dados_powerbi.html` | LEGACY_CONTENT_IN_NEW_SHELL | legacy overlay | REAL | Analytics · Power BI | reskin | Normalize |
| `/dashboard_powerbi` | `dashboard_powerbi.html` | LEGACY_CONTENT_IN_NEW_SHELL | legacy overlay | REAL | Analytics · Dashboard Power BI | reskin | Keep filter side panels |
| `/apresentacao` | `apresentacao.html` | LEGACY_CONTENT_IN_NEW_SHELL | legacy overlay | REAL | Apresentações | encapsulated reskin | Restyle chrome; keep deck |
| `/configuracoes` | `configuracoes.html` | LEGACY_CONTENT_IN_NEW_SHELL | legacy overlay | REAL | Configurações | reskin | Normalize |
| `/tendencias` | redirect | REDIRECT | — | — | → dashboard evolução | REDIRECT | Keep |
| `/executive/presentation` | gated | FLAGGED_OFF | — | — | Presentation Premium | FLAGGED_OFF | Do not activate |
| `/preview/*`, `/f/*` | preview/* | PREVIEW_ONLY | — | synthetic | homologation | PREVIEW_ONLY | Stay blocked in prod |
| `analises.html` (file) | `analises.html` | STUB / ORPHAN | — | none | stub file | ORPHAN | Out of nav; route uses analytics.html |
| `tendencias.html` (file) | `tendencias.html` | STUB / ORPHAN | — | none | stub file | ORPHAN | Route redirects |
| `inss.html` | `inss.html` | ORPHAN | — | — | unused | ORPHAN | Out of nav |
| `download_app.html` | `download_app.html` | ORPHAN / FULL_LEGACY | — | — | unused | ORPHAN | Out of nav |
| `baixar_icone.html` | `baixar_icone.html` | ORPHAN | — | — | unused | ORPHAN | Out of nav |
| `landing-legacy.html` | `landing-legacy.html` | FULL_LEGACY | — | — | archive | FULL_LEGACY | Not served as `/landing` |

## Menu (v2.1 single nav)

Início · Executive · Analytics (+ Visão Geral, Comparativos, Power BI, Produtividade, Setores, CID, Tendências) · Operação (+ Clientes, Funcionários, Uploads, Upload inteligente) · Apresentações · Fichas (disabled) · Configurações

No menu items point to stubs.
