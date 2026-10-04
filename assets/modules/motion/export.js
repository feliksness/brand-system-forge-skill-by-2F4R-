#!/usr/bin/env node
/* Optional video export for the logo animations (motion module, brand-system-forge).
   node export.js --repo <BRAND-REPO> [--fps 30] [--only assemble,outro] [--bg light|dark]
   Renders every frame deterministically (window.LM_PAGE.renderAt) in headless Chromium and, when ffmpeg is on PATH,
   writes MOTION/exports/<NN-concept>.mp4 (1280×720, H.264) and .gif (640 px, 20 fps). Without ffmpeg it skips with a
   message and exits 0 (Lite mode must never fail). Also verifies that the last frame is the untouched logo. */
'use strict';
const fs = require('fs'), path = require('path'), os = require('os'), { execFileSync, spawnSync } = require('child_process');
const F = require(path.join(__dirname, '..', '..', '..', 'scripts', 'forge_lib.js'));

function hasFfmpeg() { try { return spawnSync('ffmpeg', ['-version'], { stdio: 'ignore' }).status === 0; } catch (e) { return false; } }

async function run(b, C, o) {
  o = o || {};
  if (!hasFfmpeg()) return 'export skipped — ffmpeg not found (install ffmpeg to get MP4/GIF)';
  const LA = b.path('MOTION', 'logo-animation'), OUT = b.path('MOTION', 'exports');
  if (!C) C = fs.readdirSync(LA).filter(f => /^\d\d-.+\.html$/.test(f)).sort().map(f => ({ file: f, concept: f.replace(/^\d\d-|\.html$/g, ''), bg: /outro/.test(f) ? 'dark' : 'light' }));
  if (o.only) C = C.filter(c => o.only.includes(c.concept));
  fs.mkdirSync(OUT, { recursive: true });
  const fps = o.fps || 30, W = 1280, H = 720, br = await F.launch(), done = [], problems = [];
  for (const c of C) {
    const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'forge-motion-'));
    const pg = await br.newPage({ viewport: { width: W, height: H } });
    try {
      await pg.goto('file://' + path.join(LA, c.file) + '?record=1&bg=' + (o.bg || c.bg || 'light'));
      await pg.waitForFunction(() => document.documentElement.hasAttribute('data-ready'), null, { timeout: 15000 });
      const info = await pg.evaluate(() => ({ total: window.LM_PAGE.total(), loop: window.LM_PAGE.loop }));
      const times = [], step = 1000 / fps, end = info.loop ? info.total * 2 : info.total;
      for (let t = 0; t < 300; t += step) times.push(0);
      for (let t = 0; t < end; t += step) times.push(t);
      if (!info.loop) for (let t = 0; t <= 1200; t += step) times.push(info.total);
      let i = 0;
      for (const t of times) { await pg.evaluate(tt => window.LM_PAGE.renderAt(tt), t); await pg.screenshot({ path: path.join(tmp, 'f' + String(i++).padStart(5, '0') + '.png') }); }
      if (!info.loop) { const bad = await pg.evaluate(() => window.LM_PAGE.scene.dirty()); if (bad.length) problems.push(c.file + ': ' + bad.slice(0, 4).join(',')); }
      const base = path.join(OUT, c.file.replace('.html', ''));
      execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', String(fps), '-i', path.join(tmp, 'f%05d.png'), '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', base + '.mp4']);
      const vf = 'fps=20,scale=640:-1:flags=lanczos', pal = path.join(tmp, 'pal.png');
      execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', String(fps), '-i', path.join(tmp, 'f%05d.png'), '-vf', vf + ',palettegen=max_colors=128:stats_mode=diff', pal]);
      execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', String(fps), '-i', path.join(tmp, 'f%05d.png'), '-i', pal, '-lavfi', vf + '[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=4', '-loop', '0', base + '.gif']);
      done.push(c.file.replace('.html', ''));
    } catch (e) { problems.push(c.file + ': ' + e.message.split('\n')[0]); }
    await pg.close(); fs.rmSync(tmp, { recursive: true, force: true });
  }
  await br.close();
  fs.writeFileSync(path.join(OUT, 'README.md'), `# Logo animation exports — ${b.name}\n\nMP4 (1280×720, ${fps} fps, H.264) and GIF (640 px, 20 fps) per logo animation, rendered frame-exact from \`../logo-animation/*.html\`.\nRegenerate: \`node assets/modules/motion/export.js --repo <repo>\` (or \`build.js --export\`). Needs ffmpeg.\n\n${done.map(d => `- \`${d}.mp4\` · \`${d}.gif\``).join('\n')}\n`);
  return `exported ${done.length} MP4 + GIF${problems.length ? ' — problems: ' + problems.join(' | ') : ' (final frames verified)'}`;
}
module.exports = { run };

if (require.main === module) {
  const argv = process.argv.slice(2), arg = k => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : null; };
  const repo = arg('--repo'); if (!repo) { console.error('usage: node export.js --repo <brand-repo> [--fps 30] [--only a,b] [--bg light|dark]'); process.exit(2); }
  const b = F.load(repo);
  if (!fs.existsSync(b.path('MOTION', 'logo-animation'))) { console.log('motion export: run build.js first'); process.exit(0); }
  run(b, null, { fps: +arg('--fps') || 30, only: arg('--only') ? arg('--only').split(',') : null, bg: arg('--bg') })
    .then(m => console.log('motion export: ' + m)).catch(e => { console.log('motion export: skipped — ' + e.message.split('\n')[0]); process.exit(0); });
}
