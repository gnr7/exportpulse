"""Build prototypes/app.html from the saved Control Tower page (designs/control-tower/page-template.html).

The prototype keeps the real application code and swaps three things:
  1. API calls -> the demo-dataset snapshot plus calc.js (a verified copy of the Python logic);
  2. server-side placeholders -> values read from the page URL;
  3. styling -> the Meridian identity (route-line mark, sector photography, expanded display type).
Run:  python prototypes/build_app.py
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT.parent / "designs" / "control-tower" / "page-template.html"
OUT = ROOT / "app.html"

page = SRC.read_text(encoding="utf-8")


def swap(old, new, count=1):
    global page
    if page.count(old) < count:
        raise SystemExit(f"anchor not found: {old[:60]!r}")
    page = page.replace(old, new)


param = "new URLSearchParams(location.search).get('{0}')"
swap("__FACTORY_HTML__", "Shree Brass Works", 2)
swap("__CITY_HTML__", "Moradabad")
swap("__CATEGORY_JS__", f"({param.format('category')} || 'handicrafts')")
swap("__FACTORY_JS__", f"({param.format('factory')} || 'Shree Brass Works')")
swap("__CITY_JS__", f"({param.format('city')} || 'Moradabad')")
swap("__SELLER_JS__", "''")
swap("__DEMO_JS__", "true")

# 1. data layer: same request shapes, answered from the snapshot and the verified JS logic
API_START = "const api = async (url, o) => {"
start = page.index(API_START)
end = page.index("};", start) + 2
page = page[:start] + """const api = async (url, o) => {
  /* PROTOTYPE: answers the app's own API calls from the demo-dataset snapshot */
  const u = new URL(url, location.href), all = Object.values(EP_DATA.sectors).flat();
  const find = id => { const b = all.find(x => x.id === id); if (!b) throw new Error('Buyer not found'); return b; };
  if (u.pathname.endsWith('/api/buyers')) {
    const c = u.searchParams.get('category');
    return JSON.parse(JSON.stringify(c ? (EP_DATA.sectors[c] || []) : all));
  }
  const m = u.pathname.match(/\\/api\\/cost-calc\\/(.+)$/);
  if (m) return EPCalc.calculateCost(find(decodeURIComponent(m[1])), +u.searchParams.get('your_fob_usd'));
  if (u.pathname.endsWith('/api/outreach')) {
    const r = JSON.parse(o.body), b = find(r.buyer_id);
    const fob = r.your_fob_usd > 0 ? r.your_fob_usd : Math.round(b.competitor_fob_usd * 90) / 100;
    return EPCalc.buildTemplates(b, r.factory_name, r.factory_city, fob);
  }
  throw new Error('Data tools are switched off in the prototype');
};""" + page[end:]
swap("const exportCsv = () => { location.href = '/api/export-csv?category=' + encodeURIComponent(S); };",
     "const exportCsv = () => toast('Export works in the live app; the prototype uses a read-only snapshot');")

# 2. URL-driven start: ?q= pre-fills search, ?pick= opens an importer, sector photo follows the sector
swap("  $('sector').value = S;\n", "  $('sector').value = S;\n  setSectorPhoto(S);\n")
swap("updateChrome();\nload(S);",
     """updateChrome();
