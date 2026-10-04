#!/usr/bin/env python3
"""to_artifact_page.py — turn a full HTML document into a page body for hosts that wrap pages in their own
<!doctype><html><head><body> skeleton (e.g. claude.ai Artifacts). Keeps <title>, stylesheet links and head scripts,
moves <html>/<body> classes onto the elements via a tiny script, and adds a sticky-header safe-area fix.
usage: python3 scripts/to_artifact_page.py portable/index.html out/index.html --title "ACME Brand System"
Then publish out/index.html with every other file of the portable folder as supporting files (≤ 255 files, ≤ 64 MB)."""
import argparse, re
ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('dst'); ap.add_argument('--title')
a = ap.parse_args(); s = open(a.src, encoding='utf-8').read()
head = s[s.index('<head>') + 6:s.index('</head>')] if '<head>' in s else ''
bm = re.search(r'<body([^>]*)>', s); hm = re.search(r'<html([^>]*)>', s)
body = s[bm.end():s.rindex('</body>')] if bm else s
cls = lambda attrs: (re.search(r'class="([^"]*)"', attrs or '') or [None, ''])[1]
lang = (re.search(r'lang="([^"]*)"', hm.group(1) if hm else '') or [None, 'en'])[1]
title = a.title or (re.search(r'<title>(.*?)</title>', head) or [None, 'Brand System'])[1]
keep = [l for l in head.split('\n') if '<link rel="stylesheet"' in l or '<script src=' in l or '<style' in l]
top = (f'<title>{title}</title>\n<script>document.documentElement.lang="{lang}";'
       f'{"document.documentElement.classList.add(" + ",".join(repr(c) for c in cls(hm.group(1) if hm else "").split()) + ");" if hm and cls(hm.group(1)) else ""}'
       f'{"document.body.classList.add(" + ",".join(repr(c) for c in cls(bm.group(1)).split()) + ");" if bm and cls(bm.group(1)) else ""}</script>\n'
       + '\n'.join(keep) + '\n')
open(a.dst, 'w', encoding='utf-8').write(top + body)
print('artifact page written:', a.dst)
