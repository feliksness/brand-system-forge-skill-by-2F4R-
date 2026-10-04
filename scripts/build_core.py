#!/usr/bin/env python3
"""
build_core.py — render the starter layer with the brand prefix and the design DNA.

usage: python3 scripts/build_core.py --config brand.config.json --repo ../ACME-BRAND

Writes
  SOURCE/CSS/<p>-core.css   base · typography · layout · SHAPE GRAMMAR (.p-shape / .p-crop resolved from the DNA) · grounds · motion
  SOURCE/JS/<p>-mark.js     mark renderer (+ wordmark renderer, DNA access, seeded RNG, helpers)
  SOURCE/JS/dna-data.js     window.<G>_DNA — the design DNA for JS-driven modules (patterns, motion, social, charts…)
"""
import argparse, json, math, os
HERE = os.path.dirname(os.path.abspath(__file__)); SKILL = os.path.dirname(HERE)

def render(text, C, extra=None):
    b = C['brand']
    rep = {'{{p}}': b.get('prefix', 'bx'), '{{G}}': b.get('global', 'BX'), '{{BRAND_NAME}}': b['name'], '{{MARK_NOUN}}': b.get('mark_noun', 'mark')}
    rep.update(extra or {})
    for k, v in rep.items(): text = text.replace(k, v)
    return text

BLOB = ("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100' preserveAspectRatio='none'>"
        "<path d='M50 2C72 2 96 14 98 42c2 26-14 54-44 56C24 100 4 82 2 54 0 26 24 2 50 2Z'/></svg>")

def shape_css(p, dna):
    st = dna.get('corner', {}).get('style', 'rounded'); crop = dna.get('imagery', {}).get('crop', 'rounded')
    ang = dna.get('angles', {}).get('crop', 72); run = round(100 / math.tan(math.radians(ang)), 1) if ang < 89 else 0
    out = []
    if st == 'cut':
        ca = dna.get('angles', {}).get('cut', 45) or 45; kk = round(math.tan(math.radians(ca)), 3)
        out.append(f'/* chamfer at {ca}° (from the logo edges): the cut runs var(--cut) across and var(--cut) × tan({ca}°) = ×{kk} down */')
        out.append(f'.{p}-shape    {{ --cut: var(--cut-md); --cut-y: calc(var(--cut) * {kk}); clip-path: polygon(0 0, 100% 0, 100% calc(100% - var(--cut-y)), calc(100% - var(--cut)) 100%, 0 100%); }}')
        out.append(f'.{p}-shape-sm {{ --cut: var(--cut-sm); }} .{p}-shape-lg {{ --cut: var(--cut-lg); }} .{p}-shape-xl {{ --cut: var(--cut-xl); }}')
        out.append(f'/* Clip-path also clips outlines: put focus rings on an inner element or use outline-offset: -3px inside .{p}-shape. */')
    else:
        out.append(f'.{p}-shape    {{ border-radius: var(--radius-card); overflow: hidden; }}')
        out.append(f'.{p}-shape-sm {{ border-radius: var(--radius-sm); }} .{p}-shape-lg {{ border-radius: var(--radius-lg); }} .{p}-shape-xl {{ border-radius: var(--radius-xl); }}')
    if crop == 'angled':
        out.append(f'.{p}-crop     {{ clip-path: polygon(0 0, 100% 0, 100% 100%, {run}% 100%); }}   /* {ang}° edge — exact on square boxes */')
        out.append(f'.{p}-crop-alt {{ clip-path: polygon(0 0, {100 - run}% 0, 100% 100%, 0 100%); }}')
    elif crop == 'circle':
        out.append(f'.{p}-crop     {{ border-radius: 50%; aspect-ratio: 1; object-fit: cover; overflow: hidden; }}')
        out.append(f'.{p}-crop-alt {{ border-radius: var(--radius-pill); overflow: hidden; }}   /* capsule for wide media */')
    elif crop == 'organic':
        out.append(f'.{p}-crop     {{ -webkit-mask: url("{BLOB}") center / 100% 100% no-repeat; mask: url("{BLOB}") center / 100% 100% no-repeat; }}')
        out.append(f'.{p}-crop-alt {{ border-radius: 46% 54% 42% 58% / 55% 45% 55% 45%; overflow: hidden; }}')
    elif crop == 'rect':
        out.append(f'.{p}-crop     {{ border-radius: 0; }}')
        out.append(f'.{p}-crop-alt {{ clip-path: inset(0 0 8% 0); }}')
    else:
        out.append(f'.{p}-crop     {{ border-radius: var(--radius-lg); overflow: hidden; }}')
        out.append(f'.{p}-crop-alt {{ border-radius: var(--radius-xl) var(--radius-xl) 0 var(--radius-xl); overflow: hidden; }}')
    out.append(f'.{p}-stroke {{ stroke-width: var(--stroke-icon); stroke-linecap: var(--stroke-cap); stroke-linejoin: var(--stroke-join); fill: none; stroke: currentColor; }}')
    return '\n'.join(out)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--config', required=True); ap.add_argument('--repo', required=True)
    a = ap.parse_args(); C = json.load(open(a.config)); b = C['brand']; p = b.get('prefix', 'bx'); G = b.get('global', 'BX')
    R = lambda *x: os.path.join(a.repo, *x)
    dna_p = R('SOURCE', 'CONFIG', 'design-dna.json'); dna = json.load(open(dna_p)) if os.path.exists(dna_p) else {}
    summary = f"{dna.get('base_language', 'mixed')} geometry · {dna.get('corner', {}).get('style', 'rounded')} corners · {dna.get('imagery', {}).get('crop', 'rounded')} crops · {dna.get('motion', {}).get('character', 'glide')} motion"
    st = os.path.join(SKILL, 'assets', 'starter', 'SOURCE')
    os.makedirs(R('SOURCE', 'CSS'), exist_ok=True); os.makedirs(R('SOURCE', 'JS'), exist_ok=True)
    open(R('SOURCE', 'CSS', f'{p}-core.css'), 'w').write(render(open(os.path.join(st, 'CSS', 'core.css')).read(), C, {'{{SHAPE_PRIMITIVES}}': shape_css(p, dna), '{{DNA_SUMMARY}}': summary}))
    open(R('SOURCE', 'JS', f'{p}-mark.js'), 'w').write(render(open(os.path.join(st, 'JS', 'mark.js')).read(), C))
    js = {k: dna.get(k) for k in ('version', 'geometry', 'base_language', 'complexity', 'logo_type', 'corner', 'angles', 'stroke', 'density', 'patterns', 'motifs', 'motion', 'imagery', 'composition', 'type_voice', 'shadow_style')}
    open(R('SOURCE', 'JS', 'dna-data.js'), 'w').write(f'/* {b["name"]} design DNA — generated by build_core.py from SOURCE/CONFIG/design-dna.json. */\nwindow.{G}_DNA=' + json.dumps(js, separators=(',', ':')) + ';\n')
    print(f'core rendered: {p}-core.css ({summary}) · {p}-mark.js · dna-data.js')

if __name__ == '__main__':
    main()
