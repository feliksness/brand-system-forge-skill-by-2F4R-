#!/usr/bin/env node
// Screenshot an HTML/SVG/URL with Chromium, after fonts are ready.
// usage: node scripts/shot.js <input.html|svg|url> <out.png> <width> <height> [scale=1] [transparent=0] [fullPage=0]
const path = require('path');
const { launch } = require('./_pw.js');
(async () => {
  const [, , inp, out, w, h, s, tr, full] = process.argv;
  if (!inp || !out) { console.error('usage: shot.js <in> <out.png> <w> <h> [scale] [transparent 0|1] [fullPage 0|1]'); process.exit(1); }
  const b = await launch();
  const p = await b.newPage({ viewport: { width: +(w || 1280), height: +(h || 800) }, deviceScaleFactor: +(s || 1) });
  const url = /^(https?|file):/.test(inp) ? inp : 'file://' + path.resolve(inp);
  await p.goto(url, { waitUntil: 'load' });
  await p.evaluate(() => document.fonts && document.fonts.ready);
  await p.waitForTimeout(400);
  await p.screenshot({ path: out, omitBackground: tr === '1', fullPage: full === '1' });
  await b.close();
})().catch(e => { console.error(e.message || e); process.exit(1); });
