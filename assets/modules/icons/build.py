#!/usr/bin/env python3
"""
icons — brand-system-forge production module: the brand's icon system.

  python3 build.py --repo <BRAND-REPO> [--sets core,ui,food] [--all] [--no-previews] [--scale 1.5]

Reads the foundations (design DNA, profile, content, tokens) and draws the brand-neutral icon library
(icons_def.py) in the brand's DNA. Writes (all owned by this module, rewritten on every run):
  ICONS/SVG/<set>/<name>.svg            outline icons (currentColor)
  ICONS/SVG-DUOTONE/<set>/<name>.svg    duotone variant (tint layer at 22 % currentColor)
  ICONS/sprite.svg                      <symbol id="<p>-i-<name>"> (+ "<p>-i-<name>--duotone")
  ICONS/index.html                      gallery (search, set filter, size, outline/duotone, light/dark, copy SVG)
  ICONS/previews/icons-overview.png     specimen · ICONS/previews/sheet-<set>.png per set
  ICONS/README.md · ICONS/qa.json
  SOURCE/JS/<p>-icons.js                <G>.icon(name, opts), <p>-icon element, [data-<p>-icon] hydration
  SOURCE/JSON/icons.json                names, sets, keywords, aliases, inner SVG
"""
import argparse, json, math, os, re, shutil, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(SKILL, 'scripts')); sys.path.insert(0, os.path.join(HERE, 'lib')); sys.path.insert(0, HERE)
import forge_lib as F
import iconkit as K
import icons_def as DEF
try:
    import colorlib as CL
except Exception:
    CL = None

VERSION = '1.0.0'
BASE_SETS = ['ui', 'core']
ACRO = {'id': 'ID', 'dna': 'DNA', 'cctv': 'CCTV', 'wifi': 'Wi-Fi', 'ui': 'UI'}


def human(name):
    words = [ACRO.get(w, w) for w in name.split('-')]
    s = ' '.join(words)
    return s[0].upper() + s[1:]


def cased(text, mode):
    if mode == 'upper': return text.upper()
    if mode == 'title':
        small = {'a', 'an', 'and', 'on', 'of', 'the', 'in', 'to', 'at', 'or'}
        return ' '.join(w if (i and w.lower() in small) else w[:1].upper() + w[1:] for i, w in enumerate(text.split(' ')))
    return text


def walk_icon_keys(obj, out):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == 'icon' and isinstance(v, str): out.append(v)
            else: walk_icon_keys(v, out)
    elif isinstance(obj, list):
        for v in obj: walk_icon_keys(v, out)
    return out


def contrast(a, b):
    if CL:
        try: return CL.contrast(a, b)
        except Exception: pass
    def lum(h):
        h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    la, lb = lum(a), lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def choose_tint(b):
    """Duotone tint for galleries/previews: the brand primary when it separates from the ink, else the accent."""
    ink = b.theme.get('text-primary') or b.role.get('foundation') or '#111111'
    prim, acc = b.role.get('primary'), b.role.get('accent')
    if prim and contrast(prim, ink) >= 3: return prim
    cands = [c for c in (acc, b.theme.get('surface-brand-soft'), prim) if c and str(c).startswith('#')]
    return max(cands, key=lambda c: contrast(c, ink)) if cands else '#999999'


def optical_sw(st, size):
    if size and size < 20: return min(st.sw * 1.35, max(st.sw, 1.3 * 24 / size))
    return st.sw


def svg_tag(r, st, size=24, sw=None, duo=False, tint=None, tint_op=None, extra=''):
    sw = sw if sw is not None else optical_sw(st, size)
    t = ''
    if duo and r['tint']:
        op = tint_op if tint_op is not None else (1 if tint else 0.22)
        t = '<g style="fill:%s;fill-opacity:%s;stroke:none">%s</g>' % (tint or 'currentColor', op, r['tint'])
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="%s" height="%s" fill="none" stroke="currentColor" stroke-width="%s" '
            'stroke-linecap="%s" stroke-linejoin="%s" stroke-miterlimit="3" aria-hidden="true"%s>%s%s</svg>') % (size, size, K.fmt(sw), st.cap, st.join, extra, t, r['outline'])


