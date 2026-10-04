// docs.js — PATTERNS/README.md · GRAPHICS/README.md · PHOTOGRAPHY/README.md (direction) — written from the data.
const path = require('path');

const LIGHT = {
  angular: 'Directional daylight with clear, hard-edged shadows; let architecture and edges draw lines through the frame. Slightly cool, crisp contrast — never crushed blacks.',
  round: 'Soft, even, bright light (overcast daylight or large windows); open shadows and gentle falloff. Calm and optimistic, true skin and material colours.',
  organic: 'Warm natural window light with soft falloff; shallow depth where it helps; textures (hands, materials, surfaces) carry the mood.',
  orthogonal: 'Even, neutral, documentary light; straight verticals, honest colour, clean backgrounds.',
  mixed: 'Natural, honest light; consistent white balance across a set.'
};
const COMP = {
  'diagonal-tension': 'Diagonal tension — lines and subjects on the crop angle; leave a calm field on one side for text.',
  'radial-centred': 'Radial / centred — a clear subject at the optical centre, generous space around it; circles and halos frame it.',
  'flowing-asymmetric': 'Flowing and asymmetric — off-centre subjects, soft leading curves, room to breathe.',
  'grid-modular': 'Modular — straight horizons and verticals that align to the layout grid.'
};
const CONSENT = {
  'education-culture': ['Learners under 18 appear only with written guardian consent (and the learner\'s own assent); record it with the image.', 'Prefer hands, work and process shots over identifiable faces of minors; never publish names with photos of minors.', 'No school uniforms, badges or locations that identify a child\'s whereabouts.'],
  'health-wellness': ['Patients appear only with written, specific consent for each use; patients can withdraw it at any time.', 'Never show identifiable records, screens, wristbands or treatment details.', 'Prefer staff, spaces and care moments; use models only if labelled as such.'],
  'hospitality-food': ['Guests appear only with consent; crowd shots avoid identifiable faces unless released.', 'Food is photographed as served — no inedible styling tricks that misrepresent dishes.', 'Staff photos need staff consent; respect break areas and back-of-house privacy.'],
  'industrial-energy': ['Everyone on site wears the correct PPE in every published frame; safety rules are never staged around.', 'Get site and client permission before shooting; check for confidential equipment, drawings or plates.', 'Show real crews (with consent) — no stock hard hats.'],
  'nonprofit-ngo': ['Consent first: explain use, obtain informed consent in the subject\'s language, and honour refusals.', 'Dignity over pity — no imagery that exploits suffering; subjects are agents, not victims.', 'Protect vulnerable people: blur or omit faces and locations when exposure could harm them.'],
  'professional-services': ['Client people, offices and documents appear only with written permission; no readable screens or papers.', 'Portraits of team members need their consent; refresh when people leave.', 'No stock handshakes or staged meetings.'],
  'retail-ecommerce': ['Products are shown accurately (colour, scale, texture); retouching never changes what the customer receives.', 'Models and customers appear only with releases; disclose paid collaborations.', 'Diverse, real bodies and settings — no misleading context.'],
  'saas-tech': ['Product UI screenshots use sample data only — never real customer data.', 'People at work appear with consent; avoid readable personal information on screens.', 'Abstract 3D/graphic imagery is labelled as illustration where it could be mistaken for product.']
};

