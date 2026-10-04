#!/usr/bin/env python3
"""
build_font_catalogue.py — (re)build assets/fonts-catalogue.json from assets/fonts-seed.txt.

Seed line format:  <v|s> <fontsource-slug> <roles comma list>|<character tags comma list>
  v = @fontsource-variable/<slug>   s = @fontsource/<slug> (static)
Installs every package into a cache (npm), reads metadata.json (family, subsets, weights, styles, variable axes, licence)
and lists the CSS entry files, so fetch_fonts.py / auto_config.py can pick fonts by role, script and character.
usage: python3 scripts/build_font_catalogue.py [--cache /tmp/forge-fonts]
"""
import argparse, json, os, subprocess, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
ap = argparse.ArgumentParser(); ap.add_argument('--cache', default=os.path.join(tempfile.gettempdir(), 'forge-font-catalogue'))
a = ap.parse_args(); os.makedirs(a.cache, exist_ok=True)
seed = [l.split() for l in open(os.path.join(ROOT, 'assets', 'fonts-seed.txt')) if l.strip() and not l.startswith('#')]
pk = lambda t, s: ('@fontsource-variable/' if t == 'v' else '@fontsource/') + s
if not os.path.exists(os.path.join(a.cache, 'package.json')): subprocess.check_call(['npm', 'init', '-y'], cwd=a.cache, stdout=subprocess.DEVNULL)
subprocess.check_call(['npm', 'install', '--silent', '--no-audit', '--no-fund'] + [pk(t, s) for t, s, _ in seed], cwd=a.cache)
OVERUSED = {'inter', 'space-grotesk', 'poppins', 'montserrat', 'roboto', 'open-sans', 'lato', 'playfair-display', 'caveat'}
cat = []
for t, s, rest in seed:
    roles, tags = rest.split('|')
    d = os.path.join(a.cache, 'node_modules', *pk(t, s).split('/'))
    m = json.load(open(os.path.join(d, 'metadata.json')))
    css = sorted(f for f in os.listdir(d) if f.endswith('.css'))
    axes = m.get('variable') or {}
    entry = 'full.css' if 'full.css' in css else 'standard.css' if 'standard.css' in css else 'index.css'
    cat.append({'family': m['family'], 'slug': s, 'package': pk(t, s), 'variable': t == 'v', 'category': m.get('category'),
                'roles': roles.split(','), 'tags': tags.split(','), 'subsets': m.get('subsets', []), 'weights': m.get('weights', []),
                'styles': m.get('styles', []), 'axes': {k: [float(v['min']), float(v['max'])] for k, v in axes.items()} if axes else {},
                'css_files': css, 'recommended_css': [entry] + (['wght-italic.css'] if 'wght-italic.css' in css else []) if t == 'v' else [c for c in css if c[:3].isdigit()][:4] or ['index.css'],
                'license': (m.get('license') or {}).get('type'), 'overused': s in OVERUSED})
json.dump({'note': 'Curated open-source families (Fontsource/npm). Pick by role + script coverage (subsets) + character tags. Avoid "overused" defaults.',
           'families': cat}, open(os.path.join(ROOT, 'assets', 'fonts-catalogue.json'), 'w'), indent=1)
print(f'{len(cat)} families → assets/fonts-catalogue.json')
