#!/usr/bin/env python3
"""
foundation.py — build every FOUNDATION of a brand system in one command.

  scaffold → analyse logo → separate parts → design DNA → vectorise parts → mark + logo assets → fonts
  → lettering → tokens → core CSS/JS → foundation board (HTML + PNG) for visual QA

usage:
  python3 scripts/foundation.py --config <repo>/SOURCE/CONFIG/brand.config.json --repo <repo> [--content content.json]
         [--skip fonts,vectorize,...]  [--only tokens,core,board]
Steps: scaffold · analyze · separate · dna · vectorize · mark · fonts · wordmark · tokens · core · board · docs
Work files (analysis, part crops, label maps, meshes, comparisons) go to <repo>/SOURCE/SCRIPTS/_work/.
Tip: scripts/new_brand.py runs analyse → auto_config → this script for a brand-new logo.
"""
import argparse, json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
STEPS = ['scaffold', 'analyze', 'separate', 'dna', 'vectorize', 'mark', 'fonts', 'wordmark', 'tokens', 'core', 'board', 'docs']

def run(cmd):
    print('$', ' '.join(cmd), flush=True); subprocess.check_call(cmd)

def svg_native(svg_path, out):
    """Minimal SVG → mesh JSON: <path d fill> and <polygon points fill>. Flatten transforms first (e.g. svgo / Inkscape)."""
    s = open(svg_path).read(); facets = []
    vb = re.search(r'viewBox="([^"]+)"', s); W, H = (float(v) for v in vb.group(1).split()[2:4]) if vb else (1000, 1000)
    for i, m in enumerate(re.finditer(r'<(path|polygon)\b([^>]*)/?>', s)):
        attrs = m.group(2); fill = re.search(r'fill="(#[0-9A-Fa-f]{3,6})"', attrs) or re.search(r'fill:\s*(#[0-9A-Fa-f]{3,6})', attrs)
        if not fill: continue
        col = fill.group(1).upper()
        if len(col) == 4: col = '#' + ''.join(c * 2 for c in col[1:])
        if m.group(1) == 'path':
            d = re.search(r'\sd="([^"]+)"', attrs).group(1); facets.append({'id': i + 1, 'color': col, 'd': d, 'area': 0})
        else:
            pts = [float(v) for v in re.findall(r'-?\d+\.?\d*', re.search(r'points="([^"]+)"', attrs).group(1))]
            facets.append({'id': i + 1, 'color': col, 'points': [[x, y] for x, y in zip(pts[0::2], pts[1::2])], 'area': 0})
    kind = 'polygons' if all('points' in f for f in facets) else 'paths'
    json.dump({'width': W, 'height': H, 'facets': facets, 'kind': kind}, open(out, 'w'))
    print(f'svg-native: {len(facets)} shapes → {out}')

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--config', required=True); ap.add_argument('--repo', required=True)
    ap.add_argument('--content'); ap.add_argument('--skip', default=''); ap.add_argument('--only', default='')
    a = ap.parse_args()
    cfg_path = os.path.abspath(a.config); cfgdir = os.path.dirname(cfg_path); C = json.load(open(cfg_path))
    repo = os.path.abspath(a.repo); work = os.path.join(repo, 'SOURCE', 'SCRIPTS', '_work'); os.makedirs(work, exist_ok=True)
    steps = [s for s in (a.only.split(',') if a.only else STEPS) if s and s not in a.skip.split(',')]
    py = sys.executable; T = lambda f: os.path.join(HERE, f)
    art = C['logo']['artwork']; art = art if os.path.isabs(art) else os.path.join(cfgdir, art)
    A_path = os.path.join(work, 'analysis', 'logo-analysis.json'); parts_dir = os.path.join(work, 'parts')
    if 'scaffold' in steps:
        run([py, T('scaffold.py'), '--config', cfg_path, '--repo', repo] + (['--content', os.path.abspath(a.content)] if a.content else []))
    if 'analyze' in steps:
        run([py, T('analyze_logo.py'), art, '--out', os.path.join(work, 'analysis')])
    if 'separate' in steps:
        run([py, T('separate_lockup.py'), art, '--analysis', A_path, '--out', parts_dir] + (['--type', C['logo']['type']] if C['logo'].get('type') else []))
    if 'dna' in steps:
        prof = C['brand'].get('profile') or 'professional-services'
        run([py, T('derive_dna.py'), '--analysis', A_path, '--profile', prof, '--config', cfg_path, '--out', os.path.join(repo, 'SOURCE', 'CONFIG', 'design-dna.json')])
    if 'vectorize' in steps:
        A = json.load(open(A_path)); parts = json.load(open(os.path.join(parts_dir, 'logo-parts.json')))
        T_ = parts['logo_type']; vz = C['logo'].get('vectorize', {})
        route = vz.get('route') or A['suggested_route']
        if route == 'hybrid': route = 'faceted-mesh'
        if T_ == 'wordmark' and route == 'faceted-mesh': route = 'flat-trace'
        mark_png = os.path.join(parts_dir, parts['crops']['lettering' if T_ == 'wordmark' else 'symbol']['file'])
        levels = vz.get('levels') or ({'master': {}, 'simplified': {'thresh': 34, 'amin': 900, 'nseg': 600, 'maj': 7, 'tol_in': 14}}
                                      if route == 'faceted-mesh' else {'master': {'colors': 'auto'}, 'simplified': {'colors': 'auto', 'max_colors': 3, 'mode': 'polygon'}})
        mesh = os.path.join(work, 'mesh'); os.makedirs(mesh, exist_ok=True)
        ncol = {v['file']: v.get('colours', 3) for v in parts['crops'].values()}
        def flat(png, out, p):
            n = p.get('colors', 'auto'); n = ncol.get(os.path.basename(png), 3) if n in (None, 'auto') else n
            n = min(n, p.get('max_colors', 99))
            run([py, T('vectorize/trace_flat.py'), png, '--out', out, '--colors', str(n), '--mode', p.get('mode', 'spline')])
        for name, p in levels.items():
            out = os.path.join(mesh, f'{name}-mesh.json')
            if route == 'faceted-mesh':
                run([py, T('vectorize/facetize.py'), mark_png, '--out', mesh, '--name', name, '--thresh', str(p.get('thresh', 20)), '--amin', str(p.get('amin', 180)),
                     '--nseg', str(p.get('nseg', 1100)), '--maj', str(p.get('maj', 5))])
                run([py, T('vectorize/topomesh.py'), os.path.join(mesh, f'{name}-labels.npy'), '--logo', mark_png, '--out', out,
                     '--tol-in', str(p.get('tol_in', 16)), '--tol-sil', str(p.get('tol_sil', 1.6)), '--snap', str(p.get('snap', 5)),
                     '--preview', os.path.join(mesh, f'{name}-compare.png')])
            elif route == 'svg-native':
                svg_native(art, out)
            else:   # flat-trace · gradient-raster (posterised trace; the raster stays primary)
                flat(mark_png, out, p)
            C['logo'].setdefault('levels', {})[name] = os.path.relpath(out, cfgdir)
        lt = C['logo'].get('lettering', {'colors': 'auto', 'max_colors': 3, 'mode': 'spline'})
        if T_ == 'combination' and 'lettering' in parts['crops']:
            flat(os.path.join(parts_dir, 'lettering.png'), os.path.join(mesh, 'lettering-mesh.json'), lt)
        if T_ == 'wordmark' and 'monogram' in parts['crops']:
            flat(os.path.join(parts_dir, 'monogram.png'), os.path.join(mesh, 'monogram-mesh.json'), lt)
        json.dump(C, open(cfg_path, 'w'), indent=2, ensure_ascii=False)   # record mesh paths in the config
    if 'mark' in steps: run([py, T('build_mark.py'), '--config', cfg_path, '--repo', repo, '--work', work])
    if 'fonts' in steps: run([py, T('fetch_fonts.py'), '--config', cfg_path, '--repo', repo])
    if 'wordmark' in steps and C.get('wordmark'): run([py, T('build_wordmark.py'), '--config', cfg_path, '--repo', repo])
    if 'tokens' in steps: run([py, T('build_tokens.py'), '--config', cfg_path, '--repo', repo])
    if 'core' in steps: run([py, T('build_core.py'), '--config', cfg_path, '--repo', repo])
    if 'board' in steps: run([py, T('foundation_board.py'), '--config', cfg_path, '--repo', repo])
    if 'docs' in steps:
        run([py, T('build_spec.py'), '--repo', repo]); run([py, T('build_docs.py'), '--repo', repo])
    print('\nFoundations ready. LOOK at BRAND-BOOK/foundation-board.png and SOURCE/SCRIPTS/_work/{analysis/logo-parts.png, mesh/*-compare.png},'
          ' review SOURCE/CONFIG/design-dna.json, then run the modules (scripts/lite.py) or the full specialist phases.')

if __name__ == '__main__':
    main()
