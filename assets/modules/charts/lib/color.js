// Chart colour science: WCAG contrast, OKLab/OKLCH, CVD simulation (Machado 2009, severity 1), snapping and palette assembly.
'use strict';
const hex2rgb = h => { h = h.replace('#', ''); return [0, 2, 4].map(i => parseInt(h.substr(i, 2), 16) / 255); };
const rgb2hex = c => '#' + c.map(v => ('0' + Math.round(Math.max(0, Math.min(1, v)) * 255).toString(16)).slice(-2)).join('').toUpperCase();
const s2l = c => c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
const l2s = c => { c = Math.max(0, Math.min(1, c)); return c <= 0.0031308 ? 12.92 * c : 1.055 * Math.pow(c, 1 / 2.4) - 0.055; };
const lin = h => hex2rgb(h).map(s2l);
const relLum = h => { const [r, g, b] = lin(h); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
const contrast = (a, b) => { const x = relLum(a), y = relLum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
function oklabL([r, g, b]) {
  const l = Math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b), m = Math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b), s = Math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b);
  return [0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s, 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s, 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s];
}
function oklab2lin([L, a, b]) {
  const l = Math.pow(L + 0.3963377774 * a + 0.2158037573 * b, 3), m = Math.pow(L - 0.1055613458 * a - 0.0638541728 * b, 3), s = Math.pow(L - 0.0894841775 * a - 1.2914855480 * b, 3);
  return [4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s, -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s, -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s];
}
const oklab = h => oklabL(lin(h));
const oklch = h => { const [L, a, b] = oklab(h); return [L, Math.hypot(a, b), Math.atan2(b, a)]; };
function fromOklch(L, C, H) { // reduce chroma until in gamut
  for (let c = C; c >= 0; c -= 0.005) { const rgb = oklab2lin([L, c * Math.cos(H), c * Math.sin(H)]); if (rgb.every(v => v >= -0.0005 && v <= 1.0005)) return rgb2hex(rgb.map(l2s)); }
  return rgb2hex(oklab2lin([L, 0, 0]).map(l2s));
}
const MACHADO = {
  protan: [[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216], [-0.003882, -0.048116, 1.051998]],
  deutan: [[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.011820, 0.042940, 0.968881]]
};
function sim(h, k) { const [r, g, b] = lin(h), M = MACHADO[k], c = v => Math.max(0, Math.min(1, v)); return [c(M[0][0] * r + M[0][1] * g + M[0][2] * b), c(M[1][0] * r + M[1][1] * g + M[1][2] * b), c(M[2][0] * r + M[2][1] * g + M[2][2] * b)]; }
function dE(a, b, k) { const x = oklabL(k ? sim(a, k) : lin(a)), y = oklabL(k ? sim(b, k) : lin(b)); return 100 * Math.hypot(x[0] - y[0], x[1] - y[1], x[2] - y[2]); }
const dECVD = (a, b) => Math.min(dE(a, b, 'protan'), dE(a, b, 'deutan'));

/** Nearest colour to `c` (same family) that reaches `min` contrast on every surface: ramp steps first (documented palette), else OKLCH lightness. */
function snap(c, surfaces, min, ramps) {
  const ok = h => Math.min(...surfaces.map(s => contrast(h, s))) >= min;
  if (ok(c)) return { hex: c, how: 'as is' };
  const [, , H0] = oklch(c);
  const cands = [];
  for (const [rk, ramp] of Object.entries(ramps)) for (const [step, h] of Object.entries(ramp || {})) {
    if (!/^#[0-9A-F]{6}$/i.test(h)) continue;
    const [, C2, H2] = oklch(h); let dh = Math.abs(H2 - H0); dh = Math.min(dh, Math.PI * 2 - dh);
    if (C2 > 0.03 && dh < 0.35 && ok(h)) cands.push({ hex: h.toUpperCase(), d: dE(c, h), how: `${rk} ramp ${step}` });
  }
  cands.sort((a, b) => a.d - b.d);
  if (cands.length) return cands[0];
  const [L, C, H] = oklch(c), dir = relLum(surfaces[0]) > 0.4 ? -1 : 1;
  for (let k = 1; k <= 60; k++) { const h = fromOklch(Math.max(0, Math.min(1, L + dir * k * 0.01)), C, H); if (ok(h)) return { hex: h, how: `lightness ${dir < 0 ? '−' : '+'}${k}` }; }
  return { hex: c, how: 'relief (below 3:1 — labels/texture required)', relief: true };
}

/** Assemble the chart palette for one theme. order = forge categorical order (primary, accent, secondary, ramp). */
function buildTheme(order, surfaces, ramps, extra, n, keep) {
  const slots = [], pool = order.concat(extra), dark = relLum(surfaces[0]) < 0.2;
  for (const c of pool) {
    if (!c || slots.length >= n) continue;
    const s = snap(c.toUpperCase(), surfaces, 3, ramps), L = oklch(s.hex)[0];
    // lightness band: no near-black series on light surfaces (brand foundation excepted), no near-white on dark
    if (!dark && L < 0.27 && (!keep || s.hex !== keep.toUpperCase())) continue;
    if (dark && L > 0.97) continue;
    const near = slots.some(x => dE(x.hex, s.hex) < 11);
    if (near) continue;
    slots.push({ hex: s.hex, from: c.toUpperCase(), how: s.how, relief: !!s.relief, contrast: +Math.min(...surfaces.map(x => contrast(s.hex, x))).toFixed(2) });
  }
  // greedy reorder after the first two (primary, accent stay): maximise adjacent CVD separation
  const k = slots.length > 2 && dECVD(slots[0].hex, slots[1].hex) < 8 ? 1 : 2;   // accent stays 2nd unless it collapses into the primary under CVD
  const head = slots.slice(0, k), rest = slots.slice(k), out = head.slice();
  while (rest.length) { const last = out[out.length - 1].hex; rest.sort((a, b) => dECVD(b.hex, last) - dECVD(a.hex, last)); out.push(rest.shift()); }
  out.forEach((s, i) => {
    if (i) { s.adjCVD = +dECVD(out[i - 1].hex, s.hex).toFixed(1); s.adjNormal = +dE(out[i - 1].hex, s.hex).toFixed(1); s.texture = s.adjCVD < 8; }
  });
  return out;
}
module.exports = { contrast, oklch, dE, dECVD, snap, buildTheme, relLum, fromOklch, rgb2hex, hex2rgb };
