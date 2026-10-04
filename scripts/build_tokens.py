#!/usr/bin/env python3
"""
build_tokens.py — the single source of truth for colour + design tokens, driven by brand.config.json.

What it does
  1. Palette  : config.palette[] (sampled from the logo, named by role) → HEX/RGB/CMYK/HSL + contrast data
  2. Ramps    : config.ramps if given; otherwise an OKLCH ramp (50…950) around roles.primary with palette
                colours of the same hue family pinned at their lightness stop, and a neutral ramp from roles.foundation
  3. Themes   : light / dark / contrast semantic tokens, derived from roles + ramps (config.themes.<name> overrides
                individual tokens), then AUTO-FIXED to WCAG targets (text ≥ 4.5, primary text ≥ 7 where possible,
                UI/focus ≥ 3) and reported
  4. Non-colour tokens: type scale (derived from the chosen display font + design DNA), spacing (DNA density),
                shape (DNA: radius or cut corners, angles, borders, strokes), shadows (DNA style), blur, opacity,
                breakpoints, grid, z-index, motion (DNA character + profile energy).
                Precedence: defaults < SOURCE/CONFIG/design-dna.json tokens < config.tokens.* / config.type.*
Writes
  COLORS/colors.json · COLORS/css-variables.css · COLORS/contrast-report.json
  UI-DESIGN-SYSTEM/tokens/{design-tokens.json, tokens.css, colors.css, tailwind.preset.js}
  SOURCE/CSS/{tokens.css, colors.css} · SOURCE/JSON/design-tokens.json
Usage: python3 scripts/build_tokens.py --config brand.config.json --repo ../ACME-BRAND [--dna design-dna.json]
"""
import argparse, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from colorlib import (hex2rgb, rgb2hex, rel_lum, contrast, rating, mix, ramp, neutral_ramp, to_oklch, adjust_for_contrast,
                      rgb2cmyk, rgb2hsl, STOPS)

DEFAULT_SEMANTIC = {
    'success': {'name': 'Success', 'light': '#1F7A55', 'dark': '#3FB884', 'contrast': '#5CE0A6', 'fill': '#D9EFE5'},
    'warning': {'name': 'Warning', 'light': '#8A5700', 'dark': '#F2B33D', 'contrast': '#FFD166', 'fill': '#FBEBCB'},
    'error':   {'name': 'Error',   'light': '#C62828', 'dark': '#F28B82', 'contrast': '#FF9E9E', 'fill': '#F9DEDC'},
    'info':    {'name': 'Info',    'light': '#2C64A8', 'dark': '#7FB0F0', 'contrast': '#9EC9FF', 'fill': '#DCE7F5'},
}
ERROR_SHIFTED = {'name': 'Error', 'light': '#C0215A', 'dark': '#F26D95', 'contrast': '#FF8FB1', 'fill': '#F8DCE5'}

TYPE_ROLES = ('display', 'sans', 'mono', 'serif', 'hand', 'pixel')

def clampx(expr, k):
    """scale every number in a clamp()/rem value by k"""
    import re
    return re.sub(r'(\d*\.?\d+)(rem|vw)', lambda m: f"{round(float(m.group(1)) * k, 3):g}{m.group(2)}", expr)

