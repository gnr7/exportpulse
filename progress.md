# ExportPulse AI — Build Progress

## Overview
Single-file FastAPI micro-application (`export_buyer_engine.py`) that turns US Customs bill-of-lading data (ImportYeti) into a white-label buyer-intelligence portal for Indian export manufacturers.

## Build Plan (Section by Section)

| # | Section | Status |
|---|---------|--------|
| 1 | Foundation — Imports, FastAPI app, Pydantic models, seed data (4 sectors × 5 buyers) | ✅ Completed |
| 2 | Backend Logic — Cost calculator, outreach generator (Gemini + templates), API endpoints | ✅ Completed |
| 3 | Frontend Dashboard — Google-flat UI, white-label banner, table, calculator, outreach tabs, modals | ✅ Completed |
| 4 | Server Startup & Testing — 4 demo URLs return 200, API smoke test passes | ✅ Completed (2026-11-04) |
| 5 | Client delivery — requirements.txt, render.yaml, Procfile | ✅ Completed (2026-11-04) |

## 2026-11-04 fixes (handoff audit)
- **Startup failure cause:** the previous agent's `uvicorn --reload` was still holding port 8000. Stopped it; all dependencies were already installed.
- `POST /api/buyers/import-csv` reads the raw request body (text/csv or JSON `{"csv": ...}`), so it no longer needs python-multipart. Multipart uploads still work when python-multipart is installed.
- Record fields renamed to match the spec: `us_buyer`, `est_annual_usd`. Old CSV headers (`company_name`, `est_annual_volume_usd`) are still accepted.
- Seed buyers now have stable IDs (`hc-01` … `lt-05`).
- Commission saved = `est_annual_usd × 5% × ₹95` (previously used FOB × 10k units).
- `?factory=` / `?city=` are escaped, so names containing apostrophes or `<` can't break the page. An unknown `?category=` falls back to handicrafts.
- Factory/City inputs are pre-filled from the URL. Editing them updates the banner, the outreach copy and the shareable URL live.
- The FOB input recalculates as you type. The top-scoring buyer is auto-selected on load, so the demo opens fully populated.
- Outreach templates now include the last arrival date, the landed-cost savings % and a side-by-side spec sheet. The LinkedIn/WhatsApp note is exactly 3 sentences. Gemini uses the header API key and JSON mode, and runs off the event loop.
- `/api/export-csv` and `/api/buyers` accept `?category=` (`?sector=` alias). The exported CSV re-imports cleanly.
- Client deployments: if `client_buyers.csv` (or the `BUYERS_CSV` env var) exists, it replaces the demo seed at startup. `DEFAULT_FACTORY` / `DEFAULT_CITY` / `DEFAULT_CATEGORY` brand the root URL.

## 2026-11-04 premium redesign
- The dark hero leads with the prospect's name in a headline, then one big ₹ figure (agent commission on this trade, in crore/lakh), then a trade-lane map from their city to each US importer (line thickness = containers; click a lane to open that buyer).
- Buyer list shows recency ("17 days ago"), volume bars, match rings and a "why now" line.
- Deal desk: price slider marked with the competitor's FOB, landed-cost bars, savings tiles.
- Seller-only tools (add buyer, CSV import/export, edit factory name) live in the "Manage data" and "Edit details" buttons, out of the prospect's way.
- Demo pages (no `client_buyers.csv`) end with a "Get the full list on WhatsApp" band. Set `SELLER_WHATSAPP=91XXXXXXXXXX` before starting the server so the button opens a chat with you. Without it, WhatsApp asks the prospect to choose a contact.

## 2026-11-04 Chartroom identity (supersedes the dark-hero redesign)
- Full direction and design system are in `DESIGN.md`.
- The page is a navigation chart issued for one factory. It has an editorial title block, then a real Mercator chart (d3-geo + world-atlas from jsDelivr): the factory's city → export port → indicative sea lane via Suez/Panama → US port → importer HQ, with a graduated neatline border and moving ships.
- The importer list is now a "manifest" with a 12-month arrival timeline. Selecting an entry unfolds a dossier with passage, offer and outreach.
- City coordinates come from built-in tables (Indian export hubs, seed US cities, US state centroids as fallback). If the chart scripts can't load (offline), the chart shows a note and everything else still works.

## 2026-11-04 Map-first dashboard (supersedes Chartroom layout)
- Feedback: the Chartroom felt too newspaper-like and text-heavy, but the world map was its strongest part.
- New layout: KPI row → map with importer rail (hover a row to preview its lane) → deal room (route & landed cost, offer, outreach) → compact WhatsApp strip. See `DESIGN.md`.

## 2026-11-04 Trade intelligence application (current UI)
- The page is now an application: dark navy shell, light chart map as the workspace, a left importer panel with search and filters, and a right detail panel with Overview / Offer / Outreach / Route tabs.
- Removed moving ships and other live-looking animation, because the data is historical customs records.
- Camera zoom and pan are our own code; no new dependencies. See `DESIGN.md` (v5).

