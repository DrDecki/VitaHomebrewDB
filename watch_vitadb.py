import json, os, re, sys, urllib.request

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

neu_alle, upd_alle = [], []
for label, ep, datei in ENDPOINTS:
    try:
        vd = post(ep)
    except Exception as e:
        print('%s: %s' % (label, type(e).__name__), file=sys.stderr)
        continue
    uns = load(datei)
    # Abgleich ueber normalisierte Namen, damit "Zenonia 3" und "Zenonia 3 Vita" zusammenfinden
    uns_norm, uns_repo = {}, {}
    for a in uns:
        n = norm(a['name'])
        uns_norm[n] = a
        if n.endswith('vita'):
            uns_norm[n[:-4]] = a
        for feld in (a.get('source'), a.get('release_page'), a.get('url')):
            m = re.search(r'(github\.com|gitlab\.com)/([^/\s]+/[^/\s?#]+)', feld or '')
            if m:
                uns_repo[m.group(2).lower().rstrip('.git')] = a

    for a in vd:
        n = norm(a['name'])
        repo = None
        for feld in (a.get('source'), a.get('release_page')):
            m = re.search(r'(github\.com|gitlab\.com)/([^/\s]+/[^/\s?#]+)', feld or '')
            if m:
                repo = m.group(2).lower().rstrip('.git')
                break
        treffer = (uns_repo.get(repo) if repo else None) or uns_norm.get(n) or uns_norm.get(n + 'vita') or (uns_norm.get(n[:-4]) if n.endswith('vita') else None)
        if not treffer:
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
