#!/usr/bin/env python3
"""
facetize.py — segment a faceted / low-poly / textured logo into facet regions (label map).

Pipeline: edge-preserving smoothing (bilateral ×3 + mean-shift) → SLIC superpixels →
region-adjacency merge by colour → small-region cleanup → majority filter.
The label map is then turned into a watertight polygon mesh by topomesh.py.

Usage
  python3 scripts/vectorize/facetize.py logo.png --out work/mesh --name L1 --thresh 20 --amin 180 --nseg 1100 --maj 5
Outputs  <out>/<name>-labels.npy  and  <out>/<name>-labels.png (preview, region mean colours + white boundaries)

Tuning (for a ~600 px logo; scale --amin with area):
  master detail   --thresh 20 --amin 180 --nseg 1100 --maj 5     (~130 facets)
  simplified      --thresh 34 --amin 900 --nseg 600  --maj 7     (~35 facets)
  micro           --thresh 60 --amin 2500 --nseg 250 --maj 9     (~20 facets)
Lower --thresh = more facets (stricter colour merge). Raise --amin to drop texture specks.
"""
import argparse, os
import numpy as np, cv2
from PIL import Image
from skimage import segmentation, graph
from scipy import ndimage

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('logo'); ap.add_argument('--out', required=True); ap.add_argument('--name', default='L1')
    ap.add_argument('--thresh', type=float, default=20); ap.add_argument('--amin', type=int, default=180)
    ap.add_argument('--nseg', type=int, default=1100); ap.add_argument('--maj', type=int, default=5)
    ap.add_argument('--alpha-threshold', type=int, default=110)
    ap.add_argument('--compactness', type=float, default=14)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    im = Image.open(a.logo).convert('RGBA'); arr = np.array(im)
    alpha = arr[:, :, 3]; rgb = arr[:, :, :3].copy()
    if (alpha < 250).mean() > 0.01:
        mask = alpha > a.alpha_threshold
    else:
        corner = np.median(np.concatenate([rgb[:5, :5].reshape(-1, 3), rgb[-5:, -5:].reshape(-1, 3)]), axis=0)
        mask = np.abs(rgb.astype(int) - corner.astype(int)).sum(2) > 30
    mask = ndimage.binary_opening(mask, iterations=1)
    sm = rgb.copy()
    for _ in range(3): sm = cv2.bilateralFilter(sm, 9, 40, 9)
    sm = cv2.pyrMeanShiftFiltering(sm, 12, 26)
    seg = segmentation.slic(sm, n_segments=a.nseg, compactness=a.compactness, mask=mask, start_label=1)

    def wfn(g, src, dst, n): return {'weight': np.linalg.norm(g.nodes[dst]['mean color'] - g.nodes[n]['mean color'])}
    def mfn(g, src, dst):
        g.nodes[dst]['total color'] += g.nodes[src]['total color']
        g.nodes[dst]['pixel count'] += g.nodes[src]['pixel count']
        g.nodes[dst]['mean color'] = g.nodes[dst]['total color'] / g.nodes[dst]['pixel count']
    rag = graph.rag_mean_color(sm, seg)
    lab = graph.merge_hierarchical(seg, rag, thresh=a.thresh, rag_copy=False, in_place_merge=True, merge_func=mfn, weight_func=wfn)
    lab = lab + 1; lab[~mask] = 0
    lab, _, _ = segmentation.relabel_sequential(lab)
    # merge small regions into the most similar neighbour
    for _ in range(12):
        changed = False
        ids, counts = np.unique(lab, return_counts=True)
        for l, area in sorted(zip(ids, counts), key=lambda t: t[1]):
            if l == 0 or area >= a.amin: continue
            m = lab == l
            if not m.any(): continue
            ring = ndimage.binary_dilation(m, iterations=2) & ~m
            nb = [n for n in np.unique(lab[ring]) if n not in (0, l)]
            if not nb: continue
            mc = sm[m].mean(0)
            best = min(nb, key=lambda n: np.linalg.norm(sm[lab == n].mean(0) - mc) - 0.02 * (lab[ring] == n).sum())
            lab[m] = best; changed = True
        if not changed: break
    if a.maj > 1:
        lab = ndimage.generic_filter(lab, lambda v: np.bincount(v.astype(int)).argmax(), size=a.maj, mode='nearest')
    lab[~mask] = 0
    lab, _, _ = segmentation.relabel_sequential(lab)
    np.save(os.path.join(a.out, f'{a.name}-labels.npy'), lab)
    out = np.full_like(rgb, 255)
    for l in np.unique(lab):
        if l == 0: continue
        m = lab == l; out[m] = np.median(rgb[m], axis=0)
    out[segmentation.find_boundaries(lab)] = 255
    Image.fromarray(out).save(os.path.join(a.out, f'{a.name}-labels.png'))
    print(f'{a.name}: {lab.max()} regions → {a.out}/{a.name}-labels.npy')

if __name__ == '__main__':
    main()