## 2026-11-04 Meridian high-fidelity prototypes (awaiting approval)
- Prototypes live in `prototypes/`, served separately (`python -m http.server 8020 --directory prototypes`, then open `/index.html`). The live app, its routes and its backend are untouched.
- Pages: `home.html` (hero, sea-to-chart route story, sector bento, live product showcase, offer builder, data source, CTA), `sector.html?s=…` (all four sectors), `app.html` (Control Tower with the Meridian identity, generated by `build_app.py` from `designs/control-tower/page-template.html`).
- Data: `assets/data.js` is a snapshot of the live API (the demo seed dataset, labelled illustrative everywhere). `assets/calc.js` is a JS copy of `calculate_cost` and `_build_templates`, verified identical to the Python on 60 cost calculations and 20 outreach sequences.
- Photography: 12 free Unsplash photos, hotlinked, credited in `assets/photos.js` and on the hub page.

## 2026-11-04 Meridian QA pass (prototypes only, awaiting approval)
- Empty band under the route story: the story's height was in `vh`, so a full-page capture (a very tall viewport) made it 21,840px of sea. Heights are now capped at 1000px with a fixed 2,400px scroll distance, and viewports over 1300px tall (or reduced motion) get the final frame as a static figure.
- Route story: the photo washes out to the sea tint, the chart camera pulls back from the Arabian Sea to the whole passage, then the route draws stop by stop. Five marker glyphs (factory, export port, canal, US port of entry, importer HQ) are shared by the pins, the progress rail, the hero route card, the sector map and the app.
- Geography: every lane was sampled against the 110m world map. Waypoints were moved off land at Sri Lanka, Sicily, Tunisia, the Alboran Sea, the Bahamas, Puerto Rico, Panama's Azuero peninsula and Costa Rica, and the US ports were moved to their container terminals. The only remaining land hits are in the Gulf of Suez, which the 110m map draws as land. These corrections are in `assets/geo.js` and in `app.html` through `build_app.py`; **the live app still has the old waypoints**.
- ₹3.17 Cr is labelled as an estimate everywhere, with the working on the homepage (`#fees`): est. annual US imports × 5% assumed agent rate × ₹95/$.
- Hub photo credits: a duplicate `id="credits"` wiped the section; now a grid of cards.
- Live app unchanged (engine SHA-256 matches `designs/control-tower`), smoke tests pass, prototype maths still identical to the API (60/60, 20/20).
- Responsive fixes: tablet story layout (route on top, caption and record card below), phone sector page no longer widens to 421px (grid column `minmax(0,1fr)`), phone hero scrim, phone fee tiles.
- Found in the live app (not fixed, by instruction): when no importer is selected, the closed detail panel sits off-screen and the page scrolls sideways ~370px at 1440 wide. The prototype clips it with `html,body{overflow-x:clip}` (in `build_app.py`).
- Refinement pass: the prototype notice is now a strip at the top of the fixed header (pages offset by `--proto-h`), importer markers keep clear of each other and of port glyphs with leader lines, map labels move or hide instead of sitting under markers, the phone sector switch is a 2 × 2 grid, Route-tab stops use the five marker glyphs. Integration plan: `PRODUCTION-CHECKLIST.md`.
- Screenshots: `qa-screenshots/` (d- desktop 1440, t- tablet 768, m- phone 375; `d-home-complete` is the whole homepage), 39 captures with headless Chrome: no sideways scroll, no widened layout, no script errors.

## 2026-11-04 Meridian production integration (branch `meridian-integration`, not merged)
- Local git repo created; `main` = baseline snapshot, work in four commits on `meridian-integration`. See `INTEGRATION-PLAN.md`.
- New: `/site/` marketing pages (demo deployments only) and `/static/` assets (styles, corrected sea lanes, 11 self-hosted photos with `PHOTO-LICENSES.md`). Pages read `/api/buyers` and `/api/cost-calc`; no copied calculation code.
- Control Tower: Meridian styling, horizontal-overflow fix, corrected lanes, marker and label improvements, estimate wording, `?q=` / `?pick=` start links. Python outside the page template unchanged apart from the two mounts.
- Checks: 136 API responses identical before/after, smoke test passes, demo links 200, client-mode run serves no `/site`.

## Deploying a paid client (Render)
1. Load their buyers in the local dashboard, then click **Export CSV** and save it as `client_buyers.csv`.
2. Push the folder to a new GitHub repo, then go to Render → New → Blueprint and pick the repo (`render.yaml`).
3. Set `DEFAULT_FACTORY`, `DEFAULT_CITY` and `DEFAULT_CATEGORY` for the client.
4. Note: the free plan sleeps when idle and data is in-memory. Buyers added in the UI after deploy are lost on restart unless they're added to `client_buyers.csv` and redeployed.

## Tech Stack
- **Runtime:** Python 3.10+ (tested on 3.14; Render pinned to 3.12.7)
- **Dependencies:** fastapi, uvicorn, pydantic v2, python-multipart (optional)
- **Optional:** GEMINI_API_KEY env var for live LLM outreach generation
- **Design:** Google-flat, Inter typography, white/slate-50 surfaces, 1px #e2e8f0 borders, no gradients or drop shadows

## Sector Datasets
1. **handicrafts** — 5 US importers (wood, stone, brass, ceramic, basketware)
2. **agro_marine** — 5 US importers (spices, shrimp, cashews, pepper, seafood)
3. **textiles** — 5 US importers (bed linen, rugs, towels, curtains, dhurries)
4. **leather** — 5 US importers (handbags, accessories, dress shoes, sneakers, totes)
