#!/usr/bin/env python3
"""
auto_config.py — draft a complete brand.config.json (and a sample content.json) from the logo analysis,
the company name, its profile and its languages. The art director then reviews and edits the draft.

usage:
  python3 scripts/auto_config.py --analysis work/analysis/logo-analysis.json --logo work/logo.png \
      --name "Northwind Studio" --profile professional-services --languages en,de \
      [--descriptor "Design consultancy"] [--tagline "…"] [--legal-name "…"] [--local-name "…"] \
      --out work/brand.config.json [--content-out work/content.json] [--seed 0]

What it decides (all overridable afterwards):
  palette   primary = most chromatic significant logo colour · foundation = darkest (or derived ink) · paper = lightest
            near-white (or derived from the primary hue) · accent = the most hue-distant chromatic colour (or derived) ·
            other distinct logo colours as secondary. Colours get descriptive names (rename them in the concept phase).
  fonts     scored from assets/fonts-catalogue.json: profile type tags × logo geometry tags × script coverage of the
            languages · avoids overused defaults · adds a local-script family when needed (Armenian, Arabic, Hebrew…)
  wordmark  traced lettering for combination/wordmark logos (never re-typeset) · typeset name for symbol/emblem logos
  vectorise route + levels scaled to the artwork size
"""
import argparse, json, math, os, re, sys, hashlib
HERE = os.path.dirname(os.path.abspath(__file__)); SKILL = os.path.dirname(HERE); sys.path.insert(0, HERE)
from colorlib import to_oklch, from_oklch, to_oklab, mix, contrast, rel_lum

LATIN_EXT = set('de fr es it pt pl cs sk hu ro tr hr sl lt lv et nl sv da no nb fi is az sq ca eu gl cy ga mt'.split())
CYR = set('ru uk be bg sr mk kk ky mn tg'.split())
SCRIPT = {'hy': 'armenian', 'ka': 'georgian', 'ar': 'arabic', 'fa': 'arabic', 'ur': 'arabic', 'he': 'hebrew', 'hi': 'devanagari', 'mr': 'devanagari',
          'ne': 'devanagari', 'th': 'thai', 'bn': 'bengali', 'am': 'ethiopic'}
GEO_TAGS = {'angular': ['condensed', 'sharp-soft-axis', 'technical', 'grotesk', 'strong', 'industrial', 'editorial', 'monumental'],
            'orthogonal': ['grotesk', 'neutral', 'industrial', 'technical', 'widths', 'corporate'],
            'round': ['round', 'rounded', 'rounded-corners', 'geometric', 'friendly', 'soft'],
            'organic': ['warm', 'soft', 'serif', 'hand', 'wonky', 'friendly', 'elegant'],
            'mixed': ['contemporary', 'versatile', 'modern', 'neutral', 'clean']}
FALLBACK_ACCENT = {'nonprofit-ngo': 55, 'saas-tech': 265, 'professional-services': 75, 'retail-ecommerce': 15, 'hospitality-food': 50,
                   'health-wellness': 175, 'education-culture': 95, 'industrial-energy': 70}

def slug(s): return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
def h(seed, s): return int(hashlib.md5(f'{seed}:{s}'.encode()).hexdigest()[:6], 16) / 0xFFFFFF

def colour_name(hx):
    L, C, H = to_oklch(hx)
    if C < 0.035:
        return 'ink' if L < 0.28 else 'graphite' if L < 0.42 else 'slate' if L < 0.6 else 'stone' if L < 0.86 else 'chalk' if L < 0.96 else 'paper'
    table = [(20, 'rose' if L > 0.7 else 'crimson'), (40, 'red'), (60, 'coral' if L > 0.7 else 'vermilion'), (80, 'orange'), (100, 'amber'), (115, 'yellow'),
             (135, 'olive' if L < 0.5 else 'lime'), (165, 'green'), (190, 'jade'), (210, 'teal'), (235, 'cyan' if L > 0.7 else 'petrol'),
             (255, 'sky' if L > 0.75 else 'azure'), (275, 'navy' if L < 0.4 else 'blue'), (290, 'indigo'), (310, 'violet'), (335, 'plum' if L < 0.4 else 'purple'), (361, 'magenta')]
    name = next(n for lim, n in table if H < lim)
    if L < 0.4 and name not in ('navy', 'plum', 'olive', 'crimson'): name = 'deep-' + name
    elif L > 0.86: name = 'pale-' + name
    return name

