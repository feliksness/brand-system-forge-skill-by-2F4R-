#!/usr/bin/env node
/* motion module — brand-system-forge
   node build.js --repo <BRAND-REPO> [--export] [--no-previews]
   Writes SOURCE/CSS/<p>-motion.css, SOURCE/JS/<p>-motion.js, MOTION/ (logo animations, transitions, principles,
   previews) and GENERATIVE/ (motif animation tool). --export records MP4 + GIF per logo animation (needs ffmpeg). */
'use strict';
const fs = require('fs'), path = require('path');
const F = require(path.join(__dirname, '..', '..', '..', 'scripts', 'forge_lib.js'));
const css = require('./lib/css.js');
const gen = require('./lib/generative.js');
const T0 = Date.now();
const argv = process.argv.slice(2), arg = k => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : null; };
const repo = arg('--repo'); if (!repo) { console.error('usage: node build.js --repo <brand-repo> [--export] [--no-previews]'); process.exit(2); }
const b = F.load(repo), p = b.p, G = b.G, dna = b.dna, esc = F.esc;
if (b.profile.modules && b.profile.modules.motion === false) { console.log('motion: skipped — profile.modules.motion is false'); process.exit(0); }
const read = (...x) => { const f = b.path(...x); return fs.existsSync(f) ? fs.readFileSync(f, 'utf8') : ''; };
const T = f => fs.readFileSync(path.join(__dirname, 'templates', f), 'utf8');
const ms = v => parseFloat(String(v || '0').replace('ms', '')) || 0;
const sub = (s, map) => s.replace(/__G__/g, G).replace(/__P__/g, p).replace(/__NAME__/g, b.name).replace(/__CHARACTER__/g, map.character).replace(/__SIGNATURE__/g, map.signature).replace(/__ENERGY__/g, String(map.energy));

/* ---------------------------------------------------------------- 1. motion parameters from the DNA */
const mo = dna.motion || {}, tok = dna.tokens || {};
const character = ['snap', 'slide', 'glide', 'flow'].includes(mo.character) ? mo.character : 'glide';
const M = {
  character, energy: +(mo.energy != null ? mo.energy : 0.4), signature: mo.signature || '',
  angle: (dna.angles || {}).cut || dna.corner.angle_deg || 45, crop: (dna.angles || {}).crop || 66,
  imagery: (dna.imagery || {}).crop || 'rect', shadow: dna.shadow_style || 'soft', corner: (dna.corner || {}).style || 'square',
  base: dna.base_language || 'mixed', complexity: dna.complexity || 'flat', cap: (dna.stroke || {}).cap || 'round', join: (dna.stroke || {}).join || 'round',
  duration: Object.fromEntries(Object.entries(tok.duration || {}).map(([k, v]) => [k, ms(v)])),
  ease: tok.ease || {}, patterns: dna.patterns || [], motifs: dna.motifs || [], displayCase: (dna.type_voice || {}).display_case || 'sentence'
};
['instant', 'fast', 'base', 'slow', 'slower', 'formation', 'logo'].forEach((k, i) => { if (!M.duration[k]) M.duration[k] = [80, 160, 240, 400, 640, 1200, 2400][i]; });
['standard', 'enter', 'exit', 'emphasis'].forEach((k, i) => { if (!M.ease[k]) M.ease[k] = ['cubic-bezier(0.2, 0, 0, 1)', 'cubic-bezier(0.16, 1, 0.3, 1)', 'cubic-bezier(0.7, 0, 0.84, 0)', 'cubic-bezier(0.34, 1.4, 0.64, 1)'][i]; });
const logoType = b.logoType, content = b.content || {}, cb = content.brand || {};
const tagline = cb.tagline || b.brand.tagline || '', website = (content.contact || {}).website || '';