def svg_file(r, st, label, duo=False):
    t = ('<g fill="currentColor" fill-opacity="0.22" stroke="none">%s</g>' % r['tint']) if duo and r['tint'] else ''
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="%s" '
            'stroke-linecap="%s" stroke-linejoin="%s" stroke-miterlimit="3"><title>%s</title>%s%s</svg>\n') % (K.fmt(st.sw), st.cap, st.join, F.esc(label), t, r['outline'])


def tpl(name):
    return open(os.path.join(HERE, 'templates', name), encoding='utf-8').read()


# =====================================================================================================
def main():
    ap = argparse.ArgumentParser(description='icons module')
    ap.add_argument('--repo', required=True)
    ap.add_argument('--sets', default='', help='comma list overriding the profile sets (core and ui are always included)')
    ap.add_argument('--all', action='store_true', help='include every set of the library')
    ap.add_argument('--no-previews', action='store_true', help='skip the PNG renders')
    ap.add_argument('--scale', type=float, default=1.5, help='device scale of the PNG previews')
    a = ap.parse_args()
    t0 = time.time()
    b = F.load(a.repo)
    st = K.Style(b.dna)
    p, G = b.p, b.G

    # ---- library (+ brand-local custom icons)
    lib = DEF.library()
    custom_p = b.path('SOURCE', 'CONFIG', 'icons-custom.json')
    custom_names = []
    if os.path.exists(custom_p):
        spec = json.load(open(custom_p, encoding='utf-8'))
        for c in spec.get('icons', []):
            ic = {'name': c['name'], 'set': c.get('set', 'core'), 'prims': K.from_json(c['prims']),
                  'keywords': c.get('keywords', '').split() if isinstance(c.get('keywords', ''), str) else c['keywords'],
                  'aliases': c.get('aliases', []), 'label': c.get('label')}
            lib = [x for x in lib if x['name'] != ic['name']] + [ic]
            custom_names.append(ic['name'])
            if ic['set'] not in DEF.SETS: DEF.SETS[ic['set']] = human(ic['set'])
    byname = {ic['name']: ic for ic in lib}
    alias_all = {}
    for ic in lib:
        for al in ic['aliases']:
            if al in byname: raise SystemExit('alias %r of %s clashes with an icon name' % (al, ic['name']))
            if al in alias_all and alias_all[al] != ic['name']: raise SystemExit('alias %r used by %s and %s' % (al, alias_all[al], ic['name']))
            alias_all[al] = ic['name']

    def resolve(key):
        key = str(key).strip().lower()
        return key if key in byname else alias_all.get(key)

    # ---- which sets / icons this brand needs
    known = list(DEF.SET_ORDER) + [s for s in DEF.SETS if s not in DEF.SET_ORDER]
    if a.all: wanted = known
    else:
        prof_sets = [s.strip() for s in (a.sets.split(',') if a.sets else b.profile.get('icons', [])) if s.strip()]
        unknown_sets = [s for s in prof_sets if s not in DEF.SETS]
        if unknown_sets: print('icons: note — no icon set named %s in the library (skipped)' % ', '.join(unknown_sets))
        wanted = BASE_SETS + [s for s in prof_sets if s in DEF.SETS and s not in BASE_SETS]
    keys = walk_icon_keys(b.content, []) + walk_icon_keys(b.profile.get('sample', {}), [])
    extras, missing = [], []
    for k in keys:
        n = resolve(k)
        if not n: missing.append(k); continue
        if byname[n]['set'] not in wanted and n not in extras: extras.append(n)
    missing = sorted(set(missing))
    sel = [ic for ic in lib if ic['set'] in wanted or ic['name'] in extras or ic['name'] in custom_names]
    set_keys = [s for s in known if any(ic['set'] == s for ic in sel)]
    sel.sort(key=lambda ic: (set_keys.index(ic['set']), lib.index(ic)))
    names = [ic['name'] for ic in sel]

    # ---- render + QA
    R = {}; qa_icons = {}; hv_off = []
    for ic in sel:
        r = K.render(ic['prims'], st); R[ic['name']] = r
        q = K.ink(r['geo'], st)
        if q: qa_icons[ic['name']] = q
        for kind, data in r['geo']:
            if kind != 'lines': continue
            for (x1, y1), (x2, y2) in data:
                if abs(x1 - x2) < 1e-6 and abs(y1 - y2) > 0.5 and abs(x1 * 4 - round(x1 * 4)) > 0.02: hv_off.append(ic['name'])
                if abs(y1 - y2) < 1e-6 and abs(x1 - x2) > 0.5 and abs(y1 * 4 - round(y1 * 4)) > 0.02: hv_off.append(ic['name'])
    label = lambda ic: ic.get('label') or human(ic['name'])

    # ---- clean owned outputs
    ICONS = b.path('ICONS')
    for sub in ('SVG', 'SVG-DUOTONE', 'previews'):
        shutil.rmtree(os.path.join(ICONS, sub), ignore_errors=True)
    os.makedirs(ICONS, exist_ok=True)

    # ---- SVG files
    for ic in sel:
        r = R[ic['name']]
        F.write(os.path.join(ICONS, 'SVG', ic['set'], ic['name'] + '.svg'), svg_file(r, st, label(ic)))
        F.write(os.path.join(ICONS, 'SVG-DUOTONE', ic['set'], ic['name'] + '.svg'), svg_file(r, st, label(ic), duo=True))

    # ---- sprite
    gattr = 'fill="none" stroke="currentColor" stroke-width="%s" stroke-linecap="%s" stroke-linejoin="%s" stroke-miterlimit="3"' % (K.fmt(st.sw), st.cap, st.join)
    sym = []
    for ic in sel:
        r = R[ic['name']]
        sym.append('  <symbol id="%s-i-%s" viewBox="0 0 24 24"><title>%s</title><g %s>%s</g></symbol>' % (p, ic['name'], F.esc(label(ic)), gattr, r['outline']))
        if r['tint']:
            sym.append('  <symbol id="%s-i-%s--duotone" viewBox="0 0 24 24"><title>%s</title><g %s><g fill="currentColor" fill-opacity="0.22" stroke="none">%s</g>%s</g></symbol>'
                       % (p, ic['name'], F.esc(label(ic)), gattr, r['tint'], r['outline']))
    F.write(os.path.join(ICONS, 'sprite.svg'),
            '<!-- %s icon sprite v%s — generated by brand-system-forge/assets/modules/icons. Inline it once, then: '
            '<svg class="%s-icon" width="24" height="24" aria-hidden="true"><use href="#%s-i-NAME"/></svg> (duotone: id %s-i-NAME plus the suffix _duotone_ joined by a double hyphen) -->\n'
            '<svg xmlns="http://www.w3.org/2000/svg" style="display:none">\n%s\n</svg>\n' % (F.esc(b.name), VERSION, p, p, p, '\n'.join(sym)))

    # ---- data shared by JS + JSON
    sets_meta = [{'key': s, 'label': DEF.SETS.get(s, human(s)), 'icons': [ic['name'] for ic in sel if ic['set'] == s],
                  'source': 'base' if s in BASE_SETS else ('profile' if s in wanted else 'content')} for s in set_keys]
    aliases = {al: n for al, n in sorted(alias_all.items()) if n in names}
    style_js = {'strokeWidth': st.sw, 'cap': st.cap, 'join': st.join, 'corner': 'organic' if st.organic else st.corner,
                'cutAngle': st.cut_angle, 'faceted': st.faceted, 'organic': st.organic}
    js = (tpl('icons.template.js')
          .replace('{{ICONS}}', '{\n' + ',\n'.join('    %s: [%s, %s]' % (json.dumps(n), json.dumps(R[n]['outline']), json.dumps(R[n]['tint'])) for n in names) + '\n  }')
          .replace('{{META}}', '{\n' + ',\n'.join('    %s: %s' % (json.dumps(ic['name']), json.dumps({'set': ic['set'], 'label': label(ic), 'keywords': ic['keywords'], 'aliases': ic['aliases']}, ensure_ascii=False)) for ic in sel) + '\n  }')
          .replace('{{ALIASES}}', json.dumps(aliases))
          .replace('{{SETS}}', json.dumps([{k: s[k] for k in ('key', 'label', 'icons')} for s in sets_meta]))
          .replace('{{STYLE}}', json.dumps(style_js))
          .replace('{{SETLIST}}', ', '.join(set_keys)).replace('{{COUNT}}', str(len(names))).replace('{{VERSION}}', VERSION)
          .replace('{{SW}}', K.fmt(st.sw)).replace('{{BRAND_NAME}}', b.name).replace('{{G}}', G).replace('{{p}}', p))
    F.write(b.path('SOURCE', 'JS', '%s-icons.js' % p), js)

    data = {'name': '%s icons' % b.name, 'version': VERSION, 'generator': 'brand-system-forge/assets/modules/icons',
            'grid': 24, 'padding': 2, 'live_area': 20, 'viewBox': '0 0 24 24',
            'style': dict(style_js, describe=st.describe()),
            'attrs': {'outline': {'fill': 'none', 'stroke': 'currentColor', 'stroke-width': st.sw, 'stroke-linecap': st.cap, 'stroke-linejoin': st.join, 'stroke-miterlimit': 3},
                      'tint': {'fill': 'currentColor', 'fill-opacity': 0.22, 'stroke': 'none'}},
            'api': {'js': 'SOURCE/JS/%s-icons.js' % p, 'call': '%s.icon(name, {size, label, title, strokeWidth, variant, tint})' % G, 'element': '<%s-icon name size label>' % p,
                    'sprite': 'ICONS/sprite.svg#%s-i-<name>' % p, 'files': 'ICONS/SVG/<set>/<name>.svg', 'duotone_files': 'ICONS/SVG-DUOTONE/<set>/<name>.svg'},
            'sets': sets_meta, 'aliases': aliases,
            'icons': [{'name': ic['name'], 'set': ic['set'], 'label': label(ic), 'keywords': ic['keywords'], 'aliases': ic['aliases'],
                       'file': 'ICONS/SVG/%s/%s.svg' % (ic['set'], ic['name']), 'svg': R[ic['name']]['outline'], 'tint': R[ic['name']]['tint']} for ic in sel],
            'content_icons': sorted(set(k for k in keys)), 'missing': missing}
    F.write(b.path('SOURCE', 'JSON', 'icons.json'), json.dumps(data, ensure_ascii=False, indent=1) + '\n')

    # ---- QA
    areas = [q['area'] for q in qa_icons.values()]
    mean = sum(areas) / len(areas); sd = (sum((x - mean) ** 2 for x in areas) / len(areas)) ** 0.5
    overflow = {n: q['bounds'] for n, q in qa_icons.items() if q['bounds'][0] < 1.5 or q['bounds'][1] < 1.5 or q['bounds'][2] > 22.5 or q['bounds'][3] > 22.5}
    qa = {'style': st.describe(), 'count': len(names), 'padding_rule': 'ink inside 2…22 (tolerance 0.5 for mitred tips)',
          'overflow': overflow, 'weight': {'mean_ink_area': round(mean, 1), 'sd': round(sd, 1),
                                           'heavy': sorted(n for n, q in qa_icons.items() if q['area'] > mean + 2.2 * sd),
                                           'light': sorted(n for n, q in qa_icons.items() if q['area'] < mean - 2.2 * sd)},
          'hv_lines_off_quarter_grid': sorted(set(hv_off)), 'missing_content_icons': missing,
          'icons': qa_icons}
    F.write(os.path.join(ICONS, 'qa.json'), json.dumps(qa, indent=1) + '\n')

    # ---- gallery + previews + README
    tint = choose_tint(b)
    write_gallery(b, st, sel, R, sets_meta, tint)
    jobs = write_previews(b, st, sel, R, sets_meta, tint, keys, resolve, a.scale)
    write_readme(b, st, sel, sets_meta, aliases, missing, extras, custom_names, tint)
    if not a.no_previews:
        F.shots(jobs)
        opt = os.path.join(SKILL, 'scripts', 'optimize_png.js')
        if os.path.exists(opt):
            try:
                import subprocess
                subprocess.run(['node', opt, os.path.join(ICONS, 'previews'), '92'], check=False, timeout=300, capture_output=True)
            except Exception:
                pass
    print('icons: %d SVG (+%d duotone) · %d sets · sprite · %s-icons.js · icons.json · %d previews · %.1fs%s'
          % (len(names), len(names), len(set_keys), p, 0 if a.no_previews else len(jobs), time.time() - t0,
             (' · missing: ' + ', '.join(missing)) if missing else ''))


