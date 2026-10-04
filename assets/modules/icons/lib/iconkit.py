"""
iconkit — a small geometric icon engine.

Icons are DEFINED once as primitives on a 24 x 24 grid (lines, polylines, polygons, rects, circles, ellipses,
arcs, quadratic/cubic curves, dots) and RENDERED per brand: the design DNA decides stroke width, caps, joins,
how tagged corners are treated (cut → chamfer at dna.angles.cut · round/soft → fillets · square → sharp) and
how curves are drawn (true arcs · faceted polygons for faceted brands · eased joints for organic brands).

Coordinates are centre-lines. Keylines (ink, at stroke 2): live area 2…22 → centre-lines 3…21, circle r 9.

Corner tags (third value of a point, or the last value of a P() segment):
  'c'      container corner — cut brands chamfer only the bottom-right-most one per shape (the brand cut,
           like .p-shape in CSS); round/soft brands round every one; square brands keep them sharp
  's<n>'   shape corner with nominal radius n (shoulders, rounded ends) — round: fillet n · soft: n × 1.15 ·
           cut: chamfer each (size ≈ n) · square: sharp
  'm'      minor corner — eased a little on round/soft brands, sharp on angular ones
  'x'      always sharp (arrow tips, pencil points)
  None     untagged — sharp, except on organic brands where every joint is eased slightly
"""
import math, copy, re

GRID = 24
D2R = math.pi / 180.0


# =====================================================================================================
# 1. PRIMITIVES (used by icons_def.py)
# =====================================================================================================
def _prim(kind, **kw):
    d = {'k': kind, 'fill': None, 'stroke': True, 'solid': False}
    d.update(kw)
    return d


def _pts(pts):
    return [(float(p[0]), float(p[1]), (p[2] if len(p) > 2 else None)) for p in pts]


def PL(*pts, **kw):
    """Open polyline."""
    p = _pts(pts)
    segs = [('M', p[0][0], p[0][1], p[0][2])] + [('L', x, y, t) for x, y, t in p[1:]]
    return _prim('path', segs=segs, closed=False, **kw)


def PG(*pts, **kw):
    """Closed polygon."""
    d = PL(*pts, **kw)
    d['closed'] = True
    return d


def L(x1, y1, x2, y2, **kw):
    return PL((x1, y1), (x2, y2), **kw)


def R(x, y, w, h, tag='c', **kw):
    """Rectangle (x, y, width, height); every corner carries `tag` (default: container corner)."""
    return PG((x, y, tag), (x + w, y, tag), (x + w, y + h, tag), (x, y + h, tag), **kw)


def C(cx, cy, r, **kw):
    return _prim('circle', cx=float(cx), cy=float(cy), r=float(r), **kw)


def E(cx, cy, rx, ry, rot=0.0, **kw):
    return _prim('ellipse', cx=float(cx), cy=float(cy), rx=float(rx), ry=float(ry), rot=float(rot), **kw)


def D(cx, cy, s=1.0, **kw):
    """Solid dot (round brands: disc · angular brands: square). s scales the default size."""
    return _prim('dot', cx=float(cx), cy=float(cy), s=float(s), **kw)


def A(cx, cy, r, a0, a1, **kw):
    """Open circular arc, angles in degrees (0 = 3 o'clock, 90 = 6 o'clock); a1 > a0 runs clockwise."""
    return _prim('path', segs=[('A', float(cx), float(cy), float(r), float(r), 0.0, float(a0), float(a1), None)], closed=False, **kw)


def P(*segs, closed=False, **kw):
    """Free path: ('M',x,y[,tag]) ('L',x,y[,tag]) ('Q',cx,cy,x,y[,tag]) ('C',x1,y1,x2,y2,x,y[,tag])
    ('A',cx,cy,r,a0,a1[,tag]) ('EA',cx,cy,rx,ry,a0,a1[,tag]) — arcs start where the pen is (a line is added if not)."""
    out = []
    for s in segs:
        c = s[0]
        if c in ('M', 'L'):
            out.append((c, float(s[1]), float(s[2]), s[3] if len(s) > 3 else None))
        elif c == 'Q':
            out.append(('Q', float(s[1]), float(s[2]), float(s[3]), float(s[4]), s[5] if len(s) > 5 else None))
        elif c == 'C':
            out.append(('C',) + tuple(float(v) for v in s[1:7]) + (s[7] if len(s) > 7 else None,))
        elif c == 'A':
            out.append(('A', float(s[1]), float(s[2]), float(s[3]), float(s[3]), 0.0, float(s[4]), float(s[5]), s[6] if len(s) > 6 else None))
        elif c == 'EA':
            out.append(('A', float(s[1]), float(s[2]), float(s[3]), float(s[4]), 0.0, float(s[5]), float(s[6]), s[7] if len(s) > 7 else None))
        else:
            raise ValueError('unknown segment ' + repr(s))
    return _prim('path', segs=out, closed=closed, **kw)


def FO(p):
    """Fill-only copy of a primitive (duotone tint area, never stroked)."""
    q = copy.deepcopy(p)
    q['stroke'] = False
    q['fill'] = True
    if q['k'] == 'path':
        q['closed'] = True
    return q


def SOLID(p):
    q = copy.deepcopy(p)
    q['solid'] = True
    return q


