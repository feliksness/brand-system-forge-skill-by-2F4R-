# motion — brand-system-forge module

Turns the design DNA's motion character into a working motion system, logo animations and a generative motif tool.

```bash
node build.js --repo <BRAND-REPO>              # ~10–15 s per brand (pages, runtime, 11 PNG previews)
node build.js --repo <BRAND-REPO> --export     # + MP4/GIF per logo animation (ffmpeg; skipped with a message if missing)
node build.js --repo <BRAND-REPO> --no-previews
node export.js --repo <BRAND-REPO> [--fps 30] [--only assemble,outro] [--bg dark]   # export only
```

Skips (exit 0) when `profile.modules.motion` is `false`.

## Outputs (in the brand repo)

| Path | What |
|---|---|
| `SOURCE/CSS/<p>-motion.css` | Local motion tokens, keyframes, `data-reveal` states (auto/fade/rise/scale/drift/wipe/mask/count/logo), stagger, hover & press classes (`-sweep -press -lift -underline -nudge -zoom`), loader, skeleton, marquee, page-transition layers, reduced-motion & still rules |
| `SOURCE/JS/<p>-motion.js` | `<G>.motion` (tokens, bezier, tween), `.reveal`, `.countUp`, `.marquee`, `.transition` (cover/reveal/frame/bind), `.loader`, `.logoIntro`, `.logoAnimate`, `.logoMotion` (deterministic Scene + concept engine) |
| `MOTION/logo-animation/` | `index.html` gallery + 6 pages (player: replay, scrub, speed, light/dark, loop · keyframes · timing table); `assets/logo-data.js` (logo SVGs per background), `assets/logo-page.js` |
| `MOTION/transitions/` | `index.html` gallery of every primitive; `frames.html` page-transition storyboard |
| `MOTION/principles.md` | Character, derived values, durations table, easing curves with names, vocabulary, do/don't, reduced motion, implementation |
| `MOTION/previews/` | `logo-NN-<concept>.png` (6-frame contact sheet each), `logo-gallery.png`, `transitions.png`, `transition-frames.png` |
| `MOTION/exports/` | MP4 (1280×720) + GIF (640 px) per logo animation, only with `--export` |
| `GENERATIVE/` | `index.html` motif generator (motif · colourway · seed · density · format · play · PNG export), `sheet.html`, `assets/`, `previews/` |

## How it adapts

- **Motion character** (`dna.motion.character`) picks the vocabulary everywhere — *snap*: wipes and travel along `dna.angles.cut`, crisp stops, stepped marquee, angled page wipe; *slide*: masked rises and grid steps, column page transition; *glide*: scale/rotate from centre, radial sweeps and irises, orbit loader; *flow*: drifts, feathered wipes, springs, wave transition. `dna.motion.energy` scales travel (8 + 24e px), stagger (40 + 70e ms) and assemble spread.
- **Tokens**: every duration/easing is `--duration-*` / `--ease-*` (CSS) or the same DNA tokens (JS). Reduced motion → instant final states; designed crops/masks (`.<p>-crop`, `.<p>-mask*`) stay.
- **Imagery crop** (`dna.imagery.crop`) shapes the media reveal mask (angled / rect / circle / organic / rounded). **Shadow style** shapes the lift. **Stroke caps/joins** shape contour draws.
- **Logo type × complexity** chooses the animations (always + end card + loader):
  - symbol, faceted → facets assemble (luminance order), light sweep, contour, symbol + typeset name lockup
  - symbol, flat → build, assemble, contour, lockup · line logos → stroke draw-on first
  - combination → symbol then lettering (signature), assemble + lettering, contour, compact sting
  - wordmark → lettering reveal, letter stagger (glyph clusters from the traced lettering), monogram morph-in (compact mark → its glyph), contour
  - emblem → frame then content (frame parts detected by area; holes get a solid underlay while content arrives), assemble, contour, compact sting
- **Scene engine** reads any logo SVG: groups (`symbol`/`lettering`/`mark`), parts, glyph clusters (x-overlap), counters (perimeter-in-fill test), frames; compound typeset paths are split per glyph. Every concept is a pure function of time; the final frame removes every engine attribute (the exporter verifies it).
- **Generative**: renderers for every DNA pattern family (facets, shards, chevrons, diagonal-bands, stripes, lines, grid, blocks, orbits, dots, arcs, waves, blobs, flow-lines, contours, glow-fields); only the brand's own families are offered; colourways from the palette (paper / foundation / primary / tonal).
- Lettering of symbol lockups comes from `wordmark-data.js` (never re-typeset); the outro uses `content.json` tagline and website, `type_voice.display_case`.

## Files

`build.js` (entry) · `export.js` (Playwright frame capture → ffmpeg) · `lib/css.js` · `lib/transitions.js` · `lib/generative.js` · `lib/docs.js` ·
`templates/motion.js` + `templates/concepts.js` (runtime) · `templates/logo-page.js` · `templates/pages.css` · `templates/generative.js`.

## Limits

- Logo animations treat each SVG shape as a part; gradients/filters inside a logo are kept but not animated separately. Very complex marks (> 300 shapes) animate but storyboards get slower.
- The symbol + name lockup is an animation preview; final lockups belong to the logo-system module.
- The `brand` background (primary field) is not offered for logo animations, because a one-colour reversal can't be split into parts.
- Export needs ffmpeg and takes ~5 s per animation; it is not part of Lite mode.
