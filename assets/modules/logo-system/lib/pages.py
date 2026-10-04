"""pages.py — logo guides (clear space, minimum sizes, construction, misuse) and the logo sheet (HTML → PNG).

Everything is drawn from the composed lockups; colours come from theme tokens, type from <p>-core.css classes,
panel corners from the DNA (<p>-shape), diagram textures from the DNA language (hatch at the logo angle / dots / lines).
"""
import math, os, re
import forge_lib as F
from svgkit import f2, contrast, mix, Item, place_centre, prefix_ids, items_bbox, recolor_all
from logo import X, cap_lines, split_glyphs, container_path, corner_style

esc = F.esc
_N = [0]


def uid(p='x'):
    _N[0] += 1
    return f'{p}{_N[0]}'


# ------------------------------------------------------------------ shared look
def T(c, k, d='#888888'):
    return (c.b.theme or {}).get(k) or d


def css(c):
    p = c.b.p
    same = (T(c, 'surface', '#FFFFFF').upper() == T(c, 'background', '#FFFFFF').upper())
    pagebg = 'var(--color-background-alt)' if same else 'var(--color-background)'
    paper = 'var(--color-background)' if same else 'var(--color-surface)'
    alt = 'color-mix(in srgb, var(--color-background-alt) 100%, var(--color-text-primary) 5%)' if same else 'var(--color-background-alt)'
    return f"""
html,body{{background:{pagebg}}}
.lgs{{width:1600px;padding:64px 72px 56px;box-sizing:border-box;color:var(--color-text-primary)}}
.lgs-hd{{display:grid;grid-template-columns:minmax(0,1fr) 540px;gap:64px;align-items:end;padding-bottom:28px;border-bottom:1px solid var(--color-border-strong)}}
.lgs-hd h1{{margin-top:14px}}
.lgs-lead{{color:var(--color-text-secondary);margin:0}}
.lgs-sec{{margin-top:44px}}
.lgs-sec-hd{{display:flex;justify-content:space-between;align-items:baseline;gap:24px;margin:0 0 16px}}
.lgs-sec-hd .{p}-label{{color:var(--color-text-secondary)}}
.lgs-grid{{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:20px}}
.lgs-panel{{background:var(--color-surface);padding:26px 28px 22px;display:flex;flex-direction:column;gap:14px;min-width:0;position:relative}}
.lgs-panel.is-dark{{background:var(--color-background-inverse);color:var(--color-text-inverse)}}
.lgs-panel.is-primary{{background:var(--color-brand-primary);color:var(--color-text-on-brand)}}
.lgs-panel.is-alt{{background:{alt}}}
.lgs-panel.is-paper{{background:{paper}}}
.lgs-band{{display:flex;align-items:flex-end;justify-content:space-between;gap:28px;flex-wrap:nowrap}}
.lgs-band figure{{margin:0;display:grid;gap:12px;justify-items:start;min-width:0}}
.lgs-stage{{flex:1;display:flex;align-items:center;justify-content:center;min-height:120px}}
.lgs-stage img,.lgs-stage svg{{display:block;max-width:100%}}
.lgs-meta{{display:flex;justify-content:space-between;gap:12px;align-items:baseline;flex-wrap:wrap}}
.lgs-meta .lgs-x{{opacity:.72}}
.lgs-ft{{margin-top:44px;padding-top:16px;border-top:1px solid var(--color-border);display:flex;justify-content:space-between;gap:24px;color:var(--color-text-secondary)}}
.lgs-list{{margin:0;padding:0;list-style:none;display:grid;gap:10px}}
.lgs-list li{{display:grid;grid-template-columns:22px 1fr;gap:10px;align-items:baseline}}
.lgs-list li::before{{content:'—';color:var(--color-text-brand)}}
.lgs-kv{{display:grid;grid-template-columns:auto 1fr;gap:6px 18px;align-items:baseline;margin:0}}
.lgs-kv dt{{color:var(--color-text-secondary)}} .lgs-kv dd{{margin:0}}
.lgs-tbl{{width:100%;border-collapse:collapse}}
.lgs-tbl th{{text-align:left;font-weight:inherit;color:var(--color-text-secondary);padding:0 12px 10px 0;border-bottom:1px solid var(--color-border-strong)}}
.lgs-tbl td{{padding:12px 12px 12px 0;border-bottom:1px solid var(--color-border);vertical-align:middle}}
.lgs-num{{font-variant-numeric:tabular-nums}}
.lgs-outline *{{fill:none!important;stroke:{T(c, 'text-primary')};stroke-width:1.1px;vector-effect:non-scaling-stroke}}
""" + ''.join(f'.s{i}{{grid-column:span {i}}}' for i in range(1, 13))


def page(c, title, body, at):
    return F.page(c.b, title, body, at, head=f'<style>{css(c)}</style>', scripts=())


def header(c, idx, title, lead):
    p, b = c.b.p, c.b
    return (f'<header class="lgs-hd"><div><p class="{p}-eyebrow"><span class="{p}-index">{idx}</span> {esc(b.name)} · Logo system</p>'
            f'<h1 class="{p}-h1">{esc(title)}</h1></div><p class="{p}-body-l lgs-lead">{lead}</p></header>')


def footer(c, path, right=''):
    p = c.b.p
    return (f'<footer class="lgs-ft"><span class="{p}-label">{esc(path)}</span>'
            f'<span class="{p}-label">{esc(right or "X = cap height of the name / lettering")}</span></footer>')


def panel_cls(c, extra=''):
    return f'lgs-panel {c.b.p}-shape {extra}'.strip()


def lk_by(c, name):
    return next((l for l in c.lockups if l.name == name), None)


def texture(c, pid, col, bg, k):
    """DNA texture for clear-space zones: hatch at the logo angle (angular), dots (round), fine lines (organic)."""
    dna = c.b.dna or {}
    lang = dna.get('base_language', 'mixed')
    ang = dna.get('angles', {}).get('cut', 45) or 45
    s = 9 / k
    if lang == 'round':
        return (f'<pattern id="{pid}" width="{f2(s)}" height="{f2(s)}" patternUnits="userSpaceOnUse"><rect width="{f2(s)}" height="{f2(s)}" fill="{bg}"/>'
                f'<circle cx="{f2(s / 2)}" cy="{f2(s / 2)}" r="{f2(1.1 / k)}" fill="{col}"/></pattern>')
    if lang == 'organic':
        return (f'<pattern id="{pid}" width="{f2(2 * s)}" height="{f2(s)}" patternUnits="userSpaceOnUse"><rect width="{f2(2 * s)}" height="{f2(s)}" fill="{bg}"/>'
                f'<path d="M0 {f2(s / 2)} Q{f2(s / 2)} {f2(s * .15)} {f2(s)} {f2(s / 2)} T{f2(2 * s)} {f2(s / 2)}" fill="none" stroke="{col}" stroke-width="{f2(1 / k)}"/></pattern>')
    rot = 90 - ang if lang in ('angular', 'mixed') else 45
    return (f'<pattern id="{pid}" width="{f2(s)}" height="{f2(s)}" patternUnits="userSpaceOnUse" patternTransform="rotate({rot})">'
            f'<rect width="{f2(s)}" height="{f2(s)}" fill="{bg}"/><line x1="0" y1="0" x2="0" y2="{f2(s)}" stroke="{col}" stroke-width="{f2(1.2 / k)}"/></pattern>')


def _t(x, y, s, fs, fill, anchor='start', extra=''):
    return (f'<text x="{f2(x)}" y="{f2(y)}" font-size="{f2(fs)}" fill="{fill}" text-anchor="{anchor}" '
            f'style="font-family:var(--font-mono);letter-spacing:.06em;text-transform:uppercase"{extra}>{esc(s)}</text>')