document.querySelectorAll('[data-bind="factory"]').forEach(el => el.textContent = FN);
document.querySelectorAll('[data-bind="city"]').forEach(el => el.textContent = FC);
{ const q0 = new URLSearchParams(location.search).get('q'); if (q0) { $('q').value = q0; FILT.q = q0.trim().toLowerCase(); } }
$('waBtn').addEventListener('click', e => { e.preventDefault(); toast('In the live app this opens a WhatsApp chat with you'); });
load(S, new URLSearchParams(location.search).get('pick') || undefined);""")

# 2b. QA pass (prototype only): corrected sea-lane waypoints, the same as assets/geo.js
swap("sea:[[10.0,82.6],[5.6,80.6],", "sea:[[10.0,82.6],[6.3,82.2],[5.6,80.6],")
swap("[8.5,82.6],[5.6,80.6],", "[8.5,82.6],[6.3,82.2],[5.6,80.6],")
swap("const SUEZ = [[12.6,43.4],[20.0,38.6],[27.6,33.9],[29.95,32.56],[31.4,32.35],[33.8,26.0],[37.2,11.5],[37.3,1.0],[35.95,-5.6]];",
     "const SUEZ = [[12.6,43.4],[20.0,38.6],[27.6,33.9],[29.0,32.85],[29.95,32.56],[31.4,32.35],[33.8,26.0],[36.3,15.2],[37.4,11.3],[37.75,9.5],[37.3,1.0],[36.3,-2.2],[35.95,-5.6]];")
swap("nyc: {n:'New York / NJ',   ll:[40.60,-74.00], sea:[[38.5,-40],[40.3,-70.5]]},",
     "nyc: {n:'New York / NJ',   ll:[40.67,-74.08], sea:[[38.5,-40],[40.3,-70.5],[40.42,-73.85]]},")
swap("sav: {n:'Savannah',        ll:[32.03,-80.85], sea:[[34,-40],[31.9,-79.5]]},",
     "sav: {n:'Savannah',        ll:[32.08,-81.09], sea:[[34,-40],[31.9,-79.5],[32.03,-80.85]]},")
swap("hou: {n:'Houston',         ll:[29.40,-94.70], sea:[[29,-40],[26.2,-76.8],[25.9,-79.0],[24.3,-81.5],[25.5,-87],[28.6,-93.5]]},",
     "hou: {n:'Houston',         ll:[29.68,-95.00], sea:[[29,-40],[26.2,-76.6],[25.85,-77.0],[26.1,-78.3],[25.9,-79.3],[24.3,-81.5],[25.5,-87],[28.6,-93.5],[29.35,-94.72]]},")
swap("sea:[[22,-40],[18.4,-65.5],[12.5,-76.0],[9.38,-79.92],[8.93,-79.56],[7.2,-80.5],[14.5,-98],",
     "sea:[[22,-40],[18.45,-63.9],[12.5,-76.0],[9.38,-79.92],[8.93,-79.56],[7.0,-79.6],[6.6,-81.0],[9.8,-88.5],[14.5,-98],")

# 2c. QA pass: one marker per kind of stop (factory dot, export port open square, canal diamond,
#     US port filled square, importer ring), matching the homepage key
swap("  items.push({kind: 'origin', p: P(o)});",
     """  items.push({kind: 'via', p: P([29.95, 32.56]), t: 'SUEZ CANAL'});
  if (lanes.lax) items.push({kind: 'via', p: P([9.1, -79.7]), t: 'PANAMA CANAL'});
  items.push({kind: 'origin', p: P(o)});""")
swap("      g.setAttribute('class', 'port');",
     "      g.setAttribute('class', it.us ? 'port us' : 'port');")
swap("    } else if (it.kind === 'origin') {\n      g.innerHTML",
     """    } else if (it.kind === 'via') {
      g.setAttribute('class', 'via');
      g.innerHTML = `<rect x="-3.2" y="-3.2" width="6.4" height="6.4" transform="rotate(45)"/><text class="halo" x="0" y="15" text-anchor="middle">${esc(it.t)}</text>`;
    } else if (it.kind === 'origin') {
      g.innerHTML""")
swap("""        <span class="opt"><svg width="12" height="12" aria-hidden="true"><circle cx="6" cy="6" r="4.8" fill="#fff" stroke="#B0235B" stroke-width="1.4"/></svg>Size = containers</span>""",
     """        <span class="opt"><svg width="12" height="12" aria-hidden="true"><circle cx="6" cy="6" r="4" fill="#B0235B" stroke="#fff" stroke-width="1.6"/></svg>Factory</span>
        <span class="opt"><svg width="10" height="10" aria-hidden="true"><rect x="1.5" y="1.5" width="7" height="7" fill="#fff" stroke="#15222E" stroke-width="1.2"/></svg>Export port</span>
        <span class="opt"><svg width="10" height="10" aria-hidden="true"><rect x="2.4" y="2.4" width="5.2" height="5.2" transform="rotate(45 5 5)" fill="#fff" stroke="#D27CA0" stroke-width="1.3"/></svg>Canal</span>
        <span class="opt"><svg width="10" height="10" aria-hidden="true"><rect x="1.5" y="1.5" width="7" height="7" fill="#15222E"/></svg>US port of entry</span>
        <span class="opt"><svg width="12" height="12" aria-hidden="true"><circle cx="6" cy="6" r="4.8" fill="#fff" stroke="#B0235B" stroke-width="1.4"/></svg>Importer HQ · size = containers</span>""")

swap("  zm.style.right = ($('detail').classList.contains('open') ? $('detail').offsetWidth + 24 : 12) + 'px';\n};",
     """  zm.style.right = ($('detail').classList.contains('open') ? $('detail').offsetWidth + 24 : 12) + 'px';
  /* the longer key wraps instead of running under the detail panel */
  lg.style.maxWidth = ($('stage').clientWidth - lg.offsetLeft - parseFloat(zm.style.right) - 56) + 'px';
};""")
swap("Importer HQ · size = containers</span>", "Importer HQ (size = containers)</span>")

# 2e. Refinement pass: importer markers keep clear of each other and of port / factory glyphs,
#     and map labels give way to markers instead of sitting underneath them
swap("""  for (let n = 0; n < 40; n++) for (let a = 0; a < mks.length; a++) for (let c = a + 1; c < mks.length; c++) {
    const p = mks[a], q = mks[c];
    const dx = q.nx - p.nx, dy = q.ny - p.ny, d = Math.hypot(dx, dy) || 0.01, min = p.r + q.r + 3;
    if (d < min) { const s = (min - d) / 2 / d; p.nx -= dx * s; p.ny -= dy * s; q.nx += dx * s; q.ny += dy * s; }
  }
  mks.forEach(it => {
    it.el.setAttribute('transform', `translate(${it.nx.toFixed(1)},${it.ny.toFixed(1)})`);
    const moved = Math.hypot(it.nx - it.sx, it.ny - it.sy) > 3;
    it.lead.setAttribute('x1', it.sx); it.lead.setAttribute('y1', it.sy);
    it.lead.setAttribute('x2', it.nx); it.lead.setAttribute('y2', it.ny);
    it.lead.style.display = moved ? '' : 'none';
  });
};""", """  /* fixed glyphs (ports, canals, factory) are obstacles the markers move off */
  const fixed = MAP.overlay.filter(it => it.kind === 'port' || it.kind === 'via' || it.kind === 'origin');
  for (let n = 0; n < 60; n++) {
    for (let a = 0; a < mks.length; a++) for (let c = a + 1; c < mks.length; c++) {
      const p = mks[a], q = mks[c];
      const dx = q.nx - p.nx, dy = q.ny - p.ny, d = Math.hypot(dx, dy) || 0.01, min = p.r + q.r + 5;
      if (d < min) { const s = (min - d) / 2 / d; p.nx -= dx * s; p.ny -= dy * s; q.nx += dx * s; q.ny += dy * s; }
    }
    mks.forEach(p => fixed.forEach(f => {
      const dx = p.nx - f.sx, dy = p.ny - f.sy, d = Math.hypot(dx, dy) || 0.01, min = p.r + 7;
      if (d < min) { const s = (min - d) / d; p.nx += dx * s; p.ny += dy * s; }
    }));
  }
  mks.forEach(it => {
    it.el.setAttribute('transform', `translate(${it.nx.toFixed(1)},${it.ny.toFixed(1)})`);
    const moved = Math.hypot(it.nx - it.sx, it.ny - it.sy) > 3;
    it.lead.setAttribute('x1', it.sx); it.lead.setAttribute('y1', it.sy);
    it.lead.setAttribute('x2', it.nx); it.lead.setAttribute('y2', it.ny);
    it.lead.style.display = moved ? '' : 'none';
  });
  placeLabels(mks, selPort);
};

