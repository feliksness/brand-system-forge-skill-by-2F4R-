#!/usr/bin/env python3
"""
derive_dna.py — turn the logo's measured geometry + the company profile into a DESIGN DNA:
the shape language every module reads (corners, angles, strokes, patterns, motion, imagery, composition).

usage: python3 scripts/derive_dna.py --analysis logo-analysis.json --profile saas-tech|path/to/profile.json
                                     [--config brand.config.json] --out design-dna.json

Rules (summarised — see references/design-dna.md for the full table):
  angular     cut corners at the measured diagonal · mitred strokes, square caps · shards/chevrons/facets · angled crops · snappy motion
  orthogonal  square corners (tiny radius) · butt caps · grid/blocks/stripes · rectangular crops · sliding motion
  round       radii + pill buttons · round caps/joins · rings/dots/arcs/orbits · circle & rounded crops · gliding motion
  organic     soft large radii · round caps · waves/blobs/flow lines · organic masks · flowing, springy motion
  mixed       moderate radii · round joins · lines + dots + arcs · rounded crops · gliding motion
  complexity  faceted → facet fields & crystals · line → outline traces, stroke-matched icons · gradient → glows & mesh fields
The profile adds density, display case, motion energy and imagery direction.
config.dna (if present) overrides any key — the art director's word is final. Every decision is written to "rationale".
"""
import argparse, json, os
HERE = os.path.dirname(os.path.abspath(__file__)); SKILL = os.path.dirname(HERE)

EASE = {
    'snap':  {'standard': 'cubic-bezier(0.2, 0, 0, 1)', 'enter': 'cubic-bezier(0.16, 1, 0.3, 1)', 'exit': 'cubic-bezier(0.7, 0, 0.84, 0)', 'emphasis': 'cubic-bezier(0.34, 1.4, 0.64, 1)', 'linear': 'linear'},
    'slide': {'standard': 'cubic-bezier(0.4, 0, 0.2, 1)', 'enter': 'cubic-bezier(0, 0, 0.2, 1)', 'exit': 'cubic-bezier(0.4, 0, 1, 1)', 'emphasis': 'cubic-bezier(0.2, 0, 0, 1)', 'linear': 'linear'},
    'glide': {'standard': 'cubic-bezier(0.25, 0.1, 0.25, 1)', 'enter': 'cubic-bezier(0.22, 1, 0.36, 1)', 'exit': 'cubic-bezier(0.64, 0, 0.78, 0)', 'emphasis': 'cubic-bezier(0.34, 1.25, 0.64, 1)', 'linear': 'linear'},
    'flow':  {'standard': 'cubic-bezier(0.37, 0, 0.63, 1)', 'enter': 'cubic-bezier(0.25, 0.8, 0.25, 1)', 'exit': 'cubic-bezier(0.5, 0, 0.75, 0)', 'emphasis': 'cubic-bezier(0.45, 1.5, 0.55, 1)', 'linear': 'linear'},
}
GEO = {
    'angular':    dict(corner='cut', cap='square', join='miter', patterns=['shards', 'chevrons', 'diagonal-bands'], motifs=['shard', 'chevron', 'diagonal-band', 'cut-corner-frame'],
                       motion='snap', crop='angled', shadow='hard', composition='diagonal-tension', icon_stroke=1.75),
    'orthogonal': dict(corner='square', cap='butt', join='miter', patterns=['grid', 'blocks', 'stripes'], motifs=['grid', 'block', 'stripe', 'step', 'bracket'],
                       motion='slide', crop='rect', shadow='flat', composition='modular-grid', icon_stroke=1.5),
    'round':      dict(corner='round', cap='round', join='round', patterns=['orbits', 'dots', 'arcs'], motifs=['ring', 'dot', 'arc', 'orbit', 'halo'],
                       motion='glide', crop='circle', shadow='soft', composition='radial-centred', icon_stroke=2.0),
    'organic':    dict(corner='soft', cap='round', join='round', patterns=['waves', 'blobs', 'flow-lines'], motifs=['wave', 'blob', 'flow-line', 'ripple'],
                       motion='flow', crop='organic', shadow='diffuse', composition='flowing-asymmetric', icon_stroke=1.75),
    'mixed':      dict(corner='rounded', cap='round', join='round', patterns=['lines', 'dots', 'arcs'], motifs=['line', 'dot', 'arc', 'grid'],
                       motion='glide', crop='rounded', shadow='soft', composition='editorial-grid', icon_stroke=1.75),
}
RADII = {   # px
    'cut':     {'none': '0', 'xs': '0', 'sm': '2px', 'md': '2px', 'lg': '2px', 'xl': '2px', 'button': '0', 'pill': '9999px', 'full': '9999px'},
    'square':  {'none': '0', 'xs': '0', 'sm': '2px', 'md': '2px', 'lg': '4px', 'xl': '4px', 'button': '2px', 'pill': '9999px', 'full': '9999px'},
    'round':   {'none': '0', 'xs': '4px', 'sm': '8px', 'md': '12px', 'lg': '20px', 'xl': '28px', 'button': '9999px', 'pill': '9999px', 'full': '9999px'},
    'soft':    {'none': '0', 'xs': '6px', 'sm': '10px', 'md': '16px', 'lg': '28px', 'xl': '40px', 'button': '14px', 'pill': '9999px', 'full': '9999px'},
    'rounded': {'none': '0', 'xs': '3px', 'sm': '4px', 'md': '6px', 'lg': '10px', 'xl': '16px', 'button': '6px', 'pill': '9999px', 'full': '9999px'},
}
SHADOW = {
    'hard':    {'1': '0 1px 0 rgba(0,0,0,.08)', '2': '4px 4px 0 0 rgba(0,0,0,.14)', '3': '8px 8px 0 0 rgba(0,0,0,.18)', 'focus-lift': '6px 6px 0 0 currentColor'},
    'flat':    {'1': '0 0 0 1px rgba(0,0,0,.08)', '2': '0 0 0 1px rgba(0,0,0,.12), 0 2px 0 rgba(0,0,0,.06)', '3': '0 0 0 1px rgba(0,0,0,.14), 0 6px 0 rgba(0,0,0,.06)', 'focus-lift': '0 0 0 2px currentColor'},
    'soft':    {'1': '0 1px 2px rgba(0,0,0,.06), 0 1px 1px rgba(0,0,0,.04)', '2': '0 8px 24px -8px rgba(0,0,0,.18)', '3': '0 24px 48px -16px rgba(0,0,0,.24)', 'focus-lift': '0 12px 32px -12px rgba(0,0,0,.3)'},
    'diffuse': {'1': '0 2px 6px rgba(0,0,0,.05)', '2': '0 12px 36px -12px rgba(0,0,0,.16)', '3': '0 32px 64px -24px rgba(0,0,0,.22)', 'focus-lift': '0 16px 40px -16px rgba(0,0,0,.28)'},
}

