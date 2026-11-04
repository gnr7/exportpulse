# Meridian — production integration checklist

Status: **prepared, not started.** Nothing in this file has been merged, deployed or run against production. The live app (`export_buyer_engine.py`) still matches the saved Control Tower snapshot (SHA-256 `A75E3D04…72FC55`).

Ground rules for the integration:

- The backend stays the source of truth. Every number on every page comes from the API; the prototype's JavaScript copies (`prototypes/assets/calc.js`, `prototypes/assets/data.js`) are never shipped.
- `/` and every `/api/*` route keep their current paths, parameters and responses, so existing demo links and client deployments keep working.
- Python code outside the `DASHBOARD_HTML` string is not edited.

## Decisions needed before starting

1. **Where the marketing pages live.** Recommended: same FastAPI app, new prefix (`/site/`, `/site/sector?s=…`) through one static-files mount, so pages call `/api/*` on the same origin (no CORS change). Alternative: a separate static host, which needs a CORS middleware change in the backend.
2. **Fonts.** Archivo and Spline Sans Mono load from Google Fonts today (live app and prototypes). Keep that, or self-host the OFL font files under `static/fonts/`.
3. **The prototype notice strip.** Production drops it and sets `--proto-h: 0`. Real client datasets should still carry their source labels ("US Customs record").

## Exact files

### Changed

| File | What changes | Where |
|---|---|---|
| `export_buyer_engine.py` | Template only (inside `DASHBOARD_HTML`, lines 878–2271): overflow fix, corrected coordinates, marker / label / legend changes, estimate wording, Meridian styling | listed per item below |
| `export_buyer_engine.py` | Only if decision 1 = same app: one `app.mount("/site", StaticFiles(directory="static/site", html=True))` line and its import | after the route definitions |
| `render.yaml` | Only if a static mount or self-hosted fonts need build/publish settings; otherwise unchanged | — |
| `DESIGN.md`, `progress.md` | Record Meridian as the shipped design | — |

### Added

| File | Source |
|---|---|
| `static/site/index.html` | `prototypes/home.html`, with `EP_DATA` / `EPCalc` replaced by `fetch('/api/buyers?category=…')` and `fetch('/api/cost-calc/{id}?your_fob_usd=…')` |
| `static/site/sector.html` | `prototypes/sector.html`, same data swap |
| `static/assets/meridian.css` | `prototypes/assets/meridian.css` (notice strip removed, `--proto-h: 0`) |
| `static/assets/geo.js` | `prototypes/assets/geo.js` (the corrected lanes) |
| `static/assets/photos.js` | `prototypes/assets/photos.js`, `photoUrl()` pointing at local files |
| `static/photos/*.jpg` | 12 downloaded photographs, each at 2–3 widths (800 / 1600 / 2400) |
| `PHOTO-LICENSES.md` | Licence record per photograph (see section 3) |

### Not shipped

`prototypes/assets/data.js`, `prototypes/assets/calc.js`, `prototypes/build_app.py`, `prototypes/app.html`, `prototypes/index.html`, `qa-screenshots/`. Keep `prototypes/` in the repo as the approved reference, or delete it after sign-off.

## 1. Live-app horizontal overflow fix

Found in QA: when no importer is selected, the closed detail panel (`.detail`, `transform: translateX(100% + 24px)`, engine line 978) sits off-screen and the page scrolls sideways about 370 px at 1440 wide.

- [ ] Add `html,body{overflow-x:clip}` to the template's `<style>` (before the `@media (prefers-reduced-motion…)` block, engine line 1170).
- [ ] Check: at 1440×900 with `?q=zzz` (no results), `scrollTo(400,0)` leaves `scrollX` at 0.
- [ ] Check: the detail panel still slides in and out, and the phone layout (below 980 px) still scrolls vertically.

## 2. Corrected geographical coordinates

The same values are already in `prototypes/assets/geo.js` and applied to the prototype app by `prototypes/build_app.py` (section "2b").

