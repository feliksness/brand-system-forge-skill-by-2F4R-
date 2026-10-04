# Production modules — contract and catalogue

A **module** turns the foundations of a brand repository into one family of deliverables (icons, UI kit, social…).
Modules are brand-neutral programs: everything brand-specific comes from the repository's data, so the same module
produces a different, coherent result for a law firm, a bakery or a kids' club.

`scripts/lite.py` runs every module the profile enables, in dependency order (**Lite mode**). In **Full mode** the
art director runs the same modules first and then has specialists refine, extend and art-direct the output.

## Contents
1. Folder layout and `module.json`
2. Run contract
3. Inputs — the foundation contract
4. Rules every module follows
5. Shared helpers
6. Catalogue (what each module delivers)
7. Writing a new module

---

## 1. Folder layout and `module.json`

```
assets/modules/<name>/
  module.json          metadata (below)
  build.py | build.js  entry point
  README.md            what it makes, options, how it adapts (DNA / profile / logo type), limits
  templates/ …         any HTML/CSS/JS/SVG templates ({{p}} = CSS prefix, {{G}} = JS global, {{BRAND_NAME}})
  lib/ …               optional helpers
```

```json
{
  "name": "icons",
  "title": "Icon system",
  "version": "1.0.0",
  "description": "One sentence.",
  "depends": [],                       // other modules whose OUTPUTS this one reads (foundations are implicit)
  "order": 20,                         // tie-breaker inside the dependency order (lower first)
  "run": ["python3", "build.py"],      // or ["node", "build.js"]; called with --repo <repo>, cwd = module folder
  "outputs": ["ICONS/", "SOURCE/JS/{p}-icons.js", "SOURCE/JSON/icons.json"],
  "lite": true,                        // part of Lite mode
  "seconds": 20                        // typical run time on one brand
}
```

## 2. Run contract

- Invocation: `<run…> --repo /abs/path/to/BRAND-REPO` with the module folder as cwd. Extra flags are optional and documented in the README.
- **Idempotent**: running twice gives the same result; a module owns its output folders and may rewrite them entirely.
- Never modifies foundation files (`SOURCE/CONFIG/*`, `SOURCE/JSON/mark.json`, tokens, `LOGO/PNG/*original*`). It may ADD `SOURCE/CSS/{p}-<module>.css`, `SOURCE/JS/{p}-<module>.js`, `SOURCE/JSON/<module>.json`.
- Exit code 0 on success; print a one-line summary (`icons: 64 SVG · sprite · 4 previews`).
- Typical budget: under 2 minutes per brand (rendering included). Batch screenshots with `shots()` (one browser).
- If an optional dependency is missing (e.g. no charts module yet), degrade gracefully — never crash.

## 3. Inputs — the foundation contract

All paths are relative to the brand repository. `forge_lib.load(repo)` returns all of this in one object.

