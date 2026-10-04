"""svgkit.py — SVG geometry for the logo-system module (brand-neutral).

Parts are pieces of the logo read from the foundation SVGs (mark, lettering, typeset name lines, compact mark).
Every Part keeps ONE geometry box (measured on its colour version) and several colour versions of its markup
(`inners`), so all colourways of a lockup share exactly the same construction.
Items are Parts placed in lockup units (X = cap height of the name / lettering = 100 units).
"""
import math, re
import xml.etree.ElementTree as ET

NS = '{http://www.w3.org/2000/svg}'


def f2(v):
    s = f'{v:.2f}'.rstrip('0').rstrip('.')
    return '0' if s in ('-0', '', '-') else s


# ------------------------------------------------------------------ colour maths (WCAG)
def hex_rgb(h):
    h = h.strip().lstrip('#')
    if len(h) == 3: h = ''.join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def lum(h):
    def ch(c):
        c /= 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = hex_rgb(h)
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def mix(a, b, t):
    ra, rb = hex_rgb(a), hex_rgb(b)
    return '#' + ''.join(f'{round(x + (y - x) * t):02X}' for x, y in zip(ra, rb))


# ------------------------------------------------------------------ transforms
def _mat_mul(m, n):
    a, b, c, d, e, f = m; A, B, C, D, E, F = n
    return (a * A + c * B, b * A + d * B, a * C + c * D, b * C + d * D, a * E + c * F + e, b * E + d * F + f)


def parse_transform(s):
    m = (1, 0, 0, 1, 0, 0)
    if not s: return m
    for fn, args in re.findall(r'(\w+)\s*\(([^)]*)\)', s):
        v = [float(x) for x in re.findall(r'-?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?', args)]
        if fn == 'translate': n = (1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0)
        elif fn == 'scale': n = (v[0], 0, 0, v[1] if len(v) > 1 else v[0], 0, 0)
        elif fn == 'matrix': n = tuple(v[:6])
        elif fn == 'rotate':
            a = math.radians(v[0]); ca, sa = math.cos(a), math.sin(a)
            n = (ca, sa, -sa, ca, 0, 0)
            if len(v) == 3:
                n = _mat_mul(_mat_mul((1, 0, 0, 1, v[1], v[2]), n), (1, 0, 0, 1, -v[1], -v[2]))
        else: continue
        m = _mat_mul(m, n)
    return m


def _apply(m, x, y):
    a, b, c, d, e, f = m
    return a * x + c * y + e, b * x + d * y + f


# ------------------------------------------------------------------ path extremes
_TOK = re.compile(r'[MLHVCSQTAZmlhvcsqtaz]|-?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?')


