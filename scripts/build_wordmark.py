#!/usr/bin/env python3
"""
build_wordmark.py — typeset brand lettering as outlined SVG paths (no font needed at use time) + wordmark-data.js.

usage: python3 scripts/build_wordmark.py --config brand.config.json --repo ../ACME-BRAND

brand.config.json → wordmark:
  { "mode": "traced" | "typeset",
        traced  = the logo already contains lettering (combination / wordmark logos). It was TRACED from the artwork by the
                  foundation step (SOURCE/SVG/lettering-original.svg). Here we only typeset descriptors, a local-language
                  name and a typeset monogram (social avatars) — the brand name is never re-typeset.
        typeset = symbol / emblem logos: the name is set in the display font (stacked, one-line, each line alone).
    "font": {"slug": "archivo", "subset": "latin", "axes": {"wght": 800}},   # a family fetched into SOURCE/FONTS
    "tracking_em": 0.02, "lines": ["NORTHWIND", "STUDIO"], "line_advance_caps": 1.2, "one_line": "NORTHWIND STUDIO", "monogram": "NS",
    "descriptors": [ {"name": "descriptor", "text": "DESIGN CONSULTANCY", "font": {"slug": "dm-mono", "subset": "latin", "axes": {"wght": 500}}, "tracking_em": 0.12} ] }
  ("font" may also be a plain file name inside SOURCE/FONTS.)
Writes SOURCE/SVG/{wordmark-stacked, wordmark-line, wordmark-line-<i>, monogram(-typeset), <descriptor>}.svg (one <path> per glyph),
SOURCE/JSON/wordmark-paths.json (viewBoxes, cap heights), SOURCE/JSON/wordmark.json and SOURCE/JS/wordmark-data.js (window.<G>_WORDMARK: every lettering asset — traced
and typeset — as {vb, body} so pages can inline them from file://). Shaping: HarfBuzz with kerning.
"""
import argparse, glob, html, io, json, os, re
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.transformPen import TransformPen

def find_font(FD, spec):
    if isinstance(spec, str): return os.path.join(FD, spec), {}
    slug, sub, axes = spec['slug'], spec.get('subset', 'latin'), spec.get('axes', {})
    fs = [f for f in glob.glob(os.path.join(FD, f'{slug}-{sub}-*-normal.woff2')) if not os.path.basename(f)[len(slug) + len(sub) + 2:].startswith('ext-')]
    if not fs: fs = glob.glob(os.path.join(FD, f'{slug}-*-normal.woff2'))
    if not fs: raise SystemExit(f'font "{slug}" ({sub}) not found in {FD} — run fetch_fonts.py first')
    w = axes.get('wght', 400)
    for key in ('wght', 'standard', 'full', str(w)):
        hit = [f for f in fs if f'-{key}-normal' in f]
        if hit: return hit[0], axes
    statics = sorted(fs, key=lambda f: abs(int((re.findall(r'-(\d{3})-normal', f) or ['400'])[0]) - w))
    return statics[0], axes

def static(path, axes):
    f = TTFont(path); f.flavor = None
    if 'fvar' in f:
        f = instancer.instantiateVariableFont(f, {ax.axisTag: axes.get(ax.axisTag, ax.defaultValue) for ax in f['fvar'].axes})
    b = io.BytesIO(); f.save(b); return TTFont(io.BytesIO(b.getvalue())), b.getvalue()

def outline(text, path, axes, tracking_em=0.0):
    ft, data = static(path, axes)
    upem = ft['head'].unitsPerEm; gs = ft.getGlyphSet(); order = ft.getGlyphOrder()
    font = hb.Font(hb.Face(hb.Blob(data)))
    buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties()
    hb.shape(font, buf, {'kern': True, 'liga': False})
    bp = BoundsPen(gs); x = 0; n = len(buf.glyph_infos); glyphs = []
    for i, (info, pos) in enumerate(zip(buf.glyph_infos, buf.glyph_positions)):
        g = order[info.codepoint]; t = (1, 0, 0, -1, x + pos.x_offset, -pos.y_offset); pen = SVGPathPen(gs)
        gs[g].draw(TransformPen(pen, t)); gs[g].draw(TransformPen(bp, t))
        if pen.getCommands(): glyphs.append(pen.getCommands())
        x += pos.x_advance + (tracking_em * upem if i < n - 1 else 0)
    cap = getattr(ft['OS/2'], 'sCapHeight', 0) or int(upem * 0.7)
    return {'d': ' '.join(glyphs), 'glyphs': glyphs, 'advance': x, 'bounds': bp.bounds or (0, 0, 1, 1), 'upem': upem, 'cap': cap}

def r(v): return round(v, 2)

