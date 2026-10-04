/* __NAME__ — generative motif engine (motion module of brand-system-forge).
   Animates the brand's pattern families from the design DNA on a <canvas>; every frame is a pure function of
   (motif, seed, colourway, density, t), so stills and exports are reproducible. Classic script, file:// safe.
   window.__G__.generative.render(ctx, W, H, t, { motif, seed, colourway, density })   ·   config: window.__G___GEN */
(function (global) {
  'use strict';
  var CFG = global.__G___GEN, TAU = Math.PI * 2;
  var A = (CFG.angle || 45) * Math.PI / 180, E = CFG.energy || 0.4, CH = CFG.character || 'glide';
  function rng(seed) { var a = (seed >>> 0) || 1; return function () { a |= 0; a = (a + 0x6D2B79F5) | 0; var t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
  function hash(s) { s = String(s); var h = 1779033703 ^ s.length; for (var i = 0; i < s.length; i++) { h = Math.imul(h ^ s.charCodeAt(i), 3432918353); h = (h << 13) | (h >>> 19); } return h >>> 0; }
  function hex(h) { if (h.charAt(0) !== '#') { var m = h.match(/\d+/g); return [+m[0], +m[1], +m[2]]; } h = h.replace('#', ''); return [parseInt(h.substr(0, 2), 16), parseInt(h.substr(2, 2), 16), parseInt(h.substr(4, 2), 16)]; }
  function mix(a, b, t) { var x = hex(a), y = hex(b); return 'rgb(' + x.map(function (v, i) { return Math.round(v + (y[i] - v) * t); }).join(',') + ')'; }
  function alpha(a, o) { var x = hex(a); return 'rgba(' + x.join(',') + ',' + o + ')'; }
  function lum(h) { var c = hex(h).map(function (v) { v /= 255; return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }); return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]; }
  function rgbHex(c) { if (c.charAt(0) === '#') return c; var m = c.match(/\d+/g); return '#' + m.slice(0, 3).map(function (v) { return ('0' + (+v).toString(16)).slice(-2); }).join(''); }
  function smooth(e) { return e * e * (3 - 2 * e); }
  /* motion clock by character: snap = holds then crisp hops · slide = measured steps · glide = continuous · flow = continuous, eased */
  function clock(t, period) {
    var u = t / period;
    if (CH === 'snap') { var k = Math.floor(u), f = u - k; return k + (f < 0.62 ? 0 : 1 - Math.pow(1 - (f - 0.62) / 0.38, 3)); }
    if (CH === 'slide') { var k2 = Math.floor(u), f2 = u - k2; return k2 + smooth(Math.min(1, f2 / 0.5)); }
    return u;
  }
  function poly(ctx, pts) { ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]); for (var i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]); ctx.closePath(); }
  function cap(ctx) { ctx.lineCap = CFG.cap === 'square' ? 'square' : CFG.cap === 'butt' ? 'butt' : 'round'; ctx.lineJoin = CFG.join === 'miter' ? 'miter' : 'round'; }
  var cache = {};
  function memo(key, fn) { if (!cache[key]) { cache = {}; cache[key] = fn(); } return cache[key]; }

  var R = {};
  /* facets — jittered triangulation; a light band crosses along the cut angle */
  R.facets = function (ctx, W, H, t, o) {
    var cell = Math.max(40, Math.min(W, H) / (3 + o.density * 1.6));
    var g = memo('f' + o.seed + W + H + o.density, function () {
      var r = rng(o.seed), cols = Math.ceil(W / cell) + 2, rows = Math.ceil(H / (cell * 0.866)) + 2, pts = [], tris = [];
      for (var j = 0; j < rows; j++) { pts.push([]); for (var i = 0; i < cols; i++) pts[j].push([(i - 0.5 + (j % 2) * 0.5) * cell + (r() - 0.5) * cell * 0.55, (j - 0.5) * cell * 0.866 + (r() - 0.5) * cell * 0.5]); }
      for (var y = 0; y < rows - 1; y++) for (var x = 0; x < cols - 1; x++) {
        var a = pts[y][x], b = pts[y][x + 1], c = pts[y + 1][x], d = pts[y + 1][x + 1];
        var T1 = y % 2 ? [a, d, c] : [a, b, c], T2 = y % 2 ? [a, b, d] : [b, d, c];
        [T1, T2].forEach(function (T) { var cx = (T[0][0] + T[1][0] + T[2][0]) / 3, cy = (T[0][1] + T[1][1] + T[2][1]) / 3; tris.push({ p: T, cx: cx, cy: cy, k: r(), c: Math.floor(r() * 1000) }); });
      }
      return tris;
    });
    var span = W * Math.sin(A) + H * Math.cos(A), band = clock(t, 2600 - 1200 * E) * 0.35 % 1.6 - 0.3, r0 = rng(o.seed + 7), ph = r0() * TAU, ph2 = r0() * TAU;
    // tonal ramp: background → palette colours ordered by luminance (a crystal, not confetti)
    var ramp = [o.bg].concat(o.colors.slice(0, 3)).sort(function (x, y) { return lum(y) - lum(x); });
    g.forEach(function (f) {
      var pr = (f.cx * Math.sin(A) + f.cy * Math.cos(A)) / span, qx = f.cx / W, qy = f.cy / H;
      var v = 0.5 + 0.28 * Math.sin(pr * 3.1 + ph) + 0.18 * Math.sin(qx * 5.3 - qy * 2.1 + ph2) + (f.k - 0.5) * 0.32;
      v = Math.max(0, Math.min(0.999, v)); var seg = v * (ramp.length - 1), i0 = Math.floor(seg), col = mix(ramp[i0], ramp[i0 + 1], seg - i0);
      if (f.c % 89 === 0) col = o.accent;
      var lit = Math.max(0, 1 - Math.abs(pr - band) / 0.14);
      if (lit > 0) col = mix(rgbHex(col), o.hi, lit * 0.5);
      poly(ctx, f.p); ctx.fillStyle = col; ctx.fill(); ctx.strokeStyle = col; ctx.lineWidth = 0.75; ctx.stroke();
    });
  };
  /* shards — thin splinters aligned to the cut angle, travelling along it */
  R.shards = function (ctx, W, H, t, o) {
    var n = Math.round(14 + o.density * 12);
    var g = memo('s' + o.seed + W + H + o.density, function () { var r = rng(o.seed), L = []; for (var i = 0; i < n; i++) L.push({ x: r() * W, y: r() * H, l: (0.08 + r() * 0.3) * Math.max(W, H), w: (0.008 + r() * 0.03) * Math.min(W, H), c: Math.floor(r() * 99), s: 0.4 + r(), k: r() }); return L; });
    var dx = Math.cos(A), dy = -Math.sin(A), nx = Math.sin(A), ny = Math.cos(A), D = W + H;
    g.forEach(function (s) {
      var off = ((clock(t, 2200) * s.s * 0.06 * D + s.k * D) % D) - D * 0.25, x = s.x + dx * off, y = s.y + dy * off;
      x = ((x % (W + s.l)) + W + s.l) % (W + s.l) - s.l * 0.5; y = ((y % (H + s.l)) + H + s.l) % (H + s.l) - s.l * 0.5;
      poly(ctx, [[x - dx * s.l / 2, y - dy * s.l / 2], [x + dx * s.l / 2 + nx * s.w * 0.2, y + dy * s.l / 2 + ny * s.w * 0.2], [x + nx * s.w, y + ny * s.w]]);
      ctx.fillStyle = s.k < 0.08 ? o.accent : o.colors[s.c % Math.min(3, o.colors.length)]; ctx.fill();
    });
  };
  /* chevrons — rows of V shapes at the cut angle */
  R.chevrons = function (ctx, W, H, t, o) {
    var gap = Math.max(26, Math.min(W, H) / (4 + o.density * 2)), arm = gap * 0.9, rise = arm * Math.tan(A) * 0.5, lw = gap * 0.22, shift = clock(t, 1800) * gap * 0.5;
    cap(ctx); ctx.lineWidth = lw; var r = rng(o.seed), rows = Math.ceil(H / (rise + gap * 0.6)) + 2;
    for (var j = -1; j < rows; j++) {
      var y = j * (rise + gap * 0.6), col = o.colors[Math.floor(r() * o.colors.length)], hot = r() < 0.12;
      ctx.strokeStyle = hot ? o.accent : col; ctx.beginPath();
      for (var x = -gap * 2 + ((shift * (j % 2 ? 1 : -1)) % (gap * 2)); x < W + gap * 2; x += gap * 2) { ctx.moveTo(x, y + rise); ctx.lineTo(x + gap, y); ctx.lineTo(x + gap * 2, y + rise); }
      ctx.stroke();
    }
  };
  /* bands — parallel bands (diagonal at the cut angle, or straight for stripes/lines) sliding across */
  R.bands = function (ctx, W, H, t, o, ang, thin) {
    var a = ang == null ? A : ang, n = Math.round(6 + o.density * 4), r = rng(o.seed), widths = [];
    for (var i = 0; i < n; i++) widths.push((thin ? 0.12 : 0.4 + r() * 1.2));
    var tot = widths.reduce(function (s, v) { return s + v; }, 0), D = Math.abs(W * Math.sin(a)) + Math.abs(H * Math.cos(a)), unit = D * 1.4 / tot;
    ctx.save(); ctx.translate(W / 2, H / 2); ctx.rotate(-(Math.PI / 2 - a)); var off = (clock(t, 2400) * unit * 0.6) % (tot * unit), x = -D - off, k = 0;
    while (x < D) { var w = widths[k % n] * unit, slot = k % 4, col = k % 11 === 6 ? o.accent : slot === 0 ? o.colors[0] : slot === 2 ? o.colors[1 % o.colors.length] : null; if (thin ? k % 2 === 0 : col) { ctx.fillStyle = thin ? o.ink : col; ctx.fillRect(x, -D, thin ? Math.max(1.5, w * 0.12) : w, 2 * D); } x += thin ? unit * 0.6 : w; k++; }
    ctx.restore();
  };
  /* blocks — modular grid; cells switch on the beat */
  R.blocks = function (ctx, W, H, t, o, lines) {
    var cell = Math.max(24, Math.min(W, H) / (4 + o.density * 2)), cols = Math.ceil(W / cell), rows = Math.ceil(H / cell), beat = Math.floor(clock(t, 900));
    ctx.strokeStyle = alpha(o.inkHex, 0.14); ctx.lineWidth = 1;
    for (var i = 0; i <= cols; i++) { ctx.beginPath(); ctx.moveTo(i * cell + 0.5, 0); ctx.lineTo(i * cell + 0.5, H); ctx.stroke(); }
    for (var j = 0; j <= rows; j++) { ctx.beginPath(); ctx.moveTo(0, j * cell + 0.5); ctx.lineTo(W, j * cell + 0.5); ctx.stroke(); }
    if (lines) return;
    for (var y = 0; y < rows; y++) for (var x = 0; x < cols; x++) {
      var r = rng(o.seed + x * 131 + y * 977 + beat * 7)(); if (r > 0.18 + 0.1 * o.density / 5) continue;
      ctx.fillStyle = r < 0.03 ? o.accent : o.colors[Math.floor(r * 1000) % o.colors.length];
      var f = CH === 'slide' ? smooth(Math.min(1, (clock(t, 900) % 1) * 2)) : 1; ctx.fillRect(x * cell + 2, y * cell + 2 + (1 - f) * cell * 0.5, cell - 4, (cell - 4) * (0.5 + 0.5 * f));
    }
  };
  /* orbits — rings around centres, dots travelling on them */
  R.orbits = function (ctx, W, H, t, o) {
    var g = memo('o' + o.seed + W + H + o.density, function () { var r = rng(o.seed), C = [], n = 1 + Math.floor(r() * 2); for (var i = 0; i < n; i++) C.push({ x: W * (0.3 + r() * 0.4), y: H * (0.3 + r() * 0.4), rings: 3 + Math.round(o.density * 1.5), s: Math.min(W, H) * (0.08 + r() * 0.05), ph: r() * TAU }); return C; });
    cap(ctx);
    g.forEach(function (c, ci) {
      for (var k = 1; k <= c.rings; k++) {
        var R0 = c.s * k * 1.15, sp = (k % 2 ? 1 : -0.7) * (0.25 + E) / (k * 0.6), a = c.ph + clock(t, 6000) * TAU * sp;
        ctx.strokeStyle = alpha(o.inkHex, 0.16); ctx.lineWidth = 1.25; ctx.beginPath(); ctx.arc(c.x, c.y, R0, 0, TAU); ctx.stroke();
        ctx.strokeStyle = o.colors[(k + ci) % o.colors.length]; ctx.lineWidth = Math.max(2, c.s * 0.12); ctx.beginPath(); ctx.arc(c.x, c.y, R0, a, a + 0.6 + 0.25 * (k % 3)); ctx.stroke();
        ctx.fillStyle = k % 3 === 0 ? o.accent : o.colors[(k + 1) % o.colors.length]; ctx.beginPath(); ctx.arc(c.x + Math.cos(a + 2.4) * R0, c.y + Math.sin(a + 2.4) * R0, Math.max(3, c.s * 0.16), 0, TAU); ctx.fill();
      }
      ctx.fillStyle = o.colors[0]; ctx.beginPath(); ctx.arc(c.x, c.y, c.s * 0.5, 0, TAU); ctx.fill();
    });
  };
  /* dots — grid of dots breathing in a travelling wave */
  R.dots = function (ctx, W, H, t, o) {
    var gap = Math.max(14, Math.min(W, H) / (8 + o.density * 4)), r = rng(o.seed), cx = W * (0.25 + r() * 0.5), cy = H * (0.25 + r() * 0.5), ph = clock(t, 2600) * TAU;
    for (var y = gap / 2; y < H; y += gap) for (var x = gap / 2; x < W; x += gap) {
      var d = Math.hypot(x - cx, y - cy) / Math.max(W, H), s = 0.5 + 0.5 * Math.sin(d * 18 - ph);
      ctx.fillStyle = s > 0.93 ? o.accent : o.colors[Math.floor(d * 7) % o.colors.length];
      ctx.beginPath(); ctx.arc(x, y, gap * (0.08 + 0.26 * s), 0, TAU); ctx.fill();
    }
  };
  /* arcs — quarter-circle tiles that turn */
  R.arcs = function (ctx, W, H, t, o) {
    var cell = Math.max(30, Math.min(W, H) / (3 + o.density * 1.5)), cols = Math.ceil(W / cell), rows = Math.ceil(H / cell); cap(ctx); ctx.lineWidth = cell * 0.16;
    for (var y = 0; y < rows; y++) for (var x = 0; x < cols; x++) {
      var r = rng(o.seed + x * 31 + y * 1013), q = Math.floor(r() * 4), turn = clock(t + r() * 4000, 4200), fr = turn - Math.floor(turn), rot = (q + Math.floor(turn) + (CH === 'glide' || CH === 'flow' ? smooth(Math.min(1, fr * 3)) : fr > 0.8 ? 1 : 0)) * Math.PI / 2;
      ctx.save(); ctx.translate(x * cell + cell / 2, y * cell + cell / 2); ctx.rotate(rot);
      ctx.strokeStyle = r() < 0.1 ? o.accent : o.colors[(x + y) % o.colors.length];
      ctx.beginPath(); ctx.arc(-cell / 2, -cell / 2, cell / 2, 0, Math.PI / 2); ctx.stroke(); ctx.beginPath(); ctx.arc(cell / 2, cell / 2, cell / 2, Math.PI, Math.PI * 1.5); ctx.stroke();
      ctx.restore();
    }
  };
  /* waves — stacked sine lines */
  R.waves = function (ctx, W, H, t, o) {
    var n = Math.round(8 + o.density * 5), r = rng(o.seed), ph = clock(t, 5000) * TAU, amp = H * (0.02 + 0.04 * E), f1 = 1.5 + r() * 2, f2 = 3 + r() * 3; cap(ctx);
    for (var i = 0; i < n; i++) {
      var y0 = H * (i + 0.5) / n; ctx.strokeStyle = i % 6 === 4 ? o.accent : o.colors[i % o.colors.length]; ctx.lineWidth = Math.max(1.5, H / n * (0.12 + 0.2 * r()));
      ctx.beginPath(); for (var x = -10; x <= W + 10; x += 8) { var y = y0 + Math.sin(x / W * TAU * f1 + ph + i * 0.35) * amp + Math.sin(x / W * TAU * f2 - ph * 0.6 + i) * amp * 0.4; if (x < 0) ctx.moveTo(x, y); else ctx.lineTo(x, y); } ctx.stroke();
    }
  };
  /* blobs — soft organic shapes drifting and morphing */
  function blob(ctx, cx, cy, rad, seed, ph, wob) { var r = rng(seed), k = [r(), r(), r(), r()], pts = []; for (var i = 0; i < 48; i++) { var a = i / 48 * TAU, rr = rad * (1 + wob * (0.12 * Math.sin(a * 2 + k[0] * 6 + ph) + 0.08 * Math.sin(a * 3 + k[1] * 6 - ph * 0.7) + 0.05 * Math.sin(a * 5 + k[2] * 6 + ph * 1.3))); pts.push([cx + Math.cos(a) * rr, cy + Math.sin(a) * rr]); }
    ctx.beginPath(); for (var j = 0; j < pts.length; j++) { var p0 = pts[j], p1 = pts[(j + 1) % pts.length], mx = (p0[0] + p1[0]) / 2, my = (p0[1] + p1[1]) / 2; if (!j) ctx.moveTo(mx, my); else ctx.quadraticCurveTo(p0[0], p0[1], mx, my); } ctx.closePath(); }
  R.blobs = function (ctx, W, H, t, o) {
    var n = 3 + Math.round(o.density), r = rng(o.seed), ph = clock(t, 7000) * TAU;
    for (var i = 0; i < n; i++) { var s = Math.min(W, H) * (0.18 + r() * 0.22), x = W * r() + Math.sin(ph + i) * s * 0.25, y = H * r() + Math.cos(ph * 0.8 + i) * s * 0.2;
      blob(ctx, x, y, s, o.seed + i * 17, ph + i, 1 + E); ctx.fillStyle = i === n - 1 ? o.accent : o.colors[i % o.colors.length]; ctx.globalAlpha = i === n - 1 ? 0.95 : 0.88; ctx.fill(); ctx.globalAlpha = 1; }
  };
  /* flow-lines — streamlines of a smooth field */
  R.flow = function (ctx, W, H, t, o) {
    var n = Math.round(30 + o.density * 25), r = rng(o.seed), ph = clock(t, 9000) * TAU * 0.25, k1 = 1.2 + r() * 1.5, k2 = 1.5 + r() * 1.5; cap(ctx);
    for (var i = 0; i < n; i++) {
      var x = r() * W, y = r() * H, len = 30 + r() * 60, col = r() < 0.08 ? o.accent : o.colors[i % o.colors.length]; ctx.strokeStyle = col; ctx.lineWidth = 1.5 + r() * 2.5;
      ctx.beginPath(); ctx.moveTo(x, y);
      for (var s = 0; s < len; s++) { var a = Math.sin(x / W * TAU * k1 + ph) + Math.cos(y / H * TAU * k2 - ph * 0.8); x += Math.cos(a) * 6; y += Math.sin(a) * 6; ctx.lineTo(x, y); }
      ctx.stroke();
    }
  };
  /* contours — topographic rings */
  R.contours = function (ctx, W, H, t, o) {
    var r = rng(o.seed), cx = W * (0.3 + r() * 0.4), cy = H * (0.3 + r() * 0.4), n = Math.round(8 + o.density * 4), ph = clock(t, 8000) * TAU, step = Math.max(W, H) / n * 0.75; cap(ctx);
    for (var i = n; i >= 1; i--) { blob(ctx, cx, cy, step * i, o.seed + 3, ph * 0.5 + i * 0.15, 1.6); ctx.strokeStyle = i % 4 === 0 ? o.accent : o.colors[i % o.colors.length]; ctx.lineWidth = Math.max(1.5, step * 0.06); ctx.stroke(); }
  };
  /* glow-fields — soft light fields */
  R.glow = function (ctx, W, H, t, o) {
    var n = 3 + Math.round(o.density / 2), r = rng(o.seed), ph = clock(t, 9000) * TAU;
    for (var i = 0; i < n; i++) { var x = W * r() + Math.sin(ph + i * 2) * W * 0.08, y = H * r() + Math.cos(ph + i) * H * 0.08, rad = Math.max(W, H) * (0.3 + r() * 0.3), g = ctx.createRadialGradient(x, y, 0, x, y, rad), c = i === 0 ? o.accent : o.colors[i % o.colors.length];
      g.addColorStop(0, alpha(c.charAt(0) === '#' ? c : o.colors[0], 0.85)); g.addColorStop(1, alpha(c.charAt(0) === '#' ? c : o.colors[0], 0)); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); }
  };
  var MAP = { facets: 'facets', shards: 'shards', chevrons: 'chevrons', 'diagonal-bands': 'bands', stripes: 'stripes', lines: 'lines', grid: 'grid', blocks: 'blocks', orbits: 'orbits', dots: 'dots', arcs: 'arcs', waves: 'waves', blobs: 'blobs', 'flow-lines': 'flow', contours: 'contours', 'glow-fields': 'glow' };
  function draw(name, ctx, W, H, t, o) {
    var k = MAP[name] || name;
    if (k === 'stripes') return R.bands(ctx, W, H, t, o, Math.PI / 2, false);
    if (k === 'lines') return R.bands(ctx, W, H, t, o, Math.PI / 2, true);
    if (k === 'grid') return R.blocks(ctx, W, H, t, o, true);
    if (k === 'bands') return R.bands(ctx, W, H, t, o, A, false);
    return (R[k] || R.dots)(ctx, W, H, t, o);
  }
  var NSG = global.__G__ || (global.__G__ = {});
  var api = NSG.generative = {
    motifs: CFG.patterns, colourways: CFG.colourways, renderers: R,
    /** Draw one frame. o: { motif, seed, colourway (key), density 1–5 } */
    render: function (ctx, W, H, t, o) {
      o = o || {}; var cw = CFG.colourways.filter(function (c) { return c.key === o.colourway; })[0] || CFG.colourways[0];
      var opts = { seed: (o.seed == null ? hash(CFG.name) : +o.seed) >>> 0, density: o.density || 3, colors: cw.colors, accent: cw.accent, bg: cw.bg, hi: cw.hi, ink: cw.ink, inkHex: cw.ink };
      ctx.save(); ctx.fillStyle = cw.bg; ctx.fillRect(0, 0, W, H); draw(o.motif || CFG.patterns[0], ctx, W, H, t || 0, opts); ctx.restore();
    },
    hash: hash
  };
})(window);