def _quad_ext(p0, p1, p2):
    out = [p0, p2]; den = p0 - 2 * p1 + p2
    if abs(den) > 1e-12:
        t = (p0 - p1) / den
        if 0 < t < 1: out.append((1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t * t * p2)
    return out


def _cub_ext(p0, p1, p2, p3):
    out = [p0, p3]
    a = -p0 + 3 * p1 - 3 * p2 + p3; b = 2 * (p0 - 2 * p1 + p2); c = p1 - p0
    ts = []
    if abs(a) < 1e-12:
        if abs(b) > 1e-12: ts = [-c / b]
    else:
        disc = b * b - 4 * a * c
        if disc >= 0:
            r = math.sqrt(disc); ts = [(-b + r) / (2 * a), (-b - r) / (2 * a)]
    for t in ts:
        if 0 < t < 1:
            mt = 1 - t
            out.append(mt ** 3 * p0 + 3 * mt * mt * t * p1 + 3 * mt * t * t * p2 + t ** 3 * p3)
    return out


def path_points(d):
    """Extreme points (x, y) of a path — exact for lines and Béziers, endpoints+radius box for arcs."""
    toks = _TOK.findall(d); i = 0; cmd = None
    x = y = sx = sy = 0.0; px = py = None; pts = []

    def num():
        nonlocal i
        v = float(toks[i]); i += 1; return v
    while i < len(toks):
        t = toks[i]
        if t.isalpha():
            cmd = t; i += 1
            if cmd in 'Zz':
                x, y = sx, sy; px = py = None
                continue
        if cmd is None: break
        rel = cmd.islower(); C = cmd.upper(); ox, oy = (x, y) if rel else (0.0, 0.0)
        if C == 'M':
            x, y = num() + ox, num() + oy; sx, sy = x, y; pts.append((x, y)); cmd = 'l' if rel else 'L'; px = py = None
        elif C == 'L':
            x, y = num() + ox, num() + oy; pts.append((x, y)); px = py = None
        elif C == 'H':
            x = num() + ox; pts.append((x, y)); px = py = None
        elif C == 'V':
            y = num() + oy; pts.append((x, y)); px = py = None
        elif C in 'CS':
            if C == 'C': x1, y1 = num() + ox, num() + oy
            else: x1, y1 = (2 * x - px, 2 * y - py) if px is not None else (x, y)
            x2, y2, x3, y3 = num() + ox, num() + oy, num() + ox, num() + oy
            xs = _cub_ext(x, x1, x2, x3); ys = _cub_ext(y, y1, y2, y3)
            pts += [(xx, y3) for xx in xs] + [(x3, yy) for yy in ys]
            px, py = x2, y2; x, y = x3, y3
        elif C in 'QT':
            if C == 'Q': x1, y1 = num() + ox, num() + oy
            else: x1, y1 = (2 * x - px, 2 * y - py) if px is not None else (x, y)
            x2, y2 = num() + ox, num() + oy
            xs = _quad_ext(x, x1, x2); ys = _quad_ext(y, y1, y2)
            pts += [(xx, y2) for xx in xs] + [(x2, yy) for yy in ys]
            px, py = x1, y1; x, y = x2, y2
        elif C == 'A':
            rx, ry = abs(num()), abs(num()); num(); num(); num()
            x2, y2 = num() + ox, num() + oy
            cx, cy = (x + x2) / 2, (y + y2) / 2
            pts += [(x, y), (x2, y2), (cx - rx, cy - ry), (cx + rx, cy + ry)]
            x, y = x2, y2; px = py = None
        else:
            i += 1
    return pts


def _elem_points(el):
    tag = el.tag.replace(NS, '')
    if tag == 'path': return path_points(el.get('d', ''))
    if tag in ('polygon', 'polyline'):
        v = [float(n) for n in re.findall(r'-?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?', el.get('points', ''))]
        return list(zip(v[0::2], v[1::2]))
    if tag == 'rect':
        x, y = float(el.get('x', 0)), float(el.get('y', 0)); w, h = float(el.get('width', 0)), float(el.get('height', 0))
        return [(x, y), (x + w, y + h)]
    if tag in ('circle', 'ellipse'):
        cx, cy = float(el.get('cx', 0)), float(el.get('cy', 0))
        rx = float(el.get('r', el.get('rx', 0))); ry = float(el.get('r', el.get('ry', 0)))
        return [(cx - rx, cy - ry), (cx + rx, cy + ry)]
    return []


SKIP = {'defs', 'mask', 'clipPath', 'title', 'desc', 'style', 'pattern', 'filter', 'linearGradient', 'radialGradient'}


def element_boxes(svg_text):
    """[(x0, y0, x1, y1)] of every drawn element (outside defs/masks), transforms applied."""
    root = ET.fromstring(svg_text)
    out = []

    def walk(el, m):
        tag = el.tag.replace(NS, '')
        if tag in SKIP: return
        m2 = _mat_mul(m, parse_transform(el.get('transform')))
        pts = _elem_points(el)
        if pts:
            tp = [_apply(m2, x, y) for x, y in pts]
            xs = [p[0] for p in tp]; ys = [p[1] for p in tp]
            out.append((min(xs), min(ys), max(xs), max(ys)))
        for ch in el: walk(ch, m2)
    walk(root, (1, 0, 0, 1, 0, 0))
    return out


def union(boxes):
    boxes = [b for b in boxes if b]
    return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))


def wrap(inner):
    return f'<svg xmlns="http://www.w3.org/2000/svg">{inner}</svg>'


def ink_box(inner):
    return union(element_boxes(wrap(inner)))


# ------------------------------------------------------------------ markup helpers
def read_svg(path):
    s = open(path, encoding='utf-8').read()
    vb = tuple(float(v) for v in re.search(r'viewBox="([^"]+)"', s).group(1).replace(',', ' ').split())
    inner = re.search(r'<svg[^>]*>(.*)</svg>', s, re.S).group(1)
    inner = re.sub(r'<title[^>]*>.*?</title>|<desc[^>]*>.*?</desc>', '', inner, flags=re.S)
    return vb, inner.strip()