# =====================================================================================================
#  GALLERY (ICONS/index.html)
# =====================================================================================================
def write_gallery(b, st, sel, R, sets_meta, tint):
    p, G = b.p, b.G
    logo = F.svg(b, 'logo-original') or F.svg(b, 'symbol')
    logo_dark = F.svg(b, 'logo-original-on-dark') or F.svg(b, 'symbol-on-dark') or logo
    strip = lambda s: re.sub(r'<\?xml[^>]*>|<!--.*?-->', '', s, flags=re.S).replace('<svg', '<svg aria-hidden="true" focusable="false"', 1)
    d = st.describe()
    stacked = (b.parts.get('arrangement') == 'stacked') or b.logo_type in ('emblem', 'symbol')
    logo_h = 56 if stacked else 30
    opts = ''.join('<option value="%s">%s (%d)</option>' % (s['key'], F.esc(s['label']), len(s['icons'])) for s in sets_meta)
    search_icon = svg_tag(R['search'], st, 20) if 'search' in R else ''
    body = (tpl('gallery.html')
            .replace('{{LOGO}}', '<span class="ix-logo ix-logo--light">%s</span><span class="ix-logo ix-logo--dark">%s</span>' % (strip(logo), strip(logo_dark)))
            .replace('{{BRAND}}', F.esc(b.name)).replace('{{COUNT}}', str(len(sel))).replace('{{SETCOUNT}}', str(len(sets_meta)))
            .replace('{{TITLE}}', F.esc(cased('Icons', (b.dna.get('type_voice') or {}).get('display_case', 'sentence'))))
            .replace('{{DESCRIBE}}', F.esc('%s px stroke on a 24 px grid · %s · %s · %s · %s' % (d['stroke'], d['caps'], d['joins'], d['corners'], d['curves'])))
            .replace('{{SET_OPTIONS}}', opts).replace('{{SEARCH_ICON}}', search_icon)
            .replace('{{p}}', p).replace('{{G}}', G).replace('{{VERSION}}', VERSION))
    head = '<meta name="description" content="%s icon system: %d icons. Works offline.">' % (F.esc(b.name), len(sel)) + \
           '<style>' + tpl('gallery.css').replace('{{p}}', p).replace('{{TINT}}', tint) + ':root{--ix-logo-h:%dpx}</style>' % logo_h
    html = F.page(b, 'Icons', body, 'ICONS', head=head, scripts=('{p}-icons.js',), lang='en')
    html = html.replace('</body>', '<script>' + tpl('gallery.js').replace('{{G}}', G).replace('{{p}}', p) + '</script></body>')
    F.write(b.path('ICONS', 'index.html'), html)


