#!/usr/bin/env node
// Batch screenshots / PDFs in ONE Chromium instance (much faster than one launch per file). Waits for fonts.
// usage: node scripts/shots.js jobs.json
//   jobs.json = [{ "in": "page.html", "out": "page.png", "w": 1200, "h": 800, "scale": 1, "transparent": false,
//                  "full": false, "selector": null, "pdf": false, "wait": 300, "reducedMotion": false, "theme": null }]
// "selector": screenshot only that element · "pdf": true → out is a PDF sized w×h px (print backgrounds on).
const path = require('path'), fs = require('fs');
const { launch } = require('./_pw.js');
(async () => {
  const jobs = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const b = await launch(); let n = 0;
  for (const j of jobs) {
    const p = await b.newPage({ viewport: { width: +(j.w || 1280), height: +(j.h || 800) }, deviceScaleFactor: +(j.scale || 1) });
    if (j.reducedMotion || j.theme) await p.emulateMedia({ reducedMotion: j.reducedMotion ? 'reduce' : 'no-preference', colorScheme: j.theme === 'dark' ? 'dark' : 'light' });
    const url = /^(https?|file):/.test(j.in) ? j.in : 'file://' + path.resolve(j.in);
    try {
      await p.goto(url, { waitUntil: 'load' });
      await p.evaluate(() => document.fonts && document.fonts.ready);
      await p.waitForTimeout(j.wait == null ? 250 : j.wait);
      fs.mkdirSync(path.dirname(path.resolve(j.out)), { recursive: true });
      if (j.pdf) await p.pdf({ path: j.out, width: (j.w || 1280) + 'px', height: (j.h || 800) + 'px', printBackground: true, preferCSSPageSize: !!j.cssPage });
      else if (j.selector) await (await p.$(j.selector)).screenshot({ path: j.out, omitBackground: !!j.transparent });
      else await p.screenshot({ path: j.out, omitBackground: !!j.transparent, fullPage: !!j.full });
      n++;
    } catch (e) { console.error('shot failed', j.in, e.message.split('\n')[0]); }
    await p.close();
  }
  await b.close(); console.log(`${n}/${jobs.length} rendered`);
})().catch(e => { console.error(e.message || e); process.exit(1); });
