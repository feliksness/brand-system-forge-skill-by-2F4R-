// SOURCE/CSS/<p>-charts.css — chart palette per theme (CSS variables) + figure, marks, motion and table styles.
'use strict';
module.exports = function chartsCSS(b, K) {
  const p = b.p, ch = K.character;
  const vars = (t) => [
    ...t.cat.map((s, i) => `--${p}-chart-${i + 1}: ${s.hex};`),
    ...t.seq.map((h, i) => `--${p}-chart-seq-${i + 1}: ${h};`),
    ...t.ord.map((h, i) => `--${p}-chart-ord-${i + 1}: ${h};`),
    ...t.div.map((h, i) => `--${p}-chart-div-${i + 1}: ${h};`),
    ...t.ordInk.map((h, i) => `--${p}-chart-ord-ink-${i + 1}: ${h};`),
    ...t.seqInk.map((h, i) => `--${p}-chart-seq-ink-${i + 1}: ${h};`),
    `--${p}-chart-ink-1: ${t.ink1};`,
    `--${p}-chart-muted: ${t.muted};`
  ].join('\n  ');
  const enterBar = {
    snap: { from: 'clip-path: inset(100% 0 0 0);', fromH: 'clip-path: inset(0 100% 0 0);', to: 'clip-path: inset(0 0 0 0);', prop: 'clip-path', ease: 'var(--ease-enter)' },
    slide: { from: 'transform: scaleY(0);', fromH: 'transform: scaleX(0);', to: 'transform: none;', prop: 'transform', ease: 'var(--ease-enter)' },
    glide: { from: 'transform: scaleY(0);', fromH: 'transform: scaleX(0);', to: 'transform: none;', prop: 'transform', ease: 'var(--ease-enter)' },
    flow: { from: 'transform: scaleY(0);', fromH: 'transform: scaleX(0);', to: 'transform: none;', prop: 'transform', ease: 'var(--ease-emphasis)' }
  }[ch] || {};
  const stagger = { snap: 40, slide: 90, glide: 60, flow: 70 }[ch] || 60;
  const nodeR = K.corner === 'round' ? 14 : K.corner === 'soft' || K.corner === 'rounded' ? 10 : 0;
  return `/* ==========================================================================
   ${b.name} — ${p}-charts.css   (charts module of brand-system-forge)
   Chart palette per theme (forge categorical order, snapped to ≥ 3:1 on the theme surfaces — see SOURCE/JSON/charts.json),
   sequential / ordinal / diverging ramps, figure layout, marks, tooltip, table, KPI and infographic blocks.
   Entrance motion: ${ch} (${enterBar.prop}); none under reduced motion. Generated — regenerate rather than edit.
   ========================================================================== */
:root, [data-theme="light"] {
  ${vars(K.light)}
  --${p}-chart-surface: var(--color-surface); --${p}-chart-grid: var(--color-border-subtle); --${p}-chart-axis: var(--color-border-strong); --${p}-chart-track: var(--color-surface-sunken);
}
@media (prefers-color-scheme: dark) { :root:not([data-theme]) {
  ${vars(K.dark)}
} }
[data-theme="dark"] {
  ${vars(K.dark)}
}
[data-theme="contrast"] {
  ${vars(K.contrast)}
}
/* ---------------------------------------------------------------- figure */
.${p}-chart { position: relative; margin: 0; color: var(--color-text-primary); font-family: var(--font-sans); min-width: 0; }
.${p}-chart__head { display: flex; flex-direction: column; gap: var(--space-1); margin-bottom: var(--space-4); }
.${p}-chart__eyebrow { font-family: var(--font-mono); font-size: var(--type-eyebrow-size); letter-spacing: var(--type-eyebrow-letter-spacing); text-transform: uppercase; color: var(--color-text-secondary); }
.${p}-chart__title { font-family: var(--font-sans); font-weight: var(--type-h4-weight); font-size: var(--type-h4-size); line-height: var(--type-h4-line-height); letter-spacing: var(--type-h4-letter-spacing); text-wrap: balance; }
.${p}-chart__sub { font-size: var(--type-small-size); color: var(--color-text-secondary); max-width: 60ch; }
.${p}-chart__legend { display: flex; flex-wrap: wrap; gap: var(--space-2) var(--space-5); margin: 0 0 var(--space-3); font-size: var(--type-small-size); color: var(--color-text-secondary); }
.${p}-chart__key { display: inline-flex; align-items: center; gap: var(--space-2); }
.${p}-chart__swatch { width: 12px; height: 12px; border-radius: ${K.corner === 'round' ? '50%' : K.corner === 'soft' || K.corner === 'rounded' ? '3px' : '0'}; flex: none; }
.${p}-chart__swatch.is-line { height: 3px; width: 16px; border-radius: 2px; }
.${p}-chart__swatch.is-hatch { background-image: repeating-linear-gradient(45deg, transparent 0 3px, color-mix(in srgb, var(--${p}-chart-surface) 55%, transparent) 3px 4.5px) !important; }
.${p}-chart__plot { position: relative; width: 100%; }
.${p}-chart__svg { display: block; width: 100%; height: auto; overflow: visible; }
.${p}-chart__svg:focus-visible { outline: 2px solid var(--color-focus); outline-offset: 4px; }
.${p}-chart__foot { display: flex; flex-wrap: wrap; gap: var(--space-2) var(--space-4); align-items: center; margin-top: var(--space-3); font-size: var(--type-caption-size); color: var(--color-text-secondary); }
.${p}-chart__tag { font-family: var(--font-mono); font-size: 0.6875rem; letter-spacing: .06em; text-transform: uppercase; padding: 2px 6px; border: var(--border-hairline) solid var(--color-border); border-radius: var(--radius-tag); color: var(--color-text-secondary); }
.${p}-chart__tip { position: absolute; z-index: 5; pointer-events: none; min-width: 120px; max-width: 240px; padding: var(--space-2) var(--space-3); background: var(--color-surface-inverse); color: var(--color-text-inverse); font-size: var(--type-caption-size); line-height: 1.35; border-radius: var(--radius-sm); box-shadow: var(--shadow-2); }
.${p}-chart__tip strong { display: block; font-weight: 600; margin-bottom: 2px; }
.${p}-chart__tip span { display: flex; align-items: center; gap: 6px; }
.${p}-chart__tip i { width: 8px; height: 8px; display: inline-block; border-radius: ${K.corner === 'round' ? '50%' : '0'}; }
.${p}-chart__tip b { margin-left: auto; font-variant-numeric: tabular-nums; font-weight: 600; }
.${p}-chart__table { margin-top: var(--space-3); font-size: var(--type-small-size); }
.${p}-chart__table summary { cursor: pointer; color: var(--color-text-link); width: max-content; }
.${p}-chart__scroll { overflow-x: auto; }
/* ---------------------------------------------------------------- SVG text (text tokens only — never the data colour) */
.${p}-c-tick { font-family: var(--type-data-family, var(--font-mono)); font-size: 11.5px; fill: var(--color-text-secondary); font-variant-numeric: tabular-nums; letter-spacing: .01em; }
.${p}-c-label { font-family: var(--font-sans); font-size: 13px; fill: var(--color-text-primary); }
.${p}-c-label--strong { font-weight: 600; }
.${p}-c-value { font-family: var(--font-sans); font-size: 13px; font-weight: 600; fill: var(--color-text-primary); font-variant-numeric: tabular-nums; }
.${p}-c-value--lg { font-size: 18px; }
.${p}-c-endname { font-weight: 400; fill: var(--color-text-secondary); }
.${p}-c-big { font-family: var(--type-data-xl-family, var(--font-display)); font-weight: var(--type-data-xl-weight, 600); font-size: 34px; fill: var(--color-text-primary); font-variant-numeric: lining-nums; letter-spacing: var(--type-data-xl-letter-spacing, 0); }
.${p}-c-stepnum { font-family: var(--type-data-family, var(--font-mono)); font-size: 18px; font-weight: 600; fill: var(--color-text-on-brand); }
.${p}-c-daynum { font-family: var(--font-sans); font-size: 12px; fill: var(--color-text-primary); font-variant-numeric: tabular-nums; }
.${p}-c-daynum.is-on, .${p}-c-label.is-on, .${p}-c-tick.is-on { fill: var(--color-text-inverse); }
/* ---------------------------------------------------------------- marks */
.${p}-c-grid { stroke: var(--${p}-chart-grid); stroke-width: 1; shape-rendering: crispEdges; }
.${p}-c-base, .${p}-c-axis { stroke: var(--${p}-chart-axis); stroke-width: 1; shape-rendering: crispEdges; }
.${p}-c-axis { stroke-width: ${K.ruleW}; }
.${p}-c-guide { stroke: var(--color-text-secondary); stroke-width: 1; opacity: 0; pointer-events: none; }
.${p}-c-leader, .${p}-c-link { stroke: var(--color-border-strong); stroke-width: 1; fill: none; }
.${p}-c-today { stroke: var(--color-accent); stroke-width: 2; }
.${p}-c-target { stroke: var(--color-text-primary); stroke-width: 2; }
.${p}-c-track, .${p}-c-gtrack { fill: var(--${p}-chart-track); stroke: var(--${p}-chart-track); }
.${p}-c-gtrack { fill: none; }
.${p}-c-line { stroke-width: 2.25; stroke-linecap: ${K.cap}; stroke-linejoin: ${K.join}; }
.${p}-c-spark-line { stroke: var(--color-text-secondary); stroke-width: 1.75; stroke-linecap: ${K.cap}; stroke-linejoin: ${K.join}; }
.${p}-c-spark-area { fill: var(--color-text-secondary); opacity: .1; }
.${p}-c-dot, .${p}-c-spark-dot { stroke: var(--${p}-chart-surface); stroke-width: 2; paint-order: stroke; }
.${p}-c-node { fill: var(--${p}-chart-surface); stroke: var(--color-border-strong); stroke-width: 1; }
.${p}-c-node.is-lead { fill: var(--color-surface-inverse); stroke: none; }
.${p}-c-cell, .${p}-c-tile { stroke: var(--${p}-chart-surface); stroke-width: 2; }
.${p}-c-slice { stroke: var(--${p}-chart-surface); stroke-width: 2; stroke-linejoin: round; }
.${p}-c-bar, .${p}-c-slice, .${p}-c-cell, .${p}-c-tile, .${p}-c-arc, .${p}-c-step { transition: opacity var(--duration-fast) var(--ease-standard); }
.${p}-chart__svg:hover .${p}-c-bar:not(.is-active), .${p}-chart__svg:focus .${p}-c-bar:not(.is-active) { opacity: .55; }
.${p}-chart__svg:hover:not(:has(.is-active)) .${p}-c-bar { opacity: 1; }
.${p}-c-bar.is-active, .${p}-c-slice.is-active, .${p}-c-arc.is-active, .${p}-c-cell.is-active, .${p}-c-tile.is-active { opacity: 1; }
.${p}-c-cell.is-active, .${p}-c-tile.is-active, .${p}-c-slice.is-active, .${p}-c-cell.is-event { stroke: var(--color-text-primary); }
.${p}-c-spark { display: inline-block; vertical-align: middle; overflow: visible; }
/* ---------------------------------------------------------------- entrance motion (${ch}) */
.${p}-c-bar { transform-box: fill-box; transform-origin: 50% 100%; }
.${p}-c-bar--h { transform-origin: 0 50%; }
.${p}-c-bar--c { transform-origin: 50% 50%; }
.${p}-chart.is-pending .${p}-c-bar:not(.${p}-c-bar--h) { ${enterBar.from} }
.${p}-chart.is-pending .${p}-c-bar--h { ${enterBar.fromH} }
.${p}-chart.is-in .${p}-c-bar { ${enterBar.to} transition: ${enterBar.prop} var(--duration-formation) ${enterBar.ease}, opacity var(--duration-fast) var(--ease-standard); transition-delay: calc(var(--i, 0) * ${stagger}ms), 0ms; }
.${p}-chart.is-pending .${p}-c-line, .${p}-chart.is-pending .${p}-c-arc { stroke-dasharray: 1 1; stroke-dashoffset: 1; }
.${p}-chart.is-in .${p}-c-line, .${p}-chart.is-in .${p}-c-arc { stroke-dasharray: 1 1; stroke-dashoffset: 0; transition: stroke-dashoffset var(--duration-formation) ${ch === 'snap' ? 'var(--ease-enter)' : 'var(--ease-standard)'}; transition-delay: calc(var(--i, 0) * ${stagger * 2}ms); }
.${p}-chart.is-pending .${p}-c-area, .${p}-chart.is-pending .${p}-c-dots, .${p}-chart.is-pending .${p}-c-slice, .${p}-chart.is-pending .${p}-c-cell, .${p}-chart.is-pending .${p}-c-tile, .${p}-chart.is-pending .${p}-c-step, .${p}-chart.is-pending .${p}-c-gseg { opacity: 0; }
.${p}-chart.is-in .${p}-c-area, .${p}-chart.is-in .${p}-c-dots { opacity: 1; transition: opacity var(--duration-slower) var(--ease-standard) var(--duration-slow); }
.${p}-chart.is-in .${p}-c-slice, .${p}-chart.is-in .${p}-c-cell, .${p}-chart.is-in .${p}-c-tile, .${p}-chart.is-in .${p}-c-step, .${p}-chart.is-in .${p}-c-gseg { opacity: 1; transition: opacity var(--duration-slow) var(--ease-standard); transition-delay: calc(var(--i, 0) * ${stagger}ms); }
@media (prefers-reduced-motion: reduce) { .${p}-chart .${p}-c-bar, .${p}-chart .${p}-c-line, .${p}-chart .${p}-c-arc, .${p}-chart .${p}-c-area, .${p}-chart .${p}-c-dots { transition: none !important; transform: none !important; clip-path: none !important; stroke-dashoffset: 0 !important; opacity: 1 !important; } }
/* ---------------------------------------------------------------- table */
.${p}-c-table { width: 100%; border-collapse: collapse; font-size: var(--type-small-size); }
.${p}-c-table th, .${p}-c-table td { padding: var(--space-2) var(--space-3) var(--space-2) 0; border-bottom: var(--border-hairline) solid var(--color-border); text-align: left; vertical-align: middle; }
.${p}-c-table thead th { font-family: var(--font-mono); font-size: var(--type-label-size); font-weight: 500; letter-spacing: var(--type-label-letter-spacing); text-transform: uppercase; color: var(--color-text-secondary); border-bottom-color: var(--color-border-strong); }
.${p}-c-table tbody th { font-weight: 500; }
.${p}-c-table .num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.${p}-c-table--rich td, .${p}-c-table--rich th { padding-block: var(--space-3); }
.${p}-c-cellbar { display: inline-block; width: 72px; height: 8px; background: var(--${p}-chart-track); margin-right: var(--space-3); vertical-align: middle; border-radius: ${K.corner === 'round' ? '4px' : '0'}; overflow: hidden; }
.${p}-c-cellbar > span { display: block; height: 100%; background: var(--${p}-chart-1); }
/* ---------------------------------------------------------------- KPI card + infographic blocks */
.${p}-kpi { display: flex; flex-direction: column; gap: var(--space-2); padding: var(--space-5); background: var(--color-surface); border: var(--border-hairline) solid var(--color-border-subtle); min-width: 0; height: 100%; }
.${p}-kpi__label { margin: 0; font-size: var(--type-small-size); color: var(--color-text-secondary); }
.${p}-kpi__value { margin: 0; display: flex; align-items: baseline; gap: .25em; font-family: var(--type-data-xl-family, var(--font-display)); font-weight: var(--type-data-xl-weight); font-size: clamp(2rem, 3.2vw, 2.75rem); line-height: 1; letter-spacing: var(--type-data-xl-letter-spacing); }
.${p}-kpi__unit { font-family: var(--font-sans); font-size: var(--type-body-size); font-weight: 500; color: var(--color-text-secondary); letter-spacing: 0; }
.${p}-kpi__unit.is-tight { font-family: inherit; font-size: .62em; font-weight: inherit; color: var(--color-text-primary); margin-left: -.18em; }
.${p}-kpi__delta { margin: 0; display: inline-flex; align-items: center; gap: 6px; font-size: var(--type-caption-size); font-weight: 600; font-variant-numeric: tabular-nums; }
.${p}-kpi__delta.is-good { color: var(--color-success); } .${p}-kpi__delta.is-bad { color: var(--color-error); }
.${p}-kpi__spark { margin-top: auto; padding-top: var(--space-2); }
.${p}-kpi__note { margin: 0; font-size: var(--type-caption-size); color: var(--color-text-secondary); display: flex; gap: var(--space-2); align-items: center; flex-wrap: wrap; }
.${p}-stat { display: flex; flex-direction: column; gap: var(--space-2); border-top: ${K.ruleW}px solid var(--color-text-primary); padding-top: var(--space-4); }
.${p}-stat__icon { width: 28px; height: 28px; color: var(--color-text-brand); }
.${p}-stat__icon svg { width: 100%; height: 100%; }
.${p}-stat__value { margin: 0; font-family: var(--type-data-xl-family, var(--font-display)); font-weight: var(--type-data-xl-weight); font-size: clamp(2.75rem, 5.4vw, 4.75rem); line-height: .95; letter-spacing: var(--type-data-xl-letter-spacing); font-variant-numeric: lining-nums; }
.${p}-stat__unit { font-size: .5em; margin-left: .08em; color: var(--color-text-brand); }
.${p}-stat__label { margin: 0; font-size: var(--type-small-size); color: var(--color-text-secondary); max-width: 24ch; }
`;
};
