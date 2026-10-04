// css.js — SOURCE/CSS/<p>-graphics.css: pattern backgrounds, image masks (dna.imagery.crop), photo treatments
// (duotone / tint / mono / grain / natural from the palette) and contrast-safe scrims for text on images.
const fs = require('fs'), path = require('path');
const D2R = Math.PI / 180;

function scrimAlpha(U, F, text, min) { // smallest alpha of F over a pure-white pixel that keeps `text` ≥ min:1
  for (let a = 0.3; a <= 0.96; a += 0.01) { if (U.contrast(text, U.mix('#FFFFFF', F, a)) >= min) return Math.min(0.96, Math.ceil(a * 20) / 20); }
  return 0.96;
}
function rgba(U, hex, a) { const h = hex.replace('#', ''); return `rgba(${parseInt(h.substr(0, 2), 16)}, ${parseInt(h.substr(2, 2), 16)}, ${parseInt(h.substr(4, 2), 16)}, ${a})`; }

function polyPct(pts) { const bb = [Math.min(...pts.map(p => p[0])), Math.min(...pts.map(p => p[1])), Math.max(...pts.map(p => p[0])), Math.max(...pts.map(p => p[1]))], w = bb[2] - bb[0], h = bb[3] - bb[1];
  return { css: 'polygon(' + pts.map(p => `${(+((p[0] - bb[0]) / w * 100).toFixed(2))}% ${(+((p[1] - bb[1]) / h * 100).toFixed(2))}%`).join(', ') + ')', ar: +(w / h).toFixed(4) }; }
function simplify(pts, maxN) { if (pts.length <= maxN) return pts; const step = pts.length / maxN; const o = []; for (let i = 0; i < maxN; i++) o.push(pts[Math.floor(i * step)]); return o; }

