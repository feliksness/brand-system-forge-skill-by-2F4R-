// devices.js — GRAPHICS/<family>/<name>.svg + .png : frames, corners, bands, dividers, badges, numbers, quotes,
// arrows, highlights, shapes (dna.motifs), mark devices, backgrounds (hero / square / story).
// Every device is built from the DNA (corner style, angles, stroke, motifs, base language) + mark geometry.
const fs = require('fs'), path = require('path');
const D2R = Math.PI / 180;

function run(ctx) {
  const { b, F, gfx, cw, B } = ctx, U = ctx.CORE.util, f = U.f, dna = b.dna || {};
  const root = b.path('GRAPHICS');
  const FAMS = ['frames', 'corners', 'bands', 'dividers', 'badges', 'numbers', 'quotes', 'arrows', 'highlights', 'shapes', 'mark', 'backgrounds', 'previews'];
  FAMS.forEach(d => fs.rmSync(path.join(root, d), { recursive: true, force: true }));
  const C = gfx.C, lang = C.lang, corner = C.corner, cut = C.cut, crop = C.crop, shallow = C.shallow;
  const angular = lang === 'angular' || corner === 'cut', round = lang === 'round', organic = lang === 'organic' || corner === 'soft', ortho = lang === 'orthogonal' || (corner === 'square' && !angular && !round && !organic);
  const style = angular ? 'angular' : round ? 'round' : organic ? 'organic' : ortho ? 'orthogonal' : 'mixed';
  const pc = cw.paper, P = pc.accent, Fd = pc.ink, A = pc.accent2, BG = pc.bg, T1 = pc.t1, T2 = pc.t2, T3 = pc.t3, LN = pc.line;
  const iconPx = (dna.stroke || {}).icon_px_at_24 || 2, cap = C.cap, join = C.join;
  const G = ctx.glyphs || {}, gm = G.meta || {};
  const out = []; // {family, name, w, h, svg, title, dark}
  const rr = U.rng(U.hash(b.name + '|devices'));

  function svgDoc(w, h, body, title) { return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" role="img" aria-label="${esc(title)}"><title>${esc(b.name)} · ${esc(title)}</title>${body}</svg>`; }
  function esc(s) { return String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c])); }
  function add(family, name, w, h, body, title, o) { out.push(Object.assign({ family, name, w, h, svg: svgDoc(w, h, body, title || name), title: title || name }, o || {})); }
  const st = (c, w, o) => U.stroke(c, w, Object.assign({ cap, join }, o || {}));
  const dsw = S => Math.max(2, S / 24 * iconPx * 0.55);
  const tan = a => Math.tan(a * D2R);

  /* ------------------------------------------------------------ shape grammar */
  function chamfer(x, y, w, h, c, corners) {
    const cy = Math.min(c * tan(cut), h * 0.45), cx = Math.min(c, w * 0.45), has = k => corners.indexOf(k) >= 0, p = [];
    p.push([x + (has('tl') ? cx : 0), y]); p.push([x + w - (has('tr') ? cx : 0), y]); if (has('tr')) p.push([x + w, y + cy]);
    p.push([x + w, y + h - (has('br') ? cy : 0)]); if (has('br')) p.push([x + w - cx, y + h]);
    p.push([x + (has('bl') ? cx : 0), y + h]); if (has('bl')) p.push([x, y + h - cy]);
    p.push([x, y + (has('tl') ? cy : 0)]); return U.polyD(p);
  }
  function rrect(x, y, w, h, r, k) { r = Math.min(r, w / 2, h / 2); k = k || 0.5523; const q = r * (1 - k);
    return `M${f(x + r)} ${f(y)}H${f(x + w - r)}C${f(x + w - q)} ${f(y)} ${f(x + w)} ${f(y + q)} ${f(x + w)} ${f(y + r)}V${f(y + h - r)}C${f(x + w)} ${f(y + h - q)} ${f(x + w - q)} ${f(y + h)} ${f(x + w - r)} ${f(y + h)}H${f(x + r)}C${f(x + q)} ${f(y + h)} ${f(x)} ${f(y + h - q)} ${f(x)} ${f(y + h - r)}V${f(y + r)}C${f(x)} ${f(y + q)} ${f(x + q)} ${f(y)} ${f(x + r)} ${f(y)}Z`; }
  /** container in the brand's corner grammar */
  function shape(x, y, w, h, o) { o = o || {}; const m = Math.min(w, h);
    if (corner === 'cut') return chamfer(x, y, w, h, o.c || m * 0.16, o.corners || 'br');
    if (corner === 'round') return o.pill ? rrect(x, y, w, h, m / 2) : rrect(x, y, w, h, m * 0.14);
    if (corner === 'soft') return rrect(x, y, w, h, m * 0.24, 0.86);
    if (corner === 'rounded') return rrect(x, y, w, h, m * 0.08);
    return `M${f(x)} ${f(y)}H${f(x + w)}V${f(y + h)}H${f(x)}Z`;
  }
  /** compact badge outline around a centre */
  function badge(cx, cy, R, o) { o = o || {}; const r = U.rng(U.hash(b.name + '|badge|' + (o.seed || 0)));
    if (angular) { const c = R * 0.42, x = cx - R, y = cy - R; return chamfer(x, y, 2 * R, 2 * R, c, 'tl,br'); }
    if (organic) return U.smoothD(U.blobPts(r, cx, cy, R * 0.96, { amp: 0.09, n: 30, kmax: 3 }), true);
    if (round) return U.circleD(cx, cy, R);
    return `M${f(cx - R)} ${f(cy - R)}h${f(2 * R)}v${f(2 * R)}h${f(-2 * R)}Z`;
  }
  function text(role, str, x, y, size, o) { o = o || {}; const g = G[role];
    if (g && g.glyphs) return B.textSVG(g, str, x, y, Object.assign({ size }, o));
    const fam = (b.stacks[role === 'label' ? 'mono' : role] || b.stacks.sans || 'sans-serif').replace(/"/g, "'");
    return { svg: `<text x="${f(x)}" y="${f(y)}" font-family="${fam}" font-size="${f(size)}" fill="${o.fill || Fd}" text-anchor="${o.anchor || 'start'}">${esc(o.upper ? String(str).toUpperCase() : str)}</text>`, w: String(str).length * size * 0.56 };
  }
  function fitText(role, str, maxW, size, o) { let t = text(role, str, 0, 0, size, o); if (t.w > maxW) size = size * maxW / t.w; return size; }
  function textOnCircle(role, str, cx, cy, R, size, o) { o = o || {}; const g = G[role]; if (!g || !g.glyphs) return '';
    let s = String(str); if (o.upper) s = s.toLocaleUpperCase(); const k = size / 1000, tr = (o.tracking || 0.12) * 1000;
    const gl = [...s].map(ch => g.glyphs[ch] || g.glyphs['?'] || { d: '', w: 500 }); const total = (gl.reduce((a, q) => a + q.w + tr, 0) - tr) * k;
    const bottom = !!o.bottom, span = total / R, cap = (g.cap || 700) * k; let cum = 0; const parts = [];
    gl.forEach(q => { const wq = q.w * k, mid = cum + wq / 2;
      if (!bottom) { const a = -Math.PI / 2 - span / 2 + mid / R; parts.push(`<path transform="translate(${f(cx + R * Math.cos(a))} ${f(cy + R * Math.sin(a))}) rotate(${f(a * 180 / Math.PI + 90)}) scale(${+k.toFixed(5)}) translate(${f(-q.w / 2)} 0)" d="${q.d}"/>`); }
      else { const Rb = R + cap, a = Math.PI / 2 + span * (Rb / R) / 2 - mid / Rb * (1); parts.push(`<path transform="translate(${f(cx + Rb * Math.cos(a))} ${f(cy + Rb * Math.sin(a))}) rotate(${f(a * 180 / Math.PI - 90)}) scale(${+k.toFixed(5)}) translate(${f(-q.w / 2)} 0)" d="${q.d}"/>`); }
      cum += wq + tr * k; });
    return `<g fill="${o.fill || Fd}">${parts.join('')}</g>`;
  }
  const labelO = (fill, extra) => Object.assign({ fill, upper: gm.labelUpper !== false, tracking: gm.labelTracking || 0.06 }, extra || {});

  /* ------------------------------------------------------------ FRAMES */
  (function frames() {
    const W = 1200, H = 800, m = 80, L = 150, sw = dsw(600);
    let body = '';
    if (corner === 'cut') { const c = 44, cy = Math.min(c * tan(cut), 100);
      const tl = [[m, m + L], [m, m + cy], [m + c, m], [m + L, m]];
      [[1, 1, 0, 0], [-1, 1, W, 0], [1, -1, 0, H], [-1, -1, W, H]].forEach(([sx, sy, ox, oy], i) => { const pts = tl.map(p => [ox + sx * p[0], oy + sy * p[1]]); body += `<path d="${U.polyD(pts, true)}" ${st(i === 3 ? P : Fd, sw)}/>`; });
    } else if (corner === 'square') {
      [[m, m, 1, 1], [W - m, m, -1, 1], [m, H - m, 1, -1], [W - m, H - m, -1, -1]].forEach(([x, y, sx, sy], i) => { body += `<path d="M${x} ${y + sy * L}V${y}H${x + sx * L}" ${st(i === 3 ? P : Fd, sw, { cap: 'square', join: 'miter' })}/><path d="M${x + sx * 24} ${y + sy * 40}h${sx * 32}M${x + sx * 40} ${y + sy * 24}v${sy * 32}" ${st(LN, sw * 0.5)}/>`; });
    } else { const rad = corner === 'soft' || organic ? 90 : 56;
      [[m, m, 1, 1], [W - m, m, -1, 1], [m, H - m, 1, -1], [W - m, H - m, -1, -1]].forEach(([x, y, sx, sy], i) => { const sweep = sx * sy > 0 ? 1 : 0;
        body += `<path d="M${x} ${y + sy * L}V${y + sy * rad}A${rad} ${rad} 0 0 ${sweep} ${x + sx * rad} ${y}H${x + sx * L}" ${st(i === 3 ? P : Fd, sw, { cap: 'round' })}/>`; });
      if (round) body += `<circle cx="${W - m}" cy="${H - m}" r="${sw * 1.6}" fill="${P}"/>`;
    }
    add('frames', 'frame-corner', W, H, body, 'Corner frame — four corner marks in the brand corner grammar');
    // full frame + inner hairline
    let full = `<path d="${shape(m, m, W - 2 * m, H - 2 * m, { corners: 'tl,br', c: 70 })}" ${st(Fd, sw)}/><path d="${shape(m + 22, m + 22, W - 2 * m - 44, H - 2 * m - 44, { corners: 'tl,br', c: 56 })}" ${st(LN, Math.max(1.5, sw * 0.35))}/>`;
    if (ortho) full += [0.25, 0.5, 0.75].map(t => `<path d="M${f(m + t * (W - 2 * m))} ${m - 16}v32M${f(m + t * (W - 2 * m))} ${H - m - 16}v32" ${st(Fd, sw * 0.6)}/>`).join('');
    add('frames', 'frame-full', W, H, full, 'Full frame with inner hairline');
    // offset frame: filled ground + outlined frame offset along the brand's direction
    const off = angular ? [Math.round(36 / Math.tan(crop * D2R)) + 18, 36] : [32, 32];
    add('frames', 'frame-offset', W, H, `<path d="${shape(m + off[0], m + off[1], W - 2 * m - 40, H - 2 * m - 40)}" fill="${T2}"/><path d="${shape(m, m, W - 2 * m - 40, H - 2 * m - 40)}" ${st(P, sw)}/>`, 'Offset frame — ground shifted behind the outline (for images and quotes)');
    // window frame: gable (angular) · arch (round) · organic window · notched (orthogonal)
    const ww = 560, wh = 720, wx = (W - ww) / 2, wy = 40; let win;
    if (angular) { const rise = Math.min(ww / 2 * tan(cut), wh * 0.45); win = U.polyD([[wx, wy + wh], [wx, wy + rise], [wx + ww / 2, wy], [wx + ww, wy + rise], [wx + ww, wy + wh]]); }
    else if (round) win = `M${wx} ${wy + wh}V${wy + ww / 2}A${ww / 2} ${ww / 2} 0 0 1 ${wx + ww} ${wy + ww / 2}V${wy + wh}Z`;
    else if (organic) { const r2 = U.rng(U.hash(b.name + 'win')); const pts = []; for (let i = 0; i < 36; i++) { const a = i / 36 * Math.PI * 2; const sq = Math.pow(Math.abs(Math.cos(a)), 0.6) * Math.sign(Math.cos(a)), sy = Math.pow(Math.abs(Math.sin(a)), 0.6) * Math.sign(Math.sin(a)); pts.push([W / 2 + sq * ww / 2 * (1 + 0.04 * Math.sin(3 * a + r2() * 6)), wy + wh / 2 + sy * wh / 2 * (1 + 0.03 * Math.sin(2 * a))]); } win = U.smoothD(pts, true); }
    else { const n = 48; win = U.polyD([[wx, wy], [wx + ww - n, wy], [wx + ww - n, wy + n], [wx + ww, wy + n], [wx + ww, wy + wh], [wx, wy + wh]]); }
    add('frames', 'frame-window', W, H, `<path d="${win}" fill="${T1}"/><path d="${win}" ${st(Fd, sw)}/>`, 'Window frame — image window in the brand shape (gable / arch / organic / notched)');
  })();

  /* ------------------------------------------------------------ CORNERS */
  (function corners() {
    const S = 600; let a = '', bdy = '', c3 = '';
    if (angular) { const h = Math.min(S, S * 0.62 * tan(cut)), w0 = h / tan(cut);
      a = `<path d="${U.polyD([[0, 0], [S * 0.62, 0], [0, h]])}" fill="${P}"/><path d="${U.polyD([[S * 0.62 + 26, 0], [S * 0.62 + 44, 0], [0, h + 44 * tan(cut)], [0, h + 26 * tan(cut)]])}" fill="${Fd}"/>`;
      for (let i = 0; i < 5; i++) { const d = 60 + i * 46; bdy += `<path d="${U.polyD([[d, 0], [0, d * tan(cut) * 0.58]], true)}" ${st(i === 2 ? P : Fd, 10, { cap: 'butt' })}/>`; }
      bdy += `<path d="${U.polyD([[0, 0], [40, 0], [0, 40 * tan(cut)]])}" fill="${A}"/>`;
    } else if (round) { a = `<path d="M0 0H${S * 0.58}A${S * 0.58} ${S * 0.58} 0 0 1 0 ${S * 0.58}Z" fill="${P}"/>` + [0.72, 0.84].map((k, i) => `<path d="M${S * k} 0A${S * k} ${S * k} 0 0 1 0 ${S * k}" ${st(i ? LN : Fd, 8)}/>`).join('');
      for (let i = 1; i <= 5; i++) bdy += `<path d="M${i * 70} 0A${i * 70} ${i * 70} 0 0 1 0 ${i * 70}" ${st(i === 3 ? P : i % 2 ? Fd : T3, 12)}/>`;
      bdy += `<circle cx="${f(210 * Math.cos(0.8))}" cy="${f(210 * Math.sin(0.8))}" r="18" fill="${A}"/>`;
    } else if (organic) { const r2 = U.rng(U.hash(b.name + 'corner')); const pts = U.blobPts(r2, 60, 40, S * 0.5, { amp: 0.14, n: 36, sx: 1.1 }); a = `<path d="${U.smoothD(pts, true)}" fill="${P}"/>`;
      const p2 = U.blobPts(r2, 0, 0, S * 0.66, { amp: 0.1, n: 36 }); a = `<path d="${U.smoothD(p2, true)}" fill="${T2}"/>` + a;
      for (let i = 0; i < 6; i++) { const pts3 = []; for (let t = 0; t <= 24; t++) { const ang = t / 24 * Math.PI / 2, R = 90 + i * 52 + Math.sin(t / 24 * Math.PI * 3 + i) * 10; pts3.push([Math.cos(ang) * R, Math.sin(ang) * R]); } bdy += `<path d="${U.smoothD(pts3, false)}" ${st(i === 2 ? P : Fd, 9)}/>`; }
    } else { a = `<path d="M0 0H${S * 0.6}V${S * 0.2}H${S * 0.4}V${S * 0.4}H${S * 0.2}V${S * 0.6}H0Z" fill="${P}"/>`; for (let i = 0; i < 4; i++) for (let j = 0; j < 4 - i; j++) bdy += `<rect x="${i * 80}" y="${j * 80}" width="64" height="64" fill="${(i + j) % 3 === 0 ? P : (i + j) % 3 === 1 ? Fd : T3}"/>`; }
    add('corners', 'corner-shape', S, S, a, 'Corner shape — place at a page corner (rotate for other corners)');
    add('corners', 'corner-stack', S, S, bdy, 'Corner stack — rhythm of brand motifs anchored in a corner');
    const ms = 120, mx = 70 + ms / 2, my = 70 + ms / 2; c3 = `<path d="M70 ${70 + ms + 40}V${S - 30}M${70 + ms + 40} 70H${S - 30}" ${st(LN, 3)}/>` + gfx.unitAt(mx, my, ms, 0, 'colour', 'paper');
    add('corners', 'corner-mark', S, S, c3, 'Corner signature — the mark at the corner with hairline rules (keep clear space)');
  })();

  /* ------------------------------------------------------------ BANDS */
  (function bands() {
    const W = 1600, H = 360, names = { angular: ['band-diagonal', 'band-chevron', 'band-shard'], round: ['band-arc', 'band-orbit', 'band-dots'], organic: ['band-wave', 'band-flow', 'band-ripple'], orthogonal: ['band-stripe', 'band-steps', 'band-blocks'], mixed: ['band-stripe', 'band-dots', 'band-wave'] }[style];
    names.forEach((n, ni) => { let body = '';
      if (n === 'band-diagonal') { const dx = H / tan(crop); body = `<path d="${U.polyD([[0, 60], [W, 0], [W, H - 60], [0, H]])}" fill="${T2}"/>`; for (let x = 200; x < W; x += 260) body += `<path d="${U.polyD([[x, 0], [x + 46, 0], [x + 46 + dx, H], [x + dx, H]])}" fill="${x === 720 ? P : T3}"/>`; body += `<path d="${U.polyD([[0, 60], [W, 0]], true)}" ${st(Fd, 4, { cap: 'butt' })}/>`; }
      else if (n === 'band-chevron') { const rise = 70, w = 2 * rise / tan(cut); for (let k = 0; k < 3; k++) { const pts = []; for (let x = -w; x <= W + w; x += w) { pts.push([x, 110 + k * 54]); pts.push([x + w / 2, 110 + k * 54 + rise]); } body += `<path d="${U.polyD(pts, true)}" ${st(k === 1 ? P : Fd, 16, { cap: 'butt', join: 'miter' })}/>`; } }
      else if (n === 'band-shard') { body = `<rect y="120" width="${W}" height="120" fill="${T2}"/>`; const r = U.rng(U.hash(b.name + 'bs')); for (let i = 0; i < 26; i++) { const x = i * 64 + r() * 30, a1 = C.pickAngle(r), a2 = a1 + 40, L = 50 + r() * 70; const tri = [[x, 180], [x + L * Math.cos(a1 * D2R), 180 + L * Math.sin(a1 * D2R)], [x + L * 0.7 * Math.cos(a2 * D2R), 180 + L * 0.7 * Math.sin(a2 * D2R)]]; body += `<path d="${U.polyD(tri)}" fill="${i === 9 ? P : i % 3 ? T3 : Fd}"/>`; } }
      else if (n === 'band-arc') { const R = 1400; body = `<path d="M0 ${H}A${R} ${R} 0 0 1 ${W} ${H}V${H}Z" fill="${T2}" transform="translate(0 -40)"/><path d="M0 ${H - 40}A${R} ${R} 0 0 1 ${W} ${H - 40}" ${st(P, 14)}/><path d="M0 ${H + 20}A${R} ${R} 0 0 1 ${W} ${H + 20}" ${st(Fd, 4)}/>`; }
      else if (n === 'band-orbit') { body = `<path d="M0 ${H / 2}H${W}" ${st(Fd, 3)}/>`; for (let i = 0; i < 9; i++) { const x = 90 + i * 180, R = [26, 40, 60][i % 3]; body += `<circle cx="${x}" cy="${H / 2}" r="${R}" ${st(i === 4 ? P : Fd, 4)}/><circle cx="${x}" cy="${H / 2}" r="${R * 0.35}" fill="${i === 4 ? P : T3}"/>`; if (i % 3 === 1) body += `<circle cx="${f(x + R * Math.cos(-1))}" cy="${f(H / 2 + R * Math.sin(-1))}" r="9" fill="${A}"/>`; } }
      else if (n === 'band-dots') { for (let i = 0; i < 40; i++) for (let j = 0; j < 5; j++) { const t = i / 39, r = 4 + 20 * Math.sin(t * Math.PI) * (1 - Math.abs(j - 2) / 3); body += `<circle cx="${20 + i * 40}" cy="${100 + j * 40}" r="${f(Math.max(2, r * 0.6))}" fill="${i === 20 && j === 2 ? P : T3}"/>`; } }
      else if (n === 'band-wave') { const top = [], bot = []; for (let x = 0; x <= W; x += 20) { top.push([x, 120 + Math.sin(x / W * Math.PI * 3) * 50]); bot.push([x, 250 + Math.sin(x / W * Math.PI * 3 + 0.8) * 40]); } body = `<path d="${U.smoothD(top, false)}L${W} ${H}L0 ${H}Z" fill="${T1}"/><path d="${U.smoothD(top, false)}L${U.smoothD(bot.slice().reverse(), false).slice(1)}Z" fill="${T2}"/><path d="${U.smoothD(top, false)}" ${st(P, 6)}/><path d="${U.smoothD(bot, false)}" ${st(Fd, 3)}/>`; }
      else if (n === 'band-flow') { for (let k = 0; k < 9; k++) { const pts = []; for (let x = -20; x <= W + 20; x += 40) pts.push([x, 70 + k * 26 + Math.sin(x / W * Math.PI * 2 + k * 0.35) * 60]); body += `<path d="${U.smoothD(pts, false)}" ${st(k === 4 ? P : k % 2 ? T3 : Fd, k === 4 ? 6 : 2.5)}/>`; } }
      else if (n === 'band-ripple') { for (let k = 1; k <= 7; k++) { body += `<ellipse cx="${W * 0.62}" cy="${H / 2}" rx="${k * 110}" ry="${k * 26}" ${st(k === 2 ? P : k % 2 ? Fd : T3, k === 2 ? 6 : 2.5)}/>`; } }
      else if (n === 'band-stripe') { let x = 0, i = 0; const ws = [40, 12, 80, 12, 24, 160, 12, 40]; while (x < W) { const w = ws[i % ws.length]; if (i % 2 === 0) body += `<rect x="${x}" y="80" width="${w}" height="200" fill="${i === 4 ? P : i % 4 === 0 ? T3 : Fd}"/>`; x += w; i++; } }
      else if (n === 'band-steps') { let pts = [[0, H]]; for (let i = 0; i < 8; i++) { pts.push([i * 200, H - 40 - i * 34]); pts.push([(i + 1) * 200, H - 40 - i * 34]); } pts.push([W, H]); body = `<path d="${U.polyD(pts)}" fill="${T2}"/><path d="${U.polyD(pts.slice(1, -1), true)}" ${st(P, 6, { cap: 'square', join: 'miter' })}/>`; }
      else if (n === 'band-blocks') { for (let i = 0; i < 16; i++) body += `<rect x="${i * 100}" y="${100 + (i % 3) * 30}" width="92" height="${120 - (i % 3) * 30}" fill="${i === 6 ? P : i % 2 ? T3 : T2}"/>`; }
      add('bands', n, W, H, body, n.replace('band-', 'Band · ') + ' — full-bleed band for section breaks and headers');
    });
  })();

  /* ------------------------------------------------------------ DIVIDERS */
  (function dividers() {
    const W = 1200, H = 80, y = H / 2; let d1, d2, d3, d4;
    if (angular) { const c = 10 / tan(cut) * 2.2; d1 = `<path d="${U.polyD([[40, y - 5], [W - 40 - c, y - 5], [W - 40, y + 5], [40 + c, y + 5]])}" fill="${Fd}"/>`; const rise = 18, w = 2 * rise / tan(cut); d2 = Array.from({ length: 14 }, (_, i) => `<path d="${U.polyD([[300 + i * 44, y + rise / 2], [300 + i * 44 + w / 2, y - rise / 2], [300 + i * 44 + w, y + rise / 2]], true)}" ${st(i === 6 ? P : Fd, 5, { cap: 'butt', join: 'miter' })}/>`).join(''); }
    else if (round) { d1 = `<path d="M60 ${y}H${W - 60}" ${st(Fd, 4, { cap: 'round' })}/><circle cx="40" cy="${y}" r="9" fill="${P}"/><circle cx="${W - 40}" cy="${y}" r="9" fill="${P}"/>`; d2 = Array.from({ length: 21 }, (_, i) => `<circle cx="${200 + i * 40}" cy="${y}" r="${i === 10 ? 11 : 5}" fill="${i === 10 ? P : i % 5 === 0 ? Fd : T3}"/>`).join(''); }
    else if (organic) { const pts = [], pts2 = []; for (let x = 40; x <= W - 40; x += 10) { const t = (x - 40) / (W - 80), wd = 1 + 5 * Math.sin(t * Math.PI); pts.push([x, y - wd + Math.sin(t * Math.PI * 4) * 6]); pts2.push([x, y + wd + Math.sin(t * Math.PI * 4) * 6]); } d1 = `<path d="${U.smoothD(pts, false)}L${U.smoothD(pts2.reverse(), false).slice(1)}Z" fill="${Fd}"/>`; const w2 = []; for (let x = 200; x <= W - 200; x += 8) w2.push([x, y + Math.sin((x - 200) / 80 * Math.PI) * 12]); d2 = `<path d="${U.smoothD(w2, false)}" ${st(P, 5)}/>`; }
    else { d1 = `<path d="M40 ${y}H${W - 40}" ${st(Fd, 4, { cap: 'butt' })}/><path d="M40 ${y - 14}v28M${W - 40} ${y - 14}v28" ${st(Fd, 4, { cap: 'butt' })}/>`; d2 = Array.from({ length: 30 }, (_, i) => `<rect x="${150 + i * 30}" y="${y - 6}" width="${i % 5 === 0 ? 20 : 12}" height="12" fill="${i === 15 ? P : Fd}"/>`).join(''); }
    const ms = 56; d3 = `<path d="M40 ${y}H${W / 2 - ms}M${W / 2 + ms} ${y}H${W - 40}" ${st(LN, 3, { cap: 'butt' })}/>` + gfx.unitAt(W / 2, y, ms, 0, 'colour', 'paper');
    const dash = angular ? '28 10' : round ? '0.1 16' : organic ? '40 14 6 14' : '16 8';
    d4 = `<path d="M40 ${y}H${W - 40}" ${st(Fd, round ? 7 : 4, { cap: round ? 'round' : cap })} stroke-dasharray="${dash}"/>`;
    add('dividers', 'divider-rule', W, H, d1, 'Divider rule — line with brand end treatment');
    add('dividers', 'divider-motif', W, H, d2, 'Divider motif — repeating brand motif with one accent');
    add('dividers', 'divider-mark', W, H, d3, 'Divider with the mark — hairline rules and the mark at the centre');
    add('dividers', 'divider-dash', W, H, d4, 'Dash divider — rhythm in the brand cap style');
  })();

  /* ------------------------------------------------------------ BADGES */
  (function badges() {
    const S = 600, c = S / 2, lab = (b.labels.posts || b.labels.events || 'News'), onP = cw.primary.ink;
    add('badges', 'badge-shape', S, S, `<path d="${badge(c, c, 240)}" fill="${P}"/>`, 'Badge shape — empty brand badge');
    let t = '', fs1 = fitText('label', lab, 300, 64, labelO(onP));
    t = text('label', lab, c, c + fs1 * 0.35, fs1, labelO(onP, { anchor: 'middle' })).svg;
    add('badges', 'badge-label', S, S, `<path d="${badge(c, c, 200, { seed: 2 })}" fill="${P}"/>${t}`, 'Badge with label (text outlined from the brand label font)');
    // seal: circular text with the mark at the centre
    const ring = `${b.name} · ${(b.brand.descriptor || (b.content.brand || {}).tagline || '')}`.replace(/ · $/, '');
    let seal = '';
    if (angular) seal += `<path d="${chamfer(30, 30, 540, 540, 160, 'tl,tr,br,bl')}" fill="${Fd}"/>`;
    else if (organic) { const r2 = U.rng(U.hash(b.name + 'seal')); const pts = []; for (let i = 0; i < 120; i++) { const a = i / 120 * Math.PI * 2; pts.push([c + Math.cos(a) * (268 + 8 * Math.sin(a * 14)), c + Math.sin(a) * (268 + 8 * Math.sin(a * 14))]); } seal += `<path d="${U.smoothD(pts, true)}" fill="${Fd}"/>`; }
    else if (round) seal += `<circle cx="${c}" cy="${c}" r="270" fill="${Fd}"/>`;
    else seal += `<rect x="30" y="30" width="540" height="540" fill="${Fd}"/>`;
    seal += `<circle cx="${c}" cy="${c}" r="150" fill="none" stroke="${cw.foundation.line}" stroke-width="2"/>`;
    const sealTxt = ring.length > 46 ? b.name : ring, tsz = Math.min(36, (2 * Math.PI * 196 * 0.46) / Math.max(8, sealTxt.length * 0.66));
    seal += textOnCircle('label', sealTxt, c, c, 196, tsz, { upper: true, tracking: 0.16, fill: cw.foundation.ink });
    seal += textOnCircle('label', (b.content.contact || {}).website || b.labels.cta_primary || '', c, c, 196, Math.min(26, tsz * 0.8), { upper: true, tracking: 0.16, fill: cw.foundation.accent, bottom: true });
    seal += gfx.unitAt(c, c, 150, 0, 'colour', 'foundation');
    add('badges', 'badge-seal', S, S, seal, 'Seal — circular brand line with the mark (outlined text)', { dark: true });
    // sticker: stat from content
    const stt = ((b.content.stats || [])[0]) || { value: String(new Date().getFullYear()), label: '' };
    let stk = '';
    if (angular) { const pts = []; const n = 14; for (let i = 0; i < n * 2; i++) { const a = i / (n * 2) * Math.PI * 2 - Math.PI / 2, R = i % 2 ? 222 : 262; pts.push([c + Math.cos(a) * R, c + Math.sin(a) * R]); } stk = `<path d="${U.polyD(pts)}" fill="${A}"/>`; }
    else if (round) { const pts = []; for (let i = 0; i < 180; i++) { const a = i / 180 * Math.PI * 2, R = 250 + 12 * Math.cos(a * 18); pts.push([c + Math.cos(a) * R, c + Math.sin(a) * R]); } stk = `<path d="${U.polyD(pts)}" fill="${A}"/>`; }
    else if (organic) stk = `<path d="${U.smoothD(U.blobPts(U.rng(U.hash(b.name + 'stk')), c, c, 250, { amp: 0.12, n: 36 }), true)}" fill="${A}"/>`;
    else { stk = `<rect x="50" y="50" width="500" height="500" fill="${A}"/>` + Array.from({ length: 20 }, (_, i) => `<circle cx="${50 + i * 26.3}" cy="50" r="7" fill="${BG}"/><circle cx="${50 + i * 26.3}" cy="550" r="7" fill="${BG}"/>`).join(''); }
    const onA = U.contrast(A, Fd) >= U.contrast(A, '#FFFFFF') ? Fd : '#FFFFFF';
    const vsz = fitText('display', stt.value + (stt.unit || ''), 330, 170, { upper: gm.displayUpper });
    stk += text('display', stt.value + (stt.unit || ''), c, c + vsz * 0.3, vsz, { anchor: 'middle', fill: onA, upper: gm.displayUpper }).svg;
    if (stt.label) { const lsz = fitText('label', stt.label, 320, 26, labelO(onA)); stk += text('label', stt.label, c, c + vsz * 0.3 + 54, lsz, labelO(onA, { anchor: 'middle' })).svg; }
    add('badges', 'sticker-stat', S, S, stk, 'Sticker with a key figure from content.json');
  })();

  /* ------------------------------------------------------------ NUMBERS */
  (function numbers() {
    const S = 400;
    ['01', '02', '03'].forEach((n, i) => { const fillC = i === 0 ? P : i === 1 ? Fd : 'none', ink = i === 0 ? cw.primary.ink : i === 1 ? cw.foundation.ink : Fd;
      const shp = round ? U.circleD(S / 2, S / 2, 180) : organic ? U.smoothD(U.blobPts(U.rng(U.hash(b.name + 'n' + i)), S / 2, S / 2, 176, { amp: 0.1, n: 32, kmax: 3 }), true) : shape(20, 20, S - 40, S - 40, { corners: 'br', c: 70 });
      const sz = fitText('display', n, 230, 210, {});
      const body = `<path d="${shp}" ${fillC === 'none' ? st(Fd, 6) : `fill="${fillC}"`}/>` + text('display', n, S / 2, S / 2 + sz * 0.36, sz, { anchor: 'middle', fill: ink, tracking: gm.displayTracking || 0 }).svg;
      add('numbers', 'number-' + n, S, S, body, `Number block ${n} — display figures in the brand shape`); });
  })();

  /* ------------------------------------------------------------ QUOTES */
  (function quotes() {
    const S = 400, g = G.quote && G.quote.glyphs && G.quote.glyphs['“'] ? 'quote' : 'display';
    // centre a glyph by its real outline box (quote marks sit near cap height, not on the baseline)
    function glyphAt(ch, cx, cy, box, fill) { const gl = G[g] && G[g].glyphs && G[g].glyphs[ch]; if (!gl || !gl.d) return text(g, ch, cx, cy, box, { anchor: 'middle', fill }).svg;
      const pts = [].concat.apply([], U.parsePath(gl.d)), bb = U.bbox(pts), k = box / Math.max(bb[2] - bb[0], bb[3] - bb[1]);
      return `<path fill="${fill}" transform="translate(${f(cx - (bb[0] + bb[2]) / 2 * k)} ${f(cy - (bb[1] + bb[3]) / 2 * k)}) scale(${+k.toFixed(5)})" d="${gl.d}"/>`; }
    add('quotes', 'quote-open', S, S, glyphAt('“', S / 2, S / 2, 260, P), 'Opening quote mark — outlined from the brand quote typeface');
    add('quotes', 'quote-close', S, S, glyphAt('”', S / 2, S / 2, 260, P), 'Closing quote mark');
    const W = 900, H = 520; let qb = `<path d="${shape(0, 40, W - 40, H - 40, { corners: 'br', c: 80 })}" fill="${T1}"/>` + glyphAt('“', 140, 150, 120, P) + `<path d="M80 ${H - 90}H${W - 160}" ${st(LN, 3, { cap: 'butt' })}/>`;
    if (angular) qb += `<path d="${U.polyD([[W - 40, 40], [W, 40], [W - 40, 40 + 40 * tan(cut)]])}" fill="${P}"/>`;
    add('quotes', 'quote-block', W, H, qb, 'Quote block — tinted panel with quote mark (set the quote as live text on top)');
  })();

  /* ------------------------------------------------------------ ARROWS */
  (function arrows() {
    const S = 400, sw = dsw(S) * 1.15, head = angular ? clamp(90 - cut, 25, 45) : 42, hl = 92;
    function arrowHead(x, y, ang) { const a1 = (ang + 180 - head) * D2R, a2 = (ang + 180 + head) * D2R; return `M${f(x + Math.cos(a1) * hl)} ${f(y + Math.sin(a1) * hl)}L${f(x)} ${f(y)}L${f(x + Math.cos(a2) * hl)} ${f(y + Math.sin(a2) * hl)}`; }
    function clamp(v, a, bb) { return Math.max(a, Math.min(bb, v)); }
    const sh = organic ? `M60 ${S / 2 + 10}C150 ${S / 2 - 30} 230 ${S / 2 + 20} 330 ${S / 2}` : `M60 ${S / 2}H330`;
    add('arrows', 'arrow-right', S, S, `<path d="${sh}${arrowHead(332, S / 2, 0)}" ${st(Fd, sw)}/>`, 'Arrow — DNA stroke, caps and head angle');
    const da = angular ? -crop : -45, L = 250, x0 = S / 2 - Math.cos(da * D2R) * L / 2, y0 = S / 2 - Math.sin(da * D2R) * L / 2, x1 = S / 2 + Math.cos(da * D2R) * L / 2, y1 = S / 2 + Math.sin(da * D2R) * L / 2;
    add('arrows', 'arrow-diagonal', S, S, `<path d="M${f(x0)} ${f(y0)}L${f(x1)} ${f(y1)}${arrowHead(x1, y1, da)}" ${st(P, sw)}/>`, 'Diagonal arrow — at the brand crop angle');
    let cv;
    if (angular) { const mx = 200, my = 120; cv = `M70 300L${mx} ${f(300 - (mx - 70) * tan(90 - cut) * 0.0)}L${mx} ${my}L330 ${my}${arrowHead(330, my, 0)}`; cv = `M70 310L70 ${f(310 - 110)}L${f(70 + 110 / tan(cut))} 120H330${arrowHead(330, 120, 0)}`; }
    else if (ortho) cv = `M80 310V120H330${arrowHead(330, 120, 0)}`;
    else { cv = `M90 300A150 150 0 0 1 300 120${arrowHead(300, 120, -18)}`; }
    add('arrows', 'arrow-turn', S, S, `<path d="${cv}" ${st(Fd, sw)}/>`, 'Turning arrow — curve (round/organic) or angled elbow (angular)');
    const bx = `<path d="${round ? U.circleD(S / 2, S / 2, 170) : organic ? U.smoothD(U.blobPts(U.rng(U.hash(b.name + 'ab')), S / 2, S / 2, 166, { amp: 0.08, n: 30, kmax: 3 }), true) : shape(30, 30, S - 60, S - 60, { corners: 'br', c: 60 })}" fill="${P}"/>`;
    const hl0 = hl; add('arrows', 'arrow-button', S, S, bx + `<g transform="translate(${S / 2} ${S / 2}) scale(0.62) translate(${-S / 2} ${-S / 2})"><path d="M70 ${S / 2}H325${arrowHead(330, S / 2, 0)}" ${st(cw.primary.ink, sw * 1.3)}/></g>`, 'Arrow button — arrow in the brand badge shape');
  })();

  /* ------------------------------------------------------------ HIGHLIGHTS */
  (function highlights() {
    let u, c, mk, sp; const r = U.rng(U.hash(b.name + 'hl'));
    if (angular) { const sk = 26 / tan(cut); u = `<path d="${U.polyD([[30 + sk, 44], [780, 30], [770 - sk, 76], [20, 90]])}" fill="${P}"/>`;
      const cc = 40; c = [[60, 60, 1, 1], [740, 60, -1, 1], [60, 340, 1, -1], [740, 340, -1, -1]].map(([x, y, sx, sy]) => `<path d="${U.polyD([[x, y + sy * 90], [x, y + sy * cc * tan(cut) * 0.5], [x + sx * cc, y], [x + sx * 120, y]], true)}" ${st(P, 10, { cap: 'butt', join: 'miter' })}/>`).join('');
      const s2 = 60 / tan(crop) + 30; mk = `<path d="${U.polyD([[20 + s2, 40], [790, 40], [780 - s2, 160], [10, 160]])}" fill="${T2}"/>`;
      sp = [-60, -20, 25].map((a, i) => { const L = [70, 95, 70][i], x = 150, y = 230; const a1 = (a - 90) * D2R; const tip = [x + Math.cos(a1) * (L + 50), y + Math.sin(a1) * (L + 50)], base = [x + Math.cos(a1) * 50, y + Math.sin(a1) * 50], n = [-Math.sin(a1) * 9, Math.cos(a1) * 9]; return `<path d="${U.polyD([[base[0] + n[0], base[1] + n[1]], tip, [base[0] - n[0], base[1] - n[1]]])}" fill="${i === 1 ? P : Fd}"/>`; }).join('');
    } else if (round) { u = `<rect x="20" y="40" width="760" height="40" rx="20" fill="${P}"/>`;
      c = `<ellipse cx="400" cy="200" rx="360" ry="150" ${st(P, 10)}/>`;
      mk = `<rect x="10" y="40" width="780" height="120" rx="60" fill="${T2}"/>`;
      sp = [-50, 0, 50].map((a, i) => { const a1 = (a - 90) * D2R; return `<path d="M${f(150 + Math.cos(a1) * 60)} ${f(230 + Math.sin(a1) * 60)}L${f(150 + Math.cos(a1) * 120)} ${f(230 + Math.sin(a1) * 120)}" ${st(i === 1 ? P : Fd, 18, { cap: 'round' })}/>`; }).join('') + `<circle cx="150" cy="230" r="14" fill="${A}"/>`;
    } else if (organic) { const top = [], bot = []; for (let x = 20; x <= 780; x += 20) { const t = (x - 20) / 760, w = 16 + 10 * Math.sin(t * Math.PI) + (r() - 0.5) * 4; top.push([x, 60 - w + Math.sin(t * 5) * 6]); bot.push([x, 60 + w * 0.8 + Math.sin(t * 5) * 6]); } u = `<path d="${U.smoothD(top, false)}L${U.smoothD(bot.reverse(), false).slice(1)}Z" fill="${P}"/>`;
      const lp = []; for (let i = 0; i <= 80; i++) { const a = -0.3 + i / 80 * (Math.PI * 2 + 0.7), R = 1 + 0.04 * Math.sin(a * 3); lp.push([400 + Math.cos(a) * 360 * R, 200 + Math.sin(a) * 140 * R + i * 0.5]); } c = `<path d="${U.smoothD(lp, false)}" ${st(P, 9)}/>`;
      const mt = [], mb = []; for (let x = 10; x <= 790; x += 26) { mt.push([x, 44 + (r() - 0.5) * 14]); mb.push([x, 156 + (r() - 0.5) * 14]); } mk = `<path d="${U.smoothD(mt, false)}L${U.smoothD(mb.reverse(), false).slice(1)}Z" fill="${T2}"/>`;
      sp = [-50, -5, 40].map((a, i) => { const a1 = (a - 90) * D2R, p0 = [150 + Math.cos(a1) * 60, 230 + Math.sin(a1) * 60], p1 = [150 + Math.cos(a1 + 0.2) * 95, 230 + Math.sin(a1 + 0.2) * 95], p2 = [150 + Math.cos(a1) * 130, 230 + Math.sin(a1) * 130]; return `<path d="${U.smoothD([p0, p1, p2], false)}" ${st(i === 1 ? P : Fd, 14)}/>`; }).join('');
    } else { u = `<rect x="20" y="40" width="760" height="40" fill="${P}"/>`; c = `<rect x="40" y="50" width="720" height="300" ${st(P, 10, { cap: 'square', join: 'miter' })}/>`; mk = `<rect x="10" y="40" width="780" height="120" fill="${T2}"/>`; sp = [0, 1, 2].map(i => `<rect x="${110 + i * 34}" y="${130 - i * 30}" width="18" height="${60 + i * 30}" fill="${i === 1 ? P : Fd}"/>`).join(''); }
    add('highlights', 'highlight-underline', 800, 120, u, 'Underline highlight — sits under a key word');
    add('highlights', 'highlight-circle', 800, 400, c, 'Circle / bracket highlight — frames a word or figure');
    add('highlights', 'highlight-marker', 800, 200, mk, 'Marker highlight — tint block behind text (keep text contrast)');
    add('highlights', 'highlight-spark', 300, 300, sp, 'Attention spark — three strokes that point at something');
  })();

  /* ------------------------------------------------------------ SHAPES (dna.motifs) */
  (function shapes() {
    const map = { shard: ['shard-01', 'shard-02', 'shard-cluster'], chevron: ['chevron'], 'diagonal-band': ['diagonal-band'], 'facet-field': ['facet-cluster'], crystal: ['crystal'], ring: ['ring'], dot: ['dot-cluster'], arc: ['arc'], orbit: ['orbit-ring'], halo: ['halo'], wave: ['wave'], blob: ['blob-01', 'blob-02', 'blob-03'], 'flow-line': ['flow-line'], ripple: ['ripple'] };
    const base = { 'shard-01': 'shard', 'shard-02': 'shard', 'blob-01': 'blob', 'blob-02': 'blob', 'blob-03': 'blob' };
    let names = []; (dna.motifs || []).forEach(m => (map[m] || []).forEach(n => { if (!names.includes(n)) names.push(n); }));
    if (names.length < 4) ({ angular: ['shard-01', 'chevron', 'diagonal-band'], round: ['ring', 'dot-cluster', 'orbit-ring'], organic: ['blob-01', 'wave', 'ripple'], orthogonal: ['dot-cluster', 'diagonal-band'], mixed: ['ring', 'shard-01', 'wave'] }[style] || []).forEach(n => { if (!names.includes(n)) names.push(n); });
    names.forEach((n, i) => { const m = gfx.motif(base[n] || n, { seed: i, size: 400, cw: 'paper', color: i % 3 === 1 ? Fd : P, color2: i % 3 === 1 ? P : Fd });
      add('shapes', n, 400, 400, m.body, 'Motif shape — ' + n.replace(/-0\d$/, '') + ' (from the design DNA motifs)'); });
  })();

  /* ------------------------------------------------------------ MARK devices */
  (function markDevices() {
    const pc2 = cw.paper;
    const crop = gfx.pattern('mark-crop', 'paper'); add('mark', 'mark-crop', crop.w, crop.h, `<rect width="${crop.w}" height="${crop.h}" fill="${pc2.bg}"/>${crop.body}`, 'Mark crop — giant tonal mark as a supergraphic (the small mark keeps its clear space)');
    const S = 800, which = gfx.mark.kind === 'wordmark' ? 'unit' : 'mark', kind = which === 'unit' ? gfx.unit.kind : gfx.mark.kind; let ec;
    if (kind === 'emblem') ec = gfx.unitAt(S / 2 + 18, S / 2 + 18, S * 0.8, 0, 'tonal', 'paper', 'mark') + gfx.silAt(S / 2, S / 2, S * 0.8, 0, U.stroke(P, 6, { cap, join }), 'mark') + gfx.silAt(S / 2, S / 2, S * 0.8, 0, U.stroke(Fd, 3, { cap, join }), 'mark', 0.82);
    else if (kind === 'monogram' || kind === 'wordmark') ec = gfx.unitAt(S / 2 + 26, S / 2 + 26, S * 0.7, 0, 'tonal', 'paper', which) + gfx.silAt(S / 2, S / 2, S * 0.7, 0, U.stroke(P, 5, { cap, join }), which);
    else ec = [1, 0.74, 0.48, 0.22].map((k, i) => gfx.silAt(S / 2, S / 2, S * 0.72, 0, U.stroke(i === 0 ? P : Fd, (i === 0 ? 6 : 3), { cap, join }), which, k, true)).join('');
    add('mark', 'mark-echo', S, S, ec, kind === 'symbol' ? 'Mark echo — concentric outlines of the mark silhouette' : 'Mark offset — outline over a tonal shadow of the mark');
    const W = 1600, H = 320; let strip = `<rect width="${W}" height="${H}" fill="${pc2.t1}"/>`; const n = 9;
    for (let i = 0; i < n; i++) strip += gfx.unitAt(W / n * (i + 0.5), H / 2, 150, 0, i === 4 ? 'colour' : 'tonal', 'paper');
    add('mark', 'mark-strip', W, H, strip, 'Mark strip — repeated mark band, tonal with one full-colour mark');
    if (gfx.mark.kind === 'symbol' && gfx.mark.parts.length >= 3) {
      const M = gfx.mark, oc = M.oc, k = 700 / M.size; let ex = '';
      M.parts.forEach((p, i) => { let cx = 0, cy = 0, nn = 0; p.polys.forEach(q => q.forEach(pt => { cx += pt[0]; cy += pt[1]; nn++; })); cx /= nn; cy /= nn; const dx = (cx - oc[0]) * 0.22, dy = (cy - oc[1]) * 0.22;
        ex += `<path fill-rule="evenodd" d="${p.d}" transform="translate(${f(dx + (p.tx || 0))} ${f(dy + (p.ty || 0))})" fill="${p.c}"/>`; });
      add('mark', 'mark-exploded', 900, 900, `<g transform="translate(450 450) scale(${(k * 0.92).toFixed(4)}) translate(${f(-oc[0])} ${f(-oc[1])})">${ex}</g>`, 'Exploded mark — the mark pieces pulled apart from the optical centre (construction / hero use)');
    }
  })();

  /* ------------------------------------------------------------ BACKGROUNDS */
  (function backgrounds() {
    const pats = gfx.catalogue.filter(p => p.tile && p.key.indexOf('mark') !== 0).map(p => p.key);
    const formats = [['hero', 1920, 1080], ['square', 1080, 1080], ['story', 1080, 1920]];
    formats.forEach(([fm, W, H], fi) => Object.keys(cw).forEach((k, ci) => {
      const comp = gfx.composition(k, W, H, { seed: fi * 3 + ci + 1, pattern: pats[(fi + ci) % Math.max(1, pats.length)] });
      add('backgrounds', `${fm}-${k}`, W, H, comp.body, `${fm[0].toUpperCase() + fm.slice(1)} background (${W}×${H}) on ${k} — ${comp.mode}; calm zone for text`, { safe: comp.safe, pattern: comp.pattern, cwKey: k });
    }));
  })();

  // write
  out.forEach(g => {
    const file = path.join(root, g.family, g.name + '.svg'); F.write(file, g.svg);
    const big = g.w * g.h > 1.5e6, sc = big ? 0.5 : g.w <= 400 ? 1.5 : 1;
    ctx.rasters.push({ svg: g.svg, out: path.join(root, g.family, g.name + '.png'), scale: sc, palette: g.family !== 'backgrounds' && !/halo/.test(g.name) });
    g.file = `GRAPHICS/${g.family}/${g.name}.svg`; g.png = `GRAPHICS/${g.family}/${g.name}.png`; delete g.svg;
  });
  ctx.graphics = out; ctx.counts.graphics = out.length;
}
module.exports = { run };
