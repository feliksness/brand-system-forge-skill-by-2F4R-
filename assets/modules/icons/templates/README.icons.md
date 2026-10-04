# {{BRAND}} — Icons

{{COUNT}} icons in {{SETCOUNT}} sets, drawn for {{BRAND}} from the design DNA: **{{STROKE}} px stroke on a 24 px grid · {{CAPS}} · {{JOINS}} · {{CORNERS}} · {{CURVES}}**.
Every icon is defined once as geometry (lines, arcs, circles, rects with corner roles) and rendered in this brand's style —
it is not a generic icon font recoloured.

Gallery: [`index.html`](index.html) (search, set filter, size, outline/duotone, light/dark, click to copy SVG) ·
specimen: [`previews/icons-overview.png`](previews/icons-overview.png) · one sheet per set: `previews/sheet-<set>.png`.

## What is here

| Path | What |
|---|---|
| `SVG/<set>/<name>.svg` | outline icons, `currentColor`, 24 × 24 — the masters |
| `SVG-DUOTONE/<set>/<name>.svg` | duotone variant: the same outline over a tint layer (`currentColor` at 22 %) |
| `sprite.svg` | all icons as `<symbol id="{{p}}-i-<name>">` (duotone: `{{p}}-i-<name>--duotone`) |
| `index.html` | gallery (works offline from file://) |
| `previews/` | `icons-overview.png`, `sheet-<set>.png` and their HTML sources |
| `qa.json` | automatic checks: ink inside the 2 px padding, visual weight outliers, grid snapping, missing content icons |
| `../SOURCE/JS/{{p}}-icons.js` | runtime: `{{G}}.icon()`, `<{{p}}-icon>`, `[data-{{p}}-icon]` |
| `../SOURCE/JSON/icons.json` | metadata for other tools: name, set, label, keywords, aliases, file, inner SVG |

## Sets in this brand

| Set | Name | Icons | Why |
|---|---|---|---|
{{SETROWS}}

`ui` and `core` are always included; the other sets come from the company profile (`{{PROFILE}}` → `icons`).
Icons referenced by `content.json` (`"icon": "…"`) are always included, even when their set is not: {{EXTRAS}}.
Unresolved content icon keys: {{MISSING}}.

## Use

**JavaScript (recommended)** — classic script, file:// safe:

```html
<script src="../SOURCE/JS/{{p}}-icons.js"></script>
<script>
  el.innerHTML = {{G}}.icon('arrow-right');                         // decorative (aria-hidden)
  btn.innerHTML = {{G}}.icon('search', { size: 20, label: 'Search' }); // standalone, announced
  {{G}}.icon('heart', { variant: 'duotone', tint: 'var(--color-brand-primary)', tintOpacity: .4 });
</script>
<{{p}}-icon name="calendar" size="20"></{{p}}-icon>
<span data-{{p}}-icon="pin" data-size="16"></span>
```

Options: `size` (24) · `label` · `title` · `strokeWidth` ({{STROKE}}) · `variant` `outline`|`duotone` · `tint` · `tintOpacity` · `className` · `optical` (true).
Helpers: `{{G}}.icons.has(name)`, `.resolve(name)` (aliases → canonical), `.list(set)`, `.meta`, `.sets`, `.aliases`, `.style`, `.hydrate(root)`.
Unknown names return `''` and warn once in the console — test with `{{G}}.icons.has()` before relying on an alias.

**Sprite** — inline `sprite.svg` once (it is `display:none`), then
`<svg class="{{p}}-icon" width="24" height="24" aria-hidden="true"><use href="#{{p}}-i-mail"/></svg>`.

**Files** — `<img src="ICONS/SVG/core/mail.svg" alt="Email" width="24" height="24">` (an `<img>` cannot inherit `currentColor`;
inline the SVG when the icon must take the text colour). Design tools: import the SVG folder; strokes stay live
(`stroke-width {{STROKE}}`, `stroke-linecap {{CAP}}`, `stroke-linejoin {{JOIN}}`) — outline them only for final artwork.

## Sizes

| Size | Use | Stroke |
|---|---|---|
| 16 px | dense UI, inline with small text | optical: the JS raises the stroke to ≈ 1.3 rendered px (max × 1.35) |
| 20 px | buttons, inputs, navigation | optical |
| 24 px | default | {{STROKE}} |
| 32–48 px | feature lists, cards, empty states | {{STROKE}} (scales with the drawing) |
| ≥ 64 px | illustrations, signage — use the duotone variant or a brand graphic instead of blowing up UI icons |

Align icons to text by their 24 px box (the drawings are optically centred inside it). Keep the same size within a row.

## Accessibility

- Decorative icon next to a visible label → `aria-hidden="true"` (the default of `{{G}}.icon()` without `label`).
- Icon-only control → put the name on the control: `<button aria-label="Close">` + decorative icon, or `{{G}}.icon('close', {label: 'Close'})`.
- Meaning never by colour or icon alone: status icons (`info`, `success`, `warning`, `error`) always come with text.
- Contrast: icons that carry meaning need 3:1 against their background (WCAG 1.4.11) — use the text colour tokens.
- Tap targets around icon buttons ≥ 44 × 44 px even when the icon is 16–24 px.

## Rules of the drawing (so additions match)

- 24 × 24 grid, **2 px padding** — ink inside 2…22 (live area 20). Keylines: circle Ø 20, square 18, portrait 16 × 20, landscape 20 × 16.
- Centre-lines on the 0.25 grid; horizontals/verticals on whole or half units (crisp at 24 and 48 px).
- One stroke weight; no fills except dots, small solid details and the duotone tint.
- Corners carry roles: container corners (`'c'`), shape corners (`'s<n>'`), minor (`'m'`), always sharp (`'x'`). The DNA turns them into
  {{CORNERS}}.
- Check at 16 px (the set sheets show a 16 px row) and against the padding (`qa.json → overflow`).

## Add or change icons

- **Library icons** (all brands): edit `assets/modules/icons/icons_def.py` in the brand-system-forge skill and rebuild.
- **Brand-only icons**: create `SOURCE/CONFIG/icons-custom.json` in this repository —
  `{"icons": [{"name": "kiln", "set": "core", "keywords": "oven fire", "aliases": [], "prims": [["R", 4, 6, 16, 14], ["L", 4, 10, 20, 10], ["C", 12, 15, 2.5], ["PL", [8, 6], [8, 3, "m"], [16, 3, "m"], [16, 6]]]}]}`
  (primitives: `L`, `PL`, `PG`, `R`, `C`, `E`, `A`, `D`, `P` — see the module README). Custom icons here: {{CUSTOM}}.
- Rebuild: `python3 assets/modules/icons/build.py --repo <this repo>` (from the skill) — idempotent; it rewrites `ICONS/`,
  `SOURCE/JS/{{p}}-icons.js` and `SOURCE/JSON/icons.json`. `--all` includes every set; `--sets a,b` overrides the profile.

Generated by brand-system-forge · icons module v{{VERSION}}. Duotone preview tint: `{{TINT}}`.
