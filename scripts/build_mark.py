#!/usr/bin/env python3
"""
build_mark.py — canonical vector data + every symbol variant, from the vectorised logo parts.

usage: python3 scripts/build_mark.py --config brand.config.json --repo ../ACME-BRAND [--work <repo>/SOURCE/SCRIPTS/_work]

Reads
  brand.config.json  brand.prefix/global/name · palette · roles · logo.levels.{master,simplified}
  <work>/parts/logo-parts.json + parts/*.png   (scripts/separate_lockup.py) — which part is the MARK:
        symbol / emblem / combination → the symbol crop      wordmark → the lettering itself (compact mark = monogram)
  <work>/mesh/lettering-mesh.json, monogram-mesh.json         traced lettering / monogram (flat-trace)
Writes
  SOURCE/JSON/mark.json        viewBox, silhouette rings (+ even-odd path), optical centre, levels{master,simplified}
  SOURCE/JSON/logo-parts.json  copy of the parts description + paths of every generated logo asset
  SOURCE/JS/mark-data.js       window.<GLOBAL>_MARK (file:// safe)
  LOGO/SVG/symbol*.svg         color · small · on-dark · small-on-dark · brand(-small) · tonal-dark/light · black/white/
                               solid-primary (one-colour) · detailed-black/white · outline(-white/-detailed) · silhouette
  LOGO/SVG/logo-original*.svg  the ORIGINAL lockup rebuilt in vector (symbol + traced lettering at their original
                               positions): colour · black · white  (for symbol/emblem logos = the symbol)
  LOGO/SVG/compact*.svg        favicon/avatar mark: simplified symbol, or the traced monogram for wordmarks
Interior holes left by a faceted mesh are closed by extending the neighbour with the longest shared edge (IDs stay stable).
"""
import argparse, json, os, re, sys, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from colorlib import hex2rgb, rel_lum, mix, nearest, ramp, contrast, adjust_for_contrast

def load(p): return json.load(open(p))
def num(s): return [float(v) for v in re.findall(r'-?\d+\.?\d*(?:e-?\d+)?', s)]

def mask_of(path):
    import numpy as np
    from PIL import Image
    from scipy import ndimage
    art = np.array(Image.open(path).convert('RGBA'))
    am = art[:, :, 3] > 110 if (art[:, :, 3] < 250).mean() > 0.01 else np.abs(art[:, :, :3].astype(int) - np.median(art[:5, :5, :3].reshape(-1, 3), 0)).sum(2) > 30
    return ndimage.binary_opening(am, iterations=1)

