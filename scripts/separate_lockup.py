#!/usr/bin/env python3
"""
separate_lockup.py — split the supplied logo into its parts so each can be vectorised and used on its own.

usage: python3 scripts/separate_lockup.py <logo.png> --analysis <logo-analysis.json> --out <work/parts> [--type combination]

Uses the logo type from analyze_logo.py (or --type to override):
  symbol       symbol.png = the whole artwork                        compact mark = simplified symbol
  emblem       symbol.png = the whole artwork (lettering stays inside) compact mark = simplified emblem
  combination  symbol.png = symbol components only · lettering.png = lettering only (dots/accents included)
  wordmark     lettering.png = the whole artwork · monogram.png = first glyph (compact mark candidate)
Writes <out>/{symbol,lettering,monogram}.png (transparent, cropped with padding) and <out>/logo-parts.json:
  boxes in artwork pixels, crop offsets, and the LAYOUT RELATIONS of the original lockup (gap, lettering height and
  alignment relative to the symbol) so the logo system can rebuild the original exactly and derive alternates
  with the same proportions. The lettering is never re-typeset: it is traced from lettering.png.
"""
import argparse, json, os
import numpy as np
from PIL import Image

COLOURS = {}
def sig_colours(rgba):
    """Number of significant flat colours in a crop (k-means, near-duplicates merged in OKLab, ≥ 1.2 % of ink)."""
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from colorlib import to_oklab
    from sklearn.cluster import KMeans
    px = rgba[rgba[:, :, 3] > 200][:, :3].astype(float)
    if len(px) < 50: return 1
    px = px[:: max(1, len(px) // 40000)]; k = min(8, len(np.unique((px // 8).astype(int), axis=0)))
    km = KMeans(n_clusters=max(1, k), n_init=3, random_state=0).fit(px); cnt = np.bincount(km.labels_, minlength=k) / len(px)
    keep = []
    for i in np.argsort(-cnt):
        if cnt[i] < 0.012: continue
        lab = to_oklab('#%02X%02X%02X' % tuple(int(v) for v in km.cluster_centers_[i]))
        if not any(sum((a - b) ** 2 for a, b in zip(lab, o)) ** 0.5 < 0.06 for o in keep): keep.append(lab)
    return max(1, len(keep))

def crop(arr, keep, box, pad, path):
    out = arr.copy(); out[~keep] = 0
    x0, y0 = max(0, box[0] - pad), max(0, box[1] - pad); x1, y1 = min(arr.shape[1], box[2] + pad + 1), min(arr.shape[0], box[3] + pad + 1)
    Image.fromarray(out[y0:y1, x0:x1]).save(path); COLOURS[os.path.basename(path)] = sig_colours(out[y0:y1, x0:x1]); return [int(x0), int(y0)]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('logo'); ap.add_argument('--analysis', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--type'); ap.add_argument('--alpha-threshold', type=int, default=110)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    import cv2
    from scipy import ndimage
    A = json.load(open(a.analysis)); T = a.type or A['logo_type']
    im = Image.open(a.logo).convert('RGBA'); arr = np.array(im); H, W = arr.shape[:2]
    if A['has_alpha']:
        mask = arr[:, :, 3] > a.alpha_threshold
    else:   # make the background transparent so crops are clean
        corner = np.median(np.concatenate([arr[:6, :6, :3].reshape(-1, 3), arr[-6:, -6:, :3].reshape(-1, 3)]), axis=0)
        mask = np.abs(arr[:, :, :3].astype(int) - corner.astype(int)).sum(2) > 36; arr[:, :, 3] = np.where(mask, 255, 0)
    soft = ndimage.binary_dilation(mask, iterations=2)          # keep anti-aliased edges with their component
    n, lab = cv2.connectedComponents(soft.astype(np.uint8), connectivity=8)
    pad = max(8, int(0.03 * max(W, H)))
    sb, tb = A.get('symbol_box'), A.get('text_box')
    parts = {'logo_type': T, 'arrangement': A.get('arrangement'), 'artwork_size': [W, H], 'artwork_bbox': A['bbox'], 'crops': {}}
    def ids_in(box, grow=0):
        if not box: return []
        g = grow; sub = lab[max(0, box[1] - g):box[3] + g + 1, max(0, box[0] - g):box[2] + g + 1]
        return [i for i in np.unique(sub) if i]
    if T in ('symbol', 'emblem'):
        parts['crops']['symbol'] = {'file': 'symbol.png', 'offset': crop(arr, soft, A['bbox'], pad, os.path.join(a.out, 'symbol.png')), 'box': A['bbox']}
    if T == 'combination' and sb and tb:
        rh = max(r['height'] for r in A['text_rows'])
        tgrow = [tb[0] - int(rh * .3), tb[1] - int(rh * .6), tb[2] + int(rh * .3), tb[3] + int(rh * .4)]
        t_ids = set(ids_in(tb))
        # components that sit inside the grown text box and are small (dots, accents) belong to the lettering too
        for i in ids_in(tgrow):
            ys, xs = np.where(lab == i)
            if xs.min() >= tgrow[0] and xs.max() <= tgrow[2] and ys.min() >= tgrow[1] and ys.max() <= tgrow[3]: t_ids.add(i)
        s_ids = [i for i in range(1, n) if i not in t_ids and (lab == i).sum() > 0.002 * mask.sum()]
        smask = np.isin(lab, s_ids) & soft; tmask = np.isin(lab, list(t_ids)) & soft
        ys, xs = np.where(smask); sbox = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
        ys, xs = np.where(tmask); tbox = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
        parts['crops']['symbol'] = {'file': 'symbol.png', 'offset': crop(arr, smask, sbox, pad, os.path.join(a.out, 'symbol.png')), 'box': sbox}
        parts['crops']['lettering'] = {'file': 'lettering.png', 'offset': crop(arr, tmask, tbox, pad, os.path.join(a.out, 'lettering.png')), 'box': tbox}
        sh = sbox[3] - sbox[1] + 1; sw = sbox[2] - sbox[0] + 1
        rows = sorted(A['text_rows'], key=lambda r: r['bbox'][1])
        rel = {'symbol_size': [sw, sh], 'lettering_size': [tbox[2] - tbox[0] + 1, tbox[3] - tbox[1] + 1],
               'row_heights_rel_symbol': [round(r['height'] / sh, 4) for r in rows],
               'lettering_height_rel_symbol': round((tbox[3] - tbox[1] + 1) / sh, 4)}
        if parts['arrangement'] == 'horizontal':
            rel['gap_rel_symbol_height'] = round((tbox[0] - sbox[2]) / sh, 4) if tbox[0] > sbox[2] else round((sbox[0] - tbox[2]) / sh, 4)
            rel['symbol_side'] = 'left' if sbox[0] < tbox[0] else 'right'
            rel['lettering_center_offset_rel'] = round(((tbox[1] + tbox[3]) / 2 - (sbox[1] + sbox[3]) / 2) / sh, 4)
            rel['align'] = 'center' if abs(rel['lettering_center_offset_rel']) < 0.06 else ('top' if abs(tbox[1] - sbox[1]) < 0.06 * sh else 'bottom' if abs(tbox[3] - sbox[3]) < 0.06 * sh else 'free')
        elif parts['arrangement'] == 'stacked':
            rel['gap_rel_symbol_height'] = round((tbox[1] - sbox[3]) / sh, 4) if tbox[1] > sbox[3] else round((sbox[1] - tbox[3]) / sh, 4)
            rel['symbol_side'] = 'top' if sbox[1] < tbox[1] else 'bottom'
            rel['lettering_center_offset_rel'] = round(((tbox[0] + tbox[2]) / 2 - (sbox[0] + sbox[2]) / 2) / sw, 4)
            rel['align'] = 'center' if abs(rel['lettering_center_offset_rel']) < 0.06 else ('left' if abs(tbox[0] - sbox[0]) < 0.06 * sw else 'right' if abs(tbox[2] - sbox[2]) < 0.06 * sw else 'free')
        parts['layout'] = rel
    elif T == 'combination':
        print('combination without both boxes — falling back to symbol'); parts['logo_type'] = T = 'symbol'
        parts['crops']['symbol'] = {'file': 'symbol.png', 'offset': crop(arr, soft, A['bbox'], pad, os.path.join(a.out, 'symbol.png')), 'box': A['bbox']}
    if T == 'wordmark':
        parts['crops']['lettering'] = {'file': 'lettering.png', 'offset': crop(arr, soft, A['bbox'], pad, os.path.join(a.out, 'lettering.png')), 'box': A['bbox']}
        mb = A.get('monogram_box')
        if mb:
            mk = np.zeros_like(soft); mk[mb[1]:mb[3] + 1, mb[0]:mb[2] + 1] = True
            mmask = np.isin(lab, ids_in(mb)) & soft & ndimage.binary_dilation(mk, iterations=3)
            parts['crops']['monogram'] = {'file': 'monogram.png', 'offset': crop(arr, mmask, mb, pad // 2, os.path.join(a.out, 'monogram.png')), 'box': mb}
    for k, v in parts['crops'].items(): v['colours'] = COLOURS.get(v['file'], 1)
    parts['compact'] = {'symbol': 'symbol-simplified', 'emblem': 'symbol-simplified', 'combination': 'symbol-simplified', 'wordmark': 'monogram'}[T]
    json.dump(parts, open(os.path.join(a.out, 'logo-parts.json'), 'w'), indent=2)
    print(f'{T}: ' + ', '.join(f"{k} {v['box']} ({v['colours']} colours)" for k, v in parts['crops'].items()) + (f" · layout {parts.get('layout')}" if parts.get('layout') else ''))

if __name__ == '__main__':
    main()
