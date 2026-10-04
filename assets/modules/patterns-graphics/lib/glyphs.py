#!/usr/bin/env python3
"""glyphs.py — outline brand-font glyphs for standalone SVGs (no font dependency in exported graphics).
usage: python3 glyphs.py request.json out.json
request: {"fonts": [{"key": "display", "files": ["…woff2", …], "wght": 700, "chars": "0123…"}]}
out:     {"display": {"upm": 1000, "asc": …, "desc": …, "cap": …, "glyphs": {"A": {"d": "M…", "w": 612.0}}}}
Coordinates are y-down, 1000 units per em, origin on the baseline. Files are searched in order per character
(latin, latin-ext, cyrillic … subsets). Variable fonts are read at the requested weight."""
import json
import sys

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont


def load(files):
    out = []
    for fp in files:
        try:
            out.append(TTFont(fp))
        except Exception:  # missing / unreadable subset → skip
            pass
    return out


def glyphset(f, wght):
    if 'fvar' in f:
        loc = {}
        for a in f['fvar'].axes:
            if a.axisTag == 'wght':
                loc['wght'] = max(a.minValue, min(a.maxValue, float(wght)))
            elif a.axisTag == 'wdth':
                loc['wdth'] = max(a.minValue, min(a.maxValue, 100.0))
            elif a.axisTag == 'opsz':
                loc['opsz'] = a.maxValue
        try:
            return f.getGlyphSet(location=loc)
        except TypeError:
            return f.getGlyphSet()
    return f.getGlyphSet()


def main():
    req = json.load(open(sys.argv[1], encoding='utf-8'))
    out = {}
    for spec in req.get('fonts', []):
        fonts = load(spec.get('files', []))
        res = {'upm': 1000, 'glyphs': {}, 'asc': 800, 'desc': 200, 'cap': 700}
        if not fonts:
            out[spec['key']] = res
            continue
        sets = [glyphset(f, spec.get('wght', 400)) for f in fonts]
        cmaps = [f.getBestCmap() or {} for f in fonts]
        f0 = fonts[0]
        s0 = 1000.0 / f0['head'].unitsPerEm
        if 'OS/2' in f0:
            os2 = f0['OS/2']
            res['asc'] = round(os2.sTypoAscender * s0, 1)
            res['desc'] = round(-os2.sTypoDescender * s0, 1)
            res['cap'] = round((getattr(os2, 'sCapHeight', 0) or 700 / s0) * s0, 1)
            res['xh'] = round((getattr(os2, 'sxHeight', 0) or 500 / s0) * s0, 1)
        for ch in sorted(set(spec.get('chars', '')) | {' ', '?'}):
            for f, gs, cm in zip(fonts, sets, cmaps):
                if ord(ch) not in cm:
                    continue
                g = cm[ord(ch)]
                s = 1000.0 / f['head'].unitsPerEm
                pen = SVGPathPen(gs, ntos=lambda v: ('%.1f' % v).rstrip('0').rstrip('.'))
                gs[g].draw(TransformPen(pen, (s, 0, 0, -s, 0, 0)))
                res['glyphs'][ch] = {'d': pen.getCommands(), 'w': round(gs[g].width * s, 1)}
                break
        out[spec['key']] = res
    json.dump(out, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False)


if __name__ == '__main__':
    main()