# =====================================================================================================
#  PREVIEWS (overview specimen + one sheet per set)
# =====================================================================================================
def construction_svg(b, st, r, S=12.5):
    W = 24 * S
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="-28 -22 %s %s" width="%s" height="%s" role="img" aria-label="Icon grid: 24 px, 2 px padding, keylines">' % (W + 40, W + 44, W + 40, W + 44)]
    o.append('<rect x="0" y="0" width="%s" height="%s" fill="var(--ov-cons-bg)"/>' % (W, W))
    o.append('<path fill="var(--ov-pad)" fill-rule="evenodd" d="M0 0H%sV%sH0Z M%s %sV%sH%sV%sZ"/>' % (W, W, 2 * S, 2 * S, 22 * S, 22 * S, 2 * S))
    for i in range(1, 24):
        o.append('<path d="M%s 0V%s M0 %sH%s" stroke="var(--ov-grid)" stroke-width="0.6"/>' % (i * S, W, i * S, W))
    key = 'stroke="var(--ov-key)" stroke-width="1.1" fill="none"'
    o.append('<circle cx="%s" cy="%s" r="%s" %s/>' % (12 * S, 12 * S, 10 * S, key))
    o.append('<rect x="%s" y="%s" width="%s" height="%s" %s/>' % (3 * S, 3 * S, 18 * S, 18 * S, key))
    o.append('<rect x="%s" y="%s" width="%s" height="%s" %s stroke-dasharray="4 4"/>' % (4 * S, 2 * S, 16 * S, 20 * S, key))
    o.append('<rect x="%s" y="%s" width="%s" height="%s" %s stroke-dasharray="4 4"/>' % (2 * S, 4 * S, 20 * S, 16 * S, key))
    o.append('<path d="M%s 0V%s M0 %sH%s M0 0L%s %s M%s 0L0 %s" stroke="var(--ov-key)" stroke-width="0.6" opacity=".55"/>' % (12 * S, W, 12 * S, W, W, W, W, W))
    nse = lambda x: x.replace('<path ', '<path vector-effect="non-scaling-stroke" ').replace('<circle ', '<circle vector-effect="non-scaling-stroke" ').replace('<rect ', '<rect vector-effect="non-scaling-stroke" ')
    o.append('<g transform="scale(%s)" fill="none" stroke="currentColor" stroke-linecap="%s" stroke-linejoin="%s" stroke-miterlimit="3">'
             '<g style="fill:var(--ov-tint);fill-opacity:.45;stroke:none">%s</g>'
             '<g style="color:var(--ov-ink)" stroke-opacity=".2" fill-opacity=".2" stroke-width="%s">%s</g>'
             '<g style="color:var(--ov-key)" stroke-width="1.4">%s</g></g>' % (S, st.cap, st.join, r['tint'], K.fmt(st.sw), r['outline'], nse(r['outline'])))
    t = 'font-family="var(--font-mono)" font-size="10" letter-spacing=".06em" fill="var(--ov-muted)"'
    o.append('<text x="%s" y="-8" %s text-anchor="middle">24</text>' % (W / 2, t))
    o.append('<text x="-8" y="%s" %s text-anchor="end">24</text>' % (W / 2 + 3, t))
    o.append('<text x="%s" y="%s" %s>PAD 2</text>' % (2, W + 16, t))
    o.append('<text x="%s" y="%s" %s text-anchor="end">LIVE 20</text>' % (W, W + 16, t))
    o.append('</svg>')
    return ''.join(o)


