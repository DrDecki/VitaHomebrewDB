import collections, datetime, json, os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = ('apps.json', 'psp_apps.json', 'preserved/plugins.json', 'preserved/tools.json')
WRITE = '--write' in sys.argv
iso = lambda ts: datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
def git(*a): return subprocess.run(['git', *a], capture_output=True, cwd=ROOT).stdout
import re
RESCUE = re.compile(r'rinnegatamante\.eu|get_hb_url|archive\.org|gamebrew|cbps', re.I)
def key(a):
    v = re.sub(r'^[v.\s]+', '', (a.get('version') or '').strip().lower())
    u = a.get('url') or ''
    b = re.sub(r'^\d+-', '', u.split('?')[0].rstrip('/').rsplit('/', 1)[-1].lower())
    return (v, b, u)
def changed(old, new):
    if old[0] != new[0]: return True
    return old[1] != new[1] and not RESCUE.search(old[2])
pro_commit = collections.Counter(); msg = {}
alle = []; gesamt = 0
for f in FILES:
    log = [l.split(' ', 2) for l in git('log', '--reverse', '--format=%H %ct %s', '--', f).decode().splitlines() if l.strip()]
    prev, last = {}, {}
    for sha, ts, s in log:
        try: d = json.loads(git('show', '%s:%s' % (sha, f)))
        except Exception: continue
        if not isinstance(d, list): continue
        cur = {str(a['id']): key(a) for a in d if isinstance(a, dict) and 'id' in a}
        for i, k in cur.items():
            if i in prev and changed(prev[i], k):
                last[i] = int(ts); pro_commit[sha[:7]] += 1; msg[sha[:7]] = s[:60]
        prev = cur
    p = os.path.join(ROOT, f); d = json.load(open(p, encoding='utf-8'))
    n = 0
    for a in d:
        ts = last.get(str(a['id']))
        if ts: a['updated'] = iso(ts); n += 1; alle.append((a['updated'], a['id'], a['name'], f))
        else: a.pop('updated', None)
    gesamt += n
    print('  %-24s %4d Commits, %4d Eintraege mit updated' % (f, len(log), n))
    if WRITE: json.dump(d, open(p, 'w', encoding='utf-8'), indent=4, ensure_ascii=False)
print('\n  Commits mit den meisten Updates:')
for sha, c in pro_commit.most_common(8): print('    %s %4d  %s' % (sha, c, msg[sha]))
print('\n  insgesamt %d Eintraege mit updated, zehn neueste:' % gesamt)
for t, i, n, f in sorted(alle, reverse=True)[:10]: print('    %s  %-5s %-34s %s' % (t, i, n[:34], f))
if not WRITE: print('\n  Probelauf, nichts geschrieben')