def type_scale(C, dna):
    """Type styles derived from the display family's character (serif / condensed / wide) and the DNA type voice."""
    fams = {f['role']: f for f in C['fonts'].get('families', [])}
    disp = fams.get('display', {}); tags = set(disp.get('tags', [])); serif = disp.get('category') == 'serif' or 'serif' in tags
    condensed = 'condensed' in tags; wide = 'wide' in tags or 'futuristic' in tags
    wmin, wmax = (disp.get('weights') or [400, 900])[0], (disp.get('weights') or [400, 900])[-1]
    tv = (dna or {}).get('type_voice', {}); upper = tv.get('display_case', 'sentence') == 'upper'
    hint = tv.get('headline_weight_hint', 700)
    dw = max(wmin, min(wmax, 500 if serif else (900 if condensed else hint)))
    k = 1.14 if condensed else 0.8 if wide else (0.96 if serif else 1.0)
    lh = 0.88 if condensed else (1.02 if serif else 0.96)
    lsd = '0.01em' if upper and not condensed else ('-0.02em' if not upper and not serif else '-0.01em' if serif else '0em')
    tf = 'uppercase' if upper else 'none'
    sw = 650 if not serif else 600
    S = lambda fam, w, size, l, ls, t='none', note='': {'family': fam, 'weight': w, 'size': size, 'line_height': l, 'letter_spacing': ls, 'transform': t, 'note': note}
    return {
      'display-xxl': S('display', dw, clampx('clamp(4rem, 11vw, 12rem)', k), str(round(lh - 0.06, 2)), lsd, tf),
      'display-xl':  S('display', dw, clampx('clamp(3.25rem, 8vw, 8.5rem)', k), str(round(lh - 0.04, 2)), lsd, tf),
      'display-l':   S('display', dw, clampx('clamp(2.5rem, 5.5vw, 5.75rem)', k), str(round(lh, 2)), lsd, tf),
      'h1':          S('display', dw, clampx('clamp(2.5rem, 5vw, 4.75rem)', k), str(round(lh + 0.02, 2)), lsd, tf),
      'h2':          S('sans', sw, 'clamp(1.75rem, 3vw, 2.875rem)', '1.06', '-0.02em'),
      'h3':          S('sans', sw - 50, 'clamp(1.3125rem, 2vw, 1.75rem)', '1.15', '-0.012em'),
      'h4':          S('sans', 600, 'clamp(1.125rem, 1.5vw, 1.3125rem)', '1.25', '-0.005em'),
      'body-l':      S('sans', 400, '1.25rem', '1.55', '0em'),
      'body':        S('sans', 400, '1.0625rem', '1.6', '0em'),
      'small':       S('sans', 400, '0.9375rem', '1.5', '0.005em'),
      'caption':     S('sans', 400, '0.8125rem', '1.45', '0.01em'),
      'label':       S('mono', 500, '0.75rem', '1.3', '0.06em', 'uppercase'),
      'eyebrow':     S('mono', 500, '0.75rem', '1.2', '0.12em', 'uppercase'),
      'button':      S('sans', 600, '0.875rem', '1', '0.06em', 'uppercase') if upper else S('sans', 600, '0.9375rem', '1', '0.01em'),
      'nav':         S('sans', 500, '0.9375rem', '1.2', '0em'),
      'data':        S('mono', 450, '0.875rem', '1.4', '0em', 'none', 'tabular-nums'),
      'data-xl':     S('display', dw, clampx('clamp(3rem, 7vw, 7rem)', k), str(round(lh - 0.04, 2)), '-0.01em', 'none', 'tabular-nums'),
      'code':        S('code', 400, '0.875rem', '1.6', '0em'),
      'quote':       S('serif' if 'serif' in fams else 'display', 400 if serif or 'serif' in fams else dw, clampx('clamp(1.5rem, 3vw, 2.5rem)', 1), '1.2', '-0.01em'),
    }

