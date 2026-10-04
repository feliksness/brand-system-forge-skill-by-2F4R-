// MOTION/transitions/index.html (gallery) and frames.html (page-transition storyboard).
'use strict';
const path = require('path');
const F = require(path.join(__dirname, '..', '..', '..', '..', 'scripts', 'forge_lib.js'));
const AT = 'MOTION/transitions';

function curveSVG(bez, label) {
  const m = /cubic-bezier\(([^)]+)\)/.exec(bez || ''); const v = m ? m[1].split(',').map(Number) : [0, 0, 1, 1];
  const W = 120, H = 120, pad = 18, X = x => pad + x * (W - 2 * pad), Y = y => H - pad - y * (H - 2 * pad);
  return `<svg viewBox="0 0 ${W} ${H}" class="tx-curve" role="img" aria-label="${label}: cubic-bezier(${v.join(', ')})"><rect x="${pad}" y="${pad}" width="${W - 2 * pad}" height="${H - 2 * pad}" fill="none" stroke="currentColor" stroke-opacity=".14"/>` +
    `<path d="M${X(0)} ${Y(0)} C${X(v[0])} ${Y(v[1])} ${X(v[2])} ${Y(v[3])} ${X(1)} ${Y(1)}" fill="none" stroke="currentColor" stroke-width="2"/>` +
    `<line x1="${X(0)}" y1="${Y(0)}" x2="${X(v[0])}" y2="${Y(v[1])}" stroke="currentColor" stroke-opacity=".35"/><line x1="${X(1)}" y1="${Y(1)}" x2="${X(v[2])}" y2="${Y(v[3])}" stroke="currentColor" stroke-opacity=".35"/>` +
    `<circle cx="${X(v[0])}" cy="${Y(v[1])}" r="3" fill="currentColor"/><circle cx="${X(v[2])}" cy="${Y(v[3])}" r="3" fill="currentColor"/></svg>`;
}
const PAGE_CSS = p => `<style>
.tx-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: var(--space-5); }
.tx-card { padding: var(--space-6); background: var(--color-surface); border: var(--border-hairline) solid var(--color-border-subtle); min-height: 168px; display: flex; flex-direction: column; justify-content: space-between; gap: var(--space-4); }
.tx-card h3 { margin: 0; }
.tx-card code, .tx-mono { font-family: var(--font-mono); font-size: var(--type-label-size); color: var(--color-text-secondary); }
.tx-bar { height: 10px; background: var(--color-brand-primary); }
.tx-dur { display: grid; grid-template-columns: 9rem 1fr 4.5rem; gap: var(--space-2) var(--space-4); align-items: center; font-size: var(--type-small-size); }
.tx-dur .num { text-align: right; font-family: var(--font-mono); font-variant-numeric: tabular-nums; }
.tx-curves { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: var(--space-5); }
.tx-curves figure { margin: 0; color: var(--color-text-primary); }
.tx-curve { width: 100%; max-width: 160px; height: auto; }
.tx-curves figcaption { font-size: var(--type-small-size); margin-top: var(--space-2); }
.tx-list { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: var(--space-3); }
.tx-list li { padding: var(--space-5); background: var(--color-surface); border-top: var(--border-strong) solid var(--color-brand-primary); }
.tx-list strong { display: block; margin-bottom: var(--space-1); }
.tx-media { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--space-5); }
.tx-media > div { aspect-ratio: 4 / 3; position: relative; overflow: hidden; }
.tx-field { position: absolute; inset: 0; background: linear-gradient(135deg, var(--color-brand-primary), var(--color-background-inverse)); }
.tx-field--b { background: linear-gradient(200deg, var(--color-accent-soft), var(--color-brand-primary)); }
.tx-field--c { background: radial-gradient(circle at 30% 30%, var(--color-surface-brand-soft), var(--color-background-inverse)); }
.tx-cropdemo { position: absolute; inset: 0; display: grid; place-items: center; background: var(--color-surface); }
.tx-cropdemo .tx-field { position: relative; inset: auto; height: 100%; width: auto; aspect-ratio: 1; }
.tx-field svg { position: absolute; right: -8%; bottom: -12%; width: 70%; height: auto; opacity: .9; }
.tx-btns { display: flex; flex-wrap: wrap; gap: var(--space-4); align-items: center; }
.tx-btn { display: inline-flex; align-items: center; gap: .6em; min-height: 48px; padding: 0 var(--space-6); border: 0; cursor: pointer; text-decoration: none;
  font: var(--type-button-weight) var(--type-button-size)/1 var(--font-sans); letter-spacing: var(--type-button-letter-spacing); text-transform: var(--type-button-transform);
  background: var(--color-brand-primary); color: var(--color-text-on-brand); border-radius: var(--radius-button); }
.tx-btn--dark { background: var(--color-background-inverse); color: var(--color-text-inverse); --${p}-sweep-color: var(--color-brand-primary-pressed); }
.tx-btn--ghost { background: transparent; color: var(--color-text-primary); box-shadow: inset 0 0 0 var(--border-regular) var(--color-border-strong); --${p}-sweep-color: var(--color-surface-sunken); }
.tx-link { color: var(--color-text-primary); font-weight: 600; }
.tx-hcard { display: block; width: min(100%, 360px); color: inherit; text-decoration: none; background: var(--color-surface); border: var(--border-hairline) solid var(--color-border-subtle); }
.tx-hcard__media { aspect-ratio: 16 / 9; position: relative; overflow: hidden; }
.tx-hcard__body { padding: var(--space-5); }
.tx-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: var(--space-6); }
.tx-stat { border-top: var(--border-hairline) solid var(--color-border-strong); padding-top: var(--space-4); }
.tx-stat .${p}-data-xl { display: block; font-size: clamp(2.5rem, 5vw, 4rem); line-height: 1; }
.tx-stat > span:last-child { color: var(--color-text-secondary); font-size: var(--type-small-size); }
.tx-marquee { padding-block: var(--space-6); border-block: var(--border-hairline) solid var(--color-border); }
.tx-marquee li { list-style: none; white-space: nowrap; font-family: var(--font-display); font-size: var(--type-h3-size); text-transform: var(--type-h1-transform); display: inline-flex; align-items: center; gap: var(--space-10); }
.tx-marquee ul { margin: 0; padding: 0; }
.tx-marquee li::after { content: ""; width: .45em; height: .45em; background: var(--color-brand-primary); border-radius: var(--radius-tag); display: inline-block; }
.tx-load { display: flex; flex-wrap: wrap; gap: var(--space-8); align-items: center; }
.tx-skel { flex: 1 1 280px; display: grid; gap: var(--space-3); }
.tx-skel span { display: block; height: 14px; }
.tx-skel span:first-child { height: 28px; width: 60%; }
.tx-demo { position: relative; aspect-ratio: 16 / 9; overflow: hidden; background: var(--color-surface); border: var(--border-hairline) solid var(--color-border-subtle); }
.tx-wire { position: absolute; inset: 0; padding: 6%; display: grid; grid-template-rows: auto auto 1fr; gap: 6%; }
.tx-wire i { display: block; background: var(--color-surface-sunken); }
.tx-wire i:nth-child(1) { height: 8%; min-height: 10px; width: 100%; }
.tx-wire i:nth-child(2) { height: 22%; min-height: 24px; width: 70%; background: var(--color-text-primary); opacity: .82; }
.tx-wire i:nth-child(3) { width: 100%; }
.tx-intro { width: min(100%, 320px); aspect-ratio: 1; margin-inline: auto; }
.tx-intro-wrap { display: grid; place-items: center; padding: var(--space-10); background: var(--color-surface); border: var(--border-hairline) solid var(--color-border-subtle); }
.tx-frames { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--space-5) var(--space-4); }
.tx-frames figure { margin: 0; }
.tx-frames figcaption { margin-top: var(--space-2); font-size: var(--type-caption-size); color: var(--color-text-secondary); }
@media (max-width: 760px) { .tx-media { grid-template-columns: 1fr; } .tx-dur { grid-template-columns: 7rem 1fr 4rem; } }
</style>`;