def okdist(a, b): return math.dist(to_oklab(a), to_oklab(b))
def hue_d(a, b): d = abs(a - b) % 360; return min(d, 360 - d)

def palette_from(A, profile_key):
    cands = []
    for c in A['colours']['10']:
        if c['share'] < 0.008: continue
        if any(okdist(c['hex'], o['hex']) < 0.045 for o in cands):
            o = next(o for o in cands if okdist(c['hex'], o['hex']) < 0.045); o['share'] += c['share']; continue
        cands.append(dict(c))
    for c in cands: c['L'], c['C'], c['H'] = to_oklch(c['hex'])
    chrom = [c for c in cands if c['C'] > 0.045]
    notes = []
    if chrom:
        prim = max(chrom, key=lambda c: c['C'] * math.sqrt(c['share']) * (1.15 if 0.35 < c['L'] < 0.75 else 1))
        P = prim['hex']; notes.append(f"primary {P} — most chromatic significant logo colour ({prim['share'] * 100:.0f}% of ink)")
    else:
        hue = FALLBACK_ACCENT.get(profile_key, 250); P = from_oklch(0.55, 0.16, hue); prim = None
        notes.append(f'monochrome logo → primary {P} derived for the profile (the logo stays monochrome; colour lives in the system)')
    pL, pC, pH = to_oklch(P)
    darks = [c for c in cands if c['L'] < 0.36 and c is not prim]
    if darks:
        F = min(darks, key=lambda c: c['L'])['hex']; notes.append(f'foundation {F} — darkest logo colour')
    else:
        F = from_oklch(0.21, min(0.035, pC * 0.25), pH); notes.append(f'foundation {F} — derived ink tinted with the primary hue')
    lights = [c for c in cands if c['L'] > 0.95 and c['C'] < 0.03]
    if lights:
        W = max(lights, key=lambda c: c['L'])['hex']; notes.append(f'paper {W} — lightest logo colour')
    else:
        W = from_oklch(0.975, min(0.012, pC * 0.08), pH); notes.append(f'paper {W} — derived warm/cool white from the primary hue')
    acc_c = [c for c in chrom if c is not prim and hue_d(c['H'], pH) > 40 and c['hex'] not in (F, W)]
    if acc_c:
        acc = max(acc_c, key=lambda c: c['C'] * math.sqrt(c['share']))['hex']; notes.append(f'accent {acc} — most hue-distant chromatic logo colour')
    else:
        ah = (pH + (35 if profile_key in ('hospitality-food', 'professional-services', 'health-wellness') else 180)) % 360
        acc = from_oklch(0.8, max(0.11, min(0.16, pC)), ah); notes.append(f'accent {acc} — derived (hue {ah:.0f}°) because the logo has a single hue')
    used = {P, F, W, acc}
    extra = [c['hex'] for c in sorted(chrom, key=lambda c: -c['share']) if c['hex'] not in used and all(okdist(c['hex'], u) > 0.1 for u in used)][:3]
    names = {}
    def add(hx, group, role_text, origin):
        n = colour_name(hx); k = n; i = 2
        while k in names: k = f'{n}-{i}'; i += 1
        names[k] = {'group': group, 'key': k, 'name': k.replace('-', ' ').title(), 'hex': hx.upper(), 'origin': origin, 'role': role_text}
        return k
    from_logo = lambda hx: 'Sampled from the logo.' if any(okdist(hx, c['hex']) < 0.02 for c in cands) else 'Derived (not in the logo).'
    kp = add(P, 'primary', 'Brand primary: actions, emphasis, the "one primary thing" per layout.', from_logo(P))
    kf = add(F, 'primary', 'Foundation: text on light, dark theme background, one-colour logo.', from_logo(F))
    kw = add(W, 'primary', 'Paper: default background.', from_logo(W))
    ka = add(acc, 'accent', 'Accent ≤ 10%: highlights, data, focus on dark.', from_logo(acc))
    for e in extra: add(e, 'secondary', 'Secondary logo colour: illustration, data, sub-brands.', 'Sampled from the logo.')
    return list(names.values()), {'primary': kp, 'foundation': kf, 'paper': kw, 'accent': ka, 'primary_ramp': 'primary', 'neutral_ramp': 'neutral'}, notes

def subsets_for(langs):
    need = {'latin'}; scripts = []
    for l in langs:
        if l in LATIN_EXT: need.add('latin-ext')
        if l in CYR: need |= {'cyrillic'}
        if l == 'el': need.add('greek')
        if l == 'vi': need.add('vietnamese')
        if l in SCRIPT: scripts.append(SCRIPT[l])
    return sorted(need), sorted(set(scripts))

