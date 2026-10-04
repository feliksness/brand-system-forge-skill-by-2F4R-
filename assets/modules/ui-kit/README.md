# ui-kit — components, behaviours and gallery

Turns a brand repository's foundations (tokens, colours, design DNA, profile, content, logo) into a complete,
accessible UI component library that looks like *that* brand — not a re-skinned bootstrap.

```
python3 build.py --repo /abs/path/BRAND-REPO            # CSS + JS + gallery + READMEs + 20 PNG previews (~25–40 s)
python3 build.py --repo … --no-shots                     # skip previews (< 1 s)
python3 build.py --repo … --audit                        # + rendered text-contrast audit of the gallery in all three themes
```

Depends on `icons` (reads `SOURCE/JS/<p>-icons.js` → `<G>.icon(name, {size, label})` when present; otherwise the kit uses a
built-in fallback set of ~30 icons drawn with the DNA stroke — width, caps, joins, angular/round frames).

## Outputs (in the brand repo)

| File | What |
|---|---|
| `SOURCE/CSS/<p>-ui.css` | ~110 KB: recipe variables · per-theme colour choices · components · shape layer · motion/motif flavour · scripts · reduced-motion / forced-colours / print |
| `SOURCE/JS/<p>-ui.js` | classic script, no deps: theme switch (persisted, try/catch), mobile menu, tabs, accordion, modal/drawer, tooltip, popover, toasts, dismissible alerts, form validation + error summary, counters, sortable tables, file drop, range, search clear, copy |
| `SOURCE/JSON/ui-kit.json` | recipe summary + component inventory (for website / brand-book modules) |
| `UI-DESIGN-SYSTEM/components/index.html` | gallery + docs: 14 sections, ~45 live examples with code, theme switch, sidebar, mobile menu (+ `gallery.css`) |
| `UI-DESIGN-SYSTEM/components/previews/` | `overview-{light,dark,contrast,mobile}.png` + 8 section crops × light/dark |
| `UI-DESIGN-SYSTEM/components/contrast-report.json` | measured contrast of every button / control state per theme |
| `UI-DESIGN-SYSTEM/react/<Brand>UI.jsx` | Button, Card, Input, Tag, Alert wrappers using the CSS classes |
| `UI-DESIGN-SYSTEM/README.md`, `components/README.md`, `tokens/README.md` (if missing) | docs |

## Components

Buttons (primary / secondary / ghost / link / destructive / inverse · sm / lg / icon / block · loading / disabled) ·
inputs (text, textarea, select, search, input group, checkbox, radio, choice tiles, switch, range, file) with label / hint / error,
form layout, error summary, fieldset · tags, badges, chips · cards (media, stat, profile, offering, event, post, flat, outline, brand,
horizontal) · logo lockup, header, nav, mobile menu, language switcher, tabs (underline / pills / boxed), breadcrumbs, pagination,
stepper, footer, segmented control · alerts, banners, toasts · modal, drawer, tooltip, popover · table (sortable), lists,
description list, stats · accordion · progress, meter, spinner, skeleton · avatar + group, empty state, dividers, kbd / code,
quote / testimonial, pricing / offering block · placeholder art.

## How it adapts

Everything visual is derived in `lib/recipe.py` (theme-independent `--ui-*` variables + per-theme colour choices) and
`lib/flavour.py`; templates only consume variables.

| Input | Branch |
|---|---|
| `dna.corner.style` | **cut** → `templates/shape-cut.css`: the surface is a clip-path *plate* on `::before` (focus outlines and borders stay whole, `drop-shadow()` elevation follows the chamfer), chamfer run `--cut-*` × tan(`dna.angles.cut`), diagonal border edges, hover wipes along the logo angle, a fragment fills the cut corner on card hover, angled indicator ends, parallelogram meters, gradient-cut selected states · **round** → pills (buttons, tags, chips, search, tracks), radius-lg cards, circles · **soft** → large radii, inset media with an organic corner, borderless cards on diffuse shadows · **rounded / square** → radius tokens |
| facets in `dna.patterns`/`motifs` | cut brands get two opposite chamfers (top-left + bottom-right) instead of one |
| `dna.shadow_style` | hard → offset shadows from the token offsets, inked per theme · soft / diffuse → the shadow tokens · flat → borders only; contrast theme → no shadows |
| `dna.motion` | snap (short, press drops 1px, cards step onto a hard shadow) · glide (lift + depth, scale on press; energy ≥ .5 → springy ease) · flow (slow, springy toggles) · slide |
| `dna.density` | control heights, paddings, card / panel padding, header height |
| `dna.type_voice.display_case` + display font category + measured cap widths (woff2) | upper → buttons and titles in the display face in capitals, size scaled by the face's cap width; serif display → editorial card titles; field labels technical (label token) for angular brands, quiet sans otherwise; hero/section titles are capped so the longest word always fits |
| `dna.motifs` family | angular → chevron list markers, angled breadcrumb slashes, shard divider, bar spinner, diagonal-band placeholders · round → dots, chevrons, ring divider, ring spinner, concentric-ring placeholders, pill nav highlight · organic → blob markers, wave divider, soft spinner, blob placeholders, highlighter nav |
| `dna.imagery.crop` | avatar shape (circle / chamfer / squircle) |
| `logo_type` + `arrangement` | header/footer lockup: horizontal combination & wordmark → original artwork (light/on-dark pair); stacked combination → symbol + traced lettering; emblem / symbol → symbol + typeset name line (`wordmark-data.js`); placeholders use the mark silhouette (wordmark logos: the monogram) |
| `profile.labels` / `profile.pages` / `content.json` | nav items, CTAs, card data (offerings, projects, stats, people, events, posts), tabs (units), table, FAQ accordion, pricing (prices only if present), testimonial, contact; `_sample` → "Sample content" notes |
| `brand.languages` / `name_local` / `fonts.local-*` | language switcher with `hreflang`/`lang`, localisation demo with `lang` attributes, relaxed tracking and local script face for non-Latin languages |
| theme colours | per theme, button text per state, destructive, indicator line, checked fill and field border are picked by measured WCAG contrast and written as `var(--color-*)` / `color-mix()` of tokens; a primary that disappears into a dark ground switches to the brand text colour |

## Quality checks built in

- `contrast-report.json` (token-level) and `--audit` (rendered: walks every visible text node, resolves plates/gradients, AA 4.5 / 3.0).
- Previews are rendered with `?preview` (no sticky layers, animations frozen at their end state) — `theme=` URL parameter selects the theme.

## Limits

- Placeholder art stands in for photography; replace with real images (alt text) in production.
- The gallery's UI copy (field labels, alert texts) is English; brand content comes from `content.json`.
- `--audit` ignores text on images and background-image photos; snapshot states of cut brands are resolved through the wipe layer.
- Fallback icons are a compact set; unit/offering icons only look specific once the `icons` module has run.
