"""
gallery.py — UI-DESIGN-SYSTEM/components/index.html: documentation + live component gallery.

Examples are written with the neutral prefix `P-` (classes) / `data-P-` (hooks) and tokens:
  [[i:name]]   icon span (pre-filled with the fallback SVG, replaced by {{G}}.icon at runtime)
  [[ph]] [[ph:alt]] [[ph:quiet]]   placeholder art (brand-tinted field + cropped mark)
The live HTML and the code snippet are produced from the same source string.
"""
import datetime, html as _h, json, os, re, textwrap
from icons import ALIASES

MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
PAGE_LABEL = {'about': 'About', 'contact': 'Contact', 'careers': 'Careers', 'menu': None, 'visit': 'Visit', 'admissions': 'Admissions',
              'donate': 'Donate', 'shop': 'Shop', 'pricing': 'Pricing', 'docs': 'Docs', 'locations': 'Locations', 'book': 'Book'}


def esc(s):
    return _h.escape(str(s if s is not None else ''), quote=True)


class Gallery:
    def __init__(self, b, R, icons, at='UI-DESIGN-SYSTEM/components'):
        self.b, self.R, self.icons, self.at = b, R, icons, at
        self.p = b.p
        c = b.content or {}
        self.c = c
        self.L = dict(b.labels or {})
        self.offerings = c.get('offerings') or []
        self.units = {u.get('key'): u for u in (c.get('units') or [])}
        self.unit_list = c.get('units') or []
        self.sample = bool(c.get('_sample'))
        self.n_examples = 0
        self.brand_icons = self.load_brand_icons()

    def load_brand_icons(self):
        """Names (+ aliases) the brand icon set (<p>-icons.js from the icons module) can render; None when absent."""
        path = self.b.path('SOURCE', 'JS', f'{self.p}-icons.js')
        if not os.path.exists(path):
            return None
        t = open(path, encoding='utf-8').read()
        names = set(re.findall(r'^\s*"([a-z0-9][a-z0-9-]*)":\s*\[', t, re.M))
        for grp in re.findall(r'"aliases":\s*\[([^\]]*)\]', t):
            names.update(re.findall(r'"([a-z0-9-]+)"', grp))
        return names or None

    # ------------------------------------------------------------------ helpers
    def rel(self, target):
        return self.b.rel(self.at, target)

    def T(self, s):
        s = re.sub(r'data-P-', f'data-{self.p}-', s)
        return re.sub(r'(?<![A-Za-z0-9])P-(?=[a-z])', f'{self.p}-', s)

    def icon_svg(self, name):
        st = self.R['stroke']
        w = st.get('icon_px_at_24') or 1.75
        body = self.icons.get(name) or self.icons['dot']
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="{w}" '
                f'stroke-linecap="{st.get("cap", "round")}" stroke-linejoin="{st.get("join", "round")}" aria-hidden="true" focusable="false">{body}</svg>')

    def icon_span(self, name, fill=True):
        """Brand-set names (or one of their aliases) → data-P-icon (hydrated by <p>-icons.js); kit-only glyphs → data-P-ui-icon."""
        attr, use = 'icon', name
        if self.brand_icons is not None:
            hit = next((n for n in [name] + ALIASES.get(name, []) if n in self.brand_icons), None)
            attr, use = ('icon', hit) if hit else ('ui-icon', name)
        inner = self.icon_svg(name) if fill else ''
        return f'<span class="{self.p}-icon" data-{self.p}-{attr}="{use}" aria-hidden="true">{inner}</span>'

    def live(self, s):
        s = self.T(s)
        s = re.sub(r'\[\[i:([\w-]+)\]\]', lambda m: self.icon_span(m.group(1)), s)
        s = re.sub(r'\[\[ph(?::(\w+))?\]\]', lambda m: self.ph(m.group(1)), s)
        return s

    def code(self, s):
        s = self.T(textwrap.dedent(s).strip('\n'))
        s = re.sub(r'\[\[i:([\w-]+)\]\]', lambda m: self.icon_span(m.group(1), fill=False), s)
        s = re.sub(r'\[\[ph(?::(\w+))?\]\]', '<img src="photo.jpg" alt="Describe the image">', s)
        return esc(s)

    def use_mark(self, cls, extra=''):
        """<svg> showing the mark <symbol>; the outer viewBox starts at 0 0 and <use> gets an explicit size,
        so marks whose own viewBox does not start at the origin are not shifted out of view."""
        vb = [float(x) for x in str(self.mark_vb).split()]
        w, h = vb[2], vb[3]
        return (f'<svg class="{cls}" viewBox="0 0 {w:g} {h:g}" preserveAspectRatio="xMidYMid meet"{extra}>'
                f'<use href="#{self.p}-mark-sil" x="0" y="0" width="{w:g}" height="{h:g}"/></svg>')

    def ph(self, variant=None):
        cls = f'{self.p}-ph' + (f' {self.p}-ph--{variant}' if variant else '')
        return f'<span class="{cls}" aria-hidden="true">{self.use_mark(self.p + "-ph__mark")}</span>'

    def ex(self, title, src, note='', stage='', open_code=False, show_code=True, wide=False):
        self.n_examples += 1
        n = self.n_examples
        code = (f'<details class="doc-code"{" open" if open_code else ""}><summary>HTML</summary>'
                f'<div class="doc-code__bar"><button type="button" class="{self.p}-btn {self.p}-btn--ghost {self.p}-btn--sm" data-{self.p}-copy="#code-{n}">Copy</button></div>'
                f'<pre class="{self.p}-snippet" id="code-{n}" tabindex="0"><code>{self.code(src)}</code></pre></details>') if show_code else ''
        head = f'<div class="doc-example__head"><h3 class="doc-example__title">{esc(title)}</h3>' + (f'<p class="doc-example__note">{note}</p>' if note else '') + '</div>'
        return (f'<div class="doc-example{" doc-example--wide" if wide else ""}" id="ex-{n}">{head}'
                f'<div class="doc-stage {self.p}-surface {stage}">{self.live(textwrap.dedent(src))}</div>{code}</div>')

    def section(self, sid, idx, group, title, lead, body):
        idx = len(self.toc) + 1                     # numbered in page order
        self.toc.append((sid, idx, group, title))
        return (f'<section class="doc-section" id="{sid}" aria-labelledby="{sid}-title">'
                f'<header class="doc-section__head"><p class="{self.p}-eyebrow"><span class="{self.p}-index">{idx:02d}</span> {esc(group)}</p>'
                f'<h2 class="doc-section__title" id="{sid}-title" style="--_fit:{self.fit(title)}">{esc(title)}</h2><p class="doc-section__lead">{lead}</p></header>'
                f'<div class="doc-section__body">{body}</div></section>')

    def fit(self, text, scale=1.0):
        """font-size cap in cqi so the longest word of `text` always fits its container (wide caps vs condensed faces)."""
        w = self.R.get('widths') or {'caps': .66, 'lower': .52}
        longest = max((len(x) for x in re.split(r'[\s/–—-]+', str(text)) if x), default=8)
        ratio = w['caps'] if self.R['case'] == 'upper' else (w['lower'] * .82 + w['caps'] * .18)
        return f'{100 / (longest * ratio * 1.08 * scale):.1f}cqi'

    def lab(self, key, default):
        return self.L.get(key) or default

    def unit_name(self, key):
        u = self.units.get(key)
        return u.get('name') if u else ''

    @staticmethod
    def date_parts(d):
        try:
            dt = datetime.date.fromisoformat(d)
            return dt.day, MONTHS[dt.month - 1], dt.year, dt
        except Exception:
            return '', '', '', None

    def nav_items(self):
        pages = (self.b.profile or {}).get('pages') or []
        out = []
        keymap = {'units': 'units', 'offerings': 'offerings', 'projects': 'projects', 'events': 'events', 'people': 'people',
                  'insights': 'posts', 'posts': 'posts', 'news': 'posts', 'journal': 'posts', 'blog': 'posts', 'stories': 'projects'}
        for pg in pages:
            if pg in ('home', 'privacy') or pg.endswith('-detail') or pg in ('post', 'person', 'project', 'event'):
                continue
            if pg in keymap and self.L.get(keymap[pg]):
                lab = self.L[keymap[pg]]
            elif PAGE_LABEL.get(pg):
                lab = PAGE_LABEL[pg]
            elif pg in self.L:
                lab = self.L[pg]
            else:
                continue
            if lab not in out:
                out.append(lab)
        for k in ('offerings', 'projects', 'posts'):
            if len(out) < 4 and self.L.get(k) and self.L[k] not in out:
                out.append(self.L[k])
        if 'About' not in out:
            out.append('About')
        return out[:5]

    # ------------------------------------------------------------------ logo
    def logo(self, size=36, footer=False, href='#top', label=None):
        b, p = self.b, self.p
        lt = b.logo_type
        arr = (b.parts or {}).get('arrangement')
        wm = self.wordmark
        name = esc(label or f'{b.name} — home')
        S = lambda n: self.rel(f'LOGO/SVG/{n}.svg')
        exists = lambda n: os.path.exists(b.path('LOGO', 'SVG', n + '.svg'))
        if lt in ('wordmark',) or (lt == 'combination' and arr != 'stacked'):
            light, dark = 'logo-original', 'logo-original-on-dark' if exists('logo-original-on-dark') else 'logo-original-white'
            vb = self.svg_vb('logo-original')
            h = size * (0.78 if lt == 'wordmark' else 1.15)
            w = h * vb[2] / vb[3] if vb else h * 3
            mark = (f'<span class="{p}-logo__mark" style="height:{h:.0f}px;width:{w:.0f}px"><img class="{p}-logo__img--light" src="{S(light)}" alt="" width="{w:.0f}" height="{h:.0f}">'
                    f'<img class="{p}-logo__img--dark" src="{S(dark)}" alt="" width="{w:.0f}" height="{h:.0f}"></span>')
            return f'<a class="{p}-logo" href="{href}" style="--_h:{h:.0f}px">{mark}<span class="sr-only">{name}</span></a>'
        # symbol / emblem / stacked combination → symbol + lettering (traced) or typeset name line
        item = None
        if lt == 'combination':
            item = wm.get('lettering') or wm.get('line')
        else:
            item = wm.get('line') or wm.get('line_1') or wm.get('stacked')
        sym_light = 'symbol-small' if exists('symbol-small') else 'symbol'
        sym_dark = 'symbol-small-on-dark' if exists('symbol-small-on-dark') else 'symbol-white'
        vb = self.svg_vb(sym_light) or [0, 0, 1, 1]
        h = size * (1.25 if lt == 'emblem' else 1.1)
        w = h * vb[2] / vb[3]
        mark = (f'<span class="{p}-logo__mark" style="height:{h:.0f}px;width:{w:.0f}px"><img class="{p}-logo__img--light" src="{S(sym_light)}" alt="" width="{w:.0f}" height="{h:.0f}">'
                f'<img class="{p}-logo__img--dark" src="{S(sym_dark)}" alt="" width="{w:.0f}" height="{h:.0f}"></span>')
        word = ''
        if item:
            ivb = [float(x) for x in str(item.get('vb', '0 0 1 1')).split()]
            ratio = ivb[2] / ivb[3] if ivb[3] else 4
            wh = 0.9 if ratio < 2.6 else (0.4 if lt != 'emblem' else 0.36)
            body = item.get('body', '')
            mk = lambda cls, bd: (f'<svg class="{p}-logo__word{cls}" viewBox="{item.get("vb")}" style="--_wh:{wh}" aria-hidden="true" focusable="false" '
                                  f'fill="currentColor" fill-rule="evenodd">{bd}</svg>')
            if re.search(r'fill="#[0-9A-Fa-f]{3,8}"', body):
                # traced lettering keeps its own colours on light grounds; one colour (currentColor) on dark / contrast
                one = re.sub(r'fill="#[0-9A-Fa-f]{3,8}"', 'fill="currentColor"', body)
                word = mk(f' {p}-logo__img--light', body) + mk(f' {p}-logo__img--dark', one)
            else:
                word = mk('', body)
        return f'<a class="{p}-logo" href="{href}" style="--_h:{h:.0f}px">{mark}{word}<span class="sr-only">{name}</span></a>'

    def svg_vb(self, name):
        path = self.b.path('LOGO', 'SVG', name + '.svg')
        if not os.path.exists(path):
            return None
        m = re.search(r'viewBox="([^"]+)"', open(path, encoding='utf-8').read()[:600])
        try:
            return [float(x) for x in m.group(1).replace(',', ' ').split()] if m else None
        except ValueError:
            return None

    # ------------------------------------------------------------------ page
    def build(self, ui_version='1.0.0'):
        b, p, R = self.b, self.p, self.R
        self.toc = []
        self.wordmark = self.load_wordmark()
        sil = self.mark_symbol()
        L = self.L
        cta1, cta2 = L.get('cta_primary') or 'Get in touch', L.get('cta_secondary') or 'Learn more'
        nav = self.nav_items()
        sections = [
            self.s_buttons(cta1, cta2),
            self.s_forms(),
            self.s_tags(),
            self.s_cards(cta1),
            self.s_disclosure(),
            self.s_identity(cta1, cta2),
            self.s_data(),
            self.s_navigation(nav, cta1),
            self.s_feedback(),
            self.s_progress(),
            self.s_overlays(cta1),
            self.s_language(),
            self.s_theming(cta1),
            self.s_access(),
        ]
        groups = []
        for sid, idx, group, title in self.toc:
            if not groups or groups[-1][0] != group:
                groups.append((group, []))
            groups[-1][1].append((sid, idx, title))
        side = ''.join(f'<li class="doc-side__group"><span class="doc-side__group-title">{esc(g)}</span><ul>' +
                       ''.join(f'<li><a href="#{sid}"><span>{idx:02d}</span>{esc(t)}</a></li>' for sid, idx, t in items) + '</ul></li>' for g, items in groups)
        top_nav = ''.join(f'<li><a class="{p}-nav__link" href="#{items[0][0]}">{esc(g)}</a></li>' for g, items in groups[:6])
        theme_sw = self.theme_switch('doc-theme')
        menu_links = ''.join(f'<li><a class="{p}-menu__link" href="#{sid}">{esc(t)}[[i:arrow-right]]</a></li>' for sid, idx, g, t in self.toc)
        header = f'''
<header class="{p}-header {p}-header--sticky doc-top" data-{p}-header>
  <div class="{p}-header__inner">
    <div class="{p}-header__logo doc-top__brand">{self.logo(30, href="#top", label=f"{b.name} — UI kit")}<span class="doc-top__label">UI kit</span></div>
    <nav class="{p}-nav" aria-label="Component groups"><ul class="{p}-nav__list">{top_nav}</ul></nav>
    <div class="{p}-header__actions">{theme_sw}
      <button type="button" class="{p}-btn {p}-btn--ghost {p}-btn--icon {p}-header__menu-btn" aria-label="Open menu" aria-controls="doc-menu" data-{p}-menu-toggle>{self.live("[[i:menu]]")}</button>
    </div>
  </div>
</header>
<div class="{p}-menu" id="doc-menu" role="dialog" aria-modal="true" aria-label="Sections" hidden>
  <div class="{p}-menu__panel">
    <div class="{p}-menu__top">{self.logo(26, href="#top", label=f"{b.name} — UI kit")}<button type="button" class="{p}-btn {p}-btn--ghost {p}-btn--icon" aria-label="Close menu" data-{p}-menu-close>{self.live("[[i:close]]")}</button></div>
    <ul class="{p}-menu__list">{self.live(menu_links)}</ul>
    <div class="{p}-menu__footer">{self.theme_switch('menu-theme')}</div>
  </div>
</div>'''
        hero = self.hero(cta1, cta2)
        footer = self.footer(nav, cta1)
        dialogs = self.dialogs(cta1)
        body = (f'<a class="{p}-skip-link" href="#main">Skip to content</a>{sil}{header}'
                f'<div class="doc-layout"><nav class="doc-side" aria-label="Components"><ul>{side}</ul></nav>'
                f'<main id="main" class="doc-main" tabindex="-1">{hero}{"".join(sections)}</main></div>{footer}{dialogs}'
                f'<ol class="{p}-toaster" aria-live="polite" aria-label="Notifications"></ol>')
        return body

    def load_wordmark(self):
        path = self.b.path('SOURCE', 'JS', 'wordmark-data.js')
        if not os.path.exists(path):
            return {}
        s = open(path, encoding='utf-8').read()
        m = re.search(r'window\.\w+\s*=\s*(\{.*\})\s*;?\s*$', s, re.S)
        try:
            return (json.loads(m.group(1)).get('items') or {}) if m else {}
        except Exception:
            return {}

    def mark_symbol(self):
        """<symbol> with the mark silhouette (wordmark logos: the monogram) for placeholders and empty states."""
        b = self.b
        if b.logo_type == 'wordmark' and self.wordmark.get('monogram'):
            it = self.wordmark['monogram']
            self.mark_vb = it.get('vb')
            inner = it.get('body', '')
        else:
            m = b.mark or {}
            vb = m.get('viewBox') or [0, 0, 100, 100]
            self.mark_vb = ' '.join(f'{v:g}' if isinstance(v, (int, float)) else str(v) for v in vb)
            inner = f'<path fill-rule="evenodd" d="{m.get("silhouette_d") or m.get("silhouette_simple_d") or "M0 0h100v100H0z"}"/>'
        return (f'<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false"><defs>'
                f'<symbol id="{self.p}-mark-sil" viewBox="{self.mark_vb}">{inner}</symbol></defs></svg>')

    def theme_switch(self, name):
        p = self.p
        opts = [('auto', 'Auto', 'settings'), ('light', 'Light', 'sun'), ('dark', 'Dark', 'moon'), ('contrast', 'Contrast', 'contrast')]
        items = ''.join(f'<label class="{p}-segmented__option"><input class="{p}-segmented__input" type="radio" name="{name}" value="{v}"{" checked" if v == "auto" else ""}>'
                        f'<span class="{p}-segmented__label">{self.live(f"[[i:{ic}]]")}<span class="doc-theme__text">{lab}</span></span></label>' for v, lab, ic in opts)
        return f'<fieldset class="{p}-segmented doc-theme" data-{p}-theme-switch><legend class="sr-only">Theme</legend>{items}</fieldset>'

    # ------------------------------------------------------------------ hero (overview)
    def hero(self, cta1, cta2):
        b, R, p, L = self.b, self.R, self.p, self.L
        off = self.offerings[0] if self.offerings else {'name': L.get('offerings', 'Offering'), 'summary': b.brand.get('tagline', '')}
        unit = self.unit_name(off.get('unit')) or (self.unit_list[0]['name'] if self.unit_list else '')
        price = off.get('price')
        shape = {'cut': f"Cut · {R['angle']:g}°" + (' ×2' if R['facets'] else ''), 'round': 'Round · pills', 'soft': 'Soft · large radii',
                 'rounded': 'Rounded', 'square': 'Square'}[R['corner']]
        facts = [('Corner', shape), ('Depth', R['shadow'].capitalize()), ('Motion', f"{R['motion'].capitalize()} · {R['energy']:.2f}"),
                 ('Density', R['density'].capitalize()), ('Display', f"{b.fonts.get('display', '')} · {R['case']}")]
        fact_html = ''.join(f'<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k, v in facts)
        chips = ''.join(f'<button type="button" class="P-chip" aria-pressed="{"true" if i == 0 else "false"}"><span class="P-chip__check">[[i:check]]</span>{esc(u.get("name"))}</button>'
                        for i, u in enumerate(self.unit_list[:3]))
        price_html = (f'<p class="P-card__price"><small>Price</small>{esc(price)}</p>' if price else
                      f'<span class="P-btn P-btn--link">{esc(cta2)} [[i:arrow-right]]</span>')
        tag = f'<span class="P-tag">{esc(unit)}</span>' if unit else ''
        spec = f'''
<div class="doc-spec" aria-label="Overview of the components">
  <article class="P-card P-card--offering doc-spec__card">
    <div class="P-card__media">[[ph]]</div>
    <div class="P-card__body">
      <div class="P-card__meta">{tag or '<span>' + esc(L.get("offerings", "")) + '</span>'}</div>
      <h3 class="P-card__title"><a class="P-card__link" href="#cards">{esc(off.get("name"))}</a></h3>
      <p class="P-card__text">{esc(off.get("summary", ""))}</p>
      <div class="doc-spec__row">{price_html}</div>
    </div>
  </article>
  <div class="doc-spec__panel P-surface">
    <div class="P-field">
      <label class="P-field__label" for="spec-email">Email</label>
      <input class="P-input is-focus" id="spec-email" type="email" value="{esc((b.content.get("contact") or {}).get("email", "name@example.com"))}">
    </div>
    <div class="P-chip-group">{chips}</div>
    <label class="P-switch"><input class="P-switch__input" type="checkbox" role="switch" checked> <span>Updates by email</span></label>
    <div class="P-btn-group"><button type="button" class="P-btn P-btn--primary">{esc(cta1)} [[i:arrow-right]]</button><button type="button" class="P-btn P-btn--secondary">{esc(cta2)}</button></div>
  </div>
  <div class="P-toast P-toast--success P-toast--static doc-spec__toast" role="status">
    <span class="P-toast__icon">[[i:check]]</span>
    <div class="P-toast__body"><p class="P-toast__title">Saved</p><p class="P-toast__text">Your changes are live.</p></div>
  </div>
</div>'''
        n_comp = 48
        sample = f'<p class="{p}-sample">Sample content — replace in SOURCE/CONFIG/content.json</p>' if self.sample else ''
        tagline = esc(b.brand.get('tagline') or (b.content.get('brand') or {}).get('tagline') or '')
        return f'''
<section class="doc-hero" id="top" aria-labelledby="top-title">
  <div class="doc-hero__text">
    <p class="{p}-eyebrow"><span class="{p}-index">UI</span> {esc(b.name)} · Design system</p>
    <h1 class="doc-hero__title" id="top-title" style="--_fit:{self.fit("Interface components")}">Interface components</h1>
    <p class="doc-hero__lead">{n_comp}+ components generated from the {esc(b.name)} design DNA — {esc(self.summary_text())}. Light, dark and high-contrast themes, keyboard-first, WCAG&nbsp;AA.</p>
    <dl class="doc-facts">{fact_html}</dl>
    <div class="{p}-btn-group"><a class="{p}-btn {p}-btn--primary" href="#buttons">Browse components{self.live(" [[i:arrow-right]]")}</a><a class="{p}-btn {p}-btn--ghost" href="#theming">Theming</a></div>
    {sample}
  </div>
  {self.live(spec)}
</section>'''

    def summary_text(self):
        R = self.R
        shape = {'cut': f"chamfered corners at {R['angle']:g}°", 'round': 'pill shapes and generous radii', 'soft': 'large soft radii',
                 'rounded': 'moderate radii', 'square': 'crisp square corners'}[R['corner']]
        return f"{shape}, {R['shadow']} shadows, {R['motion']} motion and {R['density']} spacing"

    # ------------------------------------------------------------------ sections
    def s_buttons(self, cta1, cta2):
        variants = f'''
<div class="P-btn-group">
  <button type="button" class="P-btn P-btn--primary">{esc(cta1)}</button>
  <button type="button" class="P-btn P-btn--secondary">{esc(cta2)}</button>
  <button type="button" class="P-btn P-btn--ghost">Cancel</button>
  <button type="button" class="P-btn P-btn--link">Read more [[i:arrow-right]]</button>
  <button type="button" class="P-btn P-btn--destructive">[[i:close]] Delete</button>
</div>'''
        states = f'''
<div class="doc-grid doc-grid--states">
  <div><span class="doc-label">Rest</span><button type="button" class="P-btn P-btn--primary">{esc(cta1)}</button><button type="button" class="P-btn P-btn--secondary">{esc(cta2)}</button></div>
  <div><span class="doc-label">Hover</span><button type="button" class="P-btn P-btn--primary is-hover">{esc(cta1)}</button><button type="button" class="P-btn P-btn--secondary is-hover">{esc(cta2)}</button></div>
  <div><span class="doc-label">Focus</span><button type="button" class="P-btn P-btn--primary is-focus">{esc(cta1)}</button><button type="button" class="P-btn P-btn--secondary is-focus">{esc(cta2)}</button></div>
  <div><span class="doc-label">Pressed</span><button type="button" class="P-btn P-btn--primary is-active">{esc(cta1)}</button><button type="button" class="P-btn P-btn--secondary is-active">{esc(cta2)}</button></div>
  <div><span class="doc-label">Loading</span><button type="button" class="P-btn P-btn--primary" aria-busy="true" aria-label="{esc(cta1)}, loading"><span>{esc(cta1)}</span></button><button type="button" class="P-btn P-btn--secondary" aria-busy="true"><span>{esc(cta2)}</span></button></div>
  <div><span class="doc-label">Disabled</span><button type="button" class="P-btn P-btn--primary" disabled>{esc(cta1)}</button><button type="button" class="P-btn P-btn--secondary" disabled>{esc(cta2)}</button></div>
</div>'''
        sizes = f'''
<div class="P-btn-group">
  <button type="button" class="P-btn P-btn--primary P-btn--sm">Small</button>
  <button type="button" class="P-btn P-btn--primary">Medium</button>
  <button type="button" class="P-btn P-btn--primary P-btn--lg">{esc(cta1)} [[i:arrow-right]]</button>
  <button type="button" class="P-btn P-btn--secondary P-btn--icon P-btn--sm" aria-label="Add">[[i:plus]]</button>
  <button type="button" class="P-btn P-btn--secondary P-btn--icon" aria-label="Search">[[i:search]]</button>
  <button type="button" class="P-btn P-btn--primary P-btn--icon P-btn--lg" aria-label="Next">[[i:arrow-right]]</button>
  <button type="button" class="P-btn P-btn--ghost P-btn--icon" aria-label="Menu">[[i:menu]]</button>
</div>'''
        fields = f'''
<div class="doc-split">
  <div class="P-on-brand doc-pad"><div class="P-btn-group"><button type="button" class="P-btn P-btn--primary">{esc(cta1)}</button><button type="button" class="P-btn P-btn--secondary">{esc(cta2)}</button></div></div>
  <div class="P-scope doc-pad" data-theme="dark"><div class="P-btn-group"><button type="button" class="P-btn P-btn--primary">{esc(cta1)}</button><button type="button" class="P-btn P-btn--secondary">{esc(cta2)}</button></div></div>
</div>'''
        body = (self.ex('Variants', variants, 'One primary action per view. Secondary for alternatives, ghost for quiet tool actions, link for inline moves, destructive only for irreversible actions.', open_code=True) +
                self.ex('States', states, 'Hover, focus and pressed are shown with snapshot classes (<code class="P-code">.is-hover</code> …) — real interaction uses the pseudo-classes. Loading keeps the label width and sets <code class="P-code">aria-busy</code>.') +
                self.ex('Sizes & icon buttons', sizes, 'Small buttons keep a 44px hit area. Icon-only buttons need an <code class="P-code">aria-label</code>.') +
                self.ex('On brand and dark fields', fields, 'Inside <code class="P-code">.P-on-brand</code> the primary button inverts automatically; any element can carry <code class="P-code">data-theme</code>.', stage='doc-stage--flush'))
        return self.section('buttons', 1, 'Actions', 'Buttons', self.T('<code class="P-code">.P-btn</code> + a variant. Shape, depth and motion follow the design DNA: ') + esc(self.summary_text()) + '.', self.T(body))

    def s_forms(self):
        L = self.L
        opts = ''.join(f'<option>{esc(o.get("name"))}</option>' for o in self.offerings[:6]) or '<option>General enquiry</option>'
        fields = f'''
<div class="doc-grid doc-grid--2">
  <div class="P-field">
    <label class="P-field__label" for="f-name">Full name <span class="P-field__req">Required</span></label>
    <input class="P-input" id="f-name" autocomplete="name" placeholder="Alex Example">
  </div>
  <div class="P-field">
    <label class="P-field__label" for="f-email">Email</label>
    <p class="P-field__hint" id="f-email-hint">We reply within two working days.</p>
    <input class="P-input" id="f-email" type="email" aria-describedby="f-email-hint" value="name@example">
  </div>
  <div class="P-field">
    <label class="P-field__label" for="f-err">Phone</label>
    <input class="P-input" id="f-err" type="tel" aria-invalid="true" aria-describedby="f-err-msg" value="12">
    <p class="P-msg P-msg--error" id="f-err-msg">[[i:error]]<span><span class="sr-only">Error: </span>Enter a phone number with at least 7 digits</span></p>
  </div>
  <div class="P-field">
    <label class="P-field__label" for="f-sel">{esc(L.get("offerings", "Topic"))}</label>
    <span class="P-select"><select id="f-sel">{opts}</select></span>
  </div>
  <div class="P-field">
    <label class="P-field__label" for="f-dis">Reference</label>
    <input class="P-input" id="f-dis" value="Not editable" disabled>
  </div>
  <div class="P-field">
    <label class="P-field__label" for="f-ok">Postcode</label>
    <input class="P-input is-focus" id="f-ok" value="Focused">
  </div>
</div>'''
        text = f'''
<div class="doc-grid doc-grid--2">
  <div class="P-field">
    <label class="P-field__label" for="f-msg">Message <span class="P-field__opt">Optional</span></label>
    <textarea class="P-textarea" id="f-msg" maxlength="400" data-P-count placeholder="Tell us a little about your plans"></textarea>
  </div>
  <div class="doc-stack">
    <div class="P-field">
      <label class="P-field__label" for="f-search">Search</label>
      <div class="P-search" data-P-search>[[i:search]]<input class="P-input" id="f-search" type="search" placeholder="Search {esc(L.get("offerings", "").lower())}" value="{esc(self.offerings[0]["name"] if self.offerings else "")}"><button type="button" class="P-close P-search__clear" aria-label="Clear search">[[i:close]]</button></div>
    </div>
    <div class="P-field">
      <label class="P-field__label" for="f-range">Priority</label>
      <div class="P-range"><input class="P-range__input" id="f-range" type="range" min="1" max="5" value="3" data-P-range><output class="P-range__output" for="f-range">3</output></div>
    </div>
  </div>
</div>'''
        choices = '''
<div class="doc-grid doc-grid--3">
  <fieldset class="P-fieldset">
    <legend class="P-fieldset__legend">Contact me by</legend>
    <div class="P-choices">
      <label class="P-radio"><input class="P-radio__input" type="radio" name="f-by" checked> <span>Email</span></label>
      <label class="P-radio"><input class="P-radio__input" type="radio" name="f-by"> <span>Phone</span></label>
      <label class="P-radio"><input class="P-radio__input" type="radio" name="f-by" disabled> <span>Post (unavailable)</span></label>
    </div>
  </fieldset>
  <fieldset class="P-fieldset">
    <legend class="P-fieldset__legend">Interests</legend>
    <div class="P-choices">
      <label class="P-check"><input class="P-check__input" type="checkbox" checked> <span>News and updates</span></label>
      <label class="P-check"><input class="P-check__input" type="checkbox"> <span>Events</span></label>
      <label class="P-check"><input class="P-check__input" type="checkbox" disabled checked> <span>Service messages</span></label>
    </div>
  </fieldset>
  <fieldset class="P-fieldset">
    <legend class="P-fieldset__legend">Settings</legend>
    <div class="P-choices">
      <label class="P-switch"><input class="P-switch__input" type="checkbox" role="switch" checked> <span>Notifications</span></label>
      <label class="P-switch"><input class="P-switch__input" type="checkbox" role="switch"> <span>Compact view</span></label>
      <label class="P-switch"><input class="P-switch__input" type="checkbox" role="switch" disabled> <span>Beta features</span></label>
    </div>
  </fieldset>
</div>'''
        upload = '''
<div class="P-field">
  <span class="P-field__label" id="f-file-label">Attachments</span>
  <div class="P-file" data-P-file>
    <input class="P-file__input" id="f-file" type="file" multiple aria-labelledby="f-file-label f-file-meta">
    <label class="P-file__zone" for="f-file">
      <span class="P-file__icon">[[i:upload]]</span>
      <span class="P-file__title">Drop files here or <span class="P-file__browse">browse</span></span>
      <span class="P-file__meta" id="f-file-meta">PDF, JPG or PNG · up to 10 MB each</span>
    </label>
    <ul class="P-file__list"></ul>
  </div>
</div>'''
        form = f'''
<form class="P-form" data-P-validate data-P-demo="Thanks — your message is on its way" action="#" novalidate>
  <div class="P-error-summary" role="alert" hidden>
    <h3 class="P-error-summary__title">[[i:error]] Check the highlighted fields</h3>
    <ul></ul>
  </div>
  <div class="P-form__row">
    <div class="P-field"><label class="P-field__label" for="v-name">Full name</label><input class="P-input" id="v-name" name="name" autocomplete="name" required></div>
    <div class="P-field"><label class="P-field__label" for="v-email">Email</label><input class="P-input" id="v-email" name="email" type="email" autocomplete="email" required></div>
  </div>
  <div class="P-field"><label class="P-field__label" for="v-topic">{esc(L.get("offerings", "Topic"))}</label>
    <span class="P-select"><select id="v-topic" name="topic" required><option value="">Choose one</option>{opts}</select></span></div>
  <div class="P-field"><label class="P-field__label" for="v-msg">Message</label><textarea class="P-textarea" id="v-msg" name="message" minlength="10" maxlength="400" data-P-count required></textarea></div>
  <label class="P-check"><input class="P-check__input" type="checkbox" name="consent" required data-msg-required="Agree to the privacy notice to continue"> <span>I agree to the privacy notice</span></label>
  <div class="P-form__actions"><button type="submit" class="P-btn P-btn--primary">Send message</button><button type="reset" class="P-btn P-btn--ghost">Clear</button></div>
</form>'''
        body = (self.ex('Text fields & select', fields, 'Labels are always visible; hints and errors are linked with <code class="P-code">aria-describedby</code>. Errors combine an icon, colour and words.', open_code=True) +
                self.ex('Textarea, search & range', text, 'The counter is live (<code class="P-code">data-P-count</code>); search clears with the button or Esc; the range fill follows its value.') +
                self.ex('Checkboxes, radios & switches', choices, 'Group related options in a <code class="P-code">fieldset</code> with a <code class="P-code">legend</code>. Switches act immediately; checkboxes are submitted.') +
                self.ex('File upload', upload, 'The native input stays in the tab order (visually hidden); drag &amp; drop is an enhancement.') +
                self.ex('Form layout & validation', form, 'Try submitting empty: an error summary takes focus and links to each field; fields re-validate as you type. <code class="P-code">form[data-P-validate]</code>.'))
        return self.section('forms', 2, 'Forms', 'Inputs & forms', 'Text inputs, selects, choices, switches, range and file — with labels, hints, errors and a validating form layout.', self.T(body))

    def s_tags(self):
        units = self.unit_list[:4]
        tags = ''.join(f'<span class="P-tag">{esc(u.get("name"))}</span>' for u in units[:2])
        tags += ''.join(f'<span class="P-tag P-tag--outline">{esc(u.get("name"))}</span>' for u in units[2:4])
        tags += f'<span class="P-tag P-tag--brand">{esc(self.L.get("events", "Event"))}</span><span class="P-tag P-tag--accent">{esc(self.L.get("posts", "News"))}</span><span class="P-tag P-tag--neutral">Draft</span>'
        badges = '''
<div class="P-tag-group">
  <span class="P-badge P-badge--success">Confirmed</span>
  <span class="P-badge P-badge--warning">Pending</span>
  <span class="P-badge P-badge--error">Cancelled</span>
  <span class="P-badge P-badge--info">New</span>
  <span class="P-badge P-badge--brand">Featured</span>
  <span class="P-badge P-badge--outline">Archived</span>
  <span class="P-badge P-badge--dot P-badge--live" style="--_c: var(--color-error)">Live</span>
  <span class="P-badge P-badge--count" aria-label="3 unread">3</span>
</div>'''
        chip_items = ''.join(f'<button type="button" class="P-chip" aria-pressed="{"true" if i == 0 else "false"}"><span class="P-chip__check">[[i:check]]</span>{esc(u.get("name"))}</button>' for i, u in enumerate(self.unit_list[:4]))
        city = (self.c.get('contact') or {}).get('city') or 'City'
        chips = f'''
<div class="P-chip-group" role="group" aria-label="Filter by {esc(self.L.get("units", "category").lower())}">
  {chip_items}
  <span class="P-chip P-chip--static">{esc(city)} <button type="button" class="P-chip__remove" aria-label="Remove {esc(city)}">[[i:close]]</button></span>
</div>'''
        body = (self.ex('Tags', f'<div class="P-tag-group">{tags}</div>', f'Tags label content with a {esc(self.L.get("units", "category").lower())} or type. They are not interactive.', open_code=True) +
                self.ex('Badges', badges, 'Status words always carry the meaning; the dot only repeats it.') +
                self.ex('Chips (filters)', chips, 'Toggle buttons with <code class="P-code">aria-pressed</code>; removable chips have a labelled remove button.'))
        return self.section('tags', 3, 'Content', 'Tags, badges & chips', 'Small labels for categories, status and filters.', self.T(body))

    def s_cards(self, cta1):
        L, c = self.L, self.c
        offs = self.offerings[:3]
        off_cards = ''
        for i, o in enumerate(offs):
            unit = self.unit_name(o.get('unit'))
            u = self.units.get(o.get('unit')) or {}
            price = f'<p class="P-card__price"><small>Price</small>{esc(o["price"])}</p>' if o.get('price') else ''
            off_cards += f'''
  <article class="P-card P-card--offering">
    <div class="P-card__body">
      <span class="P-card__icon">[[i:{esc(u.get("icon") or "star")}]]</span>
      <div class="P-card__meta"><span>{esc(unit)}</span></div>
      <h3 class="P-card__title"><a class="P-card__link" href="#cards">{esc(o.get("name"))}</a></h3>
      <p class="P-card__text">{esc(o.get("summary", ""))}</p>
      <div class="doc-card-foot">{price}<span class="P-card__arrow">[[i:arrow-right]]</span></div>
    </div>
  </article>'''
        projects = (c.get('projects') or [])[:3]
        media_cards = ''
        for i, pr in enumerate(projects):
            unit = self.unit_name(pr.get('unit'))
            media_cards += f'''
  <article class="P-card">
    <div class="P-card__media">[[ph{":alt" if i == 1 else (":quiet" if i == 2 else "")}]]</div>
    <div class="P-card__body">
      <div class="P-card__meta"><span class="P-tag">{esc(unit)}</span><span>{esc(pr.get("year", ""))}</span></div>
      <h3 class="P-card__title"><a class="P-card__link" href="#cards">{esc(pr.get("title"))}</a></h3>
      <p class="P-card__text">{esc(pr.get("summary", ""))}</p>
    </div>
  </article>'''
        stats = (c.get('stats') or [])[:3]
        stat_cards = ''.join(f'''
  <article class="P-card P-card--stat">
    <div class="P-card__body">
      <p class="P-card__label">{esc(s.get("label"))}</p>
      <p class="P-card__value">{esc(s.get("value"))}<small>{esc(s.get("unit", ""))}</small></p>
    </div>
  </article>''' for s in stats)
        people = (c.get('people') or [])[:3]
        prof = ''.join(f'''
  <article class="P-card P-card--profile">
    <div class="P-card__body">
      <span class="P-avatar P-avatar--lg{" P-avatar--brand" if i == 0 else (" P-avatar--dark" if i == 2 else "")}" aria-hidden="true">{esc(pe.get("initials") or "".join(w[0] for w in pe.get("name", "?").split()[:2]))}</span>
      <h3 class="P-card__title"><a class="P-card__link" href="#cards">{esc(pe.get("name"))}</a></h3>
      <p class="P-card__role">{esc(pe.get("role", ""))}</p>
    </div>
  </article>''' for i, pe in enumerate(people))
        events = (c.get('events') or [])[:2]
        ev = ''
        for e in events:
            d, m, y, dt = self.date_parts(e.get('date', ''))
            ev += f'''
  <article class="P-card P-card--event">
    <p class="P-card__date"><time datetime="{esc(e.get("date", ""))}"><span class="P-card__day">{d}</span> <span class="P-card__month">{m} {y}</span></time></p>
    <div class="P-card__body">
      <div class="P-card__meta"><span>{esc(L.get("events", "Events"))}</span></div>
      <h3 class="P-card__title"><a class="P-card__link" href="#cards">{esc(e.get("title"))}</a></h3>
      <p class="P-card__where"><span>[[i:clock]] {esc(e.get("time", ""))}</span><span>[[i:pin]] {esc(e.get("place", ""))}</span></p>
    </div>
  </article>'''
        posts = (c.get('posts') or [])[:2]
        po = ''
        for i, pst in enumerate(posts):
            d, m, y, dt = self.date_parts(pst.get('date', ''))
            po += f'''
  <article class="P-card P-card--post P-card--horizontal">
    <div class="P-card__media">[[ph{":alt" if i else ":quiet"}]]</div>
    <div class="P-card__body">
      <div class="P-card__meta"><span>{esc(pst.get("category", ""))}</span><time datetime="{esc(pst.get("date", ""))}">{d} {m} {y}</time></div>
      <h3 class="P-card__title"><a class="P-card__link" href="#cards">{esc(pst.get("title"))}</a></h3>
      <p class="P-card__text">{esc(L.get("posts", "Posts"))} · {esc(self.b.name)}</p>
    </div>
  </article>'''
        body = ''
        if offs:
            body += self.ex(f'Offering — {L.get("offerings", "offerings")}', f'<div class="doc-cards">{off_cards}\n</div>', 'One stretched link per card: the whole card is clickable, assistive tech hears one link, the focus ring wraps the card.', open_code=True)
        if projects:
            body += self.ex(f'Media — {L.get("projects", "projects")}', f'<div class="doc-cards">{media_cards}\n</div>', 'Placeholder art = the brand field with the mark cropped at the edge. Replace with real photography (alt text required).')
        if stats:
            body += self.ex('Stat', f'<div class="doc-cards">{stat_cards}\n</div>', 'Big numbers use the display face; the label comes first in the reading order.')
        if people:
            body += self.ex(f'Profile — {L.get("people", "people")}', f'<div class="doc-cards">{prof}\n</div>')
        if events:
            body += self.ex(f'Event — {L.get("events", "events")}', f'<div class="doc-cards doc-cards--2">{ev}\n</div>', 'Dates use <code class="P-code">&lt;time datetime&gt;</code>; the date block moves on top when the card is narrow.')
        if posts:
            body += self.ex(f'Post — {L.get("posts", "posts")}', f'<div class="doc-cards doc-cards--2">{po}\n</div>')
        return self.section('cards', 4, 'Content', 'Cards', 'Containers for one subject each — built from content.json, labelled with the profile vocabulary.', self.T(body))

    def s_navigation(self, nav, cta1):
        p, L = self.p, self.L
        links = ''.join(f'<li><a class="P-nav__link" href="#navigation"{" aria-current=\"page\"" if i == 0 else ""}>{esc(n)}</a></li>' for i, n in enumerate(nav))
        langs = self.b.langs
        lang_html = ''.join(f'<li><a class="P-lang__link" href="#navigation" hreflang="{l}" lang="{l}"{" aria-current=\"true\"" if i == 0 else ""}>{l.upper()}</a></li>' for i, l in enumerate(langs))
        header = f'''
<header class="P-header">
  <div class="P-header__inner">
    <span class="P-header__logo">{self.logo(30, href="#navigation")}</span>
    <nav class="P-nav" aria-label="Main"><ul class="P-nav__list">{links}</ul></nav>
    <div class="P-header__actions">
      <nav class="P-lang" aria-label="Language"><ul class="P-lang__list">{lang_html}</ul></nav>
      <a class="P-btn P-btn--primary P-btn--sm P-header__cta" href="#navigation">{esc(cta1)}</a>
      <button type="button" class="P-btn P-btn--ghost P-btn--icon P-header__menu-btn" aria-label="Open menu">[[i:menu]]</button>
    </div>
  </div>
</header>'''
        mlinks = ''.join(f'<li><a class="P-menu__link" href="#navigation"{" aria-current=\"page\"" if i == 0 else ""}>{esc(n)}[[i:arrow-right]]</a></li>' for i, n in enumerate(nav))
        contact = self.c.get('contact') or {}
        mobile = f'''
<div class="doc-phones">
  <div class="doc-phone" aria-label="Mobile header (preview)">
    <header class="P-header"><div class="P-header__inner"><span class="P-header__logo">{self.logo(26, href="#navigation")}</span>
      <button type="button" class="P-btn P-btn--ghost P-btn--icon P-header__menu-btn" aria-label="Open menu" aria-expanded="false">[[i:menu]]</button></div></header>
    <div class="doc-phone__body"><p class="P-eyebrow">{esc(self.b.brand.get("descriptor") or L.get("offerings", ""))}</p><p class="doc-phone__title">{esc(self.b.brand.get("tagline", ""))}</p>
    <a class="P-btn P-btn--primary P-btn--block" href="#navigation">{esc(cta1)}</a></div>
  </div>
  <div class="doc-phone" aria-label="Mobile menu open (preview)">
    <div class="P-menu P-menu--static">
      <div class="P-menu__panel">
        <div class="P-menu__top">{self.logo(26, href="#navigation")}<button type="button" class="P-btn P-btn--ghost P-btn--icon" aria-label="Close menu">[[i:close]]</button></div>
        <ul class="P-menu__list">{mlinks}</ul>
        <div class="P-menu__footer"><a class="P-btn P-btn--primary P-btn--block" href="#navigation">{esc(cta1)}</a>
          <nav class="P-lang" aria-label="Language (menu)"><ul class="P-lang__list">{lang_html}</ul></nav></div>
      </div>
    </div>
  </div>
</div>'''
        units = self.unit_list[:4]
        tabs_kind = 'P-tabs--pills' if self.R['corner'] in ('round',) else ''
        tl = ''.join(f'<button type="button" role="tab" class="P-tabs__tab" id="tab-{i}" aria-controls="panel-{i}" aria-selected="{"true" if i == 0 else "false"}">{esc(u.get("name"))}'
                     f'<span class="P-tabs__count">{len([o for o in self.offerings if o.get("unit") == u.get("key")]) or ""}</span></button>' for i, u in enumerate(units))
        panels = ''
        for i, u in enumerate(units):
            items = [o for o in self.offerings if o.get('unit') == u.get('key')]
            lis = ''.join(f'<li>{esc(o.get("name"))} — <span class="doc-muted">{esc(o.get("summary", ""))}</span></li>' for o in items) or f'<li>{esc(u.get("summary", ""))}</li>'
            panels += f'<div class="P-tabs__panel" id="panel-{i}"{" hidden" if i else ""}><p class="doc-muted">{esc(u.get("summary", ""))}</p><ul class="P-list">{lis}</ul></div>'
        tabs = f'''
<div class="P-tabs {tabs_kind}" data-P-tabs>
  <div class="P-tabs__list" role="tablist" aria-label="{esc(L.get("units", "Sections"))}">{tl}</div>
  {panels}
</div>'''
        boxed_alt = 'P-tabs--boxed' if self.R['corner'] != 'round' else 'P-tabs--boxed'
        seg = f'''
<div class="P-tabs {boxed_alt}" data-P-tabs>
  <div class="P-tabs__list" role="tablist" aria-label="View"><button type="button" role="tab" class="P-tabs__tab" aria-controls="v-a" aria-selected="true">Grid</button><button type="button" role="tab" class="P-tabs__tab" aria-controls="v-b" aria-selected="false">List</button><button type="button" role="tab" class="P-tabs__tab" aria-controls="v-c" aria-selected="false">Map</button></div>
  <div class="P-tabs__panel" id="v-a"><p class="doc-muted">Grid view.</p></div><div class="P-tabs__panel" id="v-b" hidden><p class="doc-muted">List view.</p></div><div class="P-tabs__panel" id="v-c" hidden><p class="doc-muted">Map view.</p></div>
</div>'''
        o0 = self.offerings[0]['name'] if self.offerings else L.get('offerings', 'Page')
        crumbs = f'''
<nav class="P-breadcrumbs" aria-label="Breadcrumb"><ol>
  <li><a href="#navigation">Home</a></li>
  <li><a href="#navigation">{esc(L.get("offerings", "Section"))}</a></li>
  <li><span aria-current="page">{esc(o0)}</span></li>
</ol></nav>'''
        pag = '''
<nav class="P-pagination" aria-label="Pagination"><ul>
  <li><a class="P-pagination__link P-pagination__link--step" href="#navigation" aria-disabled="true">[[i:arrow-left]]<span>Previous</span></a></li>
  <li><a class="P-pagination__link" href="#navigation" aria-current="page" aria-label="Page 1">1</a></li>
  <li><a class="P-pagination__link" href="#navigation" aria-label="Page 2">2</a></li>
  <li><a class="P-pagination__link" href="#navigation" aria-label="Page 3">3</a></li>
  <li><span class="P-pagination__gap" aria-hidden="true">…</span></li>
  <li><a class="P-pagination__link" href="#navigation" aria-label="Page 12">12</a></li>
  <li><a class="P-pagination__link P-pagination__link--step" href="#navigation"><span>Next</span>[[i:arrow-right]]</a></li>
</ul></nav>'''
        steps = ['Details', L.get('offerings', 'Choose'), 'Review', 'Done']
        stepper = '<ol class="P-stepper" aria-label="Progress">' + ''.join(
            f'<li class="P-stepper__item{" is-done" if i == 0 else ""}"{" aria-current=\"step\"" if i == 1 else ""}><span class="P-stepper__marker">{"[[i:check]]" if i == 0 else ""}</span><span class="P-stepper__label">{esc(s)}{"<span class=\"sr-only\"> (completed)</span>" if i == 0 else ""}</span></li>'
            for i, s in enumerate(steps)) + '</ol>'
        body = (self.ex('Header', header, 'The header collapses into the menu button on its own width (container query) — it works in any layout.', stage='doc-stage--flush', open_code=True) +
                self.ex('Mobile header & menu', mobile, self.T('The menu is a modal dialog: <code class="P-code">[data-P-menu-toggle]</code> traps focus, closes on Esc or scrim click and returns focus to the button.'), stage='doc-stage--phones') +
                self.ex('Tabs', tabs, 'Arrow keys move between tabs, Home/End jump; panels are focusable. ' + ('Round DNA → segmented pills.' if tabs_kind else 'Underline indicator in the brand line colour.')) +
                self.ex('Segmented tabs', seg) +
                self.ex('Breadcrumbs & pagination', f'<div class="P-stack">{crumbs}{pag}</div>') +
                self.ex('Stepper', stepper, 'Use <code class="P-code">aria-current="step"</code>; on small screens only the current label stays visible.'))
        return self.section('navigation', 5, 'Navigation', 'Navigation', 'Header with logo, navigation and call to action; mobile menu; tabs, breadcrumbs, pagination, stepper and footer (bottom of this page).', self.T(body))

    def s_feedback(self):
        alerts = '''
<div class="P-stack">
  <div class="P-alert P-alert--info" role="status"><span class="P-alert__icon">[[i:info]]</span><div class="P-alert__body"><p class="P-alert__title">Opening hours change next week</p><p class="P-alert__text">We open an hour later on Monday. Everything else stays the same.</p></div><button type="button" class="P-close" aria-label="Dismiss" data-P-dismiss>[[i:close]]</button></div>
  <div class="P-alert P-alert--success" role="status"><span class="P-alert__icon">[[i:check]]</span><div class="P-alert__body"><p class="P-alert__title">Booking confirmed</p><p class="P-alert__text">A confirmation is on its way to your inbox.</p></div><button type="button" class="P-close" aria-label="Dismiss" data-P-dismiss>[[i:close]]</button></div>
  <div class="P-alert P-alert--warning" role="status"><span class="P-alert__icon">[[i:warning]]</span><div class="P-alert__body"><p class="P-alert__title">Only a few places left</p><p class="P-alert__text">Reserve soon to keep your preferred time.</p><div class="P-alert__actions"><a class="P-btn P-btn--link" href="#feedback">Reserve now</a></div></div></div>
  <div class="P-alert P-alert--error" role="alert"><span class="P-alert__icon">[[i:error]]</span><div class="P-alert__body"><p class="P-alert__title">We could not send your message</p><p class="P-alert__text">Check your connection and try again.</p></div></div>
</div>'''
        banner = f'''
<div class="P-stack">
  <div class="P-banner P-banner--brand" role="region" aria-label="Announcement"><span>{esc(self.b.brand.get("tagline", ""))}</span><a href="#feedback">{esc(self.L.get("cta_secondary", "Learn more"))}</a><button type="button" class="P-close" aria-label="Dismiss announcement" data-P-dismiss>[[i:close]]</button></div>
  <div class="P-banner" role="region" aria-label="Notice"><span>We use only essential cookies.</span><a href="#feedback">Privacy notice</a></div>
</div>'''
        toasts = '''
<div class="doc-toast-demo">
  <ol class="P-toaster P-toaster--static" aria-label="Notifications (preview)">
    <li class="P-toast P-toast--success P-toast--static"><span class="P-toast__icon">[[i:check]]</span><div class="P-toast__body"><p class="P-toast__title">Saved</p><p class="P-toast__text">Your preferences were updated.</p></div><button type="button" class="P-close" aria-label="Dismiss">[[i:close]]</button></li>
    <li class="P-toast P-toast--info P-toast--static"><span class="P-toast__icon">[[i:info]]</span><div class="P-toast__body"><p class="P-toast__title">New version available</p></div><button type="button" class="P-close" aria-label="Dismiss">[[i:close]]</button></li>
    <li class="P-toast P-toast--error P-toast--static"><span class="P-toast__icon">[[i:error]]</span><div class="P-toast__body"><p class="P-toast__title">Upload failed</p><p class="P-toast__text">The file is larger than 10 MB.</p></div><button type="button" class="P-close" aria-label="Dismiss">[[i:close]]</button></li>
  </ol>
  <div class="P-btn-group">
    <button type="button" class="P-btn P-btn--secondary" data-P-toast='{"title":"Saved","text":"Your preferences were updated.","tone":"success"}'>Show success toast</button>
    <button type="button" class="P-btn P-btn--secondary" data-P-toast='{"title":"Heads up","text":"Only a few places left.","tone":"warning"}'>Show warning toast</button>
    <button type="button" class="P-btn P-btn--ghost" data-P-toast='{"title":"Upload failed","text":"The file is larger than 10 MB.","tone":"error","timeout":0}'>Show error toast</button>
  </div>
</div>'''
        body = (self.ex('Alerts', alerts, 'Text stays in the primary text colour on the soft grounds; the semantic colour carries the icon and the edge. Errors use <code class="P-code">role="alert"</code>.', open_code=True) +
                self.ex('Banners', banner, 'Page-level messages above the header.', stage='doc-stage--flush') +
                self.ex('Toasts', toasts, 'Polite live region; pause on hover/focus; errors stay until dismissed. <code class="P-code">' + self.b.G + '.ui.toast({title, text, tone})</code>.'))
        return self.section('feedback', 6, 'Feedback', 'Alerts, banners & toasts', 'Status messages at three levels: inline, page and transient.', self.T(body))

    def s_overlays(self, cta1):
        modal = f'''
<div class="doc-split doc-split--overlay">
  <div class="P-modal P-modal--static" role="presentation">
    <div class="P-modal__frame">
      <header class="P-modal__header"><div><p class="P-modal__eyebrow">{esc(self.L.get("offerings", ""))}</p><h3 class="P-modal__title">{esc(cta1)}</h3></div><button type="button" class="P-close" aria-label="Close">[[i:close]]</button></header>
      <div class="P-modal__body"><p>{esc((self.c.get("brand") or {}).get("mission", ""))}</p></div>
      <footer class="P-modal__footer"><button type="button" class="P-btn P-btn--ghost">Cancel</button><button type="button" class="P-btn P-btn--primary">Continue</button></footer>
    </div>
  </div>
  <div class="P-stack doc-center">
    <button type="button" class="P-btn P-btn--primary" data-P-modal-open="demo-modal">Open modal</button>
    <button type="button" class="P-btn P-btn--secondary" data-P-modal-open="demo-drawer">Open drawer</button>
  </div>
</div>'''
        tips = '''
<div class="doc-split">
  <div class="P-btn-group doc-center">
    <button type="button" class="P-btn P-btn--secondary P-btn--icon" aria-label="Share" data-P-tooltip="tip-share">[[i:external]]</button><span class="P-tooltip" id="tip-share" hidden>Share this page</span>
    <span>Prices include <button type="button" class="P-term" data-P-tooltip="tip-vat">VAT</button></span><span class="P-tooltip" id="tip-vat" hidden>Value-added tax, charged at the local rate.</span>
    <span class="P-popover-anchor"><button type="button" class="P-btn P-btn--ghost" data-P-popover="pop-1">[[i:info]] Details</button>
      <div class="P-popover" id="pop-1" role="dialog" aria-label="Details" hidden style="top: calc(100% + 8px); left: 0"><p class="P-popover__title">Good to know</p><p class="P-popover__text">Popovers hold short interactive content. Esc or a click outside closes them.</p><div class="P-btn-group" style="margin-top: var(--space-4)"><button type="button" class="P-btn P-btn--primary P-btn--sm">Got it</button></div></div></span>
  </div>
  <div class="P-stack doc-center">
    <span class="P-tooltip P-tooltip--static" role="tooltip">Tooltip — short, non-essential hint</span>
    <div class="P-popover P-popover--static"><p class="P-popover__title">Popover</p><p class="P-popover__text">Can hold links and buttons.</p></div>
  </div>
</div>'''
        body = (self.ex('Modal & drawer', modal, 'Native <code class="P-code">&lt;dialog&gt;</code>: focus moves inside, Tab is trapped, Esc and the backdrop close it, focus returns to the opener.', open_code=True) +
                self.ex('Tooltip & popover', tips, 'Tooltips appear on hover and focus, can be hovered, and dismiss with Esc (WCAG 1.4.13). Never put essential information only in a tooltip.'))
        return self.section('overlays', 7, 'Overlays', 'Modal, drawer, tooltip & popover', 'Layers above the page — always dismissible, always keyboard reachable.', self.T(body))

    def s_data(self):
        L = self.L
        offs = self.offerings[:6]
        has_price = any(o.get('price') for o in offs)
        rows = ''.join(f'<tr><td><b>{esc(o.get("name"))}</b></td><td>{esc(self.unit_name(o.get("unit")))}</td><td class="doc-muted">{esc(o.get("summary", ""))}</td>' +
                       (f'<td class="is-num" data-value="{esc(o.get("price", ""))}">{esc(o.get("price", "—"))}</td>' if has_price else '') + '</tr>' for o in offs)
        th_price = '<th scope="col" class="is-num"><button type="button" class="P-table__sort">Price</button></th>' if has_price else ''
        table = f'''
<div class="P-table-wrap" role="region" aria-labelledby="tbl-cap" tabindex="0">
  <table class="P-table" data-P-sort>
    <caption id="tbl-cap">{esc(L.get("offerings", "Items"))}</caption>
    <thead><tr><th scope="col" aria-sort="ascending"><button type="button" class="P-table__sort">Name</button></th><th scope="col"><button type="button" class="P-table__sort">{esc(L.get("units", "Group"))}</button></th><th scope="col">Summary</th>{th_price}</tr></thead>
    <tbody>{rows}</tbody>
  </table>
  <p class="sr-only" aria-live="polite"></p>
</div>'''
        vals = ((self.c.get('brand') or {}).get('values') or [])[:4]
        lst = '<ul class="P-list">' + ''.join(f'<li><b>{esc(v.get("name"))}</b> — {esc(v.get("text", ""))}</li>' for v in vals) + '</ul>'
        chk = '<ul class="P-list P-list--check">' + ''.join(f'<li>{esc(o.get("name"))}</li>' for o in offs[:4]) + '</ul>'
        ol = '<ol class="P-list">' + ''.join(f'<li>{esc(s)}</li>' for s in ['Tell us what you need', 'We reply with options', 'Confirm and get started']) + '</ol>'
        people = (self.c.get('people') or [])[:3]
        divided = '<ul class="P-list P-list--divided">' + ''.join(
            f'<li class="P-list__item"><span class="P-avatar P-avatar--sm" aria-hidden="true">{esc(pe.get("initials", "?"))}</span><span><span class="P-list__title">{esc(pe.get("name"))}</span><span class="P-list__text">{esc(pe.get("role", ""))}</span></span><span class="P-list__meta">0{i + 1}</span></li>'
            for i, pe in enumerate(people)) + '</ul>'
        lists = f'<div class="doc-grid doc-grid--2">{lst}{chk}{ol}{divided}</div>'
        contact = self.c.get('contact') or {}
        dl = '<dl class="P-dl">' + ''.join(f'<dt>{k}</dt><dd>{esc(v)}</dd>' for k, v in [('Email', contact.get('email')), ('Phone', contact.get('phone')), ('Address', ', '.join(x for x in [contact.get('address'), contact.get('city')] if x)), ('Web', contact.get('website'))] if v) + '</dl>'
        stats = (self.c.get('stats') or [])[:4]
        st = '<dl class="P-stats">' + ''.join(f'<div class="P-stat"><dt class="P-stat__label">{esc(s.get("label"))}</dt><dd class="P-stat__value">{esc(s.get("value"))}<small>{esc(s.get("unit", ""))}</small></dd></div>' for s in stats) + '</dl>'
        body = ''
        if offs:
            body += self.ex('Table (sortable)', table, 'Sort buttons live in the header cells and update <code class="P-code">aria-sort</code>; the wrapper scrolls horizontally on small screens and is keyboard focusable.', open_code=True)
        body += self.ex('Lists', lists, 'Markers follow the DNA motif family; ordered lists use tabular index numbers.')
        if dl.count('<dt>'):
            body += self.ex('Description list', dl)
        if stats:
            body += self.ex('Stat block', st, 'For key figures in a row — <code class="P-code">dl</code> with label + value.')
        return self.section('data', 8, 'Data display', 'Tables, lists & stats', 'Structured content — readable, sortable and responsive.', self.T(body))

    def s_disclosure(self):
        faq = (self.c.get('faq') or [])[:]
        vals = ((self.c.get('brand') or {}).get('values') or [])
        items = [(f.get('q'), f.get('a')) for f in faq] + [(f'{v.get("name")}', v.get('text', '')) for v in vals[:3]]
        acc = '<div class="P-accordion" data-P-accordion>' + ''.join(
            f'<div class="P-accordion__item"><h3 class="P-accordion__heading"><button type="button" class="P-accordion__trigger" aria-expanded="{"true" if i == 0 else "false"}" aria-controls="acc-{i}">'
            f'<span class="P-accordion__title">{esc(q)}</span><span class="P-accordion__icon">[[i:plus]]</span></button></h3>'
            f'<div class="P-accordion__panel" id="acc-{i}"{"" if i == 0 else " hidden"}><p>{esc(a)}</p></div></div>' for i, (q, a) in enumerate(items[:5])) + '</div>'
        body = self.ex('Accordion', acc, 'Buttons inside headings; ↑ ↓ Home End move between headers. Add <code class="P-code">data-P-accordion="single"</code> to keep one panel open.', open_code=True)
        return self.section('disclosure', 9, 'Content', 'Accordion', 'Progressive disclosure for questions and long details.', self.T(body))

    def s_progress(self):
        prog = '''
<div class="doc-grid doc-grid--2">
  <div class="P-progress-field"><div class="P-progress-field__head"><span id="pg-1">Profile complete</span><span class="P-progress-field__value">64%</span></div>
    <div class="P-progress" role="progressbar" aria-labelledby="pg-1" aria-valuenow="64" aria-valuemin="0" aria-valuemax="100"><span class="P-progress__bar" style="--value: 64%"></span></div></div>
  <div class="P-progress-field"><div class="P-progress-field__head"><span id="pg-2">Uploading</span><span class="P-progress-field__value">…</span></div>
    <div class="P-progress P-progress--indeterminate" role="progressbar" aria-labelledby="pg-2"><span class="P-progress__bar"></span></div></div>
  <div class="P-progress-field"><div class="P-progress-field__head"><span id="pg-3">Places taken</span><span class="P-progress-field__value">7 of 10</span></div>
    <div class="P-meter" role="meter" aria-labelledby="pg-3" aria-valuenow="7" aria-valuemin="0" aria-valuemax="10"><i class="is-on"></i><i class="is-on"></i><i class="is-on"></i><i class="is-on"></i><i class="is-on"></i><i class="is-on"></i><i class="is-on"></i><i></i><i></i><i></i></div></div>
  <div class="P-progress-field"><div class="P-progress-field__head"><span id="pg-4">Storage</span><span class="P-progress-field__value">92%</span></div>
    <div class="P-progress P-progress--thin" role="progressbar" aria-labelledby="pg-4" aria-valuenow="92" aria-valuemin="0" aria-valuemax="100"><span class="P-progress__bar" style="--value: 92%"></span></div></div>
</div>'''
        spin = '''
<div class="P-btn-group">
  <span class="P-spinner P-spinner--sm" role="status"><span class="sr-only">Loading</span></span>
  <span class="P-spinner" role="status"><span class="sr-only">Loading</span></span>
  <span class="P-spinner P-spinner--lg" role="status"><span class="sr-only">Loading</span></span>
  <button type="button" class="P-btn P-btn--primary" aria-busy="true"><span>Saving</span></button>
</div>'''
        skel = '''
<div class="doc-cards" aria-busy="true" aria-label="Loading content">
  <div class="P-card" aria-hidden="true"><div class="P-card__media" style="background:none"><div class="P-skeleton P-skeleton--media" style="height:100%"></div></div><div class="P-card__body"><div class="P-skeleton P-skeleton--title"></div><div class="P-skeleton P-skeleton--text"></div><div class="P-skeleton P-skeleton--text" style="--w:60%"></div></div></div>
  <div class="P-card" aria-hidden="true"><div class="P-card__body"><div class="doc-row"><span class="P-skeleton P-skeleton--avatar"></span><div style="flex:1"><div class="P-skeleton P-skeleton--text" style="--w:70%"></div><div class="P-skeleton P-skeleton--text" style="--w:40%"></div></div></div><div class="P-skeleton P-skeleton--text"></div><div class="P-skeleton P-skeleton--text" style="--w:80%"></div><div class="P-skeleton P-skeleton--btn"></div></div></div>
</div>'''
        body = (self.ex('Progress & meter', prog, 'Determinate bars expose <code class="P-code">aria-valuenow</code>; segmented meters show capacity.', open_code=True) +
                self.ex('Spinners', spin, 'Spinner style follows the DNA motif family; it slows down (never stops) under reduced motion.') +
                self.ex('Skeleton', skel, 'Placeholders while content loads; the container carries <code class="P-code">aria-busy</code>.'))
        return self.section('progress', 10, 'Feedback', 'Progress, spinners & skeletons', 'Show that something is happening — and how far along it is.', self.T(body))

    def s_identity(self, cta1, cta2):
        c, L = self.c, self.L
        people = (c.get('people') or [])[:4]
        av = '<div class="P-btn-group">' + ''.join(f'<span class="P-avatar{s}" role="img" aria-label="{esc(pe.get("name"))}">{esc(pe.get("initials", "?"))}</span>' for pe, s in zip(people + people, [' P-avatar--sm', '', ' P-avatar--lg P-avatar--brand', ' P-avatar--xl P-avatar--dark'])) + \
             '<span class="P-avatar P-avatar--lg" role="img" aria-label="Online">' + esc((people[0].get('initials') if people else 'AB')) + '<span class="P-avatar__status"></span></span></div>'
        grp = '<div class="P-avatar-group" role="group" aria-label="Team: ' + esc(', '.join(pe.get('name', '') for pe in people)) + '">' + ''.join(f'<span class="P-avatar{" P-avatar--brand" if i == 1 else ""}" aria-hidden="true">{esc(pe.get("initials", "?"))}</span>' for i, pe in enumerate(people)) + '<span class="P-avatar P-avatar-group__more" aria-hidden="true">+12</span></div>'
        empty = f'''
<div class="P-empty">
  <span class="P-empty__art" aria-hidden="true">{self.use_mark("", f' fill="none" stroke="currentColor" stroke-width="{self.empty_stroke()}"')}</span>
  <h3 class="P-empty__title">No {esc(L.get("posts", "items").lower())} yet</h3>
  <p class="P-empty__text">New {esc(L.get("posts", "items").lower())} will appear here. Follow us to hear first.</p>
  <div class="P-empty__actions"><button type="button" class="P-btn P-btn--primary">{esc(cta1)}</button><button type="button" class="P-btn P-btn--ghost">{esc(cta2)}</button></div>
</div>'''
        div = f'''
<div class="P-stack">
  <hr class="P-divider">
  <div class="P-divider P-divider--label" role="separator">{esc(L.get("offerings", "Section"))}</div>
  <div class="P-divider P-divider--motif" role="separator"></div>
</div>'''
        kbd = '''<p>Press <kbd class="P-kbd">Tab</kbd> to move, <kbd class="P-kbd">Esc</kbd> to close, <kbd class="P-kbd">⌘</kbd> + <kbd class="P-kbd">K</kbd> to search. Inline code: <code class="P-code">data-P-tabs</code>.</p>
<pre class="P-snippet" tabindex="0"><code>&lt;button class="P-btn P-btn--primary"&gt;…&lt;/button&gt;</code></pre>'''
        tst = (c.get('testimonials') or [{}])[0]
        quote = f'''
<div class="doc-grid doc-grid--2">
  <figure class="P-testimonial">
    <svg class="P-testimonial__mark" viewBox="0 0 40 32" aria-hidden="true"><path fill="currentColor" d="M0 32V19C0 8.5 5.6 2.2 16 0l2 4.4C12 6 9.4 9.4 9 14h7v18H0zm22 0V19C22 8.5 27.6 2.2 38 0l2 4.4C34 6 31.4 9.4 31 14h7v18H22z"/></svg>
    <blockquote class="P-testimonial__text"><p>{esc(tst.get("quote", ""))}</p></blockquote>
    <figcaption class="P-blockquote__cite"><span class="P-avatar P-avatar--sm" aria-hidden="true">{esc("".join(w[0] for w in str(tst.get("name", "S C")).split()[:2]))}</span><span><b>{esc(tst.get("name", ""))}</b>{esc(tst.get("role", ""))}</span></figcaption>
  </figure>
  <figure class="P-blockquote">
    <blockquote class="P-blockquote__text"><p>{esc((c.get("brand") or {}).get("mission", ""))}</p></blockquote>
    <figcaption class="P-blockquote__cite"><span class="P-testimonial__sign">{esc(self.b.name)}</span></figcaption>
  </figure>
</div>'''
        offs = self.offerings[:3]
        plans = ''
        for i, o in enumerate(offs):
            feat = i == 1
            price = (f'<p class="P-pricing__price">{esc(o["price"])}</p>' if o.get('price') else '')
            plans += f'''
  <article class="P-pricing__plan{" P-pricing__plan--featured" if feat else ""}">
    {"<span class=\"P-pricing__flag\">Popular</span>" if feat else ""}
    <p class="P-pricing__unit">{esc(self.unit_name(o.get("unit")))}</p>
    <h3 class="P-pricing__name">{esc(o.get("name"))}</h3>
    {price}
    <p class="P-pricing__summary">{esc(o.get("summary", ""))}</p>
    <button type="button" class="P-btn {"P-btn--primary" if feat else "P-btn--secondary"} P-btn--block">{esc(cta1)}</button>
  </article>'''
        pricing = f'<div class="P-pricing">{plans}\n</div>'
        body = (self.ex('Avatars & group', f'<div class="P-stack">{av}{grp}</div>', 'Initials on brand-soft ground; shape follows the DNA image crop.', open_code=True) +
                self.ex('Empty state', empty, 'Explain what will appear and offer the next step. The art is the brand mark in outline.') +
                self.ex('Dividers', div, 'The motif divider uses a device from the DNA motifs.') +
                self.ex('Keyboard keys & code', kbd))
        if offs:
            body += self.ex(f'Offering / pricing block — {L.get("offerings", "")}', pricing, 'Prices only when content.json has them — otherwise the block shows summary + call to action.')
        body += self.ex('Quote & testimonial', quote)
        return self.section('identity', 11, 'Content', 'Avatars, empty states, quotes & more', 'Small pieces that make pages feel like the brand.', self.T(body))

    def empty_stroke(self):
        vb = [float(x) for x in str(self.mark_vb).split()]
        return f'{max(vb[2], vb[3]) / 90:.1f}'

    def s_language(self):
        b, p = self.b, self.p
        local = b.brand.get('name_local') or ''
        langs = b.langs
        second = next((l for l in langs if l != b.lang), None)
        lang_html = ''.join(f'<li><a class="P-lang__link" href="#language" hreflang="{l}" lang="{l}"{" aria-current=\"true\"" if i == 0 else ""}>{l.upper()}</a></li>' for i, l in enumerate(langs))
        if local and second:
            demo = f'''
<div class="doc-grid doc-grid--2">
  <div class="P-stack">
    <nav class="P-lang" aria-label="Language"><ul class="P-lang__list">{lang_html}</ul></nav>
    <p class="doc-local" lang="{second}">{esc(local)}</p>
    <div class="P-tag-group"><span class="P-tag" lang="{second}">{esc(local)}</span><span class="P-badge P-badge--brand">{second.upper()}</span></div>
  </div>
  <article class="P-card P-card--offering" lang="{second}">
    <div class="P-card__body"><div class="P-card__meta"><span>{second.upper()}</span></div><h3 class="P-card__title">{esc(local)}</h3>
    <p class="P-card__text" lang="{b.lang}">{esc(b.name)}</p></div>
  </article>
</div>'''
            note = f'Every text in another language carries <code class="P-code">lang="{second}"</code>: browsers pick the right glyph forms, hyphenation and voices; set-in-caps styles relax their tracking for this script.'
        else:
            demo = f'<nav class="P-lang" aria-label="Language"><ul class="P-lang__list">{lang_html}</ul></nav>'
            note = 'Language links carry <code class="P-code">hreflang</code> and <code class="P-code">lang</code>; the current one has <code class="P-code">aria-current</code>.'
        body = self.ex('Languages', demo, note, open_code=True)
        return self.section('language', 12, 'Foundations', 'Languages', f'{esc(b.name)} works in {", ".join(l.upper() for l in langs)}.', self.T(body))

    def s_theming(self, cta1):
        p = self.p
        def mini(theme):
            return f'''
  <div class="P-scope doc-theme-card" data-theme="{theme}" data-P-theme-fixed>
    <p class="P-eyebrow">{theme.capitalize()}</p>
    <div class="P-card P-card--offering"><div class="P-card__body"><h3 class="P-card__title">{esc(self.offerings[0]["name"] if self.offerings else self.b.name)}</h3><p class="P-card__text">{esc(self.offerings[0].get("summary", "") if self.offerings else "")}</p>
      <div class="P-btn-group"><button type="button" class="P-btn P-btn--primary P-btn--sm">{esc(cta1)}</button><button type="button" class="P-btn P-btn--secondary P-btn--sm">More</button></div></div></div>
    <div class="P-tag-group"><span class="P-badge P-badge--success">OK</span><span class="P-badge P-badge--error">Error</span><span class="P-tag">Tag</span></div>
    <label class="P-switch"><input class="P-switch__input" type="checkbox" role="switch" checked> <span>Switch</span></label>
  </div>'''
        demo = f'<div class="doc-themes">{mini("light")}{mini("dark")}{mini("contrast")}\n</div>'
        snippet = f'''<html data-theme="dark"> … </html>          <!-- or light / contrast; no attribute = follow the OS -->
<section data-theme="dark" class="P-scope"> … </section>   <!-- any element can switch theme -->
<fieldset class="P-segmented" data-P-theme-switch> … radio inputs: auto / light / dark / contrast … </fieldset>'''
        body = (self.ex('Three themes', demo, 'Every colour in the kit is a <code class="P-code">--color-*</code> token; component choices that depend on contrast are computed per theme at build time (see <code class="P-code">contrast-report.json</code>).', stage='doc-stage--flush', open_code=False) +
                f'<div class="doc-example"><div class="doc-example__head"><h3 class="doc-example__title">Usage</h3></div><pre class="{p}-snippet" tabindex="0"><code>{esc(self.T(snippet))}</code></pre></div>')
        return self.section('theming', 13, 'Foundations', 'Theming', 'Light, dark and high-contrast themes from the same tokens. The switch in the header persists your choice.', self.T(body))

    def s_access(self):
        items = [
            ('Keyboard', 'Every interactive component is reachable with Tab and operable with Enter/Space; composite widgets (tabs, accordion, menus) follow the WAI-ARIA Authoring Practices key maps.'),
            ('Focus', 'A 2px focus ring in <code class="P-code">--color-focus</code> on every interactive element — never removed. Cut shapes paint on a pseudo-element so the ring is never clipped.'),
            ('Contrast', 'Text pairs come from WCAG-checked theme tokens; button states pick their text colour by measured contrast (≥4.5:1); control borders ≥3:1.'),
            ('Targets', 'Controls are at least 44×44px (small buttons extend their hit area).'),
            ('Motion', 'All transitions use the motion tokens, which drop to 0ms under <code class="P-code">prefers-reduced-motion</code>; spinners slow down instead of stopping.'),
            ('Colour', 'Status is never colour alone — words and icons carry it. Forced-colours mode keeps borders and selection visible.'),
        ]
        dl = '<dl class="doc-a11y">' + ''.join(f'<div><dt>{k}</dt><dd>{v}</dd></div>' for k, v in items) + '</dl>'
        return self.section('accessibility', 14, 'Foundations', 'Accessibility', 'Built in, not bolted on.', self.T(dl))

    # ------------------------------------------------------------------ footer & dialogs
    def footer(self, nav, cta1):
        b, c, L, p = self.b, self.c, self.L, self.p
        contact = c.get('contact') or {}
        col1 = ''.join(f'<li><a href="#top">{esc(n)}</a></li>' for n in nav)
        units = ''.join(f'<li><a href="#top">{esc(u.get("name"))}</a></li>' for u in self.unit_list[:5])
        cinfo = ''.join(f'<li><a href="#top">{esc(v)}</a></li>' for v in [contact.get('email'), contact.get('phone')] if v)
        social = ''.join(f'<li><a href="#top">{esc(k.capitalize())}</a></li>' for k in (contact.get('social') or {}).keys())
        year = datetime.date.today().year
        sample = ' · Sample content' if self.sample else ''
        return f'''
<footer class="{p}-footer" data-theme="dark">
  <div class="{p}-footer__inner">
    <div class="{p}-footer__top">
      <div class="{p}-footer__brand">{self.logo(40, href="#top")}<p class="{p}-footer__tagline">{esc(b.brand.get("tagline", ""))}</p>
        <div><a class="{p}-btn {p}-btn--primary" href="#top">{esc(cta1)}</a></div></div>
      <nav aria-label="Footer — site"><p class="{p}-footer__title">{esc(b.name)}</p><ul class="{p}-footer__list">{col1}</ul></nav>
      <nav aria-label="Footer — {esc(L.get('units', 'sections'))}"><p class="{p}-footer__title">{esc(L.get("units", "Sections"))}</p><ul class="{p}-footer__list">{units}</ul></nav>
      <div><p class="{p}-footer__title">Contact</p><ul class="{p}-footer__list">{cinfo}{social}</ul></div>
    </div>
    <div class="{p}-footer__bottom"><span>© {year} {esc(b.brand.get("legal_name") or b.name)}{sample}</span><span>UI kit · generated by brand-system-forge</span></div>
  </div>
</footer>'''

    def dialogs(self, cta1):
        L, c = self.L, self.c
        opts = ''.join(f'<option>{esc(o.get("name"))}</option>' for o in self.offerings[:6])
        modal = f'''
<dialog class="P-modal" id="demo-modal" aria-labelledby="demo-modal-title">
  <div class="P-modal__frame">
    <header class="P-modal__header"><div><p class="P-modal__eyebrow">{esc(L.get("offerings", ""))}</p><h2 class="P-modal__title" id="demo-modal-title">{esc(cta1)}</h2></div><button type="button" class="P-close" aria-label="Close" data-P-modal-close>[[i:close]]</button></header>
    <div class="P-modal__body">
      <p>{esc((c.get("brand") or {}).get("mission", ""))}</p>
      <div class="P-field"><label class="P-field__label" for="dm-email">Email</label><input class="P-input" id="dm-email" type="email" autocomplete="email"></div>
    </div>
    <footer class="P-modal__footer"><button type="button" class="P-btn P-btn--ghost" data-P-modal-close>Cancel</button><button type="button" class="P-btn P-btn--primary" data-P-modal-close value="ok">Continue</button></footer>
  </div>
</dialog>
<dialog class="P-modal P-drawer" id="demo-drawer" aria-labelledby="demo-drawer-title">
  <div class="P-modal__frame">
    <header class="P-modal__header"><h2 class="P-modal__title" id="demo-drawer-title">Filters</h2><button type="button" class="P-close" aria-label="Close" data-P-modal-close>[[i:close]]</button></header>
    <div class="P-modal__body">
      <div class="P-field"><label class="P-field__label" for="dd-sel">{esc(L.get("offerings", "Topic"))}</label><span class="P-select"><select id="dd-sel">{opts}</select></span></div>
      <fieldset class="P-fieldset"><legend class="P-fieldset__legend">{esc(L.get("units", "Group"))}</legend><div class="P-choices">{"".join(f'<label class="P-check"><input class="P-check__input" type="checkbox"> <span>{esc(u.get("name"))}</span></label>' for u in self.unit_list[:4])}</div></fieldset>
    </div>
    <footer class="P-modal__footer"><button type="button" class="P-btn P-btn--ghost" data-P-modal-close>Reset</button><button type="button" class="P-btn P-btn--primary" data-P-modal-close>Show results</button></footer>
  </div>
</dialog>'''
        return self.live(modal)
