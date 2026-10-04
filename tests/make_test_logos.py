#!/usr/bin/env python3
"""
make_test_logos.py — synthesise a diverse set of FICTIONAL test logos (one per logo type / geometry / complexity)
so every script and module can be regression-tested without any real client's artwork.

usage: python3 tests/make_test_logos.py [--out tests/logos] [--fonts <fontsource node_modules dir>]
The PNGs are committed in tests/logos/, so this only needs to run when you change the set.
Lettering uses open-source fonts from a Fontsource npm cache when available (see scripts/fetch_fonts.py),
otherwise DejaVu. All names are invented.

  northwind.png  combination · horizontal · angular · flat        (professional services)
  orbit.png      combination · stacked    · round   · flat        (health / wellness)
  luma.png       wordmark    · serif lettering      · flat        (hospitality)
  kcc.png        emblem      · text inside a badge  · flat        (education non-profit)
  peakforge.png  symbol      · low-poly             · faceted     (industrial / energy)
  leaf-line.png  symbol      · monoline             · line        (analysis-only)
  glow.png       symbol      · soft blob            · gradient    (analysis-only)
"""
import argparse, glob, io, math, os, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))

def font_file(cache, slug, wght=400, subset='latin'):
    """Return a TTF path for a Fontsource family (variable instanced at wght), or None."""
    if not cache: return None
    from fontTools.ttLib import TTFont
    for kind in ('@fontsource-variable', '@fontsource'):
        files = [f for f in sorted(glob.glob(os.path.join(cache, kind, slug, 'files', f'{slug}-{subset}-*normal.woff2')))
                 if not os.path.basename(f)[len(slug) + len(subset) + 2:].startswith('ext-')]
        if not files: continue
        pick = next((f for f in files if f'-{wght}-' in f), None) or next((f for f in files if 'wght' in f or 'standard' in f or 'full' in f), files[0])
        f = TTFont(pick); f.flavor = None
        if 'fvar' in f:
            from fontTools.varLib import instancer
            f = instancer.instantiateVariableFont(f, {ax.axisTag: (wght if ax.axisTag == 'wght' else ax.defaultValue) for ax in f['fvar'].axes})
        out = os.path.join('/tmp', f'tl-{slug}-{wght}.ttf'); f.save(out); return out
    return None

def F(cache, slug, wght, size):
    p = font_file(cache, slug, wght)
    try: return ImageFont.truetype(p or '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', size)
    except Exception: return ImageFont.load_default()

def text(d, xy, s, font, fill, tracking=0, anchor='ls'):
    x, y = xy
    if not tracking: d.text((x, y), s, font=font, fill=fill, anchor=anchor); return
    for ch in s:
        d.text((x, y), ch, font=font, fill=fill, anchor=anchor); x += font.getlength(ch) + tracking

