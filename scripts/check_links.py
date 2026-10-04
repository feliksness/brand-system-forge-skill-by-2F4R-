#!/usr/bin/env python3
"""check_links.py — every relative src/href/url() in HTML/CSS/SVG/MD must resolve to a file.
usage: python3 scripts/check_links.py <repo>   (exit code 1 if broken references are found)
Code samples inside <pre>/<code> and JS string concatenations may show up as false positives: verify by eye."""
import os, re, sys, urllib.parse
root = sys.argv[1]
H = re.compile(r'''(?:src|href|poster|xlink:href)\s*=\s*["']([^"'#?]+)''', re.I); U = re.compile(r'''url\(\s*["']?([^"')#?]+)''', re.I); M = re.compile(r'\]\(([^)#?\s]+)')
bad = {}; n = 0
for d, dirs, fs in os.walk(root):
    dirs[:] = [x for x in dirs if x not in ('node_modules', '.git', 'forge', '_work')]
    for f in fs:
        ext = os.path.splitext(f)[1].lower()
        if ext not in ('.html', '.css', '.md', '.svg'): continue
        p = os.path.join(d, f); t = open(p, encoding='utf-8', errors='ignore').read()
        t = re.sub(r'<pre[\s\S]*?</pre>', '', t) if ext == '.html' else t
        refs = (H.findall(t) + U.findall(t)) if ext in ('.html', '.svg') else U.findall(t) if ext == '.css' else M.findall(t)
        for r in refs:
            r = r.strip()
            if not r or r.startswith(('http:', 'https:', 'data:', 'mailto:', 'tel:', 'javascript:', '//', '#', 'blob:', '/', '%23')) or any(c in r for c in "<>{}|\\+$'\"("): continue
            known = ('.html', '.htm', '.css', '.js', '.json', '.svg', '.png', '.jpg', '.jpeg', '.webp', '.gif', '.pdf', '.woff2', '.woff', '.ttf', '.otf', '.mp4', '.webm', '.ico', '.webmanifest', '.md', '.txt', '.xml', '.pptx', '.docx', '.zip')
            if '/' not in r and not r.lower().endswith(known): continue   # JS identifiers caught by the regex (e.g. a.href)
            n += 1
            if not os.path.exists(os.path.normpath(os.path.join(d, urllib.parse.unquote(r)))): bad.setdefault(os.path.relpath(p, root), set()).add(r)
print(f'{n} references checked · {len(bad)} files with broken references')
for k, v in sorted(bad.items()): print(f'  {k} → {sorted(v)[:6]}')
sys.exit(1 if bad else 0)
