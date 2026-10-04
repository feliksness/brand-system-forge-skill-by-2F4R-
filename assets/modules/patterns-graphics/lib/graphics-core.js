/* ==========================================================================
   graphics-core.js — brand-neutral graphic-language engine (patterns-graphics module)
   One source for the Node build AND the browser (copied into SOURCE/JS/<p>-graphics.js).
   Everything is derived from data: the mark geometry, the design DNA and the colourways.
   Deterministic: every generator gets a seeded RNG (hash of brand name + pattern + seed).

   const core = GFXFactory();               // CommonJS: require('./graphics-core.js')
   const g = core.create(cfg);              // cfg: { name, dna, unit, mark, colourways }
   g.catalogue            → [{ key, family, title, tags, tile }]
   g.pattern(key, cw, o)  → { w, h, body, tile }       (body without background)
   g.tileSVG(key, cw, o)  → standalone seamless SVG tile (with <rect id="bg">)
   g.swatchSVG(key, cw, W, H, o) → SVG W×H filled with the repeating tile
   g.motif(name, o)       → { w, h, body }       motif shapes (shard, blob, orbit-ring …)
   g.composition(cw, W, H, o) → { body, safe }   background compositions
   ========================================================================== */
function GFXFactory() {
  'use strict';
  var D2R = Math.PI / 180, TAU = Math.PI * 2;

  /* ------------------------------------------------------------------ numbers & random */
  function hash(s) { s = String(s); var h = 1779033703 ^ s.length; for (var i = 0; i < s.length; i++) { h = Math.imul(h ^ s.charCodeAt(i), 3432918353); h = (h << 13) | (h >>> 19); } return h >>> 0; }
  function rng(seed) { var a = (typeof seed === 'number' ? seed : hash(seed)) >>> 0; return function () { a |= 0; a = (a + 0x6D2B79F5) | 0; var t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
  function f(n) { if (!isFinite(n)) return '0'; var v = Math.round(n * 100) / 100; return (Math.abs(v) < 0.005 ? 0 : v).toString(); }
  function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
  function lerp(a, b, t) { return a + (b - a) * t; }
  function pick(r, arr) { return arr[Math.floor(r() * arr.length) % arr.length]; }
  function wpick(r, items, weights) { var s = 0, i; for (i = 0; i < weights.length; i++) s += weights[i]; var x = r() * s; for (i = 0; i < items.length; i++) { x -= weights[i]; if (x <= 0) return items[i]; } return items[items.length - 1]; }
  function range(r, a, b) { return a + r() * (b - a); }

  /* ------------------------------------------------------------------ colour */
  function h2r(h) { h = String(h).replace('#', ''); if (h.length === 3) h = h.replace(/(.)/g, '$1$1'); return [0, 2, 4].map(function (i) { return parseInt(h.substr(i, 2), 16); }); }
  function r2h(c) { return '#' + c.map(function (v) { return ('0' + Math.round(clamp(v, 0, 255)).toString(16)).slice(-2); }).join('').toUpperCase(); }
  function mix(a, b, t) { var x = h2r(a), y = h2r(b); return r2h(x.map(function (v, i) { return v + (y[i] - v) * t; })); }
  function lum(h) { return h2r(h).map(function (v) { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }).reduce(function (s, v, i) { return s + v * [0.2126, 0.7152, 0.0722][i]; }, 0); }
  function contrast(a, b) { var x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); }
  function visible(bg, cands, min) { for (var i = 0; i < cands.length; i++) if (cands[i] && contrast(bg, cands[i]) >= min) return cands[i]; var best = cands[0], bc = 0; cands.forEach(function (c) { if (c && contrast(bg, c) > bc) { bc = contrast(bg, c); best = c; } }); return best; }

  /** Three colourways shared by every pattern and graphic. Restrained: t1–t3 are close to the ground so text
   *  can sit on a panel above; `accent` is the one energetic thing per tile. */
  function makeColourways(o) {
    var P = o.primary, F = o.foundation, W = o.paper, A = o.accent || o.primary, ramp = o.ramp || {};
    var onP = o.onPrimary || (contrast(P, '#FFFFFF') >= contrast(P, F) ? '#FFFFFF' : F);
    var pf = mix(P, F, 0.22);
    // a primary that reads on the foundation (dark grounds)
    var Pd = visible(F, [P, ramp['300'], ramp['200'], ramp['100'], mix(P, '#FFFFFF', 0.4)], 3);
    var playful = !!o.playful;
    var paper = { key: 'paper', label: 'On paper', bg: W, ink: F, t1: mix(W, pf, 0.07), t2: mix(W, pf, 0.14), t3: mix(W, pf, 0.25),
      line: mix(W, F, 0.17), soft: mix(W, F, 0.34), accent: visible(W, [P, ramp['500'], ramp['600']], 1.7), accent2: visible(W, [A, P], 1.4), dark: false };
    var Pg = mix(W, Pd, 0.22);
    var found = { key: 'foundation', label: 'On foundation', bg: F, ink: W, t1: mix(F, Pg, 0.08), t2: mix(F, Pg, 0.15), t3: mix(F, Pg, 0.26),
      line: mix(F, W, 0.15), soft: mix(F, W, 0.32), accent: Pd, accent2: visible(F, [A, ramp['200'], W], 3), dark: true };
    var prim = { key: 'primary', label: 'On primary', bg: P, ink: onP, t1: mix(P, onP, 0.07), t2: mix(P, onP, 0.14), t3: mix(P, onP, 0.25),
      line: mix(P, onP, 0.22), soft: mix(P, onP, 0.4), accent: visible(P, [A !== P ? A : null, F, onP], 2.2), accent2: visible(P, [W, onP], 2), dark: lum(P) < 0.18 };
    [paper, found, prim].forEach(function (c) { c.accents = playful ? [c.accent, c.accent2, c.t3] : [c.accent]; c.playful = playful; });
    return { paper: paper, foundation: found, primary: prim };
  }

  /* ------------------------------------------------------------------ geometry */
  function dir(deg) { return [Math.cos(deg * D2R), Math.sin(deg * D2R)]; }
  /** Flatten an SVG path (M L H V C S Q T Z, abs + rel) into sub-polygons. */
  function parsePath(d, tx, ty, seg) {
    tx = tx || 0; ty = ty || 0; seg = seg || 6;
    var toks = String(d).match(/[MLHVCSQTAZmlhvcsqtaz]|-?(?:\d+\.?\d*|\.\d+)(?:e[-+]?\d+)?/g) || [];
    var subs = [], cur = null, x = 0, y = 0, sx = 0, sy = 0, cmd = '', i = 0, lcx = 0, lcy = 0, lq = null;
    function num() { return parseFloat(toks[i++]); }
    function push(px, py) { if (!cur) { cur = []; subs.push(cur); } cur.push([px + tx, py + ty]); }
    function cubic(x1, y1, x2, y2, x3, y3) { for (var k = 1; k <= seg; k++) { var t = k / seg, u = 1 - t; push(u * u * u * x + 3 * u * u * t * x1 + 3 * u * t * t * x2 + t * t * t * x3, u * u * u * y + 3 * u * u * t * y1 + 3 * u * t * t * y2 + t * t * t * y3); } }
    while (i < toks.length) {
      if (/[A-Za-z]/.test(toks[i])) cmd = toks[i++];
      var rel = cmd === cmd.toLowerCase(), C = cmd.toUpperCase(), ox = rel ? x : 0, oy = rel ? y : 0;
      if (C === 'Z') { x = sx; y = sy; cur = null; continue; }
      if (C === 'M') { x = num() + ox; y = num() + oy; sx = x; sy = y; cur = null; push(x, y); cmd = rel ? 'l' : 'L'; lq = null; continue; }
      if (C === 'L') { x = num() + ox; y = num() + oy; push(x, y); }
      else if (C === 'H') { x = num() + ox; push(x, y); }
      else if (C === 'V') { y = num() + oy; push(x, y); }
      else if (C === 'C') { var a1 = num() + ox, b1 = num() + oy, a2 = num() + ox, b2 = num() + oy, a3 = num() + ox, b3 = num() + oy; cubic(a1, b1, a2, b2, a3, b3); lcx = a2; lcy = b2; x = a3; y = b3; lq = 'c'; continue; }
      else if (C === 'S') { var r1x = lq === 'c' ? 2 * x - lcx : x, r1y = lq === 'c' ? 2 * y - lcy : y, s2 = num() + ox, t2 = num() + oy, s3 = num() + ox, t3 = num() + oy; cubic(r1x, r1y, s2, t2, s3, t3); lcx = s2; lcy = t2; x = s3; y = t3; lq = 'c'; continue; }
      else if (C === 'Q' || C === 'T') { var qx, qy; if (C === 'Q') { qx = num() + ox; qy = num() + oy; } else { qx = lq === 'q' ? 2 * x - lcx : x; qy = lq === 'q' ? 2 * y - lcy : y; } var ex = num() + ox, ey = num() + oy; cubic(x + 2 / 3 * (qx - x), y + 2 / 3 * (qy - y), ex + 2 / 3 * (qx - ex), ey + 2 / 3 * (qy - ey), ex, ey); lcx = qx; lcy = qy; x = ex; y = ey; lq = 'q'; continue; }
      else if (C === 'A') { num(); num(); num(); num(); num(); x = num() + ox; y = num() + oy; push(x, y); }
      else { i++; }
      lq = null;
    }
    return subs.filter(function (s) { return s.length > 1; });
  }
  function bbox(pts) { var b = [Infinity, Infinity, -Infinity, -Infinity]; pts.forEach(function (p) { if (p[0] < b[0]) b[0] = p[0]; if (p[1] < b[1]) b[1] = p[1]; if (p[0] > b[2]) b[2] = p[0]; if (p[1] > b[3]) b[3] = p[1]; }); return b; }
  function area(pts) { var s = 0; for (var i = 0, n = pts.length; i < n; i++) { var a = pts[i], b = pts[(i + 1) % n]; s += a[0] * b[1] - b[0] * a[1]; } return s / 2; }
  function centroid(pts) { var A = area(pts), cx = 0, cy = 0; if (Math.abs(A) < 1e-9) { var bb = bbox(pts); return [(bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2]; } for (var i = 0, n = pts.length; i < n; i++) { var a = pts[i], b = pts[(i + 1) % n], c = a[0] * b[1] - b[0] * a[1]; cx += (a[0] + b[0]) * c; cy += (a[1] + b[1]) * c; } return [cx / (6 * A), cy / (6 * A)]; }
  function inPoly(p, pts) { var c = false; for (var i = 0, j = pts.length - 1; i < pts.length; j = i++) { var a = pts[i], b = pts[j]; if (((a[1] > p[1]) !== (b[1] > p[1])) && (p[0] < (b[0] - a[0]) * (p[1] - a[1]) / (b[1] - a[1]) + a[0])) c = !c; } return c; }
  function xform(pts, o) { var c = Math.cos((o.r || 0) * D2R), s = Math.sin((o.r || 0) * D2R), k = o.s == null ? 1 : o.s, ox = o.ox || 0, oy = o.oy || 0; return pts.map(function (p) { var x = (p[0] - ox) * k * (o.fx || 1), y = (p[1] - oy) * k; return [(o.x || 0) + x * c - y * s, (o.y || 0) + x * s + y * c]; }); }
  function polyD(pts, open) { return 'M' + pts.map(function (p) { return f(p[0]) + ' ' + f(p[1]); }).join('L') + (open ? '' : 'Z'); }
  function smoothD(pts, closed, t, trim) {
    t = t == null ? 1 : t; var n = pts.length; if (n < 3) return polyD(pts, !closed);
    var P = function (i) { return closed ? pts[(i + n) % n] : pts[clamp(i, 0, n - 1)]; };
    var s0 = trim && !closed ? 1 : 0, d = 'M' + f(pts[s0][0]) + ' ' + f(pts[s0][1]), last = closed ? n : n - 1 - s0;
    for (var i = s0; i < last; i++) { var p0 = P(i - 1), p1 = P(i), p2 = P(i + 1), p3 = P(i + 2);
      d += 'C' + f(p1[0] + (p2[0] - p0[0]) / 6 * t) + ' ' + f(p1[1] + (p2[1] - p0[1]) / 6 * t) + ' ' + f(p2[0] - (p3[0] - p1[0]) / 6 * t) + ' ' + f(p2[1] - (p3[1] - p1[1]) / 6 * t) + ' ' + f(p2[0]) + ' ' + f(p2[1]); }
    return d + (closed ? 'Z' : '');
  }
  function circleD(cx, cy, r) { return 'M' + f(cx - r) + ' ' + f(cy) + 'a' + f(r) + ' ' + f(r) + ' 0 1 0 ' + f(2 * r) + ' 0a' + f(r) + ' ' + f(r) + ' 0 1 0 ' + f(-2 * r) + ' 0Z'; }
  function arcPts(cx, cy, r, a0, a1, n) { var o = []; n = n || Math.max(8, Math.ceil(Math.abs(a1 - a0) / 6)); for (var i = 0; i <= n; i++) { var a = (a0 + (a1 - a0) * i / n) * D2R; o.push([cx + r * Math.cos(a), cy + r * Math.sin(a)]); } return o; }
  function convexHull(P) { var pts = P.slice().sort(function (a, b) { return a[0] - b[0] || a[1] - b[1]; }); if (pts.length < 3) return pts; var cr = function (o, a, b) { return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]); }; var lo = [], up = [], i; for (i = 0; i < pts.length; i++) { while (lo.length >= 2 && cr(lo[lo.length - 2], lo[lo.length - 1], pts[i]) <= 0) lo.pop(); lo.push(pts[i]); } for (i = pts.length - 1; i >= 0; i--) { while (up.length >= 2 && cr(up[up.length - 2], up[up.length - 1], pts[i]) <= 0) up.pop(); up.push(pts[i]); } up.pop(); lo.pop(); return lo.concat(up); }

  /** Organic closed blob: radial harmonics, smoothed. */
  function blobPts(r, cx, cy, R, o) {
    o = o || {}; var n = o.n || 36, H = [], k; var amp = o.amp == null ? 0.16 : o.amp;
    for (k = 2; k <= (o.kmax || 4); k++) H.push([k, (r() * 2 - 1) * amp / (k - 1), r() * TAU]);
    var pts = []; for (var i = 0; i < n; i++) { var a = i / n * TAU, m = 1; H.forEach(function (h) { m += h[1] * Math.sin(h[0] * a + h[2]); }); pts.push([cx + Math.cos(a) * R * m * (o.sx || 1), cy + Math.sin(a) * R * m * (o.sy || 1)]); }
    if (o.rot) pts = xform(pts, { r: o.rot, ox: cx, oy: cy, x: cx, y: cy });
    return pts;
  }

  /** Bowyer–Watson Delaunay (fine for ≤ 1500 points). Returns [[i,j,k]…]. */
  function delaunay(P) {
    var n = P.length; if (n < 3) return [];
    var b = bbox(P), dx = b[2] - b[0], dy = b[3] - b[1], dm = Math.max(dx, dy) * 20, mx = (b[0] + b[2]) / 2, my = (b[1] + b[3]) / 2;
    var pts = P.concat([[mx - dm, my - dm], [mx, my + dm], [mx + dm, my - dm]]);
    function circ(a, bb, c) { var A = pts[a], B = pts[bb], Cc = pts[c], d = 2 * (A[0] * (B[1] - Cc[1]) + B[0] * (Cc[1] - A[1]) + Cc[0] * (A[1] - B[1])); if (Math.abs(d) < 1e-12) return { a: a, b: bb, c: c, x: 0, y: 0, r: Infinity };
      var a2 = A[0] * A[0] + A[1] * A[1], b2 = B[0] * B[0] + B[1] * B[1], c2 = Cc[0] * Cc[0] + Cc[1] * Cc[1];
      var x = (a2 * (B[1] - Cc[1]) + b2 * (Cc[1] - A[1]) + c2 * (A[1] - B[1])) / d, y = (a2 * (Cc[0] - B[0]) + b2 * (A[0] - Cc[0]) + c2 * (B[0] - A[0])) / d;
      return { a: a, b: bb, c: c, x: x, y: y, r: (A[0] - x) * (A[0] - x) + (A[1] - y) * (A[1] - y) }; }
    var tris = [circ(n, n + 1, n + 2)];
    for (var i = 0; i < n; i++) {
      var p = pts[i], keep = [], edges = {};
      for (var t = 0; t < tris.length; t++) { var T = tris[t], ex = p[0] - T.x, ey = p[1] - T.y;
        if (ex * ex + ey * ey < T.r) { [[T.a, T.b], [T.b, T.c], [T.c, T.a]].forEach(function (e) { var k = e[0] < e[1] ? e[0] + ',' + e[1] : e[1] + ',' + e[0]; edges[k] = edges[k] ? 'x' : e; }); }
        else keep.push(T); }
      Object.keys(edges).forEach(function (k) { var e = edges[k]; if (e !== 'x') keep.push(circ(e[0], e[1], i)); });
      tris = keep;
    }
    return tris.filter(function (T) { return T.a < n && T.b < n && T.c < n; }).map(function (T) { return [T.a, T.b, T.c]; });
  }

  /** Periodic Poisson-disc sampling on a W×H torus (dart throwing). */
  function poisson(W, H, r, rnd, max) {
    var pts = [], tries = Math.ceil(W * H / (r * r) * 30), r2 = r * r; max = max || 1e9;
    for (var t = 0; t < tries && pts.length < max; t++) { var x = rnd() * W, y = rnd() * H, ok = true;
      for (var j = 0; j < pts.length; j++) { var dx = Math.abs(x - pts[j][0]), dy = Math.abs(y - pts[j][1]); dx = Math.min(dx, W - dx); dy = Math.min(dy, H - dy); if (dx * dx + dy * dy < r2) { ok = false; break; } }
      if (ok) pts.push([x, y]); }
    return pts;
  }
  /** Periodic smooth field on the tile (integer frequencies → seamless). Returns f(x,y) in [-1,1]. */
  function field(rnd, W, H, n, kmax) {
    var T = [], s = 0; n = n || 4; kmax = kmax || 2;
    for (var i = 0; i < n; i++) { var kx = Math.round(range(rnd, -kmax, kmax)), ky = Math.round(range(rnd, -kmax, kmax)); if (!kx && !ky) kx = 1; var a = 1 / Math.sqrt(kx * kx + ky * ky); T.push([kx, ky, a, rnd() * TAU]); s += a; }
    return function (x, y) { var v = 0; for (var i = 0; i < T.length; i++) v += T[i][2] * Math.sin(TAU * (T[i][0] * x / W + T[i][1] * y / H) + T[i][3]); return v / s; };
  }
  function tdist(a, b, W, H) { var dx = Math.abs(a[0] - b[0]), dy = Math.abs(a[1] - b[1]); dx = Math.min(dx, W - dx); dy = Math.min(dy, H - dy); return Math.sqrt(dx * dx + dy * dy); }

  /* ------------------------------------------------------------------ tile emission (periodic copies) */
  function offsets(bb, W, H) { var o = []; var x0 = Math.ceil((0 - bb[2]) / W), x1 = Math.floor((W - bb[0]) / W), y0 = Math.ceil((0 - bb[3]) / H), y1 = Math.floor((H - bb[1]) / H);
    for (var i = x0; i <= x1; i++) for (var j = y0; j <= y1; j++) o.push([i * W, j * H]); return o; }
  function Tile(W, H) {
    var out = [];
    return { W: W, H: H, out: out,
      add: function (markup, bb) { if (!bb) { out.push(markup); return; } offsets(bb, W, H).forEach(function (o) { out.push(o[0] || o[1] ? '<g transform="translate(' + f(o[0]) + ' ' + f(o[1]) + ')">' + markup + '</g>' : markup); }); },
      poly: function (pts, attrs) { this.add('<path d="' + polyD(pts) + '" ' + attrs + '/>', bbox(pts)); },
      path: function (d, pts, attrs) { this.add('<path d="' + d + '" ' + attrs + '/>', bbox(pts)); },
      circle: function (x, y, r, attrs) { this.add('<circle cx="' + f(x) + '" cy="' + f(y) + '" r="' + f(r) + '" ' + attrs + '/>', [x - r - 2, y - r - 2, x + r + 2, y + r + 2]); },
      done: function () { return { w: W, h: H, body: out.join(''), tile: true }; } };
  }
  function fill(c, op) { return 'fill="' + c + '"' + (op != null && op < 1 ? ' fill-opacity="' + f(op) + '"' : ''); }
  function stroke(c, w, o) { o = o || {}; return 'fill="none" stroke="' + c + '" stroke-width="' + f(w) + '" stroke-linecap="' + (o.cap || 'round') + '" stroke-linejoin="' + (o.join || 'round') + '"' + (o.op != null ? ' stroke-opacity="' + f(o.op) + '"' : ''); }

  /** mark units from window.<G>_MARK (mark-data.js): { mark, unit } — unit = what repeats (the mark, or a monogram for wordmarks) */
  function fromMarkData(M, logoType, monogram) {
    if (!M) return { mark: monogram || null, unit: monogram || null };
    var vb = M.viewBox, oc = M.opticalCenter || [0.5, 0.5], lt = logoType || M.logoType || 'symbol';
    var conv = function (q) { return { d: q.d, p: q.p, tx: q.tx || 0, ty: q.ty || 0, l: q.l, c: q.c, od: q.od }; };
    var mark = { kind: lt === 'emblem' ? 'emblem' : lt === 'wordmark' ? 'wordmark' : 'symbol', vb: vb, oc: [vb[0] + oc[0] * vb[2], vb[1] + oc[1] * vb[3]],
      parts: (M.simplified || M.master).map(conv), master: (M.master || []).map(conv), sil: M.silhouetteD || null, silPts: M.silhouette || null };
    return { mark: mark, unit: lt === 'wordmark' && monogram ? monogram : mark };
  }

  /* ================================================================== create(cfg) */
  function create(cfg) {
    var dna = cfg.dna || {}, ang = dna.angles || {}, st = dna.stroke || {};
    var lang = dna.base_language || 'mixed', corner = (dna.corner || {}).style || 'square';
    var C = {
      name: cfg.name || 'brand', lang: lang, corner: corner, complexity: dna.complexity || 'flat',
      cut: ang.cut || 45, crop: ang.crop || 72, shallow: ang.shallow || 15,
      dens: { airy: 1.15, balanced: 1, dense: 0.86 }[dna.density] || 1,
      energy: (dna.motion || {}).energy == null ? 0.4 : dna.motion.energy,
      lw: Math.max(1, st.rule_px || 1) * clamp(0.8 + (((dna.motion || {}).energy == null ? 0.4 : dna.motion.energy) - 0.3) * 1.6, 0.8, 1.45), cap: st.cap === 'square' ? 'square' : (st.cap || 'round'), join: st.join === 'miter' ? 'miter' : (st.join || 'round'),
      composition: dna.composition || '', motifs: dna.motifs || [], unit: cfg.unit, mark: cfg.mark || cfg.unit
    };
    C.playful = C.energy >= 0.5; C.chunk = C.playful ? 1.7 : 1;
    var fam = (ang.families || []).map(function (F) { return [(F.range_deg[0] + F.range_deg[1]) / 2, F.weight || 1]; });
    if (!fam.length) fam = [[C.cut, 0.4], [C.crop, 0.35], [C.shallow, 0.25]];
    C.pickAngle = function (r) { var a = wpick(r, fam.map(function (x) { return x[0]; }), fam.map(function (x) { return x[1]; })) + range(r, -1.5, 1.5); return r() < 0.5 ? a : 180 - a; };
    var CW = cfg.colourways;
    function cwOf(k) { return typeof k === 'string' ? (CW[k] || CW.paper) : k; }
    var SO = { cap: C.cap, join: C.join };

    /* ---------------------------------------------------------------- mark unit helpers */
    function prepUnit(U) {
      if (!U || U._ready) return U;
      function prepParts(parts) { parts.forEach(function (p) { p.polys = p.p ? [p.p] : parsePath(p.d, p.tx, p.ty, 6); if (!p.d && p.p) p.d = polyD(p.p); });
        var ls = parts.map(function (p) { return p.l == null ? lum(p.c || '#000000') : p.l; }), uniq = ls.slice().sort(function (a, b) { return a - b; }).filter(function (v, i, a) { return !i || Math.abs(v - a[i - 1]) > 0.02; });
        parts.forEach(function (p, i) { var k = 0; uniq.forEach(function (v, j) { if (Math.abs(v - ls[i]) <= 0.02) k = j; }); p.rank = uniq.length > 1 ? k / (uniq.length - 1) : 0; }); return parts; }
      prepParts(U.parts); U.facetParts = U.master && U.master.length ? prepParts(U.master) : U.parts;
      var all = []; U.parts.forEach(function (p) { p.polys.forEach(function (q) { all = all.concat(q); }); });
      U.bb = bbox(all); U.size = Math.max(U.bb[2] - U.bb[0], U.bb[3] - U.bb[1]);
      if (!U.oc) U.oc = [(U.bb[0] + U.bb[2]) / 2, (U.bb[1] + U.bb[3]) / 2];
      U.silPolys = U.sil ? parsePath(U.sil, 0, 0, 8) : [convexHull(all)];
      var hull = convexHull(all), outer = U.silPolys.reduce(function (s, q) { return s + Math.abs(area(q)); }, 0);
      U.solidity = outer / Math.max(1, Math.abs(area(hull)));
      U._ready = true; return U;
    }
    var unit = prepUnit(cfg.unit), mark = prepUnit(cfg.mark || cfg.unit);
    /** markup of a unit placed at (x,y) with max side `size`, rotation `rot`; fills by function(part) */
    function unitAt(U, x, y, size, rot, fillFn, extra) {
      var k = size / U.size, tr = 'translate(' + f(x) + ' ' + f(y) + ')' + (rot ? ' rotate(' + f(rot) + ')' : '') + ' scale(' + (+k.toFixed(5)) + ') translate(' + f(-U.oc[0]) + ' ' + f(-U.oc[1]) + ')';
      var tt = function (p) { return p.tx || p.ty ? ' transform="translate(' + f(p.tx || 0) + ' ' + f(p.ty || 0) + ')"' : ''; };
      fillFn = monoFor(U, fillFn);
      var seams = fillFn.mono ? '<g fill="none" stroke="' + fillFn.mono + '" stroke-width="' + f(U.size / 95) + '" stroke-linejoin="round">' + U.parts.map(function (p) { return '<path d="' + p.d + '"' + tt(p) + '/>'; }).join('') + '</g>' : '';
      return '<g transform="' + tr + '"' + (extra || '') + '>' + U.parts.map(function (p) { var fl = fillFn(p); return fl ? '<path fill-rule="evenodd" d="' + p.d + '"' + tt(p) + ' ' + fl + '/>' : ''; }).join('') + seams + '</g>';
    }
    function silAt(U, x, y, size, rot, attrs, s2, outer) {
      var k = size / U.size * (s2 || 1), sw = /stroke-width="([\d.]+)"/.exec(attrs);
      var a = sw ? attrs.replace(/stroke-width="[\d.]+"/, 'stroke-width="' + f(+sw[1] / k) + '"') : attrs;
      return '<g transform="translate(' + f(x) + ' ' + f(y) + ')' + (rot ? ' rotate(' + f(rot) + ')' : '') + ' scale(' + (+k.toFixed(5)) + ') translate(' + f(-U.oc[0]) + ' ' + f(-U.oc[1]) + ')"><path fill-rule="evenodd" d="' + (outer ? polyD(U.silPolys.slice().sort(function (p1, p2) { return Math.abs(area(p2)) - Math.abs(area(p1)); })[0]) : (U.sil || U.silPolys.map(function (q) { return polyD(q); }).join(''))) + '" ' + a + '/></g>';
    }
    function partsOutlineAt(U, x, y, size, rot, col, w) {
      var k = size / U.size;
      return '<g transform="translate(' + f(x) + ' ' + f(y) + ')' + (rot ? ' rotate(' + f(rot) + ')' : '') + ' scale(' + (+k.toFixed(5)) + ') translate(' + f(-U.oc[0]) + ' ' + f(-U.oc[1]) + ')" ' + stroke(col, w / k, SO) + '>' + U.parts.map(function (p) { return '<path d="' + p.d + '"' + (p.tx || p.ty ? ' transform="translate(' + f(p.tx || 0) + ' ' + f(p.ty || 0) + ')"' : '') + '/>'; }).join('') + '</g>';
    }
    function tonal(cw) { return function (p) { var t = p.rank; return fill(t < 0.34 ? cw.t3 : t < 0.67 ? cw.t2 : cw.t1); }; }
    function trueColour(cw) { if (cw.key === 'paper') return function (p) { return fill(p.c || cw.ink); }; if (cw.key === 'foundation') return function (p) { if (p.od) return fill(p.od); var c = p.c || cw.ink; return fill(contrast(c, cw.bg) >= 2.2 ? c : cw.ink); }; var m = function () { return fill(cw.ink); }; m.mono = cw.bg; return m; }
    function monoFor(U, fn) { return fn.mono && U.parts.length < 2 ? function (p) { return fn(p); } : fn; }
    function simplePoly(U) { var s = U.silPts && U.silPts.length >= 3 ? U.silPts : convexHull([].concat.apply([], U.silPolys)); return s; }

    /* ---------------------------------------------------------------- pattern generators */
    var GEN = {};
    // ---- angular -------------------------------------------------------------
    GEN.shards = function (cw, r) {
      var W = 720, H = 450, T = Tile(W, H), pts = poisson(W, H, 90 * C.dens, r), target = [W * 0.64, H * 0.36], best = 0, bd = 1e9;
      pts.forEach(function (p, i) { var d = tdist(p, target, W, H); if (d < bd) { bd = d; best = i; } });
      pts.forEach(function (p, i) {
        var a1 = C.pickAngle(r), a2 = a1 + (r() < 0.5 ? 1 : -1) * range(r, 22, 58), L1 = range(r, 40, 120) * C.dens, L2 = L1 * range(r, 0.45, 1.05);
        var tri = [[0, 0], [L1 * Math.cos(a1 * D2R), L1 * Math.sin(a1 * D2R)], [L2 * Math.cos(a2 * D2R), L2 * Math.sin(a2 * D2R)]], c = centroid(tri);
        if (i === best) tri = xform(tri, { s: 0.7, ox: c[0], oy: c[1], x: p[0], y: p[1] }); else tri = xform(tri, { ox: c[0], oy: c[1], x: p[0], y: p[1] });
        var q = r(), a = i === best ? fill(cw.accent) : C.playful && q < 0.08 ? fill(pick(r, cw.accents)) : q < 0.4 ? fill(cw.t1) : q < 0.68 ? fill(cw.t2) : q < 0.84 ? fill(cw.t3) : stroke(cw.line, C.lw, SO);
        T.poly(tri, a);
      });
      return T.done();
    };
    GEN.chevrons = function (cw, r) {
      var th = clamp(C.cut, 30, 70), rise = Math.round(58 * C.dens), w = Math.round(2 * rise / Math.tan(th * D2R)), gap = Math.round(clamp(rise * 0.2, 9, 15));
      var nCols = Math.max(4, Math.round(600 / w)), W = nCols * w, seq = [], H = 0;
      while (H < 380) { var k = pick(r, [1, 2, 3, 3]), g = pick(r, [3, 4, 5, 7]); seq.push([k, g]); H += (k + g) * gap; }
      var T = Tile(W, H), y = 0, ac = Math.floor(r() * seq.length), lines = [];
      function zig(y0) { var pts = []; for (var j = -1; j <= nCols + 1; j++) { pts.push([j * w, y0]); pts.push([j * w + w / 2, y0 + rise]); } return pts; }
      seq.forEach(function (s, si) {
        for (var i = 0; i < s[0]; i++) { var y0 = y + i * gap; lines.push([y0, si === ac && i === 0, i]); }
        // filled band under the group
        var top = zig(y), bot = zig(y + (s[0] - 1) * gap).reverse(), col = si % 3 === 1 ? cw.t2 : cw.t1;
        if (s[0] > 1 && si % 3 !== 2) T.poly(top.concat(bot), fill(col));
        y += (s[0] + s[1]) * gap;
      });
      lines.forEach(function (L) { var pts = zig(L[0]); if (L[1]) { var j = Math.floor(r() * nCols), x0 = j * w; T.add('<path d="' + polyD([[x0, L[0]], [x0 + w / 2, L[0] + rise], [x0 + w, L[0]]], true) + '" ' + stroke(cw.accent, C.lw * 2.4, { cap: C.cap, join: 'miter' }) + '/>', [x0 - 4, L[0] - 4, x0 + w + 4, L[0] + rise + 4]); }
        T.path(polyD(pts, true), pts, stroke(L[2] === 0 ? cw.t3 : cw.line, C.lw * (L[2] === 0 ? 1.6 : 1), { cap: 'butt', join: 'miter' })); });
      return T.done();
    };
    GEN['diagonal-bands'] = function (cw, r) {
      var th = clamp(C.crop, 15, 88), P = Math.round(520 * C.dens), steep = th > 82;
      var H = steep ? 400 : Math.round(P * Math.tan(th * D2R)); if (!steep && H > 1700) { P = Math.round(1700 / Math.tan(th * D2R)); H = Math.round(P * Math.tan(th * D2R)); }
      if (!steep && H < 160) H = Math.round(P * Math.tan(th * D2R) * Math.ceil(160 / Math.max(1, P * Math.tan(th * D2R))));
      var shift = steep ? 0 : P, u = 14 * C.dens, x = 0, bands = [], ai = -1;
      while (x < P - 2 * u) { var wdt = pick(r, [1, 1, 2, 3, 5, 8]) * u, kind = pick(r, ['gap', 'gap', 't1', 't2', 't3', 'line']); if (x + wdt > P) wdt = P - x; bands.push([x, wdt, kind]); x += wdt; }
      if (x < P) bands.push([x, P - x, 'gap']);
      var cand = bands.map(function (b, i) { return b[2] === 'gap' && b[1] >= 2 * u ? i : -1; }).filter(function (i) { return i >= 0; }); ai = cand.length ? pick(r, cand) : -1;
      var T = Tile(P, H), sx = shift;
      bands.forEach(function (b, i) {
        var x0 = b[0], x1 = b[0] + b[1];
        if (i === ai) { var m = (x0 + x1) / 2, hw = Math.max(2, u * 0.32); x0 = m - hw; x1 = m + hw; }
        var poly = [[x0, 0], [x1, 0], [x1 + sx, H], [x0 + sx, H]];
        if (i === ai) T.poly(poly, fill(cw.accent));
        else if (b[2] === 'line') T.path(polyD([[x0, 0], [x0 + sx, H]], true), poly, stroke(cw.line, C.lw, SO));
        else if (b[2] !== 'gap') T.poly(poly, fill(cw[b[2]]));
      });
      return T.done();
    };
    GEN['angle-hatch'] = function (cw, r) {
      var g = Math.round(17 * C.dens), W = 480, k = Math.max(1, Math.round(W * Math.tan(clamp(C.shallow, 5, 40) * D2R) / g)), tn = k * g / W, n = Math.round(420 / g), H = n * g, T = Tile(W, H);
      for (var i = 0; i < n; i++) {
        var y0 = i * g, strong = i % 5 === 0, segs = [], x = r() * W;
        // broken rhythm: long runs with short gaps, periodic in x
        var run = 0; while (run < W) { var len = range(r, 120, 420), gp = r() < 0.45 ? range(r, 14, 60) : 0; segs.push([x + run, Math.min(len, W - run)]); run += len + gp; }
        segs.forEach(function (s) { var a = [s[0], y0 + s[0] * tn], b = [s[0] + s[1], y0 + (s[0] + s[1]) * tn]; T.path(polyD([a, b], true), [a, b], stroke(strong ? cw.t3 : cw.line, C.lw * (strong ? 1.3 : 0.9), { cap: 'butt' })); });
      }
      var ax = r() * W, ay = Math.floor(r() * n) * g + 3 * g, a1 = [ax, ay + ax * tn], a2 = [ax + 90, ay + (ax + 90) * tn];
      T.path(polyD([a1, a2], true), [a1, a2], stroke(cw.accent, C.lw * 3, { cap: C.cap }));
      return T.done();
    };
    GEN.prism = function (cw, r) {
      // low-poly relief: a periodic height field sampled on a triangle lattice at the cut angle, lit from the upper left
      var th = clamp(C.cut, 35, 70), b = Math.round(64 * C.dens), h = Math.round(b / 2 * Math.tan(th * D2R)), nx = Math.max(6, Math.round(640 / b)), ny = 2 * Math.max(2, Math.round(200 / h)), W = nx * b, H = ny * h;
      var T = Tile(W, H), F = field(r, W, H, 5, 3), amp = b * 3.2, L = [-0.45, -0.6, 0.66], tris = [], shades = [];
      var Lm = Math.sqrt(L[0] * L[0] + L[1] * L[1] + L[2] * L[2]); L = L.map(function (v) { return v / Lm; });
      for (var j = 0; j < ny; j++) for (var i = 0; i < nx * 2; i++) {
        var x = i * b / 2, up = ((i + j) % 2 === 0), tri = up ? [[x, (j + 1) * h], [x + b / 2, j * h], [x + b, (j + 1) * h]] : [[x, j * h], [x + b, j * h], [x + b / 2, (j + 1) * h]];
        var v = tri.map(function (q) { return [q[0], q[1], F(q[0], q[1]) * amp]; }), a1 = [v[1][0] - v[0][0], v[1][1] - v[0][1], v[1][2] - v[0][2]], a2 = [v[2][0] - v[0][0], v[2][1] - v[0][1], v[2][2] - v[0][2]];
        var n = [a1[1] * a2[2] - a1[2] * a2[1], a1[2] * a2[0] - a1[0] * a2[2], a1[0] * a2[1] - a1[1] * a2[0]], nm = Math.sqrt(n[0] * n[0] + n[1] * n[1] + n[2] * n[2]) || 1; if (n[2] < 0) nm = -nm;
        var sh = (n[0] * L[0] + n[1] * L[1] + n[2] * L[2]) / nm; tris.push(tri); shades.push(sh);
      }
      var srt = shades.slice().sort(function (a, c) { return a - c; }), q = function (t) { return srt[Math.floor(t * (srt.length - 1))]; }, q1 = q(0.14), q2 = q(0.4), q3 = q(0.7), acc = Math.floor(r() * tris.length);
      tris.forEach(function (tri, k) { var sh = shades[k], col = k === acc ? cw.accent : sh < q1 ? cw.t3 : sh < q2 ? cw.t2 : sh < q3 ? cw.t1 : null;
        if (col) T.poly(tri, fill(col) + ' stroke="' + col + '" stroke-width="0.6" stroke-linejoin="round"'); });
      return T.done();
    };
    GEN['cut-grid'] = function (cw, r) {
      var c = Math.round(72 * C.dens), nx = Math.max(6, Math.round(640 / c)), ny = Math.max(4, Math.round(400 / c)), W = nx * c, H = ny * c, T = Tile(W, H);
      var tn = 1 / Math.tan(clamp(C.cut, 20, 80) * D2R), ai = Math.floor(r() * nx * ny), gap = Math.max(2, Math.round(c * 0.06));
      for (var j = 0; j < ny; j++) for (var i = 0; i < nx; i++) {
        var x = i * c, y = j * c, q = r(), id = j * nx + i, s = gap / 2;
        var rect = [[x + s, y + s], [x + c - s, y + s], [x + c - s, y + c - s], [x + s, y + c - s]];
        var cutL = (c - gap) * tn, tri = pick(r, [0, 1, 2, 3]);
        var tris = [[[x + s, y + s], [x + s, y + c - s], [x + s + cutL, y + c - s]], [[x + c - s, y + s], [x + c - s, y + c - s], [x + c - s - cutL, y + c - s]], [[x + s, y + s], [x + s + cutL, y + s], [x + s, y + c - s]], [[x + c - s, y + s], [x + c - s - cutL, y + s], [x + c - s, y + c - s]]];
        if (id === ai) { T.poly(tris[tri], fill(cw.accent)); continue; }
        if (q < 0.18) T.poly(rect, fill(cw.t1));
        else if (q < 0.42) T.poly(tris[tri], fill(cw.t2));
        else if (q < 0.52) T.poly(tris[tri], fill(cw.t3));
        else if (q < 0.6) T.poly(rect, stroke(cw.line, C.lw, { cap: 'butt', join: 'miter' }));
      }
      return T.done();
    };
    GEN['rhombus-grid'] = function (cw, r) {
      var th = clamp(C.cut, 30, 75), w = Math.round(96 * C.dens), h = Math.round(w * Math.tan(th * D2R)), nx = Math.max(5, Math.round(640 / w)), ny = Math.max(2, Math.round(420 / h)), W = nx * w, H = ny * h, T = Tile(W, H);
      for (var i = -ny - 1; i <= nx + ny + 1; i++) { var a = [i * w, 0], b = [i * w + H / Math.tan(th * D2R), H], c2 = [i * w, 0], d = [i * w - H / Math.tan(th * D2R), H];
        T.path(polyD([a, b], true), [a, b], stroke(cw.line, C.lw * 0.9, { cap: 'butt' })); T.path(polyD([c2, d], true), [c2, d], stroke(cw.line, C.lw * 0.9, { cap: 'butt' })); }
      // fill a few rhombi in tones (diamonds centred on lattice points)
      var cells = []; for (var jj = 0; jj < ny * 2; jj++) for (var ii = 0; ii < nx; ii++) cells.push([ii * w + (jj % 2 ? w / 2 : 0), jj * h / 2]);
      var acc = Math.floor(r() * cells.length);
      cells.forEach(function (p, k) { var q = r(); var dm = [[p[0], p[1] - h / 2], [p[0] + w / 2, p[1]], [p[0], p[1] + h / 2], [p[0] - w / 2, p[1]]];
        if (k === acc) T.poly(xform(dm, { s: 0.36, ox: p[0], oy: p[1], x: p[0], y: p[1] }), fill(cw.accent));
        else if (q < 0.12) T.poly(dm, fill(cw.t1)); else if (q < 0.2) T.poly(dm, fill(cw.t2)); else if (q < 0.24) T.poly(xform(dm, { s: 0.5, ox: p[0], oy: p[1], x: p[0], y: p[1] }), fill(cw.t3)); });
      return T.done();
    };
    GEN['mark-lattice'] = function (cw, r) {
      var poly = simplePoly(mark), bb = bbox(poly), pw = bb[2] - bb[0], ph = bb[3] - bb[1], s = 70 * C.dens / Math.max(pw, ph);
      var w = Math.round(pw * s * 1.45), h = Math.round(ph * s * 0.82), nx = Math.max(5, Math.round(640 / w)), ny = 2 * Math.max(2, Math.round(200 / h)), W = nx * w, H = ny * h, T = Tile(W, H), acc = [Math.floor(r() * nx), Math.floor(r() * ny)];
      var cx = (bb[0] + bb[2]) / 2, cy = (bb[1] + bb[3]) / 2;
      for (var j = 0; j < ny; j++) for (var i = 0; i < nx; i++) {
        var x = i * w + (j % 2 ? w / 2 : 0), y = j * h, q = r(), P = xform(poly, { s: s * 0.94, ox: cx, oy: cy, x: x, y: y });
        if (i === acc[0] && j === acc[1]) T.poly(P, fill(cw.accent));
        else if (q < 0.22) T.poly(P, fill(cw.t1)); else if (q < 0.34) T.poly(P, fill(cw.t2)); else if (q < 0.38) T.poly(P, fill(cw.t3));
        else if (q < 0.8) T.poly(P, stroke(cw.line, C.lw * 0.9, { cap: C.cap, join: C.join }));
      }
      return T.done();
    };
    // ---- faceted -------------------------------------------------------------
    function markLookup() {
      var polys = []; mark.facetParts.forEach(function (p) { p.polys.forEach(function (q) { polys.push([q, p.rank, centroid(q), Math.abs(area(q))]); }); });
      polys.sort(function (a, b) { return a[3] - b[3]; }); // smallest first so nested parts win
      return function (u, v) { var x = mark.bb[0] + u * (mark.bb[2] - mark.bb[0]), y = mark.bb[1] + v * (mark.bb[3] - mark.bb[1]);
        for (var i = 0; i < polys.length; i++) if (inPoly([x, y], polys[i][0])) return polys[i][1];
        var best = 1, bd = 1e18; polys.forEach(function (P) { var d = (P[2][0] - x) * (P[2][0] - x) + (P[2][1] - y) * (P[2][1] - y); if (d < bd) { bd = d; best = P[1]; } }); return Math.min(1, best + 0.35); };
    }
    function periodicTris(W, H, pts) {
      var ext = []; [-1, 0, 1].forEach(function (i) { [-1, 0, 1].forEach(function (j) { pts.forEach(function (p) { ext.push([p[0] + i * W, p[1] + j * H]); }); }); });
      var tr = delaunay(ext);
      return { ext: ext, tris: tr.filter(function (t) { var b = bbox([ext[t[0]], ext[t[1]], ext[t[2]]]); return b[2] > -2 && b[0] < W + 2 && b[3] > -2 && b[1] < H + 2; }) };
    }
    GEN.facets = function (cw, r) {
      var W = 640, H = 400, pts = poisson(W, H, 54 * C.dens, r), D = periodicTris(W, H, pts), look = markLookup(), out = [], edges = [];
      var acc = null, target = [W * 0.6, H * 0.42], bd = 1e9, acc2 = null;
      D.tris.forEach(function (t, k) { var P = [D.ext[t[0]], D.ext[t[1]], D.ext[t[2]]], c = centroid(P), cm = [((c[0] % W) + W) % W, ((c[1] % H) + H) % H], d = tdist(cm, target, W, H) + Math.abs(area(P)) / 60;
        if (d < bd) { bd = d; acc = cm[0].toFixed(1) + ',' + cm[1].toFixed(1); } });
      var accP = C.playful ? [W * 0.2, H * 0.8] : null, bd2 = 1e9;
      if (accP) D.tris.forEach(function (t) { var P = [D.ext[t[0]], D.ext[t[1]], D.ext[t[2]]], c = centroid(P), cm = [((c[0] % W) + W) % W, ((c[1] % H) + H) % H], d = tdist(cm, accP, W, H); if (d < bd2) { bd2 = d; acc2 = cm[0].toFixed(1) + ',' + cm[1].toFixed(1); } });
      var vals = D.tris.map(function (t) { var P = [D.ext[t[0]], D.ext[t[1]], D.ext[t[2]]], c = centroid(P), cm = [((c[0] % W) + W) % W, ((c[1] % H) + H) % H], jit = Math.abs((Math.sin(cm[0] * 12.9898 + cm[1] * 78.233) * 43758.5453) % 1);
        return look(cm[0] / W, cm[1] / H) * 0.5 + jit * 0.5; }), srt = vals.slice().sort(function (a, b) { return a - b; }), q = function (x) { return srt[Math.floor(x * (srt.length - 1))]; }, q1 = q(0.12), q2 = q(0.36), q3 = q(0.72);
      D.tris.forEach(function (t, ti) {
        var P = [D.ext[t[0]], D.ext[t[1]], D.ext[t[2]]], c = centroid(P), cm = [((c[0] % W) + W) % W, ((c[1] % H) + H) % H], key = cm[0].toFixed(1) + ',' + cm[1].toFixed(1), v = vals[ti];
        var col = key === acc ? cw.accent : key === acc2 ? cw.accent2 : v < q1 ? cw.t3 : v < q2 ? cw.t2 : v < q3 ? cw.t1 : cw.bg;
        out.push('<path d="' + polyD(P) + '" fill="' + col + '" stroke="' + col + '" stroke-width="0.6" stroke-linejoin="round"/>');
        edges.push(polyD(P));
      });
      out.push('<path d="' + edges.join('') + '" ' + stroke(cw.line, C.lw * 0.7, { join: 'round', op: 0.55 }) + '/>');
      return { w: W, h: H, body: out.join(''), tile: true };
    };
    GEN['facet-mesh'] = function (cw, r) {
      var W = 640, H = 400, F = field(r, W, H, 3, 1), pts = [], cand = poisson(W, H, 30 * C.dens, r);
      cand.forEach(function (p) { if ((F(p[0], p[1]) + 1) / 2 > r() * 0.9) pts.push(p); });
      var D = periodicTris(W, H, pts), seen = {}, d = '', nodes = [], fills = [];
      D.tris.forEach(function (t, k) { var P = [D.ext[t[0]], D.ext[t[1]], D.ext[t[2]]];
        [[0, 1], [1, 2], [2, 0]].forEach(function (e) { var a = P[e[0]], b = P[e[1]], key = [a, b].map(function (q) { return q[0].toFixed(1) + ',' + q[1].toFixed(1); }).sort().join('|'); if (!seen[key]) { seen[key] = 1; d += 'M' + f(a[0]) + ' ' + f(a[1]) + 'L' + f(b[0]) + ' ' + f(b[1]); } });
        var c = centroid(P), cm = [((c[0] % W) + W) % W, ((c[1] % H) + H) % H], h = (Math.sin(cm[0] * 3.1 + cm[1] * 7.7) * 9999) % 1;
        if (Math.abs(h) < 0.07) fills.push('<path d="' + polyD(P) + '" ' + fill(cw.t2) + '/>');
      });
      pts.forEach(function (p, i) { if (i % 5 === 0) nodes.push([p[0], p[1]]); });
      var T = Tile(W, H); fills.forEach(function (x) { T.add(x); });
      T.add('<path d="' + d + '" ' + stroke(cw.line, C.lw * 0.8, { cap: 'round' }) + '/>');
      nodes.forEach(function (p, i) { T.circle(p[0], p[1], C.lw * 2.2, fill(i === 0 ? cw.accent : cw.t3)); });
      if (nodes[1]) T.circle(nodes[1][0], nodes[1][1], 9, stroke(cw.accent, C.lw * 1.2));
      return T.done();
    };
    GEN['facet-scatter'] = function (cw, r) {
      var W = 720, H = 450, T = Tile(W, H), pieces = []; mark.facetParts.forEach(function (p) { p.polys.forEach(function (q) { if (Math.abs(area(q)) > mark.size * mark.size * 0.002) pieces.push([q, p.rank]); }); });
      if (!pieces.length) return GEN.shards(cw, r);
      var pts = poisson(W, H, 116 * C.dens, r), acc = Math.floor(r() * pts.length);
      pts.forEach(function (p, i) { var pc = pick(r, pieces), q = pc[0], bb = bbox(q), sz = Math.max(bb[2] - bb[0], bb[3] - bb[1]), c = centroid(q);
        var k = range(r, 46, 104) * C.dens / sz, rot = C.lang === 'angular' ? pick(r, [0, C.cut, -C.cut, 180 - C.cut, C.crop, 180]) : r() * 360;
        var P = xform(q, { s: k, r: rot, ox: c[0], oy: c[1], x: p[0], y: p[1] }), t = pc[1];
        T.poly(P, i === acc ? fill(cw.accent) : fill(t < 0.34 ? cw.t3 : t < 0.67 ? cw.t2 : cw.t1)); });
      return T.done();
    };
    // ---- orthogonal ----------------------------------------------------------
    GEN.grid = function (cw, r) {
      var c = Math.round(24 * C.dens), n = Math.round(600 / c / 4) * 4, m = Math.round(400 / c / 4) * 4, W = n * c, H = m * c, T = Tile(W, H), d = '', D2 = '', x, y;
      for (x = 0; x < W; x += c) { if ((x / c) % 4 === 0) D2 += 'M' + x + ' 0V' + H; else d += 'M' + x + ' 0V' + H; }
      for (y = 0; y < H; y += c) { if ((y / c) % 4 === 0) D2 += 'M0 ' + y + 'H' + W; else d += 'M0 ' + y + 'H' + W; }
      D2 += 'M' + W + ' 0V' + H + 'M0 ' + H + 'H' + W;
      for (var k = 0; k < 6; k++) { var gx = Math.floor(r() * n / 4) * 4 * c, gy = Math.floor(r() * m / 4) * 4 * c; T.add('<rect x="' + gx + '" y="' + gy + '" width="' + 4 * c + '" height="' + 4 * c + '" ' + fill(k === 0 ? cw.t2 : cw.t1) + '/>'); }
      T.add('<path d="' + d + '" ' + stroke(cw.line, C.lw * 0.6, { cap: 'butt', op: 0.6 }) + '/><path d="' + D2 + '" ' + stroke(cw.line, C.lw, { cap: 'butt' }) + '/>');
      var ax = Math.floor(r() * n / 4) * 4 * c + 4 * c, ay = Math.floor(r() * m / 4) * 4 * c + 4 * c; T.add('<rect x="' + (ax - 4) + '" y="' + (ay - 4) + '" width="8" height="8" ' + fill(cw.accent) + '/>', [ax - 4, ay - 4, ax + 4, ay + 4]);
      return T.done();
    };
    GEN.blocks = function (cw, r) {
      var W = 640, H = 400, T = Tile(W, H), u = 40 * C.dens, rects = [[0, 0, W, H]], out = [];
      function split(R, depth) { var w = R[2], h = R[3]; if (depth > 4 || (w < 3 * u && h < 3 * u) || (depth > 1 && r() < 0.18)) { out.push(R); return; }
        if (w > h) { var s = Math.round((w * range(r, 0.3, 0.7)) / u) * u || u; split([R[0], R[1], s, h], depth + 1); split([R[0] + s, R[1], w - s, h], depth + 1); }
        else { var t = Math.round((h * range(r, 0.3, 0.7)) / u) * u || u; split([R[0], R[1], w, t], depth + 1); split([R[0], R[1] + t, w, h - t], depth + 1); } }
      split(rects[0], 0); var acc = Math.floor(r() * out.length);
      out.forEach(function (R, i) { var q = r(), g = 3, col = i === acc ? cw.accent : q < 0.3 ? cw.t1 : q < 0.5 ? cw.t2 : q < 0.6 ? cw.t3 : null;
        if (i === acc) { T.add('<rect x="' + f(R[0] + g) + '" y="' + f(R[1] + g) + '" width="' + f(Math.min(R[2], u) - 2 * g) + '" height="' + f(Math.min(R[3], u) - 2 * g) + '" ' + fill(col) + '/>'); return; }
        if (col) T.add('<rect x="' + f(R[0] + g) + '" y="' + f(R[1] + g) + '" width="' + f(R[2] - 2 * g) + '" height="' + f(R[3] - 2 * g) + '" ' + fill(col) + '/>');
        else T.add('<rect x="' + f(R[0] + g) + '" y="' + f(R[1] + g) + '" width="' + f(R[2] - 2 * g) + '" height="' + f(R[3] - 2 * g) + '" ' + stroke(cw.line, C.lw, { cap: 'butt', join: 'miter' }) + '/>'); });
      return T.done();
    };
    GEN.stripes = function (cw, r) {
      var W = 0, H = 400, u = 12 * C.dens, seq = [];
      while (W < 560) { var w = pick(r, [1, 1, 2, 3, 5]) * u, k = pick(r, ['gap', 'gap', 't1', 't2', 't3', 'line']); seq.push([W, w, k]); W += w; }
      W = Math.round(W); var T = Tile(W, H), ai = Math.floor(r() * seq.length);
      seq.forEach(function (s, i) { if (i === ai) T.add('<rect x="' + f(s[0] + s[1] / 2 - 2) + '" y="0" width="4" height="' + H + '" ' + fill(cw.accent) + '/>');
        else if (s[2] === 'line') T.add('<path d="M' + f(s[0]) + ' 0V' + H + '" ' + stroke(cw.line, C.lw, { cap: 'butt' }) + '/>');
        else if (s[2] !== 'gap') T.add('<rect x="' + f(s[0]) + '" y="0" width="' + f(s[1]) + '" height="' + H + '" ' + fill(cw[s[2]]) + '/>'); });
      return T.done();
    };
    GEN.steps = function (cw, r) {
      var s = Math.round(32 * C.dens), n = 4, W = s * n * 5, H = s * n * 3, T = Tile(W, H), ai = Math.floor(r() * 15);
      for (var j = 0; j < 3; j++) for (var i = 0; i < 5; i++) { var x0 = i * s * n, y0 = j * s * n, pts = [[x0, y0 + s * n]]; for (var k = 0; k < n; k++) { pts.push([x0 + k * s, y0 + (n - k - 1) * s]); pts.push([x0 + (k + 1) * s, y0 + (n - k - 1) * s]); } pts.push([x0 + n * s, y0 + n * s]);
        var q = r(), id = j * 5 + i; T.poly(pts, id === ai ? fill(cw.accent) : q < 0.35 ? fill(cw.t1) : q < 0.6 ? fill(cw.t2) : q < 0.7 ? fill(cw.t3) : stroke(cw.line, C.lw, { cap: 'butt', join: 'miter' })); }
      return T.done();
    };
    GEN['dot-grid'] = function (cw, r) {
      var g = Math.round(24 * C.dens), nx = Math.round(600 / g), ny = Math.round(384 / g), W = nx * g, H = ny * g, T = Tile(W, H), acc = Math.floor(r() * nx * ny);
      var dots = '';
      for (var j = 0; j < ny; j++) for (var i = 0; i < nx; i++) { var x = i * g + g / 2, y = j * g + g / 2, q = r(), id = j * nx + i;
        if (id === acc) { T.circle(x, y, g * 0.28, fill(cw.accent)); continue; }
        if (q < 0.035) T.circle(x, y, g * 0.3, stroke(cw.t3, C.lw * 1.1)); else if (q < 0.06) T.circle(x, y, g * 0.18, fill(cw.t3));
        else dots += circleD(x, y, Math.max(1.5, C.lw * 1.6) * Math.sqrt(C.chunk)); }
      T.add('<path d="' + dots + '" ' + fill(cw.soft) + ' fill-opacity="0.7"/>');
      return T.done();
    };
    // ---- round ---------------------------------------------------------------
    GEN.orbits = function (cw, r) {
      var a = Math.round(168 * C.dens), nx = 4, hr = Math.round(a * 0.866), ny = 4, W = nx * a, H = ny * hr, T = Tile(W, H), acc = Math.floor(r() * nx * ny);
      var radii = [0.16, 0.22, 0.3, 0.38];
      for (var j = 0; j < ny; j++) for (var i = 0; i < nx; i++) {
        var x = i * a + (j % 2 ? a / 2 : 0) + range(r, -0.08, 0.08) * a, y = j * hr + range(r, -0.08, 0.08) * a, R = pick(r, radii) * a, id = j * nx + i, phi = r() * 360;
        var rings = r() < 0.55 ? 2 : 1, sw = C.lw * 1.1 * C.chunk;
        if (C.playful && r() < 0.35) T.circle(x, y, R, fill(cw.t1));
        T.circle(x, y, R, stroke(cw.line, sw));
        if (rings === 2) T.circle(x, y, R * 1.55, stroke(cw.line, sw * 0.8, { op: 0.7 }));
        if (r() < 0.6) T.circle(x, y, R * 0.36, fill(cw.t2));
        var sr = Math.max(3, R * 0.16 * (C.playful ? 1.35 : 1)), sp = [x + R * Math.cos(phi * D2R), y + R * Math.sin(phi * D2R)];
        T.circle(sp[0], sp[1], sr, fill(id === acc ? cw.accent : C.playful && r() < 0.25 ? pick(r, cw.accents) : cw.t3));
        if (rings === 2 && r() < 0.5) { var p2 = (phi + 140 + r() * 60) * D2R; T.circle(x + R * 1.55 * Math.cos(p2), y + R * 1.55 * Math.sin(p2), sr * 0.6, fill(cw.t3)); }
      }
      return T.done();
    };
    GEN.dots = function (cw, r) {
      var g = Math.round(18 * C.dens), nx = Math.round(612 / g), ny = 2 * Math.round(396 / g / 2), W = nx * g, H = ny * g, F = field(r, W, H, 3, 1), T = Tile(W, H), d = '', bv = -9, bx = 0, by = 0;
      for (var j = 0; j < ny; j++) for (var i = 0; i < nx; i++) { var x = i * g + (j % 2 ? g / 2 : 0), y = j * g, v = (F(x, y) + 1) / 2, rr = g * (0.08 + 0.3 * v * v);
        if (v > bv && x > g && y > g && x < W - g && y < H - g) { bv = v; bx = x; by = y; }
        if (rr <= 0.7) continue; if (x - rr < 0 || y - rr < 0 || x + rr > W || y + rr > H) T.circle(x, y, rr, fill(cw.t3)); else d += circleD(x, y, rr); }
      T.add('<path d="' + d + '" ' + fill(cw.t3) + '/>');
      T.circle(bx, by, g * 0.42, fill(cw.accent));
      return T.done();
    };
    GEN.halftone = function (cw, r) {
      var g = Math.round(16 * C.dens), nx = Math.round(640 / g), ny = Math.round(400 / g), W = nx * g, H = ny * g, T = Tile(W, H), lam = range(r, 70, 110) * C.dens, d = '';
      var cs = [[W * range(r, 0.2, 0.35), H * range(r, 0.25, 0.4)], [W * range(r, 0.65, 0.85), H * range(r, 0.6, 0.85)]];
      for (var j = 0; j < ny; j++) for (var i = 0; i < nx; i++) { var x = i * g + g / 2, y = j * g + g / 2, dm = Math.min(tdist([x, y], cs[0], W, H), tdist([x, y], cs[1], W, H) * 1.3), v = 0.5 + 0.5 * Math.cos(TAU * dm / lam), rr = g * 0.44 * Math.pow(v, 1.4) * clamp(1.15 - dm / (W * 0.5), 0.25, 1);
        if (rr > 0.6) d += circleD(x, y, rr); }
      T.add('<path d="' + d + '" ' + fill(cw.t2) + '/>');
      T.circle(cs[0][0], cs[0][1], g * 0.5, fill(cw.accent));
      return T.done();
    };
    GEN.arcs = function (cw, r) {
      var c = Math.round(64 * C.dens), nx = Math.round(640 / c), ny = Math.round(384 / c), W = nx * c, H = ny * c, T = Tile(W, H), sw = Math.max(C.lw * 1.4, c * 0.07) * (C.playful ? 1.25 : 1), acc = Math.floor(r() * nx * ny);
      var filled = C.playful;
      for (var j = 0; j < ny; j++) for (var i = 0; i < nx; i++) {
        var x = i * c, y = j * c, o = r() < 0.5, id = j * nx + i, q = r(), col = id === acc ? cw.accent : q < 0.3 ? cw.t3 : cw.line;
        var A = o ? [[x, y, 0, 90], [x + c, y + c, 180, 270]] : [[x + c, y, 90, 180], [x, y + c, 270, 360]];
        if (filled && q > 0.82 && id !== acc) { var aa = A[0], P = [[aa[0], aa[1]]].concat(arcPts(aa[0], aa[1], c / 2, aa[2], aa[3])); T.poly(P, fill(cw.t2)); }
        A.forEach(function (a, k) { [c / 2 - c / 6, c / 2 + c / 6].forEach(function (rad, m) { var pts = arcPts(a[0], a[1], rad, a[2], a[3], 10); T.path(polyD(pts, true), pts, stroke(k === 0 && m === 0 ? col : (col === cw.accent ? cw.line : col), sw * (m ? 1 : 1), { cap: 'butt' })); }); });
      }
      return T.done();
    };
    GEN['arc-rows'] = function (cw, r) {
      var u = Math.round(96 * C.dens), nx = Math.round(640 / u), rows = 4, rh = Math.round(u * 0.5), W = nx * u, H = rows * rh * 2, T = Tile(W, H), sw = Math.max(C.lw * 1.2, u * 0.035) * C.chunk, acc = [Math.floor(r() * nx), Math.floor(r() * rows * 2)];
      for (var j = 0; j < rows * 2; j++) for (var i = 0; i < nx; i++) {
        var cx = i * u + (j % 2 ? u / 2 : 0) + u / 2, cy = (j + 1) * rh, q = r(), isA = i === acc[0] && j === acc[1];
        var col = q < 0.25 ? cw.t1 : q < 0.45 ? cw.t2 : null;
        if (col) { var P = arcPts(cx, cy, u / 2 - 2, 180, 360, 24); T.poly(P, fill(col)); }
        [0.5, 0.36, 0.22].forEach(function (k, m) { var pts = arcPts(cx, cy, u * k - 2, 180, 360, 24); T.path(polyD(pts, true), pts, stroke(isA && m === 1 ? cw.accent : m === 0 ? cw.t3 : cw.line, sw * (isA && m === 1 ? 2 : 1), { cap: 'round' })); });
        if (C.playful && q > 0.88) T.circle(cx, cy - 3, u * 0.06, fill(pick(r, cw.accents)));
      }
      return T.done();
    };
    GEN['halo-rings'] = function (cw, r, id) {
      var W = 720, H = 450, T = Tile(W, H), pts = poisson(W, H, 230 * C.dens, r, 5), gid = 'h' + (hash(C.name + id + cw.key) % 99999);
      var defs = '<defs><radialGradient id="' + gid + '"><stop offset="0" stop-color="' + cw.t3 + '"/><stop offset="0.55" stop-color="' + cw.t2 + '" stop-opacity="0.65"/><stop offset="1" stop-color="' + cw.t1 + '" stop-opacity="0"/></radialGradient></defs>';
      T.add(defs);
      pts.forEach(function (p, i) { var R = range(r, 90, 150) * C.dens; T.circle(p[0], p[1], R, 'fill="url(#' + gid + ')"');
        for (var k = 1; k <= 3; k++) T.circle(p[0], p[1], R * (0.45 + 0.28 * k), stroke(cw.line, C.lw * 0.9, { op: 1 - k * 0.22 }));
        if (i === 0) T.circle(p[0] + R * 1.01 * Math.cos(-0.7), p[1] + R * 1.01 * Math.sin(-0.7), 6, fill(cw.accent)); });
      return T.done();
    };
    GEN.rings = function (cw, r) {
      var a = Math.round(140 * C.dens), nx = 4, ny = 3, W = nx * a, H = ny * a, T = Tile(W, H), acc = Math.floor(r() * nx * ny);
      for (var j = 0; j < ny; j++) for (var i = 0; i < nx; i++) { var x = i * a + a / 2 + (j % 2 ? a / 2 : 0), y = j * a + a / 2, n = pick(r, [2, 3, 4]), id = j * nx + i;
        for (var k = n; k >= 1; k--) { var R = a * 0.13 * k; if (k === n && r() < 0.4) T.circle(x, y, R, fill(cw.t1)); T.circle(x, y, R, stroke(id === acc && k === 1 ? cw.accent : k === n ? cw.t3 : cw.line, C.lw * C.chunk * (id === acc && k === 1 ? 2.4 : 1.1))); }
        if (r() < 0.35) T.circle(x, y, C.lw * 2.4, fill(cw.t3)); }
      return T.done();
    };
    // ---- organic -------------------------------------------------------------
    GEN.waves = function (cw, r) {
      var W = 640, n = 12, H = 420, s = H / n, k1 = pick(r, [1, 2]), k2 = pick(r, [2, 3]), A1 = s * 1.15, A2 = s * 0.35, p1 = r() * TAU, p2 = r() * TAU, q = pick(r, [1, 1, 2]), dl = TAU * q / n;
      var T = Tile(W, H), tones = ['t1', null, 't2', null, 't1', 't3', null, 't2', null, 't1', null, 't2'];
      function line(i) { var pts = []; for (var x = -16; x <= W + 16; x += 16) pts.push([x, i * s + A1 * Math.sin(TAU * k1 * x / W + p1 + i * dl) + A2 * Math.sin(TAU * k2 * x / W + p2)]); return pts; }
      var ai = Math.floor(r() * n);
      for (var i = 0; i < n; i++) { var L0 = line(i), L1 = line(i + 1), tn = tones[i % tones.length];
        var bb0 = function (L) { return L.slice(1, -1); };
        if (tn) T.path(smoothD(L0, false, 1, true) + 'L' + smoothD(L1.slice().reverse(), false, 1, true).slice(1) + 'Z', bb0(L0).concat(bb0(L1)), fill(cw[tn]));
        T.path(smoothD(L0, false, 1, true), bb0(L0), stroke(i === ai ? cw.accent : cw.line, C.lw * (i === ai ? 2.2 : 0.9))); }
      return T.done();
    };
    GEN['wave-lines'] = function (cw, r) {
      var W = 600, n = 26, H = 390, s = H / n, k1 = pick(r, [1, 2]), A1 = s * 2.6, p1 = r() * TAU, dl = TAU / n, k2 = 3, A2 = s * 0.5, p2 = r() * TAU, T = Tile(W, H), ai = Math.floor(r() * n);
      for (var i = 0; i < n; i++) { var pts = []; for (var x = -15; x <= W + 15; x += 15) pts.push([x, i * s + A1 * Math.sin(TAU * k1 * x / W + p1 + i * dl) + A2 * Math.sin(TAU * k2 * x / W + p2 + i * dl * 2)]);
        T.path(smoothD(pts, false, 1, true), pts.slice(1, -1), stroke(i === ai ? cw.accent : i % 4 === 0 ? cw.t3 : cw.line, C.lw * (i === ai ? 2 : i % 4 === 0 ? 1.4 : 0.9))); }
      return T.done();
    };
    GEN.blobs = function (cw, r) {
      var W = 720, H = 450, T = Tile(W, H), pts = poisson(W, H, 128 * C.dens, r), acc = Math.floor(r() * pts.length);
      pts.forEach(function (p, i) { var R = range(r, 28, 66) * C.dens * (i === acc ? 0.55 : 1), P = blobPts(r, p[0], p[1], R, { amp: 0.2, rot: r() * 360, sx: range(r, 0.85, 1.25) }), q = r();
        var a = i === acc ? fill(cw.accent) : C.playful && q < 0.1 ? fill(pick(r, cw.accents)) : q < 0.36 ? fill(cw.t1) : q < 0.62 ? fill(cw.t2) : q < 0.76 ? fill(cw.t3) : stroke(cw.line, C.lw);
        T.path(smoothD(P, true), P, a); });
      return T.done();
    };
    GEN.terrazzo = function (cw, r) {
      var W = 640, H = 400, T = Tile(W, H), pts = poisson(W, H, 30 * C.dens, r);
      pts.forEach(function (p, i) { var R = range(r, 3.5, 11) * C.dens, P = blobPts(r, p[0], p[1], R, { n: 14, amp: 0.3, kmax: 3, rot: r() * 360, sx: range(r, 0.6, 1.4) }), q = r();
        var col = q < 0.03 ? cw.accent : (C.playful && q < 0.08) ? cw.accent2 : q < 0.4 ? cw.t2 : q < 0.7 ? cw.t1 : q < 0.92 ? cw.t3 : cw.soft;
        T.path(smoothD(P, true), P, fill(col)); });
      return T.done();
    };
    GEN['flow-lines'] = function (cw, r) {
      var W = 640, H = 400, F = field(r, W, H, 3, 1), T = Tile(W, H), seeds = poisson(W, H, 22 * C.dens, r), step = 4, sep = 10 * C.dens, cell = sep, gx = Math.ceil(W / cell), gy = Math.ceil(H / cell), occ = {};
      function key(x, y) { var i = Math.floor((((x % W) + W) % W) / cell), j = Math.floor((((y % H) + H) % H) / cell); return i + ',' + j; }
      function near(x, y) { var i = Math.floor((((x % W) + W) % W) / cell), j = Math.floor((((y % H) + H) % H) / cell); for (var di = -1; di <= 1; di++) for (var dj = -1; dj <= 1; dj++) { var k = ((i + di + gx) % gx) + ',' + ((j + dj + gy) % gy); if (occ[k]) return true; } return false; }
      var lines = [];
      seeds.forEach(function (s) { if (near(s[0], s[1])) return; var line = [s.slice()];
        [1, -1].forEach(function (sg) { var x = s[0], y = s[1], pts = []; for (var k = 0; k < 150; k++) { var a = F(x, y) * Math.PI * 0.42; x += Math.cos(a) * step * sg; y += Math.sin(a) * step * sg; if (k > 2 && near(x, y)) break; pts.push([x, y]); } if (sg > 0) line = line.concat(pts); else line = pts.reverse().concat(line); });
        if (line.length < 16) return; line.forEach(function (p, idx) { if (idx % 2 === 0) occ[key(p[0], p[1])] = 1; }); lines.push(line); });
      var ai = Math.floor(r() * lines.length);
      lines.forEach(function (L, i) { var P = L.filter(function (p, k) { return k % 2 === 0 || k === L.length - 1; }); T.path(smoothD(P, false), P, stroke(i === ai ? cw.accent : i % 4 === 0 ? cw.t3 : cw.line, C.lw * (i === ai ? 2.2 : i % 4 === 0 ? 1.6 : 1.1))); });
      return T.done();
    };
    GEN.ripples = function (cw, r) {
      var W = 720, H = 450, T = Tile(W, H), cs = poisson(W, H, 170 * C.dens, r, 9), acc = 0;
      cs.forEach(function (c, ci) { var n = pick(r, [5, 6, 7]), g0 = range(r, 11, 17) * C.dens, ph = r() * TAU;
        for (var k = 1; k <= n; k++) { var R = g0 * k * (1 + k * 0.08), pts = []; for (var a = 0; a < 48; a++) { var t = a / 48 * TAU; pts.push([c[0] + Math.cos(t) * R * (1 + 0.05 * Math.sin(3 * t + ph + k * 0.6)), c[1] + Math.sin(t) * R * (1 + 0.05 * Math.sin(2 * t + ph))]); }
          T.path(smoothD(pts, true), pts, stroke(ci === acc && k === 2 ? cw.accent : k === 1 ? cw.t3 : cw.line, C.lw * (ci === acc && k === 2 ? 2 : k === 1 ? 1.4 : 1), { op: k > n - 2 ? 0.6 : 1 })); }
        if (r() < 0.5) T.circle(c[0], c[1], g0 * 0.4, fill(cw.t2)); });
      return T.done();
    };
    GEN.contours = function (cw, r) {
      var W = 640, H = 400, F = field(r, W, H, 5, 2), st = 5, nx = W / st, ny = H / st, L = 9, segs = [], v = [];
      for (var j = 0; j <= ny; j++) { v[j] = []; for (var i = 0; i <= nx; i++) v[j][i] = F(i * st, j * st); }
      var paths = {}; for (var l = 1; l <= L; l++) paths[l] = '';
      // segments touching a tile edge are repeated on the opposite edge so strokes are never half-clipped
      function seg(lv, A, B) { var e = 4; [[0, 0]].concat([[W, 0], [-W, 0], [0, H], [0, -H]].filter(function (o) { return (o[0] > 0 && Math.min(A[0], B[0]) < e) || (o[0] < 0 && Math.max(A[0], B[0]) > W - e) || (o[1] > 0 && Math.min(A[1], B[1]) < e) || (o[1] < 0 && Math.max(A[1], B[1]) > H - e); }))
        .forEach(function (o) { paths[lv] += 'M' + f(A[0] + o[0]) + ' ' + f(A[1] + o[1]) + 'L' + f(B[0] + o[0]) + ' ' + f(B[1] + o[1]); }); }
      for (var lv = 1; lv <= L; lv++) { var t = -0.9 + 1.8 * lv / (L + 1);
        for (var jj = 0; jj < ny; jj++) for (var ii = 0; ii < nx; ii++) { var a = v[jj][ii], b = v[jj][ii + 1], c = v[jj + 1][ii + 1], d = v[jj + 1][ii], x = ii * st, y = jj * st, P = [];
          if ((a > t) !== (b > t)) P.push([x + st * (t - a) / (b - a), y]); if ((b > t) !== (c > t)) P.push([x + st, y + st * (t - b) / (c - b)]);
          if ((d > t) !== (c > t)) P.push([x + st * (t - d) / (c - d), y + st]); if ((a > t) !== (d > t)) P.push([x, y + st * (t - a) / (d - a)]);
          if (P.length >= 2) seg(lv, P[0], P[1]); if (P.length === 4) seg(lv, P[2], P[3]); } }
      var out = []; for (var k = 1; k <= L; k++) out.push('<path d="' + paths[k] + '" ' + stroke(k === L ? cw.accent : k % 3 === 0 ? cw.t3 : cw.line, C.lw * (k === L ? 1.6 : k % 3 === 0 ? 1.3 : 0.9)) + '/>');
      return { w: W, h: H, body: out.join(''), tile: true };
    };
    GEN['organic-dots'] = function (cw, r) {
      var W = 640, H = 400, T = Tile(W, H), F = field(r, W, H, 3, 1), pts = poisson(W, H, 15 * C.dens, r), acc = Math.floor(r() * pts.length);
      pts.forEach(function (p, i) { var v = (F(p[0], p[1]) + 1) / 2; if (v < 0.38 && i !== acc) return; var R = (1.2 + 4.2 * Math.pow(v, 2)) * C.dens; T.path(smoothD(blobPts(r, p[0], p[1], i === acc ? 7 : R, { n: 10, amp: 0.18, kmax: 3 }), true), [[p[0] - R, p[1] - R], [p[0] + R, p[1] + R]], fill(i === acc ? cw.accent : v > 0.8 ? cw.t3 : cw.t2)); });
      return T.done();
    };
    // ---- gradient / line / mixed ---------------------------------------------
    GEN['glow-field'] = function (cw, r, id) {
      var W = 800, H = 500, T = Tile(W, H), g = 'g' + (hash(C.name + id + cw.key) % 99999), cols = [cw.t3, cw.accent, cw.t2];
      T.add('<defs>' + cols.map(function (c, i) { return '<radialGradient id="' + g + i + '"><stop offset="0" stop-color="' + c + '" stop-opacity="' + (i === 1 ? 0.45 : 0.9) + '"/><stop offset="1" stop-color="' + c + '" stop-opacity="0"/></radialGradient>'; }).join('') + '</defs>');
      poisson(W, H, 210, r, 6).forEach(function (p, i) { var R = range(r, 150, 260); T.circle(p[0], p[1], R, 'fill="url(#' + g + (i % 3) + ')"'); });
      return T.done();
    };
    GEN['mesh-gradient'] = function (cw, r, id) {
      var W = 600, H = 400, T = Tile(W, H), g = 'm' + (hash(C.name + id + cw.key) % 99999), cols = [cw.t1, cw.t2, cw.t3];
      T.add('<defs>' + cols.map(function (c, i) { return '<radialGradient id="' + g + i + '"><stop offset="0" stop-color="' + c + '"/><stop offset="1" stop-color="' + c + '" stop-opacity="0"/></radialGradient>'; }).join('') + '</defs>');
      for (var j = 0; j < 3; j++) for (var i = 0; i < 4; i++) T.circle(i * 150 + range(r, -30, 30), j * 133 + range(r, -30, 30), range(r, 110, 170), 'fill="url(#' + g + ((i + j) % 3) + ')"');
      return T.done();
    };
    GEN['lines-dots'] = function (cw, r) {
      var g = Math.round(32 * C.dens), nx = Math.round(640 / g), ny = Math.round(384 / g), W = nx * g, H = ny * g, T = Tile(W, H), acc = Math.floor(r() * nx * ny);
      for (var j = 0; j < ny; j++) { var y = j * g + g / 2; if (j % 3 === 0) T.add('<path d="M0 ' + f(y) + 'H' + W + '" ' + stroke(cw.line, C.lw, { cap: 'butt' }) + '/>');
        for (var i = 0; i < nx; i++) { var x = i * g + g / 2, id = j * nx + i, q = r(); if (id === acc) T.circle(x, y, g * 0.18, fill(cw.accent)); else if (j % 3 !== 0 && q < 0.4) T.circle(x, y, C.lw * 1.6, fill(cw.t3)); else if (j % 3 === 0 && q < 0.3) T.circle(x, y, g * 0.1, fill(cw.t2)); } }
      return T.done();
    };
    GEN['outline-traces'] = function (cw, r) { return markOutline(cw, r, true); };
    GEN.confetti = function (cw, r) {
      var W = 720, H = 450, T = Tile(W, H), pts = poisson(W, H, 52 * C.dens, r), cols = [cw.accent, cw.accent2, cw.t3, cw.t2, cw.ink];
      pts.forEach(function (p, i) { var q = r(), col = i % 9 === 0 ? cols[4] : q < 0.22 ? cols[0] : q < 0.4 ? cols[1] : q < 0.75 ? cols[2] : cols[3], s = range(r, 7, 15) * C.dens, rot = r() * 360, k = r();
        if (C.lang === 'angular' || C.lang === 'orthogonal') { if (k < 0.5) { var a1 = C.pickAngle(r), a2 = a1 + range(r, 30, 60), tri = [[0, 0], [s * 2 * Math.cos(a1 * D2R), s * 2 * Math.sin(a1 * D2R)], [s * 1.5 * Math.cos(a2 * D2R), s * 1.5 * Math.sin(a2 * D2R)]], c = centroid(tri); T.poly(xform(tri, { ox: c[0], oy: c[1], x: p[0], y: p[1] }), fill(col)); }
          else { var th = C.cut, pl = [[-s, s * 0.5], [0, -s * 0.5 * Math.tan(th * D2R) * 0.5], [s, s * 0.5]]; T.path(polyD(xform(pl, { r: rot, x: p[0], y: p[1] }), true), xform(pl, { r: rot, x: p[0], y: p[1] }), stroke(col, C.lw * 2.4, { cap: C.cap, join: C.join })); } }
        else if (C.lang === 'organic') { if (k < 0.55) { var B = blobPts(r, p[0], p[1], s * 0.8, { n: 16, amp: 0.25, rot: rot }); T.path(smoothD(B, true), B, fill(col)); } else { var sq = []; for (var t = 0; t <= 12; t++) sq.push([t / 12 * s * 3 - s * 1.5, Math.sin(t / 12 * TAU) * s * 0.4]); sq = xform(sq, { r: rot, x: p[0], y: p[1] }); T.path(smoothD(sq, false), sq, stroke(col, C.lw * 2.2)); } }
        else { if (k < 0.4) T.circle(p[0], p[1], s * 0.45, fill(col)); else if (k < 0.7) T.circle(p[0], p[1], s * 0.6, stroke(col, C.lw * 2.2)); else { var A = arcPts(p[0], p[1], s * 0.8, rot, rot + 180, 14); T.path(polyD(A, true), A, stroke(col, C.lw * 2.4, { cap: 'round' })); } }
      });
      return T.done();
    };
    // ---- mark-derived --------------------------------------------------------
    function markRot(r, i, j) {
      if (unit.kind === 'emblem' || unit.kind === 'monogram' || unit.kind === 'wordmark') return C.lang === 'organic' ? range(r, -6, 6) : 0;
      if (C.lang === 'angular') return -C.shallow;
      if (C.lang === 'round') return ((i * 3 + j * 5) % 8) * 45;
      if (C.lang === 'organic') return range(r, -12, 12);
      return 0;
    }
    GEN['mark-repeat'] = function (cw, r) {
      var s = Math.round((unit.kind === 'emblem' ? 96 : 64) * C.dens), ax = Math.round(s * (unit.kind === 'emblem' ? 1.9 : 2.5)), ay = Math.round(s * (unit.kind === 'emblem' ? 1.7 : 1.9)), nx = 4, ny = 4, W = nx * ax, H = ny * ay, T = Tile(W, H), hero = [Math.floor(r() * nx), Math.floor(r() * ny)];
      var tf = tonal(cw), tc = trueColour(cw);
      for (var j = 0; j < ny; j++) for (var i = 0; i < nx; i++) { var x = i * ax + (j % 2 ? ax / 2 : 0) + ax / 2, y = j * ay + ay / 2, rot = markRot(r, i, j), isH = i === hero[0] && j === hero[1];
        if (C.lang === 'organic') { x += range(r, -0.08, 0.08) * ax; y += range(r, -0.08, 0.08) * ay; }
        T.add(unitAt(unit, x, y, s, rot, isH ? tc : tf), [x - s, y - s, x + s, y + s]); }
      return T.done();
    };
    function markOutline(cw, r, traces) {
      var U = (mark.kind === 'wordmark') ? mark : unit, wide = (U.bb[2] - U.bb[0]) / (U.bb[3] - U.bb[1]) > 2.5;
      if (wide) { // wordmarks: outlined rows, brick offset
        var s = Math.round(260 * C.dens), h = Math.round(s * (U.bb[3] - U.bb[1]) / (U.bb[2] - U.bb[0])), rowH = Math.round(h * 2.1), W = Math.round(s * 1.3) * 2, H = rowH * 4, T = Tile(W, H), ai = Math.floor(r() * 8);
        for (var j = 0; j < 4; j++) for (var i = 0; i < 2; i++) { var x = i * W / 2 + (j % 2 ? W / 4 : 0) + W / 4, y = j * rowH + rowH / 2, id = j * 2 + i;
          T.add(silAt(U, x, y, s, 0, stroke(id === ai ? cw.accent : j % 2 ? cw.line : cw.t3, C.lw * (id === ai ? 1.6 : 1.1))), [x - s * 0.6, y - h, x + s * 0.6, y + h]); }
        return T.done();
      }
      var simple = U.kind === 'emblem' || (U.solidity > 0.97 && U.parts.length > 3); // disc-like emblems: outline every part instead of echoing the silhouette
      var sz = Math.round((simple ? 140 : 104) * C.dens), a = Math.round(sz * (simple ? 1.3 : 1.55)), nx = 4, ny = 4, W2 = nx * a, H2 = ny * Math.round(a * 0.9), rh = Math.round(a * 0.9), T2 = Tile(W2, H2), acc = Math.floor(r() * nx * ny);
      for (var jj = 0; jj < ny; jj++) for (var ii = 0; ii < nx; ii++) { var x2 = ii * a + (jj % 2 ? a / 2 : 0) + a / 2, y2 = jj * rh + rh / 2, id2 = jj * nx + ii, rot = traces ? 0 : markRot(r, ii, jj) * 0.5, bb = [x2 - sz, y2 - sz, x2 + sz, y2 + sz];
        if (simple) { T2.add(partsOutlineAt(U, x2, y2, sz * 0.86, rot, id2 === acc ? cw.accent : cw.line, C.lw * 0.9), bb); continue; }
        [1, 0.7, 0.42].forEach(function (k, m) { T2.add(silAt(U, x2, y2, sz, rot, stroke(id2 === acc && m === 0 ? cw.accent : m === 0 ? cw.t3 : cw.line, C.lw * (m === 0 ? 1.4 : 1), SO), k), bb); });
      }
      return T2.done();
    }
    GEN['mark-outline'] = function (cw, r) { return markOutline(cw, r, false); };
    GEN['mark-crop'] = function (cw, r) {
      var W = 1600, H = 1000, U = unit, size = H * range(r, 1.22, 1.42), x = W * range(r, 0.66, 0.76), y = H * range(r, 0.45, 0.62), rot = C.lang === 'angular' ? -C.shallow : C.lang === 'organic' ? range(r, -8, 8) : 0;
      if (U.kind === 'emblem') rot = 0;
      var tf = function (p) { var t = p.rank; return fill(t < 0.34 ? cw.t3 : t < 0.67 ? cw.t2 : cw.t1); };
      var body = unitAt(U, x, y, size, rot, tf) + silAt(U, x, y, size, rot, stroke(cw.line, C.lw * 1.2, SO));
      // the one accent: a small true-colour mark in the calm area (sized for clear space)
      body += unitAt(U, W * 0.12, H * 0.82, Math.min(96, H * 0.1), 0, trueColour(cw));
      return { w: W, h: H, body: body, tile: false };
    };

    /* ---------------------------------------------------------------- catalogue */
    var META = {
      shards: ['Shards', 'shards · logo edge angles'], chevrons: ['Chevrons', 'chevrons · cut angle'], 'diagonal-bands': ['Diagonal bands', 'bands · crop angle'],
      'angle-hatch': ['Angle hatch', 'hatch · shallow angle'], prism: ['Prism', 'triangles · cut angle'], 'cut-grid': ['Cut grid', 'grid · chamfer'], 'rhombus-grid': ['Rhombus grid', 'lattice · cut angle'], 'mark-lattice': ['Mark lattice', 'mark silhouette · lattice'],
      facets: ['Facets', 'facets · mark tones'], 'facet-mesh': ['Facet mesh', 'mesh · nodes'], 'facet-scatter': ['Facet scatter', 'mark facets · scattered'],
      grid: ['Grid', 'grid · modules'], blocks: ['Blocks', 'blocks · modular'], stripes: ['Stripes', 'stripes · rhythm'], steps: ['Steps', 'steps · progress'], 'dot-grid': ['Dot grid', 'dots · grid'],
      orbits: ['Orbits', 'rings · satellites'], dots: ['Dots', 'dots · field'], halftone: ['Halftone rings', 'halftone · rings'], arcs: ['Arcs', 'arcs · truchet'], 'arc-rows': ['Arc rows', 'arcs · rows'], 'halo-rings': ['Halo', 'halo · glow'], rings: ['Rings', 'concentric · rings'],
      waves: ['Waves', 'waves · bands'], 'wave-lines': ['Wave lines', 'waves · lines'], blobs: ['Blobs', 'blobs · scattered'], terrazzo: ['Terrazzo', 'chips · texture'], 'flow-lines': ['Flow lines', 'flow · field'], ripples: ['Ripples', 'ripples · rings'], contours: ['Contours', 'contours · topography'], 'organic-dots': ['Seeds', 'dots · organic'],
      'glow-field': ['Glow field', 'gradient · glow'], 'mesh-gradient': ['Mesh gradient', 'gradient · mesh'], 'lines-dots': ['Lines & dots', 'lines · dots'], 'outline-traces': ['Outline traces', 'mark outline · traces'],
      confetti: ['Confetti', 'motifs · playful'], 'mark-repeat': ['Mark repeat', 'mark · repeat'], 'mark-outline': ['Mark outline', 'mark outline · rhythm'], 'mark-crop': ['Mark crop', 'mark · supergraphic']
    };
    var FAMILY = {
      facets: ['facets', 'facet-mesh', 'facet-scatter'], shards: ['shards'], chevrons: ['chevrons'], 'diagonal-bands': ['diagonal-bands'],
      grid: ['grid'], blocks: ['blocks'], stripes: ['stripes'], steps: ['steps'],
      orbits: ['orbits'], dots: ['dots', 'halftone'], arcs: ['arcs', 'arc-rows'], 'halftone-rings': ['halftone'], rings: ['rings'], halo: ['halo-rings'],
      waves: ['waves', 'wave-lines'], blobs: ['blobs', 'terrazzo'], 'flow-lines': ['flow-lines'], ripples: ['ripples'],
      contours: ['contours'], 'outline-traces': ['outline-traces'], 'glow-fields': ['glow-field'], 'glow-field': ['glow-field'], mesh: ['mesh-gradient'], 'mesh-gradients': ['mesh-gradient'],
      'lines-dots': ['lines-dots'], mixed: ['lines-dots']
    };
    var EXTRA = {
      angular: ['angle-hatch', 'prism', 'rhombus-grid', 'mark-lattice', 'cut-grid', 'shards', 'chevrons', 'diagonal-bands'],
      orthogonal: ['grid', 'blocks', 'stripes', 'steps', 'dot-grid', 'cut-grid', 'lines-dots'],
      round: ['dot-grid', 'halo-rings', 'rings', 'orbits', 'dots', 'arcs'],
      organic: ['ripples', 'contours', 'organic-dots', 'terrazzo', 'waves', 'blobs', 'flow-lines'],
      mixed: ['lines-dots', 'grid', 'dots', 'waves', 'dot-grid', 'arcs', 'shards']
    };
    var list = [];
    function addK(k) { if (GEN[k] && list.indexOf(k) < 0) list.push(k); }
    if (C.complexity === 'faceted') FAMILY.facets.forEach(addK);
    (dna.patterns || []).forEach(function (p) { (FAMILY[p] || [p]).forEach(addK); });
    if (C.complexity === 'gradient') { addK('glow-field'); addK('mesh-gradient'); }
    if (C.complexity === 'line' || C.complexity === 'outline') { addK('contours'); addK('outline-traces'); }
    if (C.playful) list.splice(Math.min(2, list.length), 0, 'confetti');
    (EXTRA[lang] || EXTRA.mixed).forEach(function (k) { if (list.length < 11) addK(k); });
    if (cfg.patterns) list = cfg.patterns.filter(function (k) { return GEN[k]; });
    ['mark-repeat', 'mark-outline', 'mark-crop'].forEach(function (k) { if (list.indexOf(k) >= 0) list.splice(list.indexOf(k), 1); });
    list = list.slice(0, 11).concat(['mark-repeat', 'mark-outline', 'mark-crop']);
    var catalogue = list.map(function (k) { var m = META[k] || [k, k]; var famKey = Object.keys(FAMILY).filter(function (x) { return FAMILY[x].indexOf(k) >= 0; })[0] || (k.indexOf('mark') === 0 ? 'mark' : lang);
      return { key: k, title: m[0], tags: m[1], family: famKey, tile: k !== 'mark-crop', derived: k.indexOf('mark') === 0 || k === 'facets' || k === 'facet-scatter' ? 'mark geometry' : 'design DNA' }; });

    function pattern(key, cwk, o) { o = o || {}; var cw = cwOf(cwk), g = GEN[key] || GEN['dot-grid']; return g(cw, rng(hash(C.name + '|' + key + '|' + (o.seed || 0))), key); }
    function tileSVG(key, cwk, o) { var cw = cwOf(cwk), P = pattern(key, cw, o), m = META[key] || [key];
      return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ' + P.w + ' ' + P.h + '" width="' + P.w + '" height="' + P.h + '" role="img" aria-label="' + m[0] + ' pattern — ' + cw.label + '"><title>' + esc(C.name) + ' · ' + m[0] + ' · ' + cw.label + (P.tile ? ' · seamless tile ' + P.w + '×' + P.h : ' · supergraphic') + '</title><rect id="bg" width="' + P.w + '" height="' + P.h + '" fill="' + cw.bg + '"/>' + P.body + '</svg>'; }
    function swatchSVG(key, cwk, W, H, o) { o = o || {}; var cw = cwOf(cwk), P = pattern(key, cw, o), id = 'pt' + (hash(key + cw.key) % 99999), sc = o.scale || 1;
      if (!P.tile) { var k = Math.max(W / P.w, H / P.h); return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ' + W + ' ' + H + '" width="' + W + '" height="' + H + '"><rect width="' + W + '" height="' + H + '" fill="' + cw.bg + '"/><g transform="translate(' + f((W - P.w * k) / 2) + ' ' + f((H - P.h * k) / 2) + ') scale(' + (+k.toFixed(4)) + ')">' + P.body + '</g></svg>'; }
      return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ' + W + ' ' + H + '" width="' + W + '" height="' + H + '"><defs><pattern id="' + id + '" width="' + P.w + '" height="' + P.h + '" patternUnits="userSpaceOnUse"' + (sc !== 1 ? ' patternTransform="scale(' + sc + ')"' : '') + '><rect width="' + P.w + '" height="' + P.h + '" fill="' + cw.bg + '"/>' + P.body + '</pattern></defs><rect width="' + W + '" height="' + H + '" fill="url(#' + id + ')"/></svg>'; }
    function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }

    /* ---------------------------------------------------------------- motifs (standalone shapes) */
    function motif(name, o) {
      o = o || {}; var r = rng(hash(C.name + '|motif|' + name + '|' + (o.seed || 0))), cw = cwOf(o.cw || 'paper'), col = o.color || cw.accent, col2 = o.color2 || cw.ink, S = o.size || 400, h = S / 2, b = '';
      var sw = Math.max(2, S / 90);
      switch (name) {
        case 'shard': { var a1 = C.pickAngle(r), a2 = a1 + (r() < 0.5 ? 1 : -1) * range(r, 26, 50), L = S * 0.8, tri = [[0, 0], [L * Math.cos(a1 * D2R), L * Math.sin(a1 * D2R)], [L * 0.75 * Math.cos(a2 * D2R), L * 0.75 * Math.sin(a2 * D2R)]], c = centroid(tri), bb0 = bbox(xform(tri, { ox: c[0], oy: c[1] })), k = S * 0.86 / Math.max(bb0[2] - bb0[0], bb0[3] - bb0[1]);
          b = '<path d="' + polyD(xform(tri, { ox: c[0], oy: c[1], s: k, x: h, y: h })) + '" fill="' + col + '"/>'; break; }
        case 'shard-cluster': { for (var i = 0; i < 5; i++) { var aa = C.pickAngle(r), ab = aa + (r() < 0.5 ? 1 : -1) * range(r, 22, 48), Ls = S * range(r, 0.22, 0.48), T3 = [[0, 0], [Ls * Math.cos(aa * D2R), Ls * Math.sin(aa * D2R)], [Ls * 0.7 * Math.cos(ab * D2R), Ls * 0.7 * Math.sin(ab * D2R)]], cc = centroid(T3);
            b += '<path d="' + polyD(xform(T3, { ox: cc[0], oy: cc[1], x: h + range(r, -0.24, 0.24) * S, y: h + range(r, -0.24, 0.24) * S })) + '" fill="' + (i === 0 ? col : i % 2 ? col2 : mix(col, cw.bg, 0.5)) + '"/>'; } break; }
        case 'chevron': { var th = clamp(C.cut, 30, 70), w = S * 0.7, rise = Math.min(S * 0.5, w / 2 * Math.tan(th * D2R)), t = S * 0.12; [0, 1, 2].forEach(function (k) { var y0 = h - rise / 2 + (k - 1) * t * 1.6; b += '<path d="' + polyD([[h - w / 2, y0 + rise], [h, y0], [h + w / 2, y0 + rise]], true) + '" ' + stroke(k === 1 ? col : col2, t * 0.7, { cap: C.cap === 'round' ? 'round' : 'butt', join: C.join === 'miter' ? 'miter' : 'round' }) + '/>'; }); break; }
        case 'facet-cluster': case 'crystal': { var pts = []; for (var q = 0; q < 14; q++) { var aq = r() * TAU, rq = Math.sqrt(r()) * S * 0.4; pts.push([h + Math.cos(aq) * rq * (name === 'crystal' ? 0.55 : 1), h + Math.sin(aq) * rq * (name === 'crystal' ? 1.1 : 1)]); }
          var hull = convexHull(pts); hull.forEach(function (p) { pts.push(p); }); var tri = delaunay(pts), look = markLookup();
          tri.forEach(function (tt, ti) { var P = [pts[tt[0]], pts[tt[1]], pts[tt[2]]], cc2 = centroid(P), v = look(cc2[0] / S, cc2[1] / S) + (r() - 0.5) * 0.3; var c3 = v < 0.3 ? col2 : v < 0.6 ? col : mix(col, cw.bg, 0.45); b += '<path d="' + polyD(P) + '" fill="' + c3 + '" stroke="' + c3 + '" stroke-width="0.8" stroke-linejoin="round"/>'; }); break; }
        case 'ring': b = '<circle cx="' + h + '" cy="' + h + '" r="' + f(S * 0.38) + '" ' + stroke(col, S * 0.08) + '/>'; break;
        case 'orbit-ring': case 'orbit': { var R = S * 0.33; b = '<circle cx="' + h + '" cy="' + h + '" r="' + f(R) + '" ' + stroke(col2, sw) + '/><circle cx="' + h + '" cy="' + h + '" r="' + f(R * 1.32) + '" ' + stroke(col2, sw * 0.7, { op: 0.45 }) + '/><circle cx="' + h + '" cy="' + h + '" r="' + f(R * 0.3) + '" fill="' + col + '"/><circle cx="' + f(h + R * Math.cos(-0.8)) + '" cy="' + f(h + R * Math.sin(-0.8)) + '" r="' + f(S * 0.055) + '" fill="' + col + '"/>'; break; }
        case 'dot': case 'dot-cluster': { var ps = poisson(S, S, S * 0.09, r, 26); ps.forEach(function (p, i) { var d = Math.hypot(p[0] - h, p[1] - h); if (d > S * 0.44) return; b += '<circle cx="' + f(p[0]) + '" cy="' + f(p[1]) + '" r="' + f(S * (0.014 + 0.04 * (1 - d / (S * 0.44)))) + '" fill="' + (i === 0 ? col : col2) + '"/>'; }); break; }
        case 'arc': { [0.42, 0.32, 0.22].forEach(function (k, m) { var P = arcPts(h, S * 0.72, S * k, 180, 360, 30); b += '<path d="' + polyD(P, true) + '" ' + stroke(m === 1 ? col : col2, S * 0.045, { cap: 'round' }) + '/>'; }); break; }
        case 'halo': { var gid = 'mh' + (hash(C.name + name) % 9999); b = '<defs><radialGradient id="' + gid + '"><stop offset="0" stop-color="' + col + '" stop-opacity="0.9"/><stop offset="1" stop-color="' + col + '" stop-opacity="0"/></radialGradient></defs><circle cx="' + h + '" cy="' + h + '" r="' + f(S * 0.48) + '" fill="url(#' + gid + ')"/>' + [0.2, 0.3, 0.4].map(function (k) { return '<circle cx="' + h + '" cy="' + h + '" r="' + f(S * k) + '" ' + stroke(col2, sw * 0.6, { op: 0.5 }) + '/>'; }).join(''); break; }
        case 'blob': { var P2 = blobPts(r, h, h, S * 0.36, { amp: 0.24, n: 40 }); b = '<path d="' + smoothD(P2, true) + '" fill="' + col + '"/>'; break; }
        case 'wave': { var P3 = []; for (var x = 0; x <= S; x += S / 40) P3.push([x, h + Math.sin(x / S * TAU * 1.5) * S * 0.12]); b = [0, 1, 2].map(function (k) { return '<path d="' + smoothD(P3.map(function (p) { return [p[0], p[1] + (k - 1) * S * 0.09]; }), false) + '" ' + stroke(k === 1 ? col : col2, S * 0.03) + '/>'; }).join(''); break; }
        case 'flow-line': { var F2 = field(r, S, S, 3, 1), lines = ''; for (var k2 = 0; k2 < 9; k2++) { var px = S * 0.1, py = S * (0.15 + k2 * 0.085), P4 = [[px, py]]; for (var st2 = 0; st2 < 60; st2++) { var an = F2(px, py) * 0.9; px += Math.cos(an) * S / 70; py += Math.sin(an) * S / 70; P4.push([px, py]); if (px > S * 0.92) break; } lines += '<path d="' + smoothD(P4.filter(function (p, i) { return i % 3 === 0; }), false) + '" ' + stroke(k2 === 4 ? col : col2, sw * (k2 === 4 ? 1.6 : 0.8)) + '/>'; } b = lines; break; }
        case 'ripple': { for (var k3 = 1; k3 <= 5; k3++) { var P5 = []; for (var a5 = 0; a5 < 48; a5++) { var t5 = a5 / 48 * TAU; P5.push([h + Math.cos(t5) * S * 0.085 * k3 * (1 + 0.05 * Math.sin(3 * t5 + k3)), h + Math.sin(t5) * S * 0.085 * k3 * (1 + 0.05 * Math.sin(2 * t5))]); } b += '<path d="' + smoothD(P5, true) + '" ' + stroke(k3 === 2 ? col : col2, sw * (k3 === 2 ? 1.6 : 0.9)) + '/>'; } break; }
        case 'diagonal-band': { var th2 = clamp(C.crop, 15, 88), dx = S / Math.tan(th2 * D2R); b = '<path d="' + polyD([[h - S * 0.12 - dx / 2, 0], [h + S * 0.12 - dx / 2, 0], [h + S * 0.12 + dx / 2, S], [h - S * 0.12 + dx / 2, S]]) + '" fill="' + col + '"/>'; break; }
        default: b = '<circle cx="' + h + '" cy="' + h + '" r="' + f(S * 0.3) + '" fill="' + col + '"/>';
      }
      return { w: S, h: S, body: b };
    }

    /* ---------------------------------------------------------------- compositions (backgrounds, generator) */
    /** clear-space plate behind a mark placed over artwork (corner grammar of the brand); h = half size */
    function plate(x, y, h, col) { var e = h * 1.05;
      if (C.corner === 'cut') { var c = e * 0.5, cy = Math.min(e, c * Math.tan(C.cut * D2R)); return '<path d="' + polyD([[x - e, y - e], [x + e, y - e], [x + e, y + e - cy], [x + e - c, y + e], [x - e, y + e]]) + '" fill="' + col + '"/>'; }
      if (C.corner === 'round' || C.corner === 'soft' || C.lang === 'round' || C.lang === 'organic') return '<circle cx="' + f(x) + '" cy="' + f(y) + '" r="' + f(e * 1.12) + '" fill="' + col + '"/>';
      return '<rect x="' + f(x - e) + '" y="' + f(y - e) + '" width="' + f(2 * e) + '" height="' + f(2 * e) + '" fill="' + col + '"/>'; }
    /** A background composition W×H in a colourway, with a calm `safe` zone [x, y, w, h] (fractions) for text.
     *  Geometry is placed outside the safe zone and every decoration fades out under it (feathered mask),
     *  so text never sits on pattern or line work.  o: { pattern, seed, mark (default true), patternScale } */
    function composition(cwk, W, H, o) {
      o = o || {}; var cw = cwOf(cwk), seed = o.seed || 0, r = rng(hash(C.name + '|comp|' + seed + '|' + W + 'x' + H)), uid = 'c' + (hash(C.name + cw.key + seed + W + H + (o.pattern || '')) % 999999);
      var pk = o.pattern || list[0], P = pattern(pk, cw, { seed: seed }), ar = W / H, fmt = ar >= 1.3 ? 'land' : ar > 0.8 ? 'square' : 'port', M = Math.min(W, H), sw = function (k) { return C.lw * k * M / 1080; };
      var defs = '<pattern id="' + uid + 'p" width="' + P.w + '" height="' + P.h + '" patternUnits="userSpaceOnUse"' + (o.patternScale && o.patternScale !== 1 ? ' patternTransform="scale(' + o.patternScale + ')"' : '') + '><rect width="' + P.w + '" height="' + P.h + '" fill="' + cw.bg + '"/>' + P.body + '</pattern>';
      var mode = C.composition || ({ angular: 'diagonal-tension', round: 'radial-centred', organic: 'flowing-asymmetric', orthogonal: 'grid-modular' }[C.lang] || 'grid-modular');
      var safe = fmt === 'land' ? [0.07, 0.14, 0.4, 0.72] : fmt === 'square' ? [0.08, 0.08, 0.7, 0.34] : [0.08, 0.07, 0.84, 0.33];
      var out = [], SX = safe[0] * W, SY = safe[1] * H, SR = (safe[0] + safe[2]) * W, SB = (safe[1] + safe[3]) * H;
      if (/diagonal/.test(mode)) {
        var th = clamp(C.crop, 50, 85), cot = 1 / Math.tan(th * D2R), dy = W * Math.tan(clamp(C.shallow, 8, 30) * D2R);
        if (fmt === 'land') { // band from the right, its edge on the crop angle, starting right of the text zone
          var x0 = SR + M * range(r, 0.06, 0.1), dx = H * cot;
          out.push('<path d="' + polyD([[x0, 0], [W + 10, 0], [W + 10, H], [x0 + dx, H]]) + '" fill="url(#' + uid + 'p)"/>');
          var sl = M * 0.018; out.push('<path d="' + polyD([[x0 - sl * 2.2, 0], [x0 - sl * 1.2, 0], [x0 + dx - sl * 1.2, H], [x0 + dx - sl * 2.2, H]]) + '" fill="' + cw.accent + '"/>');
          var edge = function (t) { return [x0 + dx * t, H * t]; };
        } else { // band rising from the bottom at the shallow angle
          var y0 = SB + M * 0.1;
          out.push('<path d="' + polyD([[0, y0 + dy], [W, y0], [W, H], [0, H]]) + '" fill="url(#' + uid + 'p)"/>');
          out.push('<path d="' + polyD([[0, y0 + dy - M * 0.03], [W, y0 - M * 0.03], [W, y0 - M * 0.018], [0, y0 + dy - M * 0.018]]) + '" fill="' + cw.accent + '"/>');
          var edge = function (t) { return [W * t, y0 + dy * (1 - t) - M * 0.05]; };
        }
        for (var i = 0; i < 4; i++) { var a1 = C.pickAngle(r), a2 = a1 + (r() < 0.5 ? 1 : -1) * range(r, 24, 50), L = M * range(r, 0.05, 0.13), tri = [[0, 0], [L * Math.cos(a1 * D2R), L * Math.sin(a1 * D2R)], [L * 0.7 * Math.cos(a2 * D2R), L * 0.7 * Math.sin(a2 * D2R)]], c = centroid(tri), e = edge(range(r, 0.3, 0.85));
          out.push('<path d="' + polyD(xform(tri, { ox: c[0], oy: c[1], x: e[0] + M * range(r, -0.02, 0.08), y: e[1] + M * range(r, -0.04, 0.04) })) + '" fill="' + (i === 0 ? cw.accent : i === 1 ? cw.t3 : cw.ink) + '"' + (i > 1 ? ' fill-opacity="0.85"' : '') + '/>'); }
      } else if (/radial/.test(mode)) {
        var cx, cy, R;
        if (fmt === 'land') { cx = W * range(r, 0.76, 0.8); cy = H * 0.52; R = Math.min(M * 0.5, (cx - SR - M * 0.04) / 1.24); }
        else if (fmt === 'square') { cx = W * 0.72; cy = H * 0.76; R = Math.min(M * 0.42, (cy - SB - M * 0.03) / 1.24); }
        else { cx = W * 0.5; cy = H * 0.72; R = Math.min(W * 0.46, (cy - SB - M * 0.04) / 1.24); }
        out.push('<circle cx="' + f(cx) + '" cy="' + f(cy) + '" r="' + f(R) + '" fill="url(#' + uid + 'p)"/>');
        [1.0, 1.22, 1.55].forEach(function (k, m) { out.push('<circle cx="' + f(cx) + '" cy="' + f(cy) + '" r="' + f(R * k) + '" ' + stroke(m ? cw.line : cw.t3, sw(m ? 1.6 : 2.6)) + '/>'); });
        var a0 = range(r, 110, 150), arcP = arcPts(cx, cy, R * 1.11, a0, a0 + range(r, 150, 200), 60); out.push('<path d="' + polyD(arcP, true) + '" ' + stroke(cw.accent, M * 0.016, { cap: 'round' }) + '/>');
        var ph = (a0 + range(r, 220, 260)) * D2R; out.push('<circle cx="' + f(cx + R * 1.22 * Math.cos(ph)) + '" cy="' + f(cy + R * 1.22 * Math.sin(ph)) + '" r="' + f(M * 0.022) + '" fill="' + cw.accent + '"/>');
        out.push('<circle cx="' + f(cx) + '" cy="' + f(cy) + '" r="' + f(R * 0.34) + '" fill="' + cw.bg + '"/><circle cx="' + f(cx) + '" cy="' + f(cy) + '" r="' + f(R * 0.34) + '" ' + stroke(cw.t3, sw(1.6)) + '/>');
        if (C.playful) out.push('<circle cx="' + f(cx - R * 1.3) + '" cy="' + f(cy + R * 0.85) + '" r="' + f(M * 0.04) + '" fill="' + cw.accent2 + '"/>');
      } else if (/flow|organic/.test(mode)) {
        var bx, by, BR;
        if (fmt === 'land') { bx = W * 0.8; by = H * 0.6; BR = Math.min(M * 0.6, (bx - SR) / 1.05); }
        else if (fmt === 'square') { bx = W * 0.66; by = H * 0.86; BR = M * 0.5; }
        else { bx = W * 0.62; by = H * 0.84; BR = W * 0.6; }
        var B1 = blobPts(r, bx, by, BR, { amp: 0.14, n: 40, sx: 1.08 }), B2 = blobPts(r, fmt === 'land' ? W * 0.97 : W * 0.06, fmt === 'land' ? H * 0.06 : H * 0.62, BR * 0.4, { amp: 0.2, n: 32 });
        out.push('<path d="' + smoothD(B2, true) + '" fill="' + cw.t2 + '"/>');
        out.push('<path d="' + smoothD(B1, true) + '" fill="url(#' + uid + 'p)"/>');
        out.push('<path d="' + smoothD(B1, true) + '" ' + stroke(cw.t3, sw(1.6)) + '/>');
        var F3 = field(r, W, H, 3, 1), yb = fmt === 'land' ? SB + M * 0.05 : SB + M * 0.08;
        for (var k = 0; k < 6; k++) { var Pf = [], yy = yb + k * M * 0.03; for (var xx = -20; xx <= W + 20; xx += W / 40) Pf.push([xx, yy + Math.sin(xx / W * TAU * 0.8 + k * 0.4) * M * 0.05 + F3(xx, yy) * M * 0.02]); out.push('<path d="' + smoothD(Pf, false) + '" ' + stroke(k === 2 ? cw.accent : cw.line, sw(k === 2 ? 2.2 : 1)) + '/>'); }
        var Bs = blobPts(r, fmt === 'land' ? W * 0.58 : W * 0.86, fmt === 'land' ? H * 0.86 : SB + M * 0.06, M * 0.032, { amp: 0.2 }); out.push('<path d="' + smoothD(Bs, true) + '" fill="' + cw.accent + '"/>');
      } else {
        if (fmt === 'land') { var gx = Math.max(SR + M * 0.05, W * 0.5); out.push('<rect x="' + f(gx) + '" y="0" width="' + f(W - gx) + '" height="' + H + '" fill="url(#' + uid + 'p)"/><rect x="' + f(gx - M * 0.012) + '" y="0" width="' + f(M * 0.012) + '" height="' + f(H * 0.4) + '" fill="' + cw.accent + '"/>'); }
        else { var gy = SB + M * 0.08; out.push('<rect x="0" y="' + f(gy) + '" width="' + W + '" height="' + f(H - gy) + '" fill="url(#' + uid + 'p)"/><rect x="0" y="' + f(gy - M * 0.012) + '" width="' + f(W * 0.4) + '" height="' + f(M * 0.012) + '" fill="' + cw.accent + '"/>'); }
      }
      // feathered keep-out under the text zone: decoration fades before it reaches the type
      var pad = M * 0.025, fb = M * 0.02;
      defs += '<filter id="' + uid + 'f" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="' + f(fb) + '"/></filter><mask id="' + uid + 'm" maskUnits="userSpaceOnUse" x="0" y="0" width="' + W + '" height="' + H + '"><rect width="' + W + '" height="' + H + '" fill="#fff"/><rect x="' + f(SX - pad) + '" y="' + f(SY - pad) + '" width="' + f(SR - SX + 2 * pad) + '" height="' + f(SB - SY + 2 * pad) + '" fill="#000" filter="url(#' + uid + 'f)"/></mask>';
      var markSvg = '';
      if (o.mark !== false && unit) { var ms = M * 0.075, mx = W - M * 0.07 - ms / 2, my = H - M * 0.07 - ms / 2; markSvg = plate(mx, my, ms * 1.0, cw.bg) + unitAt(unit, mx, my, ms, 0, trueColour(cw)); }
      return { body: '<defs>' + defs + '</defs><rect width="' + W + '" height="' + H + '" fill="' + cw.bg + '"/><g mask="url(#' + uid + 'm)">' + out.join('') + '</g>' + markSvg, safe: safe, mode: mode, pattern: pk };
    }

    return {
      C: C, catalogue: catalogue, colourways: CW, keys: list, generators: Object.keys(GEN),
      pattern: pattern, tileSVG: tileSVG, swatchSVG: swatchSVG, motif: motif, composition: composition,
      unitAt: function (x, y, size, rot, mode, cwk, which) { var U = which === 'mark' ? mark : unit, cw = cwOf(cwk || 'paper'); return unitAt(U, x, y, size, rot, mode === 'tonal' ? tonal(cw) : mode === 'mono' ? function () { return fill(cw.ink); } : trueColour(cw)); },
      silAt: function (x, y, size, rot, attrs, which, s2, outer) { return silAt(which === 'mark' ? mark : unit, x, y, size, rot, attrs, s2, outer); },
      plate: plate, unit: unit, mark: mark
    };
  }

  return {
    create: create, makeColourways: makeColourways, fromMarkData: fromMarkData,
    util: { hash: hash, rng: rng, f: f, mix: mix, lum: lum, contrast: contrast, visible: visible, parsePath: parsePath, bbox: bbox, area: area, centroid: centroid, xform: xform, polyD: polyD, smoothD: smoothD, circleD: circleD, arcPts: arcPts, blobPts: blobPts, delaunay: delaunay, poisson: poisson, field: field, convexHull: convexHull, inPoly: inPoly, dir: dir, stroke: stroke, fill: fill, range: range, pick: pick, clamp: clamp }
  };
}
if (typeof module === 'object' && module.exports) module.exports = GFXFactory();
