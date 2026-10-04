"""logo.py — read the logo parts of a brand repo and compose its lockups (brand-neutral).

Units: every lockup is built with X = cap height of the name / lettering = 100 units.
Colourways ("variants"): color (light grounds) · on-dark · foundation (one colour) · white (one colour) ·
primary (one colour, only when the primary reaches 3:1 on paper).
"""
import json, math, os, re
from svgkit import (Part, Item, Lockup, place_h, place_text, place_centre, items_bbox, union, element_boxes, wrap,
                    ink_box, read_svg, extract_group, recolor_all, recolor_map, colours, contrast, f2, prefix_ids, lum)

X = 100.0
WHITE = '#FFFFFF'


# ------------------------------------------------------------------ palette roles
class Ink:
    def __init__(self, b):
        r = b.role
        self.P = r.get('primary') or '#333333'
        self.F = r.get('foundation') or '#111111'
        self.PA = r.get('paper') or '#FFFFFF'
        self.A = r.get('accent') or self.P
        self.W = WHITE
        self.dark = (b.dark or {}).get('background') or self.F           # the on-dark ground
        self.light = (b.theme or {}).get('background') or self.PA        # the light ground
        self.primary_ok = contrast(self.P, self.PA) >= 3.0               # one-colour primary allowed
        # what goes on a primary field: white if it holds ≥ 3:1, else the foundation
        cw, cf = contrast(WHITE, self.P), contrast(self.F, self.P)
        self.on_primary = WHITE if (cw >= 3.0 or cw >= cf) else self.F
        self.on_primary_variant = 'white' if self.on_primary == WHITE else 'foundation'

    def variants(self):
        return ['color', 'on-dark', 'foundation', 'white'] + (['primary'] if self.primary_ok else [])

    def mono(self, v):
        return {'foundation': self.F, 'white': self.W, 'primary': self.P}.get(v)

    def text_colour(self, v):
        """colour of typeset name / descriptor lines per variant"""
        return {'color': self.F, 'on-dark': self.PA}.get(v) or self.mono(v)

    def ground(self, v):
        """the ground a variant is designed for (previews)"""
        return {'color': self.light, 'on-dark': self.dark, 'foundation': self.light, 'white': self.P if self.on_primary == WHITE else self.dark,
                'primary': self.light}[v]


def on_dark_map(cols, ink, keep=4.5):
    """light-ground lettering colours → on-dark: colours under `keep`:1 on the dark ground become paper."""
    return {c: (c if contrast(c, ink.dark) >= keep else ink.PA) for c in cols}


# ------------------------------------------------------------------ reading the repo
def _wordmark_items(b):
    p = b.path('SOURCE', 'JS', 'wordmark-data.js')
    if not os.path.exists(p): return {}
    s = open(p, encoding='utf-8').read()
    m = re.search(r'=\s*(\{.*\})\s*;?\s*$', s, re.S)
    try: return json.loads(m.group(1)).get('items', {})
    except Exception: return {}


def _wm_paths(b):
    p = b.path('SOURCE', 'JSON', 'wordmark-paths.json')
    return json.load(open(p)) if os.path.exists(p) else {}


def _first_glyph_cap(body, fallback):
    """cap height estimate of a typeset run: height of its first glyph contour when it sits on the baseline."""
    m = re.search(r'd="([^"]+)"', body)
    if not m: return fallback
    sub = re.split(r'(?=M)', m.group(1).strip())
    from svgkit import path_points
    for sp in sub:
        if not sp.strip(): continue
        pts = path_points(sp)
        if not pts: continue
        ys = [p[1] for p in pts]
        y0, y1 = min(ys), max(ys)
        if abs(y1) <= 0.06 * abs(y0) and -y0 > 0.4 * fallback:
            return -y0
        break
    return fallback


