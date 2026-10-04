// boards.js — overview boards as HTML (brand type classes) → PNG via shots():
//   PATTERNS/previews/patterns-overview.png · GRAPHICS/previews/graphics-overview.png · PHOTOGRAPHY/previews/crops-overview.png
const fs = require('fs'), path = require('path');

function run(ctx) {
  const { b, F, gfx, cw } = ctx, p = b.p, esc = F.esc, C = gfx.C, dna = b.dna || {};
  const lab = (s) => `<span class="${p}-label">${esc(s)}</span>`;
  const dnaLine = `${C.lang} · corner ${C.corner}${C.corner === 'cut' ? ' ' + C.cut + '°' : ''} · crop ${(dna.imagery || {}).crop || 'rect'} ${C.crop}° · ${b.logoType} logo`;
  const baseCss = `
  body { margin: 0; background: var(--color-background); color: var(--color-text-primary); }
  .bd { width: 2400px; padding: 96px 112px 104px; box-sizing: border-box; }
  .bd-head { display: grid; grid-template-columns: 1fr auto; align-items: end; gap: 48px; padding-bottom: 36px; border-bottom: 1px solid var(--color-border); margin-bottom: 56px; }
  .bd-title { font-size: 112px !important; line-height: 0.95 !important; margin: 14px 0 0; }
  .bd-meta { text-align: right; display: grid; gap: 10px; color: var(--color-text-secondary); }
  .bd-foot { margin-top: 64px; padding-top: 28px; border-top: 1px solid var(--color-border); display: flex; justify-content: space-between; gap: 32px; color: var(--color-text-secondary); }
  .chip { display: inline-flex; align-items: center; gap: 10px; margin-right: 28px; }
  .chip i { width: 22px; height: 22px; display: inline-block; border: 1px solid var(--color-border); }
  img { display: block; }
  `;
  function head(eyebrow, title, meta) { return `<header class="bd-head"><div><p class="${p}-eyebrow"><span class="${p}-index">${esc(b.name)}</span> ${esc(eyebrow)}</p><h1 class="${p}-display-l bd-title">${esc(title)}</h1></div><div class="bd-meta">${meta.map(lab).join('')}</div></header>`; }
  function legend() { return Object.keys(cw).map(k => { const c = cw[k]; return `<span class="chip">${[c.bg, c.t1, c.t2, c.t3, c.accent].map(h => `<i style="background:${h}"></i>`).join('')}${lab(c.label)}</span>`; }).join(''); }
  const sample = b.content._sample ? lab('Sample content — replace before publishing') : '';

  // ------------------------------------------------------------ patterns overview
  if (ctx.patterns) {
    const at = 'PATTERNS/previews', rel = t => b.rel(at, t);
    const cards = ctx.patterns.map((x, i) => `<figure class="pc"><div class="pc-sw"><img class="pc-a" src="${rel(x.files.paper.png)}" alt=""><img class="pc-b" src="${rel(x.files.foundation.png)}" alt=""><img class="pc-c" src="${rel(x.files.primary.png)}" alt=""></div>
      <figcaption><span class="${p}-index">${String(i + 1).padStart(2, '0')}</span><div><h2 class="${p}-h4">${esc(x.title)}</h2>${lab(x.tags + (x.tile ? ' · tile ' + x.w + '×' + x.h : ' · supergraphic'))}</div><span class="pc-src ${p}-label">${esc(x.derived)}</span></figcaption></figure>`).join('');
    const css = baseCss + `
    .pg { display: grid; grid-template-columns: repeat(4, 1fr); gap: 56px 40px; }
    .pc { margin: 0; }
    .pc-sw { display: grid; grid-template-columns: 2fr 1fr; grid-template-rows: 1fr 1fr; gap: 8px; aspect-ratio: 1.55; }
    .pc-sw img { width: 100%; height: 100%; object-fit: cover; }
    .pc-a { grid-row: 1 / span 2; box-shadow: inset 0 0 0 1px var(--color-border); outline: 1px solid var(--color-border-subtle); }
    .pc figcaption { display: grid; grid-template-columns: auto 1fr auto; gap: 16px; align-items: baseline; margin-top: 18px; }
    .pc h2 { margin: 0 0 6px; }
    .pc-src { color: var(--color-text-secondary); white-space: nowrap; }`;
    const html = F.page(b, 'Pattern system', `<main class="bd">${head('Pattern system', 'Pattern system', [`${ctx.patterns.length} patterns · ${Object.keys(cw).length} colourways · seamless SVG tiles`, `Derived from the mark + design DNA · ${dnaLine}`, `Patterns in DNA order: ${(dna.patterns || []).join(', ')} + mark repeat · outline · crop`])}
      <section class="pg" aria-label="Patterns">${cards}</section>
      <footer class="bd-foot"><div>${legend()}</div><div>${lab('PATTERNS/SVG · PATTERNS/PNG · tiling check in previews')}</div></footer></main>`, at, { head: `<style>${css}</style>` });
    const hp = b.path(at, 'patterns-overview.html'); F.write(hp, html);
    const rows = Math.ceil(ctx.patterns.length / 4), H = 96 + 230 + 56 + rows * (Math.round((2400 - 224 - 120) / 4 / 1.55) + 120) + (rows - 1) * 56 + 170;
    ctx.shots.push({ in: hp, out: b.path(at, 'patterns-overview.png'), w: 2400, h: 900, full: true, wait: 400 });
  }

  // ------------------------------------------------------------ graphics overview
  if (ctx.graphics) {
    const at = 'GRAPHICS/previews', rel = t => b.rel(at, t);
    const FAM = { frames: ['Frames', 'Image and content frames in the brand corner grammar.'], corners: ['Corners', 'Corner devices that anchor a layout.'], bands: ['Bands', 'Full-bleed bands for section breaks, headers and footers.'],
      dividers: ['Dividers', 'Rules and rhythm lines with the brand end treatment.'], badges: ['Badges & stickers', 'Labels, seals and stickers — text outlined from the brand fonts.'], numbers: ['Number blocks', 'Display figures for steps, chapters and lists.'],
      quotes: ['Quote marks', 'Quote glyphs and a quote panel.'], arrows: ['Arrows', 'Directional devices on the DNA stroke.'], highlights: ['Highlights', 'Underlines, brackets and markers for emphasis.'],
      shapes: ['Motif shapes', `Standalone shapes from the DNA motifs (${(dna.motifs || []).filter(m => m.indexOf('mark') !== 0).join(', ')}).`], mark: ['Mark devices', 'Supergraphic crops, echoes and strips built from the mark itself.'], backgrounds: ['Backgrounds', 'Hero 1920×1080 · square 1080 · story 1080×1920 — calm zones for text.'] };
    const sections = Object.keys(FAM).map(fk => { const items = ctx.graphics.filter(g => g.family === fk); if (!items.length) return '';
      const bg = fk === 'backgrounds';
      const AV = 2400 - 224 - 380 - 48, GAP = 22;
      const dims = items.map(g => { const ar = g.w / g.h, hgt = bg ? 300 : (ar > 3 ? 120 : 230), wd = Math.round(Math.min(bg ? 560 : 520, hgt * ar)); return { g, ar, w: Math.max(wd, bg ? 0 : 170), h: bg ? Math.round(wd / ar) : hgt }; });
      if (!bg) { const tot = dims.reduce((a, d) => a + d.w, 0) + GAP * (dims.length - 1); if (tot > AV) { const k = (AV - GAP * (dims.length - 1)) / dims.reduce((a, d) => a + d.w, 0); dims.forEach(d => { d.w = Math.floor(d.w * k); if (d.ar > 1.2) d.h = Math.min(d.h, Math.max(110, Math.round(d.w / d.ar) + 40)); }); } }
      const thumbs = dims.map(({ g, w, h }) => `<figure class="th${g.dark ? ' th--dark' : ''}${bg ? ' th--bg' : ''}"><div class="th-box" style="width:${w}px;height:${h}px"><img src="${rel(g.png)}" alt="" style="max-width:${w - (bg ? 0 : 28)}px;max-height:${h - (bg ? 0 : 28)}px"></div><figcaption class="${p}-label">${esc(g.name)}</figcaption></figure>`).join('');
      return `<section class="gs"><div class="gs-l"><p class="${p}-eyebrow">${esc(fk)}</p><h2 class="${p}-h3">${esc(FAM[fk][0])}</h2><p class="${p}-small gs-d">${esc(FAM[fk][1])}</p>${lab(items.length + ' · GRAPHICS/' + fk + '/')}</div><div class="gs-r">${thumbs}</div></section>`; }).join('');
    const css = baseCss + `
    .gs { display: grid; grid-template-columns: 380px 1fr; gap: 48px; padding: 36px 0; border-bottom: 1px solid var(--color-border-subtle); }
    .gs-l h2 { margin: 10px 0 10px; } .gs-d { color: var(--color-text-secondary); margin-bottom: 14px; max-width: 30ch; }
    .gs-r { display: flex; flex-wrap: wrap; gap: 22px; align-items: flex-end; }
    .th { margin: 0; } .th figcaption { margin-top: 10px; color: var(--color-text-secondary); }
    .th-box { display: grid; place-items: center; background: var(--color-surface); box-shadow: inset 0 0 0 1px var(--color-border-subtle); }
    .th--dark .th-box { background: var(--color-surface); }
    .th-box img { width: auto; height: auto; }
    .th--bg .th-box { background: none; box-shadow: none; } .th--bg img { box-shadow: 0 0 0 1px var(--color-border-subtle); }`;
    const html = F.page(b, 'Graphic devices', `<main class="bd">${head('Graphic devices', 'Graphic library', [`${ctx.graphics.length} SVG devices + PNG previews · ${Object.keys(FAM).filter(k => ctx.graphics.some(g => g.family === k)).length} families`, `Built from the DNA motifs + mark geometry · ${dnaLine}`, 'Generator: GRAPHICS/generator/index.html'])}${sections}
      <footer class="bd-foot"><div>${legend()}</div><div>${sample}</div></footer></main>`, at, { head: `<style>${css}</style>` });
    const hp = b.path(at, 'graphics-overview.html'); F.write(hp, html);
    ctx.shots.push({ in: hp, out: b.path(at, 'graphics-overview.png'), w: 2400, h: 900, full: true, wait: 500 });
  }

  // ------------------------------------------------------------ crops & treatments overview
  if (ctx.placeholders && ctx.maskList) {
    const at = 'PHOTOGRAPHY/previews', rel = t => b.rel(at, t), ph = ctx.placeholders;
    const pick = (ratio, tone) => (ph.find(x => x.ratio === ratio && x.tone === tone) || ph[0]);
    const demo = ctx.demoScene ? rel(ctx.demoScene) : rel(pick('3:2', 'light').png), imgL = demo;
    const maskTiles = ctx.maskList.map(m => { const cls = m.cls ? `${p}-mask-${m.cls}` : `${p}-mask`, arm = /aspect-ratio:\s*([\d.]+)/.exec(m.css || ''), ar = arm ? +arm[1] : 0.8, BX = 250;
      const w = ar >= 1 ? BX : Math.round(BX * ar), h = ar >= 1 ? Math.round(BX / ar) : BX;
      return `<figure class="mk"><div class="mk-box"><img class="${cls}" src="${demo}" alt="" style="width:${w}px;height:${h}px;aspect-ratio:auto"></div><figcaption><code class="${p}-label">.${cls}</code><span class="${p}-caption">${esc(m.note)}</span></figcaption></figure>`; }).join('');
    const defM = ctx.maskList[0], trMask = /blob|circle|mark/.test(defM.note) ? `${p}-mask-rounded` : `${p}-mask`;
    const treats = [['', 'original image'], ['natural', 'house grade'], ['mono', 'black & white'], ['duotone', 'foundation → paper'], ['duotone-brand', 'foundation → brand tint'], ['tint', 'primary wash'], ['grain', 'film grain']]
      .filter(t => !t[0] || t[0] === 'mono' || t[0] === 'natural' || t[0] === 'duotone-brand' || (dna.imagery && (dna.imagery.treatments || []).some(x => t[0].indexOf(x) === 0)) || t[0] === 'duotone')
      .map(t => `<figure class="tr"><div class="${p}-photo ${t[0] ? p + '-photo--' + t[0] : ''} ${trMask}"><img src="${imgL}" alt=""></div><figcaption><code class="${p}-label">${t[0] ? '.' + p + '-photo--' + t[0] : 'no treatment'}</code><span class="${p}-caption">${esc(t[1])}</span></figcaption></figure>`).join('');
    const tag = (b.content.brand || {}).tagline || b.name;
    const scr = (C.lang === 'angular' ? ['bottom', 'left', 'angled'] : C.lang === 'round' ? ['bottom', 'left', 'radial'] : ['bottom', 'left', 'full']).map(s => `<figure class="sc"><div class="${p}-photo ${p}-photo--natural" style="aspect-ratio:16/10"><img src="${imgL}" alt=""><span class="${p}-scrim ${p}-scrim--${s}" aria-hidden="true"></span><div class="${p}-photo__content ${s === 'radial' || s === 'bottom' ? '' : ''}"><p class="${p}-photo__caption">${esc(b.labels.projects || b.labels.posts || '')}</p><p class="${p}-h2 sc-h">${esc(tag)}</p></div></div><figcaption><code class="${p}-label">.${p}-scrim--${s}</code><span class="${p}-caption">text-inverse ≥ 4.5:1 over white</span></figcaption></figure>`).join('');
    const phs = ph.slice().sort((a, c) => a.name.localeCompare(c.name)).map(x => `<figure class="ph"><img src="${rel(x.png)}" alt="" style="height:220px;width:auto"><figcaption class="${p}-label">${esc(x.ratio)} · ${esc(x.name)}</figcaption></figure>`).join('');
    const css = baseCss + `
    .sec { margin-bottom: 64px; } .sec > h2 { margin: 8px 0 28px; }
    .mg { display: grid; grid-template-columns: repeat(7, 1fr); gap: 36px 28px; }
    .mk { margin: 0; } .mk-box { height: 300px; display: grid; place-items: center; background: var(--color-surface); box-shadow: inset 0 0 0 1px var(--color-border-subtle); padding: 18px; box-sizing: border-box; }
    .mk-box img { max-width: none; }
    figcaption { margin-top: 12px; display: grid; gap: 4px; } code { font-family: var(--font-mono); }
    .tg { display: grid; grid-template-columns: repeat(7, 1fr); gap: 28px; } .tr { margin: 0; } .tr .${p}-photo { aspect-ratio: 3/2; }
    .sg { display: grid; grid-template-columns: repeat(3, 1fr); gap: 32px; } .sc { margin: 0; } .sc-h { color: inherit; margin-top: 8px; max-width: 18ch; }
    .pg2 { display: flex; flex-wrap: wrap; gap: 20px; } .ph { margin: 0; }`;
    const html = F.page(b, 'Image crops & photo treatments', `<main class="bd">${head('Photography', 'Crops & treatments', [`${ctx.maskList.length} masks · ${dna.imagery && dna.imagery.crop || 'rect'} default crop at ${C.crop}° · ${(dna.imagery || {}).treatments ? dna.imagery.treatments.join(' / ') : ''}`, `SOURCE/CSS/${p}-graphics.css · PHOTOGRAPHY/filters.svg`, `Direction: ${(dna.imagery || {}).direction || ''}`])}
      <section class="sec"><p class="${p}-eyebrow">01</p><h2 class="${p}-h2">Image masks</h2><div class="mg">${maskTiles}</div></section>
      <section class="sec"><p class="${p}-eyebrow">02</p><h2 class="${p}-h2">Photo treatments</h2><div class="tg">${treats}</div></section>
      <section class="sec"><p class="${p}-eyebrow">03</p><h2 class="${p}-h2">Text on images</h2><div class="sg">${scr}</div></section>
      <section class="sec"><p class="${p}-eyebrow">04</p><h2 class="${p}-h2">Placeholders</h2><div class="pg2">${phs}</div></section>
      <footer class="bd-foot"><div>${lab('Placeholders are abstract compositions — replace with real, consented photography (PHOTOGRAPHY/README.md).')}</div><div>${sample}</div></footer></main>`, at, { head: `<link rel="stylesheet" href="${b.rel(at, 'SOURCE/CSS/' + p + '-graphics.css')}"><style>${css}</style>` });
    const hp = b.path(at, 'crops-overview.html'); F.write(hp, html);
    ctx.shots.push({ in: hp, out: b.path(at, 'crops-overview.png'), w: 2400, h: 900, full: true, wait: 500 });
  }
}
module.exports = { run };
