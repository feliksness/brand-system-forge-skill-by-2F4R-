"""
flavour.py — DNA-driven CSS that is not about the corner shape:
  motion character (snap / slide / glide / flow), motif family (angular / round / organic) details
  — indicators, separators, list markers, dividers, spinners, placeholder art —, script/language rules,
  and the preference queries (reduced motion, forced colours, print).
"""
from urllib.parse import quote

SCRIPTS = {'ru': 'cyrillic', 'uk': 'cyrillic', 'bg': 'cyrillic', 'sr': 'cyrillic', 'mk': 'cyrillic', 'be': 'cyrillic', 'kk': 'cyrillic',
           'hy': 'armenian', 'ka': 'georgian', 'el': 'greek', 'ar': 'arabic', 'fa': 'arabic', 'ur': 'arabic', 'he': 'hebrew',
           'hi': 'devanagari', 'mr': 'devanagari', 'ne': 'devanagari', 'bn': 'bengali', 'th': 'thai', 'zh': 'han', 'ja': 'japanese', 'ko': 'hangul'}


def _svg_url(svg):
    return 'url("data:image/svg+xml,' + quote(svg, safe=" =:/',.()-") + '")'


def motion(R, p):
    m = R['motion']
    if m == 'snap':
        return f"""/* ---- MOTION · snap — crisp, short, no overshoot: press drops 1px, cards step up-left onto a hard shadow ---- */
.{p}-btn:is(:active, .is-active):not(:disabled, [aria-disabled="true"], [aria-busy="true"]) {{ transform: translate(1px, 1px); }}
.{p}-chip:is(:active) {{ transform: translate(1px, 1px); }}
"""
    if m == 'slide':
        return f"""/* ---- MOTION · slide — lateral moves: icons and indicators travel along the reading direction ---- */
.{p}-btn:is(:hover, .is-hover):not(:disabled, [aria-disabled="true"]) > :is([data-{p}-icon], .{p}-icon):last-child {{ transform: translateX(4px); }}
.{p}-btn:is(:active, .is-active):not(:disabled, [aria-disabled="true"]) {{ transform: translateX(1px); }}
"""
    if m == 'flow':
        return f"""/* ---- MOTION · flow — slow, soft, springy: surfaces float up a little, toggles spring ---- */
:is(.{p}-btn--primary, .{p}-btn--secondary, .{p}-btn--destructive):is(:hover, .is-hover):not(:disabled, [aria-disabled="true"], [aria-busy="true"], .is-loading) {{ transform: translateY(-1px); --_elev: var(--ui-elev-1); }}
:is(.{p}-btn--primary, .{p}-btn--secondary, .{p}-btn--destructive):is(:active, .is-active):not(:disabled, [aria-disabled="true"]) {{ transform: scale(var(--ui-press-scale)); --_elev: var(--ui-elev-0); }}
.{p}-chip:is(:hover, .is-hover) {{ transform: translateY(-1px); }}
"""
    return f"""/* ---- MOTION · glide — smooth lift from the centre: buttons rise and gain depth, press settles ---- */
:is(.{p}-btn--primary, .{p}-btn--destructive):is(:hover, .is-hover):not(:disabled, [aria-disabled="true"], [aria-busy="true"], .is-loading) {{ transform: translateY(calc(var(--ui-lift) * -.5)); --_elev: var(--ui-elev-2); }}
.{p}-btn--secondary:is(:hover, .is-hover):not(:disabled, [aria-disabled="true"]) {{ transform: translateY(calc(var(--ui-lift) * -.5)); }}
.{p}-btn:is(:active, .is-active):not(:disabled, [aria-disabled="true"], [aria-busy="true"]) {{ transform: scale(var(--ui-press-scale)); --_elev: var(--ui-elev-0); }}
.{p}-chip:is(:hover, .is-hover) {{ transform: translateY(-1px); }}
.{p}-avatar-group > .{p}-avatar {{ transition: transform var(--ui-dur) var(--ui-ease-pop); }}
.{p}-avatar-group > .{p}-avatar:hover {{ transform: translateY(calc(var(--ui-lift) * -1)) scale(1.04); z-index: 1; }}
"""


