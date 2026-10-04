# Specialists — Full-mode briefs (for sub-agents or for yourself)

In Full mode every area starts from its module's output (if a module exists) and a specialist pushes it to studio quality,
or creates the deliverable from scratch where no module exists yet. Give each specialist: the COMMON part below + its role
section + the brand repository path. Run independent roles in parallel; dependent roles after (order at the end).

## Contents
- COMMON (every specialist)
- Roles: strategy & writing · logo system · icons · graphic language · UI system · motion & generative · data visualisation ·
  social · presentation · print & documents · events, merch & environment · website · brand book · showcase
- Order and hand-offs

---

## COMMON (paste first)

You are a senior designer/engineer at a top branding studio working on **{{BRAND}}** — repo `{{REPO}}`.
1. Read first: `SOURCE/CONFIG/production-spec.md` (the rules), `design-dna.json` (shape language), `profile.json` (what this company
   needs), `content.json` (the words — never invent beyond it), `brand.config.json`; the README of every module that already ran;
   LOOK at `BRAND-BOOK/foundation-board.png` and the overview PNGs of finished areas.
2. Use only the system: tokens (`--color-*`, `--type-*`, `--space-*`, `--radius-*`/`--cut-*`, `--shadow-*`, `--duration-*`/`--ease-*`),
   `<p>-core.css` classes (`.p-shape`, `.p-crop`, type classes), the logo files/`<G>.markSVG()` and lockups from logo-system,
   icons via `<G>.icon()`, patterns/devices from patterns-graphics. Never hard-code colours or fonts, never redraw or re-typeset the logo.
3. Express the DNA visibly (corner style, angles, motifs, composition, motion character) — the output must look like *this* brand,
   not a template. One dominant brand-colour element per composition. Typographic hierarchy, grid alignment, white space.
4. Avoid generic AI aesthetics: random gradients/blobs, glassmorphism everywhere, neon, purple-blue heroes, centred-everything,
   rounded cards with shadows on everything, emoji markers, lorem ipsum, stock clichés.
5. Accessibility (WCAG 2.2 AA), `lang` attributes, reduced motion, file:// safe HTML, kebab-case names, a README per folder.
6. Generate with scripts (kept in your folder or `SOURCE/SCRIPTS/<area>/`) so late fixes propagate by re-running.
7. LOOK at every render (downscaled + 100 % crops), fix, re-render — two passes on flagship pieces.
8. Sample content stays labelled. Compute weekdays from dates. Escape `&` in SVG text. No invented Pantone, partners or people.
9. Finish with a report ≤ 350 words: what you made (counts), decisions, open issues, **requests for the art director**.

## Roles

**Strategy & writing** — `BRAND-BOOK/` text spine: brand overview (story, mission, idea, principle), guidelines summary, voice
(traits, do/don't, examples per channel, language strategy), tagline routes (5–6 with rationale; client decides), naming of
colours/units/patterns, boilerplates (25/50/100 words), content review of `content.json` (replace sample where the overview allows).

**Logo system** (module `logo-system`) — review lockup proportions on real sizes, optical alignment, clear space, minimums; add
special lockups the brand needs (co-branding, sub-brand lockups, local-language lockups, watermark); refine the misuse sheet;
check favicons at 16/32 px on light and dark tabs.

**Icons** (module `icons`) — audit the set against the profile and content; add brand-specific icons (offerings, units) on the
same grid; draw a signature detail from the mark if it helps (used sparingly); unit/sub-brand marks if the brand has units.

**Graphic language** (module `patterns-graphics`) — curate: keep the strongest 8–12 patterns, retire weak ones; design 3–5
signature compositions (hero, square, story) that could only belong to this brand; photography direction with real examples of
crops and treatments; generator presets.

**UI system** (module `ui-kit`) — review states (hover/focus/active/disabled/loading/error), dark and contrast themes, density,
forms and tables with real content; add product-specific components (pricing, booking, menu, course card…); usage docs.

**Motion & generative** (module `motion`) — pick the hero logo animation; tune timing to the DNA character; export MP4/GIF
(ffmpeg); a 5–8 s sting with end card; transitions used by website/social; reduced-motion versions.

**Data visualisation** (module `charts`) — chart rules on real numbers from the overview; one infographic poster/report page;
accessibility (tables, direct labels, patterns).

**Social** *(module planned; build from this brief)* — an HTML template engine for every format in `profile.social` × post type in
`profile.post_types`, filled from content.json; layouts from the DNA composition; rotating colourways; text fitting; 30–60 rendered
PNGs; a 9–12 post feed-grid preview; a builder page (edit text → export PNG); README with formats and safe zones.

**Presentation** *(module planned)* — HTML deck (1920×1080, keyboard nav, print CSS) with 15+ layouts (title, agenda, divider,
statement, text+image, columns, quote, big numbers, chart, timeline, team, offering cards, comparison, full-bleed image, closing);
the profile's main deck type filled from content (12–18 slides); PDF; editable PPTX via pptxgenjs (static fonts, master slide, notes).

**Print & documents** *(module planned)* — every item in `profile.print` as mm-based HTML (@page, 3 mm bleed, crop marks) → print PDF
(static fonts via `scripts/make_static_fonts.py` to avoid Type 3) + digital PDF + PNG preview; `profile.documents` as DOCX templates
(docx npm: styles, header/footer, tables) + PDF samples; README with specs and paper notes.

**Events, merch & environment** *(module planned)* — only the items the profile lists: badges, roll-ups (850×2000), backdrops,
signage/wayfinding (letter height ≈ 25 mm per 10 m viewing distance), screens; merch artwork + clean flat vector mockups (never just a
centred logo); storefront, windows (manifestation band), walls, vehicles, safety signs (ISO 7010 colour logic); dimensioned elevations.

**Website** *(module planned)* — static multi-page site from `profile.pages` + a detail page per offering/project/event/post/person;
uses only the UI kit + graphics + motion; hero type suited to the profile; responsive, accessible, file:// links; theme toggle;
sitemap/robots/404; desktop + mobile previews; check_links clean.

**Brand book** *(module planned)* — HTML → PDF (A4 landscape, 60–110 pages, static fonts, ≤ 20 MB): how to use · story & idea ·
logo (original as primary, vector rebuild, lockups, colourways, sizes, clear space, misuse, favicons) · colour · type · DNA & shape
grammar · graphic language · icons · imagery · motion · data · voice · each application area · accessibility · do/don't (≥ 20 pairs) ·
files & governance. Editorial layout that itself demonstrates the identity; previews + automatic layout QA; facts match the repo.

**Showcase** *(module planned)* — `SHOWCASE/index.html` (+ root `index.html`): one scrolling page presenting the whole system with
live elements (mark variants, palette, type, patterns switcher, icons grid, UI samples, motion, applications), links into every
folder; a portable build (`SHOWCASE/portable/`, all relative) for hosting.

## Order and hand-offs
1. In parallel: strategy & writing · logo system · icons · graphic language · motion · data viz (all only need foundations).
2. Then UI system (needs icons) → in parallel: social · presentation · print & documents · events/merch/environment · website.
3. Then brand book and showcase (need everything). 4. Art director: integrate requests, facts sweep, QA, delivery.
If an agent is interrupted (rate limits), resume it by id or start a new one that finishes from the files already written.
