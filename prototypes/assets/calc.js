/* JavaScript copies of the app's business logic, for the static prototypes only.
   Mirrors calculate_cost() and _build_templates() in export_buyer_engine.py line for line;
   the live app keeps using the Python versions. */
(() => {
  const USD_TO_INR = 95.00, FREIGHT = 8.0, AGENT = 5.0;
  /* Python's round() and format() round exact halves to even; JS rounds them up. Match Python. */
  /* Works on the exact decimal digits of the double (toFixed is exact), like Python does. */
  const roundHE = (n, d = 0) => {
    const neg = n < 0, s = Math.abs(n).toFixed(d + 30);
    const [ip, fp] = s.split('.');
    const keep = ip + fp.slice(0, d), rest = fp.slice(d);
    let up = rest[0] > '5' || (rest[0] === '5' && /[1-9]/.test(rest.slice(1)));
    if (rest[0] === '5' && !/[1-9]/.test(rest.slice(1))) up = Number(keep[keep.length - 1]) % 2 === 1;
    const v = (BigInt(keep) + (up ? 1n : 0n)).toString().padStart(d + 1, '0');
    const out = Number(d ? v.slice(0, -d) + '.' + v.slice(-d) : v);
    return neg ? -out : out;
  };
  const fixed = (n, d) => roundHE(n, d).toFixed(d);
  const r2 = n => roundHE(n, 2);
  const r1 = n => roundHE(n, 1);
  const MON = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const fmtDate = s => { const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s || ''); return m ? `${m[3]} ${MON[+m[2] - 1]} ${m[1]}` : s; };
  const money0 = n => roundHE(n).toLocaleString('en-US');
  const g = n => String(+n);  /* python {:g} for duty like 3.2 / 6 */

  const calculateCost = (b, fob) => {
    const mult = 1 + b.us_duty_pct / 100 + FREIGHT / 100;
    const comp = b.competitor_fob_usd * mult, you = fob * mult, spu = comp - you;
    return {
      buyer_id: b.id, us_buyer: b.us_buyer, hs_code: b.hs_code, product_spec: b.product_spec, us_duty_pct: b.us_duty_pct,
      competitor_fob_usd: r2(b.competitor_fob_usd), competitor_landed_usd: r2(comp), your_fob_usd: r2(fob),
      your_landed_usd: r2(you), savings_per_unit_usd: r2(spu), annual_savings_10k_usd: r2(spu * 10000),
      landed_savings_pct: r1(spu / comp * 100), agent_commission_saved_inr: r2(b.est_annual_usd * AGENT / 100 * USD_TO_INR)
    };
  };

  const buildTemplates = (b, factory, city, fob) => {
    const c = calculateCost(b, fob), arrival = fmtDate(b.last_arrival_date);
    const hq = b.hq_state ? `${b.hq_city}, ${b.hq_state}` : b.hq_city, pct = c.landed_savings_pct;
    let hook, priceLine, dm;
    if (pct > 0) {
      hook = `${fixed(pct, 0)}% lower landed cost`;
      priceLine = `That is ${fixed(pct, 1)}% below your current landed cost — about $${money0(c.annual_savings_10k_usd)} a year on 10,000 units — before you remove the 5–8% buying-agent commission.`;
      dm = `about ${fixed(pct, 0)}% below your current landed cost`;
    } else {
      hook = 'direct factory pricing';
      priceLine = 'Buying direct also removes the 5–8% buying-agent commission from every order.';
      dm = 'direct from the factory with no agent commission';
    }
    return {
      cold_email_subject: `HS ${b.hs_code} ${b.product_spec}: ${hook} for ${b.us_buyer}`,
      cold_email_body: `Dear ${b.decision_maker_role},\n\nUS Customs bill-of-lading records show ${b.us_buyer} cleared ${b.containers_12m} containers under HS ${b.hs_code} in the last 12 months (~$${money0(b.est_annual_usd)}), with the most recent arrival on ${arrival}.\n\nI’m writing from ${factory} in ${city}, India. We manufacture ${b.product_spec} for direct export, and our quote is $${c.your_fob_usd.toFixed(2)}/unit FOB. Landed in the US that is $${c.your_landed_usd.toFixed(2)}/unit against roughly $${c.competitor_landed_usd.toFixed(2)}/unit on your current supply (${g(b.us_duty_pct)}% duty + 8% freight & insurance included).\n\n${priceLine}\n\nCould I send a complimentary sample box to your ${b.hq_city} office this week? A 10-minute call is enough to confirm specifications.\n\nBest regards,\n${factory}\n${city}, India`,
      followup_subject: `Complimentary DHL sample box for ${b.us_buyer} — ready to ship to ${b.hq_city}`,
      followup_body: `Hi,\n\nFollowing up on my note about HS ${b.hs_code} ${b.product_spec}. We would like to send a complimentary pre-production sample box to your ${hq} headquarters by DHL Express, at our cost.\n\nThe box includes:\n• 3–5 pre-production samples of ${b.product_spec}\n• A side-by-side spec sheet comparing our materials, construction and finish against your current HS ${b.hs_code} supply\n• Our FOB price sheet ($${c.your_fob_usd.toFixed(2)}/unit) with the landed-cost breakdown ($${c.your_landed_usd.toFixed(2)} vs $${c.competitor_landed_usd.toFixed(2)}/unit)\n• Factory audit and compliance documents\n\nReply with the best shipping contact and it leaves ${city} within 48 hours (2–3 business days to ${b.hq_city}).\n\nBest regards,\n${factory}\n${city}, India`,
      linkedin_whatsapp: `Hi — US Customs data shows ${b.us_buyer} brought in ${b.containers_12m} containers of HS ${b.hs_code} ${b.product_spec} over the last 12 months, most recently on ${arrival}. We make the same product at ${factory} in ${city} and can land it at $${c.your_landed_usd.toFixed(2)}/unit, ${dm}. Can I send a complimentary DHL sample box to your ${b.hq_city} team this week?`,
      engine: 'template'
    };
  };

  window.EPCalc = {calculateCost, buildTemplates, fmtDate, USD_TO_INR};
})();
