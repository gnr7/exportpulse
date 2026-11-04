/* Geography for the prototypes: same city tables, ports and indicative sea lanes as the live app.
   Coordinates are [lat, lon]; d3 wants [lon, lat]. */
(() => {
  const norm = s => (s || '').toLowerCase().replace(/[^a-z ]/g, '').replace(/\s+/g, ' ').trim();
  const IN_CITIES = {
    moradabad:[28.84,78.77], bhubaneswar:[20.30,85.82], panipat:[29.39,76.97], kolkata:[22.57,88.36], calcutta:[22.57,88.36],
    kanpur:[26.45,80.33], kochi:[9.93,76.27], cochin:[9.93,76.27], visakhapatnam:[17.69,83.22], vizag:[17.69,83.22],
    surat:[21.17,72.83], agra:[27.18,78.01], jaipur:[26.91,75.79], tiruppur:[11.11,77.34], chennai:[13.08,80.27],
    mumbai:[19.08,72.88], delhi:[28.61,77.21], 'new delhi':[28.61,77.21], noida:[28.54,77.39], ludhiana:[30.90,75.85],
    karur:[10.96,78.08], jodhpur:[26.24,73.02], saharanpur:[29.96,77.55], ahmedabad:[23.02,72.57], bengaluru:[12.97,77.59],
    bangalore:[12.97,77.59], hyderabad:[17.39,78.49], amritsar:[31.63,74.87], guntur:[16.31,80.44], mangaluru:[12.91,74.86],
    kollam:[8.89,76.61], firozabad:[27.15,78.40], bhadohi:[25.39,82.57], varanasi:[25.32,82.97], mirzapur:[25.15,82.57]
  };
  const US_CITIES = {
    'fort worth|TX':[32.75,-97.33], 'alameda|CA':[37.77,-122.24], 'gardena|CA':[33.89,-118.31], 'san francisco|CA':[37.77,-122.42],
    'akron|PA':[40.16,-76.20], 'hunt valley|MD':[39.50,-76.64], 'houston|TX':[29.76,-95.37], 'fresno|CA':[36.74,-119.79],
    'brea|CA':[33.92,-117.90], 'vernon|CA':[34.00,-118.23], 'minneapolis|MN':[44.98,-93.27], 'corte madera|CA':[37.93,-122.53],
    'new york|NY':[40.71,-74.01], 'union|NJ':[40.70,-74.26], 'dallas|TX':[32.78,-96.80], 'richardson|TX':[32.95,-96.73],
    'nashville|TN':[36.16,-86.78], 'greenland|NH':[43.04,-70.83], 'norwalk|CT':[41.12,-73.41], 'bentonville|AR':[36.37,-94.21],
    'los angeles|CA':[34.05,-118.24], 'chicago|IL':[41.88,-87.63], 'seattle|WA':[47.61,-122.33], 'atlanta|GA':[33.75,-84.39],
    'miami|FL':[25.76,-80.19], 'boston|MA':[42.36,-71.06]
  };
  const US_STATES = Object.fromEntries(('AL:32.8,-86.8|AK:61.4,-152.3|AZ:34.2,-111.7|AR:34.9,-92.4|CA:37.2,-119.5|CO:39.0,-105.5|CT:41.6,-72.7|' +
    'DE:39.0,-75.5|FL:28.6,-82.4|GA:32.7,-83.4|HI:20.8,-156.3|ID:44.4,-114.6|IL:40.0,-89.2|IN:39.9,-86.3|IA:42.1,-93.5|KS:38.5,-98.4|' +
    'KY:37.5,-85.3|LA:31.1,-92.0|ME:45.4,-69.2|MD:39.0,-76.8|MA:42.3,-71.8|MI:44.3,-85.4|MN:46.3,-94.3|MS:32.7,-89.7|MO:38.4,-92.5|' +
    'MT:47.0,-109.6|NE:41.5,-99.8|NV:39.3,-116.6|NH:43.7,-71.6|NJ:40.2,-74.7|NM:34.4,-106.1|NY:42.9,-75.5|NC:35.6,-79.4|ND:47.5,-100.5|' +
    'OH:40.3,-82.8|OK:35.6,-97.5|OR:43.9,-120.6|PA:40.9,-77.8|RI:41.7,-71.5|SC:33.9,-80.9|SD:44.4,-100.2|TN:35.9,-86.4|TX:31.5,-99.3|' +
    'UT:39.3,-111.7|VT:44.1,-72.7|VA:37.5,-78.9|WA:47.4,-120.5|WV:38.6,-80.6|WI:44.6,-89.9|WY:43.0,-107.6|DC:38.9,-77.0')
    .split('|').map(p => { const [k, v] = p.split(':'); return [k, v.split(',').map(Number)]; }));
  const inLL = city => IN_CITIES[norm(city)] || IN_CITIES[norm(city).split(' ')[0]] || null;
  const usLL = b => US_CITIES[norm(b.hq_city) + '|' + (b.hq_state || '').toUpperCase()] || US_STATES[(b.hq_state || '').toUpperCase()] || [39.0, -98.0];
  const IN_PORTS = {
    nhava:  {n:'Nhava Sheva',  ll:[18.95,72.95], sea:[[12.3,52.0]]},
    kochi:  {n:'Kochi',        ll:[9.97,76.24],  sea:[[11.5,60.0],[12.3,52.0]]},
    vizag:  {n:'Visakhapatnam',ll:[17.69,83.29], sea:[[10.0,82.6],[6.3,82.2],[5.6,80.6],[7.5,76.5],[11.5,60.0],[12.3,52.0]]},
    haldia: {n:'Haldia',       ll:[22.03,88.06], sea:[[20.2,88.2],[14.0,85.5],[8.5,82.6],[6.3,82.2],[5.6,80.6],[7.5,76.5],[11.5,60.0],[12.3,52.0]]}
  };
  const inPort = ([lat, lon]) => lon >= 80.5 ? (lat > 21 ? IN_PORTS.haldia : IN_PORTS.vizag) : (lat < 13 ? IN_PORTS.kochi : IN_PORTS.nhava);
  /* QA pass: waypoints moved off land (south of Sri Lanka, Sicily channel, Alboran Sea, Bahamas channels,
     Anegada Passage, Gulf of Panama, off Costa Rica); US ports moved to their container terminals with a harbour-mouth waypoint */
  const SUEZ = [[12.6,43.4],[20.0,38.6],[27.6,33.9],[29.0,32.85],[29.95,32.56],[31.4,32.35],[33.8,26.0],[36.3,15.2],[37.4,11.3],[37.75,9.5],[37.3,1.0],[36.3,-2.2],[35.95,-5.6]];
  const US_PORTS = {
    nyc: {n:'New York / NJ', ll:[40.67,-74.08], sea:[[38.5,-40],[40.3,-70.5],[40.42,-73.85]]},
    sav: {n:'Savannah',      ll:[32.08,-81.09], sea:[[34,-40],[31.9,-79.5],[32.03,-80.85]]},
    hou: {n:'Houston',       ll:[29.68,-95.00], sea:[[29,-40],[26.2,-76.6],[25.85,-77.0],[26.1,-78.3],[25.9,-79.3],[24.3,-81.5],[25.5,-87],[28.6,-93.5],[29.35,-94.72]]},
    lax: {n:'Los Angeles',   ll:[33.72,-118.26], sea:[[22,-40],[18.45,-63.9],[12.5,-76.0],[9.38,-79.92],[8.93,-79.56],[7.0,-79.6],[6.6,-81.0],[9.8,-88.5],[14.5,-98],[22.5,-110.8],[30.0,-117.5]]}
  };
  const WEST = 'CA OR WA NV AZ UT ID HI AK CO NM MT WY'.split(' '), GULF = 'TX LA OK AR KS MS'.split(' '), SE = 'GA FL SC NC AL TN'.split(' ');
  const usPortKey = st => { st = (st || '').toUpperCase(); return WEST.includes(st) ? 'lax' : GULF.includes(st) ? 'hou' : SE.includes(st) ? 'sav' : 'nyc'; };
  const flip = ([lat, lon]) => [lon, lat];
  const dms = (lat, lon) => {
    const f = (v, p, n) => { const a = Math.abs(v); let d = Math.floor(a), m = Math.round((a - d) * 60); if (m === 60) { d++; m = 0; } return d + '°' + String(m).padStart(2, '0') + '′' + (v >= 0 ? p : n); };
    return f(lat, 'N', 'S') + ' ' + f(lon, 'E', 'W');
  };
  const routeFor = (b, city) => {
    const o = inLL(city) || [22.5, 79.0], ip = inPort(o), key = usPortKey(b.hq_state), up = US_PORTS[key];
    return {key, ip, up, hq: usLL(b), o, sea: [ip.ll, ...ip.sea, ...SUEZ, ...up.sea, up.ll],
            via: key === 'lax' ? ['Suez Canal', 'Panama Canal'] : ['Suez Canal']};
  };
  let world = null;
  const loadWorld = async () => {
    if (world) return world;
    const topo = await (await fetch('https://cdn.jsdelivr.net/npm/world-atlas@2.0.2/countries-110m.json')).json();
    world = topojson.feature(topo, topo.objects.countries).features;
    return world;
  };
  /* base chart: shoal band, land (India + US lifted), graticule */
  const baseSvg = (path, feats) => {
    const shoal = feats.map(f => { const d = path(f); return d ? `<path d="${d}"/>` : ''; }).join('');
    const land = feats.map(f => { const d = path(f); return d ? `<path d="${d}"${f.id === '356' || f.id === '840' ? ' class="home"' : ''}/>` : ''; }).join('');
    return `<g class="m-shoal">${shoal}</g><g class="m-land">${land}</g><path class="m-grat" d="${path(d3.geoGraticule().step([10, 10])())}"/>`;
  };
  /* densify a waypoint list along great circles and project it, so path lengths are exact on screen */
  const screenLine = (pts, proj, steps = 24) => {
    const out = [];
    for (let i = 0; i < pts.length - 1; i++) {
      const it = d3.geoInterpolate(flip(pts[i]), flip(pts[i + 1]));
      for (let s = 0; s < steps; s++) out.push(proj(it(s / steps)));
    }
    out.push(proj(flip(pts[pts.length - 1])));
    return out;
  };
  const toD = xy => 'M' + xy.map(p => p[0].toFixed(1) + ',' + p[1].toFixed(1)).join('L');
  window.EPGeo = {inLL, usLL, inPort, usPortKey, US_PORTS, IN_PORTS, SUEZ, flip, dms, routeFor, loadWorld, baseSvg, screenLine, toD};
})();
