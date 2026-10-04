"""
recipe.py — turns the design DNA + theme colours into the UI kit's design decisions.

Everything brand-specific in <p>-ui.css flows through here:
  * shape     dna.corner.style  cut | round | soft | rounded | square   (+ dna.angles.cut, facets → two corners)
  * depth     dna.shadow_style  hard | soft | diffuse | flat
  * motion    dna.motion        snap | slide | glide | flow (+ energy)
  * density   dna.density       dense | balanced | airy
  * voice     dna.type_voice.display_case upper | title | sentence  · display font category (serif / sans)
  * motifs    dna.motifs / patterns → dividers, list markers, placeholders
  * colour    per-theme choices (light / dark / contrast) picked by WCAG contrast from the theme tokens —
              every choice is expressed as a reference to a --color-* token (or a color-mix of two tokens).
"""
import math, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', '..', 'scripts'))
import colorlib as CL  # noqa: E402

THEMES = ('light', 'dark', 'contrast')


def _hex(v):
    return isinstance(v, str) and re.fullmatch(r'#[0-9A-Fa-f]{6}', v.strip() or '') is not None


def _px(v, default=0.0):
    m = re.match(r'\s*(-?[\d.]+)', str(v or ''))
    return float(m.group(1)) if m else default


class Theme:
    """Theme token map with contrast helpers. Values that are not plain hex (rgba, …) are ignored for maths."""
    def __init__(self, name, tokens):
        self.name, self.t = name, {k: v for k, v in (tokens or {}).items()}

    def hex(self, ref):
        """ref = token name ('text-primary'), '#RRGGBB' or ('mix', a, b, t) → hex"""
        if isinstance(ref, tuple):
            _, a, b, t = ref
            return CL.mix(self.hex(a), self.hex(b), t)
        if _hex(ref):
            return ref.upper()
        v = self.t.get(ref)
        return v.upper() if _hex(v) else None

    def cr(self, a, b):
        ha, hb = self.hex(a), self.hex(b)
        return round(CL.contrast(ha, hb), 2) if ha and hb else 0.0


def css_ref(ref):
    """token name → var(--color-…) · tuple mix → color-mix(in srgb, A p%, B) · hex stays hex"""
    if isinstance(ref, tuple):
        _, a, b, t = ref
        return f'color-mix(in srgb, {css_ref(a)} {round((1 - t) * 100, 1):g}%, {css_ref(b)})'
    if _hex(ref):
        return ref
    return f'var(--color-{ref})'


def best_fg(th, bg, prefs=('text-on-brand', 'text-inverse', 'text-primary', 'background', '#FFFFFF', '#000000'), target=4.5):
    """First preferred foreground that reaches `target` on bg, else the strongest one."""
    scored = [(p, th.cr(p, bg)) for p in prefs if th.hex(p)]
    for p, c in scored:
        if c >= target:
            return p, c
    return max(scored, key=lambda x: x[1]) if scored else ('#000000', 0)


def border_mix(th, line='text-tertiary', ground=('surface', 'background'), target=3.05):
    """Lightest mix of `line` into the surface that still gives ≥3:1 against every ground (WCAG 1.4.11)."""
    base = th.hex('surface') or th.hex('background')
    if not th.hex(line) or not base:
        return line
    for t in [x / 100 for x in range(60, -1, -2)]:       # t = share of the surface colour
        ref = ('mix', line, 'surface', t)
        if all(th.cr(ref, g) >= target for g in ground if th.hex(g)):
            return ref if t > 0 else line
    return line


