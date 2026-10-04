# charts — brand-system-forge module

A dependency-free, accessible SVG chart library and infographic blocks, coloured and shaped by the brand.

```bash
node build.js --repo <BRAND-REPO>                # ~8–10 s per brand (5 PNG previews)
node build.js --repo <BRAND-REPO> --no-previews
```

Skips with a message and exit 0 when `profile.modules.charts` is `false` or `profile.dataviz` is empty (e.g. hospitality).

## Outputs (in the brand repo)

| Path | What |
|---|---|
| `SOURCE/JS/<p>-charts.js` | `<G>.charts.bar / line / area / donut / pie / kpi / sparkline / progress / gauge / timeline / table / funnel / process / calendar / map / org / stat / compare`, plus `format()`, `formatDate()`, `colors`, `color(i, theme)`, `cvar(i)` |
| `SOURCE/CSS/<p>-charts.css` | `--<p>-chart-1…n` (categorical), `-seq-*`, `-ord-*`, `-div-*`, ink-on-fill variables — for light, dark (OS + `[data-theme]`) and contrast themes; figure, legend, tooltip, table, KPI, stat styles; entrance motion |
| `SOURCE/JSON/charts.json` | Palette per theme with source colour, snapping method, contrast and adjacent CVD ΔE |
| `DATA-VIZ/index.html` | Demo & documentation: palette, the profile's `dataviz` list first, more chart types, infographic blocks (big numbers from content.json stats, icon if `<G>.icon` exists, comparison bars, process, org chart for nonprofit/professional or when listed); light/dark toggle |
| `DATA-VIZ/rules.md` | Colour order, labelling, accessibility, number/date formatting per language (Intl examples), DNA styling, which chart |
| `DATA-VIZ/previews/` | `overview.png`, `charts-profile.png`, `charts-profile-dark.png`, `charts-more.png`, `infographics.png` |

## How it adapts

- **Colour**: forge categorical order (primary, accent, secondary, ramp steps) via `forge_lib.categorical()`. Each slot is snapped to the nearest documented ramp step (else an OKLCH lightness step of the same hue) that reaches **3:1 on both theme surfaces**; near-duplicates (OKLab ΔE < 11) and near-black series are dropped; slots after the accent are re-ordered to maximise adjacent CVD separation (Machado 2009 protan/deutan). If the accent collapses into the primary under CVD it moves down. A slot still below ΔE 8 against its neighbour gets a 45°/135° hatch; sub-3:1 colours that cannot be snapped are flagged "relief" (labels/table required). Dark theme is computed separately (not a flip).
- **DNA**: bar data-ends by `dna.corner.style` (cut → chamfer at `dna.angles.cut`, round → radius, soft → smaller radius, square); lines straight for angular/orthogonal, monotone-smooth for round/organic/mixed; caps/joins from `dna.stroke`; markers diamond (faceted) / square (cut, square) / circle; donut ends round only with round caps; gauge segmented half-dial for angular/orthogonal, continuous arc otherwise; process chevrons at the cut angle, circles for round/organic, tiles otherwise; map tiles hex or square; calendar cells follow the corner style; KPI/stat numbers use the brand `data-xl` type tokens.
- **Motion** (`dna.motion.character`): snap → bars wipe up (clip), slide → measured stagger, glide → smooth scale, flow → spring; lines draw on; once on first view; none under reduced motion or `?still=1`.
- **Profile**: the demo shows `profile.dataviz` first, in its order; org chart for nonprofit/professional profiles or when listed; labels from `profile.labels` / content.json.
- **Language**: numbers and dates through `Intl` in the page language; chart UI words (Source, Sample data, Data table…) for en/de/fr/es/ru, English otherwise.

## Accessibility

`<figure>`/`<figcaption>`, SVG `role="img"` with `<title>` + generated `<desc>`, data table in `<details>` (or screen-reader only), keyboard exploration (arrows, Home/End, Esc) with a polite live tooltip, direct labels, legend for ≥ 2 series, text in text tokens only, ink computed for text on fills.

## Files

`build.js` · `lib/color.js` (contrast, OKLab/OKLCH, CVD, snapping, palette assembly) · `lib/css.js` · `lib/docs.js` (words, titles, rules.md, README) · `templates/charts.js` (runtime).

## Limits

- The map is a schematic placeholder (tiles), not geography. Org chart handles three levels.
- Brands with one or two hues get 4 categorical slots; beyond that use "Other", small multiples or tables.
- Demo numbers are sample data (labelled everywhere); KPI labels/values come from content.json.
