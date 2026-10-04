#!/usr/bin/env python3
"""
analyze_logo.py — measure a logo before designing anything around it.

usage: python3 scripts/analyze_logo.py <logo.png|jpg|webp|svg> --out <dir>

Writes into <dir>:
  logo-analysis.json  · logo-analysis.md (human summary)
  logo-swatches.png   · logo-grid.png · logo-angles.png
  logo-parts.png      components coloured by role: red = symbol, blue = lettering, green = monogram/compact candidate

What it measures
  colours        k-means (k = 6/10/14, area share, luminance, OKLCH), effective colours (90 % of ink), warm/cool share
  parts          connected components (alpha mask, then per colour layer for badges) → lettering rows (≥3 glyph-like
                 components on a shared baseline) → LOGO TYPE: symbol · combination · wordmark · emblem
                 + symbol box, text box, arrangement (horizontal/stacked), monogram box
  shape          silhouettes (all rings, 3 tolerances), optical centre, hull circularity, contour roundness, solidity,
                 true stroke width (skeleton), line-art detection — measured on the SYMBOL part (lettering excluded)
  edges          straight-edge share of the symbol outline, interior straightness (Hough), folded edge-angle families
  classification GEOMETRY angular · orthogonal · round · organic · mixed
                 COMPLEXITY flat · line · faceted · gradient · illustrative
                 ROUTE svg-native · flat-trace · faceted-mesh · gradient-raster
Every classification can be overridden in brand.config.json (logo.type / logo.geometry / logo.vectorize.route).
SVG input is rasterised with Playwright at 1024 px.
"""
import argparse, json, math, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from colorlib import to_oklch

def rasterise_svg(path, size=1024):
    out = tempfile.mktemp(suffix='.png'); html = tempfile.mktemp(suffix='.html')
    open(html, 'w').write(f'<html><body style="margin:0;background:transparent"><img src="file://{os.path.abspath(path)}" style="width:{size}px;height:{size}px;object-fit:contain"></body></html>')
    subprocess.check_call(['node', os.path.join(HERE, 'shot.js'), html, out, str(size), str(size), '1', '1']); return out

def rel_lum(rgb):
    c = np.asarray(rgb, float) / 255.0; c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]
def hexc(c): return '#%02X%02X%02X' % tuple(int(round(v)) for v in c)

def load_mask(arr, thr=110):
    alpha = arr[:, :, 3]
    if (alpha < 250).mean() > 0.01: return alpha > thr, True
    corner = np.median(np.concatenate([arr[:6, :6, :3].reshape(-1, 3), arr[-6:, -6:, :3].reshape(-1, 3), arr[:6, -6:, :3].reshape(-1, 3)]), axis=0)
    return np.abs(arr[:, :, :3].astype(int) - corner.astype(int)).sum(2) > 36, False

def components(mask, min_frac=0.0008, total=None):
    import cv2
    n, lab, stats, cent = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    tot = total or mask.sum(); comps = []
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if area < tot * min_frac: continue
        comps.append({'id': int(i), 'bbox': [int(x), int(y), int(x + w - 1), int(y + h - 1)], 'area': int(area), 'cx': float(cent[i][0]), 'cy': float(cent[i][1])})
    return lab, comps

def text_rows(comps):
    """Lettering = rows of ≥3 glyph-like components: similar height, shared baseline (or cap line), tight spacing."""
    hgt = lambda c: c['bbox'][3] - c['bbox'][1] + 1
    rows = []
    for c in sorted(comps, key=lambda c: c['cx']):
        h = hgt(c); placed = False
        for r in rows:
            rh = float(np.median([hgt(o) for o in r['items']]))
            if abs(c['cy'] - r['cy']) < 0.45 * rh and 0.45 < h / rh < 2.2:
                r['items'].append(c); r['cy'] = float(np.mean([o['cy'] for o in r['items']])); placed = True; break
        if not placed: rows.append({'cy': c['cy'], 'items': [c]})
    out = []
    for r in rows:
        it = sorted(r['items'], key=lambda c: c['bbox'][0])
        # split the row where a gap is too wide to be letter spacing
        groups, cur = [], [it[0]]
        for prev, c in zip(it, it[1:]):
            mh = float(np.median([hgt(o) for o in cur]))
            (cur.append(c) if c['bbox'][0] - prev['bbox'][2] < 1.25 * mh else (groups.append(cur), cur := [c]))
        groups.append(cur)
        for g in groups:
            if len(g) < 3: continue
            hs = np.array([hgt(c) for c in g], float); ws = np.array([c['bbox'][2] - c['bbox'][0] + 1 for c in g], float)
            mh = np.median(hs); bot = np.array([c['bbox'][3] for c in g], float); top = np.array([c['bbox'][1] for c in g], float)
            mad_b = np.median(np.abs(bot - np.median(bot))); mad_t = np.median(np.abs(top - np.median(top)))
            if hs.std() / hs.mean() < 0.5 and np.median(ws / hs) < 1.7 and min(mad_b, mad_t) < 0.1 * mh:
                out.append({'bbox': [min(c['bbox'][0] for c in g), min(c['bbox'][1] for c in g), max(c['bbox'][2] for c in g), max(c['bbox'][3] for c in g)],
                            'ids': [c['id'] for c in g], 'glyphs': len(g), 'height': int(mh)})
    return out