def font_widths(b, role='display'):
    """Mean advance of A–Z and a–z (em) of a brand font, read from its woff2 — lets wide and condensed faces get
    different sizes (button caps, hero fit). Falls back to typical values when the font cannot be read."""
    fam = next((f for f in (b.config.get('fonts') or {}).get('families', []) if f.get('role') == role), None)
    out = {'caps': 0.66, 'lower': 0.52}
    if not fam:
        return out
    d = b.path('SOURCE', 'FONTS')
    try:
        from fontTools.ttLib import TTFont
        cands = sorted(f for f in os.listdir(d) if f.startswith(fam.get('slug', '~')) and f.endswith(('.woff2', '.woff', '.ttf')) and 'italic' not in f)
        cands.sort(key=lambda f: ('latin' not in f, 'ext' in f))
        if not cands:
            return out
        ft = TTFont(os.path.join(d, cands[0]))
        if 'fvar' in ft:                                   # measure at the weight the display styles actually use
            wght = 600
            try:
                m = re.search(r'--type-h1-weight:\s*(\d+)', open(b.path('SOURCE', 'CSS', 'tokens.css'), encoding='utf-8').read())
                wght = int(m.group(1)) if m else wght
            except Exception:
                pass
            from fontTools.varLib import instancer
            ax = {a.axisTag: a for a in ft['fvar'].axes}
            loc = {'wght': max(ax['wght'].minValue, min(ax['wght'].maxValue, wght))} if 'wght' in ax else {}
            if loc:
                ft = instancer.instantiateVariableFont(ft, loc)
        cmap, hm, upm = ft.getBestCmap(), ft['hmtx'].metrics, ft['head'].unitsPerEm
        def mean(chars):
            w = [hm[cmap[ord(c)]][0] for c in chars if ord(c) in cmap and cmap[ord(c)] in hm]
            return sum(w) / len(w) / upm if w else None
        out['caps'] = round(mean('ABCDEFGHIJKLMNOPQRSTUVWXYZ') or out['caps'], 3)
        out['lower'] = round(mean('abcdefghijklmnopqrstuvwxyz') or out['lower'], 3)
    except Exception:
        pass
    return out