DEFAULT_TOKENS = {
  'space': {'0': '0', 'px': '1px', '0-5': '2px', '1': '4px', '2': '8px', '3': '12px', '4': '16px', '5': '20px', '6': '24px', '7': '28px', '8': '32px', '10': '40px', '12': '48px', '14': '56px', '16': '64px', '20': '80px', '24': '96px', '32': '128px', '40': '160px', '48': '192px',
            'gutter': 'clamp(16px, 2vw, 32px)', 'margin': 'clamp(16px, 4.5vw, 72px)', 'section': 'clamp(72px, 11vw, 176px)', 'block': 'clamp(40px, 6vw, 96px)'},
  'radius': {'none': '0', 'xs': '2px', 'sm': '4px', 'full': '9999px'},
  'cut': {'xs': '6px', 'sm': '10px', 'md': '16px', 'lg': '24px', 'xl': '40px', '2xl': '64px'},
  'angle': {'cut': '45deg', 'crop': '72deg', 'shallow': '15deg'},
  'border': {'hairline': '1px', 'regular': '1.5px', 'strong': '2px', 'heavy': '4px', 'rule': '8px'},
  'shadow': {'1': '0 1px 2px rgba(0,0,0,.08)', '2': '0 8px 20px -8px rgba(0,0,0,.2)', '3': '0 24px 48px -16px rgba(0,0,0,.32)',
             'focus-lift': '0 12px 32px -12px rgba(0,0,0,.3)', 'inset-glass': 'inset 0 1px 0 rgba(255,255,255,.55), inset 0 -1px 0 rgba(0,0,0,.06)'},
  'blur': {'none': '0', 'sm': '8px', 'md': '16px', 'lg': '28px', 'xl': '48px'},
  'opacity': {'0': '0', '4': '0.04', '8': '0.08', '12': '0.12', '16': '0.16', '24': '0.24', '40': '0.4', '64': '0.64', '80': '0.8', '100': '1'},
  'breakpoint': {'sm': '480px', 'md': '768px', 'lg': '1024px', 'xl': '1280px', '2xl': '1536px', '3xl': '1920px'},
  'z': {'below': '-1', 'base': '0', 'raised': '10', 'dropdown': '100', 'sticky': '200', 'header': '300', 'overlay': '400', 'modal': '500', 'toast': '600', 'tooltip': '700', 'cursor': '900'},
  'duration': {'instant': '80ms', 'fast': '160ms', 'base': '240ms', 'slow': '400ms', 'slower': '640ms', 'formation': '1200ms', 'logo': '2400ms'},
  'ease': {'standard': 'cubic-bezier(0.25, 0.1, 0.25, 1)', 'enter': 'cubic-bezier(0.22, 1, 0.36, 1)', 'exit': 'cubic-bezier(0.64, 0, 0.78, 0)',
           'emphasis': 'cubic-bezier(0.34, 1.25, 0.64, 1)', 'linear': 'linear'},
}
GRID = {'mobile': {'columns': 4, 'gutter': '16px', 'margin': '16px', 'min': '0px'}, 'tablet': {'columns': 8, 'gutter': '24px', 'margin': '32px', 'min': '768px'},
        'desktop': {'columns': 12, 'gutter': '24px', 'margin': '48px', 'min': '1024px'}, 'large': {'columns': 12, 'gutter': '32px', 'margin': '72px', 'min': '1536px'},
        'container-max': '1440px', 'container-wide': '1680px', 'measure': '68ch'}