def union(boxes):
    boxes = [b for b in boxes if b]
    return [min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)] if boxes else None

def inside(b, o, tol=2):
    return b[0] >= o[0] - tol and b[1] >= o[1] - tol and b[2] <= o[2] + tol and b[3] <= o[3] + tol

def contour_metrics(mask, size):
    """Straight-edge share of all contours (outer + holes), roundness and folded straight-edge angles."""
    import cv2
    cs, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    eps = max(6.0, size * 0.012); thr = max(1.3, eps * 0.2); straight = per = 0.0; ang = np.zeros(18); round_w = round_a = 0.0
    for c in cs:
        P = cv2.arcLength(c, True); A = abs(cv2.contourArea(c))
        if A < (size * 0.02) ** 2: continue
        per += P; round_w += A; round_a += A * (4 * math.pi * A / (P * P))
        pts = c[:, 0, :].astype(float); ap = cv2.approxPolyDP(c, eps, True)[:, 0, :].astype(float)
        idx = [int(np.argmin(((pts - q) ** 2).sum(1))) for q in ap]
        for k in range(len(ap)):
            a, b = ap[k], ap[(k + 1) % len(ap)]; L = float(np.hypot(*(b - a)))
            if L < size * 0.03: continue
            i0, i1 = idx[k], idx[(k + 1) % len(ap)]
            seg = pts[i0:i1 + 1] if i0 <= i1 else np.vstack([pts[i0:], pts[:i1 + 1]])
            if len(seg) < 3: continue
            dvec = (b - a) / L; nrm = np.array([-dvec[1], dvec[0]]); dev = np.abs((seg - a) @ nrm).max()
            if dev <= thr:
                straight += L; t = math.degrees(math.atan2(-(b[1] - a[1]), b[0] - a[0])) % 180
                f = t if t <= 90 else 180 - t; ang[min(17, int(f // 5))] += L
    return {'straight_share': float(straight / per) if per else 0.0, 'roundness': float(round_a / round_w) if round_w else 0.0,
            'angles_folded': ang, 'perimeter': per}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('logo'); ap.add_argument('--out', required=True); ap.add_argument('--alpha-threshold', type=int, default=110)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    import cv2
    from scipy import ndimage
    from sklearn.cluster import KMeans
    from skimage.morphology import skeletonize
    src = rasterise_svg(a.logo) if a.logo.lower().endswith('.svg') else a.logo
    im = Image.open(src).convert('RGBA'); arr = np.array(im); H, W = arr.shape[:2]
    mask, has_alpha = load_mask(arr, a.alpha_threshold)
    mask = ndimage.binary_opening(mask, iterations=1)
    ys, xs = np.where(mask); bbox = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    size = max(bbox[2] - bbox[0] + 1, bbox[3] - bbox[1] + 1)
    px = arr[mask][:, :3].astype(float)
    # ---------------------------------------------------------------- colours
    clusters = {}; sample = px[:: max(1, len(px) // 60000)]
    uniq = len(np.unique((sample // 6).astype(int), axis=0)); km6 = None
    for k in (6, 10, 14):
        kk = max(1, min(k, uniq)); km = KMeans(n_clusters=kk, n_init=4, random_state=0).fit(sample)
        if k == 6: km6 = km
        lab = km.predict(px); cnt = np.bincount(lab, minlength=kk); order = np.argsort(-cnt)
        clusters[str(k)] = []
        for i in order:
            hx = hexc(km.cluster_centers_[i]); L, C, Hh = to_oklch(hx)
            clusters[str(k)].append({'hex': hx, 'share': round(float(cnt[i] / len(px)), 4), 'luminance': round(float(rel_lum(km.cluster_centers_[i])), 4),
                                     'oklch': [round(L, 3), round(C, 3), round(Hh, 1)]})
    lum = rel_lum(px); warm = (px[:, 0] > px[:, 2] + 8).mean(); cool = (px[:, 2] > px[:, 0] + 4).mean()
    shares = sorted([c['share'] for c in clusters['14']], reverse=True); eff = int(np.searchsorted(np.cumsum(shares), 0.9) + 1)
    qcount = len(np.unique((sample // 12).astype(int), axis=0))
    # interior edge density (sharp colour boundaries inside the ink) — separates faceted/flat from gradient art
    g = cv2.GaussianBlur(arr[:, :, :3].astype(np.float32), (0, 0), 1.2)
    gm = np.zeros((H, W), np.float32)
    for ch in range(3):
        gx = cv2.Sobel(g[:, :, ch], cv2.CV_32F, 1, 0, ksize=3); gy = cv2.Sobel(g[:, :, ch], cv2.CV_32F, 0, 1, ksize=3); gm = np.maximum(gm, np.hypot(gx, gy))
    inner = ndimage.binary_erosion(mask, iterations=4)
    edge_density = float((gm[inner] > 60).mean()) if inner.any() else 0.0
    soft_alpha = float(((arr[:, :, 3] > 15) & (arr[:, :, 3] < 240)).sum() / max(1, cv2.Canny(mask.astype(np.uint8) * 255, 50, 150).astype(bool).sum())) if has_alpha else 0.0
    # ---------------------------------------------------------------- parts → logo type
    lab_img, comps = components(mask)
    ink = sum(c['area'] for c in comps) or 1
    rows = text_rows(comps); text_src = 'alpha'
    big = max(comps, key=lambda c: c['area']) if comps else None
    if not rows and km6 is not None and big and eff <= 6:
        # badges/emblems: lettering lives inside a filled shape → look for rows in each colour layer
        labels = km6.predict(arr.reshape(-1, 4)[:, :3].astype(float)).reshape(H, W)
        for li in range(km6.n_clusters):
            layer = ndimage.binary_opening((labels == li) & mask, iterations=1)
            if layer.sum() < 0.01 * ink or layer.sum() > 0.7 * ink: continue
            _, lc = components(layer, 0.0008, total=ink)
            lr = [r for r in text_rows(lc) if inside(r['bbox'], big['bbox'])]
            if lr: rows += lr; text_src = 'colour-layer'
    text_box = union([r['bbox'] for r in rows])
    text_ids = {i for r in rows for i in r['ids']} if text_src == 'alpha' else set()
    def near_text(c):   # dots of i/j, accents, punctuation
        if not text_box: return False
        rh = max(r['height'] for r in rows); tb = [text_box[0] - rh * 0.3, text_box[1] - rh * 0.6, text_box[2] + rh * 0.3, text_box[3] + rh * 0.4]
        return inside(c['bbox'], tb) and c['area'] < 0.03 * ink
    symbol_comps = [c for c in comps if c['id'] not in text_ids and not near_text(c)]
    sig_symbol = [c for c in symbol_comps if c['area'] > 0.03 * ink]
    text_ink = sum(c['area'] for c in comps if c['id'] in text_ids or near_text(c))
    if rows and text_src == 'colour-layer':
        logo_type = 'emblem'
    elif rows and big and big['id'] not in text_ids and all(inside(r['bbox'], big['bbox']) for r in rows) and big['area'] > 0.3 * ink:
        logo_type = 'emblem'             # lettering contained inside a frame/badge → the whole thing is one mark
    elif rows and (text_ink / ink > 0.8 or not sig_symbol):
        logo_type = 'wordmark'
    elif rows and sig_symbol:
        logo_type = 'combination'
    else:
        logo_type = 'symbol'
    symbol_box = union([c['bbox'] for c in sig_symbol]) if logo_type == 'combination' else (bbox if logo_type in ('symbol', 'emblem') else None)
    arrangement = None
    if logo_type == 'combination' and symbol_box and text_box:
        xo = min(symbol_box[2], text_box[2]) - max(symbol_box[0], text_box[0]); yo = min(symbol_box[3], text_box[3]) - max(symbol_box[1], text_box[1])
        arrangement = 'stacked' if xo > 0 and yo <= 0 else 'horizontal' if yo > 0 and xo <= 0 else 'overlapping'
    mono_box = None
    if logo_type == 'wordmark' and rows:
        first = min((c for c in comps if c['id'] in rows[0]['ids']), key=lambda c: c['bbox'][0]); mono_box = first['bbox']
    # ---------------------------------------------------------------- symbol mask (geometry is read from the symbol, not the lettering)
    if logo_type == 'combination':
        smask = np.isin(lab_img, [c['id'] for c in symbol_comps])
    elif logo_type == 'wordmark':
        smask = mask.copy()
    else:
        smask = mask.copy()
    if not smask.any(): smask = mask.copy()
    sy, sx = np.where(smask); sb = [int(sx.min()), int(sy.min()), int(sx.max()), int(sy.max())]; ssize = max(sb[2] - sb[0] + 1, sb[3] - sb[1] + 1)
    cs_all, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    cs_all = [c for c in cs_all if cv2.contourArea(c) > mask.sum() * 0.0004]
    sil = {str(e): [cv2.approxPolyDP(c, e, True)[:, 0, :].tolist() for c in cs_all] for e in (1.5, 4, 8)}
    M = cv2.moments(smask.astype(np.uint8), binaryImage=True); centroid = [M['m10'] / M['m00'], M['m01'] / M['m00']]
    scs, _ = cv2.findContours(smask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    hull = cv2.convexHull(np.vstack(scs)); hull_area = cv2.contourArea(hull); hull_per = cv2.arcLength(hull, True)
    circularity = float(4 * math.pi * hull_area / (hull_per ** 2)) if hull_per else 0
    solidity = float(smask.sum() / hull_area) if hull_area else 0
    fill_ratio = float(smask.sum() / ((sb[2] - sb[0] + 1) * (sb[3] - sb[1] + 1)))
    dist = ndimage.distance_transform_edt(smask); sk = skeletonize(smask)
    stroke_w = float(np.median(dist[sk]) * 2) if sk.any() else 0.0
    stroke_cover = float(sk.sum() * stroke_w / max(1, smask.sum())) if stroke_w else 0.0
    line_logo = stroke_w < ssize * 0.05 and fill_ratio < 0.35 and stroke_cover > 0.6 and logo_type != 'wordmark'
    cm = contour_metrics(smask, ssize)
    # interior straightness (facet edges) via Hough, inside the symbol only
    sm = arr[:, :, :3].copy()
    for _ in range(2): sm = cv2.bilateralFilter(sm, 9, 40, 9)
    edges = cv2.Canny(cv2.cvtColor(sm, cv2.COLOR_RGB2GRAY), 40, 110) * ndimage.binary_erosion(smask, iterations=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 360, threshold=30, minLineLength=max(14, ssize // 30), maxLineGap=3)
    hist = np.zeros(36); straight_len = 0.0
    if lines is not None:
        for x1, y1, x2, y2 in np.asarray(lines).reshape(-1, 4):
            L = math.hypot(x2 - x1, y2 - y1); angd = math.degrees(math.atan2(-(y2 - y1), x2 - x1)) % 180
            hist[int(angd // 5) % 36] += L; straight_len += L
    interior_straight = float(min(1.0, straight_len / max(1.0, float((edges > 0).sum())))) if (edges > 0).sum() > ssize else 0.0
    fold = cm['angles_folded'].copy()
    for i, v in enumerate(hist):
        a0 = i * 5; f = a0 if a0 < 90 else 180 - a0 - 5; fold[int(max(0, min(85, f)) // 5)] += v
    fam = [{'range_deg': [int(i * 5), int(i * 5 + 5)], 'weight': round(float(fold[i] / max(1, fold.sum())), 4)} for i in np.argsort(-fold)[:6] if fold[i] > 0]
    # ---------------------------------------------------------------- classification
    if line_logo: complexity = 'line'
    elif eff >= 8 and edge_density < 0.02: complexity = 'gradient'
    elif eff >= 8 and interior_straight > 0.3: complexity = 'faceted'
    elif eff >= 8: complexity = 'illustrative'
    else: complexity = 'flat'
    S = max(cm['straight_share'], interior_straight if complexity == 'faceted' else 0)
    diag = sum(f['weight'] for f in fam if 10 <= f['range_deg'][0] < 80)
    if S > 0.55: geometry = 'angular' if diag > 0.3 else 'orthogonal'
    elif S < 0.25: geometry = 'round' if (cm['roundness'] > 0.8 or circularity > 0.86) else 'organic'
    else: geometry = 'mixed'
    if logo_type == 'wordmark' and geometry in ('angular', 'orthogonal') and S < 0.7: geometry = 'mixed'
    if a.logo.lower().endswith('.svg'): route = 'svg-native'
    elif complexity == 'faceted': route = 'faceted-mesh'
    elif complexity in ('flat', 'line'): route = 'flat-trace'
    else: route = 'gradient-raster'   # keep the raster as primary; build a posterised flat-trace mark for scalable uses
    warnings = []
    if max(W, H) < 800: warnings.append(f'Artwork is only {max(W, H)} px — ask for a vector or ≥ 2000 px original; large-format use depends on the vector.')
    if not has_alpha: warnings.append('No transparency — background removed by colour distance from the corners; check logo-parts.png.')
    if logo_type == 'symbol' and (bbox[2] - bbox[0]) > 3 * (bbox[3] - bbox[1]): warnings.append('Very wide "symbol": may be connected/script lettering. If so set logo.type = "wordmark" in brand.config.json.')
    if complexity in ('gradient', 'illustrative'): warnings.append('Raster-dependent artwork: the original stays primary; a posterised vector is built for one-colour/small uses.')
    res = {'file': os.path.basename(a.logo), 'size': [W, H], 'has_alpha': bool(has_alpha), 'bbox': bbox,
           'bbox_size': [bbox[2] - bbox[0] + 1, bbox[3] - bbox[1] + 1],
           'logo_type': logo_type, 'arrangement': arrangement, 'geometry': geometry, 'complexity': complexity, 'suggested_route': route,
           'symbol_box': symbol_box, 'text_box': text_box, 'monogram_box': mono_box, 'text_rows': rows, 'text_source': text_src if rows else None,
           'centroid': [round(c, 1) for c in centroid],
           'optical_offset': [round((centroid[0] - (sb[0] + sb[2]) / 2) / max(1, sb[2] - sb[0]), 4), round((centroid[1] - (sb[1] + sb[3]) / 2) / max(1, sb[3] - sb[1]), 4)],
           'colours': clusters, 'effective_colours_90pct': eff, 'colour_variety_q12': qcount, 'interior_edge_density': round(edge_density, 4),
           'soft_alpha_ratio': round(soft_alpha, 2),
           'luminance': {'mean': round(float(lum.mean()), 4), 'dark_share_lt_0_05': round(float((lum < 0.05).mean()), 4), 'light_share_gt_0_7': round(float((lum > 0.7).mean()), 4)},
           'temperature': {'warm_share': round(float(warm), 4), 'cool_share': round(float(cool), 4)},
           'shape': {'parts': len(comps), 'symbol_parts': len(sig_symbol), 'circularity_hull': round(circularity, 3), 'roundness_contours': round(cm['roundness'], 3),
                     'solidity': round(solidity, 3), 'fill_ratio': round(fill_ratio, 3), 'stroke_width_px': round(stroke_w, 1),
                     'stroke_width_ratio': round(stroke_w / ssize, 4), 'stroke_coverage': round(stroke_cover, 2)},
           'edges': {'outline_straight_share': round(cm['straight_share'], 3), 'interior_straightness': round(interior_straight, 3), 'angle_families_folded': fam},
           'silhouette': sil, 'warnings': warnings,
           'notes': ['The supplied artwork is the primary logo and is never altered; vectors are faithful scalable equivalents.',
                     'Lettering in combination/wordmark/emblem logos is TRACED, never re-typeset (scripts/separate_lockup.py).',
                     'Edge-angle families feed the design DNA (scripts/derive_dna.py): chamfer angle, crop angle, pattern angles.']}
    json.dump(res, open(os.path.join(a.out, 'logo-analysis.json'), 'w'), indent=2)
    # ---------------------------------------------------------------- images
    try: f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', 13)
    except Exception: f = None
    img = Image.new('RGB', (1400, 220), 'white'); d = ImageDraw.Draw(img); x = 0
    for c in clusters['14']:
        w = max(2, int(round(c['share'] * 1400))); d.rectangle([x, 0, x + w, 150], fill=c['hex'])
        if w > 60: d.text((x + 4, 158), f"{c['hex']}\n{c['share']*100:.1f}%", fill='black', font=f)
        x += w
    img.save(os.path.join(a.out, 'logo-swatches.png'))
    Sx = 2 if max(W, H) <= 1200 else 1; bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); bg.alpha_composite(im); big_im = bg.resize((W * Sx, H * Sx), Image.LANCZOS); d = ImageDraw.Draw(big_im)
    step = 25 if max(W, H) <= 800 else 50
    for gx in range(0, W, step): d.line([(gx * Sx, 0), (gx * Sx, H * Sx)], fill=(0, 160, 255, 255) if gx % (step * 4) == 0 else (0, 200, 255, 90))
    for gy in range(0, H, step): d.line([(0, gy * Sx), (W * Sx, gy * Sx)], fill=(0, 160, 255, 255) if gy % (step * 4) == 0 else (0, 200, 255, 90))
    big_im.convert('RGB').save(os.path.join(a.out, 'logo-grid.png'))
    hi = Image.new('RGB', (760, 260), 'white'); d = ImageDraw.Draw(hi); mx = max(1, hist.max())
    for i, v in enumerate(hist):
        h = int(200 * v / mx); d.rectangle([20 + i * 20, 220 - h, 34 + i * 20, 220], fill=(60, 60, 70))
        if i % 3 == 0: d.text((18 + i * 20, 228), f'{i*5}°', fill='black', font=f)
    hi.save(os.path.join(a.out, 'logo-angles.png'))
    pv = bg.copy().convert('RGB'); d = ImageDraw.Draw(pv)
    for c in comps:
        col = (0, 120, 255) if (c['id'] in text_ids or near_text(c)) else (230, 60, 40); d.rectangle(c['bbox'], outline=col, width=2)
    for r in rows: d.rectangle(r['bbox'], outline=(0, 120, 255), width=2)
    for b, col in ((symbol_box, (230, 60, 40)), (text_box, (0, 120, 255)), (mono_box, (0, 170, 90))):
        if b: d.rectangle([b[0] - 4, b[1] - 4, b[2] + 4, b[3] + 4], outline=col, width=4)
    pv.save(os.path.join(a.out, 'logo-parts.png'))
    md = [f"# Logo analysis — {res['file']}", '',
          f"- **Logo type: {logo_type}**{' (' + arrangement + ')' if arrangement else ''} · **geometry: {geometry}** · **complexity: {complexity}** · route: **{route}**",
          f"- Size {W}×{H}px · alpha {has_alpha} · artwork {res['bbox_size'][0]}×{res['bbox_size'][1]}px · parts {len(comps)} (symbol parts {len(sig_symbol)}) · lettering rows {len(rows)}",
          f"- Effective colours (90% of ink) {eff} · interior edge density {edge_density:.3f} · outline straight share {cm['straight_share']:.2f} · interior straightness {interior_straight:.2f}",
          f"- Hull circularity {circularity:.2f} · contour roundness {cm['roundness']:.2f} · solidity {solidity:.2f} · stroke {stroke_w:.1f}px ({stroke_w / ssize * 100:.1f}% of size) · line art {line_logo}",
          f"- Optical centre offset x {res['optical_offset'][0]*100:.1f}% · y {res['optical_offset'][1]*100:.1f}% · dark share {res['luminance']['dark_share_lt_0_05']*100:.0f}% · warm {warm*100:.0f}% / cool {cool*100:.0f}%",
          f"- Symbol box {symbol_box} · text box {text_box} · monogram box {mono_box}  (logo-parts.png: red = symbol, blue = lettering, green = monogram)",
          *[f"- ⚠ {w}" for w in warnings],
          '', '| HEX | share | rel. luminance | OKLCH |', '|---|---|---|---|'] + [f"| `{c['hex']}` | {c['share']*100:.1f}% | {c['luminance']} | {c['oklch']} |" for c in clusters['14']] + \
         ['', '## Edge-angle families (folded 0–90°)', ''] + [f"- {x['range_deg'][0]}–{x['range_deg'][1]}°: {x['weight']*100:.1f}%" for x in fam]
    open(os.path.join(a.out, 'logo-analysis.md'), 'w').write('\n'.join(md) + '\n')
    print(json.dumps({k: res[k] for k in ('logo_type', 'arrangement', 'geometry', 'complexity', 'suggested_route', 'effective_colours_90pct')}))

if __name__ == '__main__':
    main()