def build(b):
    dna = b.dna or {}
    corner = (dna.get('corner') or {}).get('style') or 'rounded'
    if corner not in ('cut', 'round', 'soft', 'rounded', 'square'):
        corner = 'rounded'
    angles = dna.get('angles') or {}
    angle = float(angles.get('cut') or (dna.get('corner') or {}).get('angle_deg') or 45)
    angle = min(75.0, max(30.0, angle))
    patterns, motifs = dna.get('patterns') or [], dna.get('motifs') or []
    facets = corner == 'cut' and ('facets' in patterns or any('facet' in m or 'crystal' in m for m in motifs))
    density = dna.get('density') or 'balanced'
    mo = dna.get('motion') or {}
    motion, energy = mo.get('character') or 'glide', float(mo.get('energy') or 0.4)
    tv = dna.get('type_voice') or {}
    case = tv.get('display_case') or 'sentence'
    shadow = dna.get('shadow_style') or ('hard' if corner in ('cut', 'square') else 'soft')
    crop = (dna.get('imagery') or {}).get('crop') or 'rect'
    stroke = dna.get('stroke') or {}
    fams = {f.get('role'): f for f in (b.config.get('fonts') or {}).get('families', [])}
    disp_cat = (fams.get('display') or {}).get('category', 'sans-serif')
    has_hand = 'hand' in fams
    has_mono = 'mono' in fams                     # a real monospace family (not the sans fallback)
    base = dna.get('base_language') or ('angular' if corner == 'cut' else 'round')
    family = ('angular' if corner in ('cut',) or base in ('angular', 'orthogonal') else
              'organic' if corner == 'soft' or base == 'organic' else 'round')
    if corner == 'square':
        family = 'angular'

    widths = font_widths(b, 'display')
    R = dict(widths=widths, corner=corner, angle=angle, facets=facets, density=density, motion=motion, energy=energy, case=case,
             shadow=shadow, crop=crop, family=family, patterns=patterns, motifs=motifs, disp_cat=disp_cat,
             has_hand=has_hand, has_mono=has_mono, stroke=stroke, base=base)

    # ------------------------------------------------------------------ theme-independent variables
    tan = math.tan(math.radians(angle))
    D = {'dense': dict(h=(34, 40, 48), px=(12, 16, 22), card='var(--space-5)', panel='var(--space-6)', header=60, gap='8px', cgap='var(--space-3)'),
         'balanced': dict(h=(38, 46, 54), px=(14, 20, 26), card='var(--space-6)', panel='var(--space-8)', header=68, gap='10px', cgap='var(--space-3)'),
         'airy': dict(h=(40, 50, 58), px=(16, 24, 30), card='var(--space-8)', panel='var(--space-10)', header=76, gap='10px', cgap='var(--space-4)')}[
        density if density in ('dense', 'balanced', 'airy') else 'balanced']
    v = {}
    v['--ui-h-sm'], v['--ui-h-md'], v['--ui-h-lg'] = (f'{x}px' for x in D['h'])
    v['--ui-hit'] = '44px'
    v['--ui-pad-x-sm'], v['--ui-pad-x'], v['--ui-pad-x-lg'] = (f'{x}px' for x in D['px'])
    v['--ui-gap'] = D['gap']
    v['--ui-icon-sm'], v['--ui-icon-md'], v['--ui-icon-lg'] = '16px', '18px', '22px'
    v['--ui-card-pad'], v['--ui-card-gap'], v['--ui-panel-pad'] = D['card'], D['cgap'], D['panel']
    v['--ui-header-h'] = f"{D['header']}px"
    v['--ui-control-fs'] = 'max(1rem, var(--type-body-size))'

    # Type voice
    upper = case == 'upper'
    if upper:
        v['--ui-btn-family'] = 'var(--font-display)'
        v['--ui-btn-weight'] = 'var(--type-h1-weight)' if disp_cat != 'serif' else '600'
        v['--ui-btn-transform'] = 'uppercase'
        v['--ui-btn-tracking'] = f"{max(0.04, float(tv.get('tracking_upper_em') or 0) + 0.04):.3f}em"
        k = min(1.14, max(0.9, 0.66 / max(0.3, widths['caps'])))      # wide caps get smaller, condensed caps larger
        v['--ui-btn-size'] = f'calc(var(--type-button-size) * {k:.3f})'
    else:
        v['--ui-btn-family'] = 'var(--type-button-family)'
        v['--ui-btn-weight'] = 'var(--type-button-weight)'
        v['--ui-btn-transform'] = 'var(--type-button-transform)'
        v['--ui-btn-tracking'] = 'var(--type-button-letter-spacing)'
        v['--ui-btn-size'] = 'var(--type-button-size)' if density != 'dense' else 'calc(var(--type-button-size) * .94)'
    v['--ui-btn-size-sm'] = 'calc(var(--ui-btn-size) * .9)'
    v['--ui-btn-size-lg'] = 'calc(var(--ui-btn-size) * 1.1)'
    # Component titles (cards, modals, alerts): display face when it has character, sans otherwise
    if upper:
        v.update({'--ui-title-family': 'var(--font-display)', '--ui-title-weight': 'var(--type-h1-weight)', '--ui-title-transform': 'uppercase',
                  '--ui-title-tracking': 'var(--type-h1-letter-spacing)', '--ui-title-lh': '1', '--ui-title-size': 'clamp(1.375rem, 1.1rem + .8vw, 1.75rem)'})
    elif disp_cat == 'serif':
        v.update({'--ui-title-family': 'var(--font-display)', '--ui-title-weight': 'var(--type-h1-weight)', '--ui-title-transform': 'none',
                  '--ui-title-tracking': 'var(--type-h1-letter-spacing)', '--ui-title-lh': '1.1', '--ui-title-size': 'clamp(1.5rem, 1.2rem + .8vw, 1.875rem)'})
    else:
        v.update({'--ui-title-family': 'var(--font-display)', '--ui-title-weight': '600', '--ui-title-transform': 'none',
                  '--ui-title-tracking': '-0.012em', '--ui-title-lh': '1.15', '--ui-title-size': 'clamp(1.25rem, 1.1rem + .5vw, 1.5rem)'})
    v['--ui-num-family'] = 'var(--type-data-xl-family)'
    v['--ui-num-weight'] = 'var(--type-data-xl-weight)'
    v['--ui-num-transform'] = 'var(--type-h1-transform)'
    # Field labels: technical (label token, upper) for angular brands; quiet sans for the others
    if family == 'angular':
        v.update({'--ui-label-family': 'var(--type-label-family)', '--ui-label-weight': '600', '--ui-label-size': 'var(--type-label-size)',
                  '--ui-label-transform': 'var(--type-label-transform)', '--ui-label-tracking': 'var(--type-label-letter-spacing)'})
    else:
        v.update({'--ui-label-family': 'var(--font-sans)', '--ui-label-weight': '600', '--ui-label-size': 'var(--type-small-size)',
                  '--ui-label-transform': 'none', '--ui-label-tracking': '0'})
    v['--ui-accent-font'] = 'var(--font-hand)' if has_hand else 'var(--font-display)'
    v['--ui-code-font'] = 'var(--font-mono)' if has_mono else 'ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace'

    # Shape
    if corner == 'cut':
        v.update({'--ui-r-btn': '0px', '--ui-r-control': 'var(--radius-input, var(--radius-xs))', '--ui-r-check': 'var(--radius-xs)',
                  '--ui-r-tag': '0px', '--ui-r-chip': '0px', '--ui-r-card': '0px', '--ui-r-panel': '0px', '--ui-r-sm': 'var(--radius-sm)',
                  '--ui-r-media': '0px', '--ui-r-avatar': '0px', '--ui-r-track': '0px', '--ui-r-thumb': '0px'})
    elif corner == 'round':
        v.update({'--ui-r-btn': 'var(--radius-pill)', '--ui-r-control': 'var(--radius-md)', '--ui-r-check': 'calc(var(--radius-xs) + 2px)',
                  '--ui-r-tag': 'var(--radius-pill)', '--ui-r-chip': 'var(--radius-pill)', '--ui-r-card': 'var(--radius-lg)', '--ui-r-panel': 'var(--radius-xl)',
                  '--ui-r-sm': 'var(--radius-sm)', '--ui-r-media': 'var(--radius-md)', '--ui-r-avatar': '50%', '--ui-r-track': 'var(--radius-pill)', '--ui-r-thumb': '50%'})
    elif corner == 'soft':
        v.update({'--ui-r-btn': 'var(--radius-button, var(--radius-md))', '--ui-r-control': 'var(--radius-input, var(--radius-sm))', '--ui-r-check': 'var(--radius-xs)',
                  '--ui-r-tag': 'var(--radius-sm)', '--ui-r-chip': 'var(--radius-md)', '--ui-r-card': 'var(--radius-lg)', '--ui-r-panel': 'var(--radius-xl)',
                  '--ui-r-sm': 'var(--radius-sm)', '--ui-r-media': 'var(--radius-md)', '--ui-r-avatar': '38%', '--ui-r-track': 'var(--radius-pill)', '--ui-r-thumb': '50%'})
    elif corner == 'rounded':
        v.update({'--ui-r-btn': 'var(--radius-button, var(--radius-md))', '--ui-r-control': 'var(--radius-input, var(--radius-sm))', '--ui-r-check': 'var(--radius-xs)',
                  '--ui-r-tag': 'var(--radius-tag, var(--radius-sm))', '--ui-r-chip': 'var(--radius-sm)', '--ui-r-card': 'var(--radius-card, var(--radius-md))',
                  '--ui-r-panel': 'var(--radius-lg)', '--ui-r-sm': 'var(--radius-sm)', '--ui-r-media': 'var(--radius-sm)', '--ui-r-avatar': '50%',
                  '--ui-r-track': 'var(--radius-pill)', '--ui-r-thumb': '50%'})
    else:  # square
        v.update({'--ui-r-btn': 'var(--radius-button, 0px)', '--ui-r-control': 'var(--radius-xs)', '--ui-r-check': 'var(--radius-xs)', '--ui-r-tag': 'var(--radius-xs)',
                  '--ui-r-chip': 'var(--radius-xs)', '--ui-r-card': 'var(--radius-sm)', '--ui-r-panel': 'var(--radius-sm)', '--ui-r-sm': 'var(--radius-xs)',
                  '--ui-r-media': '0px', '--ui-r-avatar': 'var(--radius-xs)', '--ui-r-track': '0px', '--ui-r-thumb': '0px'})
    if crop == 'circle':
        v['--ui-r-avatar'] = '50%'
    v['--ui-cut-xs'] = 'var(--cut-xs, 6px)'
    v['--ui-cut-btn'] = 'var(--cut-xs, 6px)'
    v['--ui-cut-card'] = 'var(--cut-md, 16px)'
    v['--ui-cut-panel'] = 'var(--cut-lg, 24px)'
    v['--ui-cut-tag'] = 'calc(var(--cut-xs, 6px) * .8)'
    v['--ui-tan'] = f'{tan:.4f}'
    v['--ui-cot'] = f'{1 / tan:.4f}'
    v['--ui-sin'] = f'{math.sin(math.radians(angle)):.4f}'
    v['--ui-wipe-angle'] = f'{180 - angle:g}deg'
    v['--ui-skew'] = f'{-(90 - angle):g}deg' if family == 'angular' else '0deg'
    v['--ui-media-inset'] = 'var(--space-2)' if corner == 'soft' else '0px'

    # Borders
    v['--ui-bw'] = 'var(--border-hairline)'
    v['--ui-bw-control'] = 'var(--border-regular)' if family == 'angular' else 'var(--border-hairline)'
    v['--ui-bw-strong'] = 'var(--border-regular)' if family != 'angular' else 'var(--border-strong)'
    v['--ui-bw-card'] = '0px' if corner == 'soft' else 'var(--border-hairline)'

    # Motion
    lift = round(1 + energy * 5)
    if motion == 'snap':
        v.update({'--ui-dur': 'var(--duration-fast)', '--ui-dur-slow': 'var(--duration-base)', '--ui-ease': 'var(--ease-standard)',
                  '--ui-ease-out': 'var(--ease-exit)', '--ui-ease-pop': 'var(--ease-standard)', '--ui-lift': f'{lift}px', '--ui-press-scale': '1',
                  '--ui-hover-x': f'-{lift}px', '--ui-hover-y': f'-{lift}px', '--ui-press-y': '1px'})
    elif motion == 'slide':
        v.update({'--ui-dur': 'var(--duration-fast)', '--ui-dur-slow': 'var(--duration-slow)', '--ui-ease': 'var(--ease-enter)',
                  '--ui-ease-out': 'var(--ease-exit)', '--ui-ease-pop': 'var(--ease-enter)', '--ui-lift': f'{lift}px', '--ui-press-scale': '1',
                  '--ui-hover-x': f'{lift}px', '--ui-hover-y': '0px', '--ui-press-y': '1px'})
    elif motion == 'flow':
        v.update({'--ui-dur': 'var(--duration-base)', '--ui-dur-slow': 'var(--duration-slow)', '--ui-ease': 'var(--ease-standard)',
                  '--ui-ease-out': 'var(--ease-standard)', '--ui-ease-pop': 'var(--ease-emphasis)', '--ui-lift': f'{max(1, lift - 1)}px',
                  '--ui-press-scale': f'{1 - energy * 0.04:.3f}', '--ui-hover-x': '0px', '--ui-hover-y': f'-{max(1, lift - 1)}px', '--ui-press-y': '0px'})
    else:  # glide
        v.update({'--ui-dur': 'var(--duration-base)', '--ui-dur-slow': 'var(--duration-slow)', '--ui-ease': 'var(--ease-enter)',
                  '--ui-ease-out': 'var(--ease-exit)', '--ui-ease-pop': 'var(--ease-emphasis)' if energy >= 0.5 else 'var(--ease-enter)',
                  '--ui-lift': f'{lift}px', '--ui-press-scale': f'{1 - energy * 0.05:.3f}', '--ui-hover-x': '0px', '--ui-hover-y': f'-{lift}px', '--ui-press-y': '0px'})

    R['vars'] = v
    R['themes'] = theme_blocks(b, R)
    return R


