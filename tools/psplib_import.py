import datetime, hashlib, json, os, re, sys, time, urllib.parse, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = '/tmp/psplib_meta'; os.makedirs(CACHE, exist_ok=True)
WRITE = '--write' in sys.argv
UA = {'User-Agent': 'VitaHomebrewDB'}
def get(u, t=60):
    for i in range(4):
        try: return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=t).read()
        except Exception:
            time.sleep(3 + i * 5)
    return None
norm = lambda s: re.sub(r'[^a-z0-9]', '', (s if isinstance(s, str) else ' '.join(s or [])).lower())
txt = lambda s: (s if isinstance(s, str) else ' '.join(s or [])).strip()
docs = json.load(open('/tmp/psplib.json'))
psp = json.load(open(os.path.join(ROOT, 'psp_apps.json'), encoding='utf-8'))
seen = {norm(a['name']) for a in psp}
tpl = {k: '' for k in psp[0]}
alle = psp + [x for f in ('apps.json', 'preserved/plugins.json', 'preserved/tools.json') for x in json.load(open(os.path.join(ROOT, f), encoding='utf-8'))]
nid = max(int(x['id']) for x in alle)
neu, ohne_zip, n = [], 0, 0
for x in docs:
    n += 1
    if n % 200 == 0: print('  %d / %d' % (n, len(docs)), flush=True)
    key = norm(x.get('title'))
    if not key or key in seen: continue
    seen.add(key)
    cp = os.path.join(CACHE, re.sub(r'[^A-Za-z0-9._-]', '_', x['identifier']) + '.json')
    if os.path.exists(cp): m = json.load(open(cp))
    else:
        raw = get('https://archive.org/metadata/' + urllib.parse.quote(x['identifier']))
        if not raw: continue
        m = json.loads(raw); json.dump(m, open(cp, 'w')); time.sleep(0.3)
    orig = [f for f in m.get('files', []) if f.get('source') == 'original']
    zips = [f for f in orig if f['name'].lower().endswith('.zip') and not f['name'].startswith('Old Versions/')]
    if not zips: ohne_zip += 1; continue
    z = max(zips, key=lambda f: (('1000' not in f['name']), int(f.get('size', 0))))
    imgs = [f for f in orig if f['name'].lower().endswith(('.png', '.jpg')) and f['name'] != '__ia_thumb.jpg' and int(f.get('size', 0)) > 3000]
    tid = next((mm.group(1) for f in orig for mm in [re.match(r'^([A-Z]{4}\d{5})_', f['name'])] if mm and mm.group(1) != 'ULES99999'), '')
    desc = txt(x.get('description')); low = desc.lower()
    typ = '5' if 'emulator' in low else '2' if re.search(r'\bport\b|fan-made|remake', low) else '4' if re.match(r'(app|utility|tool|plugin)', low) else '1'
    ver = re.search(r'v?(\d+(?:\.\d+)+[a-z]?)', z['name'], re.I)
    nid += 1
    e = dict(tpl); e.update(id=str(nid), name=txt(x.get('title')), author=txt(x.get('creator')) or 'Unknown',
        version='v.' + ver.group(1) if ver else 'v.1.0', type=typ, titleid=tid, description=desc, changelog='',
        url='https://archive.org/download/%s/%s' % (x['identifier'], urllib.parse.quote(z['name'])),
        size=str(z.get('size', '0')), hash=z.get('md5', ''), date=(txt(x.get('date')) or '')[:10],
        release_page='https://archive.org/details/' + x['identifier'], downloads='0')
    e['_img'] = ['https://archive.org/download/%s/%s' % (x['identifier'], urllib.parse.quote(f['name'])) for f in imgs[:3]]
    neu.append(e)
print('\n  %d neue Eintraege, %d ohne ZIP uebersprungen' % (len(neu), ohne_zip))
import collections
print('  Kategorien:', dict(collections.Counter(e['type'] for e in neu)))
print('  mit Title-ID: %d, mit Screenshot: %d' % (sum(1 for e in neu if e['titleid']), sum(1 for e in neu if e['_img'])))
for e in neu[:4]: print('  %-5s %-26s %-18s %-10s %s' % (e['id'], e['name'][:26], e['author'][:18], e['version'][:10], e['url'][-40:]))
if not WRITE: print('\n  Probelauf, nichts geschrieben'); sys.exit()
for i, e in enumerate(neu):
    shots = []
    for u in e.pop('_img'):
        b = get(u)
        if b:
            h = hashlib.sha256(b).hexdigest(); open(os.path.join(ROOT, 'screenshots', h + '.png'), 'wb').write(b)
            shots.append('screenshots/%s.png' % h)
    e['screenshots'] = ';'.join(shots)
    if i % 200 == 0: print('  Screenshots %d / %d' % (i, len(neu)), flush=True)
psp += neu
json.dump(psp, open(os.path.join(ROOT, 'psp_apps.json'), 'w', encoding='utf-8'), indent=4, ensure_ascii=False)
print('  %d Eintraege in psp_apps.json geschrieben' % len(neu))
