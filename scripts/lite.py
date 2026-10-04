#!/usr/bin/env python3
"""
lite.py — LITE MODE: run every production module the company profile asks for, in dependency order, unattended.
The result is a complete, consistent brand system generated from the foundations (no hand art-direction).
In FULL mode the art director uses the same modules as the starting point and then refines with specialists.

usage: python3 scripts/lite.py --repo ../ACME-BRAND [--only icons,ui-kit] [--skip website] [--list] [--continue-on-error]

Modules live in assets/modules/<name>/ (module.json + build.py|build.js). Contract: references/modules.md.
Each module is called as:  <run…> --repo <repo>   (cwd = module folder) and must be idempotent.
Records SOURCE/JSON/modules-run.json (status, seconds, outputs) and refreshes READMEs (build_docs.py).
"""
import argparse, json, os, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); SKILL = os.path.dirname(HERE); MODS = os.path.join(SKILL, 'assets', 'modules')

def discover():
    out = {}
    if not os.path.isdir(MODS): return out
    for d in sorted(os.listdir(MODS)):
        mj = os.path.join(MODS, d, 'module.json')
        if os.path.exists(mj): m = json.load(open(mj)); m['dir'] = os.path.join(MODS, d); out[m['name']] = m
    return out

def order(mods, wanted):
    seen, out = set(), []
    def visit(n, stack=()):
        if n in seen or n not in mods: return
        if n in stack: raise SystemExit(f'dependency cycle: {" → ".join(stack + (n,))}')
        for d in mods[n].get('depends', []): visit(d, stack + (n,))
        seen.add(n); out.append(n)
    for n in sorted(wanted, key=lambda n: mods[n].get('order', 50)): visit(n)
    return [n for n in out if n in wanted or any(n in mods[w].get('depends', []) for w in wanted)]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--repo', required=True); ap.add_argument('--only', default=''); ap.add_argument('--skip', default='')
    ap.add_argument('--list', action='store_true'); ap.add_argument('--continue-on-error', action='store_true'); ap.add_argument('--timeout', type=int, default=1800)
    a = ap.parse_args(); repo = os.path.abspath(a.repo); mods = discover()
    prof_p = os.path.join(repo, 'SOURCE', 'CONFIG', 'profile.json'); prof = json.load(open(prof_p)) if os.path.exists(prof_p) else {'modules': {}}
    enabled = [n for n in mods if prof.get('modules', {}).get(n, True) and mods[n].get('lite', True)]
    if a.only: enabled = [n for n in a.only.split(',') if n in mods]
    enabled = [n for n in enabled if n not in a.skip.split(',')]
    plan = order(mods, enabled)
    if a.list:
        for n in plan: print(f"{n:20s} {mods[n].get('title', '')}  ← {', '.join(mods[n].get('depends', [])) or 'foundation'}")
        return
    log_p = os.path.join(repo, 'SOURCE', 'JSON', 'modules-run.json'); log = json.load(open(log_p)) if os.path.exists(log_p) else {}
    failed = []
    for n in plan:
        m = mods[n]; t0 = time.time(); print(f'\n=== {n} — {m.get("title", "")}', flush=True)
        try:
            subprocess.run(m['run'] + ['--repo', repo], cwd=m['dir'], check=True, timeout=a.timeout)
            log[n] = {'status': 'ok', 'seconds': round(time.time() - t0, 1), 'version': m.get('version', '1.0.0'), 'outputs': m.get('outputs', [])}
        except Exception as e:
            log[n] = {'status': f'failed: {e}', 'seconds': round(time.time() - t0, 1)}; failed.append(n)
            print(f'!!! {n} failed: {e}', flush=True)
            if not a.continue_on_error: break
        json.dump(log, open(log_p, 'w'), indent=1)
    subprocess.run([sys.executable, os.path.join(HERE, 'build_spec.py'), '--repo', repo]); subprocess.run([sys.executable, os.path.join(HERE, 'build_docs.py'), '--repo', repo])
    print('\nLite run: ' + ', '.join(f"{n} {log[n]['status']} ({log[n]['seconds']}s)" for n in plan if n in log))
    sys.exit(1 if failed else 0)

if __name__ == '__main__':
    main()
