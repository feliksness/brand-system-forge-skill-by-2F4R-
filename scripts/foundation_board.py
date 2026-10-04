#!/usr/bin/env python3
"""
foundation_board.py — one HTML/PNG board that shows every foundation together, for visual QA and for the
client conversation: original artwork vs vector, the rebuilt original lockup, symbol variants, compact mark,
lettering, design DNA (corner, crop, stroke, motion, patterns), palette with contrast, ramps, themes, type.
Writes BRAND-BOOK/foundation-board.html and .png (needs Playwright for the PNG).
usage: python3 scripts/foundation_board.py --config brand.config.json --repo ../ACME-BRAND
"""
import argparse, glob, json, os, subprocess, html
HERE = os.path.dirname(os.path.abspath(__file__))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--config', required=True); ap.add_argument('--repo', required=True)
    a = ap.parse_args(); C = json.load(open(a.config)); b = C['brand']; p = b.get('prefix', 'bx'); G = b.get('global', 'BX')
    R = lambda *x: os.path.join(a.repo, *x); E = html.escape
    colors = json.load(open(R('COLORS', 'colors.json')))
    pal = {c['key']: c['hex'] for c in colors['palette']}
    roles = C['roles']; prim, found, paper = pal[roles['primary']], pal[roles['foundation']], pal[roles['paper']]
    art = (glob.glob(R('LOGO', 'PNG', '*original-artwork.*')) + glob.glob(R('LOGO', 'SVG', '*original-artwork.*')))[0]
    art_rel = os.path.relpath(art, R('BRAND-BOOK'))
    dna = json.load(open(R('SOURCE', 'CONFIG', 'design-dna.json'))) if os.path.exists(R('SOURCE', 'CONFIG', 'design-dna.json')) else {}
    parts = json.load(open(R('SOURCE', 'JSON', 'logo-parts.json'))) if os.path.exists(R('SOURCE', 'JSON', 'logo-parts.json')) else {'logo_type': 'symbol'}
    T = parts.get('logo_type', 'symbol')
    stacks = C['fonts']['stacks']; samples = C['fonts'].get('samples', {})
    fams = {f['role']: f['family'] for f in C['fonts'].get('families', [])}
    chips = ''.join(
        f'<div class="chip"><i style="background:{c["hex"]}"></i><b>{E(c["name"])}</b><span>{c["hex"]}</span>'
        f'<em>{E(c.get("group", ""))} · {E(c.get("origin", ""))}<br>on paper {c["contrast"]["on_paper"]}:1 · white text {c["contrast"]["white_text"]}</em></div>'
        for c in colors['palette'])
    ramps = ''.join(f'<div class="ramp"><span>{rn}</span>' + ''.join(f'<i title="{s} {v}" style="background:{v}"></i>' for s, v in r.items()) + '</div>'
                    for rn, r in colors['ramps'].items())
    def theme_card(tn):
        return (f'<div class="theme" data-theme="{tn}"><p class="{p}-eyebrow">{tn} theme</p><h3 class="{p}-h3">Headline in the primary text colour</h3>'
                f'<p class="sec">Secondary text for supporting copy, captions and metadata.</p><p><a href="#">A text link</a> · <span class="{p}-brand">Brand-coloured text</span></p>'
                f'<p class="btns"><button class="{p}-btnx">Primary action</button> <button class="{p}-btnx focus">Focused</button></p>'
                f'<p class="sem"><span style="color:var(--color-success)">● success</span> <span style="color:var(--color-warning)">● warning</span> '
                f'<span style="color:var(--color-error)">● error</span> <span style="color:var(--color-info)">● info</span></p></div>')
    roles_html = ''.join(
        f'<div class="trow"><span class="tlab">{r}<br><b>{E(fams.get(r, stacks[r].split(",")[0].strip(chr(39))))}</b></span><span class="tsam" style="font-family:var(--font-{r}, {stacks[r]})">{E(samples.get(r, "Brand system — Ag 0123456789"))}</span></div>'
        for r in stacks if not r.startswith('local') or True)
    typescale = ''.join(f'<div class="ts"><span class="tlab">{k}</span><span class="{p}-{k}">{E(t)}</span></div>' for k, t in
                        (('display-l', samples.get('display', b['name'])), ('h1', 'Headline one'), ('h2', 'Section headline'), ('h3', 'Card title'),
                         ('body-l', 'Lead paragraph that introduces a section with warmth and clarity.'), ('body', 'Body copy for reading. ' * 3),
                         ('eyebrow', 'Eyebrow label'), ('data-xl', '1,240')))
    # lettering
    let = ''
    if os.path.exists(R('SOURCE', 'SVG', 'lettering-original.svg')):
        let += f'<div class="lk" style="background:#fff"><img class="wm" src="../SOURCE/SVG/lettering-original.svg" alt=""><em>LETTERING · TRACED FROM THE ARTWORK</em></div>'
    if os.path.exists(R('SOURCE', 'SVG', 'wordmark-stacked.svg')):
        let += f'<div class="lk" style="background:{paper}"><img class="wm" src="../SOURCE/SVG/wordmark-stacked.svg" alt=""><em>WORDMARK · TYPESET (STACKED)</em></div>'
        let += f'<div class="lk" style="background:{paper}"><img class="wm" src="../SOURCE/SVG/wordmark-line.svg" alt=""><em>WORDMARK · ONE LINE</em></div>'
    for d in C.get('wordmark', {}).get('descriptors', []):
        if os.path.exists(R('SOURCE', 'SVG', d['name'] + '.svg')):
            let += f'<div class="lk" style="background:{paper}"><img class="desc" src="../SOURCE/SVG/{d["name"]}.svg" alt=""><em>{E(d["name"].upper())}</em></div>'
    let_sec = f'<section><h2>Lettering</h2><div class="lks">{let}</div></section>' if let else ''
    # DNA
    dsec = ''
    if dna:
        rat = ''.join(f'<li>{E(r)}</li>' for r in dna.get('rationale', []))
        st = dna.get('stroke', {})
        dsec = (f'<section><h2>Design DNA — derived from the logo ({E(dna.get("geometry", ""))} · {E(dna.get("complexity", ""))} · {E(T)})</h2><div class="dna">'
                f'<div class="dcell"><div class="{p}-shape sw" style="background:{prim}"></div><em>CORNER · {E(dna["corner"]["style"])}</em></div>'
                f'<div class="dcell"><div class="{p}-crop sw img"></div><em>IMAGE CROP · {E(dna["imagery"]["crop"])}</em></div>'
                f'<div class="dcell"><svg viewBox="0 0 24 24" class="sw ic"><path class="{p}-stroke" d="M4 18 L10 8 L14 14 L20 5"/><circle class="{p}-stroke" cx="17" cy="17" r="3"/></svg><em>STROKE · {st.get("icon_px_at_24")}px · {E(st.get("cap", ""))} / {E(st.get("join", ""))}</em></div>'
                f'<div class="dcell txt"><b>Patterns</b>{E(", ".join(dna.get("patterns", [])))}<b>Motifs</b>{E(", ".join(dna.get("motifs", [])[:6]))}'
                f'<b>Motion</b>{E(dna["motion"]["character"])} — {E(dna["motion"]["signature"])}<b>Composition</b>{E(dna.get("composition", ""))}</div>'
                f'</div><ul class="rat">{rat}</ul></section>')
    lockup_cell = '<img src="../LOGO/SVG/logo-original.svg" alt="">'
    page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{E(b["name"])} — Foundation board</title>
