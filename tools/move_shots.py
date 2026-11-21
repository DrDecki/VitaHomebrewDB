import json, os, subprocess, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = 'DrDecki/VitaHomebrewDB'; DIR = os.path.join(ROOT, 'screenshots')
BASE = 'https://github.com/%s/releases/download/' % REPO
tag = lambda n: 'shots-' + (n[0].lower() if n[0].lower() in '0123456789abcdef' else 'x')
def gh(*a): return subprocess.run(['gh'] + list(a) + ['--repo', REPO], capture_output=True, text=True)
def pause():
    rl = json.loads(subprocess.run(['gh', 'api', 'rate_limit'], capture_output=True, text=True).stdout or '{}').get('resources', {}).get('core', {})
    w = max(60, rl.get('reset', 0) - int(time.time()) + 30) if rl.get('remaining', 1000) < 100 else 600
    print('    Limit erreicht, warte %d Minuten (%s)' % (w // 60, time.strftime('bis %H:%M', time.localtime(time.time() + w))), flush=True); time.sleep(w)
def run(*a):
    while True:
        r = gh(*a)
        if r.returncode == 0: return r
        if 'rate limit' in r.stderr.lower() or 'secondary' in r.stderr.lower(): pause(); continue
        return r
def assets(t): return set(run('release', 'view', t, '--json', 'assets', '--jq', '.assets[].name').stdout.split())
files = sorted(os.listdir(DIR)) if os.path.isdir(DIR) else []
groups = {}
for f in files: groups.setdefault(tag(f), []).append(f)
ok = True
for t in sorted(groups):
    if run('release', 'view', t).returncode:
        run('release', 'create', t, '--title', 'Screenshots ' + t[-1], '--notes', 'Catalog screenshots whose file name starts with "%s".' % t[-1])
    todo = [f for f in groups[t] if f not in assets(t)]
    for i in range(0, len(todo), 20):
        r = run('release', 'upload', t, '--clobber', *[os.path.join(DIR, f) for f in todo[i:i + 20]])
        if r.returncode: print('  %s: Fehler %s' % (t, r.stderr.strip()[:100]))
        time.sleep(3)
    miss = [f for f in groups[t] if f not in assets(t)]
    print('  %-8s %4d lokal, %4d oben%s  (%s)' % (t, len(groups[t]), len(groups[t]) - len(miss), '' if not miss else '  FEHLEN %d' % len(miss), time.strftime('%H:%M')), flush=True)
    if miss: ok = False
if not ok: print('\nnicht vollstaendig, nochmal starten'); sys.exit(1)
n = 0
for f in ('apps.json', 'psp_apps.json', 'preserved/plugins.json', 'preserved/tools.json'):
    p = os.path.join(ROOT, f); d = json.load(open(p, encoding='utf-8'))
    for a in d:
        s = [x.strip() for x in (a.get('screenshots') or '').split(';') if x.strip()]
        if not any(x.startswith('screenshots/') for x in s): continue
        a['screenshots'] = ';'.join(BASE + tag(x[12:]) + '/' + x[12:] if x.startswith('screenshots/') else x for x in s); n += 1
    json.dump(d, open(p, 'w', encoding='utf-8'), indent=4, ensure_ascii=False)
print('\nalles oben, %d Eintraege auf volle Adressen umgestellt' % n)
