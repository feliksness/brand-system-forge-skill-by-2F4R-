// Resolve Playwright and launch Chromium robustly.
// Order: $PLAYWRIGHT_PATH → local/global 'playwright' → common install paths. If the resolved Playwright cannot find its
// own browser build, fall back to any Chromium found in $PLAYWRIGHT_BROWSERS_PATH / ~/.cache/ms-playwright / $CHROMIUM_PATH.
const fs = require('fs'), path = require('path'), os = require('os');
function candidates() {
  const c = [process.env.PLAYWRIGHT_PATH, 'playwright', '@playwright/test', path.join(__dirname, '..', 'node_modules', 'playwright'),
             process.env.FORGE_NODE_MODULES && path.join(process.env.FORGE_NODE_MODULES, 'playwright'), '/opt/npm-tools/node_modules/playwright'];
  try { c.push(require('child_process').execSync('npm root -g', { stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim() + '/playwright'); } catch (e) {}
  return c.filter(Boolean);
}
function loadPlaywright() {
  for (const t of candidates()) { try { return require(t); } catch (e) {} }
  throw new Error('Playwright not found. Run scripts/setup.sh or set PLAYWRIGHT_PATH to a playwright package.');
}
function findChromium() {
  if (process.env.CHROMIUM_PATH && fs.existsSync(process.env.CHROMIUM_PATH)) return process.env.CHROMIUM_PATH;
  const roots = [process.env.PLAYWRIGHT_BROWSERS_PATH, path.join(os.homedir(), '.cache', 'ms-playwright'), path.join(os.homedir(), 'Library', 'Caches', 'ms-playwright')].filter(Boolean);
  const rel = ['chrome-linux/chrome', 'chrome-linux64/chrome', 'chrome-mac/Chromium.app/Contents/MacOS/Chromium', 'chrome-mac-arm64/Chromium.app/Contents/MacOS/Chromium', 'chrome-win/chrome.exe'];
  for (const r of roots) {
    if (!fs.existsSync(r)) continue;
    const dirs = fs.readdirSync(r).filter(d => /^chromium/.test(d) && !/headless/.test(d)).sort().reverse();
    for (const d of dirs) for (const x of rel) { const p = path.join(r, d, x); if (fs.existsSync(p)) return p; }
    const direct = path.join(r, 'chromium'); if (fs.existsSync(direct) && fs.statSync(direct).isFile()) return direct;
  }
  return null;
}
async function launch(opts = {}) {
  const errs = [];
  opts = { ...opts, args: [...(opts.args || []), '--disable-background-networking', '--disable-component-update', '--no-default-browser-check', '--disable-sync'] };
  for (const t of candidates()) {
    let pw; try { pw = require(t); } catch (e) { continue; }
    try { return await pw.chromium.launch(opts); } catch (e) { errs.push(e.message.split('\n')[0]); }
    const exe = findChromium();
    if (exe) { try { return await pw.chromium.launch({ ...opts, executablePath: exe }); } catch (e) { errs.push(e.message.split('\n')[0]); } }
  }
  throw new Error('Could not launch Chromium. Run `npx playwright install chromium`, or set PLAYWRIGHT_PATH / CHROMIUM_PATH.\n' + errs.join('\n'));
}
module.exports = loadPlaywright; module.exports.loadPlaywright = loadPlaywright; module.exports.launch = launch; module.exports.findChromium = findChromium;