def _shadow_offsets(tok, default):
    m = re.findall(r'(-?\d+(?:\.\d+)?)px', tok or '')
    return (float(m[0]), float(m[1])) if len(m) >= 2 else default


def theme_blocks(b, R):
    """Per-theme colour choices. Returns {theme: {var: css}} and a contrast report."""
    themes = (b.colors or {}).get('themes') or {}
    sh = (b.dna.get('tokens') or {}).get('shadow') or {}
    out, report = {}, {}
    for name in THEMES:
        th = Theme(name, themes.get(name) or themes.get('light') or {})
        v, rep = {}, {}
        dark = name != 'light'
        # ---- primary button: brand fill unless it disappears into the ground (then the brand TEXT colour)
        prim = 'brand-primary'
        hov, prs = 'brand-primary-hover', 'brand-primary-pressed'
        if th.cr(prim, 'background') < 1.6 and th.cr('text-brand', 'background') >= 3:
            prim = 'text-brand'
            hov = ('mix', 'text-brand', 'text-primary', 0.22)
            prs = ('mix', 'text-brand', 'background', 0.18)
        for state, bg in (('', prim), ('-h', hov), ('-a', prs)):
            if not th.hex(bg):
                bg = prim
            fg, c = best_fg(th, bg)
            v[f'--ui-primary-bg{state}'] = css_ref(bg)
            v[f'--ui-primary-fg{state}'] = css_ref(fg)
            rep[f'button-primary{state or "-rest"}'] = {'bg': th.hex(bg), 'fg': th.hex(fg), 'ratio': c}
        # ---- destructive
        for state, bg in (('', 'error'), ('-h', ('mix', 'error', 'text-primary', 0.18))):
            fg, c = best_fg(th, bg, prefs=('text-inverse', 'background', 'text-on-brand', 'text-primary', '#FFFFFF', '#000000'))
            v[f'--ui-danger-bg{state}'] = css_ref(bg)
            v[f'--ui-danger-fg{state}'] = css_ref(fg)
            rep[f'button-destructive{state or "-rest"}'] = {'bg': th.hex(bg), 'fg': th.hex(fg), 'ratio': c}
        # ---- "on" fill for checked controls / progress (≥3:1 against the surface)
        on = next((c for c in ('brand-primary', 'text-brand', 'text-primary') if th.cr(c, 'surface') >= 3 and th.cr(c, 'background') >= 3), 'text-primary')
        onfg, c = best_fg(th, on, prefs=('text-on-brand', 'text-inverse', 'background', 'text-primary', '#FFFFFF', '#000000'))
        v['--ui-on'], v['--ui-on-fg'] = css_ref(on), css_ref(onfg)
        rep['control-on'] = {'fill': th.hex(on), 'vs-surface': th.cr(on, 'surface'), 'mark': th.hex(onfg), 'ratio': c}
        # ---- accent line (active tab / nav indicator) ≥3:1 on the background
        line = next((c for c in ('brand-primary', 'text-brand', 'text-primary') if th.cr(c, 'background') >= 3), 'text-primary')
        v['--ui-line'] = css_ref(line)
        rep['indicator'] = {'color': th.hex(line), 'vs-background': th.cr(line, 'background')}
        # ---- field border (≥3:1, as light as possible)
        fb = 'border-strong' if name == 'contrast' else border_mix(th)
        v['--ui-field-border'] = css_ref(fb)
        rep['field-border'] = {'color': th.hex(fb), 'vs-surface': th.cr(fb, 'surface'), 'vs-background': th.cr(fb, 'background')}
        # ---- brand-soft surfaces used behind TEXT (tags, selected rows) — check text-primary on them
        rep['text-on-brand-soft'] = th.cr('text-primary', 'surface-brand-soft')
        rep['text-brand-on-surface'] = th.cr('text-brand', 'surface')
        rep['link-on-background'] = th.cr('text-link', 'background')
        rep['secondary-text-on-surface'] = th.cr('text-secondary', 'surface')
        rep['tertiary-text-on-surface'] = th.cr('text-tertiary', 'surface')
        for s in ('success', 'warning', 'error', 'info'):
            rep[f'{s}-on-soft'] = th.cr(s, f'{s}-soft')
            rep[f'text-on-{s}-soft'] = th.cr('text-primary', f'{s}-soft')
        # semantic text colour: the token itself when it passes on its soft ground, else text-primary
        for s in ('success', 'warning', 'error', 'info'):
            v[f'--ui-{s}-text'] = css_ref(s if th.cr(s, f'{s}-soft') >= 4.5 and th.cr(s, 'surface') >= 4.5 else 'text-primary')
            ic, _ = best_fg(th, s, prefs=('surface', 'text-inverse', 'background', '#FFFFFF', '#000000'))
            v[f'--ui-{s}-icon-fg'] = css_ref(ic)
        # ---- tints, selection, depth
        pct = 14 if name == 'contrast' else (8 if dark else 6)
        v['--ui-tint'] = f'color-mix(in srgb, var(--color-text-primary) {pct}%, transparent)'
        v['--ui-tint-strong'] = f'color-mix(in srgb, var(--color-text-primary) {pct * 2}%, transparent)'
        v['--ui-hairline'] = 'var(--color-border)' if name != 'contrast' else 'var(--color-border-subtle)'
        v['--ui-field-bg'] = 'var(--color-surface)'
        v['--ui-selected-bg'], v['--ui-selected-fg'] = 'var(--color-text-primary)', 'var(--color-text-inverse)'
        v['--ui-skeleton'] = 'var(--color-surface-sunken)' if name != 'contrast' else 'var(--color-border-subtle)'
        v['--ui-skeleton-shine'] = ('color-mix(in srgb, var(--color-surface) 70%, transparent)' if not dark else
                                    'color-mix(in srgb, var(--color-text-primary) 8%, transparent)') if name != 'contrast' else 'transparent'
        v['--ui-code-bg'] = 'var(--color-surface-inverse)' if not dark else 'var(--color-surface-sunken)'
        v['--ui-code-fg'] = 'var(--color-text-inverse)' if not dark else 'var(--color-text-primary)'
        if name == 'contrast':
            v['--ui-code-bg'], v['--ui-code-fg'] = 'var(--color-surface)', 'var(--color-text-primary)'
        v['--ui-card-edge'] = ('var(--color-border-subtle)' if R['corner'] in ('round', 'soft') else 'var(--color-border)') if name != 'contrast' else 'var(--color-border)'
        if R['corner'] == 'soft' and not dark:
            v['--ui-card-edge'] = 'transparent'
        v['--ui-logo-light'], v['--ui-logo-dark'] = ('none', 'block') if dark else ('block', 'none')
        # elevation
        ink = {'light': 'color-mix(in srgb, var(--color-text-primary) 18%, transparent)',
               'dark': 'color-mix(in srgb, #000 55%, transparent)', 'contrast': 'var(--color-border)'}[name]
        v['--ui-shadow-ink'] = ink
        v.update(elevations(R, sh, name))
        out[name] = v
        report[name] = rep
    R['report'] = report
    return out


