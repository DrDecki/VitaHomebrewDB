import json, os, re, zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
ORIG = os.path.expanduser('~/Downloads/VitaDB.zip')

def load(n):
    with open(os.path.join(ROOT, n), 'rb') as f:
        return json.loads(f.read().decode('utf-8', 'replace'))

def live(a):
    return 'get_hb_url' not in a.get('url', '')

cats = [('PSVITA homebrews', 'apps.json'), ('Plugins', 'preserved/plugins.json'),
        ('PSP homebrews', 'psp_apps.json'), ('PC tools', 'preserved/tools.json')]

LAST_VITADB_ID = 1449

rows, tot, ok = [], 0, 0
added, added_ok = 0, 0
for label, f in cats:
    d = load(f)
    kept = [a for a in d if int(a['id']) <= LAST_VITADB_ID]
    new_ones = [a for a in d if int(a['id']) > LAST_VITADB_ID]
    n = sum(1 for a in kept if live(a))
    rows.append((label, len(kept), n))
    tot += len(kept)
    ok += n
    added += len(new_ones)
    added_ok += sum(1 for a in new_ones if live(a))

icons = len([x for x in os.listdir(os.path.join(ROOT, 'icons')) if x.endswith('.png')])
need = set()
for f in ('apps.json', 'psp_apps.json'):
    for a in load(f):
        if a.get('icon'):
            need.add(a['icon'])

_ss_ref = set()
for _a in load('apps.json'):
    if int(_a['id']) <= LAST_VITADB_ID:
        _ss_ref |= set(re.findall(r'[0-9a-f]{64}\.png', _a.get('screenshots') or ''))
ss_have = len(_ss_ref)
_tr_orig = set()
if os.path.exists(os.path.join(ROOT, 'totals.json')):
    _tr_orig = set(load('totals.json').get('trailer_ids') or [])
if not _tr_orig and os.path.exists(ORIG):
    with zipfile.ZipFile(ORIG) as _z:
        _tr_orig = {a['id'] for a in json.loads(_z.read('VitaDB/apps.json').decode('utf-8', 'replace')) if a.get('trailer')}
if _tr_orig:
    tr_have = sum(1 for a in load('apps.json') if a.get('trailer') and a['id'] in _tr_orig)
else:
    tr_have = sum(1 for a in load('apps.json') if a.get('trailer') and int(a['id']) <= LAST_VITADB_ID)
unused_tr = len([x for x in os.listdir(os.path.join(ROOT, 'videos'))
               if x.endswith('.mp4')]) if os.path.isdir(os.path.join(ROOT, 'videos')) else 0

ss_total = tr_total = 0
if os.path.exists(ORIG):
    z = zipfile.ZipFile(ORIG)
    orig = json.loads(z.read('VitaDB/apps.json').decode('utf-8', 'replace'))
    ss_total = len(set(m for a in orig for m in re.findall(r'[0-9a-f]{64}\.png', a.get('screenshots') or '')))
    tr_total = sum(1 for a in orig if a.get('trailer'))

if os.path.exists(os.path.join(ROOT, 'totals.json')):
    _t = load('totals.json')
    ss_total = _t.get('screenshots_total', ss_total)
    tr_total = _t.get('trailers_total', tr_total)
data_missing = sum(1 for a in load('apps.json') if a.get('data') and 'rinnegatamante' in a['data'])
missing_dl = tot - ok
unmatched = 0
if os.path.exists('/tmp/cdx_len.txt'):
    used = set()
    for a in load('apps.json'):
        m = re.search(r'files/vitadb/(.+)$', a['url'])
        if m: used.add(m.group(1))
    for line in open('/tmp/cdx_len.txt'):
        q = line.split()
        if len(q) >= 3 and q[2] == '200':
            m = re.search(r'files/vitadb/(.+)$', q[0])
            if m and m.group(1) not in used: unmatched += 1

out = ['<!-- STATS -->\n']
out.append('| | Entries | With a working download |\n| --- | ---: | ---: |\n')
for label, n, k in rows:
    out.append('| %s | %d | %d |\n' % (label, n, k))
