#!/usr/bin/env python3
"""
new_brand.py — one command from "logo + name + company type" to a brand repository with all foundations.

usage:
  python3 scripts/new_brand.py --logo logo.png --name "Northwind Studio" --profile professional-services \
      --repo ../NORTHWIND-STUDIO-BRAND [--languages en,de] [--descriptor "Design consultancy"] [--tagline "…"]
      [--legal-name "…"] [--local-name "…"] [--content my-content.json] [--lite] [--seed 0]

Steps
  1. copy the logo into <repo>/LOGO/PNG (never modified) and analyse it
  2. auto_config.py → <repo>/SOURCE/CONFIG/brand.config.json (+ sample content.json from the profile unless --content)
  3. foundation.py  → mark, logo assets, fonts, lettering, tokens, core CSS/JS, foundation board
  4. --lite         → lite.py runs every module the profile asks for (complete system, no hand art-direction)
Afterwards: review the config, the DNA and the board; edit; re-run foundation.py --only … ; then the modules.
Profiles: nonprofit-ngo · saas-tech · professional-services · retail-ecommerce · hospitality-food · health-wellness ·
          education-culture · industrial-energy   (assets/profiles/*.json)
"""
import argparse, json, os, re, shutil, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))

def run(cmd): print('$', ' '.join(cmd), flush=True); subprocess.check_call(cmd)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--logo', required=True); ap.add_argument('--name', required=True); ap.add_argument('--profile', required=True); ap.add_argument('--repo', required=True)
    ap.add_argument('--languages', default='en'); ap.add_argument('--descriptor', default=''); ap.add_argument('--tagline', default='')
    ap.add_argument('--legal-name', default=''); ap.add_argument('--local-name', default=''); ap.add_argument('--content'); ap.add_argument('--lite', action='store_true')
    ap.add_argument('--seed', default='0')
    a = ap.parse_args(); py = sys.executable; repo = os.path.abspath(a.repo)
    slug = re.sub(r'[^a-z0-9]+', '-', a.name.lower()).strip('-'); ext = os.path.splitext(a.logo)[1].lower()
    for d in ('LOGO/PNG', 'LOGO/SVG', 'SOURCE/CONFIG', 'SOURCE/SCRIPTS/_work'): os.makedirs(os.path.join(repo, d), exist_ok=True)
    art = os.path.join(repo, 'LOGO', 'SVG' if ext == '.svg' else 'PNG', f'{slug}-original-artwork{ext}')
    shutil.copy(a.logo, art)
    work = os.path.join(repo, 'SOURCE', 'SCRIPTS', '_work'); cfg = os.path.join(repo, 'SOURCE', 'CONFIG', 'brand.config.json')
    run([py, os.path.join(HERE, 'analyze_logo.py'), art, '--out', os.path.join(work, 'analysis')])
    content = os.path.join(repo, 'SOURCE', 'CONFIG', 'content.json')
    if a.content: shutil.copy(a.content, content)
    run([py, os.path.join(HERE, 'auto_config.py'), '--analysis', os.path.join(work, 'analysis', 'logo-analysis.json'), '--logo', art, '--name', a.name,
         '--profile', a.profile, '--languages', a.languages, '--descriptor', a.descriptor, '--tagline', a.tagline, '--legal-name', a.legal_name,
         '--local-name', a.local_name, '--out', cfg, '--content-out', content, '--seed', a.seed])
    run([py, os.path.join(HERE, 'foundation.py'), '--config', cfg, '--repo', repo, '--skip', 'analyze'])
    if a.lite: run([py, os.path.join(HERE, 'lite.py'), '--repo', repo])
    print(f'\n{a.name}: foundations ready in {repo}. Board: BRAND-BOOK/foundation-board.png')

if __name__ == '__main__':
    main()