<link rel="stylesheet" href="../SOURCE/CSS/{p}-core.css">
<style>
body{{margin:0;background:var(--color-background);color:var(--color-text-primary);padding:56px 64px;width:1600px;box-sizing:border-box}}
h2{{font:600 12px/1 var(--font-mono);letter-spacing:.14em;text-transform:uppercase;margin:0 0 18px;color:var(--color-text-secondary)}}
section{{border-top:1px solid var(--color-border);padding:28px 0 36px}} .meta{{font:500 12px var(--font-mono);letter-spacing:.08em;color:var(--color-text-secondary);margin:0 0 6px}}
.row{{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:14px}} .cell{{aspect-ratio:1;display:flex;align-items:center;justify-content:center;padding:18px;position:relative;border:1px solid var(--color-border-subtle)}}
.cell span.m, .cell img{{width:80%;height:80%;object-fit:contain;display:block}} .cell em, .lk em, .dcell em{{position:absolute;left:10px;bottom:8px;font:500 10px var(--font-mono);letter-spacing:.06em;opacity:.75;font-style:normal}}
.wide{{grid-column:span 2;aspect-ratio:2/1}}
.chips{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}} .chip{{display:grid;gap:4px;font-size:13px}} .chip i{{display:block;height:84px;box-shadow:inset 0 0 0 1px var(--color-border)}} .chip span{{font:500 12px var(--font-mono)}} .chip em{{font-style:normal;font-size:11px;color:var(--color-text-secondary)}}
.ramp{{display:grid;grid-template-columns:120px repeat(12,1fr);gap:4px;align-items:center;margin:6px 0;font:500 12px var(--font-mono)}} .ramp i{{height:34px;display:block}}
.themes{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}} .theme{{background:var(--color-background);color:var(--color-text-primary);padding:24px;border:1px solid var(--color-border)}}
.theme h3{{margin:8px 0}} .theme .sec{{color:var(--color-text-secondary)}} .theme a{{color:var(--color-text-link)}} .btns{{margin:14px 0}}
.{p}-btnx{{font:var(--type-button-weight) var(--type-button-size)/1 var(--font-sans);background:var(--color-brand-primary);color:var(--color-on-brand);border:0;padding:12px 20px;border-radius:var(--radius-button)}} .{p}-btnx.focus{{box-shadow:var(--focus-ring)}}
.trow{{display:grid;grid-template-columns:200px 1fr;align-items:baseline;border-bottom:1px solid var(--color-border-subtle);padding:12px 0}} .tlab{{font:500 12px var(--font-mono);color:var(--color-text-secondary)}} .tlab b{{font-family:var(--font-sans);color:var(--color-text-primary)}} .tsam{{font-size:40px;line-height:1.1}}
.ts{{display:grid;grid-template-columns:200px 1fr;align-items:baseline;padding:10px 0;border-bottom:1px solid var(--color-border-subtle)}} .ts .{p}-body{{max-width:70ch}}
.lks{{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}} .lk{{position:relative;display:flex;align-items:center;justify-content:center;padding:56px 40px;min-height:200px;border:1px solid var(--color-border-subtle)}} .lk .wm{{max-height:110px;max-width:90%}} .lk .desc{{height:18px}}
.dna{{display:grid;grid-template-columns:1fr 1fr 1fr 1.6fr;gap:14px}} .dcell{{position:relative;min-height:240px;display:flex;align-items:center;justify-content:center;border:1px solid var(--color-border-subtle);padding:24px}}
.sw{{width:150px;height:150px}} .img{{background:linear-gradient(135deg,{prim},{found})}} .ic{{color:var(--color-text-primary);width:120px;height:120px}}
.dcell.txt{{display:grid;align-content:start;justify-content:stretch;gap:4px;font-size:14px}} .dcell.txt b{{font:600 11px var(--font-mono);letter-spacing:.1em;text-transform:uppercase;color:var(--color-text-secondary);margin-top:10px}}
.rat{{columns:2;font-size:13px;color:var(--color-text-secondary);margin:18px 0 0;padding-left:18px}}
</style></head><body>
<p class="meta">{E(b.get("legal_name", b["name"]))} · {E(b.get("profile", ""))} · FOUNDATION BOARD · brand-system-forge</p>
<h1 class="{p}-display-l" style="margin:0 0 12px">{E(samples.get("display", b["name"]))}</h1><p class="{p}-lead">{E(b.get("tagline", ""))}</p>
<section><h2>Logo — original artwork, vector rebuild and variants ({E(T)})</h2><div class="row">
<div class="cell wide" style="background:#fff"><img src="{art_rel}" alt=""><em>ORIGINAL ARTWORK (PRIMARY, NEVER ALTERED)</em></div>
<div class="cell wide" style="background:#fff">{lockup_cell}<em>VECTOR REBUILD OF THE ORIGINAL</em></div>
<div class="cell" style="background:#fff"><span class="m" data-v="color" data-l="master"></span><em>MARK · MASTER</em></div>
<div class="cell" style="background:#fff"><img src="../LOGO/SVG/compact.svg" alt=""><em>COMPACT MARK</em></div>
</div><div class="row" style="margin-top:14px">
<div class="cell" style="background:#fff"><span class="m" data-v="color" data-l="simplified"></span><em>MARK · SIMPLIFIED</em></div>
<div class="cell" style="background:#fff"><span class="m" data-v="outline" data-l="master" data-c="{found}"></span><em>CONSTRUCTION</em></div>
<div class="cell" style="background:{found};color:#fff"><span class="m" data-v="on-dark" data-l="master"></span><em>ON DARK</em></div>
<div class="cell" style="background:{prim};color:#fff"><span class="m" data-v="mono" data-l="simplified" data-c="#FFFFFF"></span><em>ONE COLOUR ON PRIMARY</em></div>
<div class="cell" style="background:{paper}"><span class="m" data-v="mono" data-l="simplified" data-c="{found}"></span><em>ONE COLOUR</em></div>
<div class="cell" style="background:{paper}"><span class="m" data-v="brand" data-l="master"></span><em>BRAND RAMP</em></div>
</div><div class="row" style="margin-top:14px">
<div class="cell wide" style="background:{found}"><img src="../LOGO/SVG/logo-original-on-dark.svg" alt=""><em style="color:#fff">ORIGINAL ON DARK</em></div>
<div class="cell" style="background:{paper}"><span class="m" data-v="tonal-dark" data-l="master"></span><em>TONAL</em></div>
<div class="cell" style="background:{paper}"><span class="m" data-v="silhouette" data-l="master" data-c="{found}"></span><em>SILHOUETTE</em></div>
<div class="cell" style="background:{paper}"><img src="../LOGO/SVG/compact.svg" alt="" style="width:32px;height:32px"><em>32 PX</em></div>
<div class="cell" style="background:{found}"><img src="../LOGO/SVG/compact-white.svg" alt="" style="width:24px;height:24px"><em style="color:#fff">24 PX ON DARK</em></div>
</div></section>
{let_sec}
{dsec}
<section><h2>Palette — from the logo, named by role</h2><div class="chips">{chips}</div></section>
<section><h2>Ramps</h2>{ramps}</section>
<section><h2>Themes — light · dark · contrast (all text pairs WCAG-checked)</h2><div class="themes">{theme_card("light")}{theme_card("dark")}{theme_card("contrast")}</div></section>
<section><h2>Type roles</h2>{roles_html}</section>
<section><h2>Type scale (tokens)</h2>{typescale}</section>
<script src="../SOURCE/JS/mark-data.js"></script><script src="../SOURCE/JS/{p}-mark.js"></script>
<script>document.querySelectorAll('.m').forEach(function(e){{e.innerHTML={G}.markSVG({{level:e.dataset.l||'master',variant:e.dataset.v||'color',color:e.dataset.c,decorative:true}});var s=e.firstChild;s.style.width='100%';s.style.height='100%';}});</script>
</body></html>'''
    out = R('BRAND-BOOK', 'foundation-board.html'); os.makedirs(R('BRAND-BOOK'), exist_ok=True); open(out, 'w').write(page)
    try:
        subprocess.check_call(['node', os.path.join(HERE, 'shot.js'), out, R('BRAND-BOOK', 'foundation-board.png'), '1600', '1200', '1', '0', '1'])
        print('board →', R('BRAND-BOOK', 'foundation-board.png'))
    except Exception as e:
        print('board HTML written; PNG render failed:', e)

if __name__ == '__main__':
    main()
