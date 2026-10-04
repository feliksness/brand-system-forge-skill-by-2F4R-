// forge_lib.js — shared helpers for production modules written in Node.
//   const F = require(path.join(__dirname, '..', '..', '..', 'scripts', 'forge_lib.js'));
//   const b = F.load(repo);  b.p, b.G, b.name, b.dna, b.profile, b.content, b.labels, b.pal, b.role, b.theme, b.dark,
//                            b.tokens, b.colors, b.mark, b.parts, b.logoType, b.fonts, b.stacks, b.langs, b.lang, b.path(...)
//   F.page(b, title, bodyHtml, at)  → full file://-safe HTML wired to fonts/tokens/core + JS data (at = repo-relative folder)
//   await F.shots([{in, out, w, h, scale, transparent, full, selector, pdf, reducedMotion, theme}])   (one browser for all)
//   F.launch()  → Playwright Chromium (robust resolution, see _pw.js)
const fs = require('fs'), path = require('path');
const { launch } = require('./_pw.js');
const J = (p, d = {}) => (fs.existsSync(p) ? JSON.parse(fs.readFileSync(p, 'utf8')) : d);
function load(repo) {
  repo = path.resolve(repo); const R = (...x) => path.join(repo, ...x);
  const C = J(R('SOURCE', 'CONFIG', 'brand.config.json')), br = C.brand, colors = J(R('COLORS', 'colors.json'));
  const pal = Object.fromEntries(C.palette.map(p => [p.key, p.hex])), roles = C.roles;
  const profile = J(R('SOURCE', 'CONFIG', 'profile.json')), content = J(R('SOURCE', 'CONFIG', 'content.json')), parts = J(R('SOURCE', 'JSON', 'logo-parts.json'));
  const b = {
    repo, config: C, brand: br, name: br.name, p: br.prefix || 'bx', G: br.global || 'BX', dna: J(R('SOURCE', 'CONFIG', 'design-dna.json')),
    profile, content, labels: Object.assign({}, profile.labels || {}, content.labels || {}), tokens: J(R('SOURCE', 'JSON', 'design-tokens.json')), colors,
    theme: (colors.themes || {}).light || {}, dark: (colors.themes || {}).dark || {}, pal,
    role: Object.fromEntries(['primary', 'foundation', 'paper', 'accent'].filter(k => pal[roles[k]]).map(k => [k, pal[roles[k]]])),
    mark: J(R('SOURCE', 'JSON', 'mark.json')), parts, logoType: parts.logo_type || C.logo.type || 'symbol',
    fonts: Object.fromEntries((C.fonts.families || []).map(f => [f.role, f.family])), stacks: C.fonts.stacks || {},
    langs: br.languages || ['en'], lang: br.primary_language || (br.languages || ['en'])[0],
  };
  b.path = (...x) => path.join(repo, ...x);
  b.rel = (at, target) => path.relative(b.path(at), b.path(target)).split(path.sep).join('/');
  return b;
}
const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
function page(b, title, body, at, o = {}) {
  const scripts = o.scripts || ['mark-data.js', 'wordmark-data.js', 'dna-data.js', 'content-data.js', '{p}-mark.js'];
  const js = scripts.map(s => s.replace('{p}', b.p)).filter(s => fs.existsSync(b.path('SOURCE', 'JS', s))).map(s => `<script src="${b.rel(at, 'SOURCE/JS/' + s)}"></script>`).join('');
  return `<!doctype html><html lang="${o.lang || b.lang}"${o.theme ? ` data-theme="${o.theme}"` : ''}><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">` +
    `<title>${esc(title)} — ${esc(b.name)}</title><link rel="stylesheet" href="${b.rel(at, `SOURCE/CSS/${b.p}-core.css`)}">${o.head || ''}</head><body class="${o.bodyClass || ''}">${body}${js}${o.tail || ''}</body></html>`;
}
const svg = (b, name) => { const p = b.path('LOGO', 'SVG', name + '.svg'); return fs.existsSync(p) ? fs.readFileSync(p, 'utf8') : ''; };
function write(p, text) { fs.mkdirSync(path.dirname(path.resolve(p)), { recursive: true }); fs.writeFileSync(p, text); }
async function shots(jobs) {
  if (!jobs.length) return; const br = await launch();
  for (const j of jobs) {
    const pg = await br.newPage({ viewport: { width: +(j.w || 1280), height: +(j.h || 800) }, deviceScaleFactor: +(j.scale || 1) });
    if (j.reducedMotion || j.theme) await pg.emulateMedia({ reducedMotion: j.reducedMotion ? 'reduce' : 'no-preference', colorScheme: j.theme === 'dark' ? 'dark' : 'light' });
    try {
      await pg.goto(/^(https?|file):/.test(j.in) ? j.in : 'file://' + path.resolve(j.in), { waitUntil: 'load' });
      await pg.evaluate(() => document.fonts && document.fonts.ready); await pg.waitForTimeout(j.wait == null ? 250 : j.wait);
      fs.mkdirSync(path.dirname(path.resolve(j.out)), { recursive: true });
      if (j.pdf) await pg.pdf({ path: j.out, width: (j.w || 1280) + 'px', height: (j.h || 800) + 'px', printBackground: true, preferCSSPageSize: !!j.cssPage });
      else if (j.selector) await (await pg.$(j.selector)).screenshot({ path: j.out, omitBackground: !!j.transparent });
      else await pg.screenshot({ path: j.out, omitBackground: !!j.transparent, fullPage: !!j.full });
    } catch (e) { console.error('shot failed', j.in, e.message.split('\n')[0]); }
    await pg.close();
  }
  await br.close();
}
function categorical(b, n = 8, theme = 'light') {
  const ch = J(b.path('SOURCE', 'JSON', 'charts.json')); const cat = ((ch.themes || {})[theme] || {}).categorical;
  if (cat) return cat.map(c => (typeof c === 'object' ? c.hex : c)).slice(0, n);
  const pr = (b.colors.ramps || {}).primary || {};
  const out = [b.role.primary, b.role.accent, ...b.config.palette.filter(p => p.group === 'secondary').map(p => p.hex), ...['800', '400', '600', '300', '900', '200'].map(s => pr[s])];
  const seen = []; out.forEach(c => { if (c && !seen.some(s => s.toUpperCase() === c.toUpperCase())) seen.push(c); }); return seen.slice(0, n);
}
module.exports = { load, page, svg, write, shots, launch, esc, categorical };