def write_previews(b, st, sel, R, sets_meta, tint, keys, resolve, scale):
    p = b.p
    case = (b.dna.get('type_voice') or {}).get('display_case', 'sentence')
    d = st.describe()
    ICONS = b.path('ICONS'); PV = os.path.join(ICONS, 'previews')
    names = [ic['name'] for ic in sel]
    byname = {ic['name']: ic for ic in sel}
    content_icons = []
    for k in keys:
        n = resolve(k)
        if n and n in R and n not in content_icons: content_icons.append(n)
    if st.faceted: lead_k = 'Cut, faceted, exact.'
    elif st.organic: lead_k = 'Soft, never stiff.'
    elif st.corner == 'cut': lead_k = 'Cut, not rounded.'
    elif st.corner in ('round', 'soft'): lead_k = 'Round, open, friendly.'
    else: lead_k = 'Square and precise.'
    sample = 'pin' if st.faceted else ('chat' if st.organic or st.corner in ('round', 'soft') else 'calendar')
    if sample not in R: sample = names[0]
    css = tpl('specimen.css').replace('{{TINT}}', tint).replace('{{p}}', p)
    head = '<style>' + css + '</style>'

    def tile(n, size=28, duo=False):
        return '<div class="ov-tile">%s<span>%s</span></div>' % (svg_tag(R[n], st, size, duo=duo, tint='var(--ov-tint)', tint_op=0.85 if duo else None), n)

    # sizes row
    pick = []
    for n in ['search', 'calendar', 'user', 'heart', 'settings'] + content_icons:
        if n in R and n not in pick: pick.append(n)
    pick = pick[:7]
    sizes = ''.join('<div class="ov-size"><div class="ov-size-row">%s</div><span>%s</span></div>' %
                    (''.join(svg_tag(R[n], st, s) for n in pick), '%d px%s' % (s, ' · optical %s' % K.fmt(optical_sw(st, s)) if s < 20 else '')) for s in (16, 24, 32, 48))
    ground_icons = (content_icons + [n for n in names if n not in content_icons and byname[n]['set'] not in ('ui',)])[:7]
    grounds = ''.join(('<div class="ov-ground ov-ground--%s ' + p + '-shape"><span class="ov-ground-l">%s</span><div class="ov-ground-row">%s</div><div class="ov-ground-row">%s</div></div>') %
                      (k, l, ''.join(svg_tag(R[n], st, 32) for n in ground_icons),
                       ''.join(svg_tag(R[n], st, 32, duo=True, tint='var(--gr-tint)', tint_op=1) for n in ground_icons))
                      for k, l in (('light', 'Light'), ('dark', 'Dark'), ('primary', 'Primary')))
    bands = []
    for i, s in enumerate(sets_meta):
        note = {'base': 'always', 'profile': 'profile set', 'content': 'used by content.json'}[s['source']]
        bands.append('<section class="ov-band"><div class="ov-band-h"><span><b>%02d</b>%s</span><span>%s · %d</span></div><div class="ov-grid">%s</div></section>'
                     % (i + 1, F.esc(s['label']), note, len(s['icons']), ''.join(tile(n) for n in s['icons'])))
    spec = ''.join('<dt>%s</dt><dd>%s</dd>' % (k, v) for k, v in (
        ('Grid', '24 × 24 · padding 2 · live area 20'), ('Stroke', '%s at 24 px · %s · %s' % (d['stroke'], d['caps'], d['joins'])),
        ('Corners', d['corners']), ('Curves', d['curves']),
        ('Sets', '%d sets · %s' % (len(sets_meta), ', '.join(s['key'] for s in sets_meta))),
        ('Keylines', 'circle 20 · square 18 · portrait 16×20 · landscape 20×16')))
    title = cased('%d icons, drawn on one grid.' % len(sel), case)
    body = ('<main class="ov"><header class="ov-head"><div><div class="ov-eyebrow"><span>%s</span><span>Icon system</span><b>v%s</b></div>'
            '<h1 class="ov-h1">%s</h1><p class="ov-lead"><strong>%s</strong> %s px strokes with %s and %s; %s; %s.</p></div>'
            '<div class="ov-cons-wrap"><figure class="ov-cons">%s</figure><dl class="ov-spec">%s</dl></div></header>'
            '<section class="ov-band ov-band--sizes"><div class="ov-band-h"><span><b>A</b>Sizes · same drawing, optical stroke below 20 px</span></div><div class="ov-sizes">%s</div></section>'
            '<section class="ov-band"><div class="ov-band-h"><span><b>B</b>Grounds · outline and duotone</span></div><div class="ov-grounds">%s</div></section>'
            '%s<footer class="ov-foot"><span>Shown at 28 px · currentColor</span><span>Decorative: aria-hidden · standalone: role="img" + label</span>'
            '<span>%s.icon(name, {size, label}) · ICONS/SVG/&lt;set&gt;/&lt;name&gt;.svg</span></footer></main>') % (
        F.esc(b.name), VERSION, F.esc(title), F.esc(lead_k), d['stroke'], d['caps'], d['joins'], d['corners'], d['curves'],
        construction_svg(b, st, R[sample]), spec, sizes, grounds, ''.join(bands), b.G)
    F.write(os.path.join(PV, 'overview.html'), F.page(b, 'Icon overview', body, 'ICONS/previews', head=head, scripts=(), lang='en', body_class='ov-body'))

    # sheets
    sheets = []
    for i, s in enumerate(sets_meta):
        ics = s['icons']
        sheets.append(('<section class="sh" id="set-%s"><header class="sh-head"><div class="ov-eyebrow"><span>%s</span><span>Icon set %02d / %02d</span><b>%d icons</b></div>'
                       '<h2 class="sh-h">%s</h2><p class="sh-meta">%s px · %s · %s · %s</p></header>'
                       '<div class="sh-grid">%s</div>'
                       '<div class="sh-row"><span class="sh-l">16 px</span><div>%s</div></div>'
                       '<div class="sh-row"><span class="sh-l">24 px</span><div>%s</div></div>'
                       '<div class="sh-row"><span class="sh-l">Duotone</span><div>%s</div></div>'
                       '<div class="sh-row sh-row--dark %s-shape"><span class="sh-l">On dark</span><div>%s</div></div></section>') % (
            s['key'], F.esc(b.name), i + 1, len(sets_meta), len(ics), F.esc(cased(s['label'], case)), d['stroke'], d['caps'], d['joins'], d['corners'],
            ''.join('<div class="sh-tile">%s<span>%s</span></div>' % (svg_tag(R[n], st, 48), n) for n in ics),
            ''.join(svg_tag(R[n], st, 16) for n in ics), ''.join(svg_tag(R[n], st, 24) for n in ics),
            ''.join(svg_tag(R[n], st, 32, duo=True, tint='var(--ov-tint)', tint_op=0.85) for n in ics),
            p, ''.join(svg_tag(R[n], st, 24) for n in ics)))
    script = ('<script>(function(){var h=location.hash.slice(1);if(!h)return;document.documentElement.classList.add("one");'
              'var e=document.getElementById("set-"+h);if(e)e.classList.add("on");})();</script>')
    F.write(os.path.join(PV, 'sheets.html'), F.page(b, 'Icon sets', '<main class="shs">%s</main>%s' % (''.join(sheets), script), 'ICONS/previews', head=head, scripts=(), lang='en', body_class='ov-body'))
    jobs = [{'in': os.path.join(PV, 'overview.html'), 'out': os.path.join(PV, 'icons-overview.png'), 'w': 1600, 'h': 1200, 'full': True, 'scale': scale, 'wait': 400}]
    for s in sets_meta:
        jobs.append({'in': 'file://' + os.path.join(PV, 'sheets.html') + '#' + s['key'], 'out': os.path.join(PV, 'sheet-%s.png' % s['key']), 'w': 1200, 'h': 600, 'full': True, 'scale': scale, 'wait': 300})
    return jobs


