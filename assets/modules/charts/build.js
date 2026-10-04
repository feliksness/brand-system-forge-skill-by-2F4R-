#!/usr/bin/env node
/* charts module — brand-system-forge
   node build.js --repo <BRAND-REPO> [--no-previews]
   Writes SOURCE/JS/<p>-charts.js, SOURCE/CSS/<p>-charts.css, SOURCE/JSON/charts.json and DATA-VIZ/ (demo, rules, previews).
   Skips (exit 0) when profile.modules.charts is false or profile.dataviz is empty. */
'use strict';
const fs = require('fs'), path = require('path');
const F = require(path.join(__dirname, '..', '..', '..', 'scripts', 'forge_lib.js'));
const K = require('./lib/color.js'), css = require('./lib/css.js'), docs = require('./lib/docs.js');
const T0 = Date.now();
const argv = process.argv.slice(2), arg = k => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : null; };
const repo = arg('--repo'); if (!repo) { console.error('usage: node build.js --repo <brand-repo> [--no-previews]'); process.exit(2); }
const b = F.load(repo), p = b.p, G = b.G, dna = b.dna, esc = F.esc, prof = b.profile || {};
const dv = prof.dataviz || [];
if ((prof.modules && prof.modules.charts === false) || !dv.length) { console.log(`charts: skipped — profile "${prof.key || '?'}" has ${prof.modules && prof.modules.charts === false ? 'charts disabled' : 'no dataviz list'}`); process.exit(0); }

