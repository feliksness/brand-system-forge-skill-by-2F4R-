#!/usr/bin/env python3
"""
topomesh.py — turn a label map into a WATERTIGHT polygon mesh (shared vertices, straight facet edges).

How: trace crack edges between pixels of different labels → chains between junctions (points where
3+ regions meet) → simplify each shared chain ONCE (so neighbours stay watertight) → assemble one ring
per region → colour each facet with the median colour of the ORIGINAL artwork beneath it.

Usage
  python3 scripts/vectorize/topomesh.py work/mesh/L1-labels.npy --logo logo.png --out work/mesh/L1-mesh.json \
          --tol-in 16 --tol-sil 1.6 --snap 5 --preview work/mesh/L1-compare.png
  --tol-in   interior edge tolerance in px (high = straight facet edges; 14–18 for faceted art)
  --tol-sil  silhouette tolerance (low = faithful outline)
  --snap     merge junctions closer than this (px)
Output JSON: {width, height, facets:[{id, area, color, points:[[x,y],…]}]} sorted by area (desc).
"""
import argparse, json, os
import numpy as np
from collections import defaultdict
from PIL import Image
from sklearn.cluster import DBSCAN

def dp(pts, tol):
    pts = np.asarray(pts, float)
    if len(pts) < 3: return pts
    A, B = pts[0], pts[-1]; AB = B - A; L = np.hypot(*AB)
    if L < 1e-9: d = np.hypot(*(pts - A).T)
    else:
        D = pts - A; d = np.abs(AB[0] * D[:, 1] - AB[1] * D[:, 0]) / L
    i = int(d.argmax())
    if d[i] > tol:
        l = dp(pts[:i + 1], tol); r = dp(pts[i:], tol)
        return np.vstack([l[:-1], r])
    return np.vstack([A, B])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('labels'); ap.add_argument('--logo', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--tol-in', type=float, default=16); ap.add_argument('--tol-sil', type=float, default=1.6)
    ap.add_argument('--snap', type=float, default=5); ap.add_argument('--preview')
    a = ap.parse_args()
    lab = np.load(a.labels); H, W = lab.shape
    P = np.pad(lab, 1, constant_values=0)
    edges = defaultdict(list)
    def add(n1, n2, pair): edges[n1].append((n2, pair)); edges[n2].append((n1, pair))
    for y in range(H + 1):
        up = P[y, 1:W + 1]; dn = P[y + 1, 1:W + 1]
        for x in np.where(up != dn)[0]: add((x, y), (x + 1, y), (min(up[x], dn[x]), max(up[x], dn[x])))
    for x in range(W + 1):
        lf = P[1:H + 1, x]; rt = P[1:H + 1, x + 1]
        for y in np.where(lf != rt)[0]: add((x, y), (x, y + 1), (min(lf[y], rt[y]), max(lf[y], rt[y])))
    def is_junction(n):
        e = edges[n]; return len(e) != 2 or e[0][1] != e[1][1]
    def ekey(p, q): return (p, q) if p < q else (q, p)
    visited = set(); chains = []
    for n in list(edges):
        if not is_junction(n): continue
        for (m, pair) in edges[n]:
            if ekey(n, m) in visited: continue
            pts = [n, m]; visited.add(ekey(n, m)); cur, prev = m, n
            while not is_junction(cur):
                nxt = [e for e in edges[cur] if e[0] != prev and e[1] == pair]
                if not nxt: break
                nx = nxt[0][0]
                if ekey(cur, nx) in visited: break
                visited.add(ekey(cur, nx)); pts.append(nx); prev, cur = cur, nx
            chains.append({'pair': pair, 'pts': pts})
    for n in list(edges):
        for (m, pair) in edges[n]:
            if ekey(n, m) in visited: continue
            pts = [n, m]; visited.add(ekey(n, m)); prev, cur = n, m
            while cur != n:
                nxt = [e for e in edges[cur] if e[0] != prev and e[1] == pair and ekey(cur, e[0]) not in visited]
                if not nxt: break
                nx = nxt[0][0]; visited.add(ekey(cur, nx)); pts.append(nx); prev, cur = cur, nx
            if cur != n: pts.append(n)
            chains.append({'pair': pair, 'pts': pts, 'loop': True})
    ends = np.array([c['pts'][0] for c in chains] + [c['pts'][-1] for c in chains], float)
    cl = DBSCAN(eps=a.snap, min_samples=1).fit(ends).labels_
    cent = {k: ends[cl == k].mean(0) for k in set(cl)}
    N = len(chains)
    for i, c in enumerate(chains): c['a'] = cl[i]; c['b'] = cl[N + i]
    for c in chains:
        pts = np.array(c['pts'], float); tol = a.tol_sil if 0 in c['pair'] else a.tol_in
        if c.get('loop'):
            h = len(pts) // 2; s = np.vstack([dp(pts[:h + 1], tol)[:-1], dp(pts[h:], tol)])
        else:
            s = dp(pts, tol); s[0] = cent[c['a']]; s[-1] = cent[c['b']]
        c['s'] = s
    regions = defaultdict(list)
    for i, c in enumerate(chains):
        for l in c['pair']:
            if l != 0: regions[l].append(i)
    def area(r):
        if len(r) < 3: return 0
        x, y = r[:, 0], r[:, 1]; return 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))
    polys = {}
    for l, ids in regions.items():
        rings = [chains[i]['s'] for i in ids if chains[i].get('loop')]
        open_ = [i for i in ids if not chains[i].get('loop')]
        adj = defaultdict(list)
        for i in open_: adj[chains[i]['a']].append(i); adj[chains[i]['b']].append(i)
        used = set()
        for start in open_:
            if start in used: continue
            ring = []; cur = start; node = chains[cur]['a']
            while True:
                used.add(cur); c = chains[cur]
                seg = c['s'] if c['a'] == node else c['s'][::-1]
                ring.extend(seg[:-1].tolist())
                node = c['b'] if c['a'] == node else c['a']
                cand = [j for j in adj[node] if j not in used]
                if not cand: break
                cur = cand[0]
            rings.append(np.array(ring))
        rings = [r for r in rings if len(r) >= 3]
        if rings: polys[l] = max(rings, key=area)
    img = np.array(Image.open(a.logo).convert('RGB')).astype(float)
    facets = []
    for l, r in polys.items():
        m = lab == l
        col = np.median(img[m], axis=0)
        rr = [r[0]]
        for p in r[1:]:
            if np.hypot(*(p - rr[-1])) > 0.5: rr.append(p)
        if len(rr) < 3: continue
        facets.append({'id': int(l), 'area': int(m.sum()), 'color': '#%02X%02X%02X' % tuple(int(v) for v in col),
                       'points': [[round(float(x), 1), round(float(y), 1)] for x, y in rr]})
    facets.sort(key=lambda f: -f['area'])
    json.dump({'width': W, 'height': H, 'facets': facets}, open(a.out, 'w'))
    print(f'{len(facets)} facets · {sum(len(f["points"]) for f in facets)} vertices → {a.out}')
    if a.preview:
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">' + ''.join(
            f'<polygon points="{" ".join(f"{x},{y}" for x, y in f["points"])}" fill="{f["color"]}" stroke="{f["color"]}" stroke-width="0.8" stroke-linejoin="round"/>'
            for f in facets) + '</svg>'
        tmp = a.out + '.preview.svg'; open(tmp, 'w').write(svg)
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        os.system(f'node "{here}/shot.js" "{tmp}" "{tmp}.png" {W} {H} 1 >/dev/null 2>&1')
        try:
            orig = Image.open(a.logo).convert('RGBA'); w = Image.new('RGBA', orig.size, (255, 255, 255, 255)); w.alpha_composite(orig)
            vec = Image.open(tmp + '.png').convert('RGB')
            cmp_ = Image.new('RGB', (W * 2 + 20, H), 'white'); cmp_.paste(w.convert('RGB'), (0, 0)); cmp_.paste(vec, (W + 20, 0)); cmp_.save(a.preview)
            os.remove(tmp + '.png')
        except Exception as e:
            print('preview failed:', e)
        os.remove(tmp)

if __name__ == '__main__':
    main()
