import datetime, hashlib, json, os, re, subprocess, sys, time, urllib.parse, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = ('apps.json', 'psp_apps.json', 'preserved/plugins.json', 'preserved/tools.json')
WRITE = '--write' in sys.argv
ONLY = sys.argv[sys.argv.index('--only') + 1] if '--only' in sys.argv else None
BAD = ('-logging', '-debug', '-test', '_test', 'blank', 'source', 'partial', 'symbols', 'no-demo', 'nodemo')
HOSTS = [('github', r'https?://github\.com/([^/\s]+)/([^/\s?#]+)'),
         ('gitlab', r'https?://gitlab\.com/([^/\s]+)/([^/\s?#]+)'),
         ('gitea', r'https?://git\.silica\.codes/([^/\s]+)/([^/\s?#]+)')]
def get(u):
    try: return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'VitaHomebrewDB'}), timeout=60))
    except Exception: return None
def releases(host, key):
    if host == 'github':
        r = subprocess.run(['gh', 'api', 'repos/%s/releases?per_page=4' % key], capture_output=True, text=True, timeout=90)
        return json.loads(r.stdout) if r.returncode == 0 else None
    if host == 'gitea': return get('https://git.silica.codes/api/v1/repos/%s/releases?limit=4' % key)
    raw = get('https://gitlab.com/api/v4/projects/%s/releases?per_page=4' % urllib.parse.quote(key, safe='')) or []
    return [{'tag_name': r.get('tag_name'), 'prerelease': False, 'draft': False,
             'assets': [{'name': l.get('name'), 'browser_download_url': l.get('url'), 'size': 0}
                        for l in (r.get('assets') or {}).get('links') or []]} for r in raw]
def repo_of(a):
    for field in ('release_page', 'source', 'url'):
        v = a.get(field) or ''
        if 'DrDecki/VitaHomebrewDB' in v: continue
        for host, pat in HOSTS:
            m = re.match(pat, v)
            if m: return host, '%s/%s' % (m.group(1), re.sub(r'\.git$', '', m.group(2)))
    return None, None
def vernum(s): return [int(x) for x in re.findall(r'\d+', s or '')[:4]]
def slug(s): return re.sub(r'[^a-z0-9]', '', (s or '').lower())
todo = []
for f in FILES:
    for a in json.load(open(os.path.join(ROOT, f), encoding='utf-8')):
        if 'nightly' in (a.get('version') or '').lower(): continue
        if ONLY and slug(a['name']) != slug(ONLY): continue
        host, key = repo_of(a)
        if not key: continue
        rel = releases(host, key)
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
        kern = re.sub(r'^(v|ver|version|release)[-_. ]*', '', r['tag_name'] or '', flags=re.I)
        if not re.match(r'^[0-9]+(\.[0-9]+)*[a-z]?(-?(alpha|beta|rc)[.-]?[0-9]*)?$', kern, re.I): continue
        nv, av, bv = 'v.' + kern, vernum(kern), vernum(a.get('version'))
        if [i for i in av if i] == [i for i in bv if i] or av <= bv: continue
        data = None
        d0 = (a.get('data') or '').strip()
        if d0 and '/releases/download/' in d0:
            dn = d0.rsplit('/', 1)[-1]
            data = next(((y['browser_download_url'], y.get('size', 0)) for y in r['assets'] if y['name'] == dn), None)
        print('  %-28s %-14s -> %-12s %s%s' % (a['name'][:28], (a.get('version') or '')[:14], nv, x['name'][:26], '  +data' if data else ''), flush=True)
        todo.append((f, a['id'], a['name'], a.get('version'), nv, a['url'].rsplit('/', 1)[-1], x['browser_download_url'], x['name'], data))
        time.sleep(0.2)
print('\n%d Aktualisierungen%s' % (len(todo), '' if WRITE else ' (Probelauf)'))
if not WRITE: sys.exit()
done = []
for k, (f, i, name, ov, nv, ofile, url, nfile, data) in enumerate(todo):
    if k and len(todo) < 50: time.sleep(60)
    try: b = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'v'}), timeout=900).read()
    except Exception as e: print('  %s: Download fehlgeschlagen, %s' % (name, type(e).__name__)); continue
    p = os.path.join(ROOT, f); d = json.load(open(p, encoding='utf-8'))
    for a in d:
        if a['id'] == i:
            a.update(version=nv, url=url, size=str(len(b)), hash=hashlib.md5(b).hexdigest(),
                     updated=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))
            if data: a.update(data=data[0], data_size=str(data[1] or a.get('data_size') or '0'))
    json.dump(d, open(p, 'w', encoding='utf-8'), indent=4, ensure_ascii=False)
    done.append('- **%s** %s -> %s  \n  `%s` -> `%s` (%.1f MB)%s' % (name, ov, nv, ofile, nfile, len(b) / 1048576.0, ', data file updated too' if data else ''))
    print('  geschrieben: %s %s' % (i, nv), flush=True)
open(os.path.join(ROOT, 'update_report.md'), 'w', encoding='utf-8').write('## Updates found\n\n' + ('\n'.join(done) if done else 'None.') + '\n')
if os.environ.get('GITHUB_OUTPUT'):
    open(os.environ['GITHUB_OUTPUT'], 'a').write('count=%d\n' % len(done))