def T(prims, rot=0.0, dx=0.0, dy=0.0, s=1.0, flipx=False, flipy=False, cx=12.0, cy=12.0):
    """Transform primitives: mirror (about cx/cy), scale s, rotate rot° (clockwise on screen), then translate."""
    if isinstance(prims, dict):
        return T([prims], rot, dx, dy, s, flipx, flipy, cx, cy)[0]
    ca, sa = math.cos(rot * D2R), math.sin(rot * D2R)

    def pt(x, y):
        x, y = x - cx, y - cy
        if flipx: x = -x
        if flipy: y = -y
        x, y = x * s, y * s
        x, y = x * ca - y * sa, x * sa + y * ca
        return x + cx + dx, y + cy + dy

    def ang(a):
        if flipx: a = 180.0 - a
        if flipy: a = -a
        return a

    def phi(f):
        if flipx: f = -f
        if flipy: f = -f
        return f + rot

    out = []
    for p in prims:
        q = copy.deepcopy(p)
        k = q['k']
        if k in ('circle', 'dot'):
            q['cx'], q['cy'] = pt(q['cx'], q['cy'])
            if k == 'circle': q['r'] *= s
        elif k == 'ellipse':
            q['cx'], q['cy'] = pt(q['cx'], q['cy'])
            q['rx'] *= s; q['ry'] *= s
            q['rot'] = phi(q['rot'])
        elif k == 'path':
            segs = []
            for g in q['segs']:
                c = g[0]
                if c in ('M', 'L'):
                    x, y = pt(g[1], g[2]); segs.append((c, x, y, g[3]))
                elif c == 'Q':
                    a = pt(g[1], g[2]); b = pt(g[3], g[4]); segs.append(('Q', a[0], a[1], b[0], b[1], g[5]))
                elif c == 'C':
                    a = pt(g[1], g[2]); b = pt(g[3], g[4]); e = pt(g[5], g[6]); segs.append(('C', a[0], a[1], b[0], b[1], e[0], e[1], g[7]))
                elif c == 'A':
                    o = pt(g[1], g[2]); segs.append(('A', o[0], o[1], g[3] * s, g[4] * s, phi(g[5]), ang(g[6]), ang(g[7]), g[8]))
            q['segs'] = segs
        out.append(q)
    return out


# ---- composite helpers ------------------------------------------------------------------------------
def tangent_pts(cx, cy, r, px, py):
    """Angles (deg) of the two tangent points on circle (cx,cy,r) seen from point P: (left/ccw, right/cw)."""
    dx, dy = px - cx, py - cy
    d = math.hypot(dx, dy)
    base = math.degrees(math.atan2(dy, dx))
    off = math.degrees(math.acos(min(1.0, r / d)))
    return base + off, base - off


def pin(cx, cy, r, tip, tag='m', **kw):
    """Map-pin outline: circle (cx,cy,r) with a point at (cx, tip) below it."""
    a_left, a_right = tangent_pts(cx, cy, r, cx, tip)
    return P(('M', cx, tip, tag), ('L', cx + r * math.cos(a_left * D2R), cy + r * math.sin(a_left * D2R)),
             ('A', cx, cy, r, a_left, a_right + 360), closed=True, **kw)


def drop(cx, cy, r, tip, tag='m', **kw):
    """Drop: circle (cx,cy,r) with a point at (cx, tip) above it."""
    off = math.degrees(math.acos(min(1.0, r / abs(cy - tip))))
    a0, a1 = -90 + off, 270 - off
    return P(('M', cx, tip, tag), ('L', cx + r * math.cos(a0 * D2R), cy + r * math.sin(a0 * D2R)),
             ('A', cx, cy, r, a0, a1), closed=True, **kw)


def heart(cx=12.0, top=4.5, w=17.0, tip=20.0, tag='m', **kw):
    """Heart from two tangent lobes and a point."""
    r = w / 4.0
    lc, rc = (cx - r, top + r), (cx + r, top + r)
    al, _ = tangent_pts(lc[0], lc[1], r, cx, tip)
    _, ar = tangent_pts(rc[0], rc[1], r, cx, tip)
    pl = (lc[0] + r * math.cos(al * D2R), lc[1] + r * math.sin(al * D2R))
    return P(('M', cx, tip, tag), ('L', pl[0], pl[1]), ('A', lc[0], lc[1], r, al, 360), ('A', rc[0], rc[1], r, 180, 360 + ar),
             closed=True, **kw)


def star_pts(cx, cy, ro, ri, n=5, rot=-90.0, tag='m'):
    pts = []
    for i in range(2 * n):
        r = ro if i % 2 == 0 else ri
        a = (rot + i * 180.0 / n) * D2R
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a), tag))
    return pts


def reg_pts(cx, cy, r, n, rot=-90.0, tag='m'):
    return [(cx + r * math.cos((rot + i * 360.0 / n) * D2R), cy + r * math.sin((rot + i * 360.0 / n) * D2R), tag) for i in range(n)]


