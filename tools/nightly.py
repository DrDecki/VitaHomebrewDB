import datetime, hashlib, io, json, os, re, subprocess, sys, time, urllib.request, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from media import _upload
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); WRITE = '--write' in sys.argv
FILES = ('apps.json', 'psp_apps.json', 'preserved/plugins.json', 'preserved/tools.json')
ROLL = re.compile(r'https://github\.com/([^/]+/[^/]+)/releases/download/(continuous|latest|nightly|release)/([^/?#]+)$', re.I)
BASE = 'https://github.com/DrDecki/VitaHomebrewDB/releases/download/nightly/'
now = lambda: datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
def api(p):
    r = subprocess.run(['gh', 'api', p], capture_output=True, text=True)
    return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else None
def get(u): return urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'VitaHomebrewDB'}), timeout=900).read()
cat = {}; todo = []
for f in FILES:
    for a in json.load(open(os.path.join(ROOT, f), encoding='utf-8')):
        cat[a['url']] = (f, a)
        m = ROLL.match(a.get('url') or '')
        if not m or 'DrDecki/VitaHomebrewDB' in m.group(1): continue
        rel = api('repos/%s/releases/tags/%s' % (m.group(1), m.group(2)))
        x = next((y for y in (rel or {}).get('assets', []) if y['name'] == m.group(3)), None)
        if not x: continue
        if a.get('size') == str(x['size']): continue
        todo.append(('roll', f, a['id'], a['name'], a['url'], 'Nightly ' + x['updated_at'][:10], None))
for s in json.load(open(os.path.join(ROOT, 'nightly_sources.json'), encoding='utf-8')):
    arts = api('repos/%s/actions/artifacts?name=%s&per_page=5' % (s['repo'], s['artifact'])) or {}
    art = next((x for x in arts.get('artifacts', []) if not x.get('expired')), None)
    if not art: print('  %s: kein Artefakt' % s['name']); continue
    url = BASE + s['file']; hit = cat.get(url)
    ver = 'Nightly %s (%s)' % (art['created_at'][:10], ((art.get('workflow_run') or {}).get('head_sha') or '')[:7])
    if hit and hit[1].get('version') == ver: continue
    todo.append(('art', hit[0] if hit else 'apps.json', hit[1]['id'] if hit else None, s['name'], url, ver, (s, art)))
for t in todo: print('  %-4s %-30s -> %s' % (t[0], t[3][:30], t[5]), flush=True)
print('\n%d Nightly-Aenderungen%s' % (len(todo), '' if WRITE else ' (Probelauf)'))
if not WRITE: sys.exit()
done = []
for k, (kind, f, i, name, url, ver, extra) in enumerate(todo):
    if k and len(todo) < 50: time.sleep(60)
    try:
        if kind == 'roll': b = get(url)
        else:
            s, art = extra
            z = subprocess.run(['gh', 'api', 'repos/%s/actions/artifacts/%d/zip' % (s['repo'], art['id'])], capture_output=True).stdout
            zf = zipfile.ZipFile(io.BytesIO(z)); vi = next(m for m in zf.infolist() if m.filename.lower().endswith('.vpk'))
            b = zf.read(vi); tmp = '/tmp/' + s['file']; open(tmp, 'wb').write(b)
            if not _upload('nightly', tmp, 'Nightly builds', 'Latest builds of projects that only publish nightlies. Each file is replaced when a new build appears.'):
                print('  %s: Upload fehlgeschlagen' % name); continue
    except Exception as e: print('  %s: %s' % (name, type(e).__name__)); continue
    if i is None:
        args = ['python3', 'add_app.py', '--url', url, '--type', s['type'], '--author', s['author'], '--name', name, '--desc', s['desc'],
                '--source', 'https://github.com/' + s['repo'], '--release-page', 'https://github.com/%s/actions' % s['repo'], '--version', ver]
        o = subprocess.run(args + (['--requirements', s['requirements']] if s.get('requirements') else []), cwd=ROOT, capture_output=True, text=True)
        print('  ' + ([l for l in (o.stdout + o.stderr).splitlines() if l.startswith('added') or 'ERROR' in l] or ['? ' + name])[0], flush=True)
        done.append('- **%s** added as %s' % (name, ver)); continue
    p = os.path.join(ROOT, f); d = json.load(open(p, encoding='utf-8'))
    for a in d:
        if a['id'] == i:
            old = a.get('version'); h = hashlib.md5(b).hexdigest()
            if kind == 'roll' and h == a.get('hash'): ver = None; break
            if kind == 'roll' and not re.match(r'(nightly|v\.(continuous|latest|nightly))', (old or '').lower()): ver = old
            a.update(version=ver, size=str(len(b)), hash=h, updated=now())
    if ver is None: continue
    json.dump(d, open(p, 'w', encoding='utf-8'), indent=4, ensure_ascii=False)
    done.append('- **%s** %s -> %s  \n  nightly build, %.1f MB' % (name, old, ver, len(b) / 1048576.0))
    print('  geschrieben: %s %s' % (i, ver), flush=True)
rp = os.path.join(ROOT, 'update_report.md')
old = open(rp, encoding='utf-8').read() if os.path.exists(rp) else ''
prev = [l for l in old.splitlines() if l.startswith('- **') or l.startswith('  ')]
allv = prev + [x for d in done for x in d.split('\n')]
open(rp, 'w', encoding='utf-8').write('## Updates found\n\n' + ('\n'.join(allv) if allv else 'None.') + '\n')
if os.environ.get('GITHUB_OUTPUT'):
    open(os.environ['GITHUB_OUTPUT'], 'a').write('count=%d\n' % sum(1 for l in allv if l.startswith('- **')))
