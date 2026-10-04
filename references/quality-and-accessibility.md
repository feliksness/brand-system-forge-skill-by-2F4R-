# Quality bar, visual QA and accessibility

## The bar
"Presented to a demanding international design studio": coherent, distinctive, scalable, professional, memorable, accessible,
technically organised, beautiful and practical. It should look as if the company already has a mature identity — and as if it
could only belong to this company (the logo's geometry visibly drives everything).

## Avoid (generic AI aesthetics)
random gradients · blobs without a reason · glass everywhere · neon · generic 3D objects · purple-blue hero · cream + serif +
terracotta by default · near-black with one acid accent · default system/overused fonts · emoji section markers · everything
centred · rounded cards with shadows everywhere · overuse of the primary colour · decorative numbering that encodes nothing ·
lorem ipsum · stock handshakes and fake smiles.

## Do
- One idea per composition; one dominant brand-colour element.
- Editorial confidence: strong type scale, asymmetric splits, real white space, aligned to the grid.
- Vary rhythm across a series (feed, deck, posters): photo / big type / data / mark graphic / quote / announcement.
- Images cropped with the DNA crop; placeholders honest and labelled.
- Copy: plain, specific, active; dates like "21 Nov 2026".

## Visual QA procedure
1. Render (`forge_lib.shots()` / `scripts/shots.js`, fonts ready; emulate reduced motion for pages with reveals).
2. LOOK at the PNG (Read tool): full page downscaled, then 100 % crops of dense areas.
3. Check: overflow/clipping · collisions · orphan headings · widows in display type · fallback fonts/tofu · small-text contrast ·
   grid alignment · consistent corners/angles · logo per rules · sample labels · facts vs spec · weekdays vs dates.
4. Fix → re-render → look again (two passes on flagship outputs: home page, brand book cover, logo sheet).
5. Motion: the final frame equals the untouched logo; reduced motion shows the final state.

## Automated checks
```bash
python3 scripts/validate_repo.py <repo> --fix   # junk, empty files/folders, bad JSON/SVG (unescaped &), TODO/lorem, missing READMEs
python3 scripts/check_links.py <repo>           # broken relative references in HTML/CSS/SVG/MD
python3 tests/run_tests.py --out /tmp/forge-test   # (skill development) all test brands
```
Facts sweep before packaging: counts, sizes, colours and names quoted in READMEs / brand book / website must match the data.

## Accessibility (WCAG 2.2 AA minimum)

| Area | Rule | Enforced by |
|---|---|---|
| Contrast | text ≥ 4.5:1 (large 3:1) on background, alternate backgrounds and cards; UI/focus ≥ 3:1; primary text ≥ 7:1 where possible | `build_tokens.py` auto-fix + `COLORS/contrast-report.json` |
| Brand colour on buttons | on-brand text ≥ 4.5:1; darker button shade derived if needed (graphics keep the original) | build_tokens |
| Error ≠ brand | distinct hue; icon + text, never colour alone | semantic tokens, UI kit |
| Focus | always visible (`--focus-ring`); clip-path shapes keep focus on an unclipped layer | core.css, UI kit |
| Targets | ≥ 44 × 44 px | UI kit |
| Type | body ≥ 17 px / 1.6, measure ≤ 68ch; display/special fonts never for body | tokens |
| Motion | `prefers-reduced-motion`: no parallax/assembly/auto-loops, final state visible without JS | core.css, motion |
| Transparency / contrast modes | `prefers-reduced-transparency`, `prefers-contrast: more`, `[data-theme="contrast"]`, `forced-colors` | core.css, tokens, UI kit |
| Semantics & keyboard | landmarks, one h1, heading order, labels, skip link, focus trap + Esc in dialogs, APG patterns | UI kit, website |
| Images | meaningful alt text; decorative graphics `aria-hidden` | all modules |
| Language | `lang` on every page and on mixed-language spans | all HTML |
| Data viz | text alternatives / data tables, direct labels, not colour alone | charts |
| Physical | signage letter height ≈ 25 mm per 10 m; glass manifestation; step-free routes | events/environment |

Testing: keyboard-only pass, zoom 200 %, reduced-motion and forced-colours emulation, no horizontal scroll at 390 px.
