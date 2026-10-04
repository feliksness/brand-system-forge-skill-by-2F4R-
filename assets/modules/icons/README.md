# icons — icon system module

Draws one brand-neutral **icon definition library** (`icons_def.py`, 308 icons in 33 theme sets) in the brand's design DNA
and ships it in every format other modules need. Icons are defined as geometry on a 24 × 24 grid — lines, polylines,
polygons, rects, circles, ellipses, arcs, quadratic/cubic curves, dots — with **corner roles**, never as fixed SVG art, so
the same definitions become a different, coherent family for every brand.

```
python3 build.py --repo <BRAND-REPO> [--sets core,ui,food] [--all] [--no-previews] [--scale 1.5]
```
Idempotent (owns `ICONS/` and rewrites it), ~10–16 s per brand with previews, < 1 s with `--no-previews`.
Needs Python 3.9+ and shapely (QA only — degrades gracefully without it); previews use `scripts/shots.js` (Playwright).

## Outputs (in the brand repo)

| Path | |
|---|---|
| `ICONS/SVG/<set>/<name>.svg` | outline icons, `currentColor`, live strokes |
| `ICONS/SVG-DUOTONE/<set>/<name>.svg` | duotone variant (tint layer = `currentColor` 22 %) |
| `ICONS/sprite.svg` | `<symbol id="<p>-i-<name>">` + `<p>-i-<name>--duotone` |
| `ICONS/index.html` | gallery: search (names, keywords, aliases), set filter, size slider, outline/duotone, light/dark, click = copy SVG |
| `ICONS/previews/icons-overview.png` | specimen: construction grid + keylines, DNA spec, sizes 16/24/32/48, light/dark/primary grounds, full index |
| `ICONS/previews/sheet-<set>.png` | one sheet per set (48 px grid, 16 px and 24 px rows, duotone, on dark) |
| `ICONS/README.md`, `ICONS/qa.json` | usage/a11y/how to add icons · automatic checks |
| `SOURCE/JS/<p>-icons.js` | runtime (only the brand's sets) |
| `SOURCE/JSON/icons.json` | name, set, label, keywords, aliases, file, inner SVG + style |

## Stable API (other modules rely on it)

```js
<G>.icon(name, { size, label, title, strokeWidth, variant: 'outline'|'duotone', tint, tintOpacity, className, optical })  // → '<svg…>' | ''
<G>.icons.has(name) · .resolve(name) · .list(set) · .meta[name] · .sets · .aliases · .style · .hydrate(root) · .svg(name, opts)
<p-icon name="search" size="20" label="Search"></p-icon>   ·   <span data-<p>-icon="pin" data-size="16"></span>
```
Python modules read `SOURCE/JSON/icons.json` (`icons[].svg` + `attrs.outline`) or the SVG files. Unknown names return `''`;
aliases resolve to canonical names (`x`→`close`, `location`→`pin`, `gear`→`settings`, `fork`→`cutlery`, `move`→`run` …).
Every `"icon"` key used in the profiles' `sample` blocks and in content.json resolves (content icons are always included,
even when their set is not in the profile).

## How it adapts

| Data | Effect |
|---|---|
| `dna.stroke.icon_px_at_24`, `.cap`, `.join` | stroke width, linecap, linejoin of every icon (miterlimit 3) |
| `dna.corner.style` = `cut` | the bottom-right **container corner** of each shape (`'c'` role, true bottom-right corners only — like `.p-shape`) is chamfered at `dna.angles.cut` (60° → legs 1 : 1.73); shape corners (`'s<n>'`) chamfered; minor corners sharp; dots square |
| `round` / `soft` | container corners filleted with a radius from `dna.tokens.radius.md`; shape corners rounded; minor corners eased; dots round |
| `square` | all corners sharp |
| `dna.base_language` = `organic` | soft radii + every joint eased + one **pebble** bottom-right corner (×1.65) — echoes blob/organic crops |
| `dna.complexity` = `faceted` or `facets` in patterns/motifs | arcs, circles and curves become facets (octagonal, 45° steps) |
| `dna.type_voice.display_case` | case of the specimen/gallery headlines |
| profile `icons` | which theme sets are built (core + ui always); content.json `icon` keys pull in single icons |
| palette / theme tokens | gallery & specimen colours, duotone preview tint (primary if it separates from the ink, else accent) |
| fonts | specimen/gallery typography (display, sans, mono roles) |
| logo SVGs | gallery header (light and on-dark versions, never redrawn) |

Verified families (the five test brands, see `preview.jpg`): angular cut (square caps, mitred, 60° chamfer, true arcs) ·
angular faceted (same + facets) · round ×2 (2 px, round caps, rounded corners) · organic (1.75 px, eased joints, pebble corner).

## Library and sets

`ui` (46) · `core` (27) · education, culture, people, time, location, accessibility, health, body, care, communication,
food, drink, dietary, hospitality, industry, energy, logistics, delivery, safety, data, environment, community, business,
finance, legal, commerce, social, product-care, product, devices, security (6–10 each). `python3 icons_def.py` prints counts.

### Primitive grammar (`lib/iconkit.py`)
`L(x1,y1,x2,y2)` · `PL(pts…)` · `PG(pts…)` · `R(x,y,w,h,tag='c')` · `C(cx,cy,r)` · `E(cx,cy,rx,ry,rot)` · `A(cx,cy,r,a0,a1)` (deg, 0 = 3 o'clock,
clockwise) · `D(cx,cy,s)` dot · `P(('M',x,y),('L',x,y,tag),('Q',…),('C',…),('A',cx,cy,r,a0,a1),('EA',…), closed=)` · `FO(p)` fill-only (duotone) ·
`SOLID(p)` · `T(prims, rot, dx, dy, s, flipx, flipy)` · helpers `pin`, `drop`, `heart`, `gear`, `capsule`, `chain`, `wave`, `bumps`, `arrowhead` …
Points take a corner role as third value: `'c'` container · `'s<n>'` shape (radius n) · `'m'` minor · `'x'` always sharp.
The duotone tint uses `fill=True` primitives, or the first closed stroked shape.

### Adding icons
Library: add an `icon(name, set, prims, keywords, aliases)` call (centre-lines in 3…21, quarter grid), run on two DNA families,
check `qa.json` (ink inside the padding, weight outliers, H/V lines on the 0.25 grid). Brand-only icons: `SOURCE/CONFIG/icons-custom.json`
in the brand repo with the same primitives as JSON lists (see ICONS/README.md) — parsed by `iconkit.from_json`.

## Optical rules enforced
2 px padding (ink 2…22, checked with shapely buffers per DNA) · pixel snap: horizontal/vertical straight edges land on the 0.25 grid
after every transform · consistent weight (ink-area outliers reported) · 16 px rendering: the JS/specimen raise the stroke below 20 px
to ≈ 1.3 rendered px (max × 1.35), and every sheet shows a 16 px row.

## Limits
- No platform logos (Instagram, LinkedIn …): use the platforms' official brand assets.
- Faceted rendering polygonises every curve — very small circles become octagons by design.
- Organic brands share the round geometry plus easing/pebble corner; hand-drawn wobble is not simulated.
- Filled ("solid") variant is not generated — duotone is the second style.