def gear(cx, cy, ro, ri, n=8, tw=3.0, rot=-90.0, **kw):
    """Gear outline: n parallel-sided teeth of width tw, roots on circle ri (arcs)."""
    segs = []
    step = 360.0 / n
    ro = math.hypot(ro, tw / 2)              # ro is given as the distance to the flat tooth top (keeps tops on the grid)
    a_out = math.degrees(math.asin((tw / 2) / ro))
    a_in = math.degrees(math.asin((tw / 2) / ri))
    for k in range(n):
        th = rot + k * step
        p1 = (cx + ri * math.cos((th - a_in) * D2R), cy + ri * math.sin((th - a_in) * D2R))
        p2 = (cx + ro * math.cos((th - a_out) * D2R), cy + ro * math.sin((th - a_out) * D2R))
        p3 = (cx + ro * math.cos((th + a_out) * D2R), cy + ro * math.sin((th + a_out) * D2R))
        p4 = (cx + ri * math.cos((th + a_in) * D2R), cy + ri * math.sin((th + a_in) * D2R))
        segs.append(('M' if k == 0 else 'L', p1[0], p1[1]))
        segs.append(('L', p2[0], p2[1], 'm'))
        segs.append(('L', p3[0], p3[1], 'm'))
        segs.append(('L', p4[0], p4[1]))
        segs.append(('A', cx, cy, ri, th + a_in, th + step - a_in))
    return P(*segs, closed=True, **kw)


def capsule(cx, cy, length, width, deg=0.0, **kw):
    """Stadium (pill) of total length/width with its axis at `deg`."""
    r = width / 2.0
    h = max(0.0, length / 2.0 - r)
    ux, uy = math.cos(deg * D2R), math.sin(deg * D2R)
    c1 = (cx - ux * h, cy - uy * h); c2 = (cx + ux * h, cy + uy * h)
    an = deg - 90.0
    s = (c1[0] + r * math.cos(an * D2R), c1[1] + r * math.sin(an * D2R))
    e = (c2[0] + r * math.cos(an * D2R), c2[1] + r * math.sin(an * D2R))
    return P(('M', s[0], s[1]), ('L', e[0], e[1]), ('A', c2[0], c2[1], r, an, an + 180),
             ('L', c1[0] + r * math.cos((an + 180) * D2R), c1[1] + r * math.sin((an + 180) * D2R)),
             ('A', c1[0], c1[1], r, an + 180, an + 360), closed=True, **kw)


def link(c1, c2, r1, r2, gap=0.0):
    """Line between two circles, trimmed by their radii (+gap)."""
    dx, dy = c2[0] - c1[0], c2[1] - c1[1]
    d = math.hypot(dx, dy); ux, uy = dx / d, dy / d
    return L(c1[0] + ux * (r1 + gap), c1[1] + uy * (r1 + gap), c2[0] - ux * (r2 + gap), c2[1] - uy * (r2 + gap))


def arrowhead(tx, ty, deg, size=3.5, spread=45.0):
    """Open arrowhead with its tip at (tx,ty) pointing along `deg`."""
    a1, a2 = (deg + 180 - spread) * D2R, (deg + 180 + spread) * D2R
    return PL((tx + size * math.cos(a1), ty + size * math.sin(a1)), (tx, ty, 'x'), (tx + size * math.cos(a2), ty + size * math.sin(a2)))


def arc_arrow(cx, cy, r, a0, a1, size=3.5):
    """Arc with an arrowhead at its end (direction follows the sweep)."""
    end = (cx + r * math.cos(a1 * D2R), cy + r * math.sin(a1 * D2R))
    tang = a1 + (90 if a1 > a0 else -90)
    return [A(cx, cy, r, a0, a1), arrowhead(end[0], end[1], tang, size)]


def chain(circles, start_deg, end_deg, upper=True):
    """Arc segments along the outline of overlapping circles [(cx,cy,r)…] taken left→right over the top."""
    segs = []
    prev = start_deg
    for i in range(len(circles)):
        cx, cy, r = circles[i]
        if i < len(circles) - 1:
            dx2, dy2, r2 = circles[i + 1]
            # intersection of circle i and i+1 (upper one)
            d = math.hypot(dx2 - cx, dy2 - cy)
            a = (r * r - r2 * r2 + d * d) / (2 * d)
            h = math.sqrt(max(0.0, r * r - a * a))
            mx, my = cx + a * (dx2 - cx) / d, cy + a * (dy2 - cy) / d
            p1 = (mx + h * (dy2 - cy) / d, my - h * (dx2 - cx) / d)
            p2 = (mx - h * (dy2 - cy) / d, my + h * (dx2 - cx) / d)
            ip = p1 if (p1[1] < p2[1]) == upper else p2
            ang = math.degrees(math.atan2(ip[1] - cy, ip[0] - cx))
            while ang < prev: ang += 360
            segs.append(('A', cx, cy, r, prev, ang))
            nxt = math.degrees(math.atan2(ip[1] - dy2, ip[0] - dx2))
            prev = nxt
        else:
            e = end_deg
            while e < prev: e += 360
            segs.append(('A', cx, cy, r, prev, e))
    return segs


def wave(x0, x1, y, periods=2, amp=1.5):
    """Wavy line (quadratic segments)."""
    n = int(periods * 2)
    w = (x1 - x0) / n
    segs = [('M', x0, y)]
    for i in range(n):
        xa = x0 + i * w
        segs.append(('Q', xa + w / 2, y + (-amp if i % 2 == 0 else amp) * 2, xa + w, y))
    return P(*segs)


def bumps(x0, x1, y, n, up=True):
    """Scalloped edge of n semicircles between x0 and x1 on line y (up = bulging upwards)."""
    w = (x1 - x0) / n; r = w / 2
    segs = [('M', x0, y)]
    for i in range(n):
        c = x0 + w * i + r
        segs.append(('A', c, y, r, 180, 360) if up else ('A', c, y, r, 180, 0))
    return segs


# =====================================================================================================
# 2. STYLE (from the design DNA)
# =====================================================================================================
def _px(v, d=8.0):
    try:
        return float(str(v).replace('px', '').strip())
    except Exception:
        return d