/* ---------------------------------------------------------------- 2. logo assets for the engine */
function svgParts(str) {
  const m = /<svg\b([^>]*)>([\s\S]*)<\/svg>/i.exec(str || ''); if (!m) return null;
  const vbm = /viewBox="([^"]+)"/.exec(m[1]); const vb = vbm ? vbm[1].trim().split(/[\s,]+/).map(Number) : [0, 0, 100, 100];
  return { vb, inner: m[2].replace(/<title[\s\S]*?<\/title>/gi, '').replace(/<desc[\s\S]*?<\/desc>/gi, '').trim() };
}
const fills = s => [...new Set((s.match(/fill="(#[0-9A-Fa-f]{3,8})"/g) || []).map(x => x.slice(6, -1).toUpperCase()))];
const full = { light: F.svg(b, 'logo-original'), dark: F.svg(b, 'logo-original-on-dark') || F.svg(b, 'logo-original-white') };
const compact = { light: F.svg(b, 'compact') || F.svg(b, 'symbol-small') || full.light };
if (logoType === 'wordmark') {
  const odf = fills(full.dark);
  compact.dark = odf.length === 1 ? compact.light.replace(/fill="#[0-9A-Fa-f]{3,8}"/g, `fill="${odf[0]}"`) : (F.svg(b, 'compact-white') || compact.light);
} else compact.dark = F.svg(b, 'symbol-small-on-dark') || F.svg(b, 'compact-white') || compact.light;
// wordmark data (typeset / traced lettering items)
function loadWordmark() {
  const src = read('SOURCE', 'JS', 'wordmark-data.js'); if (!src) return null;
  try { const window = {}; new Function('window', src)(window); return window[G + '_WORDMARK'] || null; } catch (e) { return null; }
}
const WM = loadWordmark();
let lockup = null;
if (logoType === 'symbol' && WM && WM.items) {
  const it = WM.items.line || WM.items.line_1 || WM.items.stacked;
  if (it) {
    const multi = !WM.items.line && WM.items.stacked === it;
    lockup = {};
    for (const bg of ['light', 'dark']) {
      const s = svgParts(full[bg]); if (!s) continue;
      const [x, y, w, h] = s.vb, nvb = it.vb.split(/[\s,]+/).map(Number);
      const k = (h * (multi ? 0.5 : 0.3)) / nvb[3], gap = h * 0.25;
      const opt = (b.mark.optical_center || [0.5, 0.5])[1];
      let cy = y + h * opt; const half = nvb[3] * k / 2; cy = Math.min(Math.max(cy, y + half), y + h - half);
      const tx = x + w + gap - nvb[0] * k, ty = cy - (nvb[1] + nvb[3] / 2) * k;
      const ink = bg === 'light' ? (b.role.foundation || b.theme['text-primary']) : (b.dark['text-primary'] || '#FFFFFF');
      const W = w + gap + nvb[2] * k;
      lockup[bg] = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${x} ${y} ${W.toFixed(2)} ${h}">${s.inner}<g id="lettering" fill="${ink}"><g transform="translate(${tx.toFixed(3)} ${ty.toFixed(3)}) scale(${k.toFixed(6)})">${it.body}</g></g></svg>`;
    }
  }
}
const assets = { full, compact }; if (lockup) assets.lockup = lockup;
const roles = { full: logoType === 'wordmark' ? { mark: 'lettering' } : {}, compact: {}, lockup: {} };
// outro text geometry (root units of logo-original)
const fv = (svgParts(full.light) || { vb: [0, 0, 100, 100] }).vb, Hf = Math.max(fv[3] / 0.5, fv[2] / (0.62 * 16 / 9));
const textScale = { tagline: +(Hf * 0.074).toFixed(2), url: +(Hf * 0.036).toFixed(2), taglineY: +(fv[1] + fv[3] + Hf * 0.19).toFixed(2), urlY: +(fv[1] + fv[3] + Hf * 0.19 + Hf * 0.1).toFixed(2) };
const upper = M.displayCase === 'upper';
const logoData = {
  assets, roles, label: b.name + ' logo animation',
  bg: { light: b.theme.background || b.role.paper || '#FFFFFF', dark: b.dark.background || b.role.foundation || '#111111' },
  ink: { light: b.theme['text-primary'] || '#111', dark: b.dark['text-primary'] || '#FFF' },
  muted: { light: b.theme['text-secondary'] || '#555', dark: b.dark['text-secondary'] || '#CCC' },
  fill: { full: logoType === 'wordmark' ? 0.4 : 0.5, compact: 0.46, lockup: 0.44 },
  texts: { tagline, url: website, lang: b.lang, transform: upper ? 'uppercase' : 'none', tracking: upper ? ((dna.type_voice || {}).tracking_upper_em || 0.02) : -0.005, weight: 'var(--type-h1-weight)' },
  textScale
};

