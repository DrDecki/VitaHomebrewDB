import datetime, json, os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = ('apps.json', 'psp_apps.json', 'preserved/plugins.json', 'preserved/tools.json')
WRITE = '--write' in sys.argv
iso = lambda ts: datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
def git(*a): return subprocess.run(['git', *a], capture_output=True, cwd=ROOT).stdout
alle = []
for f in FILES:
    log = [l.split() for l in git('log', '--reverse', '--format=%H %ct', '--', f).decode().splitlines() if l.strip()]
    first = {}
    for sha, ts in log:
        try: d = json.loads(git('show', '%s:%s' % (sha, f)))
        except Exception: continue
        if not isinstance(d, list): continue
        for a in d:
            if isinstance(a, dict) and 'id' in a: first.setdefault(str(a['id']), int(ts))
    p = os.path.join(ROOT, f); cur = json.load(open(p, encoding='utf-8'))
    fallback = int(log[-1][1]) if log else int(datetime.datetime.now().timestamp())
    gesetzt = fehlte = 0
    for a in cur:
        if a.get('added'): continue
        ts = first.get(str(a['id']))
        if ts is None: ts = fallback; fehlte += 1
        a['added'] = iso(ts); gesetzt += 1
    print('  %-24s %4d Commits, %5d Eintraege, %5d gesetzt, %d ohne Fund (Fallback)' % (f, len(log), len(cur), gesetzt, fehlte))
    alle += [(a['added'], a['id'], a['name'], f) for a in cur]
    if WRITE: json.dump(cur, open(p, 'w', encoding='utf-8'), indent=4, ensure_ascii=False)
print('\n  zehn neueste:')
for t, i, n, f in sorted(alle, reverse=True)[:10]: print('    %s  %-5s %-34s %s' % (t, i, n[:34], f))
if not WRITE: print('\n  Probelauf, nichts geschrieben')
