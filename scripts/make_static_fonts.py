#!/usr/bin/env python3
"""make_static_fonts.py — instance variable WOFF2 fonts into static TTFs for PDF rendering (avoids Type 3 fonts),
Office templates (.docx/.pptx) and desktop installation.
usage: python3 scripts/make_static_fonts.py <repo>/SOURCE/FONTS/<family>-latin-wght-normal.woff2 --axes wght=400 --name "Family Regular" --out <repo>/SOURCE/FONTS/static/
Needs: pip install fonttools brotli"""
import argparse, io, os
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
ap = argparse.ArgumentParser(); ap.add_argument('font'); ap.add_argument('--axes', required=True); ap.add_argument('--name'); ap.add_argument('--out', required=True)
a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
axes = {k: float(v) for k, v in (p.split('=') for p in a.axes.split(','))}
f = TTFont(a.font); f.flavor = None
f = instancer.instantiateVariableFont(f, axes, updateFontNames=True)
if a.name:
    for rec in f['name'].names:
        if rec.nameID in (1, 4, 16): rec.string = a.name
        if rec.nameID == 6: rec.string = a.name.replace(' ', '')
fn = os.path.join(a.out, (a.name or os.path.splitext(os.path.basename(a.font))[0]).replace(' ', '') + '-' + '-'.join(f'{k}{int(v)}' for k, v in axes.items()) + '.ttf')
f.save(fn); print('static font:', fn)