/* ---------------------------------------------------------------- 1. palette per theme */
const ramps = (b.colors.ramps || {}), pr = ramps.primary || {}, ac = ramps.accent || {}, ne = ramps.neutral || {};
const order = F.categorical(b, 8);
const th = { light: b.theme, dark: b.dark, contrast: (b.colors.themes || {}).contrast || b.dark };
const surf = t => [th[t].background, th[t].surface].filter(h => /^#[0-9A-F]{6}$/i.test(h || ''));
const pick = (r, steps) => steps.map(s => r[s]).filter(Boolean);
function ink(fill, t) { const a = th[t]['text-primary'] || '#111111', bb = t === 'light' ? '#FFFFFF' : (th[t]['text-inverse'] || '#111111'); return K.contrast(fill, a) >= K.contrast(fill, bb) ? a : bb; }
function theme(t) {
  const extra = t === 'light' ? [b.role.foundation, ac['700'], ne['600'], ac['500'], ne['400']] : [b.role.paper, ac['200'], pr['100'], ne['300'], ac['400'], ne['500']];
  const cat = K.buildTheme(order, surf(t), { primary: pr, accent: ac, neutral: ne }, extra, 6, b.role.foundation);
  const seq = t === 'light' ? pick(pr, ['100', '200', '300', '500', '700', '900']) : pick(pr, ['900', '800', '600', '500', '300', '100']);
  const ord = t === 'light' ? pick(pr, ['800', '700', '600', '500', '400', '300']) : pick(pr, ['200', '300', '400', '500', '600', '700']);
  const div = t === 'light' ? [...pick(ac, ['700', '500', '300']), ne['200'], ...pick(pr, ['300', '500', '700'])] : [...pick(ac, ['200', '400', '600']), ne['700'], ...pick(pr, ['600', '400', '200'])];
  return { cat, seq, ord, div: div.filter(Boolean), muted: t === 'light' ? (ne['300'] || '#BBBBBB') : (ne['600'] || '#555555'), ordInk: ord.map(c => ink(c, t)), seqInk: seq.map(c => ink(c, t)), ink1: ink(cat[0].hex, t), surfaces: surf(t) };
}
const P = { light: theme('light'), dark: theme('dark'), contrast: theme('contrast') };
const slots = Math.min(P.light.cat.length, P.dark.cat.length);
const corner = (dna.corner || {}).style || 'square', base = dna.base_language || 'mixed', stroke = dna.stroke || {};
const cfg = {
  lang: b.lang, corner, angle: (dna.angles || {}).cut || dna.corner.angle_deg || 45, cap: stroke.cap || 'round', join: stroke.join || 'round', base,
  marker: corner === 'cut' ? (dna.complexity === 'faceted' ? 'diamond' : 'square') : corner === 'square' ? 'square' : 'circle',
  smooth: ['round', 'organic', 'mixed'].includes(base), character: (dna.motion || {}).character || 'glide', slots,
  palette: { light: P.light.cat.slice(0, slots).map(s => s.hex), dark: P.dark.cat.slice(0, slots).map(s => s.hex) },
  texture: P.light.cat.slice(0, slots).map(s => !!(s.texture || s.relief)), words: docs.words(b.lang)
};
const Kc = { character: cfg.character, corner, cap: cfg.cap === 'square' ? 'square' : cfg.cap === 'butt' ? 'butt' : 'round', join: cfg.join === 'miter' ? 'miter' : 'round', ruleW: stroke.rule_px || 1,
  light: Object.assign({}, P.light, { cat: P.light.cat.slice(0, slots) }), dark: Object.assign({}, P.dark, { cat: P.dark.cat.slice(0, slots) }), contrast: Object.assign({}, P.contrast, { cat: P.contrast.cat.slice(0, slots) }) };

/* ---------------------------------------------------------------- 2. runtime files (DATA-VIZ/ is owned by this module and rewritten) */
fs.rmSync(b.path('DATA-VIZ'), { recursive: true, force: true });
const tpl = fs.readFileSync(path.join(__dirname, 'templates', 'charts.js'), 'utf8')
  .replace(/__G__/g, G).replace(/__P__/g, p).replace(/__NAME__/g, b.name).replace(/__CORNER__/g, corner).replace(/__CAP__/g, cfg.cap).replace(/__JOIN__/g, cfg.join).replace(/__CHARACTER__/g, cfg.character)
  .replace('__CFG__', () => JSON.stringify(cfg));
F.write(b.path('SOURCE', 'JS', `${p}-charts.js`), tpl);
F.write(b.path('SOURCE', 'CSS', `${p}-charts.css`), css(b, Kc));
F.write(b.path('SOURCE', 'JSON', 'charts.json'), JSON.stringify({
  note: 'Chart palette generated by the charts module from the forge categorical order (primary, accent, secondary, ramp), snapped to >= 3:1 on each theme surface. Regenerate; do not edit.',
  order_source: order, slots, themes: Object.fromEntries(['light', 'dark', 'contrast'].map(t => [t, { surfaces: P[t].surfaces, categorical: P[t].cat.slice(0, slots), sequential: P[t].seq, ordinal: P[t].ord, diverging: P[t].div }])),
  dna: { corner, marker: cfg.marker, smooth: cfg.smooth, cap: cfg.cap, join: cfg.join, motion: cfg.character }, dataviz: dv
}, null, 2));

/* ---------------------------------------------------------------- 3. sample data (deterministic) */
let seed = 0; for (const ch of b.name) seed = (seed * 31 + ch.charCodeAt(0)) >>> 0;
const rnd = () => { seed = (seed + 0x6D2B79F5) >>> 0; let t = seed; t = Math.imul(t ^ (t >>> 15), 1 | t); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
const c = b.content || {}, units = (c.units || []).map(u => u.name), offers = (c.offerings || []).map(o => o.name), L = b.labels || {};
const months = Array.from({ length: 12 }, (_, i) => new Intl.DateTimeFormat(b.lang, { month: 'short' }).format(new Date(Date.UTC(2026, i, 15))));
const cats = (units.length >= 3 ? units : offers).slice(0, 5); while (cats.length < 4) cats.push(['North', 'South', 'East', 'West', 'Central'][cats.length]);
const series = cats.slice(0, 3);
const walk = (n, start, drift, noise) => { let v = start; return Array.from({ length: n }, () => { v = Math.max(1, v + drift + (rnd() - 0.45) * noise); return Math.round(v); }); };
const toNum = s => parseFloat(String(s).replace(/,/g, '')) || 0;
const stats = (c.stats || []).slice(0, 4);
const pctStat = stats.find(s => s.unit === '%');
const years = [2023, 2024, 2025, 2026].map(String);
const D = {
  line: { x: months, series: series.map((s, i) => ({ name: s, values: walk(12, 40 + i * 18 + rnd() * 10, 2.2 - i * 0.5, 9) })) },
  bar: { data: cats.map(n => [n, Math.round(30 + rnd() * 70)]) },
  stacked: { categories: years, series: series.map((s, i) => ({ name: s, values: years.map((y, j) => Math.round((30 - i * 6) * (1 + j * 0.18) + rnd() * 8)) })) },
  grouped: { categories: years.slice(1), series: series.slice(0, 2).map((s, i) => ({ name: s, values: [0, 1, 2].map(j => Math.round(40 + j * 9 + i * 12 + rnd() * 10)) })) },
  donut: { data: (offers.length >= 3 ? offers : cats).slice(0, 4).map((n, i) => [n, Math.round([38, 27, 21, 14][i] + rnd() * 4)]) },
  gauge: { value: pctStat ? toNum(pctStat.value) : 72, label: pctStat ? pctStat.label : 'Target reached' },
  progress: (offers.length ? offers : cats).slice(0, 3).map((n, i) => ({ label: n, value: Math.round(86 - i * 19 + rnd() * 6), max: 100, target: 80 })),
  events: (c.events || []).map(e => ({ date: e.date, label: e.name || e.title || '', note: e.place || e.location || '' })).filter(e => e.date),
  table: cats.map((n, i) => [n, Math.round(120 + rnd() * 880), +(rnd() * 24 - 6).toFixed(1), walk(8, 20 + rnd() * 10, 1.2, 6)]),
  funnel: [['Visits', 12400], ['Enquiries', 3100], ['Proposals', 940], ['Clients', 310]].map((x, i) => [x[0], Math.round(x[1] * (0.85 + rnd() * 0.3))]),
  process: [{ label: 'Listen', text: 'Brief and goals' }, { label: 'Plan', text: 'Scope and timeline' }, { label: 'Deliver', text: 'Build and test' }, { label: 'Review', text: 'Measure and improve' }],
  map: 'ABCDEFGHIJKL'.split('').map((l, i) => ({ name: 'Region ' + l, code: l, value: Math.round(10 + rnd() * 90), col: [1, 2, 3, 0, 1, 2, 3, 4, 1, 2, 3, 2][i], row: [0, 0, 0, 1, 1, 1, 1, 1, 2, 2, 2, 3][i] })),
  compare: stats.length >= 2 ? null : null
};
if (!D.events.length) D.events = [{ date: '2026-03-12', label: 'Kick-off' }, { date: '2026-06-04', label: 'Milestone' }, { date: '2026-10-20', label: 'Launch' }];
const ev0 = D.events[0].date.split('-').map(Number);
D.calendar = { year: ev0[0], month: ev0[1], events: D.events.filter(e => e.date.startsWith(ev0[0] + '-' + String(ev0[1]).padStart(2, '0'))), values: {} };
for (let d = 1; d <= 28; d++) { const dt = new Date(Date.UTC(ev0[0], ev0[1] - 1, d)); if (dt.getUTCDay() % 6) D.calendar.values[`${ev0[0]}-${String(ev0[1]).padStart(2, '0')}-${String(d).padStart(2, '0')}`] = Math.round(rnd() * 40 + 5); }
D.kpis = (stats.length ? stats : [{ label: 'Index', value: '100', unit: '' }]).map((s, i) => ({ label: s.label, value: s.value, unit: s.unit && s.unit.length > 1 ? s.unit : (s.unit || ''), delta: { value: +(rnd() * 12 - 3).toFixed(1), unit: '%', good: /injury|wait|incident|cost|error/i.test(s.label) ? 'down' : 'up', period: 'vs 2025' }, trend: walk(10, 20 + rnd() * 10, 1.4, 6) }));
D.org = { name: b.name, role: (c.people || [])[0] ? (c.people[0].role || '') : '', children: (c.people || []).slice(1, 4).map((pp, i) => ({ name: pp.name, role: pp.role, children: units.slice(i * 2, i * 2 + 2).map(u => ({ name: u, role: L.units ? L.units.replace(/s$/, '') : '' })) })) };
if ((c.people || [])[0]) D.org = { name: c.people[0].name, role: c.people[0].role, children: D.org.children };
D.compare = stats.filter(s => s.unit === '%').length ? [[stats.find(s => s.unit === '%').label, toNum(stats.find(s => s.unit === '%').value)], ['Sector average (sample)', Math.round(toNum(stats.find(s => s.unit === '%').value) * 0.72)]] : [[cats[0], 78], [cats[1], 54]];

/* ---------------------------------------------------------------- 4. demo page */
const sampleNote = 'Sample data — replace with real figures';
const titles = docs.titles(b, D, L);
const blocks = {
  kpi: { title: 'KPI cards', js: `D.kpis.forEach(function(k,i){var h=document.getElementById('kpi-'+i);if(h)C.kpi(h,Object.assign({sample:${!!c._sample}},k));});`, html: `<div class="dv-kpis">${D.kpis.map((k, i) => `<div id="kpi-${i}"></div>`).join('')}</div>`, wide: true, note: `From content.json stats${c._sample ? ' (sample content)' : ''}; deltas and trends are sample data.` },
  line: { title: titles.line, js: `C.line('#c-line',{title:${JSON.stringify(titles.line)},subtitle:'Monthly index, ${years[3]}',x:D.line.x,series:D.line.series,sample:true,source:${JSON.stringify(sampleNote)}});`, id: 'c-line', wide: true },
  area: { title: titles.area, js: `C.area('#c-area',{title:${JSON.stringify(titles.area)},subtitle:'Monthly volume',x:D.line.x,series:[D.line.series[0]],sample:true,source:${JSON.stringify(sampleNote)}});`, id: 'c-area' },
  bar: { title: titles.bar, js: `C.bar('#c-bar',{title:${JSON.stringify(titles.bar)},subtitle:'By ${(L.units || 'unit').toLowerCase()}',data:D.bar.data,sample:true,source:${JSON.stringify(sampleNote)}});`, id: 'c-bar' },
  'bar-h': { title: titles.barh, js: `C.bar('#c-barh',{title:${JSON.stringify(titles.barh)},orientation:'horizontal',data:D.bar.data.slice().sort(function(a,b){return b[1]-a[1];}),sample:true,source:${JSON.stringify(sampleNote)}});`, id: 'c-barh' },
  'stacked-bar': { title: titles.stacked, js: `C.bar('#c-stacked',{title:${JSON.stringify(titles.stacked)},subtitle:'Per year, stacked',categories:D.stacked.categories,series:D.stacked.series,mode:'stacked',sample:true,source:${JSON.stringify(sampleNote)}});`, id: 'c-stacked' },
  grouped: { title: titles.grouped, js: `C.bar('#c-grouped',{title:${JSON.stringify(titles.grouped)},categories:D.grouped.categories,series:D.grouped.series,mode:'grouped',sample:true,source:${JSON.stringify(sampleNote)}});`, id: 'c-grouped' },
  percent: { title: titles.percent, js: `C.bar('#c-percent',{title:${JSON.stringify(titles.percent)},orientation:'horizontal',categories:D.stacked.categories,series:D.stacked.series,mode:'percent',sample:true,source:${JSON.stringify(sampleNote)}});`, id: 'c-percent' },
  donut: { title: titles.donut, js: `C.donut('#c-donut',{title:${JSON.stringify(titles.donut)},data:D.donut.data,center:{value:C.format(D.donut.data.reduce(function(s,d){return s+d[1];},0)),label:'Total'},sample:true,source:${JSON.stringify(sampleNote)}});`, id: 'c-donut' },
  pie: { title: 'Share (pie)', js: `C.pie('#c-pie',{title:'Share (pie)',data:D.donut.data.slice(0,3),sample:true,source:${JSON.stringify(sampleNote)}});`, id: 'c-pie' },
  gauge: { title: titles.gauge, js: `C.gauge('#c-gauge',{title:${JSON.stringify(titles.gauge)},value:D.gauge.value,min:0,max:100,display:C.format(D.gauge.value,{unit:'%',decimals:0}),label:D.gauge.label,sample:true,source:${JSON.stringify(sampleNote)}});`, id: 'c-gauge' },
  progress: { title: titles.progress, js: `C.progress('#c-progress',{title:${JSON.stringify(titles.progress)},subtitle:'Target marked at 80 %',items:D.progress,unit:'%',sample:true,source:${JSON.stringify(sampleNote)}});`, id: 'c-progress' },
  table: { title: titles.table, js: `C.table('#c-table',{title:${JSON.stringify(titles.table)},columns:['${esc(L.units || 'Unit')}','Volume','Change','Trend'],rows:D.table,bars:1,spark:3,units:{2:'%'},decimals:{2:1},sample:true,source:${JSON.stringify(sampleNote)}});`, id: 'c-table', wide: true },
  timeline: { title: titles.timeline, js: `C.timeline('#c-timeline',{title:${JSON.stringify(titles.timeline)},data:D.events,sample:${!!c._sample},source:'content.json events'});`, id: 'c-timeline', wide: true },
  funnel: { title: titles.funnel, js: `C.funnel('#c-funnel',{title:${JSON.stringify(titles.funnel)},data:D.funnel,sample:true,source:${JSON.stringify(sampleNote)}});`, id: 'c-funnel' },
  sparkline: { title: 'Sparklines', js: `D.table.forEach(function(r,i){var h=document.getElementById('sp-'+i);if(h)C.sparkline(h,{data:r[3],width:160,height:40,area:true,label:r[0]});});`, html: `<div class="dv-sparks">${D.table.map((r, i) => `<div><span class="${p}-small">${esc(r[0])}</span><span id="sp-${i}"></span></div>`).join('')}</div>`, note: 'Inline trend; last value marked in the primary data colour.' },
  process: { title: titles.process, js: `C.process('#c-process',{title:${JSON.stringify(titles.process)},steps:D.process,sample:true});`, id: 'c-process', wide: true },
  calendar: { title: titles.calendar, js: `C.calendar('#c-calendar',{title:${JSON.stringify(titles.calendar)},year:D.calendar.year,month:D.calendar.month,events:D.calendar.events,values:D.calendar.values,sample:true,source:'Events from content.json; attendance is sample data'});`, id: 'c-calendar' },
  'map-placeholder': { title: titles.map, js: `C.map('#c-map',{title:${JSON.stringify(titles.map)},subtitle:'Schematic tiles — replace with real geography',regions:D.map,cols:5,sample:true,source:${JSON.stringify(sampleNote)}});`, id: 'c-map' },
  'org-chart': { title: titles.org, js: `C.org('#c-org',{title:${JSON.stringify(titles.org)},root:D.org,sample:${!!c._sample}});`, id: 'c-org', wide: true }
};
const ALL = ['kpi', 'line', 'bar', 'stacked-bar', 'bar-h', 'grouped', 'percent', 'area', 'donut', 'pie', 'gauge', 'progress', 'table', 'timeline', 'funnel', 'sparkline', 'process', 'calendar', 'map-placeholder'];
// pack: a half-width card followed by a wide one pulls the next half-width card forward so rows stay full
function pack(list) { const out = [], rest = list.slice(); let open = false; while (rest.length) { let i = 0; if (open && blocks[rest[0]].wide) { const j = rest.findIndex(k => !blocks[k].wide); if (j > 0) i = j; } const k = rest.splice(i, 1)[0]; out.push(k); open = blocks[k].wide ? false : !open; } return out; }
const yours = pack(dv.filter(k => blocks[k]));
const more = pack(ALL.filter(k => !dv.includes(k)));
const orgWanted = dv.includes('org-chart') || ['nonprofit-ngo', 'professional-services'].includes(prof.key);
function orphans(list) { const o = new Set(); let open = null; list.forEach(k => { if (blocks[k].wide) { if (open) o.add(open); open = null; } else open = open ? null : k; }); if (open) o.add(open); return o; }
const ORPH = new Set([...orphans(yours), ...orphans(more)]);
const card = k => { const B = blocks[k]; return `<article class="dv-card${B.wide || ORPH.has(k) ? ' dv-card--wide' : ''}" data-type="${k}">${B.id ? `<div id="${B.id}"></div>` : `<h3 class="${p}-chart__title" style="margin-bottom:var(--space-4)">${esc(B.title)}</h3>${B.html}`}${B.note ? `<p class="dv-note">${esc(B.note)}</p>` : ''}<details class="dv-code"><summary>Code</summary><code>${esc(B.js.replace(/D\.[a-z.]+/gi, m => m).slice(0, 400))}</code></details></article>`; };
const AT = 'DATA-VIZ';
const sw = t => P[t].cat.slice(0, slots).map((s, i) => `<li><span class="dv-sw" style="background:${s.hex}"></span><span><b>${i + 1}</b> ${s.hex}</span><span class="dv-cr">${s.contrast}:1${s.how !== 'as is' ? ' · snapped' : ''}${s.texture ? ' · texture' : ''}</span></li>`).join('');
const ramp = (list, label) => `<div class="dv-ramp"><span class="dv-lab">${label}</span><div>${list.map(h => `<i style="background:${h}"></i>`).join('')}</div></div>`;
const statsHTML = stats.map(s => `<div class="dv-stat" data-stat='${esc(JSON.stringify({ value: s.value, unit: s.unit || '', label: s.label, icon: s.icon || null }))}'></div>`).join('');
const body = `<a class="${p}-skip-link" href="#yours">Skip to charts</a>
<main class="dv"><div class="dv-wrap">
<header class="dv-head" id="top"><div>
  <p class="dv-kicker ${p}-eyebrow"><span class="${p}-index">${dv.length}</span><span>${esc(b.name)} · Data visualisation</span></p>
  <h1 class="${p}-h1">Charts &amp; infographics</h1>
  <p class="dv-lead">${esc(`Dependency-free SVG charts (${G}.charts) styled by the design DNA: ${corner} data-ends, ${cfg.smooth ? 'smooth' : 'straight'} lines with ${cfg.cap} caps, ${cfg.marker} markers, ${cfg.character} entrance. The ${prof.title || prof.key} profile asks for ${dv.join(', ')} — shown first.`)}</p>
  <div class="dv-theme" role="radiogroup" aria-label="Theme"><label><input type="radio" name="dv-theme" value="light" checked> Light</label><label><input type="radio" name="dv-theme" value="dark"> Dark</label></div>
</div>
<div class="dv-pal"><h2 class="dv-lab">Categorical — light</h2><ol class="dv-sws">${sw('light')}</ol><h2 class="dv-lab">Categorical — dark</h2><ol class="dv-sws dv-sws--dark">${sw('dark')}</ol>
${ramp(P.light.seq, 'Sequential')}${ramp(P.light.ord, 'Ordinal')}${ramp(P.light.div, 'Diverging')}</div></header>
${c._sample || true ? `<p class="dv-banner">Every chart on this page uses <strong>sample data</strong> (labelled on each chart). Labels come from content.json; replace the numbers with real figures before publishing.</p>` : ''}
<section class="dv-sec" id="yours" aria-labelledby="h-yours"><h2 class="${p}-h2" id="h-yours">For ${esc((prof.title || prof.key || '').split(',')[0])}</h2><p class="dv-sub">The profile's dataviz list: ${dv.map(esc).join(' · ')}.${dv.filter(k => !blocks[k]).length ? ' (Not a chart type here: ' + dv.filter(k => !blocks[k]).map(esc).join(', ') + '.)' : ''}</p>
<div class="dv-grid">${yours.map(card).join('')}</div></section>
<section class="dv-sec" id="more" aria-labelledby="h-more"><h2 class="${p}-h2" id="h-more">More chart types</h2><p class="dv-sub">Available in the library for when the story needs them.</p>
<div class="dv-grid">${more.map(card).join('')}</div></section>
<section class="dv-sec" id="info" aria-labelledby="h-info"><h2 class="${p}-h2" id="h-info">Infographic blocks</h2><p class="dv-sub">Big numbers from content.json${c._sample ? ' (sample content)' : ''}, comparison bars${orgWanted ? ', organisation chart' : ''} — <code>${G}.charts.stat()</code>, <code>.compare()</code>${orgWanted ? ', <code>.org()</code>' : ''}.</p>
<div class="dv-stats">${statsHTML}</div>
<div class="dv-grid" style="margin-top:var(--space-10)"><article class="dv-card"><div id="c-compare"></div></article>${!yours.includes('process') ? `<article class="dv-card"><div id="c-process2"></div></article>` : ''}${orgWanted ? `<article class="dv-card dv-card--wide"><div id="c-org"></div></article>` : ''}</div></section>
<nav class="dv-nav"><a href="rules.md">Data-viz rules</a><a href="README.md">README</a></nav>
</div></main>`;
const head = `<link rel="stylesheet" href="../SOURCE/CSS/${p}-charts.css"><script>(function(){var q=location.search;if(/[?&]still=1/.test(q))document.documentElement.setAttribute('data-motion-still','');var m=/[?&]theme=(\\w+)/.exec(q);if(m)document.documentElement.setAttribute('data-theme',m[1]);})();</script><style>
.dv { padding-block: var(--space-12) var(--space-16); }
.dv-wrap { max-width: 1280px; margin-inline: auto; padding-inline: var(--grid-margin); }
.dv-head { display: grid; grid-template-columns: minmax(0, 1.25fr) minmax(300px, 1fr); gap: var(--space-10); padding-bottom: var(--space-10); border-bottom: var(--border-hairline) solid var(--color-border); }
.dv-kicker { display: flex; gap: .75em; margin-bottom: var(--space-4); }
.dv-lead { margin-top: var(--space-4); max-width: 62ch; color: var(--color-text-secondary); font-size: var(--type-body-l-size); line-height: var(--type-body-l-line-height); }
.dv-theme { display: inline-flex; margin-top: var(--space-6); font-size: var(--type-small-size); border: var(--border-hairline) solid var(--color-border); border-radius: var(--radius-button); overflow: hidden; }
.dv-theme label { position: relative; padding: 8px 16px; cursor: pointer; }
.dv-theme input { position: absolute; inset: 0; opacity: 0; margin: 0; cursor: pointer; }
.dv-theme label:has(input:checked) { background: var(--color-text-primary); color: var(--color-background); font-weight: 600; }
.dv-theme label:has(input:focus-visible) { outline: 2px solid var(--color-focus); outline-offset: -4px; }
.dv-lab { font-family: var(--font-mono); font-size: var(--type-label-size); letter-spacing: var(--type-label-letter-spacing); text-transform: uppercase; color: var(--color-text-secondary); font-weight: 500; margin: 0 0 var(--space-2); }
.dv-pal { display: grid; gap: var(--space-2); align-content: start; }
.dv-sws { list-style: none; margin: 0 0 var(--space-4); padding: 0; display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--space-2); font-size: var(--type-caption-size); }
.dv-sws li { display: grid; grid-template-columns: 28px 1fr; grid-template-rows: auto auto; column-gap: var(--space-2); align-items: center; }
.dv-sws .dv-sw { grid-row: span 2; width: 28px; height: 28px; border-radius: ${corner === 'round' ? '50%' : corner === 'soft' ? '6px' : '0'}; }
.dv-sws--dark { background: ${P.dark.surfaces[0]}; color: ${b.dark['text-primary'] || '#fff'}; padding: var(--space-3); }
.dv-sws--dark .dv-cr { color: ${b.dark['text-secondary'] || '#ccc'}; }
.dv-cr { color: var(--color-text-secondary); font-variant-numeric: tabular-nums; }
.dv-ramp { display: grid; grid-template-columns: 7rem 1fr; align-items: center; gap: var(--space-3); }
.dv-ramp .dv-lab { margin: 0; }
.dv-ramp div { display: flex; height: 18px; } .dv-ramp i { flex: 1; }
.dv-banner { margin: var(--space-8) 0 0; padding: var(--space-3) var(--space-4); border-left: var(--border-heavy) solid var(--color-brand-primary); background: var(--color-surface); font-size: var(--type-small-size); }
.dv-sec { margin-top: var(--space-16); }
.dv-sub { margin: var(--space-2) 0 var(--space-8); color: var(--color-text-secondary); max-width: 70ch; }
.dv-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-6); }
.dv-card { padding: var(--space-6); background: var(--color-surface); border: var(--border-hairline) solid var(--color-border-subtle); min-width: 0; }
.dv-card--wide { grid-column: 1 / -1; }
.dv-note { margin: var(--space-3) 0 0; font-size: var(--type-caption-size); color: var(--color-text-secondary); }
.dv-code { margin-top: var(--space-3); font-size: var(--type-caption-size); }
.dv-code summary { cursor: pointer; color: var(--color-text-secondary); width: max-content; }
.dv-code code { display: block; margin-top: var(--space-2); padding: var(--space-3); background: var(--color-surface-sunken); font-family: var(--font-mono); white-space: pre-wrap; word-break: break-word; }
.dv-kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: var(--space-4); }
.dv-sparks { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: var(--space-4) var(--space-6); }
.dv-sparks > div { display: flex; flex-direction: column; gap: var(--space-2); }
.dv-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: var(--space-8); }
.dv-nav { display: flex; gap: var(--space-6); margin-top: var(--space-16); padding-top: var(--space-6); border-top: var(--border-hairline) solid var(--color-border); font-size: var(--type-small-size); }
.dv-nav a { color: var(--color-text-primary); }
@media (max-width: 900px) { .dv-head, .dv-grid { grid-template-columns: 1fr; } .dv-sws { grid-template-columns: repeat(2, 1fr); } }
</style>`;
const iconJs = fs.existsSync(b.path('SOURCE', 'JS', `${p}-icons.js`)) ? `${p}-icons.js` : null;
const tail = `<script src="../SOURCE/JS/${p}-charts.js"></script><script>
var C=window.${G}.charts, D=${JSON.stringify(D)};
${[...yours, ...more].map(k => blocks[k].js).join('\n')}
document.querySelectorAll('.dv-stat').forEach(function(el){var s=JSON.parse(el.getAttribute('data-stat'));C.stat(el,{value:C.format(parseFloat(String(s.value).replace(/,/g,'')),{decimals:String(s.value).indexOf('.')>-1?String(s.value).split('.')[1].length:0}),unit:s.unit&&s.unit.length<=2?s.unit:'',label:s.label+(s.unit&&s.unit.length>2?' ('+s.unit+')':''),icon:s.icon});});
C.compare('#c-compare',{title:${JSON.stringify(titles.compare)},data:D.compare,unit:${JSON.stringify(D.compare[0] && stats.some(s => s.unit === '%') ? '%' : '')},max:100,sample:true,source:${JSON.stringify(sampleNote)}});
if(document.getElementById('c-process2'))C.process('#c-process2',{title:${JSON.stringify(titles.process)},steps:D.process,sample:true});
${orgWanted ? blocks['org-chart'].js : ''}
document.querySelectorAll('[name="dv-theme"]').forEach(function(r){r.checked=r.value===(document.documentElement.getAttribute('data-theme')||'light');r.addEventListener('change',function(){if(r.checked)document.documentElement.setAttribute('data-theme',r.value);});});
document.documentElement.setAttribute('data-ready','');
</script>`;
F.write(b.path(AT, 'index.html'), F.page(b, 'Charts & infographics', body, AT, { head, scripts: ['mark-data.js', 'dna-data.js', 'content-data.js', '{p}-mark.js'].concat(iconJs ? [iconJs.replace(p, '{p}')] : []), tail }));
F.write(b.path(AT, 'rules.md'), docs.rules(b, P, cfg, slots, dv));
F.write(b.path(AT, 'README.md'), docs.readme(b, cfg, dv, yours, more, !!c._sample));

/* ---------------------------------------------------------------- 5. previews */
(async () => {
  const jobs = [];
  if (!argv.includes('--no-previews')) {
    const u = q => 'file://' + b.path(AT, 'index.html') + q;
    jobs.push({ in: u('?still=1'), out: b.path(AT, 'previews', 'overview.png'), w: 1440, h: 900, selector: '#top', wait: 700 });
    jobs.push({ in: u('?still=1'), out: b.path(AT, 'previews', 'charts-profile.png'), w: 1440, h: 900, selector: '#yours', wait: 700 });
    jobs.push({ in: u('?still=1'), out: b.path(AT, 'previews', 'charts-more.png'), w: 1440, h: 900, selector: '#more', wait: 700 });
    jobs.push({ in: u('?still=1'), out: b.path(AT, 'previews', 'infographics.png'), w: 1440, h: 900, selector: '#info', wait: 700 });
    jobs.push({ in: u('?still=1&theme=dark'), out: b.path(AT, 'previews', 'charts-profile-dark.png'), w: 1440, h: 900, selector: '#yours', wait: 700 });
    await F.shots(jobs);
  }
  const n = jobs.length;
  console.log(`charts: ${p}-charts.js (${ALL.length + 2} types) · ${slots} categorical colours (light ${P.light.cat.slice(0, slots).filter(s => s.how !== 'as is').length} snapped) · DATA-VIZ demo (${yours.length} profile + ${more.length} more) · rules.md · ${n} previews · ${((Date.now() - T0) / 1000).toFixed(1)}s`);
})().catch(e => { console.error('charts: preview step failed —', e.message); process.exit(1); });
