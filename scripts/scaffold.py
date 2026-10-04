#!/usr/bin/env python3
"""
scaffold.py — create a new brand repository skeleton from brand.config.json.

Creates the standard folder tree (references/repo-structure.md; profile-specific folders come from the modules),
copies the logo artwork, the config, the profile, the content file (+ content-data.js)
and a self-contained copy of the forge scripts into SOURCE/SCRIPTS/forge/ so the repository can regenerate itself.

usage: python3 scripts/scaffold.py --config brand.config.json --repo ../ACME-BRAND [--content content.json]
"""
import argparse, json, os, re, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); SKILL = os.path.dirname(HERE)

TREE = ['BRAND-BOOK', 'LOGO/SVG', 'LOGO/PNG', 'COLORS', 'UI-DESIGN-SYSTEM/tokens',       # modules create their own folders
        'SOURCE/SVG', 'SOURCE/JSON', 'SOURCE/CSS', 'SOURCE/JS', 'SOURCE/CONFIG', 'SOURCE/FONTS', 'SOURCE/SCRIPTS']

def render(text, C):
    b = C['brand']
    rep = {'{{p}}': b.get('prefix', 'bx'), '{{G}}': b.get('global', 'BX'), '{{BRAND_NAME}}': b['name'],
           '{{PROFILE}}': b.get('profile', ''), '{{MARK_NOUN}}': b.get('mark_noun', 'mark')}
    for k, v in rep.items(): text = text.replace(k, v)
    return text

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--config', required=True); ap.add_argument('--repo', required=True)
    ap.add_argument('--content'); a = ap.parse_args()
    cfgdir = os.path.dirname(os.path.abspath(a.config)); C = json.load(open(a.config)); b = C['brand']
    R = lambda *x: os.path.join(a.repo, *x)
    for d in TREE: os.makedirs(R(d), exist_ok=True)
    art = C['logo']['artwork']; art = art if os.path.isabs(art) else os.path.join(cfgdir, art)
    slug = re.sub(r'[^a-z0-9]+', '-', b['name'].lower()).strip('-')
    ext = os.path.splitext(art)[1].lower()
    def cp(src, dst):
        if not (os.path.exists(dst) and os.path.samefile(src, dst)): shutil.copy(src, dst)
    cp(art, R('LOGO', 'PNG' if ext != '.svg' else 'SVG', f'{slug}-original-artwork{ext}'))
    cp(a.config, R('SOURCE', 'CONFIG', 'brand.config.json'))
    prof = b.get('profile')
    if prof:
        pp = prof if os.path.exists(prof) else os.path.join(SKILL, 'assets', 'profiles', prof + '.json')
        if os.path.exists(pp): cp(pp, R('SOURCE', 'CONFIG', 'profile.json'))
    content = a.content or C.get('content')
    if content:
        content = content if os.path.isabs(content) else os.path.join(cfgdir, content)
        if os.path.exists(content):
            d = json.load(open(content)); cp(content, R('SOURCE', 'CONFIG', 'content.json'))
            open(R('SOURCE', 'JS', 'content-data.js'), 'w').write(
                f"/* {b['name']} content — generated from SOURCE/CONFIG/content.json. SAMPLE DATA where marked: replace before public use. */\n"
                f"window.{b.get('global', 'BX')}_CONTENT=" + json.dumps(d, ensure_ascii=False, separators=(',', ':')) + ';\n')
    dst = R('SOURCE', 'SCRIPTS', 'forge')      # self-contained copy: scripts + assets (modules, profiles, starter, catalogue)
    if os.path.exists(dst): shutil.rmtree(dst)
    ign = shutil.ignore_patterns('__pycache__', '*.pyc', 'node_modules', 'preview*.jpg', 'preview*.png')
    shutil.copytree(HERE, os.path.join(dst, 'scripts'), ignore=ign)
    shutil.copytree(os.path.join(SKILL, 'assets'), os.path.join(dst, 'assets'), ignore=ign)
    for f in ('package.json', 'requirements.txt'):
        if os.path.exists(os.path.join(SKILL, f)): shutil.copy(os.path.join(SKILL, f), os.path.join(dst, f))
    print(f'scaffolded {a.repo} · prefix "{b.get("prefix", "bx")}" · global {b.get("global", "BX")} · profile {prof} · artwork → LOGO/')

if __name__ == '__main__':
    main()
