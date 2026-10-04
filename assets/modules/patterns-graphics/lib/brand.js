// brand.js — reads the foundations into what the graphic engine needs:
// mark units (symbol / emblem / wordmark + monogram), colourways, type tokens, outlined glyphs, raster helper.
const fs = require('fs'), path = require('path'), vm = require('vm'), os = require('os');
const { execFileSync } = require('child_process');
const CORE = require('./graphics-core.js');
const U = CORE.util;

function loadWindow(file) {
  const sb = { window: {} }; sb.self = sb.window;
  if (fs.existsSync(file)) { try { vm.runInNewContext(fs.readFileSync(file, 'utf8'), sb); } catch (e) { /* tolerate */ } }
  return sb.window;
}

/** <path>/<polygon> elements of a standalone SVG → parts [{d, tx, ty, c}] + viewBox */
function svgParts(text) {
  const vb = (/viewBox="([^"]+)"/.exec(text) || [, '0 0 100 100'])[1].trim().split(/[\s,]+/).map(Number);
  const parts = [];
  const re = /<(path|polygon)\b([^>]*)\/?>/g; let m;
  while ((m = re.exec(text))) {
    const a = m[2], get = k => { const x = new RegExp('\\s' + k + '="([^"]*)"').exec(a); return x ? x[1] : null; };
    const fillC = get('fill'); if (fillC === 'none') continue;
    const tr = /translate\(\s*([-\d.]+)[\s,]+([-\d.]+)\s*\)/.exec(get('transform') || '');
    const d = m[1] === 'path' ? get('d') : 'M' + (get('points') || '').trim().replace(/\s+/g, ' L') + 'Z';
    if (!d) continue;
    const c = fillC && /^#/.test(fillC) ? fillC : '#000000';
    parts.push({ d, tx: tr ? +tr[1] : 0, ty: tr ? +tr[2] : 0, c, l: U.lum(c) });
  }
  return { vb, parts };
}

function markUnits(b) {
  const W = loadWindow(b.path('SOURCE', 'JS', 'mark-data.js'));
  const M = W[b.G + '_MARK'] || Object.values(W).find(v => v && v.viewBox) || null;
  const lt = b.logoType || 'symbol';
  let mono = null;
  if (lt === 'wordmark' || !M) {
    // wordmarks repeat as their compact monogram (LOGO/SVG/compact.svg) when it is roughly square
    const cp = b.path('LOGO', 'SVG', 'compact.svg');
    if (fs.existsSync(cp)) {
      const s = svgParts(fs.readFileSync(cp, 'utf8')), ar = s.vb[2] / s.vb[3];
      if (s.parts.length && ar > 0.4 && ar < 2.5) mono = { kind: 'monogram', vb: s.vb, parts: s.parts,
        sil: s.parts.map(p => U.parsePath(p.d, p.tx, p.ty, 8).map(q => U.polyD(q)).join('')).join('') };
    }
  }
  return CORE.fromMarkData(M, lt, mono);
}

/** --type-<style>-<prop> tokens from tokens.css */
function typeTokens(b) {
  const css = fs.existsSync(b.path('SOURCE', 'CSS', 'tokens.css')) ? fs.readFileSync(b.path('SOURCE', 'CSS', 'tokens.css'), 'utf8') : '';
  const T = {}; const re = /--type-([a-z0-9-]+?)-(family|weight|size|line-height|letter-spacing|transform):\s*([^;]+);/g; let m;
  while ((m = re.exec(css))) { (T[m[1]] = T[m[1]] || {})[m[2]] = m[3].trim(); }
  const fontVar = {}; const re2 = /--font-([a-z0-9-]+):\s*([^;]+);/g; while ((m = re2.exec(css))) fontVar[m[1]] = m[2].trim();
  return { T, fontVar };
}

