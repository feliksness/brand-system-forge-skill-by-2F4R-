# Logo analysis, vectorisation and the design DNA

## Contents
1. What the analysis measures
2. Logo types and what each means downstream
3. Vectorisation routes
4. Design DNA rules
5. Overrides and edge cases

---

## 1. What the analysis measures (`scripts/analyze_logo.py`)

| Measure | Use |
|---|---|
| colour clusters (k = 6/10/14, share, OKLCH), effective colours | palette roles, number of trace colours |
| connected components → lettering rows (≥ 3 glyph-like parts on a shared baseline) | logo type, symbol/text boxes |
| colour-layer rows inside one filled shape | emblem detection (badge with lettering inside) |
| outline straight-edge share, interior straightness, edge-angle families | geometry, chamfer/crop angles |
| hull circularity, contour roundness, solidity, true stroke width (skeleton) | round vs organic, line art |
| interior edge density | flat vs faceted vs gradient |
| optical centre | lockup alignment |

Images: `logo-parts.png` (always look), `logo-swatches.png`, `logo-angles.png`, `logo-grid.png`.

## 2. Logo types

| Type | Detection | Mark (`mark.json`) | Lettering | Compact (favicon/avatar) |
|---|---|---|---|---|
| **symbol** | no lettering rows | whole artwork | name is TYPESET in the display font | simplified symbol |
| **combination** | rows + significant non-text parts | the symbol part | TRACED from the artwork (`lettering-original.svg`); original layout recorded (gap, scale, alignment) | simplified symbol |
| **wordmark** | rows are ≥ 80 % of the ink | the lettering itself | it IS the logo | traced first letter (`compact.svg`) |
| **emblem** | lettering inside a frame/badge | the whole emblem, never split | name typeset for horizontal lockups | simplified emblem; frame only below ~24 px |

Never re-typeset lettering that exists in the artwork. The supplied artwork stays the primary logo; vectors are faithful
equivalents for scaling, one-colour use and animation.

## 3. Vectorisation routes

| Route | For | How | Check |
|---|---|---|---|
| `flat-trace` | flat logos, line art, lettering | k-means quantise → vtracer cutout (no overlaps); spline, with automatic polygon fallback when spline fitting drifts | `pixel_error` < 1–2 % |
| `faceted-mesh` | low-poly / faceted / painted geometric art | `facetize.py` (smoothing → SLIC → colour merge) → `topomesh.py` (watertight shared edges, straight facets, colour from the artwork) | `*-compare.png`; tune `thresh` (lower = more facets), `amin`, `tol_in` |
| `gradient-raster` | gradients, illustrations, photos | keep the raster as primary; build a posterised flat trace for one-colour/small uses | is the posterised mark recognisable? |
| `svg-native` | vector input | read paths/polygons directly (flatten transforms first) | — |

Two levels: **master** (detail) and **simplified** (small sizes, one-colour). Holes in a mesh are closed by extending the
neighbour with the longest shared edge so part counts stay stable.

## 4. Design DNA rules (`scripts/derive_dna.py` → `SOURCE/CONFIG/design-dna.json`)

| Geometry | Corners | Strokes | Patterns / motifs | Image crop | Shadows | Motion | Composition |
|---|---|---|---|---|---|---|---|
| angular | cut (chamfer at the measured diagonal) | square caps, mitre joins | shards, chevrons, diagonal bands | angled (steep edge family) | hard offset | snap: cuts/wipes along the angle | diagonal tension |
| orthogonal | square (≤ 2 px) | butt caps, mitre | grid, blocks, stripes, steps | rectangle | flat/borders | slide: modular steps | modular grid |
| round | radii; pill buttons/tags | round caps/joins | orbits, dots, arcs, halos | circle / capsule | soft | glide: scale/rotate from centre | radial, centred |
| organic | large soft radii | round | waves, blobs, flow lines, ripples | organic mask | diffuse | flow: drift, morph, springs | flowing, asymmetric |
| mixed | moderate radii | round joins | lines + dots + arcs | rounded | soft | glide | editorial grid |

Complexity adds: **faceted** → facet fields, crystals (and angular language even with a mixed outline) · **line** → contour
patterns, icon stroke matched to the logo stroke · **gradient/illustrative** → glow fields, mesh gradients.
The profile adds density (airy/balanced/dense → spacing scale), display case (upper/title/sentence), motion energy (durations),
imagery direction and the icon style (outline/duotone).
DNA tokens (radius, cut, angle, border, stroke, shadow, duration, ease) flow into `tokens.css`; `build_core.py` resolves
`.p-shape` (the brand's container corner) and `.p-crop` (the brand's image crop) from it.

## 5. Overrides and edge cases

- `brand.config.json → logo.type | logo.geometry | logo.vectorize.route | logo.vectorize.levels | logo.lettering` override analysis.
- `brand.config.json → dna` deep-merges into the derived DNA (e.g. `{"corner": {"style": "round"}, "motion": {"energy": 0.3}}`). The art director's word is final; record why.
- Script/connected lettering may read as one wide "symbol" → set `logo.type: "wordmark"`.
- Very small artwork (< 800 px) → vectors are the only route to large formats; ask for a better original.
- JPG with background → background removed by colour distance from the corners; check `logo-parts.png`.
- Multi-colour gradient logo: the raster remains primary on screens; one-colour versions use the posterised trace.
