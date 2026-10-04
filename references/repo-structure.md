# Brand repository structure

What a run produces (folders appear when the module that owns them runs; the profile decides which items are made).

```
<BRAND>-BRAND/
├── README.md               generated index (start here, palette, contents, regenerate commands)
├── BRAND-BOOK/             foundation-board.(html|png) · brand book (PDF/HTML) · text spine (Full mode)
├── LOGO/                   PNG/<slug>-original-artwork.* (primary, untouched) · SVG/ (symbol variants, logo-original*, compact*) ·
│                           LOCKUPS/ · MONOCHROME/ · FAVICON/ · AVATARS/ · GUIDES/ (clear space, sizes, construction, misuse) · logo-sheet
├── COLORS/                 colors.json · css-variables.css · contrast-report.json
├── ICONS/                  SVG/<set>/ · sprite.svg · index.html · previews/
├── PATTERNS/ · GRAPHICS/ · PHOTOGRAPHY/      tiles, devices, backgrounds, generator, placeholders, crops, direction
├── UI-DESIGN-SYSTEM/       tokens/ (DTCG JSON, CSS, Tailwind preset) · components/ (gallery + previews) · react/
├── MOTION/ · GENERATIVE/   logo animations, transitions, principles, exports · motif tool
├── DATA-VIZ/               chart demo, rules (profiles with dataviz)
├── SOCIAL-MEDIA/ · PRESENTATION/ · PRINT/ · EVENTS/ · MERCH/ · ENVIRONMENT/ · WEBSITE/ · SHOWCASE/   application areas
└── SOURCE/
    ├── CONFIG/             brand.config.json · design-dna.json · profile.json · content.json · production-spec.md
    ├── CSS/                fonts.css · tokens.css · colors.css · <p>-core.css · <p>-<module>.css
    ├── JS/                 mark-data.js · wordmark-data.js · dna-data.js · content-data.js · <p>-mark.js · <p>-<module>.js
    ├── JSON/               mark.json · logo-parts.json · design-tokens.json · wordmark*.json · <module>.json · modules-run.json
    ├── SVG/                lettering-original.svg · wordmark-*.svg · descriptor.svg · monogram*.svg
    ├── FONTS/              self-hosted woff2 + OFL licences
    └── SCRIPTS/            forge/ (copy of the skill's scripts + assets → the repo regenerates itself) · _work/ (analysis, parts, meshes)
```
Regenerate inside a delivered repo: `python3 SOURCE/SCRIPTS/forge/scripts/foundation.py --config SOURCE/CONFIG/brand.config.json --repo .`
then `python3 SOURCE/SCRIPTS/forge/scripts/lite.py --repo .` (run `npm install` in `SOURCE/SCRIPTS/forge` once for Node modules).
