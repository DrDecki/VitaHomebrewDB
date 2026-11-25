import json, os, re, sys, urllib.request
import json as _j, os as _o, re as _r
_BL = _j.load(open(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), 'blocklist.json'), encoding='utf-8'))
def blocked(name, author, src=''):
    if any(b['match'].lower() in ((author or '') + ' ' + (src or '')).lower() for b in _BL['authors']): return True
    return any(_r.search(b['match'], name or '', _r.I) for b in _BL['names'])


ROOT = os.path.dirname(os.path.abspath(__file__))
UA = 'vitadbtoo'
ENDPOINTS = [
    ('Vita homebrews', 'list_hbs_by_titleid.php', 'apps.json'),
    ('Plugins', 'list_plugins_json.php', 'preserved/plugins.json'),
    ('PSP homebrews', 'list_psp_hbs_json.php', 'psp_apps.json'),
    ('PC tools', 'list_tools_json.php', 'preserved/tools.json'),
]

def load(n):
    with open(os.path.join(ROOT, n), 'rb') as f:
        return json.loads(f.read().decode('utf-8', 'replace'))

def post(ep):
    req = urllib.request.Request('https://www.rinnegatamante.eu/vitadb/' + ep,
                                 data=b'', headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode('utf-8', 'replace'))

def norm(s):
    return re.sub(r'[^a-z0-9]', '', (s or '').lower())

def vernum(s):
    return [int(x) for x in re.findall(r'\d+', s or '')[:4]]

# Bewusst entfernt: nur als Nightly verfuegbar, siehe REMOVED.md
NIGHTLY_ONLY = {'186', '405', '553', '815', '910', '1028', '1093', '1504'}

AL = json.load(open(os.path.join(ROOT, 'author_aliases.json'), encoding='utf-8'))
neu_alle, upd_alle = [], []
for label, ep, datei in ENDPOINTS:
    try:
        vd = post(ep)
    except Exception as e:
        print('%s: %s' % (label, type(e).__name__), file=sys.stderr)
        continue
    uns = load(datei)
    # Abgleich ueber normalisierte Namen, damit "Zenonia 3" und "Zenonia 3 Vita" zusammenfinden
    uns_norm, uns_repo, uns_tid = {}, {}, {}
    uns_id = {str(x.get('id')): x for x in uns}
    for a in uns:
        n = norm(a['name'])
        uns_norm[n] = a
        if a.get('titleid'):
            uns_tid.setdefault(a['titleid'].upper(), []).append(a)
        if n.endswith('vita'):
            uns_norm[n[:-4]] = a
        for feld in (a.get('source'), a.get('release_page'), a.get('url')):
            m = re.search(r'(github\.com|gitlab\.com)/([^/\s]+/[^/\s?#]+)', feld or '')
            if m:
                uns_repo[m.group(2).lower().removesuffix('.git')] = a

    rc = {}
    for a in vd:
        for feld in (a.get('source'), a.get('release_page')):
            m = re.search(r'(github\.com|gitlab\.com)/([^/\s]+/[^/\s?#]+)', feld or '')
            if m:
                k = m.group(2).lower().removesuffix('.git'); rc[k] = rc.get(k, 0) + 1
                break
    for a in vd:
        if blocked(a.get('name'), a.get('author'), a.get('source') or a.get('url')): continue
        n = norm(a['name'])
        repo = None
        for feld in (a.get('source'), a.get('release_page')):
            m = re.search(r'(github\.com|gitlab\.com)/([^/\s]+/[^/\s?#]+)', feld or '')
            if m:
                repo = m.group(2).lower().removesuffix('.git')
                break
        per_id = uns_id.get(str(a.get('id')))
        if per_id and not (norm(per_id['name']).startswith(n) or n.startswith(norm(per_id['name']))):
            per_id = None
        _a0 = re.split(r'\s*\\?&\s*|\s*,\s*', a.get('author') or '')[0].strip()
        au = norm(AL.get(_a0, _a0))[:4]
        tid = (a.get('titleid') or '').upper()
        # title IDs like ABCD12345 are shared by many homebrews: name or author must fit too
        c = uns_tid.get(tid, []) if tid else []
        treffer = next((x for x in c if norm(x['name']) in (n, n[:-4], n + 'vita')), None) \
            or next((x for x in c if norm(x.get('author'))[:4] == au), None) \
            or next((x for x in c if norm(x['name'])[:6] == n[:6]), None)
        # a repository only identifies the entry when no other VitaDB entry uses it
        if not treffer and repo and rc.get(repo) == 1:
            r = uns_repo.get(repo)
            if r:
                treffer = r
        if not treffer:
            treffer = per_id or uns_norm.get(n) or uns_norm.get(n + 'vita') or (uns_norm.get(n[:-4]) if n.endswith('vita') else None)
            # same name, different title ID and author: a different port
            if treffer and tid and treffer.get('titleid') and treffer['titleid'].upper() != tid and norm(treffer.get('author'))[:4] != au:
                treffer = None
        if not treffer:
            if str(a.get('id')) in NIGHTLY_ONLY:
                continue
            neu_alle.append((label, a))
            continue
        if treffer.get('_gemeldet'):
            continue
        vv, uv = vernum(a.get('version')), vernum(treffer.get('version'))
        # Datumsangaben als Version taugen nicht zum Vergleich
        if vv and vv[0] > 1900:
            continue
        # gleiche Ziffernfolge, nur anders geschrieben (1.0.1 gegen 1.01)
        if [x for x in vv if x] == [x for x in uv if x]:
            continue
        if vv and uv and vv > uv:
            treffer['_gemeldet'] = True
            upd_alle.append((label, a, treffer))

lines = []
if neu_alle:
    lines.append('## New on VitaDB\n')
    for label, a in sorted(neu_alle, key=lambda x: x[1].get('date') or ''):
        src = a.get('source') or a.get('release_page') or ''
        lines.append('- **%s** by %s *(%s, %s)*%s' % (
            a['name'], a.get('author') or '?', label, a.get('date') or '?',
            '  —  %s' % src if src else '  —  no repository'))
    lines.append('')
if upd_alle:
    lines.append('## Newer version on VitaDB\n')
    for label, a, t in sorted(upd_alle, key=lambda x: x[1].get('date') or ''):
        lines.append('- **%s** %s -> %s *(%s)*' % (t['name'], t.get('version'), a.get('version'), label))
    lines.append('')

if lines:
    lines.append('Nothing here has been checked. VitaDB links are not used directly:')
    lines.append('entries are added pointing at their own repository where one exists.')
    open(os.path.join(ROOT, 'vitadb_issue.md'), 'w', encoding='utf-8').write('\n'.join(lines))
    print('%d neu, %d mit neuerer Version' % (len(neu_alle), len(upd_alle)))
else:
    print('nichts Neues bei VitaDB')
