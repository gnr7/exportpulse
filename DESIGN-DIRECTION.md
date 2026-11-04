# ExportPulse — Visual Identity Proposal

*Research and recommendation only. No code changed. Awaiting approval. 4 Nov 2026.*
*The current app design is saved as "Control Tower" in `designs/control-tower/`.*

---

## 1. Research findings

### Your references
**"GFS" hero (Dribbble):**
- A full-bleed aerial photo of a container ship, with a huge geometric sans headline (Outfit-like) and a warm orange pill CTA.
- Data cards (route CN SHG → US OAK with ATD/ETA, a rating card) float *on* the photograph, so the product appears inside the story.
- Lesson: photography carries the emotion and small data cards carry the credibility.

**Dribbble "Shipping UI UX" grid.** The recurring patterns:
1. Cinematic ship and port photography with overlaid UI cards (GFS, Eloqent, LAIN, Pixelean).
2. Device mockups: a phone in hand, a laptop on a desk (Qudra, RonDesignLab, Pixelean).
3. 3D globe with orbiting data cards (UICORE).
4. Light route-optimisation SaaS screens with maps (Ruslan Kosinov).
5. Poster-like bold typography and colour blocking (Nixtio "Beyond Borders", Ismail Nahid).
6. Flat illustration (Delisas).
7. Dark operations dashboards with 3D containers (RonDesignLab).

