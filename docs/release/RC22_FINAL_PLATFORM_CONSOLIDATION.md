# RC22 — Final Platform Consolidation

**Result target:** one BioMed Platform experience from login to logout.  
**Non-goals:** no new features, no DB/API/business-rule changes, Presentation Premium OFF, Ficha OFF, Ingestion/Performance OFF.

## What changed

1. **Inventory** — `docs/release/RC22_ROUTE_INVENTORY.md`
2. **Shell** — cache `rc22`; single nav unchanged in structure; Analytics children use real routes/anchors only
3. **Content isolation CSS** — `biomed-platform.css` RC-22 layer:
   - hides legacy sidebars / user widgets / duplicate chrome
   - preserves Power BI filter panels (`.sidebar-left` / `.sidebar-right`)
   - normalizes headers, cards, buttons, inputs, tables under `body.bm-plat-legacy`
   - reskins Clientes hero away from indigo/green legacy look
   - encapsulates `/apresentacao` deck inside platform shell (no full-bleed indigo body)
4. **Brand** — landing/login/hub/ops public strings → BioMed Platform; scrub GrupoBioMed / Absenteísmo Controller on active surfaces
5. **Surface labels** — dashboard title → Analytics · Visão Geral; ops/analytics page titles aligned
6. **Tests** — `tests/release/test_rc22_final_platform_consolidation.py`

## Explicitly unchanged

- Database schema / migrations
- API contracts
- Business rules / calculations
- Feature flags (Presentation Premium, Preview/Ficha, Ingestion, Performance)
- Presentation Premium route remains OFF
- Legacy files kept on disk (stubs/orphans) but out of menu

## GO criteria (checklist)

| Question | Expected |
|----------|----------|
| Active v2.1 screen looks like old product? | NÃO |
| Duplicate menu? | NÃO |
| Relevant old branding? | NÃO |
| Menu → stub? | NÃO |
| Functionality lost? | NÃO |