class Style:
    def __init__(self, dna):
        dna = dna or {}
        st = dna.get('stroke') or {}
        self.sw = float(st.get('icon_px_at_24') or 1.75)
        self.cap = {'square': 'square', 'butt': 'butt', 'round': 'round'}.get(st.get('cap'), 'round')
        self.join = {'miter': 'miter', 'mitre': 'miter', 'round': 'round', 'bevel': 'bevel'}.get(st.get('join'), 'round')
        base = dna.get('base_language') or dna.get('geometry') or 'mixed'
        cs = ((dna.get('corner') or {}).get('style') or '').lower()
        cs = {'rounded': 'round', 'pill': 'round', 'chamfer': 'cut', 'sharp': 'square'}.get(cs, cs)
        if cs not in ('cut', 'square', 'round', 'soft'):
            cs = 'round' if base in ('round', 'organic') else ('cut' if base == 'angular' else 'square')
        self.corner = cs
        self.base = base
        self.organic = base == 'organic'
        pats = set(dna.get('patterns') or []) | set(dna.get('motifs') or [])
        self.faceted = dna.get('complexity') == 'faceted' or 'facets' in pats or 'facet-field' in pats
        ang = dna.get('angles') or {}
        self.cut_angle = float(ang.get('cut') or (dna.get('corner') or {}).get('angle_deg') or 45)
        md = _px(((dna.get('tokens') or {}).get('radius') or {}).get('md', '8px'))
        self.radius = max(1.5, min(3.25, md / 5.0))
        self.radius_soft = max(2.75, min(4.25, md / 4.0))
        self.cut = 3.6
        self.dot_round = self.corner in ('round', 'soft') or self.organic
        self.miter_limit = 3

    def describe(self):
        caps = {'square': 'square caps', 'butt': 'flat caps', 'round': 'round caps'}[self.cap]
        joins = {'miter': 'mitred joins', 'round': 'round joins', 'bevel': 'bevelled joins'}[self.join]
        corner = {'cut': '%g° chamfer on the bottom-right container corner' % self.cut_angle,
                  'organic': 'soft corners, one pebble-round bottom-right corner (r %s / %s)' % (fmt(self.radius_soft), fmt(self.radius_soft * 1.65)),
                  'round': 'rounded container corners (r %s)' % fmt(self.radius),
                  'soft': 'soft container corners (r %s)' % fmt(self.radius_soft),
                  'square': 'sharp container corners'}['organic' if self.organic else self.corner]
        curves = ('faceted curves — arcs and circles become facets' if self.faceted else
                  'eased joints — every vertex softened' if self.organic else 'true arcs')
        return {'stroke': fmt(self.sw), 'caps': caps, 'joins': joins, 'corners': corner, 'curves': curves}


# =====================================================================================================
# 3. RENDERER
# =====================================================================================================
def fmt(v, nd=2):
    s = ('%.*f' % (nd, v)).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '', '-') else s


def _ell_pt(cx, cy, rx, ry, phi, a):
    ca, sa = math.cos(a * D2R), math.sin(a * D2R)
    cp, sp = math.cos(phi * D2R), math.sin(phi * D2R)
    return (cx + rx * ca * cp - ry * sa * sp, cy + rx * ca * sp + ry * sa * cp)


def _facet_angles(a0, a1, phase=22.5, step=45.0):
    """Intermediate polygon vertex angles strictly between a0 and a1 (in sweep order)."""
    out = []
    if a1 > a0:
        k = math.floor((a0 - phase) / step) + 1
        while phase + k * step < a1 - 1e-6:
            v = phase + k * step
            if v > a0 + 1e-6: out.append(v)
            k += 1
    else:
        k = math.ceil((a0 - phase) / step) - 1
        while phase + k * step > a1 + 1e-6:
            v = phase + k * step
            if v < a0 - 1e-6: out.append(v)
            k -= 1
    return out


def _bez(p0, c1, c2, p3, t):
    u = 1 - t
    return (u ** 3 * p0[0] + 3 * u * u * t * c1[0] + 3 * u * t * t * c2[0] + t ** 3 * p3[0],
            u ** 3 * p0[1] + 3 * u * u * t * c1[1] + 3 * u * t * t * c2[1] + t ** 3 * p3[1])


def _q2c(p0, q, p1):
    return ((p0[0] + 2 * (q[0] - p0[0]) / 3, p0[1] + 2 * (q[1] - p0[1]) / 3), (p1[0] + 2 * (q[0] - p1[0]) / 3, p1[1] + 2 * (q[1] - p1[1]) / 3))


