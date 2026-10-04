#!/usr/bin/env python3
"""
split_zip.py — deliver a large repository as several small, standalone zips that merge back into one folder.

Why: chat/file uploads fail above ~25–50 MB (seen as HTTP 502). Parts of ≤ 18 MB always went through.
Every part is a normal zip with full paths, so extracting ALL parts into the same folder rebuilds the repo.
Part 1 carries _PARTS/HOW-TO-MERGE.txt (macOS/Linux + Windows commands) and MANIFEST.txt (file count + SHA-256).

usage: python3 scripts/split_zip.py <repo-dir> <out-dir> [--prefix acme-] [--mb 18] [--single-too]
"""
import argparse, hashlib, os, zipfile
ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('out'); ap.add_argument('--prefix', default='part-')
ap.add_argument('--mb', type=float, default=18); ap.add_argument('--single-too', action='store_true')
a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
base = os.path.dirname(os.path.abspath(a.src)); name = os.path.basename(os.path.abspath(a.src)); budget = a.mb * 1048576
SKIP = {'__pycache__', 'node_modules', '.git'}; STORE = {'.png', '.jpg', '.jpeg', '.gif', '.mp4', '.webm', '.woff2', '.zip', '.pptx', '.docx', '.pdf'}
files = []
for d, dirs, fs in os.walk(a.src):
    dirs[:] = sorted(x for x in dirs if x not in SKIP)
    for f in sorted(fs):
        if f.endswith('.pyc') or f in ('.DS_Store',): continue
        p = os.path.join(d, f); files.append((p, os.path.getsize(p)))
parts, cur, size = [], [], 0
for p, s in files:
    est = s if os.path.splitext(p)[1].lower() in STORE else s * 0.35
    if cur and size + est > budget: parts.append(cur); cur, size = [], 0
    cur.append(p); size += est
if cur: parts.append(cur)
n = len(parts); total = len(files)
man = '\n'.join(f'{hashlib.sha256(open(p, "rb").read()).hexdigest()}  {os.path.relpath(p, base)}' for p, _ in files)
how = f"""{name} — delivered in {n} parts ({a.prefix}1.zip … {a.prefix}{n}.zip). Expected files after merge: {total}

1) Put ALL {n} zips in one new, empty folder.
2) Open a terminal in that folder and run:

macOS / Linux:
  mkdir -p merged && for f in {a.prefix}*.zip; do unzip -o -q "$f" -d merged; done
  rm -rf merged/{name}/_PARTS
  echo "Files: $(find merged/{name} -type f | wc -l)   (expected {total})"

Windows PowerShell:
  New-Item -ItemType Directory -Force merged | Out-Null
  Get-ChildItem {a.prefix}*.zip | ForEach-Object {{ Expand-Archive $_.FullName -DestinationPath .\\merged -Force }}
  Remove-Item .\\merged\\{name}\\_PARTS -Recurse -Force
  "Files: " + (Get-ChildItem .\\merged\\{name} -Recurse -File).Count + "   (expected {total})"

If Safari auto-extracted the downloads into folders: rsync -a ~/Downloads/{a.prefix}*/{name}/ merged/{name}/
Optional single zip:  cd merged && zip -r -q ../{name}.zip {name}
Optional git repo:    cd merged/{name} && git init && git add . && git commit -m "{name} v1"
Verify integrity:     cd merged && shasum -a 256 -c {name}/_PARTS/MANIFEST.txt   (before deleting _PARTS)
"""
for i, part in enumerate(parts, 1):
    zp = os.path.join(a.out, f'{a.prefix}{i}.zip')
    with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr(f'{name}/_PARTS/{a.prefix}{i}-of-{n}.txt', f'Part {i} of {n}. See HOW-TO-MERGE.txt (in part 1).\n')
        if i == 1:
            z.writestr(f'{name}/_PARTS/HOW-TO-MERGE.txt', how); z.writestr(f'{name}/_PARTS/MANIFEST.txt', man + '\n')
        for p in part:
            z.write(p, os.path.relpath(p, base), compress_type=zipfile.ZIP_STORED if os.path.splitext(p)[1].lower() in STORE else zipfile.ZIP_DEFLATED)
    print(f'{a.prefix}{i}.zip  {os.path.getsize(zp) / 1048576:6.1f} MB  {len(part):4d} files')
if a.single_too:
    zp = os.path.join(a.out, f'{name}.zip')
    with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p, _ in files: z.write(p, os.path.relpath(p, base))
    print(f'{name}.zip {os.path.getsize(zp) / 1048576:.1f} MB (single — only deliverable if under the upload limit)')
print(f'{n} parts · {total} files · merge guide in part 1: {name}/_PARTS/HOW-TO-MERGE.txt')
print('\n' + how)
