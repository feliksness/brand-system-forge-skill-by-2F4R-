#!/usr/bin/env bash
# brand-system-forge — install everything the tools need. Safe to re-run.
set -e
cd "$(dirname "$0")/.."   # the skill root
echo "→ Python packages"
python3 -m pip install -q -r requirements.txt 2>/dev/null || python3 -m pip install -q --break-system-packages -r requirements.txt
echo "→ Node packages (playwright, sharp, pptxgenjs, docx, pdf-lib)"
if [ -n "$PLAYWRIGHT_PATH" ] && node -e "require(process.env.PLAYWRIGHT_PATH)" 2>/dev/null; then
  echo "  using PLAYWRIGHT_PATH=$PLAYWRIGHT_PATH"; PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm install --silent --no-audit --no-fund --omit=optional || true
else
  npm install --silent --no-audit --no-fund
  # download Chromium only if no browser is preinstalled
  if [ -z "$PLAYWRIGHT_BROWSERS_PATH" ] || [ ! -d "$PLAYWRIGHT_BROWSERS_PATH" ]; then npx playwright install chromium; fi
fi
echo "→ Checks"
python3 -c "import numpy, PIL, scipy, skimage, sklearn, cv2, fontTools, brotli, uharfbuzz, shapely, vtracer; print('  python ok')"
if node -e "require('./scripts/_pw.js').launch().then(b=>{console.log('  chromium launch ok');return b.close()}).catch(e=>{console.error(e.message);process.exit(1)})"; then :; else
  echo "  Chromium did not launch — trying: npx playwright install chromium"; npx playwright install chromium || echo "  → install a browser or set PLAYWRIGHT_PATH / CHROMIUM_PATH"; fi
command -v ffmpeg >/dev/null && echo "  ffmpeg ok (motion exports)" || echo "  ffmpeg missing — needed only for MP4/GIF motion exports"
echo "Done. Next: read SKILL.md"