def _edges(prim):
    """Path primitive → subpaths [{'edges': [...], 'closed': bool, 'start_tag': tag}] with explicit start points."""
    subs = []
    cur = None; pen = None
    def new(pt, tag):
        nonlocal cur
        cur = {'edges': [], 'closed': False, 'start': pt, 'start_tag': tag}
        subs.append(cur)
    for g in prim['segs']:
        c = g[0]
        if c == 'M':
            new((g[1], g[2]), g[3]); pen = (g[1], g[2]); continue
        if c == 'A':
            cx, cy, rx, ry, phi, a0, a1, tag = g[1:]
            s = _ell_pt(cx, cy, rx, ry, phi, a0); e = _ell_pt(cx, cy, rx, ry, phi, a1)
            if cur is None:
                new(s, None); pen = s
            elif math.hypot(s[0] - pen[0], s[1] - pen[1]) > 0.02:
                cur['edges'].append({'t': 'L', 'a': pen, 'b': s, 'tag': None})
            cur['edges'].append({'t': 'A', 'a': s, 'b': e, 'arc': (cx, cy, rx, ry, phi, a0, a1), 'tag': tag})
            pen = e
            continue
        if cur is None:
            raise ValueError('path must start with M or A')
        if c == 'L':
            b = (g[1], g[2])
            if math.hypot(b[0] - pen[0], b[1] - pen[1]) < 1e-6: continue
            cur['edges'].append({'t': 'L', 'a': pen, 'b': b, 'tag': g[3]}); pen = b
        elif c == 'Q':
            b = (g[3], g[4]); c1, c2 = _q2c(pen, (g[1], g[2]), b)
            cur['edges'].append({'t': 'C', 'a': pen, 'b': b, 'c1': c1, 'c2': c2, 'tag': g[5], 'q': (g[1], g[2])}); pen = b
        elif c == 'C':
            b = (g[5], g[6])
            cur['edges'].append({'t': 'C', 'a': pen, 'b': b, 'c1': (g[1], g[2]), 'c2': (g[3], g[4]), 'tag': g[7]}); pen = b
    if prim.get('closed') and subs:
        for s in subs:
            if not s['edges']: continue
            last = s['edges'][-1]['b']; st = s['start']
            if math.hypot(last[0] - st[0], last[1] - st[1]) > 0.02:
                s['edges'].append({'t': 'L', 'a': last, 'b': st, 'tag': s['start_tag']})
            else:
                s['edges'][-1]['tag'] = s['start_tag'] if s['start_tag'] is not None else s['edges'][-1]['tag']
            s['closed'] = True
    return subs


def _facetize(sub, style):
    out = []
    for e in sub['edges']:
        if e['t'] == 'A':
            cx, cy, rx, ry, phi, a0, a1 = e['arc']
            pts = [_ell_pt(cx, cy, rx, ry, phi, a) for a in _facet_angles(a0, a1)]
            # keep facets crisp: scale vertices out a touch so the polygon reads at the arc's size
            k = 1.0 / math.cos(22.5 * D2R) * 0.97
            pts = [(cx + (x - cx) * k, cy + (y - cy) * k) for x, y in pts]
            seq = [e['a']] + pts + [e['b']]
            for i in range(len(seq) - 1):
                out.append({'t': 'L', 'a': seq[i], 'b': seq[i + 1], 'tag': (e['tag'] if i == len(seq) - 2 else 'f'), 'fac': True})
        elif e['t'] == 'C':
            chord = math.hypot(e['b'][0] - e['a'][0], e['b'][1] - e['a'][1])
            n = 3 if chord > 9 else 2
            seq = [e['a']] + [_bez(e['a'], e['c1'], e['c2'], e['b'], i / n) for i in range(1, n)] + [e['b']]
            for i in range(len(seq) - 1):
                out.append({'t': 'L', 'a': seq[i], 'b': seq[i + 1], 'tag': (e['tag'] if i == len(seq) - 2 else 'f'), 'fac': True})
        else:
            out.append(e)
    sub['edges'] = out
    return sub


def _unit(v):
    d = math.hypot(v[0], v[1])
    return (v[0] / d, v[1] / d) if d > 1e-9 else (0.0, 0.0)


def _treatment(tag, style, is_brand):
    org = style.organic
    cs = style.corner
    if tag == 'x' or tag == 'f':
        return None
    if tag == 'c':
        if org: return ('fillet', style.radius_soft * (1.65 if is_brand else 1.0))
        if cs == 'cut': return ('chamfer', style.cut, True) if is_brand else None
        if cs == 'round': return ('fillet', style.radius)
        if cs == 'soft': return ('fillet', style.radius_soft)
        return None
    if isinstance(tag, str) and tag.startswith('s'):
        n = float(tag[1:] or 2)
        if org: return ('fillet', n * 1.2)
        if cs == 'cut': return ('chamfer', n * 0.85, False)
        if cs == 'round': return ('fillet', n)
        if cs == 'soft': return ('fillet', n * 1.15)
        return None
    if tag == 'm':
        if org or cs == 'soft': return ('fillet', 1.5)
        if cs == 'round': return ('fillet', 0.9)
        return None
    if tag is None and org:
        return ('fillet', 1.0)
    return None


def _snap(sub, q=0.25, tol=0.02):
    """Pixel snap: horizontal/vertical straight edges get their fixed coordinate on the q grid (also after rotations
    and scaling). Only vertices between two straight edges (or free path ends) move, by at most q/2."""
    E_ = sub['edges']; n = len(E_)
    if not n: return sub
    closed = sub['closed']
    m = n if closed else n + 1                       # number of distinct vertices
    pts = [list(E_[i]['a']) for i in range(n)] + ([] if closed else [list(E_[-1]['b'])])
    vi = lambda i: i % m                              # vertex index of edge i's start; end = vi(i + 1)
    free = [True] * m
    for i, e in enumerate(E_):
        if e['t'] != 'L': free[vi(i)] = free[vi(i + 1)] = False
    for i, e in enumerate(E_):
        if e['t'] != 'L': continue
        a, b = pts[vi(i)], pts[vi(i + 1)]
        if not (free[vi(i)] and free[vi(i + 1)]): continue
        if abs(a[1] - b[1]) < tol and abs(a[0] - b[0]) > 0.5:
            a[1] = b[1] = round((a[1] + b[1]) / 2 / q) * q
        elif abs(a[0] - b[0]) < tol and abs(a[1] - b[1]) > 0.5:
            a[0] = b[0] = round((a[0] + b[0]) / 2 / q) * q
    for i, e in enumerate(E_):
        e['a'] = tuple(pts[vi(i)]); e['b'] = tuple(pts[vi(i + 1)])
    return sub


