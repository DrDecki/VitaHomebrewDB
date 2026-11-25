# Adds several entries at once. Usage: python3 tools/bulk_add.py spec.py
# spec.py defines S = [(repo, tag, asset, kind, type, name, desc, requirements, data_asset), ...]
# kind is "app" (VPK, or ZIP with a VPK inside) or "plugin" (skprx/suprx, goes to preserved/plugins.json).
import json, re, os, io, sys, zipfile, hashlib, datetime, subprocess, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT); sys.path.insert(0, os.path.join(ROOT, 'tools'))
from media import mirror_upload
exec(open(sys.argv[1], encoding='utf-8').read())
GH = 'https://github.com/'
FS = ('apps.json', 'psp_apps.json', 'preserved/plugins.json', 'preserved/tools.json')
def get(u): return urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'VitaHomebrewDB'}), timeout=600).read()
def ver(tag):
    if tag.lower() == 'nightly': return 'Nightly ' + datetime.date.today().isoformat()
    v = re.sub(r'^[^0-9]*', '', tag)
    return 'v.' + v if v else None
ok, bad = [], []
for k, (repo, tag, asset, kind, typ, name, desc, req, data) in enumerate(S):
    if k and len(S) < 50: __import__('time').sleep(60)
    owner = repo.split('/')[0]; url = GH + '%s/releases/download/%s/%s' % (repo, tag, asset)
    try:
        if kind == 'plugin':
            b = get(url); now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            nid = str(max(int(x['id']) for f in FS for x in json.load(open(f, encoding='utf-8'))) + 1)
            p = json.load(open('preserved/plugins.json', encoding='utf-8'))
            p.append({'name': name, 'version': ver(tag) or 'v.1.0', 'author': owner, 'description': desc, 'id': nid, 'date': datetime.date.today().isoformat(), 'screenshots': '', 'long_description': desc, 'downloads': '0', 'status': '0', 'source': GH + repo, 'release_page': GH + repo + '/releases', 'trailer': '', 'size': str(len(b)), 'data_size': '0', 'hash': hashlib.md5(b).hexdigest(), 'hash2': '', 'changelog': '- First Release', 'requirements': req, 'trophies': '0', 'tags': '', 'url': url, 'added': now, 'updated': now})
            json.dump(p, open('preserved/plugins.json', 'w', encoding='utf-8'), indent=4, ensure_ascii=False)
            ok.append(name); print('plugin', nid, name, flush=True); continue
        if asset.lower().endswith('.zip'):
            z = zipfile.ZipFile(io.BytesIO(get(url)))
            v = next(n for n in z.namelist() if n.lower().endswith('.vpk'))
            fn = '/tmp/%s-%s.vpk' % (re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-'), re.sub(r'[^A-Za-z0-9.]+', '', tag))
            open(fn, 'wb').write(z.read(v)); url = mirror_upload(fn)
            if not url: raise Exception('mirror upload failed')
        args = ['python3', 'add_app.py', '--type', typ, '--author', owner, '--name', name, '--url', url, '--desc', desc, '--long-desc', desc, '--source', GH + repo, '--release-page', GH + repo + '/releases']
        if ver(tag): args += ['--version', ver(tag)]
        if req: args += ['--requirements', req]
        if data: args += ['--data', GH + '%s/releases/download/%s/%s' % (repo, tag, data)]
        r = subprocess.run(args, capture_output=True, text=True)
        if r.returncode: raise Exception((r.stdout + r.stderr).strip().splitlines()[-1])
        ok.append(name); print(r.stdout.strip().splitlines()[-2], flush=True)
    except Exception as e:
        bad.append('%s: %s' % (name, e)); print('FEHLER', name, e, flush=True)
print('\n%d angelegt, %d Fehler' % (len(ok), len(bad))); print('\n'.join(bad))