def css_for(f, role):
    if f['variable']:
        return f['recommended_css']
    ws = [w for w in (400, 500, 700) if w in f['weights']] or f['weights'][:1]
    css = [f'{w}.css' for w in ws]
    if role == 'sans' and 'italic' in f.get('styles', []): css.append(f'{ws[0]}-italic.css')
    return css

def pick_fonts(profile, base, langs, seed):
    cat = json.load(open(os.path.join(SKILL, 'assets', 'fonts-catalogue.json')))['families']
    need, scripts = subsets_for(langs); T = profile.get('type', {}); gt = GEO_TAGS.get(base, [])
    def score(f, role, avoid=()):
        if role not in f['roles']: return -1e9
        if not set(need) <= set(f['subsets']): return -1e9
        tags = set(f['tags']); want = T.get(role) if isinstance(T.get(role), list) else []
        s = 3 * len(tags & set(want)) + 2 * len(tags & set(gt))
        if role == 'display':
            serif = f['category'] == 'serif' or 'serif' in tags
            s += (2 if T.get('serif') else -3) if serif else 0
        s += 0.5 if f['variable'] else 0; s -= 4 if f.get('overused') else 0
        s -= 6 if f['slug'] in avoid else 0
        return s + h(seed, f['slug']) * 1.5
    out = {}
    out['display'] = max(cat, key=lambda f: score(f, 'display'))
    out['sans'] = max(cat, key=lambda f: score(f, 'sans', avoid=(out['display']['slug'],) if 'sans' not in out['display']['roles'] or out['display']['category'] == 'serif' else ()))
    if T.get('mono'): out['mono'] = max(cat, key=lambda f: score(f, 'mono'))
    if T.get('hand'): out['hand'] = max(cat, key=lambda f: score(f, 'hand'))
    for sc in scripts:
        loc = [f for f in cat if 'local' in f['roles'] and sc in f['tags']]
        if loc: out[f'local-{sc}'] = max(loc, key=lambda f: h(seed, f['slug']) + (0.5 if f['variable'] else 0))
    fams, stacks = [], {}
    FALL = {'display': "system-ui, sans-serif", 'sans': "system-ui, -apple-system, 'Segoe UI', sans-serif", 'mono': 'ui-monospace, Menlo, Consolas, monospace', 'hand': 'cursive'}
    for role, f in out.items():
        subs = sorted(set(need) & set(f['subsets'])) if not role.startswith('local') else sorted(set(f['subsets']) & {role.split('-', 1)[1], 'latin'})
        fams.append({'role': role, 'family': f['family'], 'slug': f['slug'], 'package': f['package'], 'css': css_for(f, role), 'subsets': subs or ['latin'],
                     'category': f['category'], 'tags': f['tags'], 'weights': [min(f['weights']), max(f['weights'])], 'variable': f['variable']})
        fb = 'serif' if f['category'] == 'serif' else FALL.get(role.split('-')[0], 'sans-serif')
        stacks[role] = f"'{f['family']}', {fb}"
    if 'mono' not in stacks: stacks['mono'] = stacks['sans']
    for role in [r for r in stacks if r.startswith('local-')]:   # local script falls back inside the main stacks
        stacks['sans'] = stacks['sans'].replace("', ", f"', '{out[role]['family']}', ", 1)
        stacks['display'] = stacks['display'].replace("', ", f"', '{out[role]['family']}', ", 1)
    return fams, stacks

SCRIPT_RANGES = [('cyrillic', 0x0400, 0x04FF), ('greek', 0x0370, 0x03FF), ('armenian', 0x0530, 0x058F), ('hebrew', 0x0590, 0x05FF), ('arabic', 0x0600, 0x06FF),
                 ('devanagari', 0x0900, 0x097F), ('bengali', 0x0980, 0x09FF), ('thai', 0x0E00, 0x0E7F), ('georgian', 0x10A0, 0x10FF), ('ethiopic', 0x1200, 0x139F)]
def script_of(text):
    for ch in text:
        for name, lo, hi in SCRIPT_RANGES:
            if lo <= ord(ch) <= hi: return name
    return 'latin-ext' if any(ord(ch) > 0x7F for ch in text) else 'latin'