| File | What it gives you |
|---|---|
| `SOURCE/CONFIG/brand.config.json` | `brand` (name, legal_name, name_local, descriptor, tagline, languages, primary_language, profile, prefix `p`, global `G`), `palette[]` (key, name, hex, group primary/accent/secondary, role), `roles` (primary, foundation, paper, accent → palette keys), `fonts` (families[] with role/family/slug/subsets, stacks{role: css}), `wordmark`, `logo` |
| `SOURCE/CONFIG/design-dna.json` | `base_language` angular/orthogonal/round/organic/mixed · `corner.style` cut/square/round/soft/rounded (+ `angle_deg`) · `angles` {cut, crop, shallow} · `stroke` {icon_px_at_24, cap, join, rule_px} · `density` · `patterns[]` · `motifs[]` · `motion` {character snap/slide/glide/flow, energy, signature} · `imagery` {crop angled/rect/circle/organic/rounded, direction, treatments} · `composition` · `type_voice` {display_case upper/title/sentence} · `shadow_style` · `tokens` |
| `SOURCE/CONFIG/profile.json` | company type: `labels` (what to call offerings/units/projects…), `voice`, `pages`, `icons` (sets), `social` (formats), `post_types`, `presentation`, `print`, `documents`, `events`, `merch`, `environment`, `dataviz`, `modules` {name: enabled} |
| `SOURCE/CONFIG/content.json` | `brand` (tagline, mission, values[]), `labels`, `contact`, `units[]` (key, name, summary, icon), `offerings[]` (key, name, unit, summary, price?), `projects[]`, `events[]` (date YYYY-MM-DD), `posts[]`, `people[]`, `stats[]`, `testimonials[]`, `faq[]`, `_sample` (true = placeholder content: say so in outputs) |
| `SOURCE/JSON/logo-parts.json` | `logo_type` symbol/combination/wordmark/emblem · `arrangement` horizontal/stacked · `layout` (gap, lettering height, alignment relative to the symbol) · `assets` (paths of logo-original, compact, lettering) |
| `SOURCE/JSON/mark.json` · `SOURCE/JS/mark-data.js` | the mark: viewBox, `optical_center`, `silhouette_d` (even-odd path), `levels.master|simplified` [{id, points | d+tx+ty, color, on_dark, luminance}] → `window.<G>_MARK` |
| `SOURCE/JS/<p>-mark.js` | `<G>.markSVG({level, variant: color/on-dark/brand/tonal-dark/tonal-light/mono/outline/silhouette, color, label, decorative})`, `<G>.wordmarkSVG(name, {color})`, `<G>.rng(seed)`, `<G>.hash()`, `<G>.mix()`, `<G>.reducedMotion()`, `<G>.dna`, custom element `<p-mark>` |
| `SOURCE/JS/wordmark-data.js` | `window.<G>_WORDMARK.items` — `lettering` (traced from the logo, combination/wordmark), `stacked`/`line`/`line_1…` (typeset name, symbol/emblem logos), `monogram`, `descriptor`, `name-local` |
| `SOURCE/JS/dna-data.js` · `content-data.js` | `window.<G>_DNA`, `window.<G>_CONTENT` |
| `LOGO/SVG/*.svg` | `logo-original(-black/-white/-on-dark)`, `compact(-black/-white)`, `symbol(-small/-on-dark/-brand/-black/-white/-solid-primary/-outline/-silhouette/…)` |
| `SOURCE/CSS/<p>-core.css` | imports fonts.css + tokens.css; base, `.p-display-xl … .p-h4 .p-body .p-label .p-eyebrow .p-data .p-quote`, layout `.p-container .p-grid .p-section .p-stack .p-cluster`, shape `.p-shape(-sm/-lg/-xl) .p-crop(-alt) .p-cut* .p-round-* .p-pill .p-stroke`, grounds `.p-primary-field .p-dark-field .p-soft-field .p-grain .p-dotgrid .p-linegrid .p-glass .p-rule .p-annot` |
| `SOURCE/CSS/tokens.css` / `colors.css` | `--color-*` theme tokens (light/dark/contrast via `[data-theme]`), palette `--<p>-<key>`, ramps `--<p>-primary-50…950`, `--font-*`, `--type-<style>-{family,weight,size,line-height,letter-spacing,transform}`, `--space-*`, `--radius-*` (+ `--radius-button/card/input/tag`), `--cut-*`, `--angle-*`, `--border-*`, `--stroke-{icon,cap,join}`, `--shadow-*`, `--blur-*`, `--duration-*`, `--ease-{standard,enter,exit,emphasis}`, `--focus-ring`, grid vars |
| `COLORS/colors.json` | palette with contrast data, ramps, semantic colours, themes (light/dark/contrast token maps) |
| `SOURCE/FONTS/*.woff2` + `SOURCE/CSS/fonts.css` | self-hosted fonts (for PDF/Office use `scripts/make_static_fonts.py` to get static TTFs) |

## 4. Rules every module follows