def extract_group(svg, gid):
    """(attrs, inner) of <g id="gid" …>…</g> with proper nesting — or (None, None)."""
    m = re.search(r'<g\b([^>]*\bid="' + re.escape(gid) + r'"[^>]*)>', svg)
    if not m: return None, None
    depth, i = 1, m.end()
    for t in re.finditer(r'<g\b[^>]*?(/?)>|</g>', svg[i:]):
        if t.group(0).startswith('</'): depth -= 1
        elif not t.group(1): depth += 1
        if depth == 0:
            return m.group(1), svg[i:i + t.start()]
    return None, None


_MASKS = re.compile(r'(<(mask|clipPath|pattern)\b.*?</\2>)', re.S)


def _outside_masks(inner, fn):
    parts = _MASKS.split(inner)
    out = []; k = 0
    while k < len(parts):
        seg = parts[k]
        if k + 2 < len(parts) and parts[k + 1] and parts[k + 1].startswith('<'):
            out.append(fn(seg)); out.append(parts[k + 1]); k += 3
        else:
            out.append(fn(seg)); k += 1
    return ''.join(out)


_HEX = r'#[0-9A-Fa-f]{3,8}\b'


def colours(inner):
    found = []
    _outside_masks(inner, lambda s: found.extend(re.findall(r'(?:fill|stroke)="(' + _HEX + ')"', s)) or s)
    seen = []
    for c in found:
        if c.upper() not in seen: seen.append(c.upper())
    return seen


def recolor_all(inner, colour):
    """Every fill/stroke colour outside masks → `colour` (masks keep their #fff/#000 logic)."""
    return _outside_masks(inner, lambda s: re.sub(r'((?:fill|stroke)=")' + _HEX + '"', r'\g<1>' + colour + '"', s))


def recolor_map(inner, mapping):
    up = {k.upper(): v for k, v in mapping.items()}
    def rep(m):
        c = m.group(2).upper()
        return m.group(1) + up.get(c, m.group(2)) + '"'
    return _outside_masks(inner, lambda s: re.sub(r'((?:fill|stroke)=")(' + _HEX + ')"', rep, s))


def strip_ids(inner, keep=()):
    return re.sub(r'\sid="(?!(?:' + '|'.join(map(re.escape, keep or ('__none__',))) + r')")[^"]*"', '', inner)


def prefix_ids(inner, pfx):
    ids = set(re.findall(r'\bid="([^"]+)"', inner))
    if not ids: return inner
    for i in sorted(ids, key=len, reverse=True):
        inner = (inner.replace(f'id="{i}"', f'id="{pfx}-{i}"').replace(f'url(#{i})', f'url(#{pfx}-{i})')
                 .replace(f'href="#{i}"', f'href="#{pfx}-{i}"'))
    return inner


# ------------------------------------------------------------------ parts & items
class Part:
    """A logo element. box = geometry box (x0, y0, x1, y1) in source units, shared by every colour version.
    cap/baseline: text parts (cap height and first baseline in source units). oc: optical centre (marks)."""
    def __init__(self, name, inners, box, cap=None, baseline=None, oc=None, role='mark', far=None, meta=None):
        self.name, self.inners, self.box = name, dict(inners), tuple(box)
        self.cap, self.baseline, self.role = cap, baseline, role
        self.oc = oc or ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)
        self.far = far          # points used for circle-safe sizing (source units), default box corners
        self.meta = meta or {}

    @property
    def w(self): return self.box[2] - self.box[0]

    @property
    def h(self): return self.box[3] - self.box[1]

    def inner(self, variant):
        return self.inners.get(variant) or self.inners.get('color')

    def far_radius(self, cx, cy):
        pts = self.far or [(self.box[0], self.box[1]), (self.box[2], self.box[1]), (self.box[0], self.box[3]), (self.box[2], self.box[3])]
        return max(math.hypot(x - cx, y - cy) for x, y in pts)