def _ln(x1, y1, x2, y2, col, w=1, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    return f'<line x1="{f2(x1)}" y1="{f2(y1)}" x2="{f2(x2)}" y2="{f2(y2)}" stroke="{col}" stroke-width="{w}" vector-effect="non-scaling-stroke"{d}/>'


def _rect(x, y, w, h, fill='none', stroke=None, sw=1, dash=None, extra=''):
    s = f' stroke="{stroke}" stroke-width="{sw}" vector-effect="non-scaling-stroke"' if stroke else ''
    d = f' stroke-dasharray="{dash}"' if dash else ''
    return f'<rect x="{f2(x)}" y="{f2(y)}" width="{f2(w)}" height="{f2(h)}" fill="{fill}"{s}{d}{extra}/>'


def dim_h(x1, x2, y, label, col, k, above=True):
    t = 4 / k; fs = 11 / k
    ty = y - 6 / k if above else y + 15 / k
    return (_ln(x1, y, x2, y, col) + _ln(x1, y - t, x1, y + t, col) + _ln(x2, y - t, x2, y + t, col) +
            _t((x1 + x2) / 2, ty, label, fs, col, 'middle'))


def dim_v(x, y1, y2, label, col, k, side='left'):
    t = 4 / k; fs = 11 / k
    tx = x - 7 / k if side == 'left' else x + 7 / k
    return (_ln(x, y1, x, y2, col) + _ln(x - t, y1, x + t, y1, col) + _ln(x - t, y2, x + t, y2, col) +
            _t(tx, (y1 + y2) / 2 + 4 / k, label, fs, col, 'end' if side == 'left' else 'start'))


# ------------------------------------------------------------------ diagrams
def _frame(w_u, h_u, width_px, max_h, L, R, Tm, B):
    """scale k (px per unit) so content w_u×h_u plus pixel margins fits width_px (and max_h)"""
    k = (width_px - L - R) / w_u
    if max_h: k = min(k, (max_h - Tm - B) / h_u)
    return k


def _svg(vx0, vy0, vw, vh, k, body):
    return (f'<svg viewBox="{f2(vx0)} {f2(vy0)} {f2(vw)} {f2(vh)}" width="{f2(vw * k)}" height="{f2(vh * k)}" '
            f'aria-hidden="true" style="overflow:visible">{body}</svg>')


def zone_svg(c, lk, variant, width_px, unit, ground, label='X', show_cap=True, max_h=None):
    """clear-space diagram: textured zone of `unit` around the lockup box, unit boxes on each side, cap guides."""
    x0, y0, x1, y1 = lk.bbox
    u = unit
    zx0, zy0, zx1, zy1 = x0 - u, y0 - u, x1 + u, y1 + u
    L, R, Tm, B = (54 if show_cap else 14), 50, 34, 12
    k = _frame(zx1 - zx0, zy1 - zy0, width_px, max_h, L, R, Tm, B)
    vx0, vy0 = zx0 - L / k, zy0 - Tm / k
    vw, vh = (zx1 - zx0) + (L + R) / k, (zy1 - zy0) + (Tm + B) / k
    brand = T(c, 'text-brand'); meas = T(c, 'text-secondary'); soft = mix(ground, T(c, 'brand-primary'), 0.18)
    hid = uid('h')
    out = [f'<defs>{texture(c, hid, mix(ground, brand, 0.45), mix(ground, soft, 0.5), k)}</defs>',
           _rect(zx0, zy0, zx1 - zx0, zy1 - zy0, f'url(#{hid})'), _rect(x0, y0, x1 - x0, y1 - y0, ground),
           _rect(zx0, zy0, zx1 - zx0, zy1 - zy0, 'none', brand, 1.25, '6 4'),
           lk.body(variant, uid('c'), ids=False),
           _rect(x0, y0, x1 - x0, y1 - y0, 'none', meas, 0.75, '2 3')]
    fs = 11 / k
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    for bx, by in ((zx0, cy - u / 2), (x1, cy - u / 2), (cx - u / 2, zy0), (cx - u / 2, y1)):
        out.append(_rect(bx, by, u, u, mix(ground, '#FFFFFF', 0.4), brand, 1))
        out.append(_t(bx + u / 2, by + u / 2 + fs * 0.36, label, fs, brand, 'middle'))
    out.append(dim_h(zx0, x0, zy0 - 12 / k, f'1{label}', brand, k))
    out.append(dim_v(zx1 + 12 / k, zy0, y0, f'1{label}', brand, k, side='right'))
    if show_cap:
        it = next((i for i in lk.items if i.part.role in ('name', 'lettering')), None)
        cl = cap_lines(it) if it else None
        if cl:
            ct, bl = cl
            out.append(_ln(zx0 - 4 / k, ct, zx1, ct, brand, 0.75, '1 3'))
            out.append(_ln(zx0 - 4 / k, bl, zx1, bl, brand, 0.75, '1 3'))
            bx = zx0 - 18 / k
            out.append(_ln(bx, ct, bx, bl, brand, 1.25))
            out.append(_ln(bx - 3 / k, ct, bx + 3 / k, ct, brand, 1.25) + _ln(bx - 3 / k, bl, bx + 3 / k, bl, brand, 1.25))
            out.append(_t(bx - 8 / k, (ct + bl) / 2 + fs * 0.36, 'X', fs * 1.1, brand, 'end'))
    return _svg(vx0, vy0, vw, vh, k, ''.join(out))


def construction_svg(c, lk, width_px, ground, max_h=None):
    """lockup construction: mark height, gap, cap height in X on an X/2 grid; optical-centre axis."""
    items = lk.items
    m = next((i for i in items if i.part.role in ('symbol', 'monogram')), None)
    txt = [i for i in items if i.part.role in ('name', 'lettering', 'descriptor', 'local')]
    x0, y0, x1, y1 = lk.bbox
    w, h = x1 - x0, y1 - y0
    horizontal = bool(m and txt and m.bbox[2] <= items_bbox(txt)[0] + 1e-6)
    L, R, Tm, B = 78, (128 if horizontal else 56), (34 if horizontal else 40), 40
    k = _frame(w, h, width_px, max_h, L, R, Tm, B)
    vx0, vy0 = x0 - L / k, y0 - Tm / k
    vw, vh = w + (L + R) / k, h + (Tm + B) / k
    brand = T(c, 'text-brand'); meas = T(c, 'text-secondary'); grid = mix(ground, T(c, 'text-primary'), 0.09)
    g = X / 2
    lines = []
    yy = math.ceil((y0 - 0.5 * X) / g) * g
    while yy <= y1 + 0.5 * X:
        lines.append(f'M{f2(x0 - 0.5 * X)} {f2(yy)}H{f2(x1 + 0.5 * X)}'); yy += g
    xx = math.ceil((x0 - 0.5 * X) / g) * g
    while xx <= x1 + 0.5 * X:
        lines.append(f'M{f2(xx)} {f2(y0 - 0.5 * X)}V{f2(y1 + 0.5 * X)}'); xx += g
    out = [f'<path d="{"".join(lines)}" stroke="{grid}" stroke-width="1" vector-effect="non-scaling-stroke" fill="none"/>',
           lk.body('color', uid('k'), ids=False)]
    fs = 11 / k
    if m is not None and txt:
        mb = m.bbox
        tb = items_bbox(txt)
        ocx, ocy = m.oc
        out.append(dim_v(mb[0] - 16 / k, mb[1], mb[3], f'{(mb[3] - mb[1]) / X:.2f}X', meas, k))
        if horizontal:
            out.append(_ln(mb[0] - 4 / k, ocy, x1 + 34 / k, ocy, brand, 1, '5 4'))
            out.append(_t(x1 + 38 / k, ocy - 2 / k, 'optical', fs, brand))
            out.append(_t(x1 + 38 / k, ocy + 11 / k, 'centre', fs, brand))
            out.append(dim_h(mb[2], tb[0], y1 + 20 / k, f'{(tb[0] - mb[2]) / X:.2f}X', meas, k, above=False))
        else:
            out.append(_ln(ocx, y0 - 22 / k, ocx, y1 + 8 / k, brand, 1, '5 4'))
            out.append(_t(ocx + 8 / k, y0 - 12 / k, 'optical axis', fs, brand))
            gx = min(mb[0], tb[0]) - 16 / k
            if tb[1] - mb[3] > 0:
                out.append(dim_v(gx if tb[0] < mb[0] else mb[0] - 16 / k, mb[3], tb[1], f'{(tb[1] - mb[3]) / X:.2f}X', meas, k))
        out.append(f'<circle cx="{f2(ocx)}" cy="{f2(ocy)}" r="{f2(6 / k)}" fill="none" stroke="{ground}" stroke-width="4" vector-effect="non-scaling-stroke"/>'
                   f'<circle cx="{f2(ocx)}" cy="{f2(ocy)}" r="{f2(6 / k)}" fill="none" stroke="{brand}" stroke-width="1.5" vector-effect="non-scaling-stroke"/>')
    t0 = next((i for i in txt if i.part.role in ('name', 'lettering')), None)
    if t0 is not None:
        cl = cap_lines(t0)
        if cl:
            ct, bl = cl
            out.append(_ln(t0.bbox[0], ct, t0.bbox[2], ct, brand, 0.75, '1 3'))
            out.append(_ln(t0.bbox[0], bl, t0.bbox[2], bl, brand, 0.75, '1 3'))
            if horizontal:
                xr = t0.bbox[2] + 12 / k
                out.append(_ln(xr, ct, xr, bl, brand, 1.25) + _ln(xr - 3 / k, ct, xr + 3 / k, ct, brand, 1.25) + _ln(xr - 3 / k, bl, xr + 3 / k, bl, brand, 1.25))
                out.append(_t(xr, ct - 7 / k, 'X', fs, brand, 'middle'))
            else:
                xr = t0.bbox[0] - 10 / k
                out.append(_ln(xr, ct, xr, bl, brand, 1.25))
                out.append(_t(xr - 5 / k, (ct + bl) / 2 + 4 / k, 'X', fs, brand, 'end'))
    return _svg(vx0, vy0, vw, vh, k, ''.join(out))


def mark_grid_svg(c, part, variant, width_px, ground, title_oc=True):
    """the mark on a 12-module grid with its bounding box, box centre (+) and optical centre (◎)"""
    x0, y0, x1, y1 = part.box
    w, h = x1 - x0, y1 - y0
    side = max(w, h) * 1.24
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    vx0, vy0 = cx - side / 2, cy - side / 2
    k = width_px / side
    step = max(w, h) / 12
    brand = T(c, 'text-brand'); meas = T(c, 'text-secondary'); grid = mix(ground, T(c, 'text-primary'), 0.12)
    lines = []
    gx = x0 - math.floor((x0 - vx0) / step) * step
    while gx <= vx0 + side + 1e-6:
        lines.append(f'M{f2(gx)} {f2(vy0)}V{f2(vy0 + side)}'); gx += step
    gy = y0 - math.floor((y0 - vy0) / step) * step
    while gy <= vy0 + side + 1e-6:
        lines.append(f'M{f2(vx0)} {f2(gy)}H{f2(vx0 + side)}'); gy += step
    ox, oy = part.oc
    a = 7 / k
    out = [f'<path d="{"".join(lines)}" stroke="{grid}" stroke-width="1" vector-effect="non-scaling-stroke" fill="none"/>',
           f'<g>{prefix_ids(part.inner(variant), uid("g"))}</g>',
           _rect(x0, y0, w, h, 'none', meas, 1, '3 3'),
           _ln(vx0, oy, vx0 + side, oy, brand, 1), _ln(ox, vy0, ox, vy0 + side, brand, 1),
           _ln(cx - a, cy, cx + a, cy, meas, 1.5) + _ln(cx, cy - a, cx, cy + a, meas, 1.5),
           f'<circle cx="{f2(ox)}" cy="{f2(oy)}" r="{f2(8 / k)}" fill="none" stroke="{ground}" stroke-width="5" vector-effect="non-scaling-stroke"/>',
           f'<circle cx="{f2(ox)}" cy="{f2(oy)}" r="{f2(8 / k)}" fill="none" stroke="{brand}" stroke-width="2" vector-effect="non-scaling-stroke"/>',
           f'<circle cx="{f2(ox)}" cy="{f2(oy)}" r="{f2(2.5 / k)}" fill="{brand}"/>']
    return f'<svg viewBox="{f2(vx0)} {f2(vy0)} {f2(side)} {f2(side)}" width="{f2(width_px)}" height="{f2(width_px)}" aria-hidden="true">{"".join(out)}</svg>'


def lettering_metrics_svg(c, lk, width_px, ground):
    """wordmark construction: cap line, x-height and baseline across the lettering"""
    it = lk.items[0]
    p = it.part
    x0, y0, x1, y1 = lk.bbox
    pad = 0.7 * X
    vx0, vy0, vw, vh = x0 - pad, y0 - pad, (x1 - x0) + 2 * pad, (y1 - y0) + 2 * pad
    k = width_px / vw
    brand = T(c, 'text-brand'); meas = T(c, 'text-secondary')
    out = [lk.body('color', uid('w'), ids=False)]
    cl = cap_lines(it)
    glyphs = split_glyphs(p.inner('color'))
    if cl:
        ct, bl = cl
        hs = sorted((g[0][3] - g[0][1]) for g in glyphs)
        xh = None
        short = [g for g in glyphs if (g[0][3] - g[0][1]) < 0.85 * p.cap and abs(g[0][3] - p.meta.get('base', g[0][3])) < 0.04 * p.cap]
        if short:
            tops = sorted(it.to(0, g[0][1])[1] for g in short)
            xh = tops[len(tops) // 2]
        for y, lab in ((ct, 'cap height'), (bl, 'baseline')) + (((xh, 'x-height'),) if xh else ()):
            out.append(_ln(vx0 + 6 / k, y, vx0 + vw - 6 / k, y, brand if lab != 'x-height' else meas, 0.9, '4 3'))
            out.append(_t(vx0 + vw - 8 / k, y - 6 / k, lab, 11 / k, brand if lab != 'x-height' else meas, 'end'))
        out.append(dim_v(x0 - 18 / k, ct, bl, 'X', brand, k))
        if xh:
            out.append(dim_v(x1 + 18 / k, xh, bl, f'{(bl - xh) / X:.2f}X', meas, k, side='right'))
    return f'<svg viewBox="{f2(vx0)} {f2(vy0)} {f2(vw)} {f2(vh)}" width="{f2(width_px)}" height="{f2(vh * k)}" aria-hidden="true">{"".join(out)}</svg>'


def fit_lockup(lk, variant, pw, ph, wf=0.68, hf=0.52, pfx=None, wrap=''):
    """lockup group fitted into a pw×ph panel (centred). Returns (svg group, (gx, gy, k))."""
    x0, y0, x1, y1 = lk.bbox
    k = min(wf * pw / (x1 - x0), hf * ph / (y1 - y0))
    gx = (pw - (x1 - x0) * k) / 2; gy = (ph - (y1 - y0) * k) / 2
    body = lk.body(variant, pfx or uid('f'), ids=False)
    return f'<g transform="translate({f2(gx)} {f2(gy)}) scale({k:.6f}) translate({f2(-x0)} {f2(-y0)})"{wrap}>{body}</g>', (gx, gy, k)


def xbadge(c, x, y, s=22):
    style, ang = corner_style(c.b)
    col = T(c, 'error', '#C62828')
    if style == 'round':
        shape = f'<circle cx="{f2(x + s / 2)}" cy="{f2(y + s / 2)}" r="{f2(s / 2)}" fill="{col}"/>'
    elif style == 'cut':
        cc = s * 0.28
        shape = f'<polygon points="{f2(x)},{f2(y)} {f2(x + s)},{f2(y)} {f2(x + s)},{f2(y + s - cc)} {f2(x + s - cc)},{f2(y + s)} {f2(x)},{f2(y + s)}" fill="{col}"/>'
    else:
        shape = f'<rect x="{f2(x)}" y="{f2(y)}" width="{s}" height="{s}" rx="{f2(s * 0.24)}" fill="{col}"/>'
    i = s * 0.3
    return (shape + f'<path d="M{f2(x + i)} {f2(y + i)}L{f2(x + s - i)} {f2(y + s - i)}M{f2(x + s - i)} {f2(y + i)}L{f2(x + i)} {f2(y + s - i)}" '
                    f'stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round"/>')


# ------------------------------------------------------------------ 01 clear space
def page_clear_space(c):
    b, p = c.b, c.b.p
    prim = lk_by(c, c.primary)
    ground = T(c, 'surface', '#FFFFFF')
    pct = c.rules['clear_pct']
    second = next((l for l in c.lockups if l.kind == 'lockup' and l.name != c.primary and abs(math.log(l.aspect / prim.aspect)) > 0.5), None)
    sym = next((l for l in c.lockups if l.kind == 'symbol' and l.name in ('symbol',)), None) or next((l for l in c.lockups if l.kind in ('symbol', 'compact')), None)
    wide = prim.aspect >= 1.4
    big_w = 1456 - 56 if not wide else 880 - 56
    zone1 = zone_svg(c, prim, 'color', big_w, X, ground, max_h=520)
    blocks = [f'<div class="{panel_cls(c, "s12" if not wide else "s8")}"><div class="lgs-stage" style="min-height:420px">{zone1}</div>'
              f'<div class="lgs-meta"><span class="{p}-label">{esc(prim.title)} — 1X on every side</span>'
              f'<span class="{p}-label lgs-x">X = cap height · measured from the logo box</span></div></div>']
    if sym:
        unit = c.clear[sym.name]
        side_w = 340 if wide else 420
        zs = zone_svg(c, sym, 'color', side_w, unit, ground, label='C', show_cap=False, max_h=420)
        blocks.append(f'<div class="{panel_cls(c, "s4" if wide else "s5")}"><div class="lgs-stage">{zs}</div>'
                      f'<div class="lgs-meta"><span class="{p}-label">{esc(sym.title)} alone</span><span class="{p}-label lgs-x">C = {pct}% of the shorter side</span></div></div>')
    if second:
        w2 = 640 if not wide or not sym else 880 - 56
        z2 = zone_svg(c, second, 'color', w2, X, ground, max_h=360)
        span = 's7' if not wide else 's8'
        blocks.append(f'<div class="{panel_cls(c, span)}"><div class="lgs-stage">{z2}</div>'
                      f'<div class="lgs-meta"><span class="{p}-label">{esc(second.title)}</span><span class="{p}-label lgs-x">same rule, every lockup</span></div></div>')
    rules = ['Other logos, partner marks, badges and seals', 'Text, captions, URLs, hashtags', 'Frame edges, folds, trims and UI chrome',
             'Busy image detail — use a calm area, a solid panel or a scrim']
    blocks.append(f'<div class="{panel_cls(c, "s4 is-alt" if (wide and second) else "s12 is-alt" if not second else "s5 is-alt")}">'
                  f'<h2 class="{p}-h3">What may not enter the clear space</h2><ul class="lgs-list {p}-body">'
                  + ''.join(f'<li>{esc(r)}</li>' for r in rules) +
                  f'</ul><p class="{p}-caption" style="margin-top:auto">Partner lockups: 2X apart, divided by a hairline. Avatars, app icons and favicons carry their own padding.</p></div>')
    body = (f'<main class="lgs">{header(c, "01", "Clear space", f"Keep <strong>1X</strong> free on every side of a lockup — X is the cap height of the {"lettering" if b.logo_type in ("combination", "wordmark") else "name"}. The mark alone keeps <strong>{pct}%</strong> of its shorter side.")}'
            f'<section class="lgs-sec"><div class="lgs-grid">{"".join(blocks)}</div></section>{footer(c, "LOGO/GUIDES/clear-space.html")}</main>')
    return page(c, 'Logo clear space', body, 'LOGO/GUIDES')


# ------------------------------------------------------------------ 02 minimum sizes (real pixels)
def page_min_sizes(c):
    b, p, ink = c.b, c.b.p, c.ink
    rows = []
    sq_name = 'compact' if b.logo_type == 'wordmark' else 'symbol'
    tiles = []
    for ground_cls, v in (('is-paper', 'color'), ('is-dark', 'on-dark')):
        cells = []
        for s in (16, 24, 32, 48, 64):
            simple = s < c.rules['master_px'] and b.logo_type != 'wordmark'
            if b.logo_type == 'wordmark':
                src = f'../LOCKUPS/{c.slug}-compact-{v}.svg'
            else:
                src = f'../PNG/{c.slug}-symbol-{v}-{s}.png' if s in (16, 32, 48, 64) else f'../LOCKUPS/{c.slug}-symbol-{v}.svg'
                if simple and s not in (16, 32, 48): src = f'_compact-{v}.svg'
            cells.append(f'<figure style="margin:0;display:grid;justify-items:center;gap:10px"><div style="height:64px;display:flex;align-items:center">'
                         f'<img src="{src}" alt="" width="{s}" height="{s}" style="width:{s}px;height:{s}px;object-fit:contain"></div>'
                         f'<figcaption class="{p}-label lgs-num">{s} px{" · simplified" if simple else ""}</figcaption></figure>')
        tiles.append(f'<div class="{panel_cls(c, "s6 " + ground_cls)}"><div style="display:flex;justify-content:space-around;align-items:end;padding:18px 0 6px">{"".join(cells)}</div></div>')
    trs = []
    for l in c.lockups:
        mn = c.mins[l.name]
        f = c.files[l.name]['color']['svg']
        src = '../' + f.split('LOGO/', 1)[1]
        if mn['measure'] == 'width':
            wpx = mn['px']; hpx = wpx / l.aspect
            meas = f'{mn["px"]} px wide · {mn["mm"]} mm'
        else:
            hpx = mn['px']; wpx = hpx * l.aspect
            meas = f'{mn["px"]} px tall · {mn["mm"]} mm' + (f' (simplified below {mn.get("master_px", 48)} px)' if b.logo_type != 'wordmark' else '')
        trs.append(f'<tr><td class="{p}-label" style="width:260px">{esc(l.title)}</td><td class="{p}-data lgs-num" style="width:300px">{esc(meas)}</td>'
                   f'<td><div style="display:inline-grid;gap:7px;padding:6px 0"><img src="{src}" alt="{esc(l.title)} at minimum size" style="width:{f2(wpx)}px;height:{f2(hpx)}px">'
                   f'<span style="display:block;height:1px;width:{f2(wpx)}px;background:var(--color-text-brand)"></span></div></td></tr>')
    tail = (f'the compact mark carries the brand down to <strong>{c.rules["compact_px"]} px</strong>.' if b.logo_type == 'wordmark' else
            f'the mark switches to its simplified drawing below <strong>{c.rules["master_px"]} px</strong> and stops at <strong>{c.rules["compact_px"]} px</strong>.')
    lead = (f'Shown at actual size (1 CSS px = 1 device px). Lockups never go below <strong>{c.rules["lockup_px"]} px / {c.rules["lockup_mm"]} mm</strong> wide; ' + tail)
    body = (f'<main class="lgs">{header(c, "02", "Minimum sizes", lead)}'
            f'<section class="lgs-sec"><div class="lgs-sec-hd"><h2 class="{p}-h3">{"Compact mark" if b.logo_type == "wordmark" else "Mark"} at small sizes</h2>'
            f'<span class="{p}-label">16 · 24 · 32 · 48 · 64 px</span></div><div class="lgs-grid">{"".join(tiles)}</div></section>'
            f'<section class="lgs-sec"><div class="lgs-sec-hd"><h2 class="{p}-h3">Lockups at their minimum</h2><span class="{p}-label">screen · print (≈{c.rules["lockup_px"] // max(c.rules["lockup_mm"], 1)} px per mm)</span></div>'
            f'<div class="{panel_cls(c)}"><table class="lgs-tbl"><thead><tr><th class="{p}-label">Lockup</th><th class="{p}-label">Minimum</th><th class="{p}-label">Actual size</th></tr></thead>'
            f'<tbody>{"".join(trs)}</tbody></table></div></section>{footer(c, "LOGO/GUIDES/minimum-sizes.html", "Below the minimum, switch lockup — never shrink past it")}</main>')
    return page(c, 'Logo minimum sizes', body, 'LOGO/GUIDES')


# ------------------------------------------------------------------ 03 construction
def page_construction(c):
    b, p = c.b, c.b.p
    ground = T(c, 'surface', '#FFFFFF')
    prim = lk_by(c, c.primary)
    blocks = []
    if b.logo_type == 'wordmark':
        let = lk_by(c, 'wordmark')
        blocks.append(f'<div class="{panel_cls(c, "s12")}"><div class="lgs-stage">{lettering_metrics_svg(c, let, 1340, ground)}</div>'
                      f'<div class="lgs-meta"><span class="{p}-label">Lettering metrics — traced from the artwork, never re-typeset</span>'
                      f'<span class="{p}-label lgs-x">X = cap height = 100 units in every lockup file</span></div></div>')
        cl = c.compact_lockup
        part = c.parts['compact']
        blocks.append(f'<div class="{panel_cls(c, "s5")}"><div class="lgs-stage">{mark_grid_svg(c, part, "color", 420, ground)}</div>'
                      f'<div class="lgs-meta"><span class="{p}-label">Monogram — traced first letter · <span style="color:var(--color-text-brand)">◎</span> centre</span><span class="{p}-label lgs-x">12-module grid</span></div></div>')
        cont = cl.inline('color', uid('cc'), style='width:300px;height:300px')
        blocks.append(f'<div class="{panel_cls(c, "s3")}"><div class="lgs-stage">{cont}</div><div class="lgs-meta"><span class="{p}-label">Container</span>'
                      f'<span class="{p}-label lgs-x">{esc(cl.shape_name)}</span></div></div>')
        wd = lk_by(c, 'wordmark-descriptor')
        if wd:
            blocks.append(f'<div class="{panel_cls(c, "s4")}"><div class="lgs-stage">{construction_svg(c, wd, 420, ground)}</div>'
                          f'<div class="lgs-meta"><span class="{p}-label">Wordmark + descriptor</span><span class="{p}-label lgs-x">gap {wd.notes.get("descriptor_gap", 0):.2f}X · cap {wd.notes.get("descriptor_cap", 0):.2f}X</span></div></div>')
    else:
        part = c.parts['mark']
        oc = (b.mark or {}).get('optical_center') or [0.5, 0.5]
        blocks.append(f'<div class="{panel_cls(c, "s5")}"><div class="lgs-stage">{mark_grid_svg(c, part, "color", 470, ground)}</div>'
                      f'<div class="lgs-meta"><span class="{p}-label">Mark on a 12-module grid · <span style="color:var(--color-text-brand)">◎ optical centre</span> · + box centre</span><span class="{p}-label lgs-x lgs-num">{oc[0]:.3f} · {oc[1]:.3f}</span></div></div>')
        blocks.append(f'<div class="{panel_cls(c, "s7")}"><div class="lgs-stage">{construction_svg(c, prim, 780, ground, max_h=470)}</div>'
                      f'<div class="lgs-meta"><span class="{p}-label">{esc(prim.title)} — construction in X</span><span class="{p}-label lgs-x">text block centred on the optical centre</span></div></div>')
        others = [l for l in c.lockups if l.kind == 'lockup' and l.name != c.primary][:3]
        osp, ow = {1: ('s12', 900), 2: ('s6', 620)}.get(len(others), ('s4', 420))
        for l in others:
            blocks.append(f'<div class="{panel_cls(c, osp)}"><div class="lgs-stage">{construction_svg(c, l, ow, ground, max_h=300)}</div>'
                          f'<div class="lgs-meta"><span class="{p}-label">{esc(l.title)}</span><span class="{p}-label lgs-x lgs-num">{l.aspect:.2f} : 1</span></div></div>')
    # proportions table
    trs = []
    for l in c.lockups:
        n = l.notes
        cells = [f'{n["mark_h"]:.2f}X' if 'mark_h' in n else '—', f'{n["gap"]:.2f}X' if 'gap' in n else '—',
                 f'{n["lettering_h"]:.2f}X' if 'lettering_h' in n else ('1X cap' + (f' · {n["lines"]} lines' if n.get('lines', 1) > 1 else '') if l.kind == 'lockup' else '—'),
                 f'{l.aspect:.2f} : 1']
        trs.append(f'<tr><td class="{p}-label">{esc(l.title)}</td>' + ''.join(f'<td class="{p}-data lgs-num">{x}</td>' for x in cells) + '</tr>')
    blocks.append(f'<div class="{panel_cls(c, "s12")}"><table class="lgs-tbl"><thead><tr><th class="{p}-label">Lockup</th><th class="{p}-label">Mark height</th>'
                  f'<th class="{p}-label">Gap</th><th class="{p}-label">Lettering / name</th><th class="{p}-label">Aspect</th></tr></thead><tbody>{"".join(trs)}</tbody></table></div>')
    lt = b.logo_type
    lead = {'combination': 'Every alternate keeps the measured relationship of the original: the same symbol-to-lettering scale and the same gap. Text aligns to the symbol\'s optical centre, not its box.',
            'wordmark': 'The lettering is the logo. Proportions are measured from the traced artwork; the monogram sits in a container that follows the brand\'s corner grammar.',
            'emblem': 'The emblem is one unit and is never split. The typeset name sits beside or below it, sized from its cap height and centred on the emblem\'s optical centre.',
            'symbol': 'The symbol stands alone; the typeset name is sized from its cap height and aligned to the symbol\'s optical centre, not its bounding box.'}.get(lt, '')
    body = (f'<main class="lgs">{header(c, "03", "Construction", lead)}<section class="lgs-sec"><div class="lgs-grid">{"".join(blocks)}</div></section>'
            f'{footer(c, "LOGO/GUIDES/construction.html")}</main>')
    return page(c, 'Logo construction', body, 'LOGO/GUIDES')


# ------------------------------------------------------------------ 04 misuse
def _lockup_items_svg(lk, variant, pfx, filt_role=None, filt=''):
    out = []
    for k, it in enumerate(lk.items):
        g = it.svg(variant, f'{pfx}{k}')
        if filt_role and it.part.role in filt_role:
            g = f'<g filter="url(#{filt})">{g}</g>'
        out.append(g)
    return ''.join(out)


def misuse_cells(c):
    """(defs, [(key, figure html)]) — the twelve don'ts, each an inline SVG that scales to its column"""
    b, p, ink = c.b, c.b.p, c.ink
    lk = lk_by(c, c.primary)
    if lk.aspect < 1.4:      # tall primary: demonstrate on the wide lockup so the cells stay readable
        wide = [l for l in c.lockups if l.kind == 'lockup' and 1.6 <= l.aspect <= 5.5]
        if wide: lk = min(wide, key=lambda l: abs(math.log(l.aspect / 2.8)))
    wm = b.logo_type == 'wordmark'
    pw, ph = 332, 206
    ground = T(c, 'surface', '#FFFFFF')
    fam = {f['role']: f for f in b.config.get('fonts', {}).get('families', [])}
    disp_serif = 'serif' in (fam.get('display', {}).get('category') or '') and 'sans' not in (fam.get('display', {}).get('category') or '')
    wrong_font = "Georgia, 'Times New Roman', serif" if not disp_serif else "Arial, Helvetica, sans-serif"
    traced = b.logo_type in ('combination', 'wordmark')
    cases = [
        ('stretch', 'Don’t stretch or squash', 'Scale proportionally — lock the aspect ratio.'),
        ('rotate', 'Don’t rotate or tilt', 'The logo always sits level.'),
        ('recolour', 'Don’t recolour', 'Only the supplied colourways.'),
        ('effects', 'Don’t add effects', 'No shadows, glows, bevels or gradients.'),
        ('outline', 'Don’t outline', 'Solid shapes only — no keylines.'),
        ('busy', 'Don’t use busy backgrounds', 'Use a calm area, a solid panel or a scrim.'),
        ('lowcontrast', 'Don’t use the light-ground version on dark', 'On dark grounds use the on-dark files.'),
        ('onprimary', 'Don’t put the colour logo on the primary', f'On primary fields use one-colour {"white" if ink.on_primary_variant == "white" else "foundation"}.'),
        ('retype', 'Don’t re-typeset the lettering' if traced else 'Don’t set the name in another font',
         'The lettering is traced artwork — never live type.' if traced else 'The name is supplied as outlined artwork.'),
        ('rearrange', 'Don’t break the lettering' if wm else 'Don’t rearrange the lockup',
         'Keep the words on one line, as drawn.' if wm else 'Use the supplied lockups as they are.'),
        ('respace' if wm else 'proportion', 'Don’t re-space the letters' if wm else 'Don’t change the proportions',
         'Spacing is part of the drawing.' if wm else 'The mark-to-name ratio is fixed.'),
        ('crowd', 'Don’t crowd the clear space', 'Keep 1X free on every side.'),
    ]
    cells = []
    defs = ('<filter id="mu-hue" color-interpolation-filters="sRGB"><feColorMatrix type="hueRotate" values="150"/></filter>'
            '<filter id="mu-fx" x="-20%" y="-30%" width="140%" height="170%"><feDropShadow dx="5" dy="8" stdDeviation="5" flood-color="#000" flood-opacity=".45"/>'
            f'<feDropShadow dx="0" dy="0" stdDeviation="7" flood-color="{ink.A}" flood-opacity=".9"/></filter>'
            f'<filter id="mu-busy" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".022 .05" numOctaves="3" seed="11"/>'
            f'<feColorMatrix type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -2.2 1.6"/><feComposite in2="SourceGraphic" operator="in"/></filter>')
    busy_cols = [ink.P, ink.A, ink.F, mix(ink.P, '#FFFFFF', .5)]
    for idx, (key, title, why) in enumerate(cases):
        pre = uid('m')
        bg = ground
        content = ''
        if key == 'lowcontrast': bg = ink.dark
        if key == 'onprimary': bg = ink.P
        base, (gx, gy, k) = fit_lockup(lk, 'color', pw, ph, pfx=pre)
        x0, y0, x1, y1 = lk.bbox
        cxp, cyp = pw / 2, ph / 2
        if key == 'stretch':
            content = f'<g transform="translate({cxp} {cyp}) scale(1.32 0.7) translate({-cxp} {-cyp})">{base}</g>'
        elif key == 'rotate':
            content = f'<g transform="rotate(-13 {cxp} {cyp})">{base}</g>'
        elif key == 'recolour':
            inner = _lockup_items_svg(lk, 'color', pre, filt_role=('symbol', 'lettering') if not wm else ('lettering',), filt='mu-hue')
            content = f'<g transform="translate({f2(gx)} {f2(gy)}) scale({k:.6f}) translate({f2(-x0)} {f2(-y0)})">{inner}</g>'
        elif key == 'effects':
            content = f'<g filter="url(#mu-fx)">{base}</g>'
        elif key == 'outline':
            content = f'<g class="lgs-outline">{base}</g>'
        elif key == 'busy':
            stripes = ''.join(f'<rect x="{-40 + i * 46}" y="-60" width="30" height="{ph + 120}" fill="{busy_cols[i % len(busy_cols)]}" transform="rotate(22 {cxp} {cyp})"/>' for i in range(12))
            dots = ''.join(f'<circle cx="{(i * 53) % pw}" cy="{(i * 37) % ph}" r="{6 + (i * 7) % 14}" fill="{busy_cols[(i + 1) % len(busy_cols)]}" opacity=".85"/>' for i in range(26))
            content = f'<g>{stripes}{dots}<rect width="{pw}" height="{ph}" fill="{ink.PA}" filter="url(#mu-busy)" opacity=".55"/></g>{base}'
        elif key in ('lowcontrast', 'onprimary'):
            content = base
        elif key == 'retype':
            txt_items = [i for i in lk.items if i.part.role in ('lettering', 'name')]
            keep = [i for i in lk.items if i not in txt_items and i.part.role not in ('descriptor', 'local')]
            tb = items_bbox(txt_items)
            word = b.name
            fam_css = 'var(--font-display)' if traced else wrong_font
            words = word.split()
            nrows = max(1, min(len(words), (txt_items[0].part.meta.get('rows') or 1) if traced else len([i for i in txt_items if i.part.role == 'name'])))
            per = math.ceil(len(words) / nrows)
            rows = [' '.join(words[i:i + per]) for i in range(0, len(words), per)]
            cfg_lines = (b.config.get('wordmark') or {}).get('lines') or []
            if not traced and len(cfg_lines) == nrows:
                rows = [ln.title() for ln in cfg_lines]
            longest = max(len(r) for r in rows)
            fs = min(X / 0.7, 0.98 * (tb[2] - tb[0]) / (0.5 * longest))
            lead = 1.08 * fs
            top = (tb[1] + tb[3]) / 2 - (lead * (len(rows) - 1)) / 2 + 0.36 * fs
            parts_svg = ''.join(it.svg('color', f'{pre}r{j}') for j, it in enumerate(keep))
            tcol = ink.F if not wm else (ink.P if ink.primary_ok else ink.F)
            spans = ''.join(f'<tspan x="{f2(tb[0])}" y="{f2(top + i * lead)}">{esc(r)}</tspan>' for i, r in enumerate(rows))
            text = (f'<text font-size="{f2(fs)}" fill="{tcol}" style="font-family:{fam_css};font-weight:400;letter-spacing:0">{spans}</text>')
            content = f'<g transform="translate({f2(gx)} {f2(gy)}) scale({k:.6f}) translate({f2(-x0)} {f2(-y0)})">{parts_svg}{text}</g>'
        elif key == 'rearrange':
            if wm:
                it = lk.items[0]
                glyphs = split_glyphs(it.part.inner('color'))
                gaps = [(glyphs[i + 1][0][0] - glyphs[i][0][2], i) for i in range(len(glyphs) - 1)]
                g2, cut = max(gaps) if gaps else (0, 0)
                a_, b_ = glyphs[:cut + 1], glyphs[cut + 1:]
                lh = it.part.h
                bx0 = b_[0][0][0] if b_ else 0
                ax0 = a_[0][0][0]
                grp = (f'<g>{"".join(g[1] for g in a_)}</g>'
                       f'<g transform="translate({f2(ax0 - bx0 + lh * 0.6)} {f2(lh * 1.05)})">{"".join(g[1] for g in b_)}</g>')
                wpx = max((a_[-1][0][2] - ax0), (b_[-1][0][2] - bx0 + lh * 0.6) if b_ else 0)
                hpx = lh * 2.05
                kk = min(0.6 * pw / wpx, 0.6 * ph / hpx)
                content = (f'<g transform="translate({f2((pw - wpx * kk) / 2)} {f2((ph - hpx * kk) / 2)}) scale({kk:.6f}) translate({f2(-ax0)} {f2(-it.part.box[1])})">'
                           f'{prefix_ids(grp, pre)}</g>')
            else:
                mk = [i for i in lk.items if i.part.role == 'symbol']
                tx = [i for i in lk.items if i.part.role != 'symbol']
                tb = items_bbox(tx)
                moved = []
                for j, it in enumerate(tx):
                    moved.append(Item(it.part, it.x - tb[0], it.y - tb[1], it.s))
                tw = tb[2] - tb[0]
                for j, it in enumerate(mk):
                    hh = (it.bbox[3] - it.bbox[1]) * 0.8
                    moved.append(Item(it.part, tw + 0.5 * X, 0, it.s * 0.8))
                from svgkit import Lockup as _L
                L2 = _L('x', 'x', '', moved)
                content, _ = fit_lockup(L2, 'color', pw, ph, pfx=pre)
        elif key == 'proportion':
            mk = [i for i in lk.items if i.part.role == 'symbol']
            tx = [i for i in lk.items if i.part.role != 'symbol']
            moved = [Item(i.part, i.x, i.y, i.s) for i in tx]
            for it in mk:
                s2 = it.s * 0.5
                ocx, ocy = it.oc
                n = Item(it.part, 0, 0, s2)
                n.shift(ocx - n.oc[0] + (it.bbox[2] - it.bbox[0]) * 0.25, ocy - n.oc[1])
                moved.append(n)
            from svgkit import Lockup as _L
            content, _ = fit_lockup(_L('x', 'x', '', moved), 'color', pw, ph, pfx=pre)
        elif key == 'respace':
            it = lk.items[0]
            glyphs = split_glyphs(it.part.inner('color'))
            sp = it.part.h * 0.16
            grp = ''.join(f'<g transform="translate({f2(i * sp)} 0)">{g[1]}</g>' for i, g in enumerate(glyphs))
            wpx = it.part.w + sp * (len(glyphs) - 1)
            kk = min(0.74 * pw / wpx, 0.5 * ph / it.part.h)
            content = (f'<g transform="translate({f2((pw - wpx * kk) / 2)} {f2((ph - it.part.h * kk) / 2)}) scale({kk:.6f}) translate({f2(-it.part.box[0])} {f2(-it.part.box[1])})">'
                       f'{prefix_ids(grp, pre)}</g>')
        elif key == 'crowd':
            base2, (gx2, gy2, k2) = fit_lockup(lk, 'color', pw, ph, wf=0.56, hf=0.4, pfx=pre)
            lh = (y1 - y0) * k2
            tag = (b.content.get('brand', {}) or {}).get('tagline') or b.brand.get('tagline') or b.name
            ty = gy2 + lh + 0.12 * X * k2 + 12
            content = (base2 + f'<text x="{f2(gx2)}" y="{f2(ty)}" font-size="13" fill="{ink.F}" style="font-family:var(--font-sans)">{esc(tag[:42])}</text>'
                       f'<rect x="{f2(gx2 + (x1 - x0) * k2 + 4)}" y="{f2(gy2 - 6)}" width="2" height="{f2(lh + 12)}" fill="{ink.F}"/>')
        svg = (f'<svg viewBox="0 0 {pw} {ph}" role="img" aria-label="{esc(title)}" style="display:block;width:100%;height:auto">'
               f'<rect width="{pw}" height="{ph}" fill="{bg}"/>{content}{xbadge(c, 12, 12)}</svg>')
        cells.append((key, f'<figure class="s3" style="margin:0;display:grid;gap:12px;align-content:start"><div class="{p}-shape" style="overflow:hidden;line-height:0">{svg}</div>'
                     f'<figcaption><p class="{p}-label" style="margin:0"><span style="color:{T(c, "error")}">{idx + 1:02d}</span>&nbsp; {esc(title)}</p>'
                     f'<p class="{p}-caption" style="margin:4px 0 0">{esc(why)}</p></figcaption></figure>'))
    return defs, cells


def page_misuse(c):
    p = c.b.p
    defs, cells = misuse_cells(c)
    lead = 'The logo is fixed artwork. If a layout seems to need one of these, change the layout — not the logo.'
    body = (f'<main class="lgs"><svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>{defs}</defs></svg>'
            f'{header(c, "04", "Misuse", lead)}<section class="lgs-sec"><div class="lgs-grid" style="row-gap:32px">{"".join(h for _, h in cells)}</div></section>'
            f'{footer(c, "LOGO/GUIDES/misuse.html", "✕ = never")}</main>')
    return page(c, 'Logo misuse', body, 'LOGO/GUIDES')


def build_guides(c, job):
    b = c.b
    G = lambda *a: b.path('LOGO', 'GUIDES', *a)
    # helper svg for 24 px compact tiles (render-only copies live next to the page, prefixed with _)
    if b.logo_type != 'wordmark':
        part = c.parts['compact']
        x0, y0, x1, y1 = part.box
        side = max(x1 - x0, y1 - y0); cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        for v in ('color', 'on-dark'):
            F.write(G(f'_compact-{v}.svg'), f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{f2(cx - side / 2)} {f2(cy - side / 2)} {f2(side)} {f2(side)}">'
                                            f'{prefix_ids(part.inner(v), "q")}</svg>\n')
    out = []
    for name, fn, h in (('clear-space', page_clear_space, 1100), ('minimum-sizes', page_min_sizes, 1000),
                        ('construction', page_construction, 1200), ('misuse', page_misuse, 1100)):
        F.write(G(name + '.html'), fn(c))
        job(c, G(name + '.html'), G(name + '.png'), 1600, h, transparent=False, wait=150, full=True)
        out += [name + '.html', name + '.png']
    return out


# ------------------------------------------------------------------ logo sheet
def build_sheet(c, job):
    b, p, ink = c.b, c.b.p, c.ink
    L = lambda n, v='color': c.files[n][v]['svg'].split('LOGO/', 1)[1]
    prim = lk_by(c, c.primary)
    lt = b.logo_type
    dna = b.dna or {}
    lang = dna.get('base_language', 'mixed')
    tex = {'round': f'{p}-dotgrid', 'organic': f'{p}-grain', 'angular': f'{p}-linegrid', 'orthogonal': f'{p}-linegrid'}.get(lang, '')
    kind = {'combination': 'Combination — symbol + traced lettering', 'wordmark': 'Wordmark — traced lettering',
            'emblem': 'Emblem — one closed unit, lettering inside', 'symbol': 'Symbol — typeset name beside it'}.get(lt, lt)
    n_files = sum(len(v) for v in c.files.values())
    mn = c.mins[c.primary]
    ground = T(c, 'surface', '#FFFFFF')

    def stage(src, h, alt, style=''):
        return (f'<div class="lgs-stage" style="min-height:{h}px;{style}"><img src="{src}" alt="{esc(alt)}" '
                f'style="max-height:{max(40, h - 40)}px;width:auto;max-width:84%"></div>')

    def meta(left, right=''):
        return f'<div class="lgs-meta"><span class="{p}-label">{esc(left)}</span><span class="{p}-label lgs-x">{esc(right)}</span></div>'

    def sec(idx, title, right, inner, grid=True):
        return (f'<section class="lgs-sec"><div class="lgs-sec-hd"><h2 class="{p}-h3"><span class="{p}-label" style="color:var(--color-text-brand);margin-right:14px">{idx}</span>{esc(title)}</h2>'
                f'<span class="{p}-label">{esc(right)}</span></div>' + (f'<div class="lgs-grid">{inner}</div>' if grid else inner) + '</section>')

    # 01 primary
    tall = prim.aspect < 1.3
    hero_h = 440 if not tall else 560
    on_p = ink.on_primary_variant
    side_h = (hero_h + 54 - 20) // 2 - 54
    hero = (f'<div class="{panel_cls(c, "s8 is-paper")}">{stage(L(c.primary), hero_h, prim.title, "padding:24px 0")}{meta(prim.title, "full colour · light grounds")}</div>'
            f'<div class="s4" style="display:grid;grid-template-rows:1fr 1fr;gap:20px">'
            f'<div class="{panel_cls(c, "is-dark")}">{stage(L(c.primary, "on-dark"), side_h, prim.title + " on dark")}{meta("On dark", "on-dark")}</div>'
            f'<div class="{panel_cls(c, "is-primary")}">{stage(L(c.primary, on_p), side_h, prim.title + " on primary")}{meta("On primary", "one colour " + on_p)}</div></div>')
    # 02 family on light
    fam = [l for l in c.lockups if l.name != c.primary]
    spans = {1: ['s12'], 2: ['s6', 's6'], 3: ['s4'] * 3, 4: ['s6'] * 4, 5: ['s4', 's4', 's4', 's6', 's6'], 6: ['s4'] * 6}.get(len(fam), ['s4'] * len(fam))
    cards = []
    for l, sp in zip(fam, spans):
        m = c.mins[l.name]
        h = 210 if l.aspect >= 1.6 else 260
        cards.append(f'<div class="{panel_cls(c, sp)}">{stage(L(l.name), h, l.title)}'
                     f'{meta(l.title, "min " + str(m["px"]) + " px " + ("wide" if m["measure"] == "width" else "tall"))}</div>')
    # 03 every lockup on dark and on primary (bands)
    def band(v, cls, label):
        figs = []
        for l in c.lockups:
            hh = 54 if l.aspect >= 2.2 else (78 if l.aspect >= 1.2 else 104)
            figs.append(f'<figure><img src="{L(l.name, v)}" alt="{esc(l.title)}, {esc(label)}" style="height:{hh}px;width:auto;display:block">'
                        f'<figcaption class="{p}-label lgs-x">{esc(l.title)}</figcaption></figure>')
        return f'<div class="{panel_cls(c, "s12 " + cls)}" style="padding:34px 36px 26px"><div class="lgs-band">{"".join(figs)}</div></div>'
    bands = band('on-dark', 'is-dark', 'on dark') + band(on_p, 'is-primary', 'on primary')
    # 04 colourways of the primary lockup
    vs = ink.variants()
    wspan = {4: 3, 5: None}.get(len(vs), 3)
    ways = []
    for i, v in enumerate(vs):
        cls = {'color': 'is-paper', 'on-dark': 'is-dark', 'foundation': 'is-paper', 'white': 'is-primary' if on_p == 'white' else 'is-dark', 'primary': 'is-paper'}[v]
        span = wspan or (4 if i < 3 else 6)
        lab = {'color': 'Full colour', 'on-dark': 'On dark', 'foundation': 'One colour', 'white': 'One colour white', 'primary': 'One colour primary'}[v]
        ways.append(f'<div class="{panel_cls(c, cls)}" style="grid-column:span {span}">{stage(L(c.primary, v), 170, prim.title + " " + lab)}{meta(lab, v)}</div>')
    # 05 digital
    style, _ = corner_style(b)
    rad = {'round': '22%', 'soft': '24%', 'rounded': '22%', 'square': '12%', 'cut': '22%'}.get(style, '22%')
    tabs = ''.join(
        f'<div style="display:flex;align-items:center;gap:10px;padding:11px 16px;background:{bg};color:{fg};border-radius:{"10px 10px 0 0" if style != "cut" else "0"}">'
        f'<img src="FAVICON/favicon-16.png" width="16" height="16" alt=""><span class="{p}-small" style="white-space:nowrap">{esc(b.name)}</span></div>'
        for bg, fg in ((T(c, 'background'), T(c, 'text-primary')), (ink.dark, T(c, 'text-inverse'))))
    fav_sizes = ''.join(f'<figure style="margin:0;display:grid;justify-items:center;gap:8px"><img src="FAVICON/favicon-{s}.png" width="{s}" height="{s}" alt="">'
                        f'<figcaption class="{p}-label lgs-num">{s}</figcaption></figure>' for s in (16, 32, 48))
    digital = (f'<div class="{panel_cls(c, "s4")}"><div class="lgs-stage" style="flex-direction:column;gap:24px;min-height:250px">'
               f'<div style="display:grid;gap:8px;width:100%">{tabs}</div><div style="display:flex;gap:30px;align-items:end">{fav_sizes}</div></div>'
               f'{meta("Favicon", "ICO 16/32/48 · SVG")}</div>'
               f'<div class="{panel_cls(c, "s4 is-alt")}"><div class="lgs-stage" style="gap:24px;min-height:250px">'
               f'<img src="FAVICON/apple-touch-icon.png" width="128" height="128" alt="App icon" style="border-radius:{rad}">'
               f'<img src="FAVICON/maskable-512.png" width="128" height="128" alt="Maskable icon under a circle mask" style="border-radius:50%">'
               f'<img src="FAVICON/android-chrome-192.png" width="96" height="96" alt="Icon in the brand container"></div>'
               f'{meta("App icons", "touch · maskable · " + c.icon.get("shape", ""))}</div>'
               f'<div class="{panel_cls(c, "s4")}"><div class="lgs-stage" style="gap:16px;min-height:250px">'
               + ''.join(f'<img src="AVATARS/avatar-{a["name"]}-400.png" width="104" height="104" alt="Profile image, {a["name"]}" '
                         f'style="border-radius:50%;box-shadow:0 0 0 1px var(--color-border)">' for a in c.avatars) +
               f'</div>{meta("Profile images", "circle-safe · 400 / 1080")}</div>')
    if c.compact_lockup is not None:
        digital = (f'<div class="{panel_cls(c, "s12 is-alt")}" style="flex-direction:row;align-items:center;gap:40px;padding:28px 36px">'
                   + ''.join(f'<div style="background:{ink.ground(v)};padding:18px;line-height:0" class="{p}-shape {p}-shape-sm"><img src="{L("compact", v)}" alt="Compact mark, {v}" style="width:104px;height:104px"></div>' for v in ink.variants()) +
                   f'<div style="margin-left:auto;max-width:360px"><p class="{p}-h4" style="margin:0 0 6px">Compact mark</p><p class="{p}-small lgs-lead">'
                   f'Monogram in the {esc(c.compact_lockup.shape_name)} container — avatars, app icons and favicons. Never placed next to the wordmark.</p></div></div>') + digital
    # 06 rules: clear space + minimum sizes (real px) + six don'ts
    mdefs, mis = misuse_cells(c)
    zone = zone_svg(c, prim, 'color', 700 if not tall else 560, X, ground, max_h=380)
    sq = 'compact' if lt == 'wordmark' else 'symbol'
    small = ''
    for s in (16, 24, 32, 48):
        if lt == 'wordmark':
            src = L('compact')
        else:
            src = f'PNG/{c.slug}-symbol-color-{s}.png' if s in (16, 32, 48) else f'GUIDES/_compact-color.svg'
        small += (f'<figure style="margin:0;display:grid;justify-items:center;gap:8px;align-content:end"><img src="{src}" width="{s}" height="{s}" alt="" style="object-fit:contain">'
                  f'<figcaption class="{p}-label lgs-num">{s}</figcaption></figure>')
    wpx = mn['px'] if mn['measure'] == 'width' else mn['px'] * prim.aspect
    mins = (f'<div style="display:grid;gap:30px;align-content:center;flex:1">'
            f'<div style="display:flex;gap:30px;align-items:end">{small}</div>'
            f'<div style="display:inline-grid;gap:8px;justify-items:start"><img src="{L(c.primary)}" alt="{esc(prim.title)} at its minimum" style="width:{f2(wpx)}px;height:auto">'
            f'<span style="display:block;height:1px;width:{f2(wpx)}px;background:var(--color-text-brand)"></span>'
            f'<span class="{p}-label lgs-num">{mn["px"]} px · {mn["mm"]} mm</span></div></div>')
    rules = (f'<div class="{panel_cls(c, "s8")}"><div class="lgs-stage">{zone}</div>{meta("Clear space", "1X · X = cap height")}</div>'
             f'<div class="{panel_cls(c, "s4")}">{mins}{meta("Minimum sizes", "actual pixels")}</div>'
             + ''.join(h.replace('class="s3"', 'class="s2"', 1) for k_, h in mis if k_ in ('stretch', 'rotate', 'recolour', 'effects', 'busy', 'retype')))
    facts = [('Logo type', kind), ('Unit', 'X = cap height = 100 units'), ('Clear space', f'1X · mark alone {c.rules["clear_pct"]}% of its shorter side'),
             ('Minimum', f'{mn["px"]} px / {mn["mm"]} mm wide · mark {c.rules["compact_px"]} px'),
             ('Files', f'{len(c.lockups)} lockups × {len(vs)} colourways · {n_files} SVG + PNG')]
    kv = ''.join(f'<dt class="{p}-label">{esc(k)}</dt><dd class="{p}-small">{esc(v)}</dd>' for k, v in facts)
    head = (f'<header class="lgs-hd {tex}" style="grid-template-columns:minmax(0,1fr) 560px;margin:-64px -72px 0;padding:64px 72px 30px">'
            f'<div><p class="{p}-eyebrow"><span class="{p}-index">00</span> {esc(b.name)} · Logo system</p>'
            f'<h1 class="{p}-display-l" style="margin-top:18px">Logo sheet</h1></div><dl class="lgs-kv">{kv}</dl></header>')
    body = (f'<main class="lgs"><svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>{mdefs}</defs></svg>{head}'
            + sec('01', 'Primary', 'LOGO/LOCKUPS', hero)
            + sec('02', 'Lockup family', 'same parts · fixed proportions', ''.join(cards))
            + sec('03', 'On dark · on primary', 'every lockup', bands)
            + sec('04', 'Colourways', 'LOCKUPS + MONOCHROME', ''.join(ways))
            + sec('05', 'Compact & digital', 'LOGO/FAVICON · LOGO/AVATARS', digital)
            + sec('06', 'Rules', 'LOGO/GUIDES', rules)
            + footer(c, 'LOGO/logo-sheet.html', f'Regenerate: python3 assets/modules/logo-system/build.py --repo {os.path.basename(b.repo)}') + '</main>')
    F.write(b.path('LOGO', 'logo-sheet.html'), page(c, 'Logo sheet', body, 'LOGO'))
    job(c, b.path('LOGO', 'logo-sheet.html'), b.path('LOGO', 'logo-sheet.png'), 1600, 2400, transparent=False, wait=300, full=True)