def flat_colour_count(A):
    keep = []
    for c in A['colours']['10']:
        if c['share'] < 0.012: continue
        if not any(okdist(c['hex'], k) < 0.06 for k in keep): keep.append(c['hex'])
    return max(1, len(keep))

def split_lines(name):
    w = name.split()
    if len(w) <= 1: return [name]
    best = min(range(1, len(w)), key=lambda i: abs(len(' '.join(w[:i])) - len(' '.join(w[i:]))))
    return [' '.join(w[:best]), ' '.join(w[best:])]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--analysis', required=True); ap.add_argument('--logo', required=True); ap.add_argument('--name', required=True)
    ap.add_argument('--profile', required=True); ap.add_argument('--languages', default='en'); ap.add_argument('--descriptor', default='')
    ap.add_argument('--tagline', default=''); ap.add_argument('--legal-name', default=''); ap.add_argument('--local-name', default='')
    ap.add_argument('--out', required=True); ap.add_argument('--content-out'); ap.add_argument('--seed', default='0')
    a = ap.parse_args()
    A = json.load(open(a.analysis))
    P = json.load(open(a.profile)) if os.path.exists(a.profile) else json.load(open(os.path.join(SKILL, 'assets', 'profiles', a.profile + '.json')))
    langs = [l.strip() for l in a.languages.split(',') if l.strip()]
    outdir = os.path.dirname(os.path.abspath(a.out)); os.makedirs(outdir, exist_ok=True)
    pal, roles, notes = palette_from(A, P['key'])
    base = 'angular' if A['complexity'] == 'faceted' and A['geometry'] in ('mixed', 'organic') else A['geometry']
    fams, stacks = pick_fonts(P, base, langs, a.seed + a.name)
    words = re.findall(r'[A-Za-z0-9]+', a.name)
    initials = ''.join(w[0] for w in words).upper()[:3] or a.name[:2].upper()
    prefix = (initials[:2] if len(initials) >= 2 else a.name[:2]).lower()
    disp = next(f for f in fams if f['role'] == 'display'); sans = next(f for f in fams if f['role'] == 'sans')
    mono = next((f for f in fams if f['role'] == 'mono'), sans)
    serif_display = disp['category'] == 'serif'
    wght = 400 if serif_display else min(disp['weights'][1], 800 if base in ('angular', 'orthogonal') else 700)
    mode = 'traced' if A['logo_type'] in ('combination', 'wordmark') else 'typeset'
    case_upper = P.get('dna_bias', {}).get('display_case') == 'upper' and not serif_display
    disp_name = a.name.upper() if case_upper else a.name
    route = A['suggested_route']; size = max(A['bbox_size']); s2 = round((size / 650) ** 2, 2)
    eff = A['effective_colours_90pct']; fc = flat_colour_count(A); poly = A['geometry'] in ('angular', 'orthogonal')
    if route == 'faceted-mesh':
        levels = {'master': {'thresh': 16, 'amin': int(180 * s2), 'nseg': 1100, 'maj': 5, 'tol_in': 16},
                  'simplified': {'thresh': 34, 'amin': int(900 * s2), 'nseg': 600, 'maj': 7, 'tol_in': 14}}
    elif route == 'svg-native':
        levels = {'master': {}}
    else:
        levels = {'master': {'colors': 6 if route == 'gradient-raster' else 'auto', 'mode': 'polygon' if poly else 'spline'},
                  'simplified': {'colors': 'auto', 'max_colors': 3, 'mode': 'polygon' if poly else 'spline'}}
    rel = lambda p: os.path.relpath(os.path.abspath(p), outdir)
    C = {
        '$schema_note': 'Draft written by scripts/auto_config.py — review every value (references/schemas/brand.config.schema.md).',
        'brand': {'name': a.name, 'legal_name': a.legal_name or a.name, 'name_local': a.local_name, 'descriptor': a.descriptor, 'tagline': a.tagline or P['sample']['tagline'],
                  'languages': langs, 'primary_language': langs[0], 'profile': P['key'], 'repo_name': slug(a.name).upper() + '-BRAND',
                  'prefix': prefix, 'global': prefix.upper(), 'mark_noun': 'mark', 'brand_idea': '', 'principle': ''},
        'logo': {'artwork': rel(a.logo), 'type': A['logo_type'], 'geometry': A['geometry'], 'complexity': A['complexity'],
                 'vectorize': {'route': route, 'levels': levels}, 'lettering': {'colors': 'auto', 'max_colors': 3, 'mode': 'spline'}},
        'roles': roles, 'palette': pal, 'palette_notes': notes, 'semantic': {}, 'themes': {'light': {}, 'dark': {}, 'contrast': {}},
        'fonts': {'families': fams, 'stacks': stacks,
                  'settings': {'headline': 'normal', 'body': 'normal'},
                  'samples': {'display': disp_name, 'sans': f"{a.tagline or P['sample']['tagline']} — 0123456789", 'mono': f"{prefix.upper()} / REF. 2026-014 · 08:30 · №0042"}},
        'wordmark': {'mode': mode, 'font': {'slug': disp['slug'], 'subset': 'latin', 'axes': {'wght': wght}}, 'tracking_em': 0.02 if case_upper else -0.01,
                     'lines': split_lines(disp_name), 'line_advance_caps': 1.2, 'one_line': disp_name, 'monogram': initials,
                     'descriptors': ([{'name': 'descriptor', 'text': a.descriptor.upper() if case_upper else a.descriptor,
                                       'font': {'slug': mono['slug'], 'subset': script_of(a.descriptor), 'axes': {'wght': 500}}, 'tracking_em': 0.12}] if a.descriptor else []) +
                                    ([{'name': 'name-local', 'text': a.local_name, 'font': {'slug': next((f['slug'] for f in fams if f['role'] == 'local-' + script_of(a.local_name)), disp['slug']),
                                       'subset': script_of(a.local_name), 'axes': {'wght': 600}}, 'tracking_em': 0.02}] if a.local_name else [])},
        'dna': {}, 'tokens': {}, 'type': {},
        'content': 'content.json',
    }
    json.dump(C, open(a.out, 'w'), indent=2, ensure_ascii=False)
    print(f"config → {a.out}\n  palette: " + ', '.join(f"{p['key']} {p['hex']}" for p in pal) + f"\n  fonts: " + ', '.join(f"{f['role']}={f['family']}" for f in fams) + f"\n  wordmark: {mode} · route {route}")
    for n in notes: print('  ·', n)
    if a.content_out and not os.path.exists(a.content_out):
        S = P['sample']; L = P['labels']
        content = {'_sample': True, '_note': 'SAMPLE content generated from the profile. Replace with real content from the company overview before public use.',
                   'brand': {'name': a.name, 'legal_name': a.legal_name or a.name, 'tagline': a.tagline or S['tagline'], 'descriptor': a.descriptor,
                             'mission': S['mission'], 'values': S['values'], 'languages': langs},
                   'labels': L,
                   'contact': {'email': f'hello@{slug(a.name)}.example', 'phone': '+00 000 000 000', 'address': '1 Example Street', 'city': 'City', 'country': 'Country',
                               'website': f'{slug(a.name)}.example', 'social': {'instagram': '@' + slug(a.name).replace('-', ''), 'linkedin': slug(a.name)}},
                   'units': S['units'], 'offerings': S['offerings'], 'stats': S['stats'],
                   'people': [{'name': 'Alex Example', 'role': 'Director', 'initials': 'AE'}, {'name': 'Sam Sample', 'role': 'Lead', 'initials': 'SS'}, {'name': 'Kim Placeholder', 'role': 'Coordinator', 'initials': 'KP'}],
                   'projects': [{'key': f'project-{i + 1}', 'title': f"{u['name']} — flagship {L['projects'].lower().rstrip('s')}", 'unit': u['key'], 'year': 2026, 'summary': u['summary']} for i, u in enumerate(S['units'][:3])],
                   'events': [{'key': f'event-{i + 1}', 'title': t, 'date': d, 'time': '18:00', 'place': 'Main venue'} for i, (t, d) in enumerate([('Open evening', '2026-11-12'), ('Community meetup', '2026-12-03'), ('Annual showcase', '2027-02-18')])],
                   'posts': [{'key': f'post-{i + 1}', 'title': t, 'date': d, 'category': c} for i, (t, d, c) in enumerate([('A new chapter', '2026-10-01', 'News'), ('What we learned this year', '2026-09-12', 'Insight'), ('Meet the team', '2026-08-20', 'People')])],
                   'testimonials': [{'quote': 'Clear, kind and genuinely useful.', 'name': 'Sample Client', 'role': 'Partner'}],
                   'faq': [{'q': 'How do I get started?', 'a': 'Get in touch and we will reply within two working days.'}]}
        json.dump(content, open(a.content_out, 'w'), indent=2, ensure_ascii=False); print(f'sample content → {a.content_out}')

if __name__ == '__main__':
    main()
