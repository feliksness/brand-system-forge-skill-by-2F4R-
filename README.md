# Brand System Forge

**A Claude skill (and a plain repository) that turns a company's logo + overview into a complete brand system.**
Works for any company type and any logo type. The AI measures the logo, derives a design DNA from it, picks a company profile,
and runs production modules that generate the whole system, then delivers it as small zip parts with merge commands.

## Use it as a skill
- **Claude (Cowork / claude.ai):** install the `brand-system-forge` skill (the zip of this folder), then send a logo +
  company overview and say e.g. "build our full brand system". `START-HERE-PROMPT.md` has a ready message.
- **Claude Code / any agent that can run code:** put this folder where the agent can read it (or a Git repo URL), and give it
  `START-HERE-PROMPT.md` with the logo and the overview. The agent follows `SKILL.md`.

## Use it by hand
```bash
bash scripts/setup.sh
python3 scripts/new_brand.py --logo logo.png --name "Acme Studio" --profile professional-services --languages en --repo ../ACME-STUDIO-BRAND --lite
```
Open `../ACME-STUDIO-BRAND/README.md` and `BRAND-BOOK/foundation-board.png`.

## What it produces
| From the logo | Generated |
|---|---|
| type (symbol / combination / wordmark / emblem), geometry, colours, angles | faithful vector rebuild, symbol variants, compact mark, lockups for that logo type, favicons, avatars, clear-space and misuse guides |
| design DNA (corners, angles, strokes, patterns, crops, motion) | tokens (DTCG / CSS / Tailwind, three WCAG-checked themes), core CSS, icons, patterns and graphics, UI kit, motion and logo animations, charts |
| company profile (8 types) | the right labels, pages, social formats, print/event/merch items, icon sets |
| content.json | one story told consistently across every output |

This version ships six production modules: logo system, icons, patterns and graphics, UI kit, motion and charts. It also ships specialist briefs for social, presentation, print, events/merch/environment, website and the brand book (`references/specialists.md`). Those six areas will become modules too.

## Inside
| Path | What |
|---|---|
| `SKILL.md` | the agent's instructions (workflow, non-negotiables, reference map) |
| `START-HERE-PROMPT.md` | message to send an agent together with the logo and overview |
| `references/` | workflow, logo & DNA, foundations, concept, profiles, modules contract, specialist briefs, QA & accessibility, delivery, lessons, schemas, intake form |
| `scripts/` | analysis, auto-config, foundations, module runner (`lite.py`), shared module library, QA, packaging |
| `assets/` | company profiles, production modules, starter CSS/JS, font catalogue (72 OFL families), example config/content |
| `tests/` | 7 fictional test logos, 5 test brands, `run_tests.py` |

Requirements: Python 3.11+, Node 18+, Chromium (installed by setup), npm registry access for fonts, optional ffmpeg for video.
Fonts are fetched at build time under their own licences (SIL OFL); none are bundled. Generated content is sample content
until replaced.