def rings_of(mask, eps):
    import cv2
    cs, hier = cv2.findContours(mask.astype('uint8'), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    tot = mask.sum(); out = []
    for c in cs:
        if abs(cv2.contourArea(c)) < tot * 0.0004: continue
        out.append(cv2.approxPolyDP(c, eps, True)[:, 0, :].astype(float).tolist())
    return out

def traced_silhouette(mask, mode, dx, dy):
    """Smooth even-odd silhouette path traced from the alpha mask (vtracer, binary). Returns d or None."""
    try:
        import vtracer, tempfile, numpy as np
        from PIL import Image
    except ImportError:
        return None
    png = tempfile.mktemp(suffix='.png'); svg = tempfile.mktemp(suffix='.svg')
    Image.fromarray(np.where(mask, 0, 255).astype('uint8')).save(png)
    vtracer.convert_image_to_svg_py(png, svg, colormode='binary', mode=mode, filter_speckle=4, corner_threshold=60,
                                    length_threshold=4.0, splice_threshold=45, path_precision=2)
    out = []
    for m in re.finditer(r'<path d="([^"]+)"([^>]*)>', open(svg).read()):
        tr = re.search(r'translate\(([-\d.]+),([-\d.]+)\)', m.group(2))
        tx, ty = (float(tr.group(1)) if tr else 0) - dx, (float(tr.group(2)) if tr else 0) - dy; toks = re.findall(r'[A-Za-z]|-?\d*\.?\d+(?:e-?\d+)?', m.group(1)); k = 0; o = []
        for t in toks:
            if t.isalpha(): o.append(t); continue
            o.append(f'{float(t) + (tx if k % 2 == 0 else ty):.2f}'.rstrip('0').rstrip('.')); k += 1
        out.append(' '.join(o))
    os.remove(png); os.remove(svg)
    return ' '.join(out) or None

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--config', required=True); ap.add_argument('--repo', required=True); ap.add_argument('--work')
    a = ap.parse_args()
    cfgdir = os.path.dirname(os.path.abspath(a.config)); C = load(a.config)
    R = lambda *p: os.path.join(a.repo, *p); work = a.work or R('SOURCE', 'SCRIPTS', '_work')
    rel = lambda p: p if os.path.isabs(p) else os.path.join(cfgdir, p)
    brand, logo = C['brand'], C['logo']; GLOBAL = brand.get('global', 'BX'); N = brand['name']
    pal = {p['key']: p['hex'] for p in C['palette']}; roles = C.get('roles', {})
    prim = pal[roles['primary']]; found = pal[roles['foundation']]; paper = pal[roles['paper']]
    pramp = C.get('ramps', {}).get(roles.get('primary_ramp', 'primary')) or ramp(prim)
    BRAND_RAMP = [pramp[s] for s in ['950', '900', '800', '700', '600', '500', '400', '300', '200'] if s in pramp]
    lift = logo.get('on_dark_lift', mix(found, '#FFFFFF', 0.4))
    parts_p = os.path.join(work, 'parts', 'logo-parts.json')
    parts = load(parts_p) if os.path.exists(parts_p) else {'logo_type': logo.get('type', 'symbol'), 'crops': {}}
    T = parts['logo_type']
    mark_part = 'lettering' if T == 'wordmark' else 'symbol'
    art_path = os.path.join(work, 'parts', parts['crops'][mark_part]['file']) if mark_part in parts['crops'] else rel(logo['artwork'])
    mark_offset = parts['crops'].get(mark_part, {}).get('offset', [0, 0])
    lv = logo['levels']; master = load(rel(lv['master'])); simple = load(rel(lv.get('simplified', lv['master'])))
    kind = master.get('kind', 'polygons')

    import numpy as np, cv2
    am = mask_of(art_path)
    sil_rings = rings_of(am, 1.5); sil_rings_s = rings_of(am, 6)
    M = cv2.moments(am.astype(np.uint8), binaryImage=True); cen = [M['m10'] / M['m00'], M['m01'] / M['m00']]

    def pts_of(f):
        if 'points' in f: return f['points']
        nums = num(f['d']); return [[x + f.get('tx', 0), y + f.get('ty', 0)] for x, y in zip(nums[0::2], nums[1::2])]
    allp = [p for f in master['facets'] for p in pts_of(f)] + [p for r in sil_rings for p in r]
    minx = min(p[0] for p in allp); miny = min(p[1] for p in allp)
    W = round(max(p[0] for p in allp) - minx, 1); H = round(max(p[1] for p in allp) - miny, 1)
    def norm(pts): return [[round(x - minx, 1), round(y - miny, 1)] for x, y in pts]
    def ring_d(rings): return ' '.join('M' + ' L'.join(f'{x},{y}' for x, y in r) + 'Z' for r in rings)

    def patch_holes(facets):
        if kind != 'polygons': return facets
        try:
            from shapely.geometry import Polygon
            from shapely.ops import unary_union
        except ImportError:
            print('shapely missing: hole patching skipped'); return facets
        polys = [Polygon(f['points']).buffer(0) for f in facets]
        U = unary_union(polys); geoms = [U] if U.geom_type == 'Polygon' else list(U.geoms)
        for g in geoms:
            for ring in g.interiors:
                hp = Polygon(ring)
                if hp.area < 2: continue
                nb = [i for i, pg in enumerate(polys) if pg.boundary.intersection(hp.boundary).length > 1.0]
                if not nb: continue
                i = max(nb, key=lambda k: polys[k].boundary.intersection(hp.boundary).length)
                mg = unary_union([polys[i], hp.buffer(0.01)]).buffer(-0.01).simplify(0.05)
                if mg.geom_type != 'Polygon': continue
                facets[i]['points'] = [[round(x, 1), round(y, 1)] for x, y in list(mg.exterior.coords)[:-1]]
                facets[i]['patched_gap'] = True; polys[i] = Polygon(facets[i]['points']).buffer(0)
                print(f'closed a {hp.area:.0f}px² gap by extending {facets[i]["id"]}')
        return facets

    def level(src):
        out = []
        for i, f in enumerate(src['facets']):
            e = {'id': f'F{i + 1:03d}', 'color': f['color'], 'tone': nearest(f['color'], pal), 'luminance': round(rel_lum(f['color']), 4), 'area': f.get('area', 0)}
            if 'points' in f: e['points'] = norm(f['points'])
            else: e['d'] = f['d']; e['tx'] = round(f.get('tx', 0) - minx, 2); e['ty'] = round(f.get('ty', 0) - miny, 2)
            pp = e.get('points') or norm(pts_of(f))
            e['centroid'] = [round(sum(p[0] for p in pp) / len(pp), 1), round(sum(p[1] for p in pp) / len(pp), 1)]
            out.append(e)
        return patch_holes(out)

    rings_n = [norm(r) for r in sil_rings]; rings_ns = [norm(r) for r in sil_rings_s]
    geo = logo.get('geometry', 'mixed')
    smooth_d = traced_silhouette(am, 'polygon' if geo in ('angular', 'orthogonal') else 'spline', minx, miny)
    outer = max(rings_n, key=lambda r: cv2.contourArea(np.array(r, np.float32)))
    data = {'name': f'{N} — vector mark', 'version': '2.0.0', 'kind': kind, 'logo_type': T, 'mark_part': mark_part,
            'note': 'Faithful vectorisation of the original artwork. Regenerate with the forge scripts; never edit by hand.',
            'viewBox': [0, 0, W, H], 'origin_offset_in_artwork': [round(minx + mark_offset[0], 1), round(miny + mark_offset[1], 1)],
            'optical_center': [round((cen[0] - minx) / W, 4), round((cen[1] - miny) / H, 4)],
            'silhouette': outer, 'silhouette_rings': rings_n, 'silhouette_d': smooth_d or ring_d(rings_n), 'silhouette_simple_d': ring_d(rings_ns),
            'levels': {'master': level(master), 'simplified': level(simple)}}
    for d in (('SOURCE', 'JSON'), ('SOURCE', 'JS'), ('LOGO', 'SVG')): os.makedirs(R(*d), exist_ok=True)

    seam = kind == 'polygons'
    def shape(f, attrs):
        if 'points' in f: return f'<polygon points="{" ".join(f"{x},{y}" for x, y in f["points"])}"{attrs}/>'
        tr = f' transform="translate({f["tx"]},{f["ty"]})"' if (f.get('tx') or f.get('ty')) else ''
        return f'<path fill-rule="evenodd" d="{f["d"]}"{tr}{attrs}/>'
    def head(title, vb=None):
        return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb or f"0 0 {W} {H}"}" role="img" aria-labelledby="t"><title id="t">{title}</title>'
    def body(lvl, fn=lambda f: f['color']):
        return ''.join(shape(f, f' fill="{fn(f)}"' + (f' stroke="{fn(f)}" stroke-width="0.75" stroke-linejoin="round"' if seam else '') + f' data-part="{f["id"]}"') for f in data['levels'][lvl])
    def colour_svg(lvl, title, fn=lambda f: f['color']): return head(title) + f'<g id="mark">{body(lvl, fn)}</g></svg>'
    def masked(lvl, fill, title, line):
        fs = data['levels'][lvl]; edges = ''.join(shape(f, '') for f in fs)
        return (head(title) + f'<defs><mask id="lines" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">'
                f'<g fill="#fff" stroke="#000" stroke-width="{line}" stroke-linejoin="round">{edges}</g></mask></defs>'
                f'<g mask="url(#lines)" fill="{fill}"><path fill-rule="evenodd" d="{data["silhouette_d"]}"/>{edges}</g></svg>')
    def outline(lvl, stroke, title, w):
        fs = data['levels'][lvl]
        return (head(title, f'-6 -6 {W + 12} {H + 12}') + f'<g fill="none" stroke="{stroke}" stroke-width="{w}" stroke-linejoin="round">'
                + ''.join(shape(f, '') for f in fs) + f'<path d="{data["silhouette_d"]}" stroke-width="{w * 1.8}"/></g></svg>')
    def lifted(f):
        l = f['luminance']
        if l < 0.012: return mix(f['color'], lift, 0.55)
        if l < 0.03: return mix(f['color'], lift, 0.42)
        if l < 0.06: return mix(f['color'], lift, 0.28)
        return f['color']
    # if the graded lift leaves most of the mark invisible on the dark ground (e.g. dark one-colour logos), lighten for legibility
    def visible_share(lvl):   # share of the mark's area that still reads (≥ 3:1) on the dark ground after the graded lift
        fs = data['levels'][lvl]; tot = sum(max(1, f.get('area', 1)) for f in fs)
        return sum(max(1, f.get('area', 1)) for f in fs if contrast(lifted(f), found) >= 3) / tot
    od_target = 4.5 if T == 'wordmark' else 3.0
    rescue = {lvl: visible_share(lvl) < 0.3 for lvl in ('master', 'simplified')}
    def on_dark_for(lvl):
        def fn(f):
            c = lifted(f)
            if rescue[lvl] and contrast(c, found) < od_target: c = adjust_for_contrast(c, found, od_target, 'lighter')[0]
            return c
        return fn
    on_dark = on_dark_for('master')
    for lvl in ('master', 'simplified'):
        for f in data['levels'][lvl]: f['on_dark'] = on_dark_for(lvl)(f)
    def quantile(lvl):
        ls = sorted(f['luminance'] for f in data['levels'][lvl])
        return lambda f: BRAND_RAMP[min(len(BRAND_RAMP) - 1, int(ls.index(f['luminance']) / max(1, len(ls) - 1) * len(BRAND_RAMP)))]
    def tonal(dark, light): return lambda f: mix(dark, light, min(1, (f['luminance'] ** 0.5) / 0.85) * 0.9)
    Mv, Sv = 'master', 'simplified'; lw_s = round(W / (95 if seam else 140), 2); lw_m = round(W / (240 if seam else 300), 2)
    V = {
        'symbol.svg': colour_svg(Mv, f'{N} symbol'),
        'symbol-small.svg': colour_svg(Sv, f'{N} symbol — small sizes'),
        'symbol-on-dark.svg': colour_svg(Mv, f'{N} symbol — dark backgrounds', on_dark),
        'symbol-small-on-dark.svg': colour_svg(Sv, f'{N} symbol — small, dark backgrounds', on_dark_for('simplified')),
        'symbol-brand.svg': colour_svg(Mv, f'{N} symbol — primary-colour monochrome', quantile(Mv)),
        'symbol-small-brand.svg': colour_svg(Sv, f'{N} symbol — primary-colour monochrome, small', quantile(Sv)),
        'symbol-tonal-dark.svg': colour_svg(Mv, f'{N} symbol — tonal dark', tonal(found, paper)),
        'symbol-tonal-light.svg': colour_svg(Mv, f'{N} symbol — tonal light', tonal(mix(found, '#FFFFFF', 0.25), '#FFFFFF')),
        'symbol-black.svg': masked(Sv, found, f'{N} symbol — one colour, dark', lw_s),
        'symbol-white.svg': masked(Sv, '#FFFFFF', f'{N} symbol — one colour, white', lw_s),
        'symbol-solid-primary.svg': masked(Sv, prim, f'{N} symbol — one colour, primary', lw_s),
        'symbol-detailed-black.svg': masked(Mv, found, f'{N} symbol — detailed one colour', lw_m),
        'symbol-detailed-white.svg': masked(Mv, '#FFFFFF', f'{N} symbol — detailed one colour, white', lw_m),
        'symbol-outline.svg': outline(Sv, found, f'{N} symbol — outline', round(W / 190, 2)),
        'symbol-outline-white.svg': outline(Sv, '#FFFFFF', f'{N} symbol — outline, white', round(W / 190, 2)),
        'symbol-outline-detailed.svg': outline(Mv, found, f'{N} symbol — detailed outline', round(W / 400, 2)),
        'symbol-silhouette.svg': head(f'{N} silhouette') + f'<path fill-rule="evenodd" d="{data["silhouette_d"]}" fill="{found}"/></svg>',
    }
    for k, v in V.items(): open(R('LOGO', 'SVG', k), 'w').write(v)
    json.dump(data, open(R('SOURCE', 'JSON', 'mark.json'), 'w'), separators=(',', ':'))

    # ---------- original lockup + compact mark
    assets = {'symbol': 'LOGO/SVG/symbol.svg'}
    def part_svg(meshfile, offset, colour=None):
        m = load(meshfile); out = []
        for f in m['facets']:
            tx = f.get('tx', 0) + offset[0]; ty = f.get('ty', 0) + offset[1]
            fill = colour(f['color']) if callable(colour) else (colour or f['color'])
            if 'points' in f: out.append(f'<polygon points="{" ".join(f"{x + offset[0]},{y + offset[1]}" for x, y in f["points"])}" fill="{fill}"/>')
            else: out.append(f'<path fill-rule="evenodd" d="{f["d"]}" transform="translate({round(tx, 2)},{round(ty, 2)})" fill="{fill}"/>')
        return ''.join(out)
    lt_mesh = os.path.join(work, 'mesh', 'lettering-mesh.json'); mono_mesh = os.path.join(work, 'mesh', 'monogram-mesh.json')
    if T == 'combination' and os.path.exists(lt_mesh):
        aw, ah = parts['artwork_size']; bb = parts['artwork_bbox']; pad = 2
        vb = f'{bb[0] - pad} {bb[1] - pad} {bb[2] - bb[0] + 1 + 2 * pad} {bb[3] - bb[1] + 1 + 2 * pad}'
        so = data['origin_offset_in_artwork']; lo = parts['crops']['lettering']['offset']
        def lockup(sym_fn, let_colour, title):
            sym = ''.join(shape(f, f' fill="{sym_fn(f)}"' + (f' stroke="{sym_fn(f)}" stroke-width="0.75"' if seam else '')) for f in data['levels'][Mv])
            return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" role="img" aria-labelledby="t"><title id="t">{title}</title>'
                    f'<g id="symbol" transform="translate({so[0]},{so[1]})">{sym}</g><g id="lettering">{part_svg(lt_mesh, lo, let_colour)}</g></svg>')
        open(R('LOGO', 'SVG', 'logo-original.svg'), 'w').write(lockup(lambda f: f['color'], None, f'{N} logo'))
        def lockup_mono(fill, title):   # one-colour: the symbol keeps its internal separations as knock-out lines (like symbol-black)
            fs = data['levels'][Sv if len(data['levels'][Mv]) > 40 else Mv]; edges = ''.join(shape(f, '') for f in fs)
            sym = (f'<defs><mask id="ko" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}"><g fill="#fff" stroke="#000" stroke-width="{lw_s}" stroke-linejoin="round">{edges}</g></mask></defs>'
                   f'<g mask="url(#ko)" fill="{fill}"><path fill-rule="evenodd" d="{data["silhouette_d"]}"/>{edges}</g>')
            return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" role="img" aria-labelledby="t"><title id="t">{title}</title>'
                    f'<g id="symbol" transform="translate({so[0]},{so[1]})">{sym}</g><g id="lettering">{part_svg(lt_mesh, lo, fill)}</g></svg>')
        open(R('LOGO', 'SVG', 'logo-original-black.svg'), 'w').write(lockup_mono(found, f'{N} logo — one colour'))
        open(R('LOGO', 'SVG', 'logo-original-white.svg'), 'w').write(lockup_mono('#FFFFFF', f'{N} logo — white'))
        open(R('LOGO', 'SVG', 'logo-original-solid-black.svg'), 'w').write(lockup(lambda f: found, found, f'{N} logo — solid one colour (no separations)'))
        open(R('LOGO', 'SVG', 'logo-original-on-dark.svg'), 'w').write(lockup(on_dark, lambda c: paper if rel_lum(c) < 0.18 else c, f'{N} logo — dark backgrounds'))
        lb = parts['crops']['lettering']['box']
        os.makedirs(R('SOURCE', 'SVG'), exist_ok=True)
        open(R('SOURCE', 'SVG', 'lettering-original.svg'), 'w').write(
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{lb[0] - 1} {lb[1] - 1} {lb[2] - lb[0] + 3} {lb[3] - lb[1] + 3}" role="img" aria-label="{N}"><title>{N}</title>{part_svg(lt_mesh, lo)}</svg>')
        assets.update({'logo_original': 'LOGO/SVG/logo-original.svg', 'lettering': 'SOURCE/SVG/lettering-original.svg'})
    else:
        for k, src in (('logo-original.svg', 'symbol.svg'), ('logo-original-black.svg', 'symbol-detailed-black.svg'), ('logo-original-white.svg', 'symbol-detailed-white.svg'), ('logo-original-on-dark.svg', 'symbol-on-dark.svg')):
            shutil.copy(R('LOGO', 'SVG', src), R('LOGO', 'SVG', k))
        assets['logo_original'] = 'LOGO/SVG/logo-original.svg'
        if T == 'wordmark': assets['lettering'] = 'LOGO/SVG/symbol.svg'
    if T == 'wordmark' and os.path.exists(mono_mesh):
        mm = load(mono_mesh); ps = [p for f in mm['facets'] for p in pts_of(f)]
        x0, y0 = min(p[0] for p in ps), min(p[1] for p in ps); x1, y1 = max(p[0] for p in ps), max(p[1] for p in ps)
        side = max(x1 - x0, y1 - y0) * 1.12; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        vb = f'{round(cx - side / 2, 1)} {round(cy - side / 2, 1)} {round(side, 1)} {round(side, 1)}'
        od = lambda c: adjust_for_contrast(c, found, 4.5, 'lighter')[0] if contrast(c, found) < 4.5 else c
        for suffix, col in (('', None), ('-black', found), ('-white', '#FFFFFF'), ('-on-dark', od)):
            open(R('LOGO', 'SVG', f'compact{suffix}.svg'), 'w').write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" role="img" aria-label="{N}"><title>{N} — compact mark</title>{part_svg(mono_mesh, [0, 0], col)}</svg>')
        assets['compact'] = 'LOGO/SVG/compact.svg'
        compact_js = {'viewBox': [float(v) for v in vb.split()], 'parts': [{k: v for k, v in {'d': f.get('d'), 'p': f.get('points'), 'tx': f.get('tx', 0), 'ty': f.get('ty', 0), 'c': f['color'], 'od': od(f['color'])}.items() if v is not None} for f in mm['facets']]}
    else:
        for suffix, src in (('', 'symbol-small.svg'), ('-black', 'symbol-black.svg'), ('-white', 'symbol-white.svg'), ('-on-dark', 'symbol-small-on-dark.svg')):
            shutil.copy(R('LOGO', 'SVG', src), R('LOGO', 'SVG', f'compact{suffix}.svg'))
        assets['compact'] = 'LOGO/SVG/compact.svg'; compact_js = None
    parts_out = dict(parts); parts_out['assets'] = assets; parts_out['mark_part'] = mark_part
    json.dump(parts_out, open(R('SOURCE', 'JSON', 'logo-parts.json'), 'w'), indent=2)

    js = {'kind': kind, 'logoType': T, 'viewBox': data['viewBox'], 'silhouette': data['silhouette'], 'silhouetteD': data['silhouette_d'],
          'opticalCenter': data['optical_center'], 'compact': compact_js, 'ramp': BRAND_RAMP, 'lift': lift, 'foundation': found, 'paper': paper, 'primary': prim, 'seam': seam}
    for k in ('master', 'simplified'):
        js[k] = [{key: v for key, v in {'id': f['id'], 'p': f.get('points'), 'd': f.get('d'), 'tx': f.get('tx'), 'ty': f.get('ty'),
                  'c': f['color'], 'od': f['on_dark'], 'l': f['luminance'], 't': f['tone']}.items() if v is not None} for f in data['levels'][k]]
    open(R('SOURCE', 'JS', 'mark-data.js'), 'w').write(
        f'/* {N} mark data — generated by build_mark.py. Do not edit. */\nwindow.{GLOBAL}_MARK=' + json.dumps(js, separators=(',', ':')) + ';\n')
    print(f'{T}: mark = {mark_part} · viewBox {W}×{H} · master {len(data["levels"]["master"])} · simplified {len(data["levels"]["simplified"])} · {len(V)} symbol SVGs + logo-original + compact')

if __name__ == '__main__':
    main()
