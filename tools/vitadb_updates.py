import datetime, hashlib, io, zipfile, json, os, re, subprocess, sys, time, urllib.parse, urllib.request
from media import mirror_upload
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); WRITE = '--write' in sys.argv
FILES = ('apps.json', 'psp_apps.json', 'preserved/plugins.json', 'preserved/tools.json')
MIRROR = 'https://github.com/DrDecki/VitaHomebrewDB/releases/download/mirror/'
norm = lambda s: re.sub(r'(vita|psvita)$', '', re.sub(r'[^a-z0-9]', '', (s or '').lower()))
vn = lambda s: [int(x) for x in re.findall(r'\d+', s or '')[:4]]
rep = lambda s: (re.search(r'github\.com/([^/\s]+/[^/\s?#]+)', s or '') or [None, ''])[1].lower().removesuffix('.git')
AL = json.load(open(os.path.join(ROOT, 'author_aliases.json'), encoding='utf-8'))
def _parts(s): return [x.strip() for x in re.split(r'\s*\\?&\s*|\s*,\s*|\s+and\s+', s or '') if x.strip()]
def same_author(ours, theirs):
    op = {norm(x)[:4] for x in _parts(ours)}
    return any(norm(AL.get(x, x))[:4] in op for x in _parts(theirs))
BL = json.load(open(os.path.join(ROOT, 'blocklist.json'), encoding='utf-8'))
def blocked(name, author, src=''):
    if any(b['match'].lower() in ((author or '') + ' ' + (src or '')).lower() for b in BL['authors']): return True
    return any(re.search(b['match'], name or '', re.I) for b in BL['names'])
uns = [(f, a) for f in FILES for a in json.load(open(os.path.join(ROOT, f), encoding='utf-8'))]
by_repo, by_name, by_id, by_tid = {}, {}, {}, {}
for f, a in uns:
    for k in ('source', 'release_page', 'url'):
        r = rep(a.get(k))
        if r and 'drdecki/vitahomebrewdb' not in r: by_repo.setdefault(r, (f, a))
    by_name.setdefault(norm(a['name']), (f, a)); by_id[a['id']] = (f, a)
    if a.get('titleid'): by_tid.setdefault(a['titleid'].upper(), []).append((f, a))
best = {}
for ep in ('list_hbs_by_titleid', 'list_plugins_json', 'list_psp_hbs_json', 'list_tools_json'):
    try: lst = json.load(urllib.request.urlopen(urllib.request.Request('https://www.rinnegatamante.eu/vitadb/%s.php' % ep, data=b'', headers={'User-Agent': 'VitaHomebrewDB'}), timeout=90))
    except Exception as e: print('  %s: %s' % (ep, type(e).__name__)); continue
    for v in lst:
        _c = by_tid.get((v.get('titleid') or '').upper(), [])
        hit = next((x for x in _c if norm(x[1]['name']) == norm(v['name'])), None) or next((x for x in _c if same_author(x[1].get('author'), v.get('author')) and norm(x[1]['name'])[:6] == norm(v['name'])[:6] and len(_c) == 1), None)
        if not hit:
            r = by_repo.get(rep(v.get('source'))) or by_repo.get(rep(v.get('release_page')))
            if r and norm(r[1]['name'])[:6] == norm(v['name'])[:6]: hit = r
        if not hit: hit = by_name.get(norm(v['name']))
        if not hit and str(v.get('id')) in by_id and norm(by_id[str(v['id'])][1]['name'])[:4] == norm(v['name'])[:4]: hit = by_id[str(v['id'])]
        if not hit: continue
        f, a = hit; ver = v.get('version') or ''
        if (ep == 'list_psp_hbs_json') != (f == 'psp_apps.json'): continue
        if 'nightly' in ver.lower() or re.search(r'\d{4}-\d{2}-\d{2}', ver): continue
        nv, ov = vn(ver), vn(a.get('version'))
        if not (nv and ov and nv > ov) or [x for x in nv if x] == [x for x in ov if x]: continue
        if not same_author(a.get('author'), v.get('author')) or blocked(a['name'], a.get('author'), a.get('source')): continue
        url = v.get('url') or ''
        if not url: continue
        if not url.startswith('http'): url = 'https://www.rinnegatamante.eu/vitadb/' + url.lstrip('/')
        if a['id'] not in best or nv > vn(best[a['id']][4]):
            best[a['id']] = (f, a['id'], a['name'], a.get('version'), 'v.' + re.sub(r'^[vV.]+', '', ver), url)
for f, i, n, ov, nv, url in best.values(): print('  %-5s %-28s %-12s -> %s' % (i, n[:28], (ov or '')[:12], nv), flush=True)
print('\n%d Updates von VitaDB%s' % (len(best), '' if WRITE else ' (Probelauf)'))
if not WRITE: sys.exit()
done = []
for k, (f, i, n, ov, nv, url) in enumerate(best.values()):
    if k and len(best) < 50: time.sleep(60)
    try: b = urllib.request.urlopen(urllib.request.Request(urllib.parse.quote(url, safe=':/%?=&'), headers={'User-Agent': 'VitaHomebrewDB'}), timeout=900).read()
    except Exception as e: print('  %s: Download fehlgeschlagen %s' % (n, type(e).__name__)); continue
    fn = '%s-%s-%s.%s' % (i, re.sub(r'[^a-z0-9]+', '-', n.lower()).strip('-')[:40], re.sub(r'[^A-Za-z0-9.]+', '', nv[2:]), 'vpk' if b[:4] == b'PK\x03\x04' and 'sce_sys/param.sfo' in zipfile.ZipFile(io.BytesIO(b)).namelist() else 'zip')
    open('/tmp/' + fn, 'wb').write(b)
    murl = mirror_upload('/tmp/' + fn)
    if not murl:
        print('  %s: Upload fehlgeschlagen' % n); continue
    p = os.path.join(ROOT, f); data = json.load(open(p, encoding='utf-8'))
    for a in data:
        if a['id'] == i:
            a.update(version=nv, url=murl, size=str(len(b)), hash=hashlib.md5(b).hexdigest(), updated=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))
    json.dump(data, open(p, 'w', encoding='utf-8'), indent=4, ensure_ascii=False)
    done.append('- **%s** %s -> %s  \n  from VitaDB, mirrored as `%s` (%.1f MB)' % (n, ov, nv, fn, len(b) / 1048576.0))
    print('  geschrieben: %s %s' % (i, nv), flush=True)
rp = os.path.join(ROOT, 'update_report.md')
old = open(rp, encoding='utf-8').read() if os.path.exists(rp) else '## Updates found\n\nNone.\n'
prev = [l for l in old.splitlines() if l.startswith('- **') or l.startswith('  ')]
allv = prev + [x for d in done for x in d.split('\n')]
open(rp, 'w', encoding='utf-8').write('## Updates found\n\n' + ('\n'.join(allv) if allv else 'None.') + '\n')
if os.environ.get('GITHUB_OUTPUT'):
    open(os.environ['GITHUB_OUTPUT'], 'a').write('count=%d\n' % sum(1 for l in allv if l.startswith('- **')))
