import hashlib, json, os, re, sys, time, urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
dry = '--write' not in sys.argv

ZIEL = {
 'ShowInfo Lite': 'preserved/plugins.json', 'uac-pstv-host': 'preserved/plugins.json',
}
NAMEN = ["ShowInfo Lite","Please, Don't Touch Anything","OpenXcom","vitaQuakeII","devilutionX",
         "Zenonia 2","Switchfin","Save Keeper","OpenMW Vita","uac-pstv-host","Save Sync",
         "WoozyLLM","VitaDB Downloader","OpenNow Vita","Minecraft: Story Mode",
         "CTR: High Octane","BattleShip","dRally Vita","VitaMediaDeck","Prince of Persia Classic","Amnesia: The Dark Descent"]

def load(n):
    with open(os.path.join(ROOT, n), 'rb') as f:
        return json.loads(f.read().decode('utf-8', 'replace'))

import subprocess

def api(u):
    # ueber gh, damit das Kontingent bei 5000/h statt 60/h liegt
    pfad = u.replace('https://api.github.com/', '')
    r = subprocess.run(['gh', 'api', pfad], capture_output=True, text=True, timeout=90)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or '').strip()[:60])
    return json.loads(r.stdout)

def slug(s):
    return re.sub(r'[^a-z0-9]', '', (s or '').lower())

daten = {f: load(f) for f in ('apps.json', 'preserved/plugins.json')}
for name in NAMEN:
    datei = ZIEL.get(name, 'apps.json')
    a = next((x for x in daten[datei] if x['name'] == name), None)
    if not a:
        print('  %-26s nicht gefunden' % name[:26]); continue
    m = re.search(r'github\.com/([^/\s]+/[^/\s?#]+)', (a.get('source') or a.get('release_page') or ''))
    if not m:
        print('  %-26s kein Repo' % name[:26]); continue
    repo = m.group(1).rstrip('.git')
    try:
        rels = api('https://api.github.com/repos/%s/releases?per_page=5' % repo)
    except Exception as e:
        print('  %-26s API %s' % (name[:26], getattr(e, 'code', '?'))); continue
    if not isinstance(rels, list) or not rels:
        print('  %-26s keine Releases' % name[:26]); continue
    cur_ext = os.path.splitext(a['url'].split('?')[0])[1].lower()
    SCHLECHT = ('logging', 'debug', 'partial', 'test', 'beta')
    cur_stem = re.sub(r'\d', '', slug(os.path.splitext(a['url'].rsplit('/', 1)[-1])[0]))
    best = None
    for r in rels:
        if r.get('prerelease'):
            continue
        kand = [x for x in r.get('assets', [])
                if os.path.splitext(x['name'])[1].lower() == cur_ext
                and not any(w in x['name'].lower() for w in SCHLECHT)]
        # Dateiname muss zum bisherigen passen, sonst ist es ein anderes Programm
        kand = [x for x in kand
                if not cur_stem or cur_stem in re.sub(r'\d', '', slug(os.path.splitext(x['name'])[0]))
                or re.sub(r'\d', '', slug(os.path.splitext(x['name'])[0])) in cur_stem]
        if kand:
            best = (r, kand[0]); break
    if not best:
        print('  %-26s kein passendes Asset' % name[:26]); continue
    r, x = best
    tag = r['tag_name']
    neu_ver = 'v.' + tag.lstrip('vV.')
    if neu_ver == a.get('version'):
        print('  %-26s schon aktuell (%s)' % (name[:26], a.get('version'))); continue
    print('  %-26s %-14s -> %-14s %s' % (name[:26], a.get('version'), neu_ver, x['name'][:28]))
    if not dry:
        blob = urllib.request.urlopen(urllib.request.Request(x['browser_download_url'],
               headers={'User-Agent': 'vitadbtoo'}), timeout=600).read()
        a['version'] = neu_ver
        a['url'] = x['browser_download_url']
        a['size'] = str(len(blob))
        a['hash'] = hashlib.md5(blob).hexdigest()
    time.sleep(1)

if not dry:
    for f, d in daten.items():
        json.dump(d, open(os.path.join(ROOT, f), 'w', encoding='utf-8'), indent=4, ensure_ascii=False)
    print()
    print('geschrieben')
else:
    print()
    print('Probelauf, nichts geaendert')
