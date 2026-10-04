# Workflow — from logo + overview to a delivered brand repository

## Contents
0. Modes and time
1. Intake
2. Analyse the logo
3. Draft config + content
4. Concept (Full mode)
5. Foundations
6. Modules (Lite) / specialists (Full)
7. QA
8. Package and deliver

---

## 0. Modes and time

| Mode | When | What happens | Typical time |
|---|---|---|---|
| **Lite** | "quick", "draft", a small business, limited budget, or the user just wants everything fast | analyse → auto config → foundations → `lite.py` runs every module the profile enables → QA → zip | 20–60 min of agent time |
| **Full** | "best", "studio quality", a flagship identity | Lite first (it is the base), then a concept phase, art-directed refinement of every module's output, specialists for anything without a module, brand book written properly | several hours, parallel sub-agents |

Always start with Lite's foundation steps: they are fast and make every later decision concrete. If unsure, run Lite, show the
user, then upgrade selected areas to Full.

## 1. Intake

Inputs: the **logo file** (vector > PNG with transparency > large JPG) and a **company overview** (free text, or
`references/intake-template.md` filled in). Extract:

- name, legal name, local-language name; descriptor ("Design consultancy"); tagline if any
- company type → one of the 8 profiles (`references/profiles.md`); if two fit, pick the one whose deliverables matter more
- languages (ISO codes; first = primary) → script coverage of fonts
- audiences, values, personality, what it must NOT look like
- real content you can use (services, people, numbers, addresses); everything else becomes clearly labelled sample content

Do not stop to ask questions the overview already answers; make reasonable decisions and record them. Ask only when the
logo is missing/unusable or the company type is genuinely unclear.

## 2. Analyse the logo

```bash
python3 scripts/analyze_logo.py logo.png --out work/analysis
```
Read `logo-analysis.md`, then LOOK at `logo-parts.png` (red = symbol, blue = lettering) and `logo-swatches.png`.
Confirm type / geometry / complexity / route (`references/logo-and-dna.md`). Wrong? Override in the config
(`logo.type`, `logo.geometry`, `logo.vectorize.route`). Note warnings (low resolution, no alpha, script lettering).

## 3. Draft config + content

`scripts/new_brand.py` does steps 2–5 in one go:
```bash
python3 scripts/new_brand.py --logo logo.png --name "Acme Studio" --profile professional-services \
  --languages en,de --descriptor "Design consultancy" --repo ../ACME-STUDIO-BRAND [--content content.json] [--lite]
```
It writes `SOURCE/CONFIG/brand.config.json` (palette roles, fonts, wordmark mode, vectorisation levels) and, without
`--content`, a SAMPLE `content.json` from the profile. **Then replace the sample content with real content from the overview**
(`references/schemas/content.schema.md`): units, offerings, people, stats, events, posts, contact, labels. Keep `_sample: true`
while anything is invented.

Review the config (`references/foundations.md`): rename colours meaningfully, check the font pairing against the brand
personality, set `brand_idea` and `principle` after the concept phase, adjust `dna` overrides if the art direction needs it.

## 4. Concept (Full mode; optional in Lite)

`references/concept.md`: what the logo literally is → brand idea (2–6 words) → principle (X + Y) → 3 directions → the chosen
direction and why → naming (colours, sub-brands). Write it into `brand.config.json` (`brand_idea`, `principle`, palette `name`s)
and BRAND-BOOK notes. Send the user the foundation board + idea in one short message if they are present.

## 5. Foundations

```bash
python3 scripts/foundation.py --config <repo>/SOURCE/CONFIG/brand.config.json --repo <repo>
# re-run single steps after edits:  --only tokens,core,board,docs    or    --only mark,board
```
Steps: scaffold · analyze · separate · dna · vectorize · mark · fonts · wordmark · tokens · core · board · docs.
LOOK at `BRAND-BOOK/foundation-board.png` (logo rebuild vs original, variants, DNA, palette, themes, type) and the
vectorisation comparisons in `SOURCE/SCRIPTS/_work/mesh/*-compare.png`. Fix and re-run until the vector is faithful
(trace `pixel_error` is printed; faceted meshes: tune `thresh`/`amin` per level).

## 6. Modules (Lite) / specialists (Full)

```bash
python3 scripts/lite.py --repo <repo> --list      # the plan for this profile
python3 scripts/lite.py --repo <repo>             # run it (≈ 4–8 min per brand)
```
Modules: `references/modules.md`. In Full mode run them first, then brief specialists (`references/specialists.md`) to
review and push each area beyond the generated base, and to create any deliverable that has no module yet. Parallelise with
sub-agents where available; each agent works in its own folders and ends with a short report (requests to the art director).

## 7. QA

`references/quality-and-accessibility.md`. Minimum: `validate_repo.py`, `check_links.py`, look at every overview/preview PNG,
fix, re-render. Facts consistency sweep (numbers, names, dates).

## 8. Package and deliver

`references/delivery.md`: optimise PNGs → split into ≤ 18 MB zip parts with a manifest → send all parts + the merge commands
+ a short summary + the decisions only the client can make.
