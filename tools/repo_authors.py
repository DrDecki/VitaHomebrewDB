# Sets the author of each entry to the owner of its repository.
# Dry run by default; --write applies the single-author changes.
import json, re, os, sys, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
FS = ('apps.json', 'psp_apps.json', 'preserved/plugins.json', 'preserved/tools.json')
RX = re.compile(r'https?://(?:www\.)?(github\.com|gitlab\.com|gitee\.com|codeberg\.org)/([^/\s?#]+)/([^/\s?#]+)', re.I)
def repo(a):
    for k in ('source', 'release_page', 'url'):
        m = RX.search(a.get(k) or '')
        if m and not (m.group(2).lower() == 'drdecki' and m.group(3).lower() == 'vitahomebrewdb'):
            return m.group(1).lower(), m.group(2), m.group(3).removesuffix('.git')
data = {f: json.load(open(f, encoding='utf-8')) for f in FS}
gh = sorted({(r[1], r[2]) for f in FS for a in data[f] for r in [repo(a)] if r and r[0] == 'github.com'})
owner = {}
for i in range(0, len(gh), 50):
    part = gh[i:i + 50]
    q = 'query{' + ''.join('r%d:repository(owner:%s,name:%s){owner{__typename login}}' % (j, json.dumps(o), json.dumps(n)) for j, (o, n) in enumerate(part)) + '}'
    r = subprocess.run(['gh', 'api', 'graphql', '-f', 'query=' + q], capture_output=True, text=True)
    d = json.loads(r.stdout or '{}').get('data') or {}
    for j, k in enumerate(part):
        g = d.get('r%d' % j)
        if g: owner[(k[0].lower(), k[1].lower())] = (g['owner']['login'], g['owner']['__typename'])
    print('%d/%d Repos abgefragt' % (min(i + 50, len(gh)), len(gh)), file=sys.stderr)
single, multi, orgs, missing = [], [], [], []
for f in FS:
    for a in data[f]:
        r = repo(a)
        if not r: continue
        if r[0] == 'github.com':
            o = owner.get((r[1].lower(), r[2].lower()))
            if not o: missing.append((f, a['id'], a['name'], r[1] + '/' + r[2])); continue
            login, typ = o
        else:
            login, typ = r[1], 'User'
        old = a.get('author') or ''
        if typ == 'Organization': orgs.append((f, a['id'], a['name'], old, login)); continue
        if old == login: continue
        if re.search(r'\\?&|\sand\s|,|/', old): multi.append((f, a['id'], a['name'], old, login))
        else: single.append((f, a['id'], a['name'], old, login))
out = ['## Ein Autor: %d Aenderungen\n' % len(single)]
for f, i, n, old, new in sorted(single, key=lambda x: (x[4].lower(), x[3])): out.append('%s | %-5s %-40s %s -> %s' % (f[:4], i, n[:40], old, new))
out.append('\n## Mehrere Autoren: %d (einzeln anpassen)\n' % len(multi))
for f, i, n, old, new in sorted(multi, key=lambda x: x[4].lower()): out.append('%s | %-5s %-40s %s   [Repo: %s]' % (f[:4], i, n[:40], old, new))
out.append('\n## Organisationen, bleiben: %d\n' % len(orgs))
for f, i, n, old, new in orgs: out.append('%s | %-5s %-40s %s   [Org: %s]' % (f[:4], i, n[:40], old, new))
out.append('\n## Repo nicht gefunden (geloescht oder privat): %d\n' % len(missing))
for f, i, n, r in missing: out.append('%s | %-5s %-40s %s' % (f[:4], i, n[:40], r))
open('/tmp/authors.txt', 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print('%d einzeln, %d mehrere, %d Orgs, %d nicht gefunden' % (len(single), len(multi), len(orgs), len(missing)))
if '--write' in sys.argv:
    ch = {(f, i): new for f, i, n, old, new in single}
    for f in FS:
        for a in data[f]:
            if (f, a['id']) in ch: a['author'] = ch[(f, a['id'])]
        json.dump(data[f], open(f, 'w', encoding='utf-8'), indent=4, ensure_ascii=False)
    print('geschrieben')