def elevations(R, sh, theme):
    """--ui-elev-0…3 + --ui-elev-hover as box-shadows (radius shapes) or drop-shadow() filters (cut shapes)."""
    cut = R['corner'] == 'cut'
    none = 'none' if cut else '0 0 #0000'
    if theme == 'contrast' or R['shadow'] == 'flat':
        e = {i: none for i in range(4)}
        e['hover'] = none
    elif R['shadow'] == 'hard':
        o2 = _shadow_offsets(sh.get('2'), (4, 4)); o3 = _shadow_offsets(sh.get('3'), (8, 8))
        if cut:
            e = {0: 'none', 1: 'drop-shadow(0 1px 0 var(--ui-shadow-ink))', 2: f'drop-shadow({o2[0]:g}px {o2[1]:g}px 0 var(--ui-shadow-ink))',
                 3: f'drop-shadow({o3[0]:g}px {o3[1]:g}px 0 var(--ui-shadow-ink))'}
        else:
            e = {0: none, 1: '0 1px 0 var(--ui-shadow-ink)', 2: f'{o2[0]:g}px {o2[1]:g}px 0 0 var(--ui-shadow-ink)', 3: f'{o3[0]:g}px {o3[1]:g}px 0 0 var(--ui-shadow-ink)'}
        e['hover'] = e[2]
    else:  # soft / diffuse → the token shadows (rgba black works on light and dark grounds)
        if cut:
            def f(tok):
                layers = [l.strip() for l in re.split(r',(?![^(]*\))', tok or '') if l.strip()]
                outl = []
                for l in layers:
                    nums = re.findall(r'(-?\d+(?:\.\d+)?)px|(?<![\w.])0(?![\w.])', l)
                    col = re.search(r'(rgba?\([^)]*\)|#[0-9a-fA-F]{3,8})', l)
                    px = [float(a) if a else 0.0 for a in nums]
                    while len(px) < 3: px.append(0.0)
                    outl.append(f'drop-shadow({px[0]:g}px {px[1]:g}px {px[2] / 2:g}px {col.group(1) if col else "rgba(0,0,0,.2)"})')
                return ' '.join(outl) or 'none'
            e = {0: 'none', 1: f(sh.get('1')), 2: f(sh.get('2')), 3: f(sh.get('3'))}
        else:
            e = {0: none, 1: 'var(--shadow-1)', 2: 'var(--shadow-2)', 3: 'var(--shadow-3)'}
        e['hover'] = e[3] if R['shadow'] == 'diffuse' else e[2]
    out = {f'--ui-elev-{k}': val for k, val in e.items()}
    # box-shadow form of level 1 for small inner surfaces (selected pills, range thumbs) — also on cut brands
    out['--ui-elev-1-box'] = ('0 0 #0000' if theme == 'contrast' or R['shadow'] == 'flat' else
                              '0 1px 0 var(--ui-shadow-ink)' if R['shadow'] == 'hard' else 'var(--shadow-1)')
    return out