def northwind(cache):
    im = Image.new('RGBA', (1500, 520), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    navy, teal, orange = (27, 42, 65, 255), (46, 196, 182, 255), (255, 159, 28, 255)
    # compass kite: two halves + a small orange tip
    d.polygon([(200, 60), (330, 300), (200, 250)], fill=teal)
    d.polygon([(200, 60), (200, 250), (70, 300)], fill=navy)
    d.polygon([(70, 300), (200, 250), (200, 460)], fill=navy)
    d.polygon([(200, 250), (330, 300), (200, 460)], fill=teal)
    d.polygon([(200, 60), (232, 120), (168, 120)], fill=orange)
    text(d, (420, 290), 'NORTHWIND', F(cache, 'archivo', 800, 150), navy, tracking=4)
    text(d, (426, 400), 'STUDIO', F(cache, 'archivo', 500, 64), navy, tracking=30)
    return im

def orbit(cache):
    im = Image.new('RGBA', (1000, 1000), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    green, deep = (43, 182, 115, 255), (14, 124, 134, 255)
    d.ellipse([300, 120, 700, 520], outline=green, width=46)
    d.ellipse([430, 250, 570, 390], fill=deep)
    d.ellipse([620, 130, 720, 230], fill=deep)
    f = F(cache, 'outfit', 700, 120)
    w = f.getlength('ORBIT'); text(d, (500 - w / 2, 720), 'ORBIT', f, deep)
    f2 = F(cache, 'outfit', 400, 70); w2 = f2.getlength('HEALTH') + 5 * 18
    text(d, (500 - w2 / 2, 830), 'HEALTH', f2, green, tracking=18)
    return im

def luma(cache):
    im = Image.new('RGBA', (1500, 420), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    plum = (74, 37, 69, 255)
    f = F(cache, 'dm-serif-display', 400, 190)
    text(d, (60, 280), 'Maison Luma', f, plum, tracking=2)
    return im

def kcc(cache):
    im = Image.new('RGBA', (1000, 1000), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    orange, yellow, white, ink = (255, 107, 53, 255), (255, 210, 63, 255), (255, 255, 255, 255), (30, 30, 60, 255)
    d.ellipse([60, 60, 940, 940], fill=orange)
    d.ellipse([100, 100, 900, 900], outline=ink, width=10)
    f0 = F(cache, 'rubik', 800, 150); w = f0.getlength('</>'); text(d, (500 - w / 2, 360), '</>', f0, yellow)
    for i, (s, size) in enumerate((('KIDS', 140), ('CODE CLUB', 104))):
        f = F(cache, 'rubik', 800, size); w = f.getlength(s); text(d, (500 - w / 2, 540 + i * 150), s, f, white)
    return im

def peakforge(_cache):
    from scipy.spatial import Delaunay
    W, H = 1000, 860; rng = np.random.default_rng(7)
    sil = [(80, 780), (330, 250), (430, 380), (560, 90), (920, 780)]
    from matplotlib.path import Path
    P = Path(sil); pts = [p for p in sil] + [((sil[i][0] + sil[(i + 1) % 5][0]) / 2, (sil[i][1] + sil[(i + 1) % 5][1]) / 2) for i in range(5)]
    while len(pts) < 70:
        q = (rng.uniform(80, 920), rng.uniform(90, 780))
        if P.contains_point(q, radius=-25): pts.append(q)
    pts = np.array(pts); tri = Delaunay(pts)
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    dark, slate, amber, ember, light = np.array([22, 30, 42]), np.array([58, 76, 98]), np.array([242, 140, 40]), np.array([214, 69, 38]), np.array([255, 214, 150])
    for s in tri.simplices:
        c = pts[s].mean(0)
        if not P.contains_point(c): continue
        t = (c[0] - 80) / 840; v = 1 - (c[1] - 90) / 690
        base = dark * (1 - t) * 1.0 + slate * 0 if t < 0.45 else ember * (1 - (t - 0.45) / 0.55) + amber * ((t - 0.45) / 0.55)
        if t < 0.45: base = dark + (slate - dark) * (t / 0.45) * rng.uniform(0.3, 1.2)
        if v > 0.8: base = base * 0.5 + light * 0.5
        col = np.clip(base * rng.uniform(0.72, 1.28), 0, 255).astype(int)
        d.polygon([tuple(p) for p in pts[s]], fill=tuple(col) + (255,))
    arr = np.array(im).astype(float); noise = rng.normal(0, 4, arr[:, :, :3].shape)   # painted texture
    arr[:, :, :3] = np.clip(arr[:, :, :3] + noise * (arr[:, :, 3:] > 0), 0, 255)
    return Image.fromarray(arr.astype(np.uint8)).filter(ImageFilter.SMOOTH)

def leaf_line(_cache):
    im = Image.new('RGBA', (900, 900), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = (38, 92, 66, 255)
    t = np.linspace(0, math.pi, 120)
    left = [(450 - 230 * math.sin(a), 120 + 600 * a / math.pi) for a in t]
    right = [(450 + 230 * math.sin(a), 120 + 600 * a / math.pi) for a in t]
    d.line(left, fill=c, width=22, joint='curve'); d.line(right, fill=c, width=22, joint='curve')
    d.line([(450, 160), (450, 820)], fill=c, width=22)
    for k in range(4):
        y = 300 + k * 110; d.line([(450, y + 60), (450 - 120 + k * 15, y)], fill=c, width=16); d.line([(450, y + 60), (450 + 120 - k * 15, y)], fill=c, width=16)
    for p in ((450, 120), (450, 820)): d.ellipse([p[0] - 11, p[1] - 11, p[0] + 11, p[1] + 11], fill=c)
    return im

def glow(_cache):
    W = 900; y, x = np.mgrid[0:W, 0:W].astype(float)
    r = np.hypot(x - 450, y - 450) / 380; ang = np.arctan2(y - 450, x - 450)
    rr = r * (1 + 0.12 * np.sin(3 * ang))
    a = np.clip((1 - rr) * 12, 0, 1)
    t = np.clip((x - 120) / 660, 0, 1)
    c1, c2, c3 = np.array([108, 92, 231]), np.array([0, 184, 217]), np.array([253, 121, 168])
    col = (c1 * (1 - t)[..., None] + c2 * t[..., None]) * (1 - 0.4 * (1 - rr.clip(0, 1)))[..., None] + c3 * (0.4 * (1 - rr.clip(0, 1)))[..., None]
    arr = np.dstack([np.clip(col, 0, 255), a * 255]).astype(np.uint8)
    return Image.fromarray(arr, 'RGBA')

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', default=os.path.join(HERE, 'logos')); ap.add_argument('--fonts', default=os.environ.get('FONTSOURCE_CACHE'))
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    for name, fn in (('northwind', northwind), ('orbit', orbit), ('luma', luma), ('kcc', kcc), ('peakforge', peakforge), ('leaf-line', leaf_line), ('glow', glow)):
        im = fn(a.fonts); bb = im.getbbox(); pad = 24
        im = im.crop((max(0, bb[0] - pad), max(0, bb[1] - pad), min(im.width, bb[2] + pad), min(im.height, bb[3] + pad)))
        im.save(os.path.join(a.out, f'{name}.png'), optimize=True); print(name, im.size)

if __name__ == '__main__':
    main()