def _typeset_part(name, item, cap, ink, role):
    body = item['body']
    vb = [float(v) for v in item['vb'].split()]
    try: box = ink_box(body)
    except Exception: box = (vb[0], vb[1], vb[0] + vb[2], vb[1] + vb[3])
    if cap is None: cap = _first_glyph_cap(body, -vb[1])
    baselines = sorted({round(float(t), 2) for t in re.findall(r'translate\([-\d.]+[ ,]+([-\d.]+)\)', body)} or {0.0})
    inners = {v: f'<g fill="{ink.text_colour(v)}">{body}</g>' for v in ('color', 'on-dark', 'foundation', 'white', 'primary')}
    return Part(name, inners, box, cap=cap, baseline=baselines[0], role=role, meta={'baselines': baselines, 'text': item.get('text')})


def _rows(boxes):
    """cluster glyph boxes into text rows (vertical overlap)"""
    rows = []
    for bx in sorted(boxes, key=lambda b: (b[1] + b[3]) / 2):
        for r in rows:
            ov = min(r['y1'], bx[3]) - max(r['y0'], bx[1])
            if ov > 0.5 * min(r['y1'] - r['y0'], bx[3] - bx[1]):
                r['b'].append(bx); r['y0'] = min(r['y0'], bx[1]); r['y1'] = max(r['y1'], bx[3]); break
        else:
            rows.append({'b': [bx], 'y0': bx[1], 'y1': bx[3]})
    return rows