function run(ctx) {
  const { b, F, gfx, cw } = ctx, C = gfx.C, dna = b.dna || {}, img = dna.imagery || {}, p = b.p;
  const sample = b.content._sample ? '\n> **Sample content.** Copy used in previews and badges comes from `SOURCE/CONFIG/content.json`, which is still placeholder content. Replace it before publishing.\n' : '';
  const regen = '\n## Regenerate\n```\nnode <skill>/assets/modules/patterns-graphics/build.js --repo .\n```\nThe module rewrites `PATTERNS/{SVG,PNG,previews}`, `GRAPHICS/<families>`, `PHOTOGRAPHY/{placeholders,previews}`, `SOURCE/CSS/' + p + '-graphics.css`, `SOURCE/JS/' + p + '-graphics.js` and `SOURCE/JSON/patterns-graphics.json`. Geometry is seeded from the brand name, so re-runs give identical files. Edit the DNA (`SOURCE/CONFIG/design-dna.json`: `patterns`, `motifs`, `angles`, `corner`, `imagery`) or the palette, then regenerate — do not hand-edit generated files.\n';
  const cwTable = '| Colourway | Ground | Tones t1 · t2 · t3 | Line | Accent |\n|---|---|---|---|---|\n' + Object.keys(cw).map(k => { const c = cw[k]; return `| ${c.label} (\`${k}\`) | ${c.bg} | ${c.t1} · ${c.t2} · ${c.t3} | ${c.line} | ${c.accent} |`; }).join('\n');

  // ---------------------------------------------------------------- PATTERNS
  if (ctx.patterns) {
    const rows = ctx.patterns.map((x, i) => `| ${String(i + 1).padStart(2, '0')} | **${x.title}** (\`${x.key}\`) | ${x.tags} | ${x.derived} | ${x.tile ? x.w + '×' + x.h + ' tile' : 'supergraphic (no repeat)'} |`).join('\n');
    F.write(b.path('PATTERNS', 'README.md'), `# Patterns — ${b.name}

${ctx.patterns.length} patterns in ${Object.keys(cw).length} colourways, generated from the logo and the design DNA (**${C.lang}** language, corner **${C.corner}**, angles cut ${C.cut}° · crop ${C.crop}° · shallow ${C.shallow}°, DNA patterns: ${(dna.patterns || []).join(', ') || '—'}).
Mark-derived patterns (repeat, outline, crop) use the real mark geometry from \`SOURCE/JS/mark-data.js\`${gfx.unit.kind === 'monogram' ? ' — the wordmark repeats as its compact monogram (`LOGO/SVG/compact.svg`)' : ''}.
${sample}
![Pattern system](previews/patterns-overview.png)

| # | Pattern | Family | Derived from | Size |
|---|---|---|---|---|
${rows}

## Files
- \`SVG/<pattern>-<colourway>.svg\` — seamless tile (first element \`<rect id="bg">\` is the ground; delete it for a transparent tile). Repeat at 100 % for the intended scale.
- \`PNG/<pattern>-<colourway>.png\` — 1600×1000 swatch (tile repeated), for slides and quick use.
- \`previews/patterns-overview.png\` — the board above · \`previews/tiling-check.png\` — every tile drawn 3×3 as clipped copies (tick marks = tile edges) to prove the repeat is seamless.

## Colourways
Restrained on purpose: tones t1–t3 sit close to the ground so text can go on a calm panel above; the accent is the one energetic element per tile.

${cwTable}

## Use
- CSS: \`<div class="${p}-pattern ${p}-pattern--${ctx.patterns[0].key}">\` (paper), add \`${p}-pattern--foundation\` or \`${p}-pattern--primary\`; dark theme switches automatically. Scale with \`--${p}-pattern-scale\`. Put text on \`.${p}-pattern-panel\` — never directly on a busy pattern.
- JS: \`${b.G}.gfx.tileSVG('${ctx.patterns[0].key}', 'paper')\` / \`${b.G}.gfx.swatchSVG(key, cw, w, h, {seed})\` from \`SOURCE/JS/${p}-graphics.js\` (same engine as the build).
- One pattern per layout; patterns never touch the logo's clear space; no recolouring outside the colourways.
- The generator (\`GRAPHICS/generator/index.html\`) composes patterns with type and the mark and exports PNG/SVG.
${regen}`);
  }

  // ---------------------------------------------------------------- GRAPHICS
  if (ctx.graphics) {
    const fams = {}; ctx.graphics.forEach(g => (fams[g.family] = fams[g.family] || []).push(g));
    const list = Object.keys(fams).map(f => `### ${f}\n` + fams[f].map(g => `- \`${f}/${g.name}.svg\` — ${g.title.replace(/^.*?—\s*/, '') === g.title ? g.title : g.title}`).join('\n')).join('\n\n');
    F.write(b.path('GRAPHICS', 'README.md'), `# Graphic devices — ${b.name}

${ctx.graphics.length} SVG devices (+ PNG previews) built from the DNA motifs (${(dna.motifs || []).join(', ')}), the mark geometry and the corner grammar (**${C.corner}**${C.corner === 'cut' ? ' at ' + C.cut + '°' : ''}). Strokes follow the DNA (${(dna.stroke || {}).cap || 'round'} caps, ${(dna.stroke || {}).join || 'round'} joins). Text in badges, numbers and quote marks is outlined from the brand fonts, so the SVGs render the same everywhere.
${sample}
![Graphic library](previews/graphics-overview.png)

## Families
${list}

## Generator
\`generator/index.html\` — open from disk (no server). Choose a pattern, colourway, layout, seed, size and headline (from content.json or typed), place the mark, then export PNG or SVG (fonts embedded). The URL hash holds the recipe: same link → same image. Preview: \`previews/generator.png\`.

## Rules
- Devices are built in the paper colourway; on dark grounds use the foundation versions of patterns/backgrounds, or recolour devices only to palette colours (\`COLORS/colors.json\`).
- One accent device per layout; keep backgrounds' calm zone (left / top) for text.
- Never place devices over the mark or inside its clear space; never rebuild the logo from devices — the mark devices (\`mark/\`) are supergraphics, not logos.
${regen}`);
  }

  // ---------------------------------------------------------------- PHOTOGRAPHY
  if (ctx.placeholders) {
    const S = ctx.photoSubjects || { subj: [], qual: [], units: [] };
    const masks = (ctx.maskList || []).map(m => `| \`.${p}-mask${m.cls ? '-' + m.cls : ''}\` | ${m.note} |`).join('\n');
    const tr = (img.treatments || ['natural']).map(t => ({ natural: `- **Natural** (\`.${p}-photo--natural\`) — the house grade for most images.`, duotone: `- **Duotone** (\`.${p}-photo--duotone\`, \`--duotone-brand\`) — foundation shadows to paper or brand-tint highlights; for covers, section openers and mixed-quality image sets. Exact print/SVG filters: \`filters.svg\`.`, tint: `- **Tint** (\`.${p}-photo--tint\`) — primary wash for short display moments; always with a scrim under text.`, grain: `- **Grain** (\`.${p}-photo--grain\`) — subtle texture that unifies documentary images.`, mono: `- **Mono** (\`.${p}-photo--mono\`) — black and white with lifted shadows.` }[t] || `- **${t}**`)).join('\n');
    const avoid = ((b.profile.voice || {}).avoid || []).filter(a => /stock|photo|imag|pity|over|styl|clich/i.test(a));
    const scr = require('./css.js').scrimAlpha(ctx.CORE.util, b.role.foundation || '#111111', (b.theme || {})['text-inverse'] || '#FFFFFF', 4.5);
    F.write(b.path('PHOTOGRAPHY', 'README.md'), `# Photography direction — ${b.name}

Derived from the company profile (**${b.profile.title || b.profile.key || ''}**) and the design DNA (${C.lang} · crop **${img.crop || 'rect'}** at ${C.crop}° · composition ${dna.composition || '—'}).
${sample}
![Crops and treatments](previews/crops-overview.png)

## Subjects
Direction: *${img.direction || (b.profile.dna_bias || {}).imagery || '—'}*.
${S.subj.map(s => `- ${s[0].toUpperCase() + s.slice(1)}`).join('\n')}
${S.units.length ? `\nCover every ${String(b.labels.units || 'unit').toLowerCase()}: ${S.units.join(', ')}.` : ''}

## Light
${LIGHT[C.lang] || LIGHT.mixed}${S.qual.length ? ` Keywords: ${S.qual.join(', ')}.` : ''}

## Composition & crops
${COMP[dna.composition] || COMP['grid-modular']} Default crop: \`.${p}-mask\` (${img.crop || 'rect'}).

| Class | What it does |
|---|---|
${masks}

## Treatments
${tr}
- Treatments are display-time CSS approximations; grade masters once (Lightroom/Capture One) with the same intent.

## Text on images
Use a scrim — \`<span class="${p}-scrim ${p}-scrim--bottom|left|full|angled|radial">\` with content in \`.${p}-photo__content\`. Scrim alpha **${scr}** of the foundation colour keeps text-inverse at ≥ 4.5:1 even over pure white pixels (computed from the palette). Never set small text on an unscrimmed photo; side, angled and radial scrims limit text to the solid half.

## Avoid
${(avoid.length ? avoid : ['stock clichés']).map(a => '- ' + a[0].toUpperCase() + a.slice(1)).join('\n')}
- Heavy filters, fake lens flares, text baked into photographs, AI-generated people presented as real.

## Consent & ethics
${(CONSENT[b.profile.key] || CONSENT['professional-services']).map(c => '- ' + c).join('\n')}
- Keep model/property releases with the image files; caption and credit photographers; write meaningful alt text (decorative images: \`alt=""\`).

## Placeholders
${ctx.placeholders.length} abstract, brand-coloured placeholders (no people, no real places) in common ratios — SVG + PNG in \`placeholders/\`. Each carries a small "PHOTO" label and the suggested subject; replace with real, consented photography.

| File | Ratio | Size | Suggested subject |
|---|---|---|---|
${ctx.placeholders.map(x => `| \`${x.name}\` | ${x.ratio} | ${x.w}×${x.h} | ${x.subject} |`).join('\n')}

## Files
- \`placeholders/*.svg|png\` · \`filters.svg\` (exact duotone/mono SVG filters) · \`previews/crops-overview.png\` (masks, treatments, scrims; \`previews/demo-scene.png\` is a neutral stand-in image used only on that board).
- CSS: \`SOURCE/CSS/${p}-graphics.css\` (masks, treatments, scrims).
${regen}`);
  }
}
module.exports = { run };
