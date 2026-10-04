# Foundations — reviewing the generated config

`auto_config.py` drafts every value; your job is to judge and refine. Edit `SOURCE/CONFIG/brand.config.json`, then
`python3 scripts/foundation.py --config … --repo … --only fonts,wordmark,tokens,core,board,docs` (or the steps you touched).

## Palette (`palette[]`, `roles`)
- **primary** = the most chromatic significant logo colour · **foundation** = darkest logo colour or a derived ink tinted with
  the primary hue · **paper** = lightest near-white or a derived tinted white · **accent** = most hue-distant logo colour, or a
  derived one when the logo is single-hue · **secondary** = other distinct logo colours.
- Check `palette_notes`: derived colours are marked "Derived (not in the logo)". Keep derivations few and justified.
- If the sampled primary cannot carry white text, `build_tokens.py` derives a button shade and reports an auto-fix — graphics
  keep the original. Prefer tuning the primary between two sampled shades over a big jump.
- Accent: one, used ≤ 10 %. Reject clichés for the category (acid lime for tech, purple-blue gradients for AI…) and say why.
- Error colour must never read as the brand primary (red brands get a magenta-shifted error automatically).
- Rename colours (concept.md §6). Never invent Pantone numbers; CMYK values are conversions to be proofed.

## Type (`fonts.families`, `fonts.stacks`, `wordmark`)
- Picked from `assets/fonts-catalogue.json` (72 OFL families via Fontsource) by profile tags × logo geometry × script coverage.
  Swap freely within the catalogue (`slug`, `package`, `css`, `subsets`); any Fontsource family works if you add its entry.
- Roles: display · sans (body/UI) · mono (labels/data; profiles without mono reuse the sans) · optional hand · local-<script>.
- Coverage: every language must render without tofu. Non-Latin scripts get a `local-<script>` family and are added to the stacks.
- Avoid the overused defaults (`overused: true` in the catalogue) unless the brand truly needs them.
- `wordmark.mode`: `traced` (combination/wordmark — lettering comes from the artwork) or `typeset` (symbol/emblem — the name is set
  in `wordmark.font` with tracking/weight; check kerning on the board). Descriptor and local name are always typeset.

## Type scale
Derived in `build_tokens.py` from the display family (condensed → bigger/tighter, wide → smaller, serif → lighter weight) and
`dna.type_voice.display_case`. Override single styles in `config.type.<style>` (family, weight, size, line_height,
letter_spacing, transform).

## Tokens
Precedence: defaults < DNA tokens < `config.tokens.<group>`. Themes light/dark/contrast are derived from roles + ramps and
auto-fixed to WCAG targets (text 4.5:1 on background, alternate backgrounds and cards; primary text 7:1; focus/borders 3:1).
Read `COLORS/contrast-report.json`; every fix is listed.

## Content
`SOURCE/CONFIG/content.json` (schema: `references/schemas/content.schema.md`). Every module reads it: write it once, well.
Use the profile's labels (Services / Menu / Programmes…). Dates ISO (weekdays are computed). `_sample: true` until real.

## What "done" looks like
The foundation board shows: a vector rebuild indistinguishable from the original at normal size; legible on-dark and
one-colour variants; a compact mark that reads at 16–24 px; a palette with sensible roles and names; three themes passing
contrast; a type pairing that expresses the principle; DNA that obviously comes from the logo.