1. **Brand-neutral code.** No hard-coded colours, fonts, names, copy, languages or prefixes. Colours come from tokens/palette, type from type tokens, shape from the DNA, words from content.json + profile labels. A grep for any test-brand name in a module must return nothing.
2. **Branch on the data, not on taste.** At minimum: `dna.corner.style` (cut → clip-path chamfers at `angles.cut`; round → radii/pills; square; soft), `dna.base_language`/`patterns`/`motifs` (which graphic devices), `dna.motion.character`, `dna.type_voice.display_case`, `logo_type` (lockups, where lettering comes from), `profile.*` lists (which items to make), `langs` (lang attributes, local script font from `fonts['local-<script>']`).
3. **Logo integrity.** Use the generated logo SVGs/`markSVG()`; never redraw, recolour arbitrarily or re-typeset lettering. Respect clear space and minimum sizes from the spec.
4. **Accessibility.** Text pairs from theme tokens (already WCAG-checked); visible focus; semantic HTML; alt/aria; `prefers-reduced-motion`; `lang` per text.
5. **file:// safe.** Classic `<script src>` (no modules, no fetch), inline SVG or same-folder files, relative links. Pages must work offline straight from the unzipped repo.
6. **Sample content is honest.** If `content._sample` is true, outputs that look like real communication carry a small "Sample content" note where appropriate (galleries, READMEs), and never invent real people, partners, prices or claims beyond content.json.
7. **Look at the output.** Every module renders previews (PNG) and the developer/agent inspects them on at least three different test brands before calling it done. Typical failures: text overflow, low contrast on images, lettering collisions, a DNA branch that was never exercised.
8. **Document.** `README.md` in the module and a README in each output folder (what's there, how to edit, how to regenerate).

## 5. Shared helpers

- `scripts/forge_lib.py` / `scripts/forge_lib.js` — `load(repo)`, `page(b, title, body, at)` (full HTML wired to fonts/tokens/core/JS data), `shots(jobs)` (batch PNG/PDF in one browser), `svg(b, name)`, `write()`, `categorical(b)` (data colour order), `esc()`.
  Import from a module: `sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'scripts'))` · `require(path.join(__dirname, '..', '..', '..', 'scripts', 'forge_lib.js'))`.
- `scripts/shots.js` — batch renderer used by `forge_lib.py`. `scripts/shot.js` — single render. `scripts/_pw.js` — robust Playwright/Chromium launch.
- `scripts/colorlib.py` — OKLCH, contrast, ramps, mixing. `scripts/make_static_fonts.py` — static TTFs for PDF/PPTX/DOCX.
- Node packages available after `scripts/setup.sh`: playwright, sharp, pptxgenjs, docx, pdf-lib.
- Test brands: `tests/brands.json` → build them with `python3 tests/run_tests.py --out /tmp/forge-test` (5 fictional brands covering combination/wordmark/emblem/symbol logos; angular/round/organic/faceted DNA; 5 profiles; Latin, Cyrillic and Armenian).

## 6. Catalogue

| Module | Depends | Delivers (adapted per DNA / profile / logo type) |
|---|---|---|
| `logo-system` | — | Lockups for the logo type (original rebuild; horizontal/stacked/vertical alternates for combination; name lockups for symbol/emblem; wordmark + compact for wordmarks) in colour/one-colour/reversed, SVG + PNG; clear-space and minimum-size diagrams; favicon set (ICO, PNG 16–512, apple-touch, maskable, manifest); social avatars; misuse sheet; logo sheet preview; `LOGO/README.md` |
| `icons` | — | Icon set drawn on the DNA grid (stroke, caps, joins, corners) — core UI + the profile's icon sets; SVG files, sprite, `<p>-icons.js` (`<G>.icon(name, {size, label})`), `icons.json`, preview sheets |
| `patterns-graphics` | — | Patterns from the mark geometry and DNA pattern families (SVG tiles + PNG), graphic devices from the DNA motifs (frames, bands, shapes), image crops/masks + photo treatments (duotone/tint), photo placeholders; CSS `<p>-graphics.css`; generator page |
| `ui-kit` | icons | `<p>-ui.css` + `<p>-ui.js`: buttons, links, inputs, selects, checkboxes, radios, switches, tags/badges, cards, navigation (header/footer/tabs/breadcrumbs/pagination), alerts/toasts, modals/drawers, tables, lists, accordions, tooltips, progress, avatars, empty states, forms — all token/DNA-driven, three themes; component gallery `UI-DESIGN-SYSTEM/components/index.html` + previews |
| `motion` | — | Motion principles from DNA character; `<p>-motion.css/.js` (reveals, transitions, reduced motion); logo animation HTML pages (assemble/draw/reveal per logo type and complexity) + optional MP4/GIF export (ffmpeg); transitions; generative tool page |
| `charts` | — | `<p>-charts.js` SVG chart library (bar, line, area, donut, stacked, KPI, sparkline, progress, timeline, table) using `categorical()`; infographic blocks; demo page + previews; skipped when the profile has no dataviz |
| `social` | logo-system, icons, patterns-graphics | Template engine (HTML) for every profile social format × post type, filled from content.json; rendered PNG set; carousel; profile avatars/covers; builder page |
| `presentation` | logo-system, icons, patterns-graphics, charts | HTML slide deck (16:9) with the profile's deck types and 15+ layouts; PDF export; PPTX via pptxgenjs (editable, brand fonts/colours) |
| `print-docs` | logo-system, icons, patterns-graphics | Profile print set (business cards, letterhead, envelope, certificates, posters, flyers, brochures, reports, menus…) as HTML → press PDF (bleed/crop marks) + PNG previews; DOCX templates for documents |
| `events-merch-env` | logo-system, icons, patterns-graphics | Event set (badges, lanyards, roll-ups, backdrops, signage, wayfinding), merch artwork + flat mockups, environmental graphics (storefront, walls, windows, vehicles) — only what the profile lists |
| `website` | ui-kit, icons, logo-system, patterns-graphics, motion | Static multi-page site from profile `pages` + content.json, using the UI kit; responsive, accessible, file:// safe; page previews (desktop + mobile) |
| `brand-book` | everything available | Brand book (HTML → PDF) assembled from what exists: idea, logo, colour, type, DNA/shape grammar, icons, patterns, imagery, motion, data, voice, applications; plus `SHOWCASE/index.html` (single page overview, portable) |

## 7. Writing a new module

Copy the smallest existing module, change `module.json`, read the brand with `forge_lib.load()`, branch on the DNA/profile,
render previews with `shots()`, test on the five test brands, look at the PNGs, write the README. Add the module name to
the profiles that should run it (`assets/profiles/*.json → modules`).