### Sites I visited
| Source | What it shows | Lesson |
|---|---|---|
| [Logika on Awwwards](https://www.awwwards.com/inspiration/homepage-logika-beyond-logistics-1) | Warehouse photography in a rust duotone with halftone grain; minimal white type; outlined label frames | A *treatment* turns stock-like photos into a brand texture |
| [Kpler](https://www.kpler.com/) | Aerial port photo under a dark scrim; giant centred "Global **trade**" with one coral word | One accent word in a big headline is enough |
| [Planet](https://www.planet.com/) | A mosaic of satellite tiles as the hero; black canvas, teal outlines | Imagery from the data itself is more convincing than stock |
| [Forto](https://forto.com/en/) | White canvas, bold navy grotesk; aerial ship photo cropped into an arch with isometric line cubes | Geometric photo masks plus line illustration feel ownable |
| [Dribbble: supply chain website](https://dribbble.com/search/supply-chain-website) | Dark heroes with real UI cards peeking from below; laptop mockups | Show the actual product early |
| Earlier rounds: [MarineTraffic](https://www.marinetraffic.com/), [Flexport](https://www.flexport.com/products/flexport-platform/), [Windward](https://windward.ai/), [Shipmap.org](https://www.shipmap.org/) | Map-as-interface, mono metadata, HUD frames, real-data maps | The map is the category's most credible visual |
| Awwwards logistics entries ([M.V.P. Trans-Logistics](https://www.awwwards.com/sites/m-v-p-trans-logistics), [Madar](https://www.awwwards.com/sites/madar), [Emons](https://www.awwwards.com/sites/emons)) | Award-listed logistics brands | Recognition goes to strong art direction, not dashboards |

Land-book search requires an account, and Godly now redirects to a lazy-loading site, so neither yielded usable references. I didn't accept any cookie consent; I denied or rejected it where that was needed to see a page.

### What the best work has in common
1. **One emotional image and one honest data point, together.** The photograph sells the dream; a small card with a real number makes it believable.
2. **The product appears early,** inside the story, not on a separate "features" page.
3. **A signature visual device** that no other site has (Planet's tile mosaic, Forto's geometric masks).
4. **Restraint:** one accent colour and one typeface family. Text sits on calm surfaces.
5. **Motion tied to meaning:** routes draw and counters count up, instead of decorative blobs.

---

## 2. Five directions

### A · Horizon — cinematic photography
- **References:** your GFS shot, Kpler, Eloqent/LAIN on Dribbble.
- **Type and colour:** Outfit (display) + Inter (UI); deep ocean `#1D3A57`, sky `#4E7392`, saffron `#E8A33D`, warm white.
- **Hero:** full-bleed aerial photo or an 8-second muted loop of a ship, a giant headline, a saffron CTA, and glass cards with real routes.
- **Media:** drone photography and slow loops; cool shadows with warm highlights.
- **Motion:** slow parallax, cards rising in, a video crossfade between sections.
- **App:** photos only in headers and empty states; the work happens in a clean shell.
- **Pros:** instantly emotional and closest to your references.
- **Cons:** the most common look in the category (stock-ship cliché), heavy media, and image licensing to sort out.

### B · Meridian — cartographic intelligence *(recommended)*
- **References:** our own map, Shipmap.org, MarineTraffic, Forto's geometry.
- **Type and colour:** Archivo Expanded for display, Archivo for UI, Spline Sans Mono for data. Chart paper, sea, buff land, route magenta, deep-ocean navy shell.
- **Hero:** photography *transitions into* our chart (see §3).
- **Media:** aerial photos, plus catalogue photography of the goods for sectors.
- **Motion:** scroll-scrubbed route drawing, plus a stop-by-stop reveal of real records.
- **App:** Control Tower with the same tokens.
- **Pros:** ownable, consistent between site and app, built on real data, and it keeps the map you love.
- **Cons:** needs careful motion craft to feel cinematic, and is less instantly "wow" than A.

### C · Manifest — industrial typography
- **References:** Nixtio "Beyond Borders", Ismail Nahid posters, container livery.
- **Type and colour:** Big Shoulders Display (condensed, stencil-like) + mono ISO container codes; rust `#A9472A`, signal yellow, steel blue, black.
- **Hero:** a poster-sized number ("30 CTR → LAX") on corrugated-steel texture.
- **Media:** macro photos of container doors, lashing gear and port cranes.
- **Motion:** stacking-container scroll reveals, number flips.
- **App:** livery colours for sectors, condensed numerals for KPIs.
- **Pros:** very memorable, and striking on WhatsApp.
- **Cons:** loud, reads "freight forwarder" more than "intelligence", and gets tiring inside an app.

### D · Orbit — earth observation
- **References:** Planet, Windward, Kpler.
- **Type and colour:** Space Grotesk + mono; near-black, deep teal, cyan.
- **Hero:** a mosaic of satellite tiles of the actual ports (Nhava Sheva, LA/Long Beach) with HUD frames.
- **Media:** satellite imagery and a dark globe.
- **Motion:** tile zooms, HUD reticles.
- **App:** dark map workspace.
- **Pros:** feels high-tech and analytical.
- **Cons:** implies real-time surveillance we don't have (this breaks your honesty rule), satellite imagery is expensive to license, and dark globes are a cliché.

### E · Atelier — craft to commerce
- **References:** luxury catalogue photography, artisan brands.
- **Type and colour:** Hanken Grotesk; cotton white, brass `#B8862F`, madder red, indigo.
- **Hero:** the *goods* (a Moradabad brass lamp, Kerala cardamom, Panipat linen) shot like a catalogue, with "Made in India. Already selling in America."
- **Media:** product macro photography and artisans' hands.
- **Motion:** slow image reveals, product rotations.
- **App:** sector colours from materials.
- **Pros:** no logistics site does this, it's deeply relevant to Indian exporters, and it's emotional.
- **Cons:** risks reading as e-commerce, is weaker on the "intelligence" story, and needs real product photography.

---

## 3. Recommendation: **Meridian** (B), with A's photography and E's goods

**Why:**
- It's the only direction where the visual signature is *our own data*: routes from the factory's city to real importers. A competitor can't copy it without our data model.
- It carries straight into the application. The site and the app share one visual language, which you asked for.
- It borrows A's emotion: the hero photograph you liked.
- It borrows E's relevance: sector pages show the actual goods.
- Neither of those becomes the whole identity.

**Signature moment: "the sea becomes the chart".**
1. **Arrive:** a full-bleed aerial photograph (or 8-second loop) of a container ship. The headline is personalised ("US buyers for *Shree Brass Works*") and there's an HS-code search box. One real-record card reads "5 importers · US Customs · 12 months".
2. **Dissolve:** as you scroll, the photo's ocean cross-fades into the chart's sea colour. The coastline draws in and the route starts at Moradabad.
3. **Passage:** the route continues stop by stop: Nhava Sheva → via Suez → US port of entry → importer HQ. Each stop reveals a small card with a *real* record: containers, last recorded arrival.
4. **Hand-off:** the final frame *is* the app's map, with an "Open the full map" button that goes into Control Tower.

**Honesty built in:**
- No moving ships or "live" badges.
- Every card says "US Customs record" or "last recorded arrival".
- Routes are labelled "indicative".
- **No invented ratings or testimonials** (your GFS reference had a 4.8★ review card). The trust section uses the data source and method until real customers exist.

---

## 4. Proposed design system (Meridian)

| Role | Token | Value |
|---|---|---|
| Ocean (shell, dark sections) | `--ocean` | `#0F1D2B` |
| Ocean 2 / line | `--ocean-2` / `--ocean-line` | `#16293B` / `#22374B` |
| Paper (light sections) | `--paper` | `#F6F7F4` |
| Chart sea / shoal | `--sea` / `--shoal` | `#E2ECEC` / `#CFE0E3` |
| Chart land / India and US | `--land` / `--land-home` | `#EDE4CB` / `#E4D29F` |
| Ink / secondary / muted | `--ink` / `--ink-2` / `--muted` | `#14232C` / `#44555E` / `#6F8189` |
| **Route magenta (signature + primary)** | `--route` | `#B0235B` (on dark `#D27CA0`) |
| Buying signal | `--signal` | `#8A5A12` on `#FBF3E4` |
| Savings / positive | `--good` | `#1F6B41` on `#E6F3EB` |
| Warning / above market | `--bad` | `#B42318` on `#FDECEC` |

- **Typography**
  - Display: Archivo Expanded (width 125), 600–700, sizes 64/48/36/28, tracking −1%. Wide, international, livery-like without being a gimmick.
  - UI/body: Archivo 400–600, 16/14/13.
  - Data: Spline Sans Mono 11–12 for HS codes, coordinates, ports and dates.
  - No serif; one family plus mono.
- **Grid:** 12 columns, 1280px content width, 32px gutters. Sections alternate full-bleed photo / paper / ocean for rhythm.
- **Surfaces:** cards 14px radius with a 1px line. Floating cards on photos use 92% white or 82% ocean with a 12px backdrop blur, the only blur in the system. One shadow token, for floating elements only.
- **Iconography:** 1.6px line icons with round caps. Chart glyphs: ring = factory, square = port, numbered disc = importer, dashed line = inland leg.
- **Brand motif:** the **route line**. It becomes the logo underline, section dividers, the loading indicator (a route drawing), focus rings and hover underlines.
- **Photography**
  - Style: aerial, top-down or 45°; ocean, port, container geometry; no people pointing at screens and no handshakes.
  - Grade: cool shadows (towards `--ocean`) and neutral highlights, so photos sit next to the chart palette.
  - Sectors: catalogue shots of the goods on paper backgrounds.
- **Video:** 6–10 second silent loops, at most 2 MB (H.264 + WebM), always with a poster frame. Not loaded on slow connections ("save data"), and the poster replaces the video under reduced motion.
- **Motion:**
  - Scroll-scrubbed route drawing and the sea-to-chart dissolve.
  - Cards rise in (12px, 400 ms); numbers count between values.
  - Hover: lift 2px plus the route underline.
  - All of it switches off under reduced motion. Nothing loops except the optional hero video.

---

## 5. Proposed structure

### Website (`/`, personalised by `?factory=&city=&category=`)
1. **Navigation:** transparent over the hero, ocean-navy once scrolled. Brand, Product, Sectors, Data source, and an "Open the map" CTA.
2. **Hero:** aerial photo or loop, personalised headline, HS-code or product search, one real-record card.
3. **Sea-to-chart route story:** scroll-scrubbed, with 3–4 stops of real records.
4. **Sector bento:** four tiles with goods photography (brassware, spices and cashews, home textiles, leather). Each shows its importer count and containers from the database.
5. **The product in a frame:** the real Control Tower UI in a browser frame, interactive, not a picture.
6. **Offer teaser:** an FOB slider showing "buyer saves / you keep", using the real calculator API.
7. **Data source and method:** a sample bill-of-lading record, clearly labelled as a sample, showing what's inside one.
8. **Personalised CTA:** "Get every importer for *Shree Brass Works*", via WhatsApp.
9. **Footer:** a route-line motif, sitemap and data notes.

### Application (`/app`)
- **Map workspace:** Control Tower with Meridian tokens.
- **Importer detail tabs:** unchanged in function.
- **Sector overview (new):** the importers, ports of entry and HS codes for one sector, on the map.
- **Offer sheet (new):** a printable or PDF one-page offer per importer, using the browser's print styles (no library).
- **Outreach composer:** a sequence view.
- **Data manager:** add buyer and CSV import/export.

---

## 6. How media would be used
| Where | Photo | Video | Animation | Product visual |
|---|---|---|---|---|
| Hero | Aerial ship or port (graded) | Optional 8-second loop, poster first | Headline and cards rise in | Real-record card |
| Route story | Sea photo dissolving into chart | — | Scroll-scrubbed route plus stop cards | The live map component |
| Sector bento | Goods catalogue shots | — | Hover lift, count-up | Counts from the database |
| Product frame | — | — | Tabs switch on hover or scroll | The actual app UI |
| Offer teaser | — | — | Slider-driven numbers | The real calculator API |
| App empty states | Small duotone port photo | — | Route-line loader | — |

**Image sourcing:** free-licence aerial photography (Pexels or Unsplash, checked per image) or your own photos of factories and goods, which would be stronger and more honest. Everything is compressed to AVIF/WebP, and the hero stays at or under 300 KB.

---

## 7. Implementation plan (after approval)
1. **Decisions** (needs your input):
   - Where the marketing homepage and app live. Proposed: homepage at `/`, app at `/app`, and today's demo links keep working by opening the personalised homepage, which leads into the app.
   - Photo source: your own photos, or free-licence photos.
2. **Tokens and assets:** one shared `brand.css` (tokens, type, components) served with FastAPI's built-in static files (no new dependency). An `assets/` folder for optimised photos and the poster frame.
3. **Homepage:** build sections 1–9. The route story reuses the existing map code. Scroll effects use the browser's IntersectionObserver plus a scroll-progress CSS variable, with no animation library.
4. **App rebrand:** apply tokens to Control Tower; add the sector overview and the printable offer sheet.
5. **Motion and media pass:** video loading rules, reduced-motion and save-data handling.
6. **QA:**
   - Targets: LCP < 2.5 s on a mid-range laptop, CLS < 0.05, hero media ≤ 1.5 MB.
   - Checks: keyboard and screen-reader basics, desktop/tablet/phone, and the existing smoke tests plus new checks for `/app`.
7. **Snapshot:** save the result as a named design (like Control Tower) so you can compare and switch.

### Extra ideas
- **WhatsApp link preview card:** when you send a prospect their link, the preview could show "Prepared for Shree Brass Works" with their route. That needs server-side image generation, which means a new dependency (Pillow), so it's optional and only with your approval.
- **HS code as the front door:** the hero's main action is "type your HS code", so the site proves its value in the first click.
- **Route line as the brand:** the same magenta line is the logo underline, the loader, the dividers and the focus ring. The identity travels into every screen.
- **Printable offer sheet:** a one-page PDF per importer that the factory owner can forward internally. It turns the demo into a document they keep.
