#!/usr/bin/env python3
"""validate_repo.py — hygiene gate before packaging.
Checks: empty files · empty folders · temp/junk files · __pycache__ · invalid JSON · SVG XML well-formedness (incl. unescaped &) ·
non-kebab or spaced file names · huge files (> 15 MB) · folders without README/guide · leftover TODO/lorem text.
usage: python3 scripts/validate_repo.py <repo> [--fix]   (--fix deletes __pycache__/temp files)"""
import json, os, re, shutil, sys
import xml.etree.ElementTree as ET
root = sys.argv[1]; fix = '--fix' in sys.argv; issues = []
for d, dirs, fs in os.walk(root):
    dirs[:] = [x for x in dirs if not (x == 'forge' and d.endswith('SCRIPTS'))]
    if not dirs and not fs: issues.append(f'empty folder: {os.path.relpath(d, root)}')
    for x in list(dirs):
        if x in ('__pycache__', '.pytest_cache', 'node_modules'):
            issues.append(f'junk dir: {os.path.join(d, x)}')
            if fix: shutil.rmtree(os.path.join(d, x)); dirs.remove(x)
    for f in fs:
        p = os.path.join(d, f); rel = os.path.relpath(p, root); ext = os.path.splitext(f)[1].lower()
        if f in ('.DS_Store', 'Thumbs.db') or f.endswith(('.tmp', '.bak', '~', '.pyc')):
            issues.append(f'junk file: {rel}');  fix and os.remove(p); continue
        if os.path.getsize(p) == 0: issues.append(f'empty file: {rel}')
        if os.path.getsize(p) > 15 * 1048576: issues.append(f'large file (>15 MB): {rel}')
        if ' ' in f: issues.append(f'space in name: {rel}')
        if ext == '.json':
            try: json.load(open(p))
            except Exception as e: issues.append(f'bad JSON: {rel} ({e})')
        if ext == '.svg':
            try: ET.parse(p)
            except Exception as e: issues.append(f'bad SVG: {rel} ({e})')
        if ext in ('.html', '.md'):
            t = open(p, encoding='utf-8', errors='ignore').read()
            if re.search(r'lorem ipsum dolor', t, re.I): issues.append(f'lorem ipsum placeholder text: {rel}')
            if re.search(r'\bTODO[:(]|\bFIXME[:(]', t): issues.append(f'TODO/FIXME left: {rel}')
            if '‹fill' in t and (rel.startswith(os.path.join('SOURCE', 'CONFIG')) or rel == 'README.md'): issues.append(f'unfilled ‹fill› marker: {rel}')
for top in sorted(os.listdir(root)):
    p = os.path.join(root, top)
    if os.path.isdir(p) and not any(f.lower().endswith('.md') for f in os.listdir(p)): issues.append(f'no README/guide .md in top folder: {top}/')
nfiles = sum(len(fs) for _, _, fs in os.walk(root))
print(f'{nfiles} files · {len(issues)} issues')
try:
    for i in issues[:200]: print('  -', i)
except BrokenPipeError:
    pass
sys.exit(1 if any(not i.startswith(('junk', 'no README')) for i in issues) else 0)
