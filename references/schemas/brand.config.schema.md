# brand.config.json — schema (v2)

Lives at `SOURCE/CONFIG/brand.config.json`. Drafted by `scripts/auto_config.py`, reviewed by the art director. Paths are relative
to the config file. Example (fictional): `assets/templates/brand.config.example.json`.

## brand
| Key | Example | Used by |
|---|---|---|
| `name` | "Northwind Studio" | everything |
| `legal_name`, `name_local` | "Northwind Studio GmbH", "" | footers, documents, local lockups |
| `descriptor`, `tagline` | "Design consultancy", "Clear thinking. Measurable results." | lockups, website, social |
| `languages`, `primary_language` | ["en", "de"], "en" | font subsets, `lang` attributes |
| `profile` | "professional-services" | deliverables (copied to `SOURCE/CONFIG/profile.json`) |
| `prefix`, `global` | "ns", "NS" | CSS prefix (`.ns-*`, `ns-core.css`), JS global (`window.NS`) |
| `repo_name`, `mark_noun` | "NORTHWIND-STUDIO-BRAND", "mark" | scaffold, docs |
| `brand_idea`, `principle` | "Two views. One direction.", "PRECISION + WARMTH" | spec, brand book (write after the concept phase) |

## logo
| Key | Notes |
|---|---|
| `artwork` | the original file (never modified) |
| `type`, `geometry`, `complexity` | from the analysis; override when wrong (`symbol`/`combination`/`wordmark`/`emblem`; `angular`/`orthogonal`/`round`/`organic`/`mixed`) |
| `vectorize.route` | `flat-trace` · `faceted-mesh` · `gradient-raster` · `svg-native` |
| `vectorize.levels.{master,simplified}` | flat: `colors` (number or "auto"), `max_colors`, `mode` spline/polygon · faceted: `thresh`, `amin`, `nseg`, `maj`, `tol_in`, `tol_sil`, `snap` |
| `lettering` | trace settings for the lettering/monogram (`colors`, `max_colors`, `mode`) |
| `levels` | written by foundation.py (mesh paths) |
| `on_dark_lift` | optional colour used to lift dark parts on dark grounds |

## colour
- `palette[]`: `{group: primary|accent|secondary, key, name, hex, origin, role}`
- `roles`: `{primary, foundation, paper, accent, primary_ramp, neutral_ramp}` → palette keys
- `ramps` (optional explicit ramps), `semantic` (override success/warning/error/info), `themes.{light,dark,contrast}` (override single tokens)

## fonts
- `families[]`: `{role: display|sans|mono|hand|local-<script>, family, slug, package, css[], subsets[], category, tags, weights, variable}`
- `stacks`: `{role: "CSS font stack"}` · `settings`: `{headline, body}` (font-variation-settings) · `samples`: `{role: text}`

## wordmark
`{mode: traced|typeset, font: {slug, subset, axes}, tracking_em, lines[], line_advance_caps, one_line, monogram,
descriptors: [{name, text, font: {slug, subset, axes}, tracking_em}]}`

## overrides
- `dna`: deep-merged into the derived design DNA (`references/logo-and-dna.md`)
- `tokens.<group>`: space, radius, cut, angle, border, stroke, shadow, blur, opacity, breakpoint, z, duration, ease
- `type.<style>`: `{family, weight, size, line_height, letter_spacing, transform}`
- `content`: path to content.json