def family(R, p, b):
    fam, angle = R['family'], R['angle']
    motifs = R['motifs']
    out = [f'/* ---- MOTIFS · {fam} family (dna.motifs: {", ".join(motifs[:5])}) ---- */']
    if fam == 'angular':
        chevron = 'chevron' in motifs or 'chevrons' in R['patterns']
        shard = (f"<svg xmlns='http://www.w3.org/2000/svg' width='40' height='16' viewBox='0 0 40 16'><path d='M12 14 L18 2 H22 L16 14Z M20 14 L26 2 H30 L24 14Z' fill='#000'/></svg>" if chevron
                 else "<svg xmlns='http://www.w3.org/2000/svg' width='40' height='16' viewBox='0 0 40 16'><path d='M16 14 L22 2 H26 L20 14Z' fill='#000'/></svg>")
        out.append(f"""
.{p}-breadcrumbs li + li::before {{ width: 1.5px; height: 14px; background: var(--color-text-tertiary); transform: rotate({90 - angle:g}deg); }}
.{p}-list:not(.{p}-list--check, .{p}-list--divided) > li::before {{ background: var(--ui-line); width: .55em; height: .7em; top: .42em; clip-path: polygon(0 0, 45% 0, 100% 50%, 45% 100%, 0 100%, 55% 50%); }}
.{p}-divider--motif {{ background: currentColor; -webkit-mask: linear-gradient(#000 0 0) left 50% / calc(50% - 26px) 1.5px no-repeat, linear-gradient(#000 0 0) right 50% / calc(50% - 26px) 1.5px no-repeat, {_svg_url(shard)} center / 40px 16px no-repeat;
  mask: linear-gradient(#000 0 0) left 50% / calc(50% - 26px) 1.5px no-repeat, linear-gradient(#000 0 0) right 50% / calc(50% - 26px) 1.5px no-repeat, {_svg_url(shard)} center / 40px 16px no-repeat; }}
.{p}-tabs:not(.{p}-tabs--pills, .{p}-tabs--boxed) .{p}-tabs__list {{ gap: var(--space-8); }}
.{p}-testimonial__mark {{ transform: skewX(var(--ui-skew)); }}
/* spinner — three bars on the logo angle light in sequence */
.{p}-spinner::before, .{p}-btn:is(.is-loading, [aria-busy="true"])::after {{
  --_dim: color-mix(in srgb, currentColor 28%, transparent);
  content: ""; position: absolute; left: 50%; top: 50%; width: calc(var(--_sz, var(--_s)) * .18); height: calc(var(--_sz, var(--_s)) * .62);
  margin: calc(var(--_sz, var(--_s)) * -.31) 0 0 calc(var(--_sz, var(--_s)) * -.37);
  background: currentColor; box-shadow: calc(var(--_sz, var(--_s)) * .28) 0 0 var(--_dim), calc(var(--_sz, var(--_s)) * .56) 0 0 var(--_dim);
  transform: skewX(var(--ui-skew)); border-radius: 0; animation: {p}-bars 840ms steps(1, end) infinite;
}}
@keyframes {p}-bars {{
  0%   {{ background: currentColor; box-shadow: calc(var(--_sz, var(--_s)) * .28) 0 0 var(--_dim), calc(var(--_sz, var(--_s)) * .56) 0 0 var(--_dim); }}
  33%  {{ background: var(--_dim); box-shadow: calc(var(--_sz, var(--_s)) * .28) 0 0 currentColor, calc(var(--_sz, var(--_s)) * .56) 0 0 var(--_dim); }}
  66%  {{ background: var(--_dim); box-shadow: calc(var(--_sz, var(--_s)) * .28) 0 0 var(--_dim), calc(var(--_sz, var(--_s)) * .56) 0 0 currentColor; }}
}}
/* placeholder art — diagonal bands at the logo angle + the mark cropped at the edge */
.{p}-ph {{ background-color: var(--color-surface-brand-soft); background-image:
  linear-gradient({180 - angle:g}deg, transparent 54%, color-mix(in srgb, var(--color-brand-primary) 14%, transparent) 54% 72%, transparent 72%),
  repeating-linear-gradient({180 - angle:g}deg, transparent 0 17px, color-mix(in srgb, var(--color-text-primary) 7%, transparent) 17px 18px); }}""")
    elif fam == 'round':
        out.append(f"""
.{p}-breadcrumbs li + li::before {{ width: 6px; height: 6px; border-right: 1.5px solid var(--color-text-tertiary); border-bottom: 1.5px solid var(--color-text-tertiary); transform: rotate(-45deg); margin: 0 12px 0 8px; }}
.{p}-list:not(.{p}-list--check, .{p}-list--divided) > li::before {{ background: var(--ui-line); border-radius: 50%; width: .5em; height: .5em; top: .52em; }}
.{p}-divider--motif {{ background: currentColor; -webkit-mask: linear-gradient(#000 0 0) left 50% / calc(50% - 22px) 1px no-repeat, linear-gradient(#000 0 0) right 50% / calc(50% - 22px) 1px no-repeat, radial-gradient(circle, #000 0 3px, transparent 3.5px 6px, #000 6.5px 8px, transparent 8.5px) center / 18px 18px no-repeat;
  mask: linear-gradient(#000 0 0) left 50% / calc(50% - 22px) 1px no-repeat, linear-gradient(#000 0 0) right 50% / calc(50% - 22px) 1px no-repeat, radial-gradient(circle, #000 0 3px, transparent 3.5px 6px, #000 6.5px 8px, transparent 8.5px) center / 18px 18px no-repeat; }}
.{p}-nav__link {{ --_npx: 14px; border-radius: var(--radius-pill); }}
.{p}-nav__link:is(:hover, .is-hover) {{ background: var(--ui-tint); }}
.{p}-nav__link:is([aria-current="page"], [aria-current="true"]) {{ background: var(--color-surface-brand-soft); }}
.{p}-tabs__tab::after {{ border-radius: 3px 3px 0 0; }}
.{p}-lang__link {{ border-radius: var(--radius-pill); }}
.{p}-lang__link[aria-current="true"] {{ box-shadow: none; background: var(--color-surface-brand-soft); }}
.{p}-table-wrap {{ border-radius: var(--ui-r-card); }}
/* spinner — a ring */
.{p}-spinner::before, .{p}-btn:is(.is-loading, [aria-busy="true"])::after {{
  content: ""; position: absolute; inset: 0; box-sizing: border-box; border-radius: 50%;
  border: max(2px, calc(var(--_sz, var(--_s)) * .12)) solid color-mix(in srgb, currentColor 22%, transparent); border-top-color: currentColor;
  animation: {p}-spin 800ms linear infinite;
}}
.{p}-btn:is(.is-loading, [aria-busy="true"])::after {{ inset: auto; width: var(--_sz); height: var(--_sz); }}
@keyframes {p}-spin {{ to {{ transform: rotate(360deg); }} }}
/* placeholder art — concentric rings around an off-centre point + the mark */
.{p}-ph {{ background-color: var(--color-surface-brand-soft); background-image:
  radial-gradient(circle at 82% 22%, color-mix(in srgb, var(--color-brand-primary) 30%, transparent) 0 7%, transparent 7.4%),
  repeating-radial-gradient(circle at 82% 22%, transparent 0 34px, color-mix(in srgb, var(--color-text-primary) 9%, transparent) 34px 35.5px); }}""")
    else:  # organic
        wave = "<svg xmlns='http://www.w3.org/2000/svg' width='48' height='16' viewBox='0 0 48 16'><path d='M0 8 C 8 2, 16 2, 24 8 S 40 14, 48 8' fill='none' stroke='#000' stroke-width='1.5' stroke-linecap='round'/></svg>"
        out.append(f"""
.{p}-breadcrumbs li + li::before {{ width: 4px; height: 4px; border-radius: 50%; background: var(--color-text-tertiary); margin: 0 12px; }}
.{p}-list:not(.{p}-list--check, .{p}-list--divided) > li::before {{ background: var(--ui-line); width: .62em; height: .5em; top: .5em; border-radius: 62% 38% 54% 46% / 52% 60% 40% 48%; }}
.{p}-divider--motif {{ background: currentColor; -webkit-mask: {_svg_url(wave)} 0 50% / 48px 16px repeat-x; mask: {_svg_url(wave)} 0 50% / 48px 16px repeat-x; opacity: .7; }}
.{p}-nav__link:is([aria-current="page"], [aria-current="true"]) {{ background: linear-gradient(transparent 58%, color-mix(in srgb, var(--ui-line) 26%, transparent) 58% 84%, transparent 84%); }}
.{p}-nav__link:is(:hover, .is-hover) {{ background: linear-gradient(transparent 58%, var(--ui-tint-strong) 58% 84%, transparent 84%); }}
.{p}-tabs__tab::after {{ height: 3px; border-radius: 3px; bottom: 6px; }}
.{p}-tabs:not(.{p}-tabs--pills, .{p}-tabs--boxed) .{p}-tabs__list {{ border-bottom-color: transparent; box-shadow: inset 0 -1px 0 var(--ui-hairline); }}
.{p}-card--flat {{ --_r: var(--radius-xl); }}
.{p}-testimonial {{ --_r: var(--radius-xl) var(--radius-xl) var(--radius-xl) var(--radius-sm); }}
.{p}-alert {{ --_r: var(--radius-lg); }}
/* spinner — a soft ring that eases */
.{p}-spinner::before, .{p}-btn:is(.is-loading, [aria-busy="true"])::after {{
  content: ""; position: absolute; inset: 0; box-sizing: border-box; border-radius: 50%;
  border: max(2px, calc(var(--_sz, var(--_s)) * .11)) solid color-mix(in srgb, currentColor 18%, transparent); border-top-color: currentColor; border-right-color: currentColor;
  animation: {p}-spin 1.2s var(--ease-standard) infinite;
}}
.{p}-btn:is(.is-loading, [aria-busy="true"])::after {{ inset: auto; width: var(--_sz); height: var(--_sz); }}
@keyframes {p}-spin {{ to {{ transform: rotate(360deg); }} }}
/* placeholder art — soft blobs + the mark */
.{p}-ph {{ background-color: var(--color-surface-brand-soft); background-image:
  radial-gradient(34% 30% at 24% 30%, color-mix(in srgb, var(--color-accent-soft) 92%, var(--color-brand-primary)) 0 98%, transparent 100%),
  radial-gradient(26% 32% at 70% 74%, color-mix(in srgb, var(--color-brand-primary) 12%, transparent) 0 98%, transparent 100%),
  radial-gradient(14% 12% at 88% 22%, color-mix(in srgb, var(--color-brand-primary) 20%, transparent) 0 98%, transparent 100%); }}""")
    # shared placeholder parts
    out.append(f"""
.{p}-ph {{ position: relative; display: block; width: 100%; height: 100%; overflow: hidden; color: color-mix(in srgb, var(--ui-line) 32%, transparent); }}
.{p}-ph--alt {{ background-color: var(--color-accent-soft); }}
.{p}-ph--quiet {{ background-color: var(--color-background-alt); }}
.{p}-ph__mark {{ position: absolute; width: 62%; height: auto; right: -10%; bottom: -14%; fill: currentColor; overflow: visible; }}
.{p}-ph--alt .{p}-ph__mark {{ right: auto; left: -8%; bottom: -22%; width: 58%; }}
.{p}-ph--quiet .{p}-ph__mark {{ width: 44%; right: 8%; bottom: auto; top: -10%; }}
[data-theme="contrast"] .{p}-ph {{ background-image: none; color: var(--color-border-subtle); }}""")
    return '\n'.join(out)


