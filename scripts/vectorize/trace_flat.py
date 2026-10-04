#!/usr/bin/env python3
"""
trace_flat.py — vectorise a FLAT logo (few solid colours) into non-overlapping coloured shapes.

Route for logos classified 'flat graphic' by analyze_logo.py. Uses vtracer (pip install vtracer)
on a colour-quantised copy of the logo, in cutout mode so shapes never overlap (needed for
one-colour versions with knocked-out separations).

Usage
  python3 scripts/vectorize/trace_flat.py logo.png --out work/mesh/L1-mesh.json --colors 5 --mode spline
  --colors   number of flat colours to keep (from analyze_logo: effective_colours_90pct)
  --mode     spline (smooth curves; most flat logos) | polygon (geometric marks)
Output JSON (same container as topomesh.py): {width, height, facets:[{id, area, color, d, tx, ty}]}
  'd' is SVG path data (may contain several sub-paths / holes); tx,ty is a translate offset.
"""
import argparse, json, os, re, tempfile
import numpy as np
from PIL import Image

def path_mask(d, tx, ty, W, H):
    """Rasterise an absolute M/L/C/Z path (vtracer output) with even-odd fill → bool mask."""
    from PIL import Image, ImageDraw
    toks = re.findall(r'[MLCZ]|-?\d*\.?\d+(?:e-?\d+)?', d); i = 0; subs = []; cur = []; pos = (0, 0); cmd = None
    while i < len(toks):
        t = toks[i]
        if t in 'MLCZ': cmd = t; i += 1
        if cmd == 'Z':
            if cur: subs.append(cur); cur = []
            continue
        if cmd == 'M':
            if cur: subs.append(cur)
            pos = (float(toks[i]) + tx, float(toks[i + 1]) + ty); cur = [pos]; i += 2; cmd = 'L'
        elif cmd == 'L':
            pos = (float(toks[i]) + tx, float(toks[i + 1]) + ty); cur.append(pos); i += 2
        elif cmd == 'C':
            c = [float(v) for v in toks[i:i + 6]]; i += 6
            p0 = pos; p1 = (c[0] + tx, c[1] + ty); p2 = (c[2] + tx, c[3] + ty); p3 = (c[4] + tx, c[5] + ty)
            for k in range(1, 9):
                u = k / 8; a_, b_, c_, d_ = (1 - u) ** 3, 3 * u * (1 - u) ** 2, 3 * u * u * (1 - u), u ** 3
                cur.append((a_ * p0[0] + b_ * p1[0] + c_ * p2[0] + d_ * p3[0], a_ * p0[1] + b_ * p1[1] + c_ * p2[1] + d_ * p3[1]))
            pos = p3
        else: i += 1
    if cur: subs.append(cur)
    m = np.zeros((H, W), bool)
    for sp in subs:
        if len(sp) < 3: continue
        im = Image.new('1', (W, H), 0); ImageDraw.Draw(im).polygon(sp, fill=1); m ^= np.array(im)
    return m

def fidelity(facets, q, mask, W, H):
    """Share of ink pixels whose traced colour differs from the quantised artwork (lower is better)."""
    pred = np.zeros((H, W, 3), np.int16) - 1
    for f in sorted(facets, key=lambda f: -f['area']):
        pm = path_mask(f['d'], f['tx'], f['ty'], W, H); pred[pm] = [int(f['color'][k:k + 2], 16) for k in (1, 3, 5)]
    bad = (np.abs(pred - q.astype(np.int16)).sum(2) > 30) & mask
    return float(bad.sum() / max(1, mask.sum()))

def trace(tmp_png, mode, speckle):
    import vtracer
    tmp_svg = tempfile.mktemp(suffix='.svg')
    vtracer.convert_image_to_svg_py(tmp_png, tmp_svg, colormode='color', hierarchical='cutout', mode=mode,
                                    filter_speckle=speckle, color_precision=8, layer_difference=8,
                                    corner_threshold=60, length_threshold=4.0, max_iterations=10, splice_threshold=45, path_precision=2)
    svg = open(tmp_svg).read(); os.remove(tmp_svg); facets = []
    for i, m in enumerate(re.finditer(r'<path d="([^"]+)" fill="(#[0-9A-Fa-f]{6})"(?: transform="translate\(([-\d.]+),([-\d.]+)\)")?', svg)):
        d, col, tx, ty = m.group(1), m.group(2).upper(), float(m.group(3) or 0), float(m.group(4) or 0)
        nums = [float(v) for v in re.findall(r'-?\d+\.?\d*', d)]
        xs, ys = nums[0::2], nums[1::2]
        area = (max(xs) - min(xs)) * (max(ys) - min(ys)) if xs and ys else 0
        facets.append({'id': i + 1, 'area': int(area), 'color': col, 'd': d.strip(), 'tx': tx, 'ty': ty})
    return facets

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('logo'); ap.add_argument('--out', required=True)
    ap.add_argument('--colors', type=int, default=5); ap.add_argument('--mode', default='spline', choices=['spline', 'polygon'])
    ap.add_argument('--speckle', type=int, default=8); ap.add_argument('--alpha-threshold', type=int, default=110)
    a = ap.parse_args()
    import cv2
    from sklearn.cluster import KMeans
    im = Image.open(a.logo).convert('RGBA'); arr = np.array(im); H, W = arr.shape[:2]
    alpha = arr[:, :, 3]
    mask = alpha > a.alpha_threshold if (alpha < 250).mean() > 0.01 else np.ones((H, W), bool)
    rgb = cv2.medianBlur(arr[:, :, :3].copy(), 3)
    px = rgb[mask].reshape(-1, 3).astype(float)
    uniq = len(np.unique((px[:: max(1, len(px) // 50000)] // 8).astype(int), axis=0))
    km = KMeans(n_clusters=max(1, min(a.colors, uniq)), n_init=4, random_state=0).fit(px[:: max(1, len(px) // 50000)])
    q = km.cluster_centers_[km.predict(rgb.reshape(-1, 3).astype(float))].reshape(H, W, 3).astype(np.uint8)
    out = np.dstack([q, np.where(mask, 255, 0).astype(np.uint8)])
    tmp_png = tempfile.mktemp(suffix='.png')
    Image.fromarray(out).save(tmp_png)
    facets = trace(tmp_png, a.mode, a.speckle); err = fidelity(facets, q, mask, W, H); used = a.mode
    if a.mode == 'spline' and err > 0.01:      # spline fitting can drift on long closed curves → compare with polygon mode
        alt = trace(tmp_png, 'polygon', a.speckle); err2 = fidelity(alt, q, mask, W, H)
        if err2 < err * 0.7: facets, err, used = alt, err2, 'polygon (spline drifted)'
    facets.sort(key=lambda f: -f['area'])
    json.dump({'width': W, 'height': H, 'facets': facets, 'kind': 'paths', 'mode': used, 'pixel_error': round(err, 4)}, open(a.out, 'w'))
    os.remove(tmp_png)
    print(f'{len(facets)} shapes ({a.colors} colours, {used}) · pixel error {err * 100:.2f}% → {a.out}')

if __name__ == '__main__':
    main()