def write(path, parts, title, fill):
    xs, ys, paths = [], [], []
    for o, dx, dy in parts:
        x0, y0, x1, y1 = o['bounds']; xs += [x0 + dx, x1 + dx]; ys += [y0 + dy, y1 + dy]
        paths.append(f'<g transform="translate({r(dx)} {r(dy)})">' + ''.join(f'<path d="{gd}"/>' for gd in o.get('glyphs', [o['d']])) + '</g>')   # one path per glyph
    X0, Y0 = min(xs), min(ys); w = max(xs) - X0; h = max(ys) - Y0
    body = ''.join(paths); t = html.escape(title, quote=True)
    open(path, 'w').write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{r(X0)} {r(Y0)} {r(w)} {r(h)}" role="img" aria-label="{t}">'
                          f'<title>{t}</title><g fill="{fill}">{body}</g></svg>')
    return [r(X0), r(Y0), r(w), r(h)], body

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--config', required=True); ap.add_argument('--repo', required=True)
    a = ap.parse_args(); C = json.load(open(a.config)); Wm = C.get('wordmark', {})
    FD = os.path.join(a.repo, 'SOURCE', 'FONTS'); SD = os.path.join(a.repo, 'SOURCE', 'SVG'); os.makedirs(SD, exist_ok=True)
    pal = {p['key']: p['hex'] for p in C['palette']}; ink = pal[C['roles']['foundation']]
    name = C['brand']['name']; G = C['brand'].get('global', 'BX'); mode = Wm.get('mode', 'typeset'); tr = Wm.get('tracking_em', 0)
    meta = {'mode': mode}; data = {}
    if Wm.get('font'):
        fp, axes = find_font(FD, Wm['font']); meta.update({'font': os.path.basename(fp), 'axes': axes, 'tracking_em': tr})
        if mode == 'typeset':
            lines = [outline(t, fp, axes, tr) for t in Wm.get('lines', [name])]
            cap = lines[0]['cap']; lead = cap * Wm.get('line_advance_caps', 1.2); meta.update({'cap_height_units': cap, 'upem': lines[0]['upem'], 'line_advance_caps': Wm.get('line_advance_caps', 1.2)})
            meta['stacked'], data['stacked'] = write(os.path.join(SD, 'wordmark-stacked.svg'), [(o, 0, i * lead) for i, o in enumerate(lines)], name, ink)
            for i, o in enumerate(lines):
                meta[f'line_{i + 1}'], data[f'line_{i + 1}'] = write(os.path.join(SD, f'wordmark-line-{i + 1}.svg'), [(o, 0, 0)], Wm['lines'][i], ink)
            meta['line'], data['line'] = write(os.path.join(SD, 'wordmark-line.svg'), [(outline(Wm.get('one_line', name), fp, axes, tr), 0, 0)], name, ink)
        if Wm.get('monogram'):
            fn = 'monogram.svg' if mode == 'typeset' else 'monogram-typeset.svg'
            meta['monogram'], data['monogram'] = write(os.path.join(SD, fn), [(outline(Wm['monogram'], fp, axes, 0), 0, 0)], Wm['monogram'], ink)
    for d in Wm.get('descriptors', []):
        dp, dax = find_font(FD, d['font'])
        o = outline(d['text'], dp, dax, d.get('tracking_em', 0.1))
        meta[d['name']], data[d['name']] = write(os.path.join(SD, d['name'] + '.svg'), [(o, 0, 0)], d.get('label', d['text']), ink)
        meta[d['name'] + '_cap'] = {'cap_height_units': o['cap'], 'upem': o['upem']}
    # traced lettering from the artwork (combination / wordmark logos) joins the data file unchanged
    for key, fn in (('lettering', 'lettering-original.svg'),):
        p = os.path.join(SD, fn)
        if os.path.exists(p):
            s = open(p).read(); vb = re.search(r'viewBox="([^"]+)"', s).group(1)
            inner = re.sub(r'^.*?<title>.*?</title>', '', s, flags=re.S).rsplit('</svg>', 1)[0]
            data[key] = inner; meta[key] = [float(v) for v in vb.split()]
    os.makedirs(os.path.join(a.repo, 'SOURCE', 'JSON'), exist_ok=True); os.makedirs(os.path.join(a.repo, 'SOURCE', 'JS'), exist_ok=True)
    json.dump(meta, open(os.path.join(a.repo, 'SOURCE', 'JSON', 'wordmark-paths.json'), 'w'), indent=1)
    js = {k: {'vb': ' '.join(str(v) for v in meta[k]), 'body': b} for k, b in data.items()}
    json.dump({'mode': mode, 'items': js}, open(os.path.join(a.repo, 'SOURCE', 'JSON', 'wordmark.json'), 'w'), ensure_ascii=False)
    open(os.path.join(a.repo, 'SOURCE', 'JS', 'wordmark-data.js'), 'w').write(
        f'/* {name} lettering — generated by build_wordmark.py. {{vb, body}}; typeset bodies inherit fill (use currentColor). */\n'
        f'window.{G}_WORDMARK=' + json.dumps({'mode': mode, 'items': js}, ensure_ascii=False, separators=(',', ':')) + ';\n')
    print(f'wordmark ({mode}) written:', ', '.join(k for k in meta if isinstance(meta[k], list)))

if __name__ == '__main__':
    main()
