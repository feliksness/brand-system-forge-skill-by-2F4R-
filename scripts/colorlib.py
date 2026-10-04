"""colorlib.py — small, dependency-free colour maths for brand systems.
sRGB ⇄ OKLab/OKLCH, WCAG contrast, ramps, nearest-colour, accessibility fixing."""
import math

def hex2rgb(h):
    h = h.strip().lstrip('#')
    if len(h) == 3: h = ''.join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def rgb2hex(c): return '#%02X%02X%02X' % tuple(max(0, min(255, int(round(v)))) for v in c)

def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def _delin(c):
    c = max(0.0, min(1.0, c))
    return 255.0 * (12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055)

def rel_lum(h):
    r, g, b = (_lin(v) for v in hex2rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def contrast(a, b):
    la, lb = rel_lum(a), rel_lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)

def rating(r): return 'AAA' if r >= 7 else 'AA' if r >= 4.5 else 'AA-large' if r >= 3 else 'fail'

def to_oklab(h):
    r, g, b = (_lin(v) for v in hex2rgb(h))
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l, m, s = (math.copysign(abs(v) ** (1 / 3), v) for v in (l, m, s))
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)

def from_oklab(L, A, B):
    l = (L + 0.3963377774 * A + 0.2158037573 * B) ** 3
    m = (L - 0.1055613458 * A - 0.0638541728 * B) ** 3
    s = (L - 0.0894841775 * A - 1.2914855480 * B) ** 3
    r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    b = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    return rgb2hex((_delin(r), _delin(g), _delin(b)))

def to_oklch(h):
    L, A, B = to_oklab(h); return L, math.hypot(A, B), math.degrees(math.atan2(B, A)) % 360

def from_oklch(L, C, H):
    # reduce chroma until inside sRGB
    for _ in range(40):
        A, B = C * math.cos(math.radians(H)), C * math.sin(math.radians(H))
        l = (L + 0.3963377774 * A + 0.2158037573 * B) ** 3
        m = (L - 0.1055613458 * A - 0.0638541728 * B) ** 3
        s = (L - 0.0894841775 * A - 1.2914855480 * B) ** 3
        rgb = (4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
               -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
               -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)
        if all(-0.001 <= v <= 1.001 for v in rgb): break
        C *= 0.93
    return from_oklab(L, C * math.cos(math.radians(H)), C * math.sin(math.radians(H)))

def mix(a, b, t):
    x, y = hex2rgb(a), hex2rgb(b); return rgb2hex(tuple(p + (q - p) * t for p, q in zip(x, y)))

def nearest(h, palette):
    """palette: {key: hex} → key of perceptually nearest colour (OKLab distance)."""
    L, A, B = to_oklab(h)
    return min(palette, key=lambda k: sum((p - q) ** 2 for p, q in zip((L, A, B), to_oklab(palette[k]))))

STOPS = ['50', '100', '200', '300', '400', '500', '600', '700', '800', '900', '950']
L_TARGETS = [0.975, 0.94, 0.87, 0.78, 0.69, 0.61, 0.53, 0.45, 0.37, 0.28, 0.21]

def ramp(anchor_hex, anchors=None, chroma_scale=1.0):
    """11-stop ramp (50…950) around an anchor colour, hue-stable in OKLCH.
    anchors: optional {stop: hex} sampled colours to pin (e.g. colours measured from the logo)."""
    L0, C0, H0 = to_oklch(anchor_hex)
    # place the anchor at the closest lightness stop
    out = {}
    for s, Lt in zip(STOPS, L_TARGETS):
        # chroma falls off towards the extremes
        k = 1 - min(1, abs(Lt - L0) / 0.75) ** 1.6
        out[s] = from_oklch(Lt, C0 * chroma_scale * (0.25 + 0.75 * k), H0)
    i = min(range(len(STOPS)), key=lambda i: abs(L_TARGETS[i] - L0))
    out[STOPS[i]] = anchor_hex.upper()
    for s, h in (anchors or {}).items(): out[s] = h.upper()
    return out

def neutral_ramp(foundation_hex, chroma=0.012):
    L0, C0, H0 = to_oklch(foundation_hex)
    out = {'0': '#FFFFFF'}
    for s, Lt in zip(STOPS, [0.97, 0.93, 0.84, 0.74, 0.6, 0.5, 0.42, 0.33, 0.27, 0.22, 0.17]):
        out[s] = from_oklch(Lt, min(C0, chroma) if C0 > 0.002 else 0, H0)
    return out

def adjust_for_contrast(fg, bg, target=4.5, direction=None):
    """Move fg lightness (OKLCH) away from bg until contrast(fg,bg) >= target. Returns (hex, ratio)."""
    if contrast(fg, bg) >= target: return fg.upper(), round(contrast(fg, bg), 2)
    L, C, H = to_oklch(fg)
    darker = direction == 'darker' or (direction is None and rel_lum(bg) > 0.18)
    for _ in range(200):
        L = L - 0.005 if darker else L + 0.005
        if L <= 0 or L >= 1: break
        cand = from_oklch(L, C, H)
        if contrast(cand, bg) >= target: return cand, round(contrast(cand, bg), 2)
    return ('#000000' if darker else '#FFFFFF'), round(contrast('#000000' if darker else '#FFFFFF', bg), 2)

def rgb2cmyk(h):
    r, g, b = hex2rgb(h)
    if (r, g, b) == (0, 0, 0): return [0, 0, 0, 100]
    c, m, y = 1 - r / 255, 1 - g / 255, 1 - b / 255; k = min(c, m, y)
    return [round(v * 100) for v in ((c - k) / (1 - k), (m - k) / (1 - k), (y - k) / (1 - k), k)]

def rgb2hsl(h):
    import colorsys
    r, g, b = hex2rgb(h); hh, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    return [round(hh * 360), round(s * 100), round(l * 100)]
