import json, os, re, sys, time, urllib.request
from internetarchive import upload

ROOT = os.path.dirname(os.path.abspath(__file__))
ITEM = 'vitadbtoo-mirror'
TMP = '/tmp/ia_stage'
os.makedirs(TMP, exist_ok=True)

MODE = sys.argv[1] if len(sys.argv) > 1 else 'rinne'
LIMIT = int(sys.argv[2]) * 1048576 if len(sys.argv) > 2 else 10 ** 12

def load(n):
    with open(os.path.join(ROOT, n), 'rb') as f:
        return json.loads(f.read().decode('utf-8', 'replace'))

d = load('apps.json')
if MODE == 'rinne':
    import json as _j
    _ok = {e['id'] for e in _j.load(open('/tmp/tid.json'))}
    todo = [a for a in d if 'get_hb_url' in a['url'] and a['id'] in _ok]
else:
    todo = [a for a in d if 'web.archive.org' in a['url']]
todo = [a for a in todo if int(a.get('size') or 0) < LIMIT]
todo.sort(key=lambda x: int(x.get('size') or 0))

print('%s: %d Dateien, %.2f GB' % (MODE, len(todo), sum(int(a['size'] or 0) for a in todo) / 1073741824.0))
print()

done_file = os.path.join(ROOT, 'mirror_done.json')
done = json.load(open(done_file)) if os.path.exists(done_file) else {}

ok = fail = 0
for i, a in enumerate(todo, 1):
    if a['id'] in done:
        a['url'] = done[a['id']]
        continue
    try:
        req = urllib.request.Request(a['url'], headers={'User-Agent': 'vitadbtoo-mirror'})
        with urllib.request.urlopen(req, timeout=300) as r:
            real = r.url
            data = r.read()
        base = re.sub(r'[^A-Za-z0-9._-]', '_', real.split('/')[-1].split('?')[0])
        if not base or '.' not in base:
            base = a['id'] + '.vpk'
        name = a['id'] + '-' + base
        path = os.path.join(TMP, name)
        open(path, 'wb').write(data)
        upload(ITEM, files={name: path}, metadata={
            'title': 'VitaHomebrewDB mirror',
            'mediatype': 'software',
            'collection': 'opensource',
            'subject': 'psvita; homebrew; vitadb',
            'description': 'Mirror of PSVITA homebrew files cataloged by VitaHomebrewDB.'},
            verbose=False, retries=3)
        url = 'https://archive.org/download/%s/%s' % (ITEM, name)
        a['url'] = url
        a['size'] = str(len(data))
        done[a['id']] = url
        os.unlink(path)
        ok += 1
        print('  %4d/%d  %-30s %7.1f MB' % (i, len(todo), a['name'][:30], len(data) / 1048576.0), flush=True)
    except Exception as e:
        fail += 1
        print('  %4d/%d  FEHLER %-24s %s' % (i, len(todo), a['name'][:24], str(e)[:50]), flush=True)
    if i % 10 == 0:
        json.dump(done, open(done_file, 'w'), indent=1)
        with open(os.path.join(ROOT, 'apps.json'), 'w') as f:
            json.dump(d, f, indent=4, ensure_ascii=False)
    time.sleep(0.5)

json.dump(done, open(done_file, 'w'), indent=1)
with open(os.path.join(ROOT, 'apps.json'), 'w') as f:
    json.dump(d, f, indent=4, ensure_ascii=False)
print()
print('gespiegelt: %d, fehlgeschlagen: %d' % (ok, fail))