def _render_path(prim, style):
    subs = _edges(prim)
    if style.faceted:
        subs = [_facetize(s, style) for s in subs]
    subs = [_snap(s) for s in subs]
    d_parts = []; flat = []; straight = []
    for s in subs:
        E_ = s['edges']
        if not E_: continue
        n = len(E_)
        closed = s['closed']
        straight.extend((e['a'], e['b']) for e in E_ if e['t'] == 'L' and not e.get('fac'))
        # vertices: index i = between edge i-1 and edge i (vertex at E_[i]['a'])
        verts = list(range(n)) if closed else list(range(1, n))
        # brand corner: the bottom-right-most 'c' vertex that really is a bottom-right corner (one neighbour to the left,
        # one above) between two straight edges — cut brands chamfer it (like .p-shape), organic brands give it a pebble radius
        brand = None
        if style.corner == 'cut' or style.organic:
            best = None
            for i in verts:
                e_in, e_out = E_[i - 1], E_[i]
                if e_in['tag'] != 'c' or e_in['t'] != 'L' or e_out['t'] != 'L': continue
                v = e_out['a']
                d1 = (e_in['a'][0] - v[0], e_in['a'][1] - v[1]); d2 = (e_out['b'][0] - v[0], e_out['b'][1] - v[1])
                left = lambda d: d[0] < 0 and abs(d[0]) >= abs(d[1]) * 1.2
                up = lambda d: d[1] < 0 and abs(d[1]) >= abs(d[0]) * 1.2
                if not ((left(d1) and up(d2)) or (left(d2) and up(d1))): continue
                key = (round(v[0] + v[1], 3), round(v[0], 3))
                if best is None or key > best[0]: best = (key, i)
            brand = best[1] if best else None
        # desired treatments
        want = {}
        for i in verts:
            e_in, e_out = E_[i - 1], E_[i]
            if e_in['t'] != 'L' or e_out['t'] != 'L': continue
            tr = _treatment(e_in['tag'], style, i == brand)
            if not tr: continue
            v = e_out['a']
            u = _unit((e_in['a'][0] - v[0], e_in['a'][1] - v[1])); w = _unit((e_out['b'][0] - v[0], e_out['b'][1] - v[1]))
            cos = max(-1.0, min(1.0, u[0] * w[0] + u[1] * w[1])); th = math.acos(cos)
            if math.degrees(th) > 176 or math.degrees(th) < 12: continue
            if tr[0] == 'fillet':
                t = tr[1] / math.tan(th / 2)
                want[i] = ['fillet', t, t, th, u, w]
            else:
                size = tr[1]
                len_in = math.hypot(e_in['b'][0] - e_in['a'][0], e_in['b'][1] - e_in['a'][1]); len_out = math.hypot(e_out['b'][0] - e_out['a'][0], e_out['b'][1] - e_out['a'][1])
                size = min(size, 0.5 * min(len_in, len_out))
                horiz_u = abs(u[1]) < 1e-6; vert_u = abs(u[0]) < 1e-6
                horiz_w = abs(w[1]) < 1e-6; vert_w = abs(w[0]) < 1e-6
                ca = style.cut_angle * D2R
                if abs(math.degrees(th) - 90) < 1 and ((horiz_u and vert_w) or (vert_u and horiz_w)):
                    lh, lv = size * math.cos(ca), size * math.sin(ca)
                    a_in, a_out = (lh, lv) if horiz_u else (lv, lh)
                else:
                    a_in = a_out = size * 0.62
                want[i] = ['chamfer', a_in, a_out, th, u, w]
        # fit into the available edge lengths
        def elen(e): return math.hypot(e['b'][0] - e['a'][0], e['b'][1] - e['a'][1])
        for i in list(want):
            e_in, e_out = E_[i - 1], E_[i]
            j_in = i - 1 if (closed or i - 1 >= 1) else None   # vertex at the start of e_in
            j_out = (i + 1) % n if closed else (i + 1 if i + 1 < n else None)
            av_in = elen(e_in) * (0.5 if (j_in is not None and (j_in % n) in want) else 0.9)
            av_out = elen(e_out) * (0.5 if (j_out is not None and j_out in want) else 0.9)
            w_ = want[i]
            f = min(1.0, av_in / w_[1] if w_[1] > 0 else 1, av_out / w_[2] if w_[2] > 0 else 1)
            w_[1] *= f; w_[2] *= f
        # emit
        def trimmed(i):
            e = E_[i]
            a, b = e['a'], e['b']
            if e['t'] == 'L':
                ln = elen(e); ux, uy = (b[0] - a[0]) / ln, (b[1] - a[1]) / ln
                ts = want[i][2] if i in want else 0.0
                te = want[(i + 1) % n][1] if ((i + 1) % n in want and (closed or i + 1 < n)) else 0.0
                return (a[0] + ux * ts, a[1] + uy * ts), (b[0] - ux * te, b[1] - uy * te)
            return a, b
        cmds = []; pts = []
        a0, _ = trimmed(0)
        cmds.append('M%s %s' % (fmt(a0[0]), fmt(a0[1]))); pts.append([a0])
        for i in range(n):
            e = E_[i]
            sa, sb = trimmed(i)
            if e['t'] == 'L':
                cmds.append('L%s %s' % (fmt(sb[0]), fmt(sb[1]))); pts[-1].append(sb)
            elif e['t'] == 'C':
                if 'q' in e:
                    cmds.append('Q%s %s %s %s' % (fmt(e['q'][0]), fmt(e['q'][1]), fmt(sb[0]), fmt(sb[1])))
                else:
                    cmds.append('C%s %s %s %s %s %s' % (fmt(e['c1'][0]), fmt(e['c1'][1]), fmt(e['c2'][0]), fmt(e['c2'][1]), fmt(sb[0]), fmt(sb[1])))
                for k in range(1, 13): pts[-1].append(_bez(e['a'], e['c1'], e['c2'], e['b'], k / 12))
            else:
                cx, cy, rx, ry, phi, a_0, a_1 = e['arc']
                sweep = 1 if a_1 > a_0 else 0
                span = abs(a_1 - a_0)
                if span >= 359.9:
                    mid = (a_0 + a_1) / 2; mp = _ell_pt(cx, cy, rx, ry, phi, mid)
                    cmds.append('A%s %s %s 0 %d %s %s' % (fmt(rx), fmt(ry), fmt(phi), sweep, fmt(mp[0]), fmt(mp[1])))
                    span = span / 2
                large = 1 if span > 180 else 0
                cmds.append('A%s %s %s %d %d %s %s' % (fmt(rx), fmt(ry), fmt(phi), large, sweep, fmt(sb[0]), fmt(sb[1])))
                steps = max(4, int(abs(a_1 - a_0) / 6))
                for k in range(1, steps + 1): pts[-1].append(_ell_pt(cx, cy, rx, ry, phi, a_0 + (a_1 - a_0) * k / steps))
            # vertex treatment at the end of edge i
            j = (i + 1) % n
            if j in want and (closed or i + 1 < n):
                kind, t_in, t_out, th, u, w = want[j]
                nxt, _ = trimmed(j)
                if kind == 'chamfer':
                    cmds.append('L%s %s' % (fmt(nxt[0]), fmt(nxt[1]))); pts[-1].append(nxt)
                else:
                    r = t_in * math.tan(th / 2)
                    din = (-u[0], -u[1]); dout = w
                    cross = din[0] * dout[1] - din[1] * dout[0]
                    cmds.append('A%s %s 0 0 %d %s %s' % (fmt(r), fmt(r), 1 if cross > 0 else 0, fmt(nxt[0]), fmt(nxt[1])))
                    # flatten fillet
                    v = E_[j]['a']; p1 = sb; p2 = nxt
                    for k in range(1, 5):
                        tt = k / 5.0
                        q = ((1 - tt) ** 2 * p1[0] + 2 * (1 - tt) * tt * v[0] + tt * tt * p2[0], (1 - tt) ** 2 * p1[1] + 2 * (1 - tt) * tt * v[1] + tt * tt * p2[1])
                        pts[-1].append(q)
        if closed: cmds.append('Z')
        d_parts.append(''.join(cmds))
        flat.append((pts[-1], closed))
    return ''.join(d_parts), flat, straight


