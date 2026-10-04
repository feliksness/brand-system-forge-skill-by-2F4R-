---
name: brand-system-forge
description: Build a complete visual identity and design-system repository from a company's existing logo and an overview of the company — logo system, colour, typography, tokens, icons, patterns, UI kit, motion, data viz, social, slides, print, events, website, brand book — for ANY company type (non-profit, SaaS, consultancy, retail, restaurant, clinic, school, industrial) and any logo type (symbol, combination, wordmark, emblem). Use this skill whenever someone gives a logo and asks for a brand identity, brand guidelines, brand book, design system, visual identity, rebrand rollout, brand assets or "everything designed around this logo", or names this skill or repository — even if they only ask for part of it (e.g. "make social templates and a website that match our logo"). Delivers the result as small zip parts plus merge commands.
---

# Brand System Forge

Turn **a logo + a company overview** into a studio-grade brand repository. The logo is measured, not guessed: its type,
geometry, colours and angles become a **design DNA** that drives every corner radius, pattern, icon stroke, crop and motion
curve. A **company-type profile** decides what gets made and what things are called. **Modules** generate each area from
that data, so a law firm, a bakery and a kids' club get different, coherent systems from the same machinery.

## What you need
- The logo file (SVG > transparent PNG > large JPG). Never modify it: it stays the primary logo; vectors are faithful rebuilds.
- A company overview (free text or `references/intake-template.md`). Missing facts become labelled sample content.
- Python 3.11+, Node 18+, Chromium via Playwright, npm registry access (fonts). One-time: `bash scripts/setup.sh`.

## Quick start (Lite mode: everything generated, ~20–60 min)
```bash
bash scripts/setup.sh
python3 scripts/new_brand.py --logo /path/logo.png --name "Acme Studio" --profile professional-services \
        --languages en,de --descriptor "Design consultancy" --repo /path/ACME-STUDIO-BRAND
# → replace SAMPLE content in SOURCE/CONFIG/content.json with real content from the overview, review the config, then:
python3 scripts/foundation.py --config /path/ACME-STUDIO-BRAND/SOURCE/CONFIG/brand.config.json --repo /path/ACME-STUDIO-BRAND --skip analyze
python3 scripts/lite.py --repo /path/ACME-STUDIO-BRAND
python3 scripts/split_zip.py /path/ACME-STUDIO-BRAND /path/out --prefix acme-final- --mb 18
```
Profiles: `nonprofit-ngo` · `saas-tech` · `professional-services` · `retail-ecommerce` · `hospitality-food` · `health-wellness` ·
`education-culture` · `industrial-energy` (`references/profiles.md`).

## Workflow (details: `references/workflow.md`)

1. **Intake.** Extract name, legal name, descriptor, languages, profile, audiences, values, real content. Decide; don't
   interrogate. Ask only if the logo is missing/unusable or the company type is truly unclear. Choose **Lite** (fast) or
   **Full** (studio quality: Lite first, then concept + art-directed refinement + specialists).
2. **Analyse the logo** — `analyze_logo.py`. LOOK at `logo-parts.png`; confirm logo type (symbol / combination / wordmark /
   emblem), geometry (angular / orthogonal / round / organic / mixed), complexity (flat / line / faceted / gradient) and route.
   Override wrong guesses in the config. (`references/logo-and-dna.md`)
3. **Draft config + content** — `new_brand.py` (or `auto_config.py`). Rewrite `content.json` from the overview
   (`references/schemas/content.schema.md`). Review palette roles/names, font pairing, wordmark mode (`references/foundations.md`).
4. **Concept** (Full; brief in Lite) — literal description of the logo → brand idea → principle → directions → naming
   (`references/concept.md`). Write `brand_idea`/`principle` into the config.
5. **Foundations** — `foundation.py`: scaffold · analyze · separate · dna · vectorize · mark · fonts · wordmark · tokens ·
   core · board · docs. LOOK at `BRAND-BOOK/foundation-board.png` and `SOURCE/SCRIPTS/_work/mesh/*-compare.png`; iterate.
   Read `SOURCE/CONFIG/design-dna.json` and `production-spec.md` (generated rulebook).
