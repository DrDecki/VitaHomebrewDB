import datetime, hashlib, json, os, re, subprocess, sys, time, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = ('apps.json', 'psp_apps.json', 'preserved/plugins.json', 'preserved/tools.json')
WRITE = '--write' in sys.argv
ONLY = sys.argv[sys.argv.index('--only') + 1] if '--only' in sys.argv else None
BAD = ('-logging', '-debug', '-test', '_test', 'blank', 'source', 'partial', 'symbols')
def gh(p):
    r = subprocess.run(['gh', 'api', p], capture_output=True, text=True, timeout=90)
    return json.loads(r.stdout) if r.returncode == 0 else None
def vernum(s): return [int(x) for x in re.findall(r'\d+', s or '')[:4]]
def slug(s): return re.sub(r'[^a-z0-9]', '', (s or '').lower())
todo = []
for f in FILES:
    for a in json.load(open(os.path.join(ROOT, f), encoding='utf-8')):
        if 'nightly' in (a.get('version') or '').lower(): continue
        if ONLY and slug(a['name']) != slug(ONLY): continue
        m = re.search(r'github\.com/([^/\s]+/[^/\s?#]+)', (a.get('source') or '') + ' ' + (a.get('release_page') or ''))
        if not m: continue
        rel = gh('repos/%s/releases?per_page=4' % re.sub(r'(\.git)?/*$', '', m.group(1)))
        if not rel: continue
        ext = os.path.splitext(a['url'].split('?')[0])[1].lower()
        stem = re.sub(r'\d', '', slug(os.path.splitext(a['url'].rsplit('/', 1)[-1])[0]))
        best = None
        for r in rel:
            if r.get('prerelease') or r.get('draft'): continue
            for x in r.get('assets', []):
                st = re.sub(r'\d', '', slug(os.path.splitext(x['name'])[0]))
                if os.path.splitext(x['name'])[1].lower() == ext and not any(w in x['name'].lower() for w in BAD) \
                   and (not stem or not st or stem in st or st in stem):
                    best = (r, x); break
            if best: break
        if not best: continue
        r, x = best
        kern = re.sub(r'^(v|ver|version|release)[-_. ]*', '', r['tag_name'], flags=re.I)
        if not re.match(r'^[0-9]+(\.[0-9]+)*[a-z]?$', kern, re.I): continue
        nv, av, bv = 'v.' + kern, vernum(kern), vernum(a.get('version'))
        if [i for i in av if i] == [i for i in bv if i] or av <= bv: continue
        print('  %-28s %-14s -> %-12s %s' % (a['name'][:28], (a.get('version') or '')[:14], nv, x['name'][:26]), flush=True)
        todo.append((f, a['id'], nv, x['browser_download_url']))
        time.sleep(0.2)
print('\n%d Aktualisierungen%s' % (len(todo), '' if WRITE else ' (Probelauf)'))
if not WRITE: sys.exit()
for k, (f, i, nv, url) in enumerate(todo):
    if k and len(todo) < 50: time.sleep(60)
    b = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'v'}), timeout=900).read()
    p = os.path.join(ROOT, f); d = json.load(open(p, encoding='utf-8'))
    for a in d:
        if a['id'] == i:
            a.update(version=nv, url=url, size=str(len(b)), hash=hashlib.md5(b).hexdigest(),
                     updated=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))
    json.dump(d, open(p, 'w', encoding='utf-8'), indent=4, ensure_ascii=False)
    print('  geschrieben: %s %s' % (i, nv), flush=True)