def languages(R, p, b):
    fams = {f.get('role'): f for f in (b.config.get('fonts') or {}).get('families', [])}
    stacks = b.stacks or {}
    rules = []
    for lang in b.langs:
        script = SCRIPTS.get(lang.split('-')[0])
        if not script:
            continue
        local = stacks.get(f'local-{script}') or (f"'{fams[f'local-{script}']['family']}', sans-serif" if f'local-{script}' in fams else '')
        body = '--ui-btn-tracking: .02em; --ui-title-tracking: 0em;'
        if local:
            body += f' --ui-title-family: {local}; --ui-btn-family: {local}; --ui-num-family: {local};'
        rules.append(f':lang({lang}) {{ {body} }}')
    if not rules:
        return ''
    return '/* ---- SCRIPTS · non-Latin languages of this brand: tighter tracking for set-in-caps styles, local script face where the foundation provides one ---- */\n' + '\n'.join(rules)


def preferences(R, p, plated):
    return f"""/* ======================================================================
   PREFERENCES · reduced motion · forced colours · print
   ====================================================================== */
@media (prefers-reduced-motion: reduce) {{
  .{p}-card, .{p}-btn, .{p}-chip {{ transform: none !important; }}
  .{p}-skeleton::after, .{p}-progress--indeterminate .{p}-progress__bar {{ animation: none; }}
  .{p}-spinner::before, .{p}-btn:is(.is-loading, [aria-busy="true"])::after {{ animation-duration: 2.4s !important; animation-iteration-count: infinite !important; }}
}}
@media (forced-colors: active) {{
  :where({plated}) {{ border: 1px solid CanvasText; }}
  :where({plated})::before {{ display: none; }}
  .{p}-btn--primary, .{p}-chip[aria-pressed="true"], .{p}-pagination__link[aria-current] {{ border: 2px solid Highlight; }}
  .{p}-check__input:checked, .{p}-switch__input:checked {{ background: Highlight; }}
  .{p}-progress__bar, .{p}-meter > i.is-on {{ background: Highlight; }}
  .{p}-tag, .{p}-badge {{ border: 1px solid CanvasText; }}
  .{p}-tabs__tab[aria-selected="true"]::after, .{p}-nav__link[aria-current]::after {{ background: Highlight; }}
}}
@media print {{
  .{p}-header, .{p}-menu, .{p}-toaster, .{p}-btn, .{p}-modal:not([open]) {{ display: none !important; }}
  .{p}-card, .{p}-alert {{ break-inside: avoid; filter: none; box-shadow: none; }}
}}
"""