def css_vars(d, indent='  '):
    return '\n'.join(f'{indent}{k}: {val};' for k, val in d.items())


def theme_css(R):
    T = R['themes']
    return (f':root, [data-theme="light"] {{\n{css_vars(T["light"])}\n}}\n'
            f'[data-theme="dark"] {{\n{css_vars(T["dark"])}\n}}\n'
            f'@media (prefers-color-scheme: dark) {{\n  :root:not([data-theme]) {{\n{css_vars(T["dark"], "    ")}\n  }}\n}}\n'
            f'[data-theme="contrast"] {{\n{css_vars(T["contrast"])}\n}}\n'
            f'@media (prefers-contrast: more) {{\n  :root:not([data-theme]) {{\n{css_vars(T["contrast"], "    ")}\n  }}\n}}\n')


def summary(R):
    shape = {'cut': f"chamfered corners at {R['angle']:g}°" + (' (two opposite corners — faceted)' if R['facets'] else ''),
             'round': 'pill buttons and generous radii', 'soft': 'large soft radii', 'rounded': 'moderate radii', 'square': 'crisp square corners'}[R['corner']]
    return (f"{shape} · {R['shadow']} shadows · {R['motion']} motion (energy {R['energy']:.2f}) · {R['density']} density · "
            f"display case {R['case']} · {R['family']} motifs")