- [ ] Engine lines 1573–1574 (`IN_PORTS.vizag`, `IN_PORTS.haldia`): insert `[6.3,82.2]` before `[5.6,80.6]` (south of Sri Lanka).
- [ ] Engine line 1577 (`SUEZ`): replace with
  `[[12.6,43.4],[20.0,38.6],[27.6,33.9],[29.0,32.85],[29.95,32.56],[31.4,32.35],[33.8,26.0],[36.3,15.2],[37.4,11.3],[37.75,9.5],[37.3,1.0],[36.3,-2.2],[35.95,-5.6]]`
  (Malta channel, Sicily channel, north of Tunisia and Algeria, Alboran Sea).
- [ ] Engine lines 1579–1582 (`US_PORTS`):
  - `nyc`: `ll:[40.67,-74.08]`, sea adds `[40.42,-73.85]` (Ambrose approach)
  - `sav`: `ll:[32.08,-81.09]`, sea adds `[32.03,-80.85]` (Savannah River mouth)
  - `hou`: `ll:[29.68,-95.00]`, sea `[[29,-40],[26.2,-76.6],[25.85,-77.0],[26.1,-78.3],[25.9,-79.3],[24.3,-81.5],[25.5,-87],[28.6,-93.5],[29.35,-94.72]]` (Providence channels, Galveston entrance)
  - `lax`: sea `[[22,-40],[18.45,-63.9],[12.5,-76.0],[9.38,-79.92],[8.93,-79.56],[7.0,-79.6],[6.6,-81.0],[9.8,-88.5],[14.5,-98],[22.5,-110.8],[30.0,-117.5]]` (Anegada Passage, Gulf of Panama, off Costa Rica)
- [ ] Re-run the land audit (scratch script from the QA pass) against the live page: the only expected land hits are the Gulf of Suez, Gibraltar and the canal transits, which the 110 m world map draws as land.
- [ ] Look at all four sector routes on the map at 1440 and 375.

## 3. Photographs: self-hosting and licence records

All 12 are free photos under the Unsplash License, checked on each photo page on 4 Nov 2026 (none are Unsplash+). They are currently hotlinked from `images.unsplash.com`.

- [ ] Re-check each photo page on the day of download (licence and "Free" status can change).
- [ ] Download each file from its Unsplash page, export to 800 / 1600 / 2400 px wide JPEG (and optionally WebP), save under `static/photos/<key>-<width>.jpg`.
- [ ] Write `PHOTO-LICENSES.md` with one row per photo: key, photographer, Unsplash page URL, photo ID, licence ("Unsplash License"), date checked, date downloaded, where it is used.

| Key | Photographer | Unsplash page | Used on |
|---|---|---|---|
| hero | Haydn | https://unsplash.com/photos/ZT3i-6XW8J8 | Homepage hero |
| heroAlt | Venti Views | https://unsplash.com/photos/FPKnAO-CF6M | Spare (not shown) |
| sea | Bent Van Aeken | https://unsplash.com/photos/0A7YwYhZhWw | Route story opening frame |
| yard | CHUTTERSNAP | https://unsplash.com/photos/9cCeS9Sg6nU | Product section background |
| port | CHUTTERSNAP | https://unsplash.com/photos/kyCNGGKCvyw | Leather sector photo band |
| night | Sondre Millstein | https://unsplash.com/photos/cdm1L4MzCWQ | Call to action |
| brass | Thilina Alagiyawanna | https://unsplash.com/photos/JW6LKDYboeg | Handicrafts sector, app header |
| spices | Jameson Berrios | https://unsplash.com/photos/tfbzEN-GjW4 | Agro & marine sector |
| cardamom | Neil P-A | https://unsplash.com/photos/dZIs-KaRdu8 | Agro & marine detail band |
| loom | Akhil Pawar | https://unsplash.com/photos/XCd_6nOdzjo | Textiles sector |
| threads | Esha Verma | https://unsplash.com/photos/LeYd0uXln3I | Textiles detail band |
| leather | Irene Kredenets | https://unsplash.com/photos/tcVH_BwHtrc | Leather sector |

- [ ] Change `photoUrl()` in `static/assets/photos.js` to return `/site/photos/<key>-<width>.jpg`; keep the on-page credits ("Photo: name / Unsplash", linked to the photo page).
- [ ] Unsplash photos of identifiable people (the weaver, `loom`) — confirm the use stays editorial and does not imply endorsement.
- [ ] Check: no request goes to `images.unsplash.com` (browser network panel).