def lettering_cap(inner):
    """cap height of traced lettering: median height of the tall glyphs of its largest row.
    Returns (cap, rows, cap_top, baseline) in source units."""
    boxes = [bx for bx in element_boxes(wrap(inner)) if bx[3] - bx[1] > 0]
    rows = _rows(boxes)
    if not rows: return None, [], None, None
    main = max(rows, key=lambda r: (r['y1'] - r['y0']) * len(r['b']) ** 0.5)
    rh = main['y1'] - main['y0']
    tall = [bx for bx in main['b'] if bx[3] - bx[1] >= 0.75 * rh] or main['b']
    hs = sorted(bx[3] - bx[1] for bx in tall)
    tops = sorted(bx[1] for bx in tall); bots = sorted(bx[3] for bx in tall)
    return hs[len(hs) // 2], rows, tops[len(tops) // 2], bots[len(bots) // 2]


def split_glyphs(inner):
    """top-level <path …/> elements of traced lettering grouped into glyphs (an i-dot stays with its stem), left to right.
    Returns [(box, markup)]."""
    els = []
    for m in re.finditer(r'<path\b[^>]*/>', inner):
        try: bx = ink_box(m.group(0))
        except Exception: continue
        els.append([bx, m.group(0)])
    els.sort(key=lambda t: t[0][0])
    out = []
    for bx, mk in els:
        if out:
            pb = out[-1][0]
            ov = min(pb[2], bx[2]) - max(pb[0], bx[0])
            if ov > 0.5 * min(pb[2] - pb[0], bx[2] - bx[0]):
                out[-1][0] = (min(pb[0], bx[0]), min(pb[1], bx[1]), max(pb[2], bx[2]), max(pb[3], bx[3]))
                out[-1][1] += mk
                continue
        out.append([bx, mk])
    return [tuple(o) for o in out]


def load_parts(b, ink):
    """All logo parts of the brand as Part objects (one geometry box, colour versions in .inners)."""
    S = lambda n: b.path('LOGO', 'SVG', n + '.svg')
    ex = lambda n: os.path.exists(S(n))
    lt = b.logo_type
    M = b.mark or {}
    parts = {}
    # ---- the mark (symbol / emblem / combination symbol). For a wordmark the "mark" IS the lettering.
    vb, col_inner = read_svg(S('symbol'))
    oc_rel = M.get('optical_center') or [0.5, 0.5]
    oc = (vb[0] + oc_rel[0] * vb[2], vb[1] + oc_rel[1] * vb[3])
    sil = M.get('silhouette') or None
    far = [tuple(p) for p in sil] if sil and isinstance(sil[0], (list, tuple)) else None

    def mono_from(file_, colour):
        if not ex(file_): return None
        _, inner = read_svg(S(file_))
        return recolor_all(inner, colour)

    if lt == 'wordmark':
        cols = colours(col_inner)
        inners = {'color': col_inner, 'on-dark': recolor_map(col_inner, on_dark_map(cols, ink))}
        for v in ('foundation', 'white', 'primary'): inners[v] = recolor_all(col_inner, ink.mono(v))
        box = ink_box(col_inner)
        cap, rows, ctop, cbase = lettering_cap(col_inner)
        parts['lettering'] = Part('lettering', inners, box, cap=cap or box[3] - box[1], role='lettering', oc=oc,
                                  meta={'rows': len(rows), 'cap_top': ctop, 'base': cbase})
    else:
        inners = {'color': col_inner}
        inners['on-dark'] = read_svg(S('symbol-on-dark'))[1] if ex('symbol-on-dark') else col_inner
        inners['foundation'] = mono_from('symbol-black', ink.F) or recolor_all(col_inner, ink.F)
        inners['white'] = mono_from('symbol-white', ink.W) or recolor_all(col_inner, ink.W)
        inners['primary'] = mono_from('symbol-solid-primary', ink.P) or mono_from('symbol-black', ink.P) or recolor_all(col_inner, ink.P)
        parts['mark'] = Part('mark', inners, ink_box(col_inner), oc=oc, far=far, role='symbol', meta={'vb': vb})

    # ---- compact mark (favicons, avatars, small sizes)
    cvb, c_inner = read_svg(S('compact')) if ex('compact') else (vb, col_inner)
    if lt == 'wordmark':
        cbox = ink_box(c_inner)
        letter = {'color': recolor_all(c_inner, ink.P if ink.primary_ok else ink.F)}
        for v in ('foundation', 'white', 'primary'): letter[v] = recolor_all(c_inner, ink.mono(v))
        letter['on-dark'] = recolor_all(c_inner, ink.PA)
        parts['compact'] = Part('compact', letter, cbox, role='monogram',
                                oc=((cbox[0] + cbox[2]) / 2, (cbox[1] + cbox[3]) / 2))
    else:
        cin = {'color': c_inner}
        cin['on-dark'] = read_svg(S('symbol-small-on-dark'))[1] if ex('symbol-small-on-dark') else parts['mark'].inners['on-dark']
        cin['foundation'] = mono_from('compact-black', ink.F) or parts['mark'].inners['foundation']
        cin['white'] = mono_from('compact-white', ink.W) or parts['mark'].inners['white']
        cin['primary'] = mono_from('compact-black', ink.P) or parts['mark'].inners['primary']
        coc = (cvb[0] + oc_rel[0] * cvb[2], cvb[1] + oc_rel[1] * cvb[3])
        parts['compact'] = Part('compact', cin, ink_box(c_inner), oc=coc, far=far if tuple(cvb) == tuple(vb) else None, role='symbol')

    # ---- traced lettering of a combination logo (from the rebuilt original, at its original position)
    if lt == 'combination' and ex('logo-original'):
        orig = open(S('logo-original'), encoding='utf-8').read()
        _, l_inner = extract_group(orig, 'lettering')
        sattr, _ = extract_group(orig, 'symbol')
        if l_inner:
            cols = colours(l_inner)
            inners = {'color': l_inner, 'on-dark': recolor_map(l_inner, on_dark_map(cols, ink))}
            for v in ('foundation', 'white', 'primary'): inners[v] = recolor_all(l_inner, ink.mono(v))
            box = ink_box(l_inner)
            cap, rows, ctop, cbase = lettering_cap(l_inner)
            parts['lettering'] = Part('lettering', inners, box, cap=cap or 0.6 * (box[3] - box[1]), role='lettering',
                                      meta={'rows': len(rows), 'cap_top': ctop, 'base': cbase})
            t = re.search(r'translate\(\s*([-\d.]+)[ ,]+([-\d.]+)\s*\)', sattr or '')
            parts['_offset'] = (float(t.group(1)), float(t.group(2))) if t else tuple((M.get('origin_offset_in_artwork') or [0, 0]))

    # ---- typeset name lines, descriptor, local-script name (wordmark-data.js)
    items = _wordmark_items(b); wp = _wm_paths(b)
    capu = wp.get('cap_height_units')
    for key, item in items.items():
        if key == 'lettering': continue
        if key in ('stacked', 'line') or key.startswith('line_'):
            parts['name_' + key] = _typeset_part('name_' + key, item, capu, ink, 'name')
        elif key == 'descriptor':
            parts['descriptor'] = _typeset_part('descriptor', item, None, ink, 'descriptor')
        elif key == 'name-local':
            parts['local'] = _typeset_part('local', item, None, ink, 'local')
    return parts


# ------------------------------------------------------------------ helpers
def _scale_to_cap(part, cap=X):
    return cap / part.cap


def _name_lines(parts):
    """typeset name split into its lines (centred lockups need each line separately)"""
    n = len(parts['name_stacked'].meta['baselines']) if 'name_stacked' in parts else 1
    lines = [parts.get(f'name_line_{i}') for i in range(1, n + 1)]
    if n <= 1 or not all(lines):
        return [parts.get('name_line') or parts.get('name_stacked')]
    return lines


def _line_adv(b, parts):
    wp = _wm_paths(b)
    adv = wp.get('line_advance_caps')
    if adv: return adv
    st = parts.get('name_stacked')
    if st and len(st.meta['baselines']) > 1:
        return (st.meta['baselines'][1] - st.meta['baselines'][0]) / st.cap
    return 1.2


def _sub_line(part, width_limit, cap_max, cap_min):
    """cap height for a secondary line (descriptor / local name) that should not overhang the name block"""
    w_per_cap = part.w / part.cap
    return max(cap_min, min(cap_max, width_limit / w_per_cap))


def _text_block(b, parts, lines, align, x, top, subs=()):
    """name lines (cap X, line advance from the wordmark) + optional sub lines. Returns items, block bottom (last baseline)."""
    adv = _line_adv(b, parts)
    items = []
    base = top + X
    widths = [ln.w * X / ln.cap for ln in lines]
    block_w = max(widths)
    for i, ln in enumerate(lines):
        bl = top + X + i * adv * X
        items.append(place_text(ln, x, bl, X, align, role='name'))
        base = bl
    for key, cap_max, cap_min, gap in subs:
        sp = parts.get(key)
        if not sp: continue
        cap = _sub_line(sp, block_w, cap_max * X, cap_min * X)
        bl = base + gap * X + cap
        items.append(place_text(sp, x, bl, cap, align, role=sp.role))
        base = bl
    return items, base


def _centre_on(items, y_centre, top, bottom):
    dy = y_centre - (top + bottom) / 2
    for it in items: it.shift(0, dy)


# ------------------------------------------------------------------ lockups per logo type
def lockups_combination(b, parts, ink):
    mark, let = parts['mark'], parts['lettering']
    lay = b.parts.get('layout') or {}
    arr = b.parts.get('arrangement') or ('stacked' if lay.get('symbol_side') == 'top' else 'horizontal')
    k = X / let.cap
    ox, oy = parts.get('_offset', (0, 0))
    m0 = Item(mark, (mark.box[0] + ox) * k, (mark.box[1] + oy) * k, k)
    l0 = Item(let, let.box[0] * k, let.box[1] * k, k)
    mb, lb = m0.bbox, l0.bbox
    Hs = mb[3] - mb[1]
    if arr == 'horizontal':
        gap = max(lb[0] - mb[2], 0.1 * Hs)
    else:
        gap = max(lb[1] - mb[3], 0.1 * Hs)
    let_h_rel = (lb[3] - lb[1]) / Hs
    out = []
    note = {'mark_h': Hs / X, 'gap': gap / X, 'lettering_h': (lb[3] - lb[1]) / X}
    out.append(Lockup('primary', 'Primary — original lockup', 'The original arrangement, rebuilt in vector. First choice wherever it fits.',
                      [m0, l0], notes=dict(note, arrangement=arr)))

    def horizontal():
        m = Item(mark, 0, 0, k)
        l = Item(let, m.bbox[2] + gap, 0, k)
        l.shift(0, m.oc[1] - (l.bbox[1] + l.bbox[3]) / 2)
        return [m, l]

    def stacked(centred):
        l = Item(let, 0, 0, k)
        m = Item(mark, 0, 0, k)
        if centred: m.shift((l.bbox[0] + l.bbox[2]) / 2 - m.oc[0], 0)
        else: m.shift(l.bbox[0] - m.bbox[0], 0)
        l.shift(0, m.bbox[3] + gap - l.bbox[1])
        return [m, l]

    if arr == 'horizontal':
        out.append(Lockup('stacked', 'Stacked', 'Symbol above the lettering, flush left. Narrow columns, editorial layouts, left-aligned grids.',
                          stacked(False), notes=dict(note, arrangement='stacked, flush left')))
        out.append(Lockup('vertical', 'Vertical — centred', 'Symbol centred above the lettering on its optical axis. Covers, posters, square formats.',
                          stacked(True), notes=dict(note, arrangement='vertical, optically centred')))
    else:
        out.append(Lockup('horizontal', 'Horizontal', 'Symbol left, lettering centred on the symbol\'s optical centre. Headers, footers, wide formats.',
                          horizontal(), notes=dict(note, arrangement='horizontal, optically centred')))
        off = abs(lay.get('lettering_center_offset_rel', 0) or 0)
        if off > 0.03:
            out.append(Lockup('vertical', 'Vertical — centred', 'Symbol centred on the optical axis above the lettering.',
                              stacked(True), notes=dict(note, arrangement='vertical, optically centred')))
    if parts.get('descriptor'):
        base = [Item(i.part, i.x, i.y, i.s) for i in out[0].items]
        lb2 = base[1].bbox
        d = parts['descriptor']
        cap = _sub_line(d, lb2[2] - lb2[0], 0.3 * X, 0.16 * X)
        align = 'center' if (arr != 'horizontal') else 'left'
        x = (lb2[0] + lb2[2]) / 2 if align == 'center' else lb2[0]
        di = place_text(d, x, lb2[3] + 0.5 * X + cap, cap, align, role='descriptor')
        out.append(Lockup('primary-descriptor', 'Primary + descriptor', 'Original lockup with the descriptor line. Official documents, signage, first contact.',
                          base + [di], notes=dict(note, descriptor_cap=cap / X, descriptor_gap=0.5)))
    out.append(Lockup('symbol', 'Symbol', 'The symbol alone — when the name is already present or space is square.', [Item(mark, 0, 0, k)], kind='symbol',
                      notes={'mark_h': Hs / X}))
    out.append(Lockup('lettering', 'Lettering', 'The traced lettering alone — when the symbol appears elsewhere in the layout.', [Item(let, 0, 0, k)],
                      kind='lettering', notes={'lettering_h': (lb[3] - lb[1]) / X}))
    return out, 'primary'


def lockups_symbol(b, parts, ink, emblem=False):
    mark = parts['mark']
    a = mark.w / mark.h
    kt = 1.2 if emblem else 1.0
    lines = _name_lines(parts)
    stacked_n = len(lines)
    adv = _line_adv(b, parts)
    out = []

    def horizontal(name_lines, subs=()):
        items, last = _text_block(b, parts, name_lines, 'left', 0, 0, subs)
        name_h = X + (len(name_lines) - 1) * adv * X      # cap-top → last name baseline; secondary lines never inflate the mark
        Hm = max(max(1.4 * name_h, 2.0 * X) * kt * a ** -0.25, 1.1 * last)
        s = Hm / mark.h
        m = Item(mark, 0, 0, s)
        gap = 0.22 * Hm
        for it in items: it.shift(m.bbox[2] + gap, 0)
        _centre_on(items, m.oc[1], 0, last)
        return [m] + items, {'mark_h': Hm / X, 'gap': gap / X, 'cap': 1.0, 'lines': len(name_lines), 'line_advance': adv}

    def vertical(name_lines):
        items, last = _text_block(b, parts, name_lines, 'center', 0, 0)
        tw = max(i.bbox[2] - i.bbox[0] for i in items)
        Hm = min(6.0 * X, max(2.8 * X, (0.64 if emblem else 0.62) * tw / a))
        s = Hm / mark.h
        m = Item(mark, 0, 0, s)
        m.shift(-m.oc[0], 0)
        gap = max(0.6 * X, 0.15 * Hm)
        for it in items: it.shift(0, Hm + gap)
        return [m] + items, {'mark_h': Hm / X, 'gap': gap / X, 'cap': 1.0, 'lines': len(name_lines)}

    it, nt = horizontal(lines)
    out.append(Lockup('horizontal', 'Horizontal', f'{"Emblem" if emblem else "Symbol"} left, name block centred on its optical centre. The default lockup for most layouts.', it, notes=nt))
    if stacked_n > 1 and parts.get('name_line'):
        it, nt = horizontal([parts['name_line']])
        out.append(Lockup('horizontal-line', 'Horizontal — one line', 'Name on one line. Wide, shallow spaces: web headers, footers, credits.', it, notes=nt))
    if parts.get('descriptor'):
        it, nt = horizontal(lines, subs=[('descriptor', 0.3, 0.16, 0.42)])
        out.append(Lockup('horizontal-descriptor', 'Horizontal + descriptor', 'With the descriptor line. Official documents, signage, first contact.', it, notes=nt))
    it, nt = vertical(lines)
    out.append(Lockup('vertical', 'Vertical', f'{"Emblem" if emblem else "Symbol"} centred above the name. Covers, posters, square and tall formats.', it, notes=nt))
    if parts.get('local'):
        loc = [l for l in b.langs if l != b.lang][:1]
        tag = loc[0] if loc else 'local'
        it, nt = horizontal(lines, subs=[('local', 0.42, 0.2, 0.45)])
        out.append(Lockup(f'horizontal-{tag}', f'Horizontal + local name ({tag.upper()})', f'Name with its local-language form ({tag}) underneath — bilingual and local-language contexts.', it,
                          notes=dict(nt, lang=tag)))
    out.append(Lockup('symbol', 'Emblem' if emblem else 'Symbol', 'The mark alone — avatars, stamps, when the name is already present.',
                      [Item(mark, 0, 0, 3 * X / mark.h)], kind='symbol', notes={}))
    return out, 'horizontal'


def corner_style(b):
    c = (b.dna or {}).get('corner', {}) or {}
    return c.get('style') or 'rounded', c.get('angle_deg') or (b.dna or {}).get('angles', {}).get('cut') or 45


def container_path(b, x, y, S):
    """container shape for compact marks / app icons, following dna.corner.style"""
    style, ang = corner_style(b)
    if style == 'round':
        r = S / 2
        return f'<circle cx="{f2(x + r)}" cy="{f2(y + r)}" r="{f2(r)}"/>', 'circle'
    if style == 'cut':
        c = 0.16 * S; cy = min(0.36 * S, c * math.tan(math.radians(ang)))
        pts = [(x, y), (x + S, y), (x + S, y + S - cy), (x + S - c, y + S), (x, y + S)]
        return '<polygon points="' + ' '.join(f'{f2(px)},{f2(py)}' for px, py in pts) + '"/>', f'chamfered square ({ang}°)'
    r = {'soft': 0.3, 'rounded': 0.22, 'square': 0.04}.get(style, 0.22) * S
    return f'<rect x="{f2(x)}" y="{f2(y)}" width="{f2(S)}" height="{f2(S)}" rx="{f2(r)}"/>', ('rounded square' if style != 'square' else 'square')


class ContainerLockup(Lockup):
    """compact mark inside the DNA container shape; one-colour versions knock the mark out of the container"""
    def __init__(self, b, ink, letter, S=400.0, fit=(0.56, 0.62)):
        style, _ = corner_style(b)
        self.b, self.ink, self.S = b, ink, S
        fh, fw = fit if style != 'round' else (fit[0] * 0.92, fit[1] * 0.9)
        s = min(fh * S / letter.h, fw * S / letter.w)
        it = place_centre(letter, S / 2, S / 2, s, role='monogram', use_oc=True)
        super().__init__('compact', 'Compact mark', 'Monogram in the brand container shape — avatars, app icons, favicons, stamps.', [it], kind='compact', square=True)
        self.shape, self.shape_name = container_path(b, 0, 0, S)

    @property
    def bbox(self):
        return (0, 0, self.S, self.S)

    def colours(self, v):
        k = self.ink
        if v == 'color':
            letter = k.PA if contrast(k.PA, k.P) >= max(3.0, contrast(k.F, k.P) * 0.6) else k.F
            return k.P, letter
        if v == 'on-dark':
            return k.PA, (k.P if contrast(k.P, k.PA) >= 3.0 else k.F)
        return k.mono(v), None

    def body(self, variant, pfx='l', ids=True):
        cont, letter = self.colours(variant)
        it = self.items[0]
        p = it.part
        tx = it.x - p.box[0] * it.s; ty = it.y - p.box[1] * it.s
        glyph = re.sub(r'(fill|stroke)="#[0-9A-Fa-f]{3,8}"', r'\1="#000"', p.inner('foundation'))
        glyph = prefix_ids(glyph, pfx + 'g')
        g = f'<g transform="translate({f2(tx)} {f2(ty)}) scale({it.s:.6f})">'
        shape = self.shape.replace('/>', f' fill="{cont}"/>')
        if letter:
            lg = re.sub(r'(fill|stroke)="#000"', rf'\1="{letter}"', glyph)
            return f'<g id="{pfx}-container">{shape}</g>{g}{lg}</g>' if ids else f'{shape}{g}{lg}</g>'
        mk = (f'<defs><mask id="{pfx}-ko" maskUnits="userSpaceOnUse" x="0" y="0" width="{f2(self.S)}" height="{f2(self.S)}">'
              f'{self.shape.replace("/>", " fill=\"#fff\"/>")}{g}{glyph}</g></mask></defs>')
        return f'{mk}<g mask="url(#{pfx}-ko)">{shape}</g>'


def lockups_wordmark(b, parts, ink):
    let = parts['lettering']
    k = X / let.cap
    out = []
    l0 = Item(let, 0, 0, k)
    lb = l0.bbox
    out.append(Lockup('wordmark', 'Wordmark', 'The traced lettering — the logo itself. First choice everywhere.', [l0],
                      notes={'lettering_h': (lb[3] - lb[1]) / X}))
    if parts.get('descriptor'):
        d = parts['descriptor']
        comp = ((b.dna or {}).get('composition') or '')
        align = 'center' if (any(w in comp for w in ('centr', 'symmetr', 'radial')) and 'asymmetr' not in comp) else 'left'
        cap = _sub_line(d, 0.62 * (lb[2] - lb[0]), 0.3 * X, 0.16 * X)
        x = (lb[0] + lb[2]) / 2 if align == 'center' else lb[0] + 0.02 * X
        di = place_text(d, x, lb[3] + 0.55 * X + cap, cap, align, role='descriptor')
        out.append(Lockup('wordmark-descriptor', 'Wordmark + descriptor', 'With the descriptor line. Signage, packaging, official documents.',
                          [Item(let, 0, 0, k), di], notes={'descriptor_cap': cap / X, 'descriptor_gap': 0.55, 'align': align}))
    out.append(ContainerLockup(b, ink, parts['compact']))
    c = parts['compact']
    out.append(Lockup('monogram', 'Monogram', 'The traced first letter alone — embossing, pattern accents, tiny spaces. Not a replacement for the wordmark.',
                      [Item(c, 0, 0, 3 * X / c.h)], kind='symbol'))
    return out, 'wordmark'


def build_lockups(b, parts, ink):
    lt = b.logo_type
    if lt == 'combination' and 'lettering' in parts:
        return lockups_combination(b, parts, ink)
    if lt == 'wordmark':
        return lockups_wordmark(b, parts, ink)
    if any(k.startswith('name_') for k in parts):
        return lockups_symbol(b, parts, ink, emblem=(lt == 'emblem'))
    mark = parts['mark']
    return [Lockup('symbol', 'Symbol', 'The mark.', [Item(mark, 0, 0, 3 * X / mark.h)], kind='symbol')], 'symbol'


def cap_lines(item):
    """(cap_top, baseline) of a text/lettering item in lockup units — or None"""
    p = item.part
    if p.role in ('name', 'descriptor', 'local') and p.cap:
        base = item.y + (p.baseline - p.box[1]) * item.s
        return base - p.cap * item.s, base
    if p.role == 'lettering' and p.meta.get('cap_top') is not None:
        return item.to(0, p.meta['cap_top'])[1], item.to(0, p.meta['base'])[1]
    return None