def rgba(h, a): r, g, b = hex2rgb(h); return f'rgba({r}, {g}, {b}, {a})'

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--config', required=True); ap.add_argument('--repo', required=True); ap.add_argument('--dna')
    a = ap.parse_args(); C = json.load(open(a.config)); P = lambda *p: os.path.join(a.repo, *p)
    dna_p = a.dna or P('SOURCE', 'CONFIG', 'design-dna.json')
    DNA = json.load(open(dna_p)) if os.path.exists(dna_p) else {}
    brand = C['brand']; px = brand.get('prefix', 'bx'); roles = C['roles']
    PAL = C['palette']; pal = {p['key']: p['hex'].upper() for p in PAL}
    prim, found, paper = pal[roles['primary']], pal[roles['foundation']], pal[roles['paper']]
    acc = pal.get(roles.get('accent', ''), None)
    # ---------------- ramps
    ramps = dict(C.get('ramps', {}))
    pr_key = roles.get('primary_ramp', 'primary'); nr_key = roles.get('neutral_ramp', 'neutral')
    if pr_key not in ramps:
        L0, C0, H0 = to_oklch(prim); pins = {}
        from colorlib import L_TARGETS
        for p in PAL:
            L, Cc, Hh = to_oklch(p['hex'])
            if Cc > 0.05 and min(abs(Hh - H0), 360 - abs(Hh - H0)) < 25:
                s = STOPS[min(range(len(STOPS)), key=lambda i: abs(L_TARGETS[i] - L))]
                pins.setdefault(s, p['hex'].upper())
        ramps[pr_key] = ramp(prim, pins)
    if nr_key not in ramps: ramps[nr_key] = neutral_ramp(found)
    if acc and roles.get('accent_ramp', 'accent') not in ramps and not any(acc.upper() in [v.upper() for v in r.values()] for r in ramps.values()):
        ramps[roles.get('accent_ramp', 'accent')] = ramp(acc)
    PR, NR = ramps[pr_key], ramps[nr_key]
    # ---------------- semantic (error must not look like the brand primary)
    sem = {k: dict(v) for k, v in DEFAULT_SEMANTIC.items()}
    _, pc, ph = to_oklch(prim)
    if pc > 0.08 and (ph < 45 or ph > 340): sem['error'] = dict(ERROR_SHIFTED)   # red-ish brand → error shifted towards magenta so it never reads as the brand
    for k, v in C.get('semantic', {}).items(): sem.setdefault(k, {}).update(v)
    # ---------------- themes (derive → override → fix)
    def step(r, s, d):  # move d stops along a ramp from stop s
        i = STOPS.index(s); return r[STOPS[max(0, min(len(STOPS) - 1, i + d))]]
    pstop = min(STOPS, key=lambda s: abs(contrast(PR[s], prim)))  # stop that equals primary
    on_brand = '#FFFFFF' if contrast('#FFFFFF', prim) >= 4.5 else (found if contrast(found, prim) >= 4.5 else '#FFFFFF')
    accent_text = roles.get('accent_text') or (acc and adjust_for_contrast(acc, paper, 4.5)[0]) or NR['600']
    light = {
        'brand-primary': prim, 'brand-primary-hover': step(PR, pstop, 1), 'brand-primary-pressed': step(PR, pstop, 2), 'brand-secondary': found,
        'on-brand': on_brand, 'background': paper, 'background-alt': mix(paper, found, 0.06), 'background-inverse': found,
        'surface': '#FFFFFF', 'surface-raised': '#FFFFFF', 'surface-sunken': mix(paper, found, 0.06), 'surface-inverse': found,
        'surface-glass': rgba(mix(paper, '#FFFFFF', 0.4), 0.62), 'surface-glass-border': 'rgba(255, 255, 255, 0.65)',
        'surface-brand': prim, 'surface-brand-soft': PR['100'],
        'text-primary': found, 'text-secondary': NR['600'], 'text-tertiary': NR['500'], 'text-inverse': paper,
        'text-brand': prim, 'text-on-brand': on_brand, 'text-link': step(PR, pstop, 1), 'text-link-hover': step(PR, pstop, 2), 'text-disabled': NR['300'],
        'border': mix(paper, found, 0.14), 'border-strong': found, 'border-subtle': mix(paper, found, 0.07), 'border-brand': prim,
        'accent': accent_text, 'accent-strong': mix(accent_text, found, 0.5), 'accent-soft': mix(acc or accent_text, '#FFFFFF', 0.85),
        'focus': found, 'focus-halo': paper, 'selection': mix(prim, paper, 0.78),
        'success': sem['success']['light'], 'success-soft': sem['success']['fill'], 'warning': sem['warning']['light'], 'warning-soft': sem['warning']['fill'],
        'error': sem['error']['light'], 'error-soft': sem['error']['fill'], 'info': sem['info']['light'], 'info-soft': sem['info']['fill'],
        'overlay': rgba(found, 0.56), 'grain-opacity': '0.06'}
    dbg = found
    dark = {
        'brand-primary': prim, 'brand-primary-hover': step(PR, pstop, 1), 'brand-primary-pressed': step(PR, pstop, 2), 'brand-secondary': paper,
        'on-brand': on_brand, 'background': dbg, 'background-alt': mix(dbg, '#FFFFFF', 0.04), 'background-inverse': paper,
        'surface': mix(dbg, '#FFFFFF', 0.05), 'surface-raised': mix(dbg, '#FFFFFF', 0.1), 'surface-sunken': mix(dbg, '#000000', 0.35), 'surface-inverse': paper,
        'surface-glass': rgba(dbg, 0.55), 'surface-glass-border': 'rgba(255, 255, 255, 0.12)', 'surface-brand': prim, 'surface-brand-soft': PR['950'],
        'text-primary': paper, 'text-secondary': NR['200'], 'text-tertiary': NR['300'], 'text-inverse': found,
        'text-brand': PR['300'], 'text-on-brand': on_brand, 'text-link': PR['300'], 'text-link-hover': PR['100'], 'text-disabled': NR['400'],
        'border': NR['600'], 'border-strong': paper, 'border-subtle': NR['700'], 'border-brand': PR['400'],
        'accent': acc or NR['200'], 'accent-strong': mix(acc or NR['200'], '#FFFFFF', 0.6), 'accent-soft': mix(acc or NR['600'], dbg, 0.75),
        'focus': acc or paper, 'focus-halo': dbg, 'selection': PR['800'],
        'success': sem['success']['dark'], 'success-soft': mix(sem['success']['dark'], dbg, 0.82), 'warning': sem['warning']['dark'], 'warning-soft': mix(sem['warning']['dark'], dbg, 0.82),
        'error': sem['error']['dark'], 'error-soft': mix(sem['error']['dark'], dbg, 0.82), 'info': sem['info']['dark'], 'info-soft': mix(sem['info']['dark'], dbg, 0.82),
        'overlay': rgba(mix(dbg, '#000000', 0.3), 0.72), 'grain-opacity': '0.08'}
    hc_brand = adjust_for_contrast(PR['300'], '#000000', 7, 'lighter')[0]
    contrast_t = {
        'brand-primary': hc_brand, 'brand-primary-hover': mix(hc_brand, '#FFFFFF', 0.35), 'brand-primary-pressed': '#FFFFFF', 'brand-secondary': '#FFFFFF',
        'on-brand': '#000000', 'background': '#000000', 'background-alt': '#000000', 'background-inverse': '#FFFFFF',
        'surface': '#000000', 'surface-raised': '#000000', 'surface-sunken': '#000000', 'surface-inverse': '#FFFFFF',
        'surface-glass': '#000000', 'surface-glass-border': '#FFFFFF', 'surface-brand': hc_brand, 'surface-brand-soft': '#000000',
        'text-primary': '#FFFFFF', 'text-secondary': '#FFFFFF', 'text-tertiary': '#E6E9ED', 'text-inverse': '#000000',
        'text-brand': hc_brand, 'text-on-brand': '#000000', 'text-link': adjust_for_contrast(acc or '#9EE7F2', '#000000', 7, 'lighter')[0], 'text-link-hover': '#FFFFFF', 'text-disabled': '#A3ADB8',
        'border': '#FFFFFF', 'border-strong': '#FFFFFF', 'border-subtle': '#A3ADB8', 'border-brand': hc_brand,
        'accent': adjust_for_contrast(acc or '#9EE7F2', '#000000', 7, 'lighter')[0], 'accent-strong': '#FFFFFF', 'accent-soft': '#000000',
        'focus': '#FFE14D', 'focus-halo': '#000000', 'selection': '#FFE14D',
        'success': sem['success']['contrast'], 'success-soft': '#000000', 'warning': sem['warning']['contrast'], 'warning-soft': '#000000',
        'error': sem['error']['contrast'], 'error-soft': '#000000', 'info': sem['info']['contrast'], 'info-soft': '#000000',
        'overlay': 'rgba(0, 0, 0, 0.85)', 'grain-opacity': '0'}
    THEMES = {'light': light, 'dark': dark, 'contrast': contrast_t}
    for tn, ov in C.get('themes', {}).items(): THEMES.setdefault(tn, {}).update(ov)
    # auto-fix to targets
    TARGETS = {'text-primary': 7, 'text-secondary': 4.5, 'text-tertiary': 4.5, 'text-brand': 4.5, 'text-link': 4.5, 'text-link-hover': 4.5,
               'accent': 4.5, 'error': 4.5, 'success': 4.5, 'warning': 4.5, 'info': 4.5, 'focus': 3, 'border-strong': 3}
    fixes = []
    for tn, t in THEMES.items():
        bg = t['background']
        alts = [x for x in (t.get('background-alt'), t.get('surface-sunken'), t.get('surface')) if x and x.startswith('#')]
        for k, target in TARGETS.items():
            if k in t and t[k].startswith('#') and contrast(t[k], bg) < target:
                new, r = adjust_for_contrast(t[k], bg, target); fixes.append(f'{tn}.{k}: {t[k]} → {new} ({r}:1 on {bg})'); t[k] = new
            # body-text roles must also hold on the alternate backgrounds (cards, sunken bands)
            if k in ('text-secondary', 'text-link', 'text-link-hover', 'text-brand') and k in t and t[k].startswith('#'):
                for alt in alts:
                    if contrast(t[k], alt) < 4.5:
                        new, r = adjust_for_contrast(t[k], alt, 4.5); fixes.append(f'{tn}.{k}: {t[k]} → {new} ({r}:1 on {alt})'); t[k] = new
        if contrast(t['on-brand'], t['brand-primary']) < 4.5:
            new, r = adjust_for_contrast(t['brand-primary'], t['on-brand'], 4.5); fixes.append(f'{tn}.brand-primary: {t["brand-primary"]} → {new} for on-brand text ({r}:1) — review: keep the original primary for graphics, use this for buttons'); t['brand-primary'] = new
            dk = '#000000' if rel_lum(t['on-brand']) > 0.5 else '#FFFFFF'
            t['brand-primary-hover'] = mix(new, dk, 0.16); t['brand-primary-pressed'] = mix(new, dk, 0.3)
        if contrast(t['on-brand'], t['brand-primary-hover']) < 4.5:
            new, r = adjust_for_contrast(t['brand-primary-hover'], t['on-brand'], 4.5); fixes.append(f'{tn}.brand-primary-hover → {new}'); t['brand-primary-hover'] = new
    # ---------------- outputs
    T = {k: dict(v) for k, v in DEFAULT_TOKENS.items()}
    for g, v in DNA.get('tokens', {}).items(): T.setdefault(g, {}).update(v)          # DNA shape/motion language
    ks = float(DNA.get('space_scale', 1.0))
    if ks != 1.0:
        import re as _re
        for key in ('section', 'block'): T['space'][key] = _re.sub(r'(\d+)px', lambda m: f"{round(int(m.group(1)) * ks)}px", T['space'][key])
    for g, v in C.get('tokens', {}).items(): T.setdefault(g, {}).update(v)
    TYPE = type_scale(C, DNA)
    for k, v in C.get('type', {}).items():
        if isinstance(v, (list, tuple)): v = dict(zip(['family', 'weight', 'size', 'line_height', 'letter_spacing', 'note'], v))
        TYPE.setdefault(k, {}).update(v)
    stacks = dict(C['fonts']['stacks'])
    stacks.setdefault('mono', stacks.get('sans', 'ui-monospace, monospace'))
    has_mono = any(f.get('role') == 'mono' for f in C['fonts'].get('families', []))
    stacks.setdefault('code', stacks['mono'] if has_mono else "ui-monospace, 'SFMono-Regular', Menlo, Consolas, 'Liberation Mono', monospace")
    fam_of = lambda f: f if f in stacks else ('mono' if f == 'pixel' and 'mono' in stacks else 'display' if f in ('serif', 'hand', 'pixel') else 'sans')
    settings = C['fonts'].get('settings', {'headline': 'normal', 'body': 'normal'})
    colors = {'name': f"{brand['name']} colour system", 'version': '1.0.0', 'palette': [], 'ramps': ramps, 'semantic': sem, 'themes': THEMES,
              'usage_ratio': C.get('usage_ratio', {'neutral field (paper/foundation)': '60–70%', 'primary family': '15–25%', 'neutrals & photography': '10–20%', 'accent': '≤5%'}),
              'cmyk_note': 'CMYK values are mathematical conversions. Proof on press and record final values; never invent Pantone references.',
              'auto_fixes': fixes}
    for p in PAL:
        h = p['hex'].upper()
        colors['palette'].append({**p, 'hex': h, 'rgb': list(hex2rgb(h)), 'cmyk': rgb2cmyk(h), 'hsl': rgb2hsl(h), 'css': f'--{px}-{p["key"]}',
            'contrast': {'on_white': round(contrast(h, '#FFFFFF'), 2), 'on_paper': round(contrast(h, paper), 2), 'on_foundation': round(contrast(h, found), 2),
                         'white_text': rating(contrast(h, '#FFFFFF')), 'foundation_text': rating(contrast(h, found))}})
    os.makedirs(P('COLORS'), exist_ok=True)
    json.dump(colors, open(P('COLORS', 'colors.json'), 'w'), indent=2, ensure_ascii=False)
    def theme_css(n): return '\n'.join(f'  --color-{k}: {v};' for k, v in THEMES[n].items())
    pal_css = '\n'.join([f'  --{px}-{p["key"]}: {p["hex"].upper()};' for p in PAL] +
                        [f'  --{px}-{k}-light: {v["light"]}; --{px}-{k}-dark: {v["dark"]};' for k, v in sem.items()] +
                        ['  ' + ' '.join(f'--{px}-{rn}-{s}: {v};' for s, v in r.items()) for rn, r in ramps.items()])
    colors_css = f'''/* {brand['name']} — colour variables. Generated by scripts/build_tokens.py — do not edit by hand.
   Themes: light (default) · dark ([data-theme="dark"] or OS preference) · contrast ([data-theme="contrast"] or prefers-contrast: more) */
:root {{
{pal_css}
}}
:root, [data-theme="light"] {{
  color-scheme: light;
{theme_css('light')}
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme]) {{
    color-scheme: dark;
{theme_css('dark')}
  }}
}}
[data-theme="dark"] {{
  color-scheme: dark;
{theme_css('dark')}
}}
@media (prefers-contrast: more) {{
  :root:not([data-theme]) {{
{theme_css('contrast')}
  }}
}}
[data-theme="contrast"] {{
  color-scheme: dark;
{theme_css('contrast')}
}}
'''
    open(P('COLORS', 'css-variables.css'), 'w').write(colors_css)
    kv = lambda pre, d: '\n'.join(f'  --{pre}-{k}: {v};' for k, v in d.items())
    type_css = '\n'.join(f"  --type-{k}-family: var(--font-{fam_of(t['family'])}); --type-{k}-weight: {t['weight']}; --type-{k}-size: {t['size']}; --type-{k}-line-height: {t['line_height']}; --type-{k}-letter-spacing: {t['letter_spacing']}; --type-{k}-transform: {t.get('transform', 'none')};"
                         for k, t in TYPE.items())
    tokens_css = f'''/* {brand['name']} — design tokens (CSS custom properties). Generated by scripts/build_tokens.py — do not edit by hand. */
@import url("./colors.css");
:root {{
  /* Typography */
{kv('font', stacks)}
{type_css}
  --font-headline-settings: {settings.get('headline', 'normal')};
  --font-body-settings: {settings.get('body', 'normal')};
  /* Space (4px base) */
{kv('space', T['space'])}
  /* Shape */
{kv('radius', T['radius'])}
{kv('cut', T['cut'])}
{kv('angle', T['angle'])}
{kv('border', T['border'])}
{kv('stroke', T.get('stroke', {'icon': '1.75px', 'cap': 'round', 'join': 'round'}))}
  --shape-style: {DNA.get('corner', {}).get('style', 'rounded')};
  --radius-button: {T['radius'].get('button', T['radius'].get('sm', '4px'))}; --radius-card: {T['radius'].get('md', '6px')}; --radius-input: {T['radius'].get('sm', '4px')}; --radius-tag: {T['radius'].get('pill', '9999px') if DNA.get('corner', {}).get('style') == 'round' else T['radius'].get('xs', '2px')};
  /* Depth & material */
{kv('shadow', T['shadow'])}
{kv('blur', T['blur'])}
{kv('opacity', T['opacity'])}
  /* Layout */
  --container-max: {GRID['container-max']}; --container-wide: {GRID['container-wide']}; --measure: {GRID['measure']};
  --grid-columns: 4; --grid-gutter: 16px; --grid-margin: 16px;
{kv('z', T['z'])}
  /* Motion */
{kv('duration', T['duration'])}
{kv('ease', T['ease'])}
  --focus-ring: 0 0 0 2px var(--color-focus-halo), 0 0 0 4px var(--color-focus);
}}
@media (min-width: 768px) {{ :root {{ --grid-columns: 8; --grid-gutter: 24px; --grid-margin: 32px; }} }}
@media (min-width: 1024px) {{ :root {{ --grid-columns: 12; --grid-gutter: 24px; --grid-margin: 48px; }} }}
@media (min-width: 1536px) {{ :root {{ --grid-columns: 12; --grid-gutter: 32px; --grid-margin: 72px; }} }}
@media (prefers-reduced-motion: reduce) {{
  :root {{ {' '.join(f'--duration-{k}: 0ms;' for k in T['duration'])} }}
}}
'''
    for d in (P('UI-DESIGN-SYSTEM', 'tokens'), P('SOURCE', 'CSS')):
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, 'tokens.css'), 'w').write(tokens_css); open(os.path.join(d, 'colors.css'), 'w').write(colors_css)
    TT = lambda v, t, d=None: {'$value': v, '$type': t, **({'$description': d} if d else {})}
    dt = {'$description': f"{brand['name']} design tokens — W3C DTCG format. Source: scripts/build_tokens.py + brand.config.json",
          'color': {'brand': {p['key']: TT(p['hex'].upper(), 'color', f"{p['name']}. {p.get('role', '')}") for p in PAL},
                    'ramp': {rn: {s: TT(v, 'color') for s, v in r.items()} for rn, r in ramps.items()},
                    'semantic': {k: {m: TT(v[m], 'color') for m in ('light', 'dark', 'contrast', 'fill') if m in v} for k, v in sem.items()}},
          'theme': {tn: {k: TT(v, 'color') for k, v in tv.items() if k != 'grain-opacity'} for tn, tv in THEMES.items()},
          'font': {'family': {k: TT(v, 'fontFamily') for k, v in stacks.items()}},
          'typography': {k: {**TT({'fontFamily': f"{{font.family.{fam_of(t['family'])}}}", 'fontWeight': t['weight'], 'fontSize': t['size'], 'lineHeight': t['line_height'], 'letterSpacing': t['letter_spacing']}, 'typography', t.get('note') or None),
                             '$extensions': {'textTransform': t.get('transform', 'none')}} for k, t in TYPE.items()},
          **{g: {k: TT(v, 'dimension' if g in ('space', 'radius', 'cut', 'blur', 'breakpoint') else 'other') for k, v in T[g].items()} for g in ('space', 'radius', 'cut', 'angle', 'blur', 'breakpoint')},
          'border': {'width': {k: TT(v, 'dimension') for k, v in T['border'].items()}},
          'shadow': {k: TT(v, 'shadow') for k, v in T['shadow'].items()},
          'opacity': {k: TT(float(v), 'number') for k, v in T['opacity'].items()},
          'grid': {k: TT(v, 'other') for k, v in GRID.items()},
          'z-index': {k: TT(int(v), 'number') for k, v in T['z'].items()},
          'duration': {k: TT(v, 'duration') for k, v in T['duration'].items()},
          'easing': {k: TT(v, 'cubicBezier') for k, v in T['ease'].items()}}
    for d in (P('UI-DESIGN-SYSTEM', 'tokens', 'design-tokens.json'), P('SOURCE', 'JSON', 'design-tokens.json')):
        os.makedirs(os.path.dirname(d), exist_ok=True); json.dump(dt, open(d, 'w'), indent=2, ensure_ascii=False)
    tw = {'theme': {'extend': {
        'colors': {**{p['key']: p['hex'].upper() for p in PAL}, **ramps,
                   **{k: f'var(--color-{k})' for k in ['background', 'surface', 'text-primary', 'text-secondary', 'border', 'accent', 'focus']},
                   'brand': {'DEFAULT': 'var(--color-brand-primary)', 'hover': 'var(--color-brand-primary-hover)'},
                   'success': 'var(--color-success)', 'warning': 'var(--color-warning)', 'error': 'var(--color-error)', 'info': 'var(--color-info)'},
        'fontFamily': {k: [s.strip().strip("'") for s in v.split(',')] for k, v in stacks.items()},
        'spacing': {k: v for k, v in T['space'].items() if not k.isalpha()}, 'borderRadius': T['radius'], 'boxShadow': T['shadow'], 'blur': T['blur'],
        'screens': T['breakpoint'], 'zIndex': T['z'], 'transitionDuration': T['duration'], 'transitionTimingFunction': T['ease'],
        'maxWidth': {'container': GRID['container-max'], 'wide': GRID['container-wide'], 'measure': GRID['measure']}}}}
    open(P('UI-DESIGN-SYSTEM', 'tokens', 'tailwind.preset.js'), 'w').write(
        f"/* {brand['name']} — Tailwind preset. Generated by scripts/build_tokens.py.\n   v3: presets: [require('./tailwind.preset.js')] · v4: @config './tailwind.preset.js' */\nmodule.exports = " + json.dumps(tw, indent=2) + ';\n')
    rep = {'pairs': [{'name': p['name'], 'hex': p['hex'].upper(), 'white': round(contrast(p['hex'], '#FFFFFF'), 2), 'paper': round(contrast(p['hex'], paper), 2),
                      'foundation': round(contrast(p['hex'], found), 2)} for p in PAL], 'themes': {}, 'auto_fixes': fixes}
    for tn, t in THEMES.items():
        rep['themes'][tn] = {f'{k}/background': round(contrast(t[k], t['background']), 2) for k in TARGETS if k in t and t[k].startswith('#')}
        rep['themes'][tn]['on-brand/brand-primary'] = round(contrast(t['on-brand'], t['brand-primary']), 2)
    json.dump(rep, open(P('COLORS', 'contrast-report.json'), 'w'), indent=2)
    print('tokens built.', f'{len(fixes)} auto-fixes:' if fixes else 'no contrast fixes needed.')
    for f in fixes: print('  ', f)
    for tn, d in rep['themes'].items():
        low = {k: v for k, v in d.items() if v < (3 if k.startswith(('focus', 'border')) else 4.5)}
        print(f'  {tn}: min {min(d.values())}:1', '· FAILS: ' + str(low) if low else '· all pairs pass')

if __name__ == '__main__':
    main()
