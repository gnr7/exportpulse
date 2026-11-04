# Meridian integration sequence

Branch `meridian-integration`, cut from a baseline commit of the current working folder on `main`. Each stage is one commit; rollback for any stage is `git revert <stage commit>` (or `git checkout main` to drop the whole branch). Nothing is merged, pushed or deployed.

## What the inspection found (before any change)

- Registered routes: `GET /` (dashboard, `?factory=&city=&category=`), `GET /api/buyers`, `POST /api/buyers/add`, `POST /api/buyers/import-csv`, `GET /api/export-csv`, `GET /api/cost-calc/{buyer_id}`, `POST /api/outreach`, plus FastAPI's `/docs`, `/docs/oauth2-redirect`, `/redoc`, `/openapi.json`. Nothing under `/static` or `/site`.
- Demo entry points: `/?factory=…&city=…&category=handicrafts|agro_marine|textiles|leather`. An unknown category falls back to `handicrafts` (so `category=agro` shows handicrafts — existing behaviour, unchanged).
- Deploy: `Procfile` and `render.yaml` start `uvicorn export_buyer_engine:app`; health check `GET /api/buyers`. Neither needs to change.
- FastAPI 0.136 / Starlette 1.0: `StaticFiles` works without extra packages, so `requirements.txt` is unchanged.
- Storage is in memory (`BUYERS_DB`), seeded from the demo set or `client_buyers.csv`. There is no database and nothing to migrate.

## Stages

| # | Files | Purpose | Risk | Verification |
|---|---|---|---|---|
| 0 | `.gitignore` | Baseline commit on `main`, then the branch | None (local repo only) | `git status` clean |
| 1 | `static/photos/*.jpg`, `static/js/photos.js`, `PHOTO-LICENSES.md` | 11 approved photos served locally, with licence records | Low: new files only; nothing references them yet | Files open; sizes sane; every licence row filled |
| 2 | `static/css/meridian.css`, `static/js/geo.js`, `site/index.html`, `site/sector.html`, `export_buyer_engine.py` (2 mount lines + 1 import) | Marketing pages at `/site/`, assets at `/static/`, data from the live API | Medium: first change to the engine file; new paths only | Route table before/after (only additions), smoke test, API responses identical, pages render with no console errors, no request to Unsplash |
| 3 | `export_buyer_engine.py` (inside `DASHBOARD_HTML` only) | Meridian identity in Control Tower, overflow fix, corrected lanes, marker and label improvements, estimate wording, `?pick=` / `?q=` start links used by the sector pages | Medium: changes the live page | Python outside the template byte-identical (AST check), smoke test, demo links, API diff, no sideways scroll, screenshots at 1440 / 768 / 375 |
| 4 | `DESIGN.md`, `progress.md`, `PRODUCTION-CHECKLIST.md` | Record what shipped and what is still open | None | Read-through |

## Guardrails

- Backend calculations are not touched. Pages show values returned by `/api/cost-calc` and `/api/buyers`; the only arithmetic in page code is summing API values and display formatting.
- `prototypes/` stays in the repo as the approved reference. It is not served, and no file under `site/` or `static/` loads `data.js` or `calc.js`.
- The `/site` marketing pages are mounted only in demo mode (no client CSV), because their copy describes the demo dataset. Client portals keep exactly their current routes, plus `/static` for the Control Tower's photos and styles.