def load_profile(p):
    if os.path.exists(p): return json.load(open(p))
    return json.load(open(os.path.join(SKILL, 'assets', 'profiles', p + '.json')))

def snap(v, choices): return min(choices, key=lambda c: abs(c - v))

def deep_update(d, o):
    for k, v in o.items():
        if isinstance(v, dict) and isinstance(d.get(k), dict): deep_update(d[k], v)
        else: d[k] = v
    return d

def derive(A, P, C=None):
    C = C or {}; L = C.get('logo', {}); why = []
    geometry = L.get('geometry') or A['geometry']; complexity = A['complexity']; logo_type = L.get('type') or A['logo_type']
    base = geometry
    if complexity == 'faceted' and geometry in ('mixed', 'organic'):
        base = 'angular'; why.append(f'Faceted artwork with {geometry} outline → angular shape language (the facets are the visual signature).')
    g = GEO[base]; why.append(f'Geometry "{geometry}" (outline straight share {A["edges"]["outline_straight_share"]}, roundness {A["shape"]["roundness_contours"]}) → {g["corner"]} corners, {g["cap"]} caps, {g["motion"]} motion.')
    # ---- angles from the folded edge families
    fams = A['edges']['angle_families_folded']
    diag = [f for f in fams if 25 <= f['range_deg'][0] < 65]; steep = [f for f in fams if 65 <= f['range_deg'][0] < 85]; shallow = [f for f in fams if 5 <= f['range_deg'][0] < 25]
    cut = snap(diag[0]['range_deg'][0] + 2.5, [30, 36, 45, 54, 60]) if diag and base == 'angular' else 45
    crop = snap(steep[0]['range_deg'][0] + 2.5, [60, 66, 72, 75, 80]) if steep else (72 if base == 'angular' else 90)
    shal = snap(shallow[0]['range_deg'][0] + 2.5, [8, 12, 15, 18, 22]) if shallow else 15
    if base == 'angular': why.append(f'Edge families → chamfer {cut}°, editorial crop {crop}°, shallow band {shal}°.')
    # ---- density / scale
    bias = P.get('dna_bias', {}); density = bias.get('density', 'balanced')
    k = {'airy': 1.15, 'balanced': 1.0, 'dense': 0.88}[density]
    cutsz = {n: f'{round(v * k)}px' for n, v in {'xs': 6, 'sm': 10, 'md': 16, 'lg': 24, 'xl': 40, '2xl': 64}.items()} if g['corner'] == 'cut' else {n: '0' for n in ('xs', 'sm', 'md', 'lg', 'xl', '2xl')}
    # ---- strokes (icons, rules, outlines)
    sw_ratio = A['shape']['stroke_width_ratio']
    if complexity == 'line':
        icon_stroke = round(min(2.5, max(1.25, sw_ratio * 24 * 1.6)) * 4) / 4
        why.append(f'Line-art logo: icon stroke {icon_stroke}px @24 matches the logo stroke ({sw_ratio * 100:.1f}% of its size).')
    else:
        icon_stroke = g['icon_stroke']
    energy = float(bias.get('motion_energy', 0.5)); dk = round(1 / (0.7 + 0.6 * energy), 3)
    dur = {n: f'{round(v * dk)}ms' for n, v in {'instant': 80, 'fast': 160, 'base': 240, 'slow': 400, 'slower': 640, 'formation': 1200, 'logo': 2400}.items()}
    patterns = list(g['patterns']); motifs = list(g['motifs'])
    if complexity == 'faceted': patterns.insert(0, 'facets'); motifs = ['facet-field', 'crystal'] + motifs
    if complexity == 'line': patterns.insert(0, 'contours'); motifs = ['outline-trace', 'contour'] + motifs
    if complexity in ('gradient', 'illustrative'): patterns.insert(0, 'glow-fields'); motifs = ['glow', 'mesh-gradient'] + motifs
    motifs += ['mark-crop', 'mark-repeat', 'mark-outline']
    display_case = bias.get('display_case', 'sentence')
    dna = {
        'version': 2, 'geometry': geometry, 'base_language': base, 'complexity': complexity, 'logo_type': logo_type,
        'corner': {'style': g['corner'], 'angle_deg': cut if g['corner'] == 'cut' else None,
                   'note': {'cut': 'Chamfered corners (clip-path) at the logo angle; radii stay ~0.', 'square': 'Square corners; at most a 2px softening.',
                            'round': 'Generous radii; buttons and tags are pills.', 'soft': 'Large soft radii; masks may be organic.',
                            'rounded': 'Moderate radii; calm and versatile.'}[g['corner']]},
        'angles': {'cut': cut, 'crop': crop, 'shallow': shal, 'families': fams[:4]},
        'stroke': {'icon_px_at_24': icon_stroke, 'cap': g['cap'], 'join': g['join'], 'logo_stroke_ratio': sw_ratio,
                   'rule_px': 1.5 if base in ('angular', 'orthogonal') else 1},
        'density': density, 'space_scale': k,
        'patterns': patterns, 'motifs': motifs,
        'motion': {'character': g['motion'], 'energy': energy,
                   'signature': {'snap': 'cuts and wipes along the logo angle, crisp stops', 'slide': 'modular slides and step reveals on the grid',
                                 'glide': 'smooth scale/rotate from centre, orbits', 'flow': 'gentle drifts, morphs and springs'}[g['motion']]},
        'imagery': {'crop': g['crop'], 'direction': bias.get('imagery', ''), 'treatments': ['natural', 'duotone', 'tint'] + (['grain'] if complexity in ('faceted', 'illustrative') else [])},
        'composition': g['composition'],
        'type_voice': {'display_case': display_case, 'tracking_upper_em': 0.02 if display_case == 'upper' else 0, 'headline_weight_hint': 800 if base in ('angular', 'orthogonal') else 600},
        'shadow_style': g['shadow'],
        'icons': {'style': 'duotone' if P.get('key') in ('education-culture', 'retail-ecommerce') else 'outline', 'tint': 'accent' if P.get('key') in ('education-culture', 'retail-ecommerce') else 'primary'},
        'tokens': {
            'radius': RADII[g['corner']], 'cut': cutsz,
            'angle': {'cut': f'{cut}deg', 'crop': f'{crop}deg', 'shallow': f'{shal}deg'},
            'border': {'hairline': '1px', 'regular': '1.5px' if base in ('angular', 'orthogonal') else '1px', 'strong': '2px', 'heavy': '4px', 'rule': '6px' if base != 'round' else '4px'},
            'shadow': SHADOW[g['shadow']], 'duration': dur, 'ease': EASE[g['motion']],
            'stroke': {'icon': f'{icon_stroke}px', 'cap': g['cap'], 'join': g['join']},
        },
        'rationale': why + [f'Profile "{P.get("key")}" → density {density} (space ×{k}), display case {display_case}, motion energy {energy} (durations ×{dk}).',
                            f'Patterns {patterns[:3]} · imagery crop {g["crop"]} · shadows {g["shadow"]} · composition {g["composition"]}.'],
    }
    if C.get('dna'):
        deep_update(dna, C['dna']); dna['rationale'].append('config.dna overrides applied: ' + ', '.join(C['dna'].keys()))
    return dna

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--analysis', required=True); ap.add_argument('--profile', required=True)
    ap.add_argument('--config'); ap.add_argument('--out', required=True)
    a = ap.parse_args()
    A = json.load(open(a.analysis)); P = load_profile(a.profile); C = json.load(open(a.config)) if a.config else {}
    dna = derive(A, P, C)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(dna, open(a.out, 'w'), indent=2, ensure_ascii=False)
    print(f"DNA: {dna['base_language']} · corners {dna['corner']['style']} · motion {dna['motion']['character']} · patterns {dna['patterns'][:3]}")

if __name__ == '__main__':
    main()
