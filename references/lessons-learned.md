# Lessons learned (each one cost time once)

## Files and browsers
- **file://**: ES modules and `fetch()` of local files fail → ship data as `window.X = {…}` classic scripts; external SVG sprites
  (`<use href="file.svg#id">`) and external SVG filters don't render → inline them or use a JS icon map.
- **CSS `url()` inside custom properties** resolves relative to the stylesheet that uses it → pass full paths or set inline.
- **Fonts**: wait for `document.fonts.ready` before every screenshot/PDF. Fontsource subsets may lack arrows/symbols (→ ≥ ≤ ●) →
  draw them as icons. Chromium embeds variable fonts in PDFs as Type 3 → instance static fonts (`scripts/make_static_fonts.py`).
- **Grain overlays**: multiply/black noise greys the paper colour → use overlay blend; a separate subtle multiply "paper tooth".
- **Reduced motion** resets must not strip designed masks/clip-paths — scope the reset to animation states.
- **Clip-path corners** clip focus outlines and shadows → paint the clipped surface on a pseudo-layer, keep focus on the element.
- **Class-name collisions** between libraries written in parallel → namespace per library (`.p-<module>-*`).
- **Headless Chromium** tries background network calls → launch with `--disable-background-networking` (done in `_pw.js`).

## Geometry and logos
- Topological meshes can leave tiny interior holes; close them by extending a neighbour (part counts stay stable) — never append
  patch parts (counts quoted in docs would all change).
- Spline tracing can drift on long closed curves (rings); compare against the artwork (`pixel_error`) and fall back to polygons.
- Holes in traced shapes need `fill-rule="evenodd"`.
- Lettering in the artwork is traced, never re-typeset; detect the logo type before deciding lockups.
- Dark one-colour logos vanish on dark grounds → lighten for legibility when most of the mark falls under 3:1.
- Hand-drawn "micro" versions usually look worse than a coarser automatic level — try automation first.
- CSS polygon crops give the true angle only on square boxes → compute per aspect ratio.

## Data and content
- Compute weekday labels from dates in code.
- Escape `&`, `<`, `"` in SVG `<title>`/`aria-label` (one unescaped "Restaurant & bakery" invalidated SVGs).
- Never invent Pantone numbers; label sample numbers/people/quotes; keep partners generic; no real people or street names.
- Content written once in `content.json` keeps every channel consistent; labels come from the profile.

## Process
- Deliver a downloadable package early when asked; then continue.
- Uploads > ~25–50 MB fail; ≤ 18 MB parts are reliable. Palette-quantise PNGs before zipping (often −60 %).
- Keep generators for everything; late fixes propagate by re-running, not hand-editing.
- Parallel agents can be cut off by usage limits: design work so a new agent can finish from files already written; ask every
  agent for a short final report with requests for the art director.
- Test on several very different brands — a module that only ever saw one brand is a template, not a system.
