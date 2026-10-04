# scripts/

Generators and checks used by `SKILL.md`. Paths are arguments; run from anywhere. Install once: `bash scripts/setup.sh`.
Every script documents its arguments in its header (`python3 scripts/<name>.py -h`).

**One command for a new brand**
`new_brand.py` = `analyze_logo.py` → `auto_config.py` → `foundation.py` (→ `lite.py` with `--lite`)

**Foundations** (`foundation.py` runs them in order; `--only` / `--skip` to re-run steps)
`scaffold.py` → `analyze_logo.py` → `separate_lockup.py` → `derive_dna.py` → vectorise (`vectorize/trace_flat.py` |
`vectorize/facetize.py` + `vectorize/topomesh.py`) → `build_mark.py` → `fetch_fonts.py` → `build_wordmark.py` → `build_tokens.py`
→ `build_core.py` → `foundation_board.py` → `build_spec.py` + `build_docs.py`

**Modules** — `lite.py` runs `assets/modules/*` in dependency order for the brand's profile (`--list` shows the plan).
Module helpers: `forge_lib.py`, `forge_lib.js` (load the brand, page wiring, batch rendering), `shots.js` (batch PNG/PDF),
`shot.js` (single render), `_pw.js` (robust Playwright/Chromium launch).

**Helpers** — `colorlib.py` (OKLab/OKLCH, WCAG contrast, ramps, auto-fix) · `contrast.py` · `make_static_fonts.py` (static TTFs for
PDF/Office) · `build_font_catalogue.py` (rebuild `assets/fonts-catalogue.json` from `assets/fonts-seed.txt`).

**QA and delivery** — `validate_repo.py` · `check_links.py` · `optimize_png.js` · `split_zip.py` · `to_artifact_page.py`

`scaffold.py` copies `scripts/` and `assets/` into every brand repository as `SOURCE/SCRIPTS/forge/`, so each brand stays
self-contained and can regenerate itself.