function frameStrip(b, M, esc, phases) {
  return `<div class="tx-frames">${phases.map(([ph, q]) => `<figure><div class="tx-demo"><div class="tx-wire" aria-hidden="true"><i></i><i></i><i></i></div><div class="${b.p}-wipe ${b.p}-wipe--inline" data-frame="${q}" data-phase="${ph}" aria-hidden="true"></div></div><figcaption><span class="lp-tc">${ph === 'cover' ? 'Cover' : 'Reveal'} · ${Math.round(q * 100)}%</span></figcaption></figure>`).join('')}</div>`;
}
const FRAME_SCRIPT = G => `<script>(function(){function go(){document.querySelectorAll('[data-frame]').forEach(function(el){${G}.transition.frame(el,+el.getAttribute('data-frame'),el.getAttribute('data-phase'));});}if(document.readyState!=='loading')go();else document.addEventListener('DOMContentLoaded',go);window.addEventListener('resize',go);})();</script>`;
const PHASES = [['cover', 0.25], ['cover', 0.5], ['cover', 0.78], ['cover', 1], ['reveal', 0.4], ['reveal', 0.75]];

module.exports = function (b, M, o) {
  const p = b.p, G = b.G, esc = o.esc, c = b.content || {}, cb = c.brand || {};
  const d = M.duration, E = M.energy, travel = Math.round(8 + 24 * E), stagger = Math.round(40 + 70 * E);
  const autoKind = { snap: 'wipe', slide: 'rise', glide: 'scale', flow: 'drift' }[M.character];
  const charAlt = { snap: 'rise', slide: 'wipe', glide: 'rise', flow: 'scale' }[M.character];
  const use = { instant: 'state flips, toggles', fast: 'hover, press, focus', base: 'small UI: menus, tooltips', slow: 'panels, drawers, cards', slower: 'section entrances, page transitions', formation: 'hero entrances, count-ups, charts', logo: 'logo animations' };
  const maxD = Math.max(...Object.values(d));
  const offer = (c.offerings || []).slice(0, 6), units = (c.units || []).slice(0, 6), stats = (c.stats || []).slice(0, 4);
  const marq = [...units.map(u => u.name), ...offer.map(x => x.name)].slice(0, 10);
  const arrow = `<svg class="${p}-nudge__icon" width="16" height="16" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12h15M13 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="${M.cap === 'square' ? 'square' : 'round'}" stroke-linejoin="${M.join === 'miter' ? 'miter' : 'round'}"/></svg>`;
  const markInline = `<span class="tx-markslot" data-mark-variant="on-dark"></span>`;
  const sample = c._sample ? `<p class="lp-note">Sample content: the words and numbers on this page come from SOURCE/CONFIG/content.json, which is still marked as sample. Replace it before public use.</p>` : '';
  const sec = (id, title, sub, inner) => `<section class="lp-section" aria-labelledby="${id}"><h2 class="${p}-h2" id="${id}">${title}</h2>${sub ? `<p class="lp-sub">${sub}</p>` : ''}${inner}</section>`;
  const replay = target => `<p style="margin-top:var(--space-4)"><button type="button" class="lp-btn" data-replay="${target}">Replay</button></p>`;
  const body = `<a class="${p}-skip-link" href="#main">Skip to content</a>
<main class="lp" id="main"><div class="lp-wrap">
<header class="lp-head"><div><p class="lp-kicker ${p}-eyebrow"><span class="${p}-index">${esc(M.character)}</span><span>${esc(b.name)} · Motion</span></p>
<h1 class="lp-title ${p}-h1">Transitions &amp; micro-interactions</h1><p class="lp-lead">${esc(`Character ${M.character}: ${M.signature}. Everything below runs on the duration and easing tokens and the classes in ${p}-motion.css / ${p}-motion.js.`)}</p></div>
<dl class="lp-meta"><dt>Energy</dt><dd>${E}</dd><dt>Travel</dt><dd>${travel} px</dd><dt>Stagger</dt><dd>${stagger} ms</dd><dt>Edge</dt><dd>${M.angle}° cut · crop ${esc(M.imagery)}</dd><dt>Logo</dt><dd><a href="../logo-animation/index.html">Logo animations</a></dd></dl></header>

${sec('t-dur', 'Durations &amp; easing', 'Tokens from tokens.css. Reduced motion sets every duration to 0.', `<div class="lp-cols"><div class="tx-dur">${Object.entries(d).map(([k, v]) => `<code>--duration-${k}</code><div><div class="tx-bar" style="width:${Math.max(2, v / maxD * 100).toFixed(1)}%"></div><span class="tx-mono">${use[k] || ''}</span></div><span class="num">${v} ms</span>`).join('')}</div>
<div class="tx-curves">${['standard', 'enter', 'exit', 'emphasis'].map(k => `<figure>${curveSVG(M.ease[k], k)}<figcaption><code>--ease-${k}</code><br><span class="tx-mono">${esc(M.ease[k])}</span></figcaption></figure>`).join('')}</div></div>`)}

${sec('t-reveal', 'Reveal on scroll', `<code>data-reveal</code> on any block; <code>auto</code> is the brand default (${autoKind}). Masks are removed once settled.`, `<div class="tx-grid" id="g-reveal">${[['auto', `The default: ${autoKind}.`], ['fade', 'Opacity only — the calmest.'], [charAlt, 'An alternative within the character.'], ['mask', `Media: the ${esc(M.imagery)} crop opens.`]].map(([k, t], i) => `<article class="tx-card" data-reveal="${k}" data-reveal-delay="${i * stagger}"><h3 class="${p}-h4">${esc(k)}</h3><p class="${p}-small">${esc(t)}</p><code>data-reveal="${k}"</code></article>`).join('')}</div>${replay('#g-reveal')}`)}

${sec('t-stagger', 'Staggered entrance', `<code>data-reveal-stagger</code> on a parent: children follow ${stagger} ms apart.`, `<ul class="tx-list" data-reveal="auto" data-reveal-stagger id="g-stagger">${(offer.length ? offer : [{ name: 'One' }, { name: 'Two' }, { name: 'Three' }]).map(x => `<li><strong>${esc(x.name)}</strong><span class="${p}-small ${p}-muted">${esc(x.summary || '')}</span></li>`).join('')}</ul>${replay('#g-stagger')}`)}

${sec('t-media', 'Media reveal', `<code>data-reveal="mask"</code> on the wrapper; a designed crop on the inner element (here <code>.${p}-crop</code> on the third) is content and stays intact under reduced motion.`, `<div class="tx-media" id="g-media"><div data-reveal="mask"><div class="tx-field" data-mark-crop></div></div><div data-reveal="mask" data-reveal-delay="${stagger * 2}"><div class="tx-field tx-field--b"></div></div><div data-reveal="mask" data-reveal-delay="${stagger * 4}"><div class="tx-cropdemo"><div class="tx-field tx-field--c ${p}-crop"></div></div></div></div>${replay('#g-media')}`)}

${sec('t-page', 'Page &amp; section transitions', `${{ snap: `Two panels wipe along the ${M.angle}° cut`, slide: 'Grid columns step down in sequence', glide: 'An iris opens from the centre', flow: 'A soft wave rises and recedes' }[M.character]} — <code>${G}.transition.cover()</code> → navigate → <code>.reveal()</code>; links with <code>data-${p}-transition</code> do it automatically.`, `<div class="lp-cols"><div><div class="tx-demo" id="tx-demo"><div class="tx-wire" aria-hidden="true"><i></i><i></i><i></i></div><div class="${p}-wipe ${p}-wipe--inline" id="tx-demo-wipe" aria-hidden="true"></div></div><p style="margin-top:var(--space-4)" class="tx-btns"><button type="button" class="lp-btn lp-btn--primary" id="tx-play">Play in the box</button><button type="button" class="lp-btn" id="tx-full">Play full page</button></p></div>
<div>${frameStrip(b, M, esc, PHASES.slice(0, 6))}</div></div>`)}

${sec('t-hover', 'Hover &amp; press', `Opt-in classes: <code>.${p}-sweep</code> (fill sweep), <code>.${p}-press</code>, <code>.${p}-nudge</code>, <code>.${p}-underline</code>, <code>.${p}-lift</code>, <code>.${p}-zoom</code>. Keyboard focus triggers the same states.`, `<div class="lp-cols"><div class="tx-btns">
<a href="#t-hover" class="tx-btn ${p}-sweep ${p}-press ${p}-nudge">${esc((b.labels || {}).cta_primary || 'Get in touch')} ${arrow}</a>
<a href="#t-hover" class="tx-btn tx-btn--dark ${p}-sweep ${p}-press">${esc((b.labels || {}).cta_secondary || 'Learn more')}</a>
<a href="#t-hover" class="tx-btn tx-btn--ghost ${p}-sweep ${p}-press ${p}-nudge">${esc((b.labels || {}).offerings || 'Services')} ${arrow}</a>
<a href="#t-hover" class="tx-link ${p}-underline">${esc(cb.tagline || b.name)}</a></div>
<a href="#t-hover" class="tx-hcard ${p}-lift ${p}-zoom"><div class="tx-hcard__media"><div class="tx-field ${p}-zoom__media" data-mark-crop></div></div><div class="tx-hcard__body"><span class="${p}-label">${esc((b.labels || {}).projects || 'Work')}</span><h3 class="${p}-h4" style="margin-top:var(--space-2)">${esc(((c.projects || [])[0] || {}).title || 'Card title')}</h3></div></a></div>`)}

${stats.length ? sec('t-count', 'Count-up', `<code>data-reveal="count"</code> + <code>data-count</code>. Screen readers get the final value; numbers are formatted for <code>lang="${b.lang}"</code>.`, `<div class="tx-stats" data-reveal="count" id="g-count">${stats.map(s => `<div class="tx-stat"><span class="${p}-data-xl" data-count="${esc(String(s.value) + (s.unit && s.unit.length <= 2 ? s.unit : ''))}">${esc(String(s.value) + (s.unit && s.unit.length <= 2 ? s.unit : ''))}</span><span>${esc(s.label)}${s.unit && s.unit.length > 2 ? ' (' + esc(s.unit) + ')' : ''}</span></div>`).join('')}</div>${replay('#g-count')}`) : ''}

${marq.length ? sec('t-marquee', 'Marquee', `<code>.${p}-marquee</code> — ${M.character === 'snap' || M.character === 'slide' ? 'stepped: holds, then moves one item with a crisp ease' : 'continuous, slow'}. Pauses on hover/focus and has a pause button; static and wrapped under reduced motion.`, `<div class="${p}-marquee tx-marquee" aria-label="${esc((b.labels || {}).offerings || 'Offerings')}"><ul class="${p}-marquee__track">${marq.map(n => `<li>${esc(n)}</li>`).join('')}</ul></div>`) : ''}

${sec('t-load', 'Loading', `<code>${G}.loader(el)</code> or <code>data-${p}-loader</code>: derived from the simplified mark. Skeletons: <code>.${p}-skeleton</code>.`, `<div class="tx-load"><span data-${p}-loader data-size="72"></span><span data-${p}-loader data-size="40"></span><span data-${p}-loader data-size="24"></span><div class="tx-skel" aria-hidden="true"><span class="${p}-skeleton"></span><span class="${p}-skeleton"></span><span class="${p}-skeleton" style="width:80%"></span></div></div>`)}

${sec('t-intro', 'Logo intro', `<code>data-reveal="logo"</code> (or <code>${G}.logoIntro(el)</code>) plays the mark's signature entrance once, when it scrolls into view.`, `<div class="tx-intro-wrap ${p}-shape"><div class="tx-intro" data-reveal="logo" id="g-intro"></div></div>${replay('#g-intro')}`)}
${sample}
<nav class="lp-nav" aria-label="Motion"><a href="../logo-animation/index.html">← Logo animations</a><a href="../principles.md">Motion principles</a><a href="frames.html">Transition frames →</a></nav>
</div></main>`;
  const tail = `<script>(function(){
var G=window.${G};
function marks(){document.querySelectorAll('[data-mark-crop]').forEach(function(el){if(!G.markSVG||el.querySelector('svg'))return;el.insertAdjacentHTML('beforeend',G.markSVG({level:'simplified',variant:'tonal-light',decorative:true}));});}
marks();
document.querySelectorAll('[data-replay]').forEach(function(btn){btn.addEventListener('click',function(){var el=document.querySelector(btn.getAttribute('data-replay'));if(!el)return;if(el.id==='g-intro'){el.classList.remove('is-revealed');G.logoIntro(el,{});return;}if(el.matches('[data-reveal]'))G.reveal.replay(el);el.querySelectorAll('[data-reveal]').forEach(function(n){G.reveal.replay(n);});});});
var box=document.getElementById('tx-demo-wipe');
function demo(){if(!box)return;var d=G.motion.duration.slower*(G.motion.character==='slide'?1.25:1);G.motion.tween({duration:d,ease:'linear',update:function(v,u){G.transition.frame(box,u,'cover');}}).finished.then(function(){return new Promise(function(r){setTimeout(r,250);});}).then(function(){return G.motion.tween({duration:d,ease:'linear',update:function(v,u){G.transition.frame(box,u,'reveal');}}).finished;});}
var pb=document.getElementById('tx-play');if(pb)pb.addEventListener('click',demo);
var fb=document.getElementById('tx-full');if(fb)fb.addEventListener('click',function(){G.transition.cover().then(function(){return new Promise(function(r){setTimeout(r,200);});}).then(function(){G.transition.reveal();});});
if(box)G.transition.frame(box,0,'cover');
})();</script>${FRAME_SCRIPT(G)}`;
  return F.page(b, 'Transitions & micro-interactions', body, AT, { head: o.head(AT) + PAGE_CSS(p), scripts: o.coreScripts, tail });
};

module.exports.frames = function (b, M, o) {
  const p = b.p, G = b.G, esc = o.esc;
  const body = `<main class="lp"><div class="lp-wrap"><div class="lp-board" id="frames">
<div class="lp-board__head"><h1 class="${p}-h3">Page transition — frames</h1><span class="${p}-label">${esc(b.name)} · ${esc(M.character)} · ${M.duration.slower} ms per phase</span></div>
${frameStrip(b, M, esc, PHASES)}
</div></div></main>`;
  return F.page(b, 'Page transition frames', body, AT, { head: o.head(AT) + PAGE_CSS(p), scripts: o.coreScripts, tail: FRAME_SCRIPT(G) });
};