6. **Production** — `lite.py` runs the modules the profile enables, in dependency order (`references/modules.md`). In Full
   mode, then brief specialists per area (`references/specialists.md`), in parallel where you can use sub-agents.
7. **QA** — `validate_repo.py`, `check_links.py`, LOOK at every overview PNG, facts sweep
   (`references/quality-and-accessibility.md`).
8. **Deliver** — `optimize_png.js` → `split_zip.py` (≤ 18 MB parts + manifest) → send every part + merge commands + a short
   summary + client decisions (`references/delivery.md`). If the user asks for a download at any point, ship the current
   state as parts immediately, then continue.

## Modules (status of this version)

| Area | Module | Status |
|---|---|---|
| Logo system: lockups for every logo type, colourways, clear space, sizes, misuse, favicons/app icons, avatars, logo sheet | `logo-system` | ready |
| Icons: 300+ definitions on a 24 grid, drawn with the DNA (stroke, caps, corners), sets per profile, sprite, JS API, gallery | `icons` | ready |
| Patterns, graphic devices, backgrounds, image masks/treatments, photo placeholders, generator | `patterns-graphics` | ready |
| UI kit: DNA-driven components, behaviours, three themes, gallery, React wrapper | `ui-kit` | ready |
| Motion: CSS/JS motion system, logo animations per logo type, transitions, generative tool, optional MP4/GIF | `motion` | ready |
| Charts & infographics (profiles with data) | `charts` | ready |
| Social templates + builder · Presentation (HTML/PDF/PPTX) · Print & documents · Events/merch/environment · Website · Brand book + showcase | — | build with `references/specialists.md` (modules planned; same contract) |

Modules are brand-neutral programs that read the repository (`forge_lib.load()`); never edit generated outputs by hand —
change the config/content/DNA and re-run. To add a module, follow `references/modules.md` §7 and test on the five test brands
(`python3 tests/run_tests.py --out /tmp/forge-test --lite`).

## Non-negotiables
1. **The logo is the source of truth.** Never redraw, recolour arbitrarily or re-typeset lettering that exists in the artwork.
2. **Derive, don't decorate.** Shapes, angles, patterns and motion come from the measured logo (DNA); colours from the artwork;
   words from content.json + profile labels. If a choice can't be traced to the logo, the company or accessibility, drop it.
3. **One system.** Tokens and core CSS are the only source of colour/type/shape; every module uses them.
4. **Accessible by default.** WCAG 2.2 AA contrast (auto-fixed and reported), focus, semantics, reduced motion, `lang`.
5. **Honest content.** Sample text, people, numbers and photos are labelled; no invented partners, prices, Pantone numbers.
6. **Look at everything you make.** Render, open the PNG, fix, re-render. Generated ≠ finished.
7. **Works offline.** HTML runs from `file://` (classic scripts, inline data/SVG, relative links); fonts self-hosted (OFL).
8. **Reproducible.** The repository carries its own generators (`SOURCE/SCRIPTS/forge/`); late fixes propagate by re-running.

## Reference map
| Need | Read |
|---|---|
| Step-by-step workflow, modes | `references/workflow.md` |
| Logo types, vectorisation routes, DNA rules, overrides | `references/logo-and-dna.md` |
| Reviewing palette, fonts, tokens, wordmark | `references/foundations.md` |
| Brand idea, directions, naming | `references/concept.md` |
| Company types and their deliverables | `references/profiles.md` (+ `assets/profiles/*.json`) |
| Module contract, foundation API, catalogue | `references/modules.md` |
| Full-mode specialist briefs (incl. areas without modules) | `references/specialists.md` |
| QA checklist and accessibility table | `references/quality-and-accessibility.md` |
| Zip parts, merge commands, what to send | `references/delivery.md` |
| Known pitfalls | `references/lessons-learned.md` |
| Config / content schemas | `references/schemas/*.md`, examples in `assets/templates/` |
| Repository layout | `references/repo-structure.md` |
| Company overview form | `references/intake-template.md` |

## Assets
`assets/profiles/` (8 profiles) · `assets/modules/` (production modules) · `assets/starter/` (core CSS + mark renderer templates) ·
`assets/fonts-catalogue.json` (72 open-source families with roles, tags, scripts) · `assets/templates/` (example config/content) ·
`tests/` (fictional test logos + brands + regression runner).
