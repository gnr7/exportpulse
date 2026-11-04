# Logistics & Trade-Intelligence UI Research

*Frontend design research only (no business or product research). Compiled 4 Nov 2026.*

## 1. What I looked at

| Platform | What I could see | Source |
|---|---|---|
| **MarineTraffic** (Kpler) | The live app: full-screen map, left icon rail, right tool column, floating search pill | [marinetraffic.com live map](https://www.marinetraffic.com/en/ais/home/centerx:20/centery:25/zoom:3), [Kpler help: Live Map toolbar](https://help.kpler.com/en/articles/9552654) |
| **Flexport** | App frame on the product page: dark top nav with "Search or ask", KPI modules, map with mode rail | [flexport.com platform](https://www.flexport.com/products/flexport-platform/), [Flexport UX: Dashboard 2.0](https://medium.com/flexport-ux/the-flexport-dashboard-2-0-2524f8e92245), [help: dashboard map + exceptions](https://www.flexport.com/help/new-updates-to-the-flexport-platform-september-2019/) |
| **project44** | Marketing canvas (black, monochrome landmass map, bright blue); Movement app described, not public | [project44.com](https://www.project44.com/), [What's new in Movement](https://www.project44.com/blog/whats-new-in-movement-q4-2023/) |
| **Freightos Terminal** | App frame: lane list panel + index line chart, mono uppercase title bar | [Freightos Terminal](https://www.freightos.com/enterprise/terminal/) |
| **Windward** | Maritime-intelligence product imagery: satellite map, corner-bracket "evidence" cards, targeting rings | [windward.ai](https://windward.ai/) |
| **Maersk** | Live tracking page: thin oversized headline, input-first form, white canvas | [maersk.com/tracking](https://www.maersk.com/tracking/) |
| **Kuehne+Nagel** | Brand frame only (Sea Explorer URL now 404s) | kuehne-nagel.com |
| **Vizion, FourKites, Shippeo** | Apps are behind logins; feature descriptions only | [Vizion app](https://www.vizionapi.com/application-marketing), [FourKites overview](https://fugo.ai/dashboard/fourkites-dashboard) |
| **CargoWise, Magaya** | Behind login; known as dense ERP-style table interfaces | — |
| **Shipmap.org** (Kiln/UCL) | Real-data WebGL ship map with metric strip and month timeline | [shipmap.org](https://www.shipmap.org/), [IIB Awards](https://informationisbeautifulawards.com/showcase/1580-shipmap-org) |
| **Dribbble "shipping ui ux"** (your screenshot) | Concept work: 3D globes with data cards, container photography, light route-optimisation SaaS | dribbble.com/search/shipping-ui-ux |

I did not accept any cookie consent. I rejected cookies where that was needed to see a page, and otherwise left banners in place.

## 2. What the industry actually does

**Layout.** Serious tools put the map edge-to-edge and float the controls on top of it (MarineTraffic, Windward). Business SaaS (Flexport) puts the map in a module beside a column of KPIs. Analyst tools (Freightos) use a lane-list panel next to a chart. Carriers (Maersk, DHL, UPS, FedEx) lead with a tracking input, because their user arrives with a container number.

**Navigation.** The patterns are a narrow left icon rail (MarineTraffic), a dark top bar with a global search box (Flexport's "Search or ask"), and a right-hand map toolbar for layers, filters and playback (MarineTraffic). Search is always prominent and usually pill-shaped.

**Colour.**
- Maps are either deep slate/ocean blue (MarineTraffic, project44, Windward) or very pale blue with low detail (Flexport).
- One saturated "signal" colour does the talking: Flexport and K+N use electric blue, Windward orange, Maersk teal.
- Status is always red (exception), amber (watch) and green (on time).
- Gradients appear only in marketing. Inside apps, surfaces are flat.

**Typography.**
- A neutral grotesk for UI (Maersk uses a thin, wide display face).
- Monospace uppercase for labels, codes and coordinates. This shows up at Flexport (navigation), Windward (cards), Freightos (title bar) and MarineTraffic (data).
- No decorative or serif display type inside any app.

**Components.**
- KPI modules: a big number, a red exception dot and drill-down links (Flexport).
- Lane and shipment lists with a filled selected state (Freightos).
- Detail panels that slide over the map when you click an object (MarineTraffic info windows).
- Mode filter rails (Flexport).
- Map controls: zoom, layers and playback.

**Map visualisation.** Lanes are drawn with direction cues, ports and vessels are glyphs, and objects are colour-coded by type. Clicking an object opens a panel. Playback, timelines and live pulses signal freshness (MarineTraffic playback, Shipmap timeline). Intelligence products add targeting rings and corner-bracket frames to show something has been "detected" (Windward).

**Surfaces & motion.**
- Shadows are used only on floating panels, to lift them off the map.
- Borders are 1px hairlines.
- Translucent or frosted panels appear over maps.
- Motion is functional: vessels move, the camera flies to a selection, and live dots pulse. There are no decorative blobs.

**What reads as premium and enterprise-grade.** Restraint: one accent colour, real data density without clutter, consistent monospace metadata, a map that feels live, and panels that feel like instruments rather than marketing cards.

## 3. Five directions found in the industry

| | A. Command Map | B. Control Tower | C. Analyst Terminal | D. Carrier Utility | E. Cinematic Concept |
|---|---|---|---|---|---|
| Seen at | MarineTraffic, Windward, project44 | Flexport, FourKites, Shippeo | Freightos Terminal, CargoWise | Maersk, DHL, UPS, FedEx | Dribbble concepts |
| Canvas | Dark full-bleed map | Light app, map in a module | Light, chart-led | White, brand-coloured | Photo / 3D globe |
| Structure | Floating panels over the map | Top nav + KPI column + map + lists | Lane list + charts + tables | Input-first form | Hero + cards |
| Feels | Live, operational, intelligence | Trustworthy business SaaS | Data-credible, dry | Utility, consumer | Wow, but a mockup |
| Map role | *Is* the interface | One module of many | Secondary | Small or absent | Decorative |
| Risk for us | Can feel like a defence ops centre; dark text compresses badly if text sits on the map | Easily looks like a generic admin template | Too dry for a sales demo | Wrong job (no tracking number) | Not a working product |

## 4. Recommendation: "Trade Control Tower"

**A Command Map stage with Control Tower panels.** The map becomes the application canvas (from A). Every word sits on crisp light panels floating above it (from B), so text stays sharp in compressed WhatsApp video. Monospace metadata and lane lists come from C. D and E are rejected.

### Layout (desktop)
```
┌──────────────────────────────────────────────────────────────────────────────┐
│ ◎ EXPORTPULSE  [ Search importer, HS code, port… ]  Handicrafts ▾   ⓘ ✎ ⛁   │  dark bar, 56px
├──────────────────────────────────────────────────────────────────────────────┤
│┌ IMPORTERS ─────────┐   ┌ ₹3.17 Cr · $6.7M · 92 ctr · 17d ┐   ┌ SELECTED ───┐│
││ [All] [≤30d] [85+] │   └──────── floating KPI strip ──────┘   │ Pottery Barn ││
││ ① Pottery Barn  94 │                                          │ Offer|Route| ││
││ ② Pier 1        92 │       DEEP-OCEAN MAP CANVAS              │ Outreach    ││
││ ③ World Market  88 │   lanes glow · ships move · rings pulse   │  $3.51 ───● ││
││ ④ Z Gallerie    85 │                                          │ saves $4,446││
││ ⑤ 10k Villages  78 │                                          │ keep ₹1.14Cr││
│└────────────────────┘                          [+][−][⟲][layers] └─────────────┘│
│  legend · source                             [ Get the full list on WhatsApp ] │
└──────────────────────────────────────────────────────────────────────────────┘
```
- **Mobile:** the map takes the top half, and the panels become a bottom sheet with tabs (Importers / Offer / Outreach).

### Design system
| Token | Value | Use |
|---|---|---|
| `--ocean` | `#0A1A2A` | map water / app canvas |
| `--land` / `--land-home` | `#16293B` / `#1F3B54` | land / India and the US lifted slightly |
| `--coast` / `--grat` | `#2B4A63` / `rgba(255,255,255,.045)` | coastline / graticule |
| `--panel` | `#FFFFFF` (96%, backdrop blur) | all text-bearing surfaces |
| `--ink` / `--muted` / `--line` | `#0E1B26` / `#5C6B77` / `#E3E8EC` | text / secondary / hairlines |
| `--signal` | `#E0457B` (map) / `#B0235B` (panels) | lanes, selection, primary action; the brand colour we already have |
| `--live` | `#3FD0C9` | fresh activity (arrival ≤ 30 days), live pulses |
| `--watch` | `#F2A93B` | buying signal ("why now") |
| `--good` / `--bad` | `#2FA36B` / `#E5484D` | buyer savings / above-market quote |

- **Type:** Archivo for UI (14/13/12; panel titles 15/600; KPI figures 22–28/600 tabular). Archivo expanded caps for section labels. Spline Sans Mono for HS codes, coordinates, ports, dates and counts. No serif or display type.
- **Shape:** panels 14px radius with 1px hairline and a single soft shadow (`0 18px 40px -20px rgba(0,0,0,.45)`). Chips and pills 999px. No gradients inside the app.
- **Iconography:** 1.6px-stroke line icons. Map glyphs: hull (ship), square (port), ring (factory), numbered disc (importer).

### Components
1. **Top bar:** brand, global search (filters the importer list as you type), sector switch, seller tools.
2. **Importer panel:** filter chips (All / Arrived ≤ 30 days / Match 85+), ranked rows whose numbers match the map markers, hover to preview a lane, click to select.
3. **KPI strip:** four figures, floating over the top of the map.
4. **Detail panel:** slides in from the right on selection, with tabs for Offer (slider plus results), Route (port pills plus landed cost) and Outreach (sequence plus copy).
5. **Map controls:** zoom +/−, reset view, layer toggles (lanes / ports / ships).
6. **Legend and source line:** small text, bottom-left.
7. **Demo-only CTA pill:** bottom-right, opens WhatsApp. It never appears on a paid client's portal.

### Motion
- **Load:** lanes draw out from the factory, then markers settle and ships start moving.
- **Selection:** the camera eases to fit that route (zoom and pan), the lane brightens, and the detail panel slides in (240 ms).
- **Freshness:** importers with an arrival in the last 30 days pulse a cyan ring. This is the "live system" cue.
- **Figures:** numbers count between values.
- **Reduced motion:** all of the above switches off under reduced-motion settings.

### What changes from today
- **Kept:** the real d3 map, routes via Suez and Panama, ships, numbered markers, hover preview, and every calculation, outreach and data tool.
- **Changes:** the map goes dark and full-bleed and becomes the canvas; panels float over it; the deal room becomes a slide-in detail panel; search, filter chips, zoom and layer controls are added.
- **Cost:** map zoom adds `d3-zoom` from the CDN (about 25 KB). Nothing changes on the Python side.

### Risks
- **Dark canvas legibility:** handled by keeping all text on light panels.
- **Smaller laptops:** on 1280px screens the two side panels squeeze the map, so below 1180px the importer panel collapses to a toggle.
