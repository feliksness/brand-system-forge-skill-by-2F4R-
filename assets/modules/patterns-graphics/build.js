#!/usr/bin/env node
// patterns-graphics — graphic language derived from the logo + design DNA:
// seamless patterns, graphic devices, image masks + photo treatments, photo placeholders, generator, overview boards.
//   node build.js --repo <BRAND-REPO> [--only patterns,graphics,css,photos,generator,boards,docs] [--no-shots]
const fs = require('fs'), path = require('path');
const SKILL = path.join(__dirname, '..', '..', '..');
const F = require(path.join(SKILL, 'scripts', 'forge_lib.js'));
const CORE = require('./lib/graphics-core.js');
const B = require('./lib/brand.js');

const args = process.argv.slice(2), arg = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; };
const repo = arg('--repo'); if (!repo) { console.error('usage: node build.js --repo <BRAND-REPO>'); process.exit(2); }
const only = (arg('--only', '') || '').split(',').filter(Boolean), want = s => !only.length || only.includes(s);
const noShots = args.includes('--no-shots');

function rmrf(p) { if (fs.existsSync(p)) fs.rmSync(p, { recursive: true, force: true }); }

(async () => {
  const t0 = Date.now();
  const b = F.load(repo);
  const { mark, unit } = B.markUnits(b);
  if (!unit) { console.error('patterns-graphics: no mark data (SOURCE/JS/mark-data.js) — run the foundations first'); process.exit(1); }
  const cw = B.colourways(b);
  const gfx = CORE.create({ name: b.name, dna: b.dna, unit, mark, colourways: cw });
  const scratch = B.scratchDir('pg-' + b.p);
  const ctx = { b, F, CORE, B, gfx, cw, mark, unit, scratch, noShots, counts: {}, shots: [], rasters: [], want };

  // outlined glyphs for standalone SVG text (badges, numbers, quotes, placeholder labels)
  if (want('graphics') || want('photos') || want('boards')) ctx.glyphs = require('./lib/text.js').prepare(ctx);

  const stages = [['patterns', './lib/patterns.js'], ['graphics', './lib/devices.js'], ['css', './lib/css.js'], ['photos', './lib/photos.js'],
    ['generator', './lib/generator.js'], ['boards', './lib/boards.js'], ['docs', './lib/docs.js']];
  for (const [name, mod] of stages) {
    if (!want(name)) continue;
    if (!fs.existsSync(path.join(__dirname, mod))) continue;
    await require(mod).run(ctx);
  }
  if (ctx.rasters.length) ctx.counts.png = await B.raster(ctx.rasters);
  if (ctx.shots.length && !noShots) await F.shots(ctx.shots);
  if (ctx.after) for (const fn of ctx.after) await fn();
  rmrf(scratch);
  const c = ctx.counts;
  console.log(`patterns-graphics: ${c.patterns || 0} patterns × ${Object.keys(cw).length} colourways (${c.patternFiles || 0} SVG tiles) · ${c.graphics || 0} graphics · ${c.masks || 0} masks · ${c.placeholders || 0} placeholders · ${c.png || 0} PNG · ${ctx.shots.length} boards · ${((Date.now() - t0) / 1000).toFixed(1)}s`);
})().catch(e => { console.error(e.stack || e); process.exit(1); });
