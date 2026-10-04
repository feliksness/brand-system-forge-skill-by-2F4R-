#!/usr/bin/env python3
"""contrast.py — WCAG contrast matrix.  usage: python3 scripts/contrast.py "#0F766E" "#111827" ... --bg "#FFFFFF" "#F8FAFC" "#111827"
Prints ratio + rating (AAA ≥7, AA ≥4.5, AA-large ≥3) for every colour on every background."""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from colorlib import contrast, rating
ap = argparse.ArgumentParser(); ap.add_argument('colors', nargs='+'); ap.add_argument('--bg', nargs='+', default=['#FFFFFF', '#000000'])
a = ap.parse_args()
print('colour    ' + ''.join(f'{b:>18}' for b in a.bg))
for c in a.colors:
    print(f'{c:9} ' + ''.join(f'{contrast(c, b):9.2f} {rating(contrast(c, b)):>8}' for b in a.bg))
