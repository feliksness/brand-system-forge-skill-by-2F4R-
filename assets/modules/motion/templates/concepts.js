  /* ============================================================ concepts (pure functions of t)
     Each: { id, title, loop?, total(S), phases(S) → [{label, from, to, ease}], render(S, t) }.
     Pages choose concepts by logo type & complexity (see MOTION/README.md). */
  function resetMarkGroups(S) { S.groups.forEach(function (g) { if (g.role === 'mark') S.setGroup(g, {}); }); }
  function lettersDur(S) { var n = S.role('lettering').length; return Math.min(D('logo') * 0.62, D('slower') + n * STAGGER * 0.55); }
  function overlap() { return D('slow') * 0.7; }
  function sig(S) { return LM.signatureVerb(S); }
  function withLetters(S, m) { return LM.hasLettering(S) && S.role('mark').length ? m + lettersDur(S) - overlap() : m; }
  function letterPhase(S, m) { return { label: 'Lettering — ' + (CH === 'snap' ? 'wipe along the ' + CFG.angle + '° cut' : CH === 'slide' ? 'glyphs rise from the baseline' : CH === 'glide' ? 'glyphs scale from the centre out' : 'glyphs drift in, soft spring'), from: m - overlap(), to: m - overlap() + lettersDur(S), ease: CH === 'flow' ? 'emphasis' : 'enter' }; }
  function markOrderName(how) { return { lum: 'dark → light (luminance)', 'lum-desc': 'light → dark', axis: 'along the ' + CFG.angle + '° front', radial: 'centre → out', x: 'left → right', up: 'bottom → top', area: 'largest first', doc: 'paint order', angle: 'around the centre' }[how] || how; }
  LM.markOrderName = markOrderName; LM.primaryOrder = primaryOrder;

  /** intro — the mark's signature entrance (UI logoIntro, stings, outro). */
  LM.register({ id: 'intro', title: 'Mark intro',
    total: function (S) { return S.role('mark').length ? LM.phaseLen(S) : D('logo') * 0.7; },
    phases: function (S) { return [{ label: 'Mark — ' + sig(S), from: 0, to: this.total(S), ease: 'enter' }]; },
    render: function (S, t) { resetMarkGroups(S); if (S.role('mark').length) LM.markPhase(S, t, 0, LM.phaseLen(S), sig(S)); else LM.letters(S, t, 0, D('logo') * 0.7, {}); } });

  /** assemble — units arrive from an exploded state (faceted marks: by luminance), then the lettering. */
  LM.register({ id: 'assemble', title: 'Parts assemble',
    how: function (S) { return (CFG.complexity === 'faceted' || S.markUnits().length > 10) ? (CH === 'glide' ? 'radial' : CH === 'slide' ? 'up' : 'lum') : (CH === 'glide' ? 'area' : 'axis'); },
    total: function (S) { return withLetters(S, LM.phaseLen(S) * 1.05); },
    phases: function (S) { var m = LM.phaseLen(S) * 1.05, ph = [{ label: 'Parts converge — ' + markOrderName(this.how(S)), from: 0, to: m, ease: CH === 'flow' ? 'emphasis' : 'enter' }]; if (LM.hasLettering(S) && S.role('mark').length) ph.push(letterPhase(S, m)); return ph; },
    render: function (S, t) {
      resetMarkGroups(S); var m = LM.phaseLen(S) * 1.05;
      var units = order(S.markUnits(), this.how(S), S), tm = timing(units.length, m, D('slower'));
      units.forEach(function (u) { V.assemble(S, u, t, u.rank * tm.spread, tm.each, { spread: units.length > 10 ? 1 : 1.4 }); });
      if (LM.hasLettering(S) && S.role('mark').length) LM.letters(S, t, m - overlap(), lettersDur(S), {});
    } });

  /** sweep — a front crosses the mark; every unit pops as the front reaches it (faceted marks). */
  LM.register({ id: 'sweep', title: 'Light sweep',
    how: function () { return CH === 'glide' ? 'radial' : CH === 'slide' ? 'up' : CH === 'snap' ? 'axis' : 'x'; },
    total: function (S) { return withLetters(S, LM.phaseLen(S)); },
    phases: function (S) { var m = LM.phaseLen(S), ph = [{ label: 'Front travels ' + markOrderName(this.how(S)) + '; units pop on contact', from: 0, to: m, ease: 'linear + ' + (CH === 'snap' || CH === 'slide' ? 'enter' : 'emphasis') }]; if (LM.hasLettering(S) && S.role('mark').length) ph.push(letterPhase(S, m)); return ph; },
    render: function (S, t) {
      resetMarkGroups(S); var m = LM.phaseLen(S), each = Math.min(D('slower'), m * 0.4), span = m - each;
      var units = order(S.markUnits(), this.how(S), S), b = S.markBox();
      units.forEach(function (u) { V.pop(S, u, t, u.rankV * span, each); });
      // the front itself: a hairline in the accent colour, visible only while travelling
      if (!S.extras.front) {
        var node = mk('path', { fill: 'none', 'stroke-linecap': CFG.cap === 'square' ? 'square' : 'round' });
        node.setAttribute('style', 'stroke: var(--color-accent, currentColor)');
        S.addExtra({ id: 'front', node: node, at: 'over', final: 'hide' });
      }
      var fp = clamp01(t / span), path = S.extras.front.el.firstChild, W = Math.max(b.w, b.h), d = '', cx = b.x + b.w / 2, cy = b.y + b.h / 2;
      path.setAttribute('stroke-width', (W * 0.006).toFixed(2));
      if (CH === 'glide') { var R = Math.hypot(b.w, b.h) / 2 * fp; d = 'M' + (cx + R) + ' ' + cy + ' A' + R + ' ' + R + ' 0 1 0 ' + (cx - R) + ' ' + cy + ' A' + R + ' ' + R + ' 0 1 0 ' + (cx + R) + ' ' + cy; }
      else if (CH === 'slide') { var y = b.y + b.h - b.h * fp; d = 'M' + (b.x - W * 0.06) + ' ' + y + ' H' + (b.x + b.w + W * 0.06); }
      else if (CH === 'snap') { var q = angledClip(b, fp); d = 'M' + q[0][0] + ' ' + q[0][1] + ' L' + q[1][0] + ' ' + q[1][1]; S.setExtra('front', { clip: [[b.x - W * 0.04, b.y - W * 0.04], [b.x + b.w + W * 0.04, b.y - W * 0.04], [b.x + b.w + W * 0.04, b.y + b.h + W * 0.04], [b.x - W * 0.04, b.y + b.h + W * 0.04]], o: Math.min(1, fp * 12, (1 - fp) * 10) }); }
      path.setAttribute('d', d || 'M0 0');
      if (CH !== 'snap') S.setExtra('front', { o: CH === 'flow' ? 0 : Math.min(1, fp * 12, (1 - fp) * 10) });
      if (LM.hasLettering(S) && S.role('mark').length) LM.letters(S, t, m - overlap(), lettersDur(S), {});
    } });

  /** build — the mark's parts are revealed one after another, then the lettering. */
  LM.register({ id: 'build', title: 'Build in sequence',
    total: function (S) { return withLetters(S, LM.phaseLen(S)); },
    phases: function (S) { var m = LM.phaseLen(S), ph = [{ label: 'Parts build — ' + markOrderName(primaryOrder(S)) + ' (' + (CH === 'snap' ? 'angled wipes' : CH === 'slide' ? 'rise on the grid' : CH === 'glide' ? 'sweeps and scale from centre' : 'soft drift') + ')', from: 0, to: m, ease: CH === 'flow' || CH === 'glide' ? 'emphasis' : 'enter' }]; if (LM.hasLettering(S) && S.role('mark').length) ph.push(letterPhase(S, m)); return ph; },
    render: function (S, t) { resetMarkGroups(S); var m = LM.phaseLen(S); LM.markPhase(S, t, 0, m, 'build'); if (LM.hasLettering(S) && S.role('mark').length) LM.letters(S, t, m - overlap(), lettersDur(S), {}); } });

  /** signature / lockup — symbol first (signature verb), then the lettering. */
  function signatureRender(S, t) { resetMarkGroups(S); var m = LM.phaseLen(S); LM.markPhase(S, t, 0, m, sig(S)); if (LM.hasLettering(S)) LM.letters(S, t, m - overlap(), lettersDur(S), {}); }
  function signaturePhases(S) { var m = LM.phaseLen(S); return [{ label: 'Symbol — ' + sig(S) + ', ' + markOrderName(primaryOrder(S)), from: 0, to: m, ease: CH === 'flow' ? 'emphasis' : 'enter' }, letterPhase(S, m)]; }
  LM.register({ id: 'signature', title: 'Symbol, then lettering', total: function (S) { return withLetters(S, LM.phaseLen(S)); }, phases: signaturePhases, render: signatureRender });
  LM.register({ id: 'lockup', title: 'Symbol, then name', total: function (S) { return withLetters(S, LM.phaseLen(S)); }, phases: signaturePhases, render: signatureRender });

  /** contour — outlines draw on, fills flood in by luminance, outlines dissolve. */
  LM.register({ id: 'contour', title: 'Contour draw',
    total: function (S) { return Math.round(D('logo') * (LM.hasLettering(S) ? 1.3 : 1.05)); },
    phases: function (S) { var T = this.total(S); return [{ label: 'Outlines draw (' + CFG.cap + ' caps, ' + CFG.join + ' joins)', from: 0, to: T * 0.58, ease: 'standard' }, { label: 'Fills flood in, dark → light', from: T * 0.4, to: T * 0.88, ease: 'enter' }, { label: 'Outlines dissolve', from: T * 0.78, to: T, ease: 'exit' }]; },
    render: function (S, t) {
      resetMarkGroups(S); S.groups.forEach(function (g) { S.setGroup(g, {}); });
      var T = this.total(S), units = order(S.units, CH === 'glide' ? 'radial' : CH === 'slide' ? 'x' : CH === 'snap' ? 'axis' : 'x', S);
      var byLum = order(S.units, 'lum', S).map(function (u) { return u.rank; }), lumRank = {};
      order(S.units, 'lum', S).forEach(function (u, i) { lumRank[S.units.indexOf(u)] = units.length > 1 ? i / (units.length - 1) : 0; });
      var ink = S.o.ink || 'currentColor', drawEach = T * 0.34, drawSpread = T * 0.58 - drawEach, fillEach = T * 0.22, fillSpread = T * 0.26;
      units.forEach(function (u) {
        var tr = (CH === 'snap' || CH === 'slide' ? EASE.standard : EASE.inOut)(seg(t, u.rank * drawSpread, u.rank * drawSpread + drawEach));
        var lr = lumRank[S.units.indexOf(u)], f0 = T * 0.4 + lr * fillSpread, fo = EASE.enter(seg(t, f0, f0 + fillEach));
        var to = 1 - EASE.exit(seg(t, T * 0.78, T * 0.97));
        S.setUnit(u, { fo: fo, trace: tr, traceO: to, traceColor: ink, o: tr > 0 || fo > 0 ? 1 : 0 });
      });
    } });

  /** sting — the compact asset, quick (social intros, video bumpers). */
  LM.register({ id: 'sting', title: 'Compact sting',
    total: function (S) { return Math.round(Math.max(D('formation') * 0.9, LM.phaseLen(S) * 0.72)); },
    phases: function (S) { return [{ label: 'Compact mark — ' + sig(S) + ', fast', from: 0, to: this.total(S), ease: 'enter' }]; },
    render: function (S, t) {
      resetMarkGroups(S); var T = this.total(S);
      if (S.role('mark').length) LM.markPhase(S, t, 0, T, sig(S)); else LM.letters(S, t, 0, T, {});
    } });

  /** reveal — wordmark: the lettering opens as one gesture. */
  LM.register({ id: 'reveal', title: 'Lettering reveal',
    total: function (S) { return Math.round(D('logo') * 0.8); },
    phases: function (S) { return [{ label: 'Lettering opens — ' + (CH === 'snap' ? CFG.angle + '° wipe' : CH === 'slide' ? 'horizontal wipe on the grid' : CH === 'glide' ? 'iris from the centre' : 'feathered wipe'), from: 0, to: this.total(S), ease: CH === 'flow' ? 'standard' : 'enter' }]; },
    render: function (S, t) { LM.letters(S, t, 0, this.total(S), { mode: 'wipe' }); } });

  /** stagger — wordmark: glyph by glyph. */
  LM.register({ id: 'stagger', title: 'Letter stagger',
    total: function (S) { return Math.round(D('logo') * 0.95); },
    phases: function (S) { return [{ label: 'Glyphs in sequence — ' + (CH === 'glide' ? 'centre → out, scale from the baseline' : CH === 'slide' ? 'left → right, rise from the baseline' : CH === 'snap' ? 'left → right, angled wipes' : 'left → right, soft drift'), from: 0, to: this.total(S), ease: CH === 'flow' ? 'emphasis' : 'enter' }]; },
    render: function (S, t) { LM.letters(S, t, 0, this.total(S), { mode: 'stagger' }); } });

  /** monogram — wordmark: the compact mark appears, shrinks into place, the other glyphs follow. */
  LM.register({ id: 'monogram', title: 'Monogram morph-in',
    total: function (S) { return Math.round(D('logo') * 1.25); },
    phases: function (S) { var T = this.total(S); return [{ label: 'Compact mark enters at the centre', from: 0, to: T * 0.3, ease: CH === 'flow' ? 'emphasis' : 'enter' }, { label: 'Compact mark settles onto its glyph', from: T * 0.3, to: T * 0.6, ease: 'standard' }, { label: 'Remaining glyphs follow', from: T * 0.5, to: T, ease: CH === 'flow' ? 'emphasis' : 'enter' }]; },
    setup: function (S) {
      if (S._mono) return S._mono;
      var letters = S.units.slice().sort(function (a, b) { return a.cx - b.cx; }), first = letters[0], x = S.extras.mono;
      if (!x || !first) return (S._mono = { none: true });
      var inner = x.el.firstChild, bb = inner.getBBox(), m0 = inner.getAttribute('transform') || '';
      var k = first.rb.h / (bb.height || 1);
      // map the compact content bbox onto the first glyph: same height, same left & baseline
      var tx = first.rb.x - bb.x * k, ty = first.rb.y - bb.y * k;
      var wrap = mk('g', { transform: 'translate(' + tx + ' ' + ty + ') scale(' + k + ')' });
      x.el.insertBefore(wrap, inner); wrap.appendChild(inner); inner.removeAttribute('transform');
      var gcx = first.rb.x + bb.width * k / 2, gcy = first.cy, H = S.box.h, k0 = Math.min(3.2, Math.max(1.6, (S.box.h * 2.4) / first.rb.h));
      return (S._mono = { first: first, gcx: gcx, gcy: gcy, k0: k0, cx: S.box.x + S.box.w / 2, cy: S.box.y + S.box.h / 2, rest: letters.slice(1) });
    },
    render: function (S, t) {
      var T = this.total(S), M = this.setup(S), H = S.box.h; S.groups.forEach(function (g) { S.setGroup(g, {}); });
      if (M.none) return LM.letters(S, t, 0, T, { mode: 'stagger' });
      var a = seg(t, 0, T * 0.3), m = EASE.standard(seg(t, T * 0.3, T * 0.6)), xf = seg(t, T * 0.52, T * 0.64);
      var k = lerp(M.k0, 1, m), X = lerp(M.cx, M.gcx, m), Y = lerp(M.cy, M.gcy, m), ent;
      if (CH === 'glide') ent = { s: 0.6 + 0.4 * EASE.enter(a), r: -40 * (1 - EASE.enter(a)), o: Math.min(1, a * 2) };
      else if (CH === 'flow') ent = { s: 0.94 + 0.06 * EASE.emphasis(a), y: H * 0.4 * (1 - EASE.emphasis(a)), o: EASE.standard(a) };
      else if (CH === 'slide') ent = { y: H * 0.6 * (1 - EASE.enter(a)), o: Math.min(1, a * 3) };
      else ent = { o: a > 0 ? 1 : 0, wipe: EASE.enter(a) };
      var trs = 'translate(' + (X + (ent.y ? 0 : 0)).toFixed(2) + ' ' + (Y + (ent.y || 0)).toFixed(2) + ') rotate(' + (ent.r || 0).toFixed(2) + ') scale(' + (k * (ent.s || 1)).toFixed(4) + ') translate(' + (-M.gcx).toFixed(2) + ' ' + (-M.gcy).toFixed(2) + ')';
      var st = { transform: trs, o: (ent.o == null ? 1 : ent.o) * (1 - xf), hide: xf >= 1 };
      if (ent.wipe != null && ent.wipe < 1) { var r = S.extras.mono.el.getBBox(); st.clip = angledClip({ x: r.x, y: r.y, w: r.width, h: r.height }, ent.wipe); }
      S.setExtra('mono', st);
      S.setUnit(M.first, { o: xf });
      var rest = M.rest, span = T * 0.5, each = Math.min(span * 0.6, D('slower'));
      rest.forEach(function (u, i) {
        var s0 = T * 0.5 + (rest.length > 1 ? i / (rest.length - 1) : 0) * (span - each), r2 = seg(t, s0, s0 + each), Hh = u.rb.h;
        if (r2 >= 1) return S.setUnit(u, {});
        if (r2 <= 0) return S.setUnit(u, { o: 0 });
        if (CH === 'snap') S.setUnit(u, { clip: angledClip(u.rb, EASE.enter(r2)) });
        else if (CH === 'glide') S.setUnit(u, { s: 0.6 + 0.4 * EASE.enter(r2), o: Math.min(1, r2 * 2) });
        else if (CH === 'slide') S.setUnit(u, { x: -Hh * 0.4 * (1 - EASE.enter(r2)), o: Math.min(1, r2 * 3) });
        else S.setUnit(u, { x: -Hh * 0.3 * (1 - EASE.emphasis(r2)), o: EASE.standard(r2) });
      });
    } });

  /** frame — emblem: the frame forms first, then the content arrives row by row. */
  LM.register({ id: 'frame', title: 'Frame, then content',
    total: function (S) { return Math.round(D('logo') * 1.1); },
    phases: function (S) { var T = this.total(S); return [{ label: 'Frame forms — ' + (CH === 'glide' ? 'iris, then sweeps around the centre' : CH === 'snap' ? 'angled wipes' : CH === 'slide' ? 'rises from the base' : 'soft scale'), from: 0, to: T * 0.48, ease: 'enter' }, { label: 'Content arrives row by row', from: T * 0.4, to: T, ease: CH === 'flow' || CH === 'glide' ? 'emphasis' : 'enter' }]; },
    render: function (S, t) {
      resetMarkGroups(S); var T = this.total(S), units = S.markUnits(), frames = units.filter(function (u) { return u.frame; }), content = units.filter(function (u) { return !u.frame; });
      if (!frames.length) { frames = order(units, 'area', S).slice(0, 1); content = units.filter(function (u) { return frames.indexOf(u) < 0; }); }
      var fs = T * 0.48, fe = Math.min(fs, Math.max(D('slower'), fs / frames.length * 1.5)), fsp = fs - fe;
      frames.forEach(function (u, i) {
        var a = frames.length > 1 ? i / (frames.length - 1) * fsp : 0, r = seg(t, a, a + fe), e = EASE.enter(r), b = u.rb;
        if (r >= 1) return S.setUnit(u, {});
        if (r <= 0) return S.setUnit(u, { o: 0 });
        if (CH === 'glide') S.setUnit(u, i === 0 ? { clip: circleClip(u.cx, u.cy, Math.max(b.w, b.h) * 0.72 * e) } : { clip: wedgeClip(u.cx, u.cy, Math.max(b.w, b.h), -90 + i * 40, 360 * e) });
        else if (CH === 'snap') S.setUnit(u, { clip: angledClip(b, e, i % 2 === 1) });
        else if (CH === 'slide') S.setUnit(u, { clip: rectClip(b, e, 'up') });
        else S.setUnit(u, { s: 0.85 + 0.15 * EASE.emphasis(r), o: EASE.standard(r) });
      });
      // content: rows by vertical position
      var rows = []; content.slice().sort(function (a, b) { return a.cy - b.cy; }).forEach(function (u) { var row = rows.find(function (R) { return Math.abs(R.cy - u.cy) < Math.max(R.h, u.rb.h) * 0.5; }); if (row) { row.units.push(u); row.h = Math.max(row.h, u.rb.h); } else rows.push({ cy: u.cy, h: u.rb.h, units: [u] }); });
      var cs = Math.min(T * 0.5, fs * 0.94), span = T - cs, each = Math.min(span * 0.55, D('slower') * 1.1), rsp = span - each;
      rows.forEach(function (R, ri) {
        R.units.sort(function (a, b) { return a.cx - b.cx; });
        R.units.forEach(function (u, ui) {
          var a = cs + (rows.length > 1 ? ri / (rows.length - 1) : 0) * rsp * 0.75 + (R.units.length > 1 ? ui / (R.units.length - 1) : 0) * rsp * 0.25;
          if (CH === 'glide') V.pop(S, u, t, a, each); else V.build(S, u, t, a, each, {});
        });
      });
    } });

  /** outro — end card: quick logo entrance, then tagline and address; holds. */
  LM.register({ id: 'outro', title: 'End card',
    logoLen: function (S) { return Math.max(D('formation'), LM.phaseLen(S) * 0.7) + (LM.hasLettering(S) && S.role('mark').length ? lettersDur(S) * 0.8 - overlap() * 0.6 : 0); },
    total: function (S) { return Math.round(this.logoLen(S) + D('slower') * 1.6 + STAGGER * 4 + 900); },
    phases: function (S) { var L = this.logoLen(S); return [{ label: 'Logo — signature entrance, compressed', from: 0, to: L, ease: 'enter' }, { label: 'Tagline', from: L - D('slow') * 0.4, to: L - D('slow') * 0.4 + D('slower') * 1.2, ease: CH === 'flow' ? 'emphasis' : 'enter' }, { label: 'Address', from: L + STAGGER * 3, to: L + STAGGER * 3 + D('slower'), ease: 'standard' }, { label: 'Hold', from: this.total(S) - 900, to: this.total(S), ease: '—' }]; },
    render: function (S, t) {
      resetMarkGroups(S);
      var L = this.logoLen(S), hasMark = S.role('mark').length > 0, m = Math.max(D('formation'), LM.phaseLen(S) * 0.7);
      if (hasMark) { LM.markPhase(S, t, 0, m, sig(S)); if (LM.hasLettering(S)) LM.letters(S, t, m - overlap() * 0.6, lettersDur(S) * 0.8, {}); }
      else LM.letters(S, t, 0, L, {});
      var tl = [['tagline', L - D('slow') * 0.4, D('slower') * 1.2], ['url', L + STAGGER * 3, D('slower')]];
      tl.forEach(function (x) {
        var T = S.texts[x[0]]; if (!T) return; var r = seg(t, x[1], x[1] + x[2]), b = T.rb;
        if (r >= 1) return S.setExtra(x[0], {});
        if (r <= 0) return S.setExtra(x[0], { o: 0 });
        if (CH === 'snap') S.setExtra(x[0], { clip: angledClip(b, EASE.enter(r)), x: -b.h * 0.3 * (1 - EASE.enter(r)) });
        else if (CH === 'slide') { var e = EASE.enter(r); S.setExtra(x[0], { y: b.h * 0.9 * (1 - e), clip: [[b.x - b.h, b.y - b.h * 0.9 * (1 - e) - 2], [b.x + b.w + b.h, b.y - b.h * 0.9 * (1 - e) - 2], [b.x + b.w + b.h, b.y + b.h - b.h * 0.9 * (1 - e) + 4], [b.x - b.h, b.y + b.h - b.h * 0.9 * (1 - e) + 4]] }); }
        else if (CH === 'glide') S.setExtra(x[0], { s: 0.92 + 0.08 * EASE.enter(r), o: EASE.enter(Math.min(1, r * 1.4)) });
        else S.setExtra(x[0], { y: b.h * 0.5 * (1 - EASE.emphasis(r)), o: EASE.standard(r) });
      });
    } });

  /** loader — loops. Multi-part marks: parts light in sequence. Simple marks / emblems: character-specific fill or orbit. */
  LM.register({ id: 'loader', title: 'Loader', loop: true,
    total: function (S) { return Math.round(D('formation') * (CH === 'flow' ? 1.8 : CH === 'glide' ? 1.5 : 1.35)); },
    phases: function (S) { var C = this.total(S); return [{ label: 'One cycle (loops) — ' + (this.mode(S) === 'chase' ? 'parts light ' + markOrderName('angle') : CH === 'glide' ? 'an orbit circles the mark' : CH === 'snap' ? 'the mark fills along the ' + CFG.angle + '° cut' : CH === 'slide' ? 'stepped fill from the base' : 'a soft wave fills the mark'), from: 0, to: C, ease: CH === 'snap' ? 'enter / exit' : CH === 'slide' ? 'steps' : 'cosine' }]; },
    mode: function (S) { var free = S.units.filter(function (u) { return !u.frame; }); return free.length >= 4 && free.length === S.units.length ? 'chase' : 'simple'; },
    render: function (S, t) {
      var C = this.total(S), u = (t % C) / C, b = S.box;
      S.groups.forEach(function (g) { S.setGroup(g, {}); });
      if (this.mode(S) === 'chase') {
        // snap: a lit band sweeps along the cut axis · slide: stepped build-up from the base, then reset
        // glide: light orbits around the centre · flow: a soft wave crosses left → right
        var how = CH === 'snap' ? 'axis' : CH === 'slide' ? 'up' : CH === 'glide' ? 'angle' : 'x', units = order(S.units, how, S);
        units.forEach(function (un) {
          var v = how === 'angle' ? un.rank : un.rankV, lit;
          if (CH === 'snap') { var c = -0.35 + u * 1.7; lit = Math.abs(v - c) < 0.2 ? 1 : Math.abs(v - c) < 0.3 ? 0.45 : 0; }
          else if (CH === 'slide') { var k = Math.floor(u * 6) / 5; lit = u < 0.84 ? (v <= k + 0.001 ? 1 : 0) : 0; }
          else if (CH === 'glide') { var ph = ((u - v) % 1 + 1) % 1; lit = Math.pow(Math.max(0, Math.cos(ph * Math.PI)), 4); }
          else { var c2 = -0.4 + u * 1.8; lit = Math.exp(-Math.pow((v - c2) / 0.22, 2)); }
          S.setUnit(un, { o: 0.24 + 0.76 * lit });
        });
        return;
      }
      if (CH === 'glide') {
        if (!S.extras.orbit) {
          var R = Math.hypot(b.w, b.h) / 2 * 1.08, cxo = b.x + b.w / 2, cyo = b.y + b.h / 2;
          var node = mk('circle', { cx: cxo, cy: cyo, r: R, fill: 'none', pathLength: 1, 'stroke-dasharray': '0.22 0.78', 'stroke-linecap': 'round', 'stroke-width': (Math.max(b.w, b.h) * 0.045).toFixed(2) });
          node.setAttribute('style', 'stroke: var(--color-brand-primary, currentColor)');
          S.addExtra({ id: 'orbit', node: node, at: 'over', final: 'hide', inBounds: true }); S.fit();
        }
        var ob = S.extras.orbit.el.firstChild; ob.setAttribute('stroke-dashoffset', (-u).toFixed(4));
        S.units.forEach(function (un) { S.setUnit(un, { s: 0.97 + 0.03 * Math.cos(u * Math.PI * 2), pivot: [b.x + b.w / 2, b.y + b.h / 2] }); });
        return;
      }
      if (!S.extras.ghost) {
        var gh = S.root.cloneNode(true); $$('[id]', gh).forEach(function (e) { e.removeAttribute('id'); }); $$('[clip-path],[mask]', gh).forEach(function (e) { e.removeAttribute('clip-path'); e.removeAttribute('mask'); });
        S.addExtra({ id: 'ghost', node: gh, at: 'under', final: 'hide' });
      }
      S.setExtra('ghost', { o: 0.18 });
      var clip;
      if (CH === 'snap') { var q = u < 0.55 ? EASE.enter(u / 0.55) : 1, out = u > 0.78 ? EASE.exit((u - 0.78) / 0.22) : 0; clip = out > 0 ? angledClip(b, out, true) : angledClip(b, q); }
      else if (CH === 'slide') { var steps = 4, k = Math.min(steps, Math.floor(u * (steps + 1.6))) / steps; clip = rectClip(b, k, 'up'); }
      else {
        var lv = 0.5 - 0.5 * Math.cos(u * Math.PI * 2), amp = b.h * 0.05, y0 = b.y + b.h * (1.06 - 1.12 * lv), pts = [];
        for (var i = 0; i <= 28; i++) { var x = b.x - b.w * 0.05 + b.w * 1.1 * i / 28; pts.push([x, y0 + Math.sin(i / 28 * Math.PI * 3 + u * Math.PI * 4) * amp]); }
        pts.push([b.x + b.w * 1.05, b.y + b.h * 1.2]); pts.push([b.x - b.w * 0.05, b.y + b.h * 1.2]); clip = pts;
      }
      S.units.forEach(function (un) { S.setUnit(un, { clip: clip }); });
    } });

  /** Convenience: animate any logo SVG in el with a concept. o: { svg, concept, aspect, ink, roles } */
  G.logoAnimate = function (el, o) {
    o = o || {}; if (!el || !o.svg) return null;
    var S = new Scene(el, { svg: o.svg, aspect: o.aspect || 0, pad: o.pad == null ? 0.04 : o.pad, ink: o.ink, roles: o.roles || (CFG.logoType === 'wordmark' ? { mark: 'lettering' } : {}), label: o.label });
    var c = LM.concepts[o.concept || (CFG.logoType === 'combination' ? 'signature' : 'intro')];
    if (!c || reduced()) { S.finalize(); return { scene: S, player: null }; }
    var pl = new Player(S, c, {}); pl.renderAt(0); setTimeout(function () { pl.play(0); }, o.delay || 0);
    return { scene: S, player: pl };
  };
