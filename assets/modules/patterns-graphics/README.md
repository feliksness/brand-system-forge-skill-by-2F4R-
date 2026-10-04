# patterns-graphics

The brand's **graphic language**, derived from the logo and the design DNA: seamless patterns, graphic devices,
image crops / masks, photo treatments, photo placeholders + photography direction, an offline generator and
overview boards. Brand-neutral: every shape, angle, colour and word comes from the repository's data.

```
node build.js --repo /abs/path/BRAND-REPO                 # everything (~15–25 s per brand)
node build.js --repo … --only patterns,graphics,css,photos,generator,boards,docs
node build.js --repo … --no-shots                         # skip the HTML board screenshots
```
Needs Node (sharp + playwright from the skill root) and Python 3 + fontTools/brotli (glyph outlining).
Deterministic: all geometry is seeded from the brand name, so re-runs produce identical files.

## Outputs (in the brand repo)
| Path | What |
|---|---|
| `PATTERNS/SVG/<pattern>-<paper\|foundation\|primary>.svg` | 10–14 patterns × 3 colourways, seamless tiles (`<rect id="bg">` = ground) |
| `PATTERNS/PNG/*.png` | 1600×1000 swatches (tile repeated) |
| `PATTERNS/previews/patterns-overview.png` · `tiling-check.png` | board · every tile drawn 3×3 as clipped copies |
| `GRAPHICS/<family>/*.svg + .png` | ~50 devices: frames, corners, bands, dividers, badges/stickers/seal, number blocks, quote marks, arrows, highlights, motif shapes, mark devices, backgrounds (hero 1920×1080 · square 1080 · story 1080×1920 × 3 colourways) |
| `GRAPHICS/generator/index.html` | file:// generator: pattern · colourway · layout · seed · format · scale · headline (from content.json) · mark → PNG/SVG export (fonts embedded), recipe in the URL |
| `GRAPHICS/previews/graphics-overview.png` · `generator.png` | boards |
| `PHOTOGRAPHY/placeholders/*.svg + .png` | 14 abstract brand-coloured placeholders (16:9, 3:2, 4:5, 1:1, 9:16) with "PHOTO" label + suggested subject — no people |
| `PHOTOGRAPHY/README.md` · `filters.svg` · `previews/crops-overview.png` | direction (subjects, light, crops, treatments, text on images, consent) · exact duotone filters · board |
| `SOURCE/CSS/<p>-graphics.css` | pattern grounds, `.<p>-mask-*`, `.<p>-photo--*` treatments, `.<p>-scrim--*` (alpha computed for ≥ 4.5:1) |
| `SOURCE/JS/<p>-graphics.js` | the engine + brand config → `<G>.gfx` (`tileSVG`, `swatchSVG`, `composition`, `motif`, `catalogue`) for any page/module |
| `SOURCE/JSON/patterns-graphics.json` | manifest: colourways, patterns, files (for social / print / website modules) |
| `PATTERNS/README.md` · `GRAPHICS/README.md` · `PHOTOGRAPHY/README.md` | usage docs written from the data |

The module owns those folders' generated sub-folders and rewrites them; it never touches foundation files.

## How it adapts
- **Pattern families** from `dna.patterns` + `dna.complexity` + `dna.base_language`: facets / facet mesh / facet scatter (faceted marks, toned by the mark's own facet luminance) · shards (triangles built from the logo's measured edge-angle families) · chevrons (cut angle) · diagonal bands (crop angle) · angle hatch (shallow angle) · prism (low-poly relief on a cut-angle lattice) · rhombus grid · cut grid · mark lattice (simplified silhouette) · grid / blocks / stripes / steps (orthogonal) · orbits / dots / halftone rings / Truchet arcs / arc rows / halo / rings (round) · waves / wave lines / blobs / terrazzo / flow lines / ripples / contours / seeds (organic) · glow field / mesh gradient (gradient logos) · contours + outline traces (line logos) · lines & dots (mixed) · confetti (high-energy profiles, `dna.motion.energy ≥ 0.5`).
- **Always mark-derived**: mark repeat (rotation per language: angular = shallow angle, round = orbiting steps, organic = drift, emblems/monograms upright; one full-colour mark per tile), mark outline (silhouette echoes; emblems = outlined parts; wordmarks = outlined rows), mark crop (giant tonal supergraphic).
- **Logo type**: symbol/combination use `mark-data.js`; emblems repeat whole (upright, larger); wordmarks repeat as their compact monogram (`LOGO/SVG/compact.svg`) and outline as wordmark rows; the generator places the official mark via `<G>.markSVG()` (color / on-dark / mono, silhouette for wordmarks on primary) on a clear-space plate.
- **Colourways** (paper · foundation · primary) from palette roles + ramps; tones t1–t3 stay close to the ground; accent chosen by contrast; dark tones are neutral-warm; playful profiles get multi-accent.
- **Devices** branch on `dna.corner.style` (cut chamfers at `angles.cut` · round radii/pills · soft squircles · square ticks), `base_language` (band/divider/highlight/arrow families), `dna.motifs` (shape set), `dna.stroke` (caps, joins, weight scaled by energy), `profile` + `content` (badge label, stat sticker, seal text).
- **Compositions** follow `dna.composition` (diagonal-tension · radial-centred · flowing-asymmetric · grid-modular) and the format (landscape / square / portrait); a feathered keep-out mask guarantees nothing sits under the text zone.
- **Masks** follow `dna.imagery.crop` (default `.<p>-mask`), angles, corner style, the mark silhouette (`.<p>-mask-mark`) and, for faceted marks, the largest facet. **Treatments** follow `dna.imagery.treatments`; scrim alpha is solved from the palette.
- **Photography direction** from `dna.imagery.direction`, `profile.voice.avoid`, content units and profile-specific consent rules (education, health, hospitality, industrial, nonprofit, professional services, retail, SaaS).
- Text inside standalone SVGs (badges, numbers, quote marks, placeholder labels) is outlined from the brand fonts (`lib/glyphs.py`, fontTools) — local-script fonts are searched too.

## Files
`build.js` (orchestrates) · `lib/graphics-core.js` (geometry, colourways, patterns, motifs, compositions — shared with the browser) · `lib/brand.js` (foundation reader, glyphs, raster) · `lib/patterns.js` · `lib/devices.js` · `lib/css.js` · `lib/photos.js` · `lib/generator.js` · `lib/boards.js` · `lib/docs.js` · `lib/text.js` · `lib/glyphs.py` · `templates/generator.{html,css,js}`.

## Limits
- Treatment classes are CSS display approximations (exact duotones: `PHOTOGRAPHY/filters.svg`); grading masters is still a human step.
- Pattern selection is capped at 11 DNA/language patterns + 3 mark patterns; reorder or pin a list by editing `dna.patterns`.
- Very complex marks (> ~150 parts) make mark-repeat tiles heavy; the simplified level is used.
- The generator's PNG export rasterises the SVG in the browser (fonts embedded); very large custom sizes (> 6000 px) are refused.
- The crops board uses a neutral synthetic stand-in image (`PHOTOGRAPHY/previews/demo-scene.png`) — no real photography is generated.
