# logo-system

The complete logo kit of a brand repository, built from its foundations (`LOGO/SVG/*`, `SOURCE/JSON/logo-parts.json`,
`SOURCE/JSON/mark.json`, `SOURCE/JS/wordmark-data.js`, tokens, design DNA). Nothing is redrawn and traced lettering is never re-typeset:
every lockup is composed from the foundation drawings, and every colourway of a lockup shares exactly the same geometry.

```bash
python3 build.py --repo /abs/path/to/BRAND-REPO            # everything (~20–25 s per brand)
python3 build.py --repo … --svg-only                        # SVG / HTML only, no PNG rendering
python3 build.py --repo … --no-sheet                        # skip the logo sheet
```

## What it makes

| Output | Contents |
|---|---|
| `LOGO/LOCKUPS/` | `<slug>-<lockup>-color|on-dark.svg` + `.png` (@1x) + `@2x.png`, transparent |
| `LOGO/MONOCHROME/` | the same lockups in one colour: `foundation`, `white`, `primary` (only when the primary reaches 3 : 1 on paper) |
| `LOGO/PNG/` | `<slug>-<lockup>-color|on-dark-512|1024|2048.png` + square `<slug>-symbol-…-16…1024.png` (wordmark: `<slug>-compact-…`). The original artwork is never touched. |
| `LOGO/GUIDES/` | `clear-space`, `minimum-sizes` (real pixels), `construction` (12-module grid, optical centre, proportions in X), `misuse` (12 don'ts with ✕) — HTML + PNG |
| `LOGO/FAVICON/` | `favicon.ico` (16/32/48), `favicon-16/32/48.png`, `apple-touch-icon.png` (180), `android-chrome-192/512.png` (brand container), `maskable-192/512.png` (80 % safe zone), `icon.svg` (switches to on-dark colours in dark UI), `site.webmanifest`, `head-snippet.html`, SVG masters |
| `LOGO/AVATARS/` | `avatar-paper|primary|foundation` 400 + 1080 px, circle-safe (farthest point of the mark at 62 % of the crop radius) |
| `LOGO/logo-sheet.html/.png` | overview board: primary on light/dark/primary, lockup family, every lockup on dark and on primary, colourways, compact + favicon + app icons + avatars, clear space, real-size minimums, six don'ts |
| `LOGO/README.md` + folder READMEs | file map, lockup table with minimum sizes, construction numbers, clear space, colour/contrast table, favicon snippet, misuse |
| `SOURCE/JSON/logo-system.json` · `SOURCE/JS/<p>-logo-system.js` | index for other modules: lockup files per colourway, recommended file per ground (`light`, `dark`, `primary_field`, `wide`, `square`, `compact`), minimum sizes, clear space, construction |

## How it adapts

**Logo type** (`logo-parts.json → logo_type`)
- *combination* — `primary` = the original arrangement rebuilt at its measured position; alternates keep the measured symbol-to-lettering
  scale and gap: `stacked` (flush left) + `vertical` (optically centred) when the original is horizontal, `horizontal` when it is stacked
  (vertical only if the original is not already centred), `primary-descriptor`, `symbol`, `lettering`. Lettering = the traced group of `logo-original.svg`.
- *symbol / emblem* — lockups from the mark + the typeset name (`wordmark-data.js`): `horizontal` (stacked name), `horizontal-line`,
  `horizontal-descriptor`, `vertical`, `horizontal-<lang>` (local-script name), `symbol`. Mark height from the name block
  (1.4 × block, ≥ 2X; emblems × 1.2; aspect-compensated), gap 0.22 × mark, text block centred on `mark.json → optical_center`.
- *wordmark* — `wordmark`, `wordmark-descriptor` (left-aligned unless the DNA composition is centred), `compact` (traced first letter in a
  container that follows `dna.corner.style`: circle / chamfered square at `corner.angle_deg` / rounded square), `monogram`.

**Colourways** — `on-dark` uses `symbol-on-dark` and turns every lettering colour under 4.5 : 1 on the dark ground into paper; one-colour
marks keep the knock-out lines of `symbol-black|white.svg`; the on-primary version is white or foundation, whichever holds contrast.

**DNA** — panel corners via `<p>-shape`, misuse ✕ badge shape, compact/app-icon container, clear-space texture (hatch at the logo angle for
angular, dots for round, waves for organic), header texture (`<p>-linegrid` / `-dotgrid` / `-grain`), type case via the type tokens.

**Data-driven numbers** — clear space, minimum sizes from `production-spec.md` (fallback 25 % · 48/16 px · 120 px); per-lockup minimum width
keeps the cap height ≥ 6 px and secondary lines ≥ 4 px; app-icon ground = light or dark, whichever gives the compact mark more
area-weighted contrast (from `mark.json` face areas).

## Files

`build.py` (orchestration, exports, icons, index) · `lib/svgkit.py` (SVG geometry: path bboxes, parts, items, lockups, recolouring, id
prefixing) · `lib/logo.py` (parts loader + lockup builders per logo type) · `lib/pages.py` (guides + logo sheet) · `lib/docs.py` (READMEs).

## Limits

- Lettering cap height of traced lettering is measured from the tall glyphs of its largest row; unusual scripts may need a manual check.
- Emblems keep their inner lettering at favicon sizes (simplified drawing); at 16 px it reads as texture.
- Combination alternates never split or re-flow the traced lettering, so a one-line version is only made when the foundation has one.
- The module owns `LOCKUPS/ MONOCHROME/ GUIDES/ FAVICON/ AVATARS/`, the PNG exports listed in `logo-system.json`, `logo-sheet.*` and `LOGO/README.md`; it rewrites them on every run.
