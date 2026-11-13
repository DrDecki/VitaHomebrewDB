import datetime, hashlib, json, os, re, subprocess, sys, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WRITE = '--write' in sys.argv
SKIP = {'Shards of Dawn'}
BAD = re.compile(r'-logging|-debug|-test|_test|blank|source|symbols', re.I)
TYP = {'1': 'original', '2': 'port', '4': 'utility', '5': 'emulator'}
def gh(p):
    r = subprocess.run(['gh', 'api', p], capture_output=True, text=True, timeout=90)
    return json.loads(r.stdout) if r.returncode == 0 else None
subprocess.run(['python3', 'watch_vitadb.py'], cwd=ROOT, capture_output=True)
vd = {}
for e in ('list_hbs_by_titleid', 'list_plugins_json', 'list_psp_hbs_json', 'list_tools_json'):
    req = urllib.request.Request('https://www.rinnegatamante.eu/vitadb/%s.php' % e, data=b'', headers={'User-Agent': 'v'})
    for a in json.load(urllib.request.urlopen(req, timeout=90)): vd[a['name']] = a
t = open(os.path.join(ROOT, 'vitadb_issue.md'), encoding='utf-8').read()
neu = re.findall(r'^- \*\*(.+?)\*\* by (.+?) \*\((.+?), (.+?)\)\*  —  (.+)$', t, re.M)
for name, author, kat, datum, src in neu:
    v = vd.get(name, {})
    if name in SKIP or 'nightly' in (v.get('version') or '').lower():
        print('  SKIP  %-34s nightly' % name[:34]); continue
    if kat != 'Vita homebrews':
        print('  HAND  %-34s %s' % (name[:34], kat)); continue
    m = re.search(r'github\.com/([^/\s]+/[^/\s?#]+)', src)
    if not m: print('  HAND  %-34s keine GitHub-Quelle' % name[:34]); continue
    repo = re.sub(r'(\.git)?/*$', '', m.group(1))
    rel = gh('repos/%s/releases?per_page=3' % repo) or []
    best = next(((r, a) for r in rel if not r.get('draft') for a in r.get('assets', [])
                 if a['name'].lower().endswith('.vpk') and not BAD.search(a['name'])), None)
    if not best: print('  HAND  %-34s kein VPK im Release' % name[:34]); continue
    r, a = best
    ver = 'v.' + re.sub(r'^[^\d]*', '', r['tag_name'])
    print('  OK    %-34s %-12s %s' % (name[:34], ver[:12], a['name'][:30]), flush=True)
    if not WRITE: continue
    args = ['python3', 'add_app.py', '--url', a['browser_download_url'], '--type', TYP.get(v.get('type'), 'original'),
            '--author', author, '--desc', (v.get('description') or name + ' for PSVITA.').strip(),
            '--source', 'https://github.com/' + repo, '--release-page', 'https://github.com/%s/releases' % repo, '--version', ver]
    if (v.get('requirements') or '').strip(): args += ['--requirements', v['requirements'].strip()]
    out = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    res = (out.stdout + out.stderr).strip().splitlines()[-1:] or ['?']
    if 'icon0.png' in res[0]:
        b = urllib.request.urlopen(urllib.request.Request(a['browser_download_url'], headers={'User-Agent': 'v'}), timeout=900).read()
        p = os.path.join(ROOT, 'apps.json'); d = json.load(open(p, encoding='utf-8'))
        nid = str(max(int(x['id']) for f in ('apps.json', 'psp_apps.json', 'preserved/plugins.json', 'preserved/tools.json')
                      for x in json.load(open(os.path.join(ROOT, f), encoding='utf-8'))) + 1)
        d.append({'id': nid, 'name': re.sub(r' Vita$', '', name), 'author': author, 'version': ver, 'type': v.get('type') or '1',
          'titleid': '', 'icon': '', 'description': (v.get('description') or '').strip(), 'long_description': '',
          'changelog': '- First Release', 'requirements': (v.get('requirements') or '').strip(), 'url': a['browser_download_url'],
          'size': str(len(b)), 'hash': hashlib.md5(b).hexdigest(), 'hash2': '', 'data': '', 'data_size': '0',
          'date': datetime.date.today().isoformat(), 'downloads': '0', 'release_page': 'https://github.com/%s/releases' % repo,
          'source': 'https://github.com/' + repo, 'screenshots': '', 'status': '0', 'tags': '', 'trailer': '',
          'trophies': '0', 'ai': '0', 'score': '0'})
        json.dump(d, open(p, 'w', encoding='utf-8'), indent=4, ensure_ascii=False)
        res = ['added "%s" as id %s (ohne Icon)' % (name, nid)]
    print('        %s' % res[0])
