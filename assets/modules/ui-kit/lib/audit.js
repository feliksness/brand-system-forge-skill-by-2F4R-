#!/usr/bin/env node
// audit.js — rendered text-contrast audit of the UI kit gallery in the light, dark and contrast themes.
// usage: node lib/audit.js /abs/path/UI-DESIGN-SYSTEM/components/index.html
// Walks every visible text element, resolves its colour and the colour actually behind it (own background,
// the ::before "plate" of cut shapes, then ancestors) and reports pairs below WCAG AA (4.5:1, 3:1 for large text).
// Disabled controls, placeholders-only and decorative (aria-hidden) text are skipped, as WCAG allows.
const path = require('path');
const { launch } = require(path.join(__dirname, '..', '..', '..', '..', 'scripts', '_pw.js'));
(async () => {
  const file = path.resolve(process.argv[2]);
  const br = await launch(); let total = 0;
  for (const th of ['light', 'dark', 'contrast']) {
    const pg = await br.newPage({ viewport: { width: 1440, height: 900 } });
    await pg.goto('file://' + file + '?preview&theme=' + th);
    await pg.evaluate(() => document.fonts && document.fonts.ready);
    await pg.waitForTimeout(300);
    const bad = await pg.evaluate(() => {
      const parse = (s) => {
        let m = /rgba?\(([^)]+)\)/.exec(s);
        if (m) { const v = m[1].split(/[\s,/]+/).filter(Boolean).map(Number); return [v[0], v[1], v[2], v[3] == null ? 1 : v[3]]; }
        m = /color\(srgb ([^)]+)\)/.exec(s);
        if (m) { const v = m[1].split(/[\s/]+/).filter(Boolean).map(Number); return [v[0] * 255, v[1] * 255, v[2] * 255, v[3] == null ? 1 : v[3]]; }
        return null;
      };
      const blend = (top, bot) => { const a = top[3]; return [top[0] * a + bot[0] * (1 - a), top[1] * a + bot[1] * (1 - a), top[2] * a + bot[2] * (1 - a), 1]; };
      const lum = (c) => { const f = (v) => { v /= 255; return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }; return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]); };
      const cr = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
      const layers = (el) => {
        const out = [];
        for (let n = el; n && n.nodeType === 1; n = n.parentElement) {
          const cs = getComputedStyle(n);
          if (+cs.opacity === 0) return null;
          const pb = getComputedStyle(n, '::before');
          if (pb.content !== 'none' && pb.position === 'absolute' && +pb.zIndex < 0) {         // cut "plate"
            const wipe = /(\S+)\s+\S+\s*$/.exec(pb.backgroundPosition.split(',').pop().trim());
            const g = pb.backgroundImage.split('linear-gradient').pop();
            const wc = parse(g || '');
            if (wipe && parseFloat(wipe[1]) === 0 && wc && wc[3] > 0) out.push(wc);           // hover wipe fully in
            const c2 = parse(pb.backgroundColor); if (c2 && c2[3] > 0) out.push(c2);
          }
          const c = parse(cs.backgroundColor); if (c && c[3] > 0) out.push(c);
          else if (/linear-gradient/.test(cs.backgroundImage)) {                                  // gradient-cut fills
            const all = cs.backgroundImage.match(/(rgba?\([^)]+\)|color\(srgb[^)]+\))/g) || [];
            const last = all.length ? parse(all[all.length - 1]) : null; if (last && last[3] > 0) out.push(last);
          }
          if (out.length && out[out.length - 1][3] >= 1) break;
        }
        return out;
      };
      const res = [];
      const els = [...document.querySelectorAll('body *')].filter((el) => [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim()));
      for (const el of els) {
        if (el.closest('[aria-hidden="true"], .sr-only, script, style, option, pre, [hidden], :disabled, [aria-disabled="true"], .doc-code')) continue;
        if (el.closest('button:disabled, input:disabled')) continue;
        const lab = el.closest('label'); if (lab && lab.querySelector(':disabled')) continue;       // inactive control labels are exempt
        const r = el.getBoundingClientRect(); if (!r.width || !r.height) continue;
        const cs = getComputedStyle(el); if (cs.visibility === 'hidden' || +cs.opacity === 0) continue;
        const fg = parse(cs.color); if (!fg || fg[3] === 0) continue;
        const ls = layers(el); if (!ls) continue;
        let bg = [255, 255, 255, 1];
        for (let i = ls.length - 1; i >= 0; i--) bg = blend(ls[i], bg);
        const f = blend(fg, bg), ratio = cr(f, bg);
        const size = parseFloat(cs.fontSize), bold = +cs.fontWeight >= 700;
        const need = (size >= 24 || (size >= 18.66 && bold)) ? 3 : 4.5;
        if (ratio < need - 0.05) {
          const id = el.closest('[id]'); res.push({ parent: (el.parentElement.className || '').toString().slice(0, 40), text: el.textContent.trim().slice(0, 40), cls: (el.className && el.className.baseVal == null ? el.className : '').slice(0, 60), where: id ? id.id : '', ratio: Math.round(ratio * 100) / 100, need });
        }
      }
      return res;
    });
    total += bad.length;
    console.log(`\n[${th}] ${bad.length} text elements below AA`);
    bad.slice(0, 40).forEach((x) => console.log(`  ${x.ratio} < ${x.need}  #${x.where}  .${x.cls} (in .${x.parent})  "${x.text}"`));
    await pg.close();
  }
  await br.close();
  console.log(`\naudit: ${total} issue(s)`);
})().catch((e) => { console.error(e.message || e); process.exit(1); });