/* ---------------------------------------------------------------- 3. which animations (logo type × complexity) */
function countParts(svg) { return (svg.match(/<(path|polygon|rect|circle|ellipse)\b/g) || []).length; }
const nMark = countParts(full.light), faceted = M.complexity === 'faceted' || (logoType === 'symbol' && nMark > 12);
const fast = M.character === 'snap' || M.character === 'slide';
const charWords = {
  snap: `travel along the ${M.angle}° cut and stop crisply — no overshoot, no rotation`,
  slide: 'slide in along the grid in measured steps, from the side they belong to',
  glide: 'swing in around the centre and scale up as they settle — an orbit that closes into the mark',
  flow: 'drift up softly and settle with a gentle spring'
}[M.character];
const letterWords = { snap: `the lettering is wiped in along the ${M.angle}° cut`, slide: 'the glyphs rise from the baseline, left to right', glide: 'the glyphs scale up from the centre outwards', flow: 'the glyphs drift in with a soft spring' }[M.character];
const C = [];
const add = (concept, asset, title, about, extra = {}) => C.push(Object.assign({ concept, asset, title, about, bg: 'light' }, extra));
if (logoType === 'wordmark') {
  add('reveal', 'full', 'Lettering reveal', `The wordmark opens as one gesture — ${{ snap: `an edge at the ${M.angle}° cut`, slide: 'a horizontal wipe on the grid', glide: 'an iris from the centre', flow: 'a feathered, drifting wipe' }[M.character]}. The quietest version: use it wherever the logo appears on its own.`);
  add('stagger', 'full', 'Letter stagger', `Glyph by glyph — ${letterWords}. Built from the traced lettering, so every letter keeps its drawn shape.`);
  if (compact.light) add('monogram', 'full', 'Monogram morph-in', 'The compact mark enters alone, settles onto its own letter in the wordmark, and the remaining glyphs follow — the bridge between the app icon and the full name.', { mono: true });
  add('contour', 'full', 'Contour draw', `Construction: the letter outlines draw on with the brand stroke (${M.cap} caps, ${M.join} joins), the fills flood in, the outlines dissolve.`);
} else if (logoType === 'emblem') {
  add('frame', 'full', 'Frame, then content', `The emblem's frame forms first (${{ glide: 'an iris, then sweeps around the centre', snap: `angled wipes at ${M.angle}°`, slide: 'rising from the base', flow: 'a soft scale' }[M.character]}), then the content arrives row by row.`);
  add('assemble', 'full', 'Parts assemble', `Every part of the emblem arrives from an exploded state and the parts ${charWords}.`);
  add('contour', 'full', 'Contour draw', `Construction: all outlines draw on (${M.cap} caps, ${M.join} joins), the fills flood in from dark to light, the outlines dissolve.`);
  add('sting', 'compact', 'Compact sting', 'The compact emblem in about a second — for social intros, video bumpers and app launches.');
} else if (logoType === 'combination') {
  add('signature', 'full', 'Symbol, then lettering', `The signature: the symbol's parts build in sequence, then ${letterWords}. The default animation for the logo.`);
  add('assemble', 'full', 'Parts assemble', `The symbol's parts arrive from an exploded state and ${charWords}; the lettering follows.`);
  add('contour', 'full', 'Contour draw', `Construction: symbol and lettering outlines draw on (${M.cap} caps, ${M.join} joins), the fills flood in from dark to light, the outlines dissolve.`);
  add('sting', 'compact', 'Compact sting', 'The symbol alone in about a second — for social intros, video bumpers and app launches.');
} else {
  if (M.complexity === 'line') add('contour', 'full', 'Stroke draw-on', `The line mark draws itself (${M.cap} caps, ${M.join} joins) — the natural animation for a line logo.`);
  if (faceted) {
    add('assemble', 'full', 'Facets assemble', `The ${nMark} facets arrive from an exploded state, darkest first, and ${charWords}. Ends on the exact mark.`);
    add('sweep', 'full', 'Light sweep', `A front crosses the mark ${{ snap: `along the ${M.angle}° cut`, slide: 'from the base up', glide: 'outwards from the centre', flow: 'softly from left to right' }[M.character]}; each facet pops as the front reaches it.`);
  } else {
    add('build', 'full', 'Build in sequence', `The mark's parts are revealed one after another and ${charWords}.`);
    add('assemble', 'full', 'Parts assemble', `The parts arrive from an exploded state and ${charWords}.`);
  }
  if (M.complexity !== 'line') add('contour', 'full', 'Contour draw', `Construction: the outlines draw on with the brand stroke (${M.cap} caps, ${M.join} joins), the fills flood in from dark to light, the outlines dissolve.`);
  if (lockup) add('lockup', 'lockup', 'Symbol, then name', `The symbol forms, then the typeset name follows (${letterWords}). Preview of the symbol + name lockup — final lockups come from the logo system.`);
  else add('sting', 'compact', 'Compact sting', 'The compact mark in about a second.');
}
add('outro', 'full', 'End card', 'For the end of videos and presentations: a compressed signature entrance, then the tagline and the address. Holds on the final card.', { bg: 'dark', texts: true, fill: 0.62 });
add('loader', 'compact', 'Loader', `A loading indicator derived from the mark (${{ snap: `fills along the ${M.angle}° cut`, slide: 'stepped fill from the base', glide: 'an orbit circles the mark', flow: 'a soft wave fills the mark' }[M.character]}, or the parts light in sequence when the mark has four or more). Loops; under reduced motion it shows a still mark.`, { loop: true });
C.forEach((c, i) => { c.n = i + 1; c.file = String(i + 1).padStart(2, '0') + '-' + c.concept + '.html'; });

