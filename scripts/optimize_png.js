#!/usr/bin/env node
// Lossy-palette PNG optimisation (libimagequant via sharp) for previews, mockups, boards and screenshots.
// Typical saving 55–65% with no visible change. Brand masters are skipped (logo exports, favicons, icon SVG folder, fonts/source).
// usage: node tools/optimize_png.js <repo> [quality=90]
const fs = require('fs'), path = require('path');
let sharp; for (const p of [process.env.SHARP_PATH, 'sharp', '/opt/npm-tools/node_modules/sharp']) { try { if (p) { sharp = require(p); break; } } catch (e) {} }
if (!sharp) { console.error('sharp not found: npm i -g sharp (or set SHARP_PATH)'); process.exit(1); }
const root = process.argv[2], Q = +(process.argv[3] || 90);
const SKIP = [/\/LOGO\//, /\/FAVICON\//, /\/ICONS\/SVG\//, /\/SOURCE\//, /original-artwork/];
const files = [];
(function walk(d) { for (const f of fs.readdirSync(d)) { const p = path.join(d, f); const s = fs.statSync(p);
  if (s.isDirectory()) { if (!/node_modules|\.git/.test(f)) walk(p); } else if (p.endsWith('.png') && !SKIP.some(r => r.test(p))) files.push(p); } })(root);
let before = 0, after = 0, idx = 0;
(async () => {
  await Promise.all(Array.from({ length: 6 }, async () => { while (idx < files.length) { const p = files[idx++]; const buf = fs.readFileSync(p); before += buf.length;
    try { const out = await sharp(buf).png({ palette: true, quality: Q, effort: 8, dither: 0.6, compressionLevel: 9 }).toBuffer();
      if (out.length < buf.length * 0.85) { fs.writeFileSync(p, out); after += out.length; } else after += buf.length; } catch (e) { after += buf.length; } } }));
  console.log(`${files.length} PNGs · ${(before / 1048576).toFixed(1)} MB → ${(after / 1048576).toFixed(1)} MB`);
})();
