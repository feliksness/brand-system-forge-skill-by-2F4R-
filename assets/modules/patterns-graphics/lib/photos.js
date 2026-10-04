// photos.js — PHOTOGRAPHY/placeholders (abstract, brand-coloured, labelled — never fake people),
// PHOTOGRAPHY/filters.svg (exact duotone filters for inline SVG / print), PHOTOGRAPHY/README.md (direction).
const fs = require('fs'), path = require('path');

function subjects(b) {
  const dir = ((b.dna.imagery || {}).direction || (b.profile.dna_bias || {}).imagery || '').split('—')[0];
  const items = dir.split(/[,;]/).map(s => s.trim()).filter(Boolean);
  const isQ = s => /^(natural|bright|soft|warm|calm|honest|real|documentary|candid|moody|airy|clean|crisp|dark|light)( light| colour| color| tones?)?$/i.test(s);
  const subj = items.filter(s => !isQ(s)), qual = items.filter(isQ);
  const units = (b.content.units || []).map(u => u.name).filter(Boolean);
  return { subj: subj.length ? subj : ['people at work', 'places', 'details'], qual, units, raw: (b.dna.imagery || {}).direction || '' };
}
const cap = s => s ? s[0].toLocaleUpperCase() + s.slice(1) : s;

function run(ctx) {
  const { b, F, gfx, cw, B } = ctx, U = ctx.CORE.util, f = U.f, C = gfx.C;
  const root = b.path('PHOTOGRAPHY');
  ['placeholders', 'previews'].forEach(d => fs.rmSync(path.join(root, d), { recursive: true, force: true }));
  const S = subjects(b), G = ctx.glyphs || {}, gm = G.meta || {};
  const ratios = [['16x9', 1600, 900], ['16x9', 1600, 900], ['16x9', 1600, 900], ['3x2', 1500, 1000], ['3x2', 1500, 1000], ['3x2', 1500, 1000], ['4x5', 1080, 1350], ['4x5', 1080, 1350], ['4x5', 1080, 1350], ['1x1', 1080, 1080], ['1x1', 1080, 1080], ['1x1', 1080, 1080], ['9x16', 1080, 1920], ['9x16', 1080, 1920]];
  const tones = ['light', 'mid', 'dark'];
  const list = [];
  ratios.forEach(([rk, W, H], i) => {
    const r = U.rng(U.hash(b.name + '|ph|' + i)), tone = tones[i % 3], subj = S.subj[i % S.subj.length], unit = S.units.length ? S.units[(i * 2 + Math.floor(i / 3)) % S.units.length] : '';
    const pal = tone === 'light' ? { a: cw.paper.t1, b: cw.paper.t3, s1: cw.paper.t2, s2: U.mix(cw.paper.t3, cw.paper.ink, 0.18), ink: cw.paper.ink, line: cw.paper.line }
      : tone === 'mid' ? { a: U.mix(cw.primary.bg, cw.paper.bg, 0.55), b: U.mix(cw.primary.bg, cw.foundation.bg, 0.15), s1: U.mix(cw.primary.bg, cw.paper.bg, 0.3), s2: U.mix(cw.primary.bg, cw.foundation.bg, 0.4), ink: U.contrast(U.mix(cw.primary.bg, cw.paper.bg, 0.55), cw.paper.ink) > 4.5 ? cw.paper.ink : '#FFFFFF', line: U.mix(cw.primary.bg, cw.paper.bg, 0.7) }
        : { a: cw.foundation.t1, b: cw.foundation.bg, s1: cw.foundation.t2, s2: cw.foundation.t3, ink: cw.foundation.ink, line: cw.foundation.line };
    const M = Math.min(W, H), id = 'ph' + i, horizon = H * U.range(r, 0.56, 0.68);
    let body = `<defs><linearGradient id="${id}g" x1="0" y1="0" x2="0.35" y2="1"><stop offset="0" stop-color="${pal.a}"/><stop offset="1" stop-color="${pal.b}"/></linearGradient>` +
      `<radialGradient id="${id}l" cx="${U.range(r, 0.2, 0.8).toFixed(2)}" cy="0.18" r="0.75"><stop offset="0" stop-color="#FFFFFF" stop-opacity="${tone === 'dark' ? 0.12 : 0.35}"/><stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/></radialGradient></defs>`;
    body += `<rect width="${W}" height="${H}" fill="url(#${id}g)"/>`;
    // abstract "scene" in the DNA shape language (no people, no objects — just light and planes)
    if (C.lang === 'angular' || C.corner === 'cut') {
      const dx = H / Math.tan(C.crop * Math.PI / 180);
      body += `<path d="${U.polyD([[W * U.range(r, 0.45, 0.6), 0], [W, 0], [W, H], [W * U.range(r, 0.45, 0.6) + dx, H]])}" fill="${pal.s1}" fill-opacity="0.75"/>`;
      body += `<path d="${U.polyD([[0, horizon], [W, horizon - W * Math.tan(C.shallow * Math.PI / 180)], [W, H], [0, H]])}" fill="${pal.s2}" fill-opacity="0.55"/>`;
      for (let k = 0; k < 3; k++) { const a1 = C.pickAngle(r), a2 = a1 + 40, L = M * U.range(r, 0.12, 0.26), x = W * U.range(r, 0.15, 0.85), y = horizon - L * 0.2; body += `<path d="${U.polyD([[x, y], [x + L * Math.cos(a1 * Math.PI / 180), y + L * Math.sin(a1 * Math.PI / 180)], [x + L * 0.7 * Math.cos(a2 * Math.PI / 180), y + L * 0.7 * Math.sin(a2 * Math.PI / 180)]])}" fill="${pal.s2}" fill-opacity="0.5"/>`; }
    } else if (C.lang === 'round') {
      body += `<circle cx="${f(W * U.range(r, 0.6, 0.8))}" cy="${f(H * U.range(r, 0.25, 0.4))}" r="${f(M * 0.2)}" fill="${pal.s1}" fill-opacity="0.8"/>`;
      body += `<path d="M0 ${f(horizon)}Q${f(W / 2)} ${f(horizon - M * 0.14)} ${W} ${f(horizon)}V${H}H0Z" fill="${pal.s2}" fill-opacity="0.55"/>`;
      body += `<circle cx="${f(W * U.range(r, 0.15, 0.35))}" cy="${f(horizon + (H - horizon) * 0.4)}" r="${f(M * 0.12)}" fill="${pal.s1}" fill-opacity="0.6"/>`;
    } else if (C.lang === 'organic') {
      body += `<path d="${U.smoothD(U.blobPts(r, W * U.range(r, 0.6, 0.8), H * 0.35, M * 0.3, { amp: 0.18 }), true)}" fill="${pal.s1}" fill-opacity="0.75"/>`;
      const pts = []; for (let x = -20; x <= W + 20; x += W / 20) pts.push([x, horizon + Math.sin(x / W * Math.PI * 2 + r() * 6) * M * 0.04]); body += `<path d="${U.smoothD(pts, false)}L${W + 20} ${H}L-20 ${H}Z" fill="${pal.s2}" fill-opacity="0.55"/>`;
      body += `<path d="${U.smoothD(U.blobPts(r, W * 0.22, horizon + (H - horizon) * 0.45, M * 0.12, { amp: 0.2 }), true)}" fill="${pal.s1}" fill-opacity="0.7"/>`;
    } else {
      body += `<rect x="${f(W * 0.55)}" y="0" width="${f(W * 0.45)}" height="${f(horizon)}" fill="${pal.s1}" fill-opacity="0.7"/><rect x="0" y="${f(horizon)}" width="${W}" height="${f(H - horizon)}" fill="${pal.s2}" fill-opacity="0.55"/>`;
    }
    body += `<rect width="${W}" height="${H}" fill="url(#${id}l)"/>`;
    // camera frame ticks + icon
    const m = M * 0.05, tk = M * 0.04, sw = Math.max(2, M / 400);
    body += `<path d="M${f(m)} ${f(m + tk)}V${f(m)}H${f(m + tk)}M${f(W - m - tk)} ${f(m)}H${f(W - m)}V${f(m + tk)}M${f(W - m)} ${f(H - m - tk)}V${f(H - m)}H${f(W - m - tk)}M${f(m + tk)} ${f(H - m)}H${f(m)}V${f(H - m - tk)}" fill="none" stroke="${pal.ink}" stroke-opacity="0.55" stroke-width="${f(sw)}"/>`;
    const ic = M * 0.07, cx = W / 2, cy = H / 2;
    body += `<g fill="none" stroke="${pal.ink}" stroke-opacity="0.5" stroke-width="${f(sw * 1.4)}" stroke-linecap="${C.cap}" stroke-linejoin="${C.join}"><path d="${C.corner === 'cut' ? U.polyD([[cx - ic, cy - ic * 0.75], [cx + ic, cy - ic * 0.75], [cx + ic, cy + ic * 0.45], [cx + ic * 0.7, cy + ic * 0.75], [cx - ic, cy + ic * 0.75]]) : `M${f(cx - ic)} ${f(cy - ic * 0.75)}h${f(2 * ic)}v${f(1.5 * ic)}h${f(-2 * ic)}Z`}"/><path d="M${f(cx - ic)} ${f(cy + ic * 0.45)}L${f(cx - ic * 0.3)} ${f(cy - ic * 0.15)}L${f(cx + ic * 0.15)} ${f(cy + ic * 0.25)}L${f(cx + ic * 0.45)} ${f(cy + ic * 0.02)}L${f(cx + ic)} ${f(cy + ic * 0.45)}"/><circle cx="${f(cx + ic * 0.45)}" cy="${f(cy - ic * 0.38)}" r="${f(ic * 0.13)}"/></g>`;
    // labels (outlined brand label font)
    const ls = Math.max(18, M * 0.026), lo = { size: ls, fill: pal.ink, upper: gm.labelUpper !== false, tracking: gm.labelTracking || 0.06 };
    const txt = (s, x, y, o) => G.label && G.label.glyphs ? B.textSVG(G.label, s, x, y, Object.assign({}, lo, o)).svg : `<text x="${f(x)}" y="${f(y)}" font-family="${(b.stacks.mono || 'monospace').replace(/"/g, "'")}" font-size="${f((o && o.size) || ls)}" fill="${pal.ink}" text-anchor="${(o && o.anchor) || 'start'}">${s}</text>`;
    body += txt(`PHOTO · ${rk.replace('x', ':')}`, m + tk * 0.2, m + tk + ls * 1.4, {});
    const subjLine = cap(subj) + (unit ? ' · ' + unit : '');
    let sz = ls * 1.15; if (G.label && G.label.glyphs) { const w = B.textSVG(G.label, subjLine, 0, 0, Object.assign({}, lo, { size: sz })).w; if (w > W - 2 * m - tk) sz *= (W - 2 * m - tk) / w; }
    body += txt(subjLine, m + tk * 0.2, H - m - tk - ls * 0.6, { size: sz });
    body += txt(`${W}×${H}`, W - m - tk * 0.2, m + tk + ls * 1.4, { anchor: 'end', size: ls * 0.85 });
    const name = `ph-${rk}-${String(i + 1).padStart(2, '0')}`;
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-label="Photo placeholder ${rk.replace('x', ':')} — ${subjLine}"><title>${b.name} · photo placeholder · ${subjLine}</title>${body}</svg>`;
    F.write(path.join(root, 'placeholders', name + '.svg'), svg);
    ctx.rasters.push({ svg, out: path.join(root, 'placeholders', name + '.png'), palette: true, dither: 1 });
    list.push({ name, ratio: rk.replace('x', ':'), w: W, h: H, subject: subjLine, tone, svg: `PHOTOGRAPHY/placeholders/${name}.svg`, png: `PHOTOGRAPHY/placeholders/${name}.png` });
  });
  ctx.placeholders = list; ctx.counts.placeholders = list.length;
  // demo "photograph" for the crops board only (neutral, full tonal range, no people, no brand colours) — shows what masks/treatments do
  const dr = U.rng(U.hash(b.name + '|demo')), DW = 1200, DH = 900;
  let scene = `<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#F3EEE6"/><stop offset="0.55" stop-color="#D9D2C6"/><stop offset="1" stop-color="#8E8578"/></linearGradient>
    <filter id="bl" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="14"/></filter><filter id="bl2"><feGaussianBlur stdDeviation="3"/></filter>
    <filter id="gr"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="4"/><feColorMatrix values="0 0 0 0 0.5  0 0 0 0 0.5  0 0 0 0 0.5  0 0 0 0.16 0"/></filter>
    <radialGradient id="sun" cx="0.72" cy="0.18" r="0.6"><stop offset="0" stop-color="#FFF8EA" stop-opacity="0.95"/><stop offset="1" stop-color="#FFF8EA" stop-opacity="0"/></radialGradient></defs>
    <rect width="${DW}" height="${DH}" fill="url(#sky)"/><rect width="${DW}" height="${DH}" fill="url(#sun)"/>`;
  if (C.lang === 'angular' || C.corner === 'cut') { // architecture: lit and shaded planes
    scene += `<g filter="url(#bl2)"><path d="M140 900L140 260L520 120L520 900Z" fill="#E9E4DB"/><path d="M520 120L760 230L760 900L520 900Z" fill="#9C9488"/><path d="M760 230L1200 380L1200 900L760 900Z" fill="#6E675E"/><path d="M0 900L0 520L140 480L140 900Z" fill="#B7AFA3"/>`;
    for (let i = 0; i < 6; i++) scene += `<rect x="${180 + i * 54}" y="${300 + (i % 2) * 6}" width="30" height="420" fill="#CFC8BC"/>`;
    scene += `<path d="M0 820L1200 760L1200 900L0 900Z" fill="#3B3631"/></g>`;
  } else if (C.lang === 'round') { // soft interior with round lamps and bokeh
    scene += `<g filter="url(#bl)">${Array.from({ length: 9 }, (_, i) => `<circle cx="${f(100 + dr() * 1000)}" cy="${f(80 + dr() * 380)}" r="${f(30 + dr() * 70)}" fill="#FFF6E4" fill-opacity="${f(0.35 + dr() * 0.4)}"/>`).join('')}</g>
      <g filter="url(#bl2)"><path d="M0 640Q600 560 1200 640V900H0Z" fill="#A79F92"/><circle cx="380" cy="560" r="150" fill="#857C70"/><circle cx="840" cy="610" r="110" fill="#6F675C"/><path d="M0 800Q600 760 1200 800V900H0Z" fill="#3F3A34"/></g>`;
  } else if (C.lang === 'organic') { // window light over soft organic forms on a table
    scene += `<g filter="url(#bl)"><path d="M700 0L1200 0L1200 520L860 700Z" fill="#FFF7E8" fill-opacity="0.75"/></g><g filter="url(#bl2)"><path d="M0 610C300 570 800 590 1200 620V900H0Z" fill="#A59A8A"/>
      <path d="${U.smoothD(U.blobPts(dr, 420, 560, 150, { amp: 0.16 }), true)}" fill="#7D7366"/><path d="${U.smoothD(U.blobPts(dr, 760, 600, 100, { amp: 0.2 }), true)}" fill="#C9BFAF"/><path d="M0 800C400 770 800 790 1200 810V900H0Z" fill="#3E3832"/></g>`;
  } else { scene += `<g filter="url(#bl2)"><rect x="120" y="200" width="420" height="700" fill="#E3DDD3"/><rect x="540" y="300" width="320" height="600" fill="#968E82"/><rect x="860" y="380" width="340" height="520" fill="#6C655C"/><rect y="800" width="1200" height="100" fill="#3B3631"/></g>`; }
  scene += `<rect width="${DW}" height="${DH}" filter="url(#gr)"/>`;
  ctx.rasters.push({ svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${DW} ${DH}" width="${DW}" height="${DH}">${scene}</svg>`, out: path.join(root, 'previews', 'demo-scene.png'), palette: false });
  ctx.demoScene = 'PHOTOGRAPHY/previews/demo-scene.png';
  // exact duotone filters (feColorMatrix tables) for inline SVG / print workflows
  const hexF = (h) => [1, 3, 5].map(k => parseInt(h.substr(k, 2), 16) / 255);
  const duo = (id, dark, light) => { const d = hexF(dark), l = hexF(light); return `<filter id="${id}" color-interpolation-filters="sRGB"><feColorMatrix type="matrix" values="0.2126 0.7152 0.0722 0 0  0.2126 0.7152 0.0722 0 0  0.2126 0.7152 0.0722 0 0  0 0 0 1 0"/><feComponentTransfer><feFuncR type="table" tableValues="${d[0].toFixed(3)} ${l[0].toFixed(3)}"/><feFuncG type="table" tableValues="${d[1].toFixed(3)} ${l[1].toFixed(3)}"/><feFuncB type="table" tableValues="${d[2].toFixed(3)} ${l[2].toFixed(3)}"/></feComponentTransfer></filter>`; };
  const ramp = (b.colors.ramps || {}).primary || {};
  F.write(path.join(root, 'filters.svg'), `<svg xmlns="http://www.w3.org/2000/svg" width="0" height="0" style="position:absolute" aria-hidden="true">\n<!-- ${b.name} photo filters — paste into a page (or reference) and use filter="url(#${b.p}-duotone)" on <image>/<g>. Generated by patterns-graphics. -->\n<defs>\n${duo(b.p + '-duotone', b.role.foundation, b.role.paper)}\n${duo(b.p + '-duotone-brand', b.role.foundation, U.visible(b.role.foundation, [ramp['200'], ramp['100'], b.role.primary], 4))}\n${duo(b.p + '-duotone-primary', U.mix(b.role.primary, b.role.foundation, 0.6), b.role.primary)}\n<filter id="${b.p}-mono" color-interpolation-filters="sRGB"><feColorMatrix type="saturate" values="0"/><feComponentTransfer><feFuncR type="linear" slope="0.92" intercept="0.04"/><feFuncG type="linear" slope="0.92" intercept="0.04"/><feFuncB type="linear" slope="0.92" intercept="0.04"/></feComponentTransfer></filter>\n</defs>\n</svg>\n`);
  ctx.photoSubjects = S;
}
module.exports = { run, subjects };
