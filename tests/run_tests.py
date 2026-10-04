#!/usr/bin/env python3
"""
run_tests.py — regression tests for the skill on the fictional test brands (tests/brands.json).

usage: python3 tests/run_tests.py --out /tmp/forge-test [--only northwind,luma] [--lite] [--skip-build]
  1. analysis classification of every test logo vs the expected type / geometry / complexity
  2. new_brand.py for each brand (foundations), optionally --lite (all modules)
  3. checks: required foundation files exist, JSON/SVG parse, contrast report passes, validate_repo + check_links clean
Exit code 1 if anything fails. Boards to LOOK at: <out>/<BRAND>/BRAND-BOOK/foundation-board.png
"""
import argparse, json, os, subprocess, sys, glob
HERE = os.path.dirname(os.path.abspath(__file__)); SKILL = os.path.dirname(HERE); S = os.path.join(SKILL, 'scripts')
REQUIRED = ['SOURCE/CONFIG/brand.config.json', 'SOURCE/CONFIG/design-dna.json', 'SOURCE/CONFIG/profile.json', 'SOURCE/CONFIG/content.json',
            'SOURCE/JSON/mark.json', 'SOURCE/JSON/logo-parts.json', 'SOURCE/JSON/design-tokens.json', 'SOURCE/JS/mark-data.js', 'SOURCE/JS/wordmark-data.js',
            'SOURCE/JS/dna-data.js', 'SOURCE/JS/content-data.js', 'SOURCE/CSS/tokens.css', 'SOURCE/CSS/colors.css', 'SOURCE/CSS/fonts.css',
            'LOGO/SVG/symbol.svg', 'LOGO/SVG/logo-original.svg', 'LOGO/SVG/compact.svg', 'COLORS/colors.json', 'COLORS/contrast-report.json',
            'BRAND-BOOK/foundation-board.png']

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True); ap.add_argument('--only', default=''); ap.add_argument('--lite', action='store_true')
    ap.add_argument('--skip-build', action='store_true')
    a = ap.parse_args(); B = json.load(open(os.path.join(HERE, 'brands.json'))); fails = []
    os.makedirs(a.out, exist_ok=True)
    for t in B['brands'] + B['analysis_only']:
        out = os.path.join(a.out, '_analysis', os.path.basename(t['logo']).split('.')[0])
        subprocess.run([sys.executable, os.path.join(S, 'analyze_logo.py'), os.path.join(HERE, t['logo']), '--out', out], check=True, capture_output=True)
        A = json.load(open(os.path.join(out, 'logo-analysis.json')))
        bad = {k: (A[k], v) for k, v in t['expect'].items() if A[k] != v}
        print(('FAIL ' if bad else 'ok   ') + f"analysis {t['logo']}: " + (str(bad) if bad else f"{A['logo_type']} · {A['geometry']} · {A['complexity']}"))
        if bad: fails.append(f"analysis {t['logo']} {bad}")
    for t in B['brands']:
        if a.only and t['key'] not in a.only.split(','): continue
        repo = os.path.join(a.out, t['name'].upper().replace(' ', '-') + '-BRAND')
        if not a.skip_build:
            cmd = [sys.executable, os.path.join(S, 'new_brand.py'), '--logo', os.path.join(HERE, t['logo']), '--name', t['name'], '--profile', t['profile'],
                   '--languages', t['languages'], '--repo', repo] + (['--descriptor', t['descriptor']] if t.get('descriptor') else []) + \
                  (['--local-name', t['local_name']] if t.get('local_name') else []) + (['--lite'] if a.lite else [])
            r = subprocess.run(cmd, capture_output=True, text=True)
            open(os.path.join(a.out, t['key'] + '.log'), 'w').write(r.stdout + r.stderr)
            if r.returncode: fails.append(f"build {t['key']} (see {t['key']}.log)"); print(f"FAIL build {t['key']}\n" + r.stderr[-1500:]); continue
        miss = [f for f in REQUIRED if not os.path.exists(os.path.join(repo, f))]
        rep = json.load(open(os.path.join(repo, 'COLORS', 'contrast-report.json')))
        low = [f'{tn}:{k}={v}' for tn, d in rep['themes'].items() for k, v in d.items() if v < (3 if k.startswith(('focus', 'border')) else 4.5)]
        badsvg = []
        import xml.etree.ElementTree as ET
        for f in glob.glob(os.path.join(repo, '**', '*.svg'), recursive=True):
            try: ET.parse(f)
            except Exception: badsvg.append(os.path.relpath(f, repo))
        v = subprocess.run([sys.executable, os.path.join(S, 'validate_repo.py'), repo], capture_output=True, text=True)
        l = subprocess.run([sys.executable, os.path.join(S, 'check_links.py'), repo], capture_output=True, text=True)
        probs = (['missing ' + ', '.join(miss)] if miss else []) + (['contrast ' + ', '.join(low)] if low else []) + (['bad svg ' + ', '.join(badsvg[:5])] if badsvg else []) + \
                (['validate: ' + v.stdout.strip()[-400:]] if v.returncode else []) + (['links: ' + l.stdout.strip()[-400:]] if l.returncode else [])
        print(('FAIL ' if probs else 'ok   ') + f"{t['key']}: " + ('; '.join(probs) if probs else f'{sum(len(fs) for _, _, fs in os.walk(repo))} files'))
        if probs: fails.append(f"{t['key']}: {probs}")
    print('\n' + ('ALL PASSED' if not fails else f'{len(fails)} FAILURES'))
    sys.exit(1 if fails else 0)

if __name__ == '__main__':
    main()