function build(ctx) {
  const { b, gfx, cw } = ctx, U = ctx.CORE.util, p = b.p, dna = b.dna || {}, C = gfx.C, img = dna.imagery || {};
  const crop = C.crop, cut = C.cut, R = (b.dna.tokens || {}).radius || {};
  const F = b.role.foundation || '#111111', P = b.role.primary, W = b.role.paper || '#FFFFFF', A = b.role.accent || P;
  const txt = (b.theme || {})['text-inverse'] || W;
  const aBody = scrimAlpha(U, F, txt, 4.5), aLarge = scrimAlpha(U, F, txt, 3);
  const ramp = (b.colors.ramps || {}).primary || {};
  const duoLight = W, duoBrand = U.visible(F, [ramp['200'], ramp['100'], P], 4) || P;
  const masks = []; // {cls, note, css}
  const m = (cls, note, css) => masks.push({ cls, note, css });
  // ---- angled (aspect-independent: gradient masks at the true crop angle)
  const g = (deg, stop) => `-webkit-mask-image: linear-gradient(${deg}deg, #000 ${stop}, transparent 0); mask-image: linear-gradient(${deg}deg, #000 ${stop}, transparent 0);`;
  m('angled', `left edge cut at the brand crop angle (${crop}°) — aspect independent`, g(180 + crop, 'calc(100% - var(--' + p + '-mask-cut, 24%))'));
  m('angled--right', 'right edge cut at the crop angle', g(crop, 'calc(100% - var(--' + p + '-mask-cut, 24%))'));
  m('angled--both', 'both edges cut (parallelogram)', `-webkit-mask-image: linear-gradient(${180 + crop}deg, #000 calc(100% - var(--${p}-mask-cut, 20%)), transparent 0), linear-gradient(${crop}deg, #000 calc(100% - var(--${p}-mask-cut, 20%)), transparent 0); -webkit-mask-composite: source-in; mask-image: linear-gradient(${180 + crop}deg, #000 calc(100% - var(--${p}-mask-cut, 20%)), transparent 0), linear-gradient(${crop}deg, #000 calc(100% - var(--${p}-mask-cut, 20%)), transparent 0); mask-composite: intersect;`);
  m('angled--shallow', `bottom edge at the shallow angle (${C.shallow}°)`, g(180 - C.shallow, 'calc(100% - var(--' + p + '-mask-cut, 14%))').replace(/180 - /, ''));
  // ---- chamfer (exact cut angle via --cut)
  const t = Math.tan(cut * D2R).toFixed(3);
  m('cut', `chamfered corners (top-left + bottom-right) at ${cut}°; size via --${p}-mask-chamfer`, `--c: var(--${p}-mask-chamfer, 48px); --cy: calc(var(--c) * ${t}); clip-path: polygon(var(--c) 0, 100% 0, 100% calc(100% - var(--cy)), calc(100% - var(--c)) 100%, 0 100%, 0 var(--cy));`);
  m('cut--one', 'one chamfered corner (bottom-right), like the brand container', `--c: var(--${p}-mask-chamfer, 48px); --cy: calc(var(--c) * ${t}); clip-path: polygon(0 0, 100% 0, 100% calc(100% - var(--cy)), calc(100% - var(--c)) 100%, 0 100%);`);
  // ---- round family
  m('circle', 'circle (sets aspect-ratio 1)', 'clip-path: circle(50% at 50% 50%); aspect-ratio: 1;');
  m('capsule', 'capsule / pill', 'border-radius: 9999px;');
  m('arch', 'arch window (round top)', `border-radius: 9999px 9999px var(--radius-md, 8px) var(--radius-md, 8px);`);
  m('rounded', 'rounded rectangle (token radius)', `border-radius: var(--radius-xl, ${R.xl || '24px'});`);
  m('soft', 'soft squircle corners', 'border-radius: 22% / 26%;');
  m('notch', 'rectangle with a notch (top-right); size via --' + p + '-mask-notch', `--n: var(--${p}-mask-notch, 18%); clip-path: polygon(0 0, calc(100% - var(--n)) 0, calc(100% - var(--n)) var(--n), 100% var(--n), 100% 100%, 0 100%);`);
  // ---- organic blobs (seeded)
  for (let i = 1; i <= 3; i++) { const r = U.rng(U.hash(b.name + '|blobmask|' + i)), pts = U.blobPts(r, 50, 50, 46, { amp: organic(C) ? 0.14 : 0.1, n: 48, kmax: 3, sx: i === 2 ? 1.1 : 1 }); const pp = polyPct(pts); m('blob-' + i, `organic blob ${i} (seeded from the brand name)`, `clip-path: ${pp.css}; aspect-ratio: ${pp.ar};`); }
  // ---- mark silhouette / mark-derived shapes
  const U0 = gfx.mark.kind === 'wordmark' ? gfx.unit : gfx.mark;
  let silPts = U0.silPts && U0.silPts.length >= 3 ? U0.silPts : null;
  if (!silPts) { const polys = U0.silPolys || []; silPts = polys.slice().sort((a, c) => Math.abs(U.area(c)) - Math.abs(U.area(a)))[0]; }
  if (silPts && silPts.length >= 3) { const pp = polyPct(simplify(silPts, 96)); m('mark', 'the mark silhouette as a window (sets the mark aspect ratio)', `clip-path: ${pp.css}; aspect-ratio: ${pp.ar};`); }
  if (C.lang === 'angular' || C.corner === 'cut') {
    const rise = 0.5 * Math.tan(cut * D2R); m('gable', `gable window — roof at the cut angle (${cut}°)`, `clip-path: polygon(0 100%, 0 ${(Math.min(45, rise * 50)).toFixed(1)}%, 50% 0, 100% ${(Math.min(45, rise * 50)).toFixed(1)}%, 100% 100%);`);
    const r = U.rng(U.hash(b.name + '|shard')); const a1 = C.pickAngle(r), a2 = a1 + 38, tri = [[0, 0], [Math.cos(a1 * D2R) * 100, Math.sin(a1 * D2R) * 100], [Math.cos(a2 * D2R) * 80, Math.sin(a2 * D2R) * 80]]; const pp = polyPct(tri); m('shard', 'shard built from the logo edge angles', `clip-path: ${pp.css}; aspect-ratio: ${pp.ar};`);
  }
  if (C.complexity === 'faceted' && gfx.mark.facetParts) { const big = gfx.mark.facetParts.map(q => q.polys[0]).filter(Boolean).sort((a, c) => Math.abs(U.area(c)) - Math.abs(U.area(a)))[0]; if (big) { const pp = polyPct(simplify(big, 48)); m('facet', 'the largest facet of the mark', `clip-path: ${pp.css}; aspect-ratio: ${pp.ar};`); } }
  if (C.lang === 'round') m('orbit', 'circle with an orbiting satellite cut-out', `aspect-ratio: 1; -webkit-mask: radial-gradient(circle at 82% 18%, transparent 9%, #000 9.5%) , radial-gradient(circle at 50% 50%, #000 49.5%, transparent 50%); -webkit-mask-composite: source-in; mask: radial-gradient(circle at 82% 18%, transparent 9%, #000 9.5%), radial-gradient(circle at 50% 50%, #000 49.5%, transparent 50%); mask-composite: intersect;`);
  if (C.lang === 'organic') { const pts = [[0, 0], [100, 0]]; for (let x = 100; x >= 0; x -= 5) pts.push([x, 90 + Math.sin(x / 100 * Math.PI * 2.2) * 5]); m('wave', 'wavy bottom edge', `clip-path: polygon(${pts.map(q => `${q[0]}% ${q[1].toFixed(1)}%`).join(', ')});`); }
  const def = { angled: 'angled', circle: 'circle', organic: 'blob-1', rounded: 'rounded', rect: null }[img.crop] || null;
  const defCss = def ? masks.find(x => x.cls === def).css : `border-radius: var(--radius-card, ${R.md || '0'});`;
  ctx.counts.masks = masks.length + 1;
  ctx.maskList = [{ cls: '', note: `default crop of the brand (dna.imagery.crop = ${img.crop || 'rect'} → ${def || 'rect'})` }].concat(masks);

  const grainSvg = `url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 .5  0 0 0 0 .5  0 0 0 0 .5  0 0 0 1.1 0'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>")`;
  const grade = { angular: 'contrast(1.08) saturate(0.92)', round: 'brightness(1.03) saturate(1.02)', organic: 'contrast(0.98) saturate(0.95) sepia(0.06)', orthogonal: 'contrast(1.04) saturate(0.9)', mixed: 'contrast(1.03)' }[C.lang] || 'none';
  const pats = (ctx.patterns || []).filter(x => x.tile);
  const L = [];
  L.push(`/* ==========================================================================
   ${b.name} — ${p}-graphics.css  (generated by the patterns-graphics module — regenerate, do not edit)
   Graphic language derived from the logo + design DNA (${C.lang} · corner ${C.corner} · crop ${img.crop || 'rect'} ${crop}°).
   Load after ${p}-core.css:
     <link rel="stylesheet" href="…/SOURCE/CSS/${p}-core.css">
     <link rel="stylesheet" href="…/SOURCE/CSS/${p}-graphics.css">

   1. Pattern grounds   .${p}-pattern.${p}-pattern--<name>[--foundation|--primary]   (tiles in PATTERNS/SVG)
                        .${p}-pattern-panel  calm text panel above a pattern
   2. Image masks       .${p}-mask (brand default) · .${p}-mask-<shape> — on <img>/<video>/<div>
   3. Photo treatments  <figure class="${p}-photo ${p}-photo--duotone"> <img alt="…"> </figure>
                        --natural · --mono · --duotone · --duotone-brand · --tint · --grain
   4. Scrims            <span class="${p}-scrim ${p}-scrim--bottom" aria-hidden="true"></span> + .${p}-photo__content
                        Alphas are computed so text-inverse (${txt}) keeps ≥ 4.5:1 even over pure white pixels.
   Accessibility: masks and treatments are presentational; keep real alt text on images (decorative → alt="").
   ========================================================================== */
:root {
  --${p}-angle-crop: ${crop}deg; --${p}-angle-cut: ${cut}deg; --${p}-angle-shallow: ${C.shallow}deg;
  --${p}-duo-dark: ${F}; --${p}-duo-light: ${duoLight}; --${p}-duo-brand: ${duoBrand}; --${p}-tint: ${P}; --${p}-tint-accent: ${A};
  --${p}-scrim: ${F}; --${p}-scrim-alpha: ${aBody}; --${p}-scrim-alpha-large: ${aLarge};
  --${p}-pattern-scale: 1;
}

/* ---------------------------------------------------------------- 1. Pattern grounds */
.${p}-pattern { background-color: ${cw.paper.bg}; background-repeat: repeat; background-position: 0 0; }
.${p}-pattern-panel { position: relative; z-index: 1; background: var(--color-surface, ${cw.paper.bg}); color: var(--color-text-primary, ${cw.paper.ink}); padding: var(--space-8, 32px); max-width: 36rem; }`);
  pats.forEach(x => { const base = `../../PATTERNS/SVG/${x.key}`;
    L.push(`.${p}-pattern--${x.key} { background-image: url("${base}-paper.svg"); background-size: calc(${x.w}px * var(--${p}-pattern-scale)) auto; }`);
    L.push(`.${p}-pattern--${x.key}.${p}-pattern--foundation, [data-theme="dark"] .${p}-pattern--${x.key} { background-image: url("${base}-foundation.svg"); background-color: ${cw.foundation.bg}; }`);
    L.push(`.${p}-pattern--${x.key}.${p}-pattern--primary { background-image: url("${base}-primary.svg"); background-color: ${cw.primary.bg}; }`); });
  const mk = (ctx.patterns || []).find(x => x.key === 'mark-crop');
  if (mk) L.push(`.${p}-pattern--mark-crop { background-image: url("../../PATTERNS/SVG/mark-crop-paper.svg"); background-size: cover; background-position: right center; background-repeat: no-repeat; }\n.${p}-pattern--mark-crop.${p}-pattern--foundation { background-image: url("../../PATTERNS/SVG/mark-crop-foundation.svg"); background-color: ${cw.foundation.bg}; }\n.${p}-pattern--mark-crop.${p}-pattern--primary { background-image: url("../../PATTERNS/SVG/mark-crop-primary.svg"); background-color: ${cw.primary.bg}; }`);
  L.push(`.${p}-pattern-panel { ${C.corner === 'cut' ? `--c: 28px; clip-path: polygon(0 0, 100% 0, 100% calc(100% - var(--c) * ${t})), calc(100% - var(--c)) 100%, 0 100%);`.replace('))', ')') : C.corner === 'round' ? 'border-radius: var(--radius-xl, 24px);' : C.corner === 'soft' ? 'border-radius: var(--radius-xl, 32px);' : ''} }

/* ---------------------------------------------------------------- 2. Image masks */
:where([class*="${p}-mask"]):where(img, video) { object-fit: cover; display: block; }
.${p}-mask { ${defCss} }   /* brand default: ${def || 'rect'} */`);
  masks.forEach(x => L.push(`.${p}-mask-${x.cls} { ${x.css} }   /* ${x.note} */`));
  L.push(`
/* ---------------------------------------------------------------- 3. Photo treatments (layer model: ground · img · ::before tone · ::after grain · children) */
.${p}-photo { position: relative; display: block; margin: 0; overflow: hidden; isolation: isolate; background: var(--${p}-duo-dark); }
.${p}-photo > img, .${p}-photo > video, .${p}-photo > picture > img { display: block; width: 100%; height: 100%; object-fit: cover; object-position: var(--${p}-photo-pos, 50% 50%); }
.${p}-photo::before, .${p}-photo::after { content: ""; position: absolute; inset: 0; pointer-events: none; z-index: 1; opacity: 0; }
/* natural — the house grade (${C.lang}): gentle, never crushed */
.${p}-photo--natural > img, .${p}-photo--natural > video { filter: ${grade}; }
/* mono — neutral black & white with foundation-lifted shadows */
.${p}-photo--mono > img, .${p}-photo--mono > video { filter: grayscale(1) contrast(1.08); }
.${p}-photo--mono::before { background: var(--${p}-duo-dark); mix-blend-mode: lighten; opacity: 0.32; }
/* duotone — foundation shadows → paper highlights */
.${p}-photo--duotone { background: var(--${p}-duo-light); }
.${p}-photo--duotone > img, .${p}-photo--duotone > video { filter: grayscale(1) contrast(1.12) brightness(1.04); mix-blend-mode: multiply; }
.${p}-photo--duotone::before { background: var(--${p}-duo-dark); mix-blend-mode: lighten; opacity: 1; }
/* duotone-brand — foundation shadows → brand-tint highlights */
.${p}-photo--duotone-brand { background: var(--${p}-duo-brand); }
.${p}-photo--duotone-brand > img, .${p}-photo--duotone-brand > video { filter: grayscale(1) contrast(1.15); mix-blend-mode: multiply; }
.${p}-photo--duotone-brand::before { background: var(--${p}-duo-dark); mix-blend-mode: lighten; opacity: 1; }
/* tint — a primary wash (keeps detail; use behind short display text only with a scrim) */
.${p}-photo--tint > img, .${p}-photo--tint > video { filter: grayscale(0.35) contrast(1.04); }
.${p}-photo--tint::before { background: var(--${p}-tint); mix-blend-mode: ${U.lum(P) > 0.3 ? 'multiply' : 'color'}; opacity: 0.55; }
/* grain — subtle film texture (combine with any treatment) */
.${p}-photo--grain::after { background-image: ${grainSvg}; mix-blend-mode: overlay; opacity: 0.22; }

/* ---------------------------------------------------------------- 4. Scrims for text on images */
.${p}-scrim { position: absolute; inset: 0; z-index: 2; pointer-events: none; --a: var(--${p}-scrim-alpha); }
.${p}-scrim--bottom { background: linear-gradient(to top, ${rgba(U, F, aBody)} 0%, ${rgba(U, F, aBody)} 46%, ${rgba(U, F, 0)} 82%); }
.${p}-scrim--left { background: linear-gradient(to right, ${rgba(U, F, aBody)} 0%, ${rgba(U, F, aBody)} 56%, ${rgba(U, F, 0)} 88%); }
.${p}-scrim--full { background: ${rgba(U, F, aBody)}; }
.${p}-scrim--angled { background: linear-gradient(${180 - crop}deg, ${rgba(U, F, aBody)} 0%, ${rgba(U, F, aBody)} 58%, ${rgba(U, F, 0)} 58.2%); }
.${p}-scrim--radial { background: radial-gradient(circle at 0% 100%, ${rgba(U, F, aBody)} 0%, ${rgba(U, F, aBody)} 55%, ${rgba(U, F, 0)} 85%); }
.${p}-photo__content { position: absolute; z-index: 3; left: 0; right: 0; bottom: 0; padding: var(--space-8, 32px); color: ${txt}; }
.${p}-photo__content--top { top: 0; bottom: auto; }
/* keep text inside the solid part of side / angled / radial scrims */
.${p}-scrim--left ~ .${p}-photo__content, .${p}-scrim--angled ~ .${p}-photo__content, .${p}-scrim--radial ~ .${p}-photo__content { right: auto; max-width: 50%; }
.${p}-photo__caption { font-family: var(--font-mono); font-size: var(--type-caption-size, 0.75rem); letter-spacing: var(--type-label-letter-spacing, 0.06em); text-transform: var(--type-label-transform, uppercase); }
@media (forced-colors: active) { .${p}-scrim { background: Canvas; opacity: 0.9; } }
`);
  return L.join('\n');
}
function organic(C) { return C.lang === 'organic' || C.corner === 'soft'; }

function run(ctx) {
  const { b, F } = ctx;
  const css = build(ctx);
  F.write(b.path('SOURCE', 'CSS', `${b.p}-graphics.css`), css);
}
module.exports = { run, scrimAlpha };