out.append('| **Total** | **%d** | **%d (%d%%)** |\n\n' % (tot, ok, int(100.0 * ok / tot)))
if added:
    out.append('The table above counts the catalogue as it stood on 2026-07-31. Another %d entries\n' % added)
    out.append('have been added since, from VitaDB, from the authors themselves and from the wider\n')
    out.append('scene; those are listed separately in [ADDED.md](ADDED.md).\n\n')
_bytes = 0
for _f in ('apps.json', 'psp_apps.json', 'preserved/plugins.json', 'preserved/tools.json'):
    for _a in load(_f):
        _bytes += int(_a.get('size') or 0) + int(_a.get('data_size') or 0)
out.append('Everything the catalogue points at comes to **%.1f GB**.\n\n' % (_bytes / 1073741824.0))
out.append('| Asset | Recovered |\n| --- | ---: |\n')
out.append('| Metadata | 100%% (%d entries) |\n' % tot)
out.append('| Icons | %.0f%% (%d) |\n' % (100.0 * len(need & set(os.listdir(os.path.join(ROOT, 'icons')))) / max(len(need), 1), icons))
if ss_total:
    out.append('| Screenshots | %.0f%% (%d of %d) |\n' % (100.0 * ss_have / ss_total, ss_have, ss_total))
if tr_total:
    out.append('| Trailers | %.0f%% (%d of %d) |\n' % (100.0 * tr_have / tr_total, tr_have, tr_total))
data_total = 0
if os.path.exists(os.path.join(ROOT, 'totals.json')):
    data_total = load('totals.json').get('data_total', 0)
elif os.path.exists(ORIG):
    data_total = sum(1 for a in orig if a.get('data'))
if data_total:
    out.append('| Data files | %.0f%% (%d of %d) |\n' % (100.0 * (data_total - data_missing) / data_total, data_total - data_missing, data_total))
else:
    out.append('| Data files | %d missing |\n' % data_missing)
_tt = load('totals.json').get('trophy_sets_total', 0) if os.path.exists(os.path.join(ROOT, 'totals.json')) else 0
_th = len(load('trophies/index.json')) if os.path.exists(os.path.join(ROOT, 'trophies', 'index.json')) else 0
if _tt:
    out.append('| In-game trophies | %.0f%% (%d of %d sets) |\n' % (100.0 * _th / _tt, _th, _tt))
else:
    out.append('| In-game trophies | %d sets |\n' % _th)
if missing_dl or data_missing:
    out.append('\n### Help wanted\n\n')
    out.append('**%d downloads and %d data files are still missing.** ' % (missing_dl, data_missing))
    out.append('They are listed with author, version and file size in [WANTED.md](WANTED.md)')
    if unmatched:
        out.append(', together with %d archived files from the old webhost that nobody has ' % unmatched)
        out.append('been able to identify yet')
    out.append('.\n\n')
    out.append('This does not need programming. It needs people who recognise a homebrew by its ')
    out.append('filename, or who still have the file lying on an old memory card. If you can match ')
    out.append('even one entry, open an issue: every link restored is an application that stops ')
    out.append('being lost.\n')
else:
    out.append('\nNothing is missing at the moment. [WANTED.md](WANTED.md) fills back up on its own\n')
    out.append('when something breaks or a new entry arrives without a working link.\n')
out.append('<!-- /STATS -->')

readme = os.path.join(ROOT, 'README.md')
s = open(readme, encoding='utf-8').read()
block = ''.join(out)
if '<!-- STATS -->' in s:
    s = re.sub(r'<!-- STATS -->.*?<!-- /STATS -->', block, s, flags=re.S)
else:
    s = s.replace('## Files', block + '\n\n## Files', 1)
open(readme, 'w', encoding='utf-8').write(s)
print('README aktualisiert: %d von %d installierbar (%d%%)' % (ok, tot, int(100.0 * ok / tot)))
