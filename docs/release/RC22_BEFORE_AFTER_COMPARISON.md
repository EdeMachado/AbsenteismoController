# RC22 BEFORE / AFTER Comparison

## Problem (BEFORE — production Frankenstein)

| Surface | Before symptom |
|---------|----------------|
| `/dashboard` | Legacy admin chrome + own sidebar feel inside new menu |
| `/clientes` | Indigo/green hero, GrupoBioMed copy, admin look |
| `/apresentacao` | Full-bleed indigo `#1a237e` body — felt like another product |
| `/upload` | Title "Absenteísmo Controller" |
| Landing | "BioMed Absenteísmo Controller" product naming mix |
| Menu | Risk of stubs / parallel chrome via auth.js sidebar |

## AFTER (this RC)

| Surface | After state | Evidence |
|---------|-------------|----------|
| All active app routes | Single BioMed Platform shell (nav/header/crumb/footer) | `06-analytics-overview`, `10-clientes`, `14-apresentacao`, `04-executive` |
| `/dashboard` | Labeled **Analytics · Visão Geral**; legacy sidebar hidden | `06-analytics-overview.png` |
| `/clientes` | Teal BioMed hero; GrupoBioMed scrubbed | `10-clientes.png` |
| `/apresentacao` | Deck encapsulated in shell; BioMed header | `14-apresentacao.png` |
| Landing / Login | BioMed Platform | `01-landing.png`, `02-login.png` |
| Executive | Same shell + in-module steps only | `04-executive.png` |

Artifacts: `/opt/cursor/artifacts/rc22-screenshots/` and `AFTER_BOARD.png`.
