// text.js — outlined brand type for standalone SVG graphics (fontTools via glyphs.py).
// Roles follow the type tokens: display (numbers, quote marks), label (badges, placeholder captions), sans (badge text).
function prepare(ctx) {
  const { b, B } = ctx;
  const tt = B.typeTokens(b), T = tt.T;
  const ascii = Array.from({ length: 95 }, (_, i) => String.fromCharCode(32 + i)).join('') + '“”‘’«»„—–·•×№°';
  const c = b.content || {}, lab = b.labels || {};
  const words = [b.name, (c.brand || {}).tagline, (b.brand || {}).descriptor, (b.brand || {}).name_local, ...Object.values(lab).filter(v => typeof v === 'string'),
    ...(c.units || []).map(u => u.name), ...(c.offerings || []).map(o => o.name), ...((b.dna.imagery || {}).direction || '').split(',')].filter(Boolean).join(' ');
  const chars = Array.from(new Set((ascii + words + words.toLocaleUpperCase()).split(''))).join('');
  const w = (k, d) => parseInt((T[k] || {}).weight, 10) || d;
  const specs = [
    { key: 'display', role: 'display', wght: w('display-xl', 700), chars },
    { key: 'label', role: 'mono', wght: Math.max(500, w('label', 500)), chars },
    { key: 'sans', role: 'sans', wght: Math.max(600, w('h4', 600)), chars },
    { key: 'quote', role: /--font-([a-z-]+)/.test((T.quote || {}).family || '') ? /--font-([a-z-]+)/.exec(T.quote.family)[1] : 'display', wght: w('quote', 400), chars: '“”‘’«»„"\'' }
  ];
  const G = B.glyphs(b, specs, ctx.scratch);
  const tr = (k, d) => { const v = (T[k] || {})['letter-spacing']; return v && /em/.test(v) ? parseFloat(v) : d; };
  G.meta = {
    labelUpper: ((T.label || {}).transform || 'uppercase') === 'uppercase', labelTracking: tr('label', 0.06),
    displayUpper: ((T['display-xl'] || {}).transform || 'none') === 'uppercase', displayTracking: tr('display-xl', 0),
    eyebrowTracking: tr('eyebrow', 0.12)
  };
  return G;
}
module.exports = { prepare };