class Item:
    """A Part placed so that its box top-left is at (x, y) with uniform scale s (lockup units)."""
    def __init__(self, part, x, y, s, role=None):
        self.part, self.x, self.y, self.s = part, x, y, s
        self.role = role or part.role

    @property
    def bbox(self):
        p = self.part
        return (self.x, self.y, self.x + p.w * self.s, self.y + p.h * self.s)

    def to(self, sx, sy):
        """source point → lockup point"""
        return self.x + (sx - self.part.box[0]) * self.s, self.y + (sy - self.part.box[1]) * self.s

    @property
    def oc(self):
        return self.to(*self.part.oc)

    def shift(self, dx, dy):
        self.x += dx; self.y += dy; return self

    def svg(self, variant, pfx, gid=None):
        p = self.part
        tx = self.x - p.box[0] * self.s; ty = self.y - p.box[1] * self.s
        inner = prefix_ids(p.inner(variant), pfx)
        idattr = f' id="{gid}"' if gid else ''
        return f'<g{idattr} transform="translate({f2(tx)} {f2(ty)}) scale({self.s:.6f})">{inner}</g>'


def place_h(part, x, y, h, role=None):
    return Item(part, x, y, h / part.h, role)


def place_centre(part, cx, cy, s, role=None, use_oc=True):
    ox, oy = part.oc if use_oc else ((part.box[0] + part.box[2]) / 2, (part.box[1] + part.box[3]) / 2)
    return Item(part, cx - (ox - part.box[0]) * s, cy - (oy - part.box[1]) * s, s, role)


def place_text(part, x, baseline, cap_h, align='left', role=None):
    """Text part with its ink left/centre/right at x and its first baseline at `baseline`; cap height = cap_h."""
    s = cap_h / part.cap
    top = baseline + (part.box[1] - part.baseline) * s
    w = part.w * s
    left = x if align == 'left' else (x - w / 2 if align == 'center' else x - w)
    return Item(part, left, top, s, role)


def items_bbox(items):
    return union([i.bbox for i in items])


class Lockup:
    """A composed logo arrangement in lockup units (X = 100)."""
    def __init__(self, name, title, use, items, X=100.0, notes=None, kind='lockup', square=False):
        self.name, self.title, self.use, self.items, self.X = name, title, use, items, X
        self.notes = notes or {}           # construction numbers in X (for docs)
        self.kind, self.square = kind, square

    @property
    def bbox(self):
        return items_bbox(self.items)

    @property
    def size(self):
        x0, y0, x1, y1 = self.bbox
        return x1 - x0, y1 - y0

    @property
    def aspect(self):
        w, h = self.size
        return w / h

    def body(self, variant, pfx='l', ids=True):
        out = []
        used = {}
        for k, it in enumerate(self.items):
            gid = None
            if ids:
                gid = it.role if it.role not in used else f'{it.role}-{used[it.role] + 1}'
                used[it.role] = used.get(it.role, 0) + 1
            out.append(it.svg(variant, f'{pfx}{k}', gid=gid))
        return ''.join(out)

    def svg(self, variant, title, desc='', pad=0.0, pfx='l', bg=None, size=None):
        x0, y0, x1, y1 = self.bbox
        x0 -= pad; y0 -= pad; x1 += pad; y1 += pad
        w, h = x1 - x0, y1 - y0
        dims = f' width="{f2(size[0])}" height="{f2(size[1])}"' if size else ''
        bgr = f'<rect x="{f2(x0)}" y="{f2(y0)}" width="{f2(w)}" height="{f2(h)}" fill="{bg}"/>' if bg else ''
        d = f'<desc>{desc}</desc>' if desc else ''
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{f2(x0)} {f2(y0)} {f2(w)} {f2(h)}"{dims} role="img" '
                f'aria-labelledby="{pfx}-t"><title id="{pfx}-t">{title}</title>{d}{bgr}{self.body(variant, pfx, True)}</svg>\n'), (x0, y0, w, h)

    def inline(self, variant, pfx, cls='', style='', label=None, pad=0.0, extra_svg=''):
        """Inline <svg> for HTML pages (unique ids via pfx)."""
        x0, y0, x1, y1 = self.bbox
        x0 -= pad; y0 -= pad; x1 += pad; y1 += pad
        lab = f'role="img" aria-label="{label}"' if label else 'aria-hidden="true"'
        return (f'<svg class="{cls}" style="{style}" viewBox="{f2(x0)} {f2(y0)} {f2(x1 - x0)} {f2(y1 - y0)}" {lab} '
                f'xmlns="http://www.w3.org/2000/svg">{self.body(variant, pfx, False)}{extra_svg}</svg>')