## 4. Backend calculations stay the source of truth

- [ ] Marketing pages read importers from `GET /api/buyers?category=…` and costs from `GET /api/cost-calc/{id}?your_fob_usd=…`; the offer builder debounces slider calls (≈150 ms).
- [ ] The ₹ headline is computed from API data: Σ `est_annual_usd` × 5% × 95, matching `AGENT_COMMISSION_PCT` and `USD_TO_INR` (engine lines 55–57). Better: read both constants from an API field rather than hard-coding them in page JS.
- [ ] Estimate wording ships with it: KPI label (engine line 1196) "est. agent commission / yr" with the explanatory tooltip; offer tab (engine line 1308) "Agent commission avoided (est.)"; the `#fees` working on the homepage.
- [ ] No `calc.js`, no `data.js`, no copied rounding code in `static/`.
- [ ] Check: `node verify_cost.js` / `verify_calc.js` style comparison of page-displayed values against the API for all 20 seed importers.

## 5. Routes, demo links and application functionality

Current routes (unchanged by this plan):

| Method | Path | Notes |
|---|---|---|
| GET | `/` | Dashboard; `?factory=&city=&category=` white-label banner |
| GET | `/api/buyers` | `?category=` / `?sector=` |
| POST | `/api/buyers/add` | JSON body |
| POST | `/api/buyers/import-csv` | text/csv, JSON, or multipart |
| GET | `/api/export-csv` | `?category=` |
| GET | `/api/cost-calc/{buyer_id}` | `?your_fob_usd=` |
| POST | `/api/outreach` | Gemini when `GEMINI_API_KEY` is set, template otherwise |
| GET | `/docs`, `/openapi.json` | FastAPI defaults |

- [ ] The four demo URLs return 200 and show the banner: `/?factory=Shree%20Brass%20Works&city=Moradabad&category=handicrafts`, `…Kerala%20Spice%20Co&city=Kochi&category=agro`, `…Panipat%20Weaves&city=Panipat&category=textiles`, `…Kanpur%20Leather&city=Kanpur&category=leather`.
- [ ] Env vars behave as before: `GEMINI_API_KEY`, `BUYERS_CSV`, `DEFAULT_FACTORY`, `DEFAULT_CITY`, `DEFAULT_CATEGORY`, `SELLER_WHATSAPP`; DEMO mode when no client CSV.
- [ ] Add, CSV import (all three body types), CSV export, WhatsApp button, outreach (template and Gemini), FOB slider, filters, search, marker selection and all four tabs work in the live app.
- [ ] Marker and label changes from `build_app.py` sections "2c" and "2e" are ported into the template: canal markers, filled US-port squares, glyph legend, marker separation from port glyphs, label collision handling, Route-tab stop glyphs.
- [ ] `diff` of the engine file before/after shows changes only inside `DASHBOARD_HTML` (plus the optional mount line).
- [ ] `requirements.txt` unchanged (Starlette's `StaticFiles` ships with FastAPI; confirm no `aiofiles` import is needed on the pinned version).

## 6. Final responsive and regression tests

- [ ] `scratchpad/smoke.py` equivalent passes against a local server (`ALL CHECKS PASSED`), then restart the server (the smoke test adds importers to the in-memory store).
- [ ] Screenshot set at 1440×900, 768×1024 and 375×812 for `/`, `/site/`, every sector, and the app with an importer selected on each tab: no sideways scroll, no layout wider than the viewport, no console errors.
- [ ] Full-page capture of `/site/` at 1440 wide runs from hero to footer with no empty band (the route story renders its static final frame on very tall viewports).
- [ ] Reduced-motion: the route story shows the final frame; no animation runs.
- [ ] Keyboard: markers reachable with Tab, Enter selects; focus is visible on all buttons and tabs.
- [ ] Real devices: iPhone Safari and an Android Chrome phone (the QA pass only used Chrome device emulation).
- [ ] Map fallback: block `cdn.jsdelivr.net` and confirm the list still works with the "map could not load" message.
- [ ] Render deploy to a preview service first; production only after sign-off.
