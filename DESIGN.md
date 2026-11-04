# ExportPulse AI — Design Direction

## Current: Trade intelligence application (v5)
This is the "Trade Control Tower" from `DESIGN-RESEARCH.md`, built on the light chart map instead of a dark one.

- **Shell:** dark navy (`#0F1D2B`) app frame with a 56px toolbar: brand, search (importer / HS / city / port), sector picker, and three KPIs (agent fees per year, US demand, containers over 12 months). Seller tools are icons, and a demo-only WhatsApp button sits at the end.
- **Workspace:** the light chart map fills the frame, with the same cartography and magenta lanes. Camera (fit-to-route, zoom buttons, wheel zoom, drag to pan) is about 60 lines of our own code. Markers and labels sit in a screen-space overlay so they stay crisp at any zoom.
- **Left panel:** who the page is prepared for, filter chips (All / Arrived ≤ 30 days / Match 85+, each with counts), and the ranked importer list. Hovering a row previews its lane.
- **Right panel:** opens when a marker or row is selected. Four tabs:
  - **Overview:** facts, product, contact, buying signal.
  - **Offer:** quote, slider, savings.
  - **Outreach:** sequence and copy.
  - **Route:** indicative passage and landed cost.
- **Honesty rules:**
  - No moving ships, pulses or "live" wording.
  - Dates read "last recorded arrival".
  - The legend says "US Customs records · last 12 months", and lanes are "indicative".
- **Type:** Archivo throughout, with Spline Sans Mono for codes and coordinates. No serif.
- **Dependencies:** unchanged (d3-array, d3-geo, topojson-client, world-atlas from jsDelivr).

## Current: map-first intelligence dashboard (v4)
Feedback on v3 was that the Chartroom felt too much like a newspaper, with too many text-heavy sections, but the world map was its strongest part. v4 keeps the map's chart styling and drops the editorial layer:

- **Layout:**
  1. A sticky header with the sector switch built in.
  2. A KPI row: identity tile, then the hero metric (agent commission, in magenta), US demand, containers, latest arrival.
  3. The map with a ranked importer rail beside it. Rail badges match the map's numbered markers, and hovering a row previews that lane on the map.
  4. One deal room for the selected importer: route & landed cost, offer, outreach.
  5. A compact WhatsApp call-to-action strip.
- **Kept from Chartroom:** sea/buff/magenta map palette, graduated border, moving ships, Bodoni italic, which is now used only for the factory's name.
- **Dropped:** long paragraphs, the editorial manifest, the large serif headlines, 12-month timelines, and passage lists (replaced by route pills).
- **Surfaces:** white cards (16px radius, soft shadow) on `#F1F4F5`. Status colours: green for buyer savings and fresh arrivals, amber for "why now" and medium match, magenta for the factory's own money and selection.

The Chartroom write-up below is kept for reference.

## The problem with v2
The navy hero, orange accent, metric badges and rounded cards could belong to any SaaS product. Nothing in the visual language came from the subject: Indian goods crossing oceans to US warehouses, proven by customs paperwork.

## Three directions explored

### A. The Chartroom *(chosen)*
The page is a navigation chart, issued for one factory.
- **Identity:** the visual language of Admiralty/NOAA charts. Pale sea, buff land, ink linework, and magenta for routes (charts reserve magenta for traffic routes and critical information). A graduated neatline border carries real latitude/longitude ticks.
- **Type:** Bodoni Moda italic, used only for the prospect's name and water names (charts set hydrography in italic serif). Archivo with its width axis: expanded caps for chart labels, normal width for reading. Spline Sans Mono for coordinates, HS codes and figures.
- **Hero:** an editorial title block ("Prepared exclusively for *Shree Brass Works*", with the city's real coordinates), then a full-bleed Mercator chart. It shows the factory's city, its export port and indicative sea lanes via Suez/Panama to each importer's US port and HQ. Small hulls sail the lanes. Importers are numbered markers sized by containers.
- **Content:** the importer list becomes a cargo *manifest*: editorial ledger entries, not cards. Last arrival sits on a 12-month timeline. Selecting an entry unfolds a *dossier* in place with three parts: passage, offer and outreach.
- **Motion:** lanes draw out from the factory, markers settle, and ships move slowly. Manifest entries reveal as they scroll in. Figures count between values. All of it is disabled under reduced motion.
- **Why it fits:** the product's value is geographic and documentary, so the visual *is* the argument. A factory owner sees his own city connected to named US buyers within seconds.

### B. Night Port (cinematic)
A dark WebGL globe with glowing arcs, a 3D container yard, and the buyer list as a split-flap departures board.
- **Rejected:** dark globes with glowing arcs are now the most generic "AI SaaS hero". Great-circle arcs from India to the US cross the Arctic, which misrepresents shipping. The look is heavy on ordinary laptops and blurs badly in compressed WhatsApp video.

### C. Bill of Lading (documentary)
The page as an official customs document: form fields, typewriter mono, rubber stamps ("MATCHED 94"), carbon-copy blue.
- **Rejected as the lead direction:** it's authentic and builds trust, but it feels bureaucratic rather than aspirational, and it can't show the *relationships* between factory and buyers. Its documentary details (coordinates, HS codes, issue date) are folded into A.

## Design system — Chartroom

| Token | Value | Use |
|---|---|---|
| `--paper` | `#F6F7F3` | page (chart paper) |
| `--sea` / `--shoal` | `#E2ECEC` / `#CFE0E3` | water / coastal shallow band |
| `--land` / `--land-home` | `#EDE4CB` / `#E4D29F` | land / India and the US |
| `--ink` / `--ink-2` | `#14232C` / `#3E4F58` | text, linework |
| `--sound` | `#6F8189` | secondary text (chart "soundings" grey) |
| `--mag` | `#B0235B` | routes, selection, primary action |
| `--green` | `#2E7A4B` | buyer savings (positive money only) |
| `--night` | `#0F1D26` | the closing "night chart" section |

- **Type scale:** display 116/72/56 (Bodoni italic), title 28/22 (Archivo 600), body 15, labels 11 (Archivo 125% width, +0.16em tracking, caps), data 12 (mono).
- **Surfaces:** no rounded cards. Sections are separated by full-bleed changes of surface (paper → sea chart → paper → night) and 1px rules. The only object with a shadow is the outreach letter, because it is a physical object.
- **Iconography:** chart glyphs only: hull, port square, origin ring, and numbered importer marker.
- **Motion language:** "charting": things draw outward from the origin, slowly and once. There are no floating blobs, glows or parallax.