# =====================================================================================================
#  README (ICONS/README.md)
# =====================================================================================================
def write_readme(b, st, sel, sets_meta, aliases, missing, extras, custom_names, tint):
    p, G = b.p, b.G
    d = st.describe()
    rows = '\n'.join('| `%s` | %s | %d | %s |' % (s['key'], s['label'], len(s['icons']), {'base': 'always', 'profile': 'profile', 'content': 'content.json'}[s['source']]) for s in sets_meta)
    ex = ', '.join('`%s`' % n for n in extras) or '—'
    txt = tpl('README.icons.md')
    for k, v in {'{{BRAND}}': b.name, '{{p}}': p, '{{G}}': G, '{{COUNT}}': str(len(sel)), '{{SETCOUNT}}': str(len(sets_meta)), '{{SETROWS}}': rows,
                 '{{STROKE}}': d['stroke'], '{{CAPS}}': d['caps'], '{{JOINS}}': d['joins'], '{{CORNERS}}': d['corners'], '{{CURVES}}': d['curves'],
                 '{{CAP}}': st.cap, '{{JOIN}}': st.join, '{{EXTRAS}}': ex, '{{MISSING}}': (', '.join('`%s`' % m for m in missing) if missing else 'none'),
                 '{{CUSTOM}}': (', '.join('`%s`' % n for n in custom_names) if custom_names else 'none yet'), '{{VERSION}}': VERSION,
                 '{{PROFILE}}': b.profile.get('key', b.brand.get('profile', '')), '{{TINT}}': tint}.items():
        txt = txt.replace(k, v)
    F.write(b.path('ICONS', 'README.md'), txt)


if __name__ == '__main__':
    main()