/* ---------------------------------------------------------------- 4. write runtime CSS + JS */
const cfg = {
  name: b.name, lang: b.lang, logoType, character, energy: M.energy, signature: M.signature, angle: M.angle, crop: M.crop,
  complexity: faceted ? 'faceted' : M.complexity, imagery: M.imagery, corner: M.corner, cap: M.cap, join: M.join, duration: M.duration, ease: M.ease
};
const jsSrc = sub(T('motion.js'), M).replace('__CFG__', () => JSON.stringify(cfg)).replace('/*__CONCEPTS__*/', () => T('concepts.js'));
F.write(b.path('SOURCE', 'CSS', `${p}-motion.css`), css(b, M));
F.write(b.path('SOURCE', 'JS', `${p}-motion.js`), jsSrc);

/* ---------------------------------------------------------------- 5. pages */
const OUT = b.path('MOTION');   // rewritten entirely, except exports/ (expensive videos) unless --export re-renders them
if (fs.existsSync(OUT)) fs.readdirSync(OUT).forEach(f => { if (f !== 'exports' || argv.includes('--export')) fs.rmSync(path.join(OUT, f), { recursive: true, force: true }); });
const LA = 'MOTION/logo-animation';
F.write(b.path(LA, 'assets', 'logo-data.js'), `/* ${b.name} — logo assets for the logo-animation pages (generated by the motion module from LOGO/SVG). */\nwindow.${G}_LOGO_MOTION=${JSON.stringify(logoData)};\n`);
F.write(b.path(LA, 'assets', 'logo-page.js'), sub(T('logo-page.js'), M));
F.write(b.path('MOTION', 'assets', 'pages.css'), sub(T('pages.css'), M));
const stillHead = `<script>if(/[?&]still=1/.test(location.search))document.documentElement.setAttribute('data-motion-still','')</script>`;
const head = at => `<link rel="stylesheet" href="${b.rel(at, `SOURCE/CSS/${p}-motion.css`)}"><link rel="stylesheet" href="${b.rel(at, 'MOTION/assets/pages.css')}">${stillHead}`;
const coreScripts = ['mark-data.js', 'wordmark-data.js', 'dna-data.js', 'content-data.js', '{p}-mark.js', '{p}-motion.js'];
const total = { snap: 'crisp', slide: 'measured', glide: 'smooth', flow: 'soft' }[M.character];
const ctrls = c => `<div class="lp-controls" role="group" aria-label="Playback">
  <button class="lp-btn lp-btn--primary" id="lp-replay" type="button">Replay</button>
  <button class="lp-btn" id="lp-play" type="button" aria-pressed="false">Play</button>
  <input class="lp-scrub" id="lp-scrub" type="range" min="0" max="1000" step="1" value="0" aria-label="Scrub timeline">
  <span class="lp-time" id="lp-time" aria-live="off">00:00.00</span>
  <label class="lp-field">Speed <select id="lp-speed"><option value="0.25">0.25×</option><option value="0.5">0.5×</option><option value="1" selected>1×</option><option value="2">2×</option></select></label>
  <span class="lp-seg" role="radiogroup" aria-label="Background"><label><input type="radio" name="lp-bg" value="light"><span>Light</span></label><label><input type="radio" name="lp-bg" value="dark"><span>Dark</span></label></span>
  <label class="lp-field"><input type="checkbox" id="lp-loop"${c.loop ? ' checked' : ''}> Loop</label>
</div>`;
function conceptPage(c) {
  const prev = C[c.n - 2], next = C[c.n];
  const assetFile = { full: logoType === 'wordmark' ? 'LOGO/SVG/logo-original.svg (traced lettering)' : 'LOGO/SVG/logo-original.svg', compact: 'LOGO/SVG/compact.svg', lockup: 'LOGO/SVG/logo-original.svg + typeset name (wordmark-data.js)' }[c.asset];
  const sizes = c.loop ? `<section class="lp-section" aria-labelledby="sz"><h2 class="${p}-h3" id="sz">Sizes</h2><p class="lp-sub">Same loop at UI sizes, light and dark. In code: <code>${G}.loader(el, { size: 32 })</code> (uses the simplified mark) or <code>&lt;span data-${p}-loader data-size="32"&gt;&lt;/span&gt;</code>.</p>
  <div class="lp-sizes" id="lp-sizes">${[96, 48, 24].map(s => `<div data-size="${s}" data-theme="light"><span class="lp-tc">${s} px</span></div>`).join('')}${[96, 48, 24].map(s => `<div data-size="${s}" data-theme="dark"><span class="lp-tc">${s} px · dark</span></div>`).join('')}</div></section>` : '';
  const body = `<a class="${p}-skip-link" href="#stage">Skip to the animation</a>
<main class="lp"><div class="lp-wrap">
<header class="lp-head">
  <div>
    <p class="lp-kicker ${p}-eyebrow"><span class="${p}-index">${String(c.n).padStart(2, '0')} / ${String(C.length).padStart(2, '0')}</span><span>${esc(b.name)} · Motion · Logo animation</span></p>
    <h1 class="lp-title ${p}-h1">${esc(c.title)}</h1>
    <p class="lp-lead">${esc(c.about)}</p>
  </div>
  <dl class="lp-meta">
    <dt>Duration</dt><dd id="lp-total">—</dd>
    <dt>Character</dt><dd>${esc(M.character)} · energy ${M.energy}</dd>
    <dt>Logo</dt><dd>${esc(logoType)}${faceted ? ' · faceted' : ''}</dd>
    <dt>Source</dt><dd>${esc(assetFile)}</dd>
    <dt>Units</dt><dd id="lp-units">—</dd>
  </dl>
</header>
<section class="lp-section lp-stage-sec" aria-label="Animation">
  <div class="lp-stage ${p}-shape" id="stage" tabindex="-1"></div>
  ${ctrls(c)}
  <p class="lp-note" id="lp-reduced" hidden>Reduced motion is on, so the final frame is shown. Press Play or Replay to watch the animation.</p>
</section>
<section class="lp-section" aria-labelledby="kf"><div class="lp-board" id="board">
  <div class="lp-board__head"><h2 class="${p}-h3" id="kf">${esc(c.title)} — keyframes</h2><span class="${p}-label">${esc(b.name)} · ${esc(M.character)} · ${esc(logoType)}</span></div>
  <div class="lp-frames" id="storyboard"></div>
</div></section>
${sizes}
<section class="lp-section lp-cols">
  <div><h2 class="${p}-h3">Timing</h2><p class="lp-sub">Phases in milliseconds. Easings are the brand tokens (<code>--ease-*</code>); every frame is a pure function of time, so exports are exact.</p>
    <table class="lp-table" id="phases"><thead><tr><th scope="col">Phase</th><th scope="col" class="num">From</th><th scope="col" class="num">To</th><th scope="col">Ease</th></tr></thead><tbody></tbody></table></div>
  <div><h2 class="${p}-h3">Use it</h2><p class="lp-sub">On a page that loads the brand core and <code>${p}-motion.js</code>:</p>
<code class="lp-code">${esc(c.loop ? `${G}.loader(document.querySelector('#busy'), { size: 48 });` : `${G}.logoAnimate(el, {\n  svg: logoSvgMarkup,      // e.g. LOGO/SVG/${c.asset === 'compact' ? 'compact' : 'logo-original'}.svg inline\n  concept: '${c.concept}'\n});`)}</code>
    <p class="lp-sub" style="margin-top:var(--space-4)">Reduced motion: no autoplay, the final frame is shown. Video files: <code>node build.js --repo … --export</code> writes MP4 + GIF to <code>MOTION/exports/</code> when ffmpeg is available.</p></div>
</section>
<nav class="lp-nav" aria-label="Logo animations">${prev ? `<a href="${prev.file}">← ${esc(prev.title)}</a>` : '<span></span>'}<a href="index.html">All logo animations</a>${next ? `<a href="${next.file}">${esc(next.title)} →</a>` : '<span></span>'}</nav>
</div></main>`;
  const tail = `<script src="assets/logo-data.js"></script><script src="assets/logo-page.js"></script>
<script>(document.fonts ? document.fonts.ready : Promise.resolve()).then(function () { LogoPage.init(${JSON.stringify({ concept: c.concept, asset: c.asset, bg: c.bg, mono: !!c.mono, texts: !!c.texts, loop: !!c.loop, fill: c.fill })}); });</script>`;
  return F.page(b, `${c.title} · Logo animation`, body, LA, { head: head(LA), scripts: coreScripts, tail });
}
C.forEach(c => F.write(b.path(LA, c.file), conceptPage(c)));
// gallery
const galBody = `<a class="${p}-skip-link" href="#grid">Skip to the animations</a><main class="lp"><div class="lp-wrap">
<header class="lp-head"><div><p class="lp-kicker ${p}-eyebrow"><span class="${p}-index">${C.length}</span><span>${esc(b.name)} · Motion</span></p>
<h1 class="lp-title ${p}-h1">Logo animations</h1><p class="lp-lead">${esc(`Chosen for ${/^[aeiou]/.test(logoType) ? 'an' : 'a'} ${logoType}${faceted ? ' with a faceted mark' : ''} and the ${M.character} motion character (${M.signature}). Every animation ends on the exact logo.`)}</p></div>
<dl class="lp-meta"><dt>Character</dt><dd>${esc(M.character)} · energy ${M.energy}</dd><dt>Logo duration</dt><dd>${M.duration.logo} ms (token)</dd><dt>Principles</dt><dd><a href="../principles.md">principles.md</a></dd><dt>Transitions</dt><dd><a href="../transitions/index.html">Gallery</a></dd></dl></header>
<section class="lp-section"><div class="lp-grid" id="grid">${C.map(c => `<a class="lp-card" href="${c.file}"><div class="lp-card__stage ${p}-shape" id="g-${c.n}"></div><span class="${p}-label">${String(c.n).padStart(2, '0')} · ${esc(c.concept)}</span><h3 class="${p}-h4">${esc(c.title)}</h3><p>${esc(c.about)}</p></a>`).join('')}</div></section>
</div></main>`;
const galTail = `<script src="assets/logo-data.js"></script><script src="assets/logo-page.js"></script><script>(document.fonts ? document.fonts.ready : Promise.resolve()).then(function () { LogoPage.gallery(${JSON.stringify(C.map(c => ({ id: c.n, concept: c.concept, asset: c.asset, bg: c.bg, mono: !!c.mono, texts: !!c.texts, title: c.title, fill: c.fill })))}); });</script>`;
F.write(b.path(LA, 'index.html'), F.page(b, 'Logo animations', galBody, LA, { head: head(LA), scripts: coreScripts, tail: galTail }));

/* ---------------------------------------------------------------- 6. transitions gallery */
F.write(b.path('MOTION', 'transitions', 'index.html'), require('./lib/transitions.js')(b, M, { head, coreScripts, esc, tagline, C }));
F.write(b.path('MOTION', 'transitions', 'frames.html'), require('./lib/transitions.js').frames(b, M, { head, coreScripts, esc }));

/* ---------------------------------------------------------------- 7. generative tool */
fs.rmSync(b.path('GENERATIVE'), { recursive: true, force: true });
const genOut = gen(b, M, { head, coreScripts, esc, assets, logoData });

/* ---------------------------------------------------------------- 8. docs */
const docs = require('./lib/docs.js');
F.write(b.path('MOTION', 'principles.md'), docs.principles(b, M, C));
F.write(b.path('MOTION', 'README.md'), docs.readme(b, M, C));
F.write(b.path('MOTION', 'logo-animation', 'README.md'), docs.logoReadme(b, M, C));
F.write(b.path('MOTION', 'transitions', 'README.md'), docs.transReadme(b, M));
F.write(b.path('GENERATIVE', 'README.md'), docs.genReadme(b, M, genOut));

/* ---------------------------------------------------------------- 9. previews */
(async () => {
  const jobs = [];
  if (!argv.includes('--no-previews')) {
    C.forEach(c => jobs.push({ in: b.path(LA, c.file) + '?still=1', out: b.path('MOTION', 'previews', `logo-${String(c.n).padStart(2, '0')}-${c.concept}.png`), w: 1600, h: 1400, selector: '#board', wait: 500 }));
    jobs.push({ in: b.path(LA, 'index.html') + '?still=1', out: b.path('MOTION', 'previews', 'logo-gallery.png'), w: 1440, h: 900, full: true, wait: 500 });
    jobs.push({ in: b.path('MOTION', 'transitions', 'index.html') + '?still=1', out: b.path('MOTION', 'previews', 'transitions.png'), w: 1440, h: 900, full: true, wait: 600 });
    jobs.push({ in: b.path('MOTION', 'transitions', 'frames.html') + '?still=1', out: b.path('MOTION', 'previews', 'transition-frames.png'), w: 1600, h: 900, selector: '#frames', wait: 400 });
    jobs.push({ in: b.path('GENERATIVE', 'sheet.html') + '?still=1', out: b.path('GENERATIVE', 'previews', 'patterns.png'), w: 1600, h: 1000, selector: '#sheet', wait: 600 });
    jobs.push({ in: b.path('GENERATIVE', 'index.html') + '?still=1', out: b.path('GENERATIVE', 'previews', 'tool.png'), w: 1440, h: 900, wait: 600 });
    // shots() resolves '?' paths as file URLs
    jobs.forEach(j => { j.in = 'file://' + j.in; });
    await F.shots(jobs);
  }
  let exp = '';
  if (argv.includes('--export')) {
    try { exp = ' · ' + await require('./export.js').run(b, C); } catch (e) { exp = ' · export skipped (' + e.message.split('\n')[0] + ')'; }
  }
  const pngs = fs.existsSync(b.path('MOTION', 'previews')) ? fs.readdirSync(b.path('MOTION', 'previews')).length : 0;
  console.log(`motion: ${C.length} logo animations (${C.map(c => c.concept).join(', ')}) · transitions gallery · ${p}-motion.css/.js · generative (${genOut.patterns.length} motifs) · ${pngs + (jobs.length ? 2 : 0)} previews${exp} · ${((Date.now() - T0) / 1000).toFixed(1)}s`);
})().catch(e => { console.error('motion: preview step failed —', e.message); process.exit(1); });