/* labels in priority order; each tries its own position, then the other side, then hides if it would cover a marker or a stronger label */
const placeLabels = (mks, selPort) => {
  const boxes = mks.map(m => [m.nx - m.r - 2, m.ny - m.r - 2, m.nx + m.r + 2, m.ny + m.r + 2]);
  const hit = b => boxes.some(o => b[0] < o[2] && b[2] > o[0] && b[1] < o[3] && b[3] > o[1]);
  const rank = it => it.kind === 'origin' ? 0 : it.us && it.us === selPort ? 1 : it.kind === 'port' ? 2 : it.kind === 'via' ? 3 : 4;
  MAP.overlay.filter(it => it.kind !== 'mk').sort((a, b) => rank(a) - rank(b)).forEach(it => {
    it.el.querySelectorAll('text').forEach(t => {
      if (t.style.display === 'none' && it.us) return;      /* zoomed-out port names stay hidden, as before */
      t.style.display = '';
      if (t.dataset.x0 === undefined) { t.dataset.x0 = t.getAttribute('x') || 0; t.dataset.y0 = t.getAttribute('y') || 0; t.dataset.a0 = t.getAttribute('text-anchor') || 'middle'; }
      const x0 = +t.dataset.x0, y0 = +t.dataset.y0, a0 = t.dataset.a0;
      /* ports: own spot, mirrored, right, left, above, below */
      const tries = it.kind === 'port' ? [[x0, y0, a0], [-(x0 || 7), y0, a0 === 'end' ? 'start' : 'end'], [8, 3, 'start'], [-8, 3, 'end'], [0, -9, 'middle'], [0, 15, 'middle']] : [[null, null, null]];
      for (const [x, y, a] of tries) {
        if (x !== null) { t.setAttribute('x', x); t.setAttribute('y', y); t.setAttribute('text-anchor', a); }
        const bb = t.getBBox(), b = [it.sx + bb.x - 2, it.sy + bb.y - 1, it.sx + bb.x + bb.width + 2, it.sy + bb.y + bb.height + 1];
        if (!hit(b)) { boxes.push(b); return; }
      }
      t.style.display = 'none';
    });
  });
};""")

# 2d. QA pass: the commission figure is an estimate, and says so where it appears
swap("""<div class="kpi k1" title="5% buying-agent commission on these importers' annual US imports"><b class="num" id="kComm">–</b><span>agent fees / yr</span></div>""",
     """<div class="kpi k1" title="Estimate: 5% buying-agent commission × these importers' estimated annual US imports × ₹95 per US$"><b class="num" id="kComm">–</b><span>est. agent commission / yr</span></div>""")
swap('<div class="k">Commission you keep</div>', '<div class="k">Agent commission avoided (est.)</div>')

# 3. Meridian identity
swap("""    <div class="brand">
      <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="10.5" fill="none" stroke="#E6EDF2" stroke-width="1.5"/><path d="M12 1.5v21M1.5 12h21" stroke="#E6EDF2" stroke-width="1" opacity=".6"/><path d="M12 5l2.2 7L12 19l-2.2-7z" fill="#D27CA0"/></svg>
      EXPORTPULSE
    </div>""",
     """    <a class="brand" href="home.html" target="_top" style="text-decoration:none;color:inherit">
      <svg width="30" height="14" viewBox="0 0 30 14" aria-hidden="true"><circle cx="3" cy="11" r="2.6" fill="#E6EDF2"/><path d="M5 10 C 11 1, 19 1, 25 8" fill="none" stroke="#D27CA0" stroke-width="2" stroke-linecap="round"/><rect x="24" y="6.5" width="5" height="5" rx="1" fill="none" stroke="#E6EDF2" stroke-width="1.4"/></svg>
      EXPORTPULSE
    </a>
    <span class="proto-chip">Prototype · demo data</span>""")

MERIDIAN_CSS = """
/* ===== Meridian identity layer (prototype) ===== */
/* QA pass: the closed detail panel sits off-screen to the right; clip it so the page never scrolls sideways */
html,body{overflow-x:clip}
.search{width:auto;flex:1 1 240px;min-width:170px;max-width:320px}
@media (max-width:1440px){ .kpi.k3{display:none} }
@media (max-width:980px){ .search{max-width:none;flex-basis:100%} }
.proto-chip{height:24px;padding:0 9px;border-radius:999px;background:#3A2E12;color:#F2D58A;font-family:var(--mono);font-size:10.5px;display:inline-flex;align-items:center;white-space:nowrap}
.ph{position:relative;color:#fff;background:#0F1D2B;padding:18px 16px 16px;border-bottom:none;overflow:hidden;min-height:118px;display:flex;flex-direction:column;justify-content:flex-end}
.ph::before{content:"";position:absolute;inset:0;background:var(--ph-img,none) center/cover;transition:opacity .4s}
.ph::after{content:"";position:absolute;inset:0;background:linear-gradient(0deg,rgba(15,29,43,.92) 0%,rgba(15,29,43,.45) 60%,rgba(15,29,43,.25) 100%)}
.ph>*{position:relative;z-index:1}
.ph .lbl{color:#F0A9C6}
h1.who{font-stretch:125%;font-size:17px;color:#fff}
.who-sub{color:#C9D6E0}
.who-sub .mono{color:#9FB2C0}
.ph-credit{position:absolute!important;right:10px;top:8px;font-size:10px;color:rgba(255,255,255,.65);text-decoration:none;z-index:2}
.dh h2{font-stretch:112%}
.tabs button.on{box-shadow:inset 0 -2px 0 var(--mag),0 0 0 1px var(--line)}
.fact .v{font-stretch:110%}
.kpi b{font-stretch:112%}
.port.us rect{fill:var(--ink)}
/* Route tab stops use the same five glyphs as the map key */
.stops li:first-child::before{background:var(--mag);border-color:#fff;box-shadow:0 0 0 1.5px var(--mag)}
.stops li:nth-child(2)::before{border-radius:2px;border-color:var(--ink)}
.stops li.via::before{border-radius:1px;transform:rotate(45deg)}
.stops li:nth-last-child(2)::before{border-radius:2px;background:var(--ink);border-color:var(--ink)}
.stops li.end::before{background:#fff;border:3px solid var(--mag)}
/* importer markers read clearly over land and lanes */
.mk{filter:drop-shadow(0 1px 1.5px rgba(15,29,43,.35))}
.mk-c{stroke-width:2}
.mk-lead{stroke:var(--mag);stroke-width:1;opacity:.55}
.via rect{fill:#fff;stroke:var(--mag-2);stroke-width:1.3}
.via text{font-family:var(--mono);font-size:9px;fill:var(--muted);letter-spacing:.06em}
"""
swap("@media (prefers-reduced-motion:reduce){\n  *,*::before,*::after{animation:none!important;transition:none!important}\n}\n</style>",
     "@media (prefers-reduced-motion:reduce){\n  *,*::before,*::after{animation:none!important;transition:none!important}\n}\n" + MERIDIAN_CSS + "</style>")
swap('<span class="lbl">Prepared exclusively for</span>',
     '<a class="ph-credit" id="phCredit" target="_blank" rel="noopener"></a>\n          <span class="lbl">Prepared exclusively for</span>')

PRE = """<script src="assets/data.js"></script>
<script src="assets/photos.js"></script>
<script src="assets/calc.js"></script>
<script>
function setSectorPhoto(s) {
  const m = SECTOR_META[s] || SECTOR_META.handicrafts, p = EP_PHOTOS[m.photo];
  document.querySelector('.ph').style.setProperty('--ph-img', `url("${photoUrl(m.photo, 800, 70)}")`);
  const c = document.getElementById('phCredit'); c.href = p.page; c.textContent = p.by + ' / Unsplash';
}
</script>
<script>"""
swap('<script src="https://cdn.jsdelivr.net/npm/topojson-client@3.1.0/dist/topojson-client.min.js"></script>\n<script>',
     '<script src="https://cdn.jsdelivr.net/npm/topojson-client@3.1.0/dist/topojson-client.min.js"></script>\n' + PRE)

swap("<title>ExportPulse AI — Shree Brass Works</title>", "<title>ExportPulse — Map workspace (prototype)</title>")
OUT.write_text(page, encoding="utf-8", newline="\n")
print("wrote", OUT, len(page), "chars")
