"""
forge_lib.py — shared helpers for every production module (Python side). Import from a module's build.py:

    import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'scripts'))
    import forge_lib as F
    b = F.load(repo)                       # everything the foundations produced, in one object
    html = F.page(b, 'Title', body_html, at='SOCIAL-MEDIA/templates')   # full HTML doc wired to fonts/tokens/core/JS data
    F.shots([{'in': path_html, 'out': path_png, 'w': 1080, 'h': 1080}])  # batch screenshots in ONE browser

Brand object (dict-like + attributes): repo, config, brand, name, p (prefix), G (JS global), dna, profile, content, labels,
tokens (DTCG), colors (colors.json), theme (light theme {token: value}), dark, pal {key: hex}, role {primary, foundation,
paper, accent: hex}, mark (mark.json), parts (logo-parts.json), logo_type, fonts {role: family}, stacks {role: css stack},
langs, lang (primary), path(*parts) → absolute path inside the repo.
"""
import json, os, re, subprocess, html as _html
HERE = os.path.dirname(os.path.abspath(__file__))

class Brand(dict):
    __getattr__ = dict.get
    def path(self, *p): return os.path.join(self['repo'], *p)
    def rel(self, at, target):
        """relative URL from folder `at` (repo-relative) to `target` (repo-relative)"""
        return os.path.relpath(self.path(target), self.path(at)).replace(os.sep, '/')

def _j(p, d=None):
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else ({} if d is None else d)

def load(repo):
    repo = os.path.abspath(repo); R = lambda *x: os.path.join(repo, *x)
    C = _j(R('SOURCE', 'CONFIG', 'brand.config.json')); b = C['brand']
    colors = _j(R('COLORS', 'colors.json')); pal = {p['key']: p['hex'] for p in C['palette']}; roles = C['roles']
    content = _j(R('SOURCE', 'CONFIG', 'content.json')); profile = _j(R('SOURCE', 'CONFIG', 'profile.json'))
    parts = _j(R('SOURCE', 'JSON', 'logo-parts.json'))
    o = Brand(repo=repo, config=C, brand=b, name=b['name'], p=b.get('prefix', 'bx'), G=b.get('global', 'BX'),
              dna=_j(R('SOURCE', 'CONFIG', 'design-dna.json')), profile=profile, content=content,
              labels={**profile.get('labels', {}), **content.get('labels', {})},
              tokens=_j(R('SOURCE', 'JSON', 'design-tokens.json')), colors=colors,
              theme=colors.get('themes', {}).get('light', {}), dark=colors.get('themes', {}).get('dark', {}),
              pal=pal, role={k: pal[roles[k]] for k in ('primary', 'foundation', 'paper', 'accent') if roles.get(k) in pal},
              mark=_j(R('SOURCE', 'JSON', 'mark.json')), parts=parts, logo_type=parts.get('logo_type', C['logo'].get('type', 'symbol')),
              fonts={f['role']: f['family'] for f in C['fonts'].get('families', [])}, stacks=C['fonts'].get('stacks', {}),
              langs=b.get('languages', ['en']), lang=b.get('primary_language', (b.get('languages') or ['en'])[0]))
    return o

def esc(s): return _html.escape(str(s), quote=True)

def page(b, title, body, at, head='', scripts=('mark-data.js', 'wordmark-data.js', 'dna-data.js', 'content-data.js', '{p}-mark.js'), lang=None, theme=None, body_class=''):
    """A complete, file://-safe HTML document placed in repo folder `at` (repo-relative), linked to the brand core."""
    css = b.rel(at, f'SOURCE/CSS/{b.p}-core.css')
    js = ''.join(f'<script src="{b.rel(at, "SOURCE/JS/" + s.replace("{p}", b.p))}"></script>' for s in scripts if os.path.exists(b.path('SOURCE', 'JS', s.replace('{p}', b.p))))
    th = f' data-theme="{theme}"' if theme else ''
    return (f'<!doctype html><html lang="{lang or b.lang}"{th}><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{esc(title)} — {esc(b.name)}</title><link rel="stylesheet" href="{css}">{head}</head>'
            f'<body class="{body_class}">{body}{js}</body></html>')

def svg(b, name):
    """Contents of LOGO/SVG/<name>.svg (e.g. 'logo-original', 'symbol-on-dark', 'compact-white') — '' if missing."""
    p = b.path('LOGO', 'SVG', name + '.svg')
    return open(p).read() if os.path.exists(p) else ''

def shots(jobs, timeout=900):
    """Batch screenshots in one Chromium. jobs: [{'in': html|svg path, 'out': png, 'w': 1200, 'h': 800, 'scale': 1,
    'transparent': False, 'full': False, 'selector': None, 'pdf': False, 'reducedMotion': False, 'theme': None}]
    'pdf': True writes a PDF (w/h in px → page size) · 'reducedMotion': True renders the still state · 'theme': 'dark' emulates colour scheme."""
    if not jobs: return
    tmp = os.path.join(os.path.dirname(os.path.abspath(jobs[0]['out'])), '.shots.json')
    json.dump(jobs, open(tmp, 'w'))
    try: subprocess.run(['node', os.path.join(HERE, 'shots.js'), tmp], check=True, timeout=timeout)
    finally:
        if os.path.exists(tmp): os.remove(tmp)

def write(path, text):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True); open(path, 'w', encoding='utf-8').write(text)

def tok(b, name, theme='light'):
    """A light/dark theme colour token (e.g. 'brand-primary', 'text-secondary') as HEX/rgba."""
    return (b.theme if theme == 'light' else b.dark).get(name)

def categorical(b, n=8, theme='light'):
    """Data/illustration colour order: primary, accent, secondary palette colours, then primary-ramp steps.
    If the charts module ran, its contrast-checked palette (SOURCE/JSON/charts.json) is returned instead."""
    ch = _j(b.path('SOURCE', 'JSON', 'charts.json'))
    cat = ch.get('themes', {}).get(theme, {}).get('categorical')
    if cat: return [c['hex'] if isinstance(c, dict) else c for c in cat][:n]
    out = [b.role.get('primary'), b.role.get('accent')] + [p['hex'] for p in b.config['palette'] if p.get('group') == 'secondary']
    ramps = b.colors.get('ramps', {}); pr = ramps.get('primary', {})
    out += [pr.get(s) for s in ('800', '400', '600', '300', '900', '200') if pr.get(s)]
    seen = []; [seen.append(c) for c in out if c and c.upper() not in [s.upper() for s in seen]]
    return seen[:n]
