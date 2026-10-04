# Packaging and delivery

## Facts that shape delivery
- Chat uploads of very large files fail (observed: ≥ 50 MB failed, ≤ 22 MB worked). Use zip parts of **≤ 18 MB**.
- People want something downloadable early. When asked, ship the current state immediately (as parts), then keep working.
- Name sets so they never mix: `acme1.zip…` for a work-in-progress set, `acme-final-1.zip…` for the final; tell the user to
  merge a new set into a new empty folder.

## Steps
```bash
python3 scripts/validate_repo.py <repo> --fix
python3 scripts/check_links.py <repo>
node scripts/optimize_png.js <repo>                       # palette-quantise previews (~60 % smaller; masters untouched)
python3 scripts/split_zip.py <repo> <out> --prefix acme-final- --mb 18
```
`split_zip.py` writes standalone parts (full paths) and puts `_PARTS/HOW-TO-MERGE.txt` + `MANIFEST.txt` (SHA-256 of every file,
expected count) in part 1, and prints the merge commands. Paste them in your message:

**macOS / Linux** (terminal opened in the folder with all parts)
```bash
mkdir -p merged && for f in acme-final-*.zip; do unzip -o -q "$f" -d merged; done
rm -rf merged/ACME-BRAND/_PARTS
echo "Files: $(find merged/ACME-BRAND -type f | wc -l)"
```
**Windows PowerShell**
```powershell
New-Item -ItemType Directory -Force merged | Out-Null
Get-ChildItem acme-final-*.zip | ForEach-Object { Expand-Archive $_.FullName -DestinationPath .\merged -Force }
Remove-Item .\merged\ACME-BRAND\_PARTS -Recurse -Force
"Files: " + (Get-ChildItem .\merged\ACME-BRAND -Recurse -File).Count
```
Also explain how to open a terminal in a folder (macOS: right-click the folder → Services → New Terminal at Folder; Windows: type
`powershell` in the Explorer address bar), the Safari auto-unzip fallback (copy the unzipped folders' contents into one folder),
and optionally `git init` the merged repository.

## What to send
1. All zip parts (one SendUserFile call with every path).
2. The brand-book PDF separately if it exists and is ≤ 20 MB.
3. Optionally the showcase as a hosted page (portable build; ≤ 255 files).
4. A short message: what is inside (one line per area), the merge commands, the expected file count, and the decisions only the
   client can make (replace sample content, native-language review, tagline choice, legal checks, print proofs, better artwork).