/** @font-face blocks of fonts.css → { family: [{style, file}] } */
function fontFiles(b) {
  const p = b.path('SOURCE', 'CSS', 'fonts.css'); const out = {};
  if (!fs.existsSync(p)) return out;
  const css = fs.readFileSync(p, 'utf8'); const re = /@font-face\s*{([^}]*)}/g; let m;
  while ((m = re.exec(css))) {
    const blk = m[1], fam = (/font-family:\s*['"]?([^;'"]+)['"]?/.exec(blk) || [])[1], style = (/font-style:\s*(\w+)/.exec(blk) || [, 'normal'])[1], src = (/url\(([^)]+)\)/.exec(blk) || [])[1];
    if (!fam || !src) continue;
    (out[fam] = out[fam] || []).push({ style, file: path.resolve(path.dirname(p), src.replace(/['"]/g, '')) });
  }
  return out;
}
function familyOf(stack) { return (stack || '').split(',')[0].replace(/['"]/g, '').trim(); }

/** Outline glyphs for the given role → text specs via lib/glyphs.py (fontTools). */
function glyphs(b, specs, scratch) {
  const files = fontFiles(b); const tt = typeTokens(b);
  const famFor = role => familyOf(tt.fontVar[role] || b.stacks[role] || b.stacks.sans || '');
  const local = Object.keys(b.fonts).filter(k => k.indexOf('local-') === 0).map(k => b.fonts[k]);
  const req = { fonts: specs.map(s => {
    const fam = famFor(s.role), list = (files[fam] || []).filter(x => x.style === 'normal').map(x => x.file);
    local.forEach(lf => (files[lf] || []).filter(x => x.style === 'normal').forEach(x => list.push(x.file)));
    return { key: s.key, files: list, wght: s.wght || 400, chars: s.chars };
  }) };
  const rq = path.join(scratch, 'glyph-req.json'), out = path.join(scratch, 'glyph-out.json');
  fs.writeFileSync(rq, JSON.stringify(req));
  try { execFileSync('python3', [path.join(__dirname, 'glyphs.py'), rq, out], { stdio: ['ignore', 'ignore', 'inherit'] }); return JSON.parse(fs.readFileSync(out, 'utf8')); }
  catch (e) { console.error('patterns-graphics: glyph outlining failed —', e.message.split('\n')[0]); return {}; }
}

/** Outlined text as an SVG group. G = glyph set; o: {size, tracking (em), anchor, fill, upper} → {svg, w} */
function textSVG(G, str, x, y, o) {
  o = o || {}; const size = o.size || 16, k = size / 1000, tr = (o.tracking || 0) * 1000;
  if (!G || !G.glyphs) return { svg: '', w: 0 };
  let s = String(str); if (o.upper) s = s.toLocaleUpperCase();
  let cx = 0; const parts = [];
  for (const ch of s) { const g = G.glyphs[ch] || G.glyphs['?'] || { d: '', w: 500 }; if (g.d) parts.push(`<path transform="translate(${U.f(cx)} 0)" d="${g.d}"/>`); cx += g.w + tr; }
  if (s.length) cx -= tr;
  const w = cx * k, x0 = o.anchor === 'middle' ? x - w / 2 : o.anchor === 'end' ? x - w : x;
  return { svg: `<g fill="${o.fill || 'currentColor'}" transform="translate(${U.f(x0)} ${U.f(y)}) scale(${+k.toFixed(5)})">${parts.join('')}</g>`, w };
}
/** glyphs placed along a circle (badges / seals): centred at angle a0 (deg, 0 = top) */
function textOnCircle(G, str, cx, cy, R, o) {
  o = o || {}; const size = o.size || 16, k = size / 1000, tr = (o.tracking || 0) * 1000; let s = String(str); if (o.upper) s = s.toLocaleUpperCase();
  const gl = [...s].map(ch => G.glyphs[ch] || G.glyphs['?'] || { d: '', w: 500 }); const total = gl.reduce((a, g) => a + g.w + tr, 0) - tr;
  const span = total * k / R, bottom = !!o.bottom; let a = (o.a0 || 0) * Math.PI / 180 - (bottom ? -span / 2 : span / 2); const out = [];
  gl.forEach(g => { const half = g.w * k / 2 / R; a += bottom ? -half : half; const ang = a - Math.PI / 2;
    const px = cx + Math.cos(bottom ? a + Math.PI / 2 : ang) * R, py = cy + Math.sin(bottom ? a + Math.PI / 2 : ang) * R, rot = bottom ? a * 180 / Math.PI : a * 180 / Math.PI;
    if (g.d) out.push(`<path transform="translate(${U.f(px)} ${U.f(py)}) rotate(${U.f(rot)}) scale(${+k.toFixed(5)}) translate(${U.f(-g.w / 2)} ${bottom ? U.f(0.72 * 1000 * 0) : 0})" d="${g.d}"/>`);
    a += (bottom ? -1 : 1) * (half + tr * k / R); });
  return `<g fill="${o.fill || 'currentColor'}">${out.join('')}</g>`;
}

function colourways(b) {
  const ramps = (b.colors && b.colors.ramps) || {};
  const energy = ((b.dna || {}).motion || {}).energy;
  return CORE.makeColourways({ primary: b.role.primary, foundation: b.role.foundation || '#111111', paper: b.role.paper || '#FFFFFF', accent: b.role.accent || b.role.primary,
    onPrimary: (b.theme || {})['text-on-brand'], ramp: ramps.primary || {}, playful: energy != null && energy >= 0.5 });
}

/** SVG → PNG with sharp (librsvg), 2 at a time. jobs: [{svg, out, scale, palette}] */
async function raster(jobs) {
  let sharp; try { sharp = require('sharp'); } catch (e) { console.error('patterns-graphics: sharp not installed — PNG previews skipped'); return 0; }
  let i = 0, n = 0;
  async function worker() { while (i < jobs.length) { const j = jobs[i++]; fs.mkdirSync(path.dirname(j.out), { recursive: true });
    try { await sharp(Buffer.from(j.svg), { density: 72 * (j.scale || 1), limitInputPixels: false }).png(j.palette === false ? { compressionLevel: 9 } : { compressionLevel: 9, palette: true, quality: 92, effort: 4, dither: j.dither == null ? 0.5 : j.dither }).toFile(j.out); n++; }
    catch (e) { console.error('raster failed', path.basename(j.out), e.message.split('\n')[0]); } } }
  await Promise.all([worker(), worker()]);
  return n;
}

function scratchDir(name) { const d = fs.mkdtempSync(path.join(os.tmpdir(), name + '-')); return d; }

module.exports = { loadWindow, svgParts, markUnits, typeTokens, fontFiles, glyphs, textSVG, textOnCircle, colourways, raster, scratchDir, familyOf };