def _circle_poly(cx, cy, rx, ry, rot=0.0):
    k = 1.0 / math.cos(22.5 * D2R) * 0.97
    return [_ell_pt(cx, cy, rx * k, ry * k, rot, 22.5 + 45 * i) for i in range(8)]


def _poly_d(pts):
    return 'M' + 'L'.join('%s %s' % (fmt(x), fmt(y)) for x, y in pts) + 'Z'


def resolve_fill(prims):
    """Which primitives form the duotone tint: explicit fill=True, else the first closed stroked shape."""
    exp = [p for p in prims if p.get('fill') is True]
    if exp: return exp
    for p in prims:
        if p.get('fill') is False or not p.get('stroke', True): continue
        if p['k'] in ('circle', 'ellipse') or (p['k'] == 'path' and p.get('closed')):
            return [p]
    return []


def render(prims, style):
    """→ {'outline': inner SVG, 'tint': inner SVG of the tint layer ('' if none), 'geo': [(kind, data)] for QA}."""
    out = []; tint = []; geo = []
    fills = [id(p) for p in resolve_fill(prims)]
    for p in prims:
        k = p['k']
        if k == 'dot':
            r = style.sw * 0.66 * p['s']
            if style.dot_round:
                el = '<circle cx="%s" cy="%s" r="%s" fill="currentColor" stroke="none"/>' % (fmt(p['cx']), fmt(p['cy']), fmt(r))
                geo.append(('disc', (p['cx'], p['cy'], r)))
            else:
                a = r * 0.9
                el = '<rect x="%s" y="%s" width="%s" height="%s" fill="currentColor" stroke="none"/>' % (fmt(p['cx'] - a), fmt(p['cy'] - a), fmt(2 * a), fmt(2 * a))
                geo.append(('poly', [(p['cx'] - a, p['cy'] - a), (p['cx'] + a, p['cy'] - a), (p['cx'] + a, p['cy'] + a), (p['cx'] - a, p['cy'] + a)]))
            out.append(el)
            continue
        if k == 'circle':
            if style.faceted:
                pts = _circle_poly(p['cx'], p['cy'], p['r'], p['r'])
                d = _poly_d(pts); flat = [(pts, True)]
                el = '<path d="%s"/>' % d
            else:
                d = None; flat = [([(p['cx'] + p['r'] * math.cos(a * D2R), p['cy'] + p['r'] * math.sin(a * D2R)) for a in range(0, 360, 6)], True)]
                el = '<circle cx="%s" cy="%s" r="%s"/>' % (fmt(p['cx']), fmt(p['cy']), fmt(p['r']))
        elif k == 'ellipse':
            cx, cy, rx, ry, rot = p['cx'], p['cy'], p['rx'], p['ry'], p['rot']
            if style.faceted:
                pts = _circle_poly(cx, cy, rx, ry, rot); flat = [(pts, True)]
                d = _poly_d(pts)
            else:
                s0 = _ell_pt(cx, cy, rx, ry, rot, 0); s1 = _ell_pt(cx, cy, rx, ry, rot, 180)
                d = 'M%s %sA%s %s %s 1 1 %s %sA%s %s %s 1 1 %s %sZ' % (fmt(s0[0]), fmt(s0[1]), fmt(rx), fmt(ry), fmt(rot), fmt(s1[0]), fmt(s1[1]), fmt(rx), fmt(ry), fmt(rot), fmt(s0[0]), fmt(s0[1]))
                flat = [([_ell_pt(cx, cy, rx, ry, rot, a) for a in range(0, 360, 6)], True)]
            el = '<path d="%s"/>' % d
        else:
            d, flat, straight = _render_path(p, style)
            if p.get('stroke', True): geo.append(('lines', straight))
            el = '<path d="%s"/>' % d
        if p.get('solid'):
            el = el.replace('/>', ' fill="currentColor"/>')
        if p.get('stroke', True):
            out.append(el)
            for pts, closed in flat: geo.append(('stroke', (pts, closed)))
            if p.get('solid'):
                for pts, closed in flat: geo.append(('poly', pts))
        if id(p) in fills or (not p.get('stroke', True) and p.get('fill')):
            if k == 'circle' and not style.faceted:
                tint.append('<circle cx="%s" cy="%s" r="%s"/>' % (fmt(p['cx']), fmt(p['cy']), fmt(p['r'])))
            else:
                tint.append('<path d="%s"/>' % (d if d else ''))
    return {'outline': ''.join(out), 'tint': ''.join(tint), 'geo': geo}


# =====================================================================================================
# 4. QA (ink bounds + visual weight)
# =====================================================================================================
def ink(geo, style):
    try:
        from shapely.geometry import LineString, LinearRing, Polygon, Point
        from shapely.ops import unary_union
    except Exception:
        return None
    cap = {'round': 'round', 'square': 'square', 'butt': 'flat'}[style.cap]
    join = {'round': 'round', 'miter': 'mitre', 'bevel': 'bevel'}[style.join]
    parts = []
    for kind, data in geo:
        if kind == 'lines': continue
        try:
            if kind == 'stroke':
                pts, closed = data
                pts = [(round(x, 4), round(y, 4)) for x, y in pts]
                ded = [pts[0]] + [q for i, q in enumerate(pts[1:]) if q != pts[i]]
                if len(ded) < 2: continue
                if closed and len(ded) >= 3:
                    g = LinearRing(ded).buffer(style.sw / 2, join_style=join, mitre_limit=1.5)
                else:
                    g = LineString(ded).buffer(style.sw / 2, cap_style=cap, join_style=join, mitre_limit=1.5)
            elif kind == 'disc':
                g = Point(data[0], data[1]).buffer(data[2])
            else:
                g = Polygon(data).buffer(0)
            parts.append(g)
        except Exception:
            continue
    if not parts: return None
    u = unary_union(parts)
    return {'bounds': [round(v, 2) for v in u.bounds], 'area': round(u.area, 2)}


# =====================================================================================================
# 5. JSON definitions (brand-local extra icons: SOURCE/CONFIG/icons-custom.json)
# =====================================================================================================
def from_json(spec):
    """[['L',x1,y1,x2,y2], ['PL',[x,y],[x,y,'c'],…], ['PG',…], ['R',x,y,w,h,tag?], ['C',cx,cy,r], ['E',cx,cy,rx,ry,rot?],
    ['A',cx,cy,r,a0,a1], ['D',cx,cy,s?], ['P',['M',x,y],['L',x,y,tag?],['Q',…],['C',…],['A',…]]] — a trailing dict
    holds options: {"fill": true|false, "closed": true, "solid": true, "fillOnly": true}."""
    out = []
    for item in spec:
        kind, args = item[0], list(item[1:])
        opts = args.pop() if args and isinstance(args[-1], dict) else {}
        kw = {k: opts[k] for k in ('fill',) if k in opts}
        if kind == 'L': p = L(*args, **kw)
        elif kind == 'PL': p = PL(*[tuple(a) for a in args], **kw)
        elif kind == 'PG': p = PG(*[tuple(a) for a in args], **kw)
        elif kind == 'R': p = R(*args, **kw)
        elif kind == 'C': p = C(*args, **kw)
        elif kind == 'E': p = E(*args, **kw)
        elif kind == 'A': p = A(*args, **kw)
        elif kind == 'D': p = D(*args)
        elif kind == 'P': p = P(*[tuple(a) for a in args], closed=bool(opts.get('closed')), **kw)
        else: raise ValueError('unknown primitive %r' % kind)
        if opts.get('solid'): p = SOLID(p)
        if opts.get('fillOnly'): p = FO(p)
        out.append(p)
    return out
