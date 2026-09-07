import difflib, hashlib, json, os, re, sys, time, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.abspath(__file__))
TOKEN = os.environ.get('GH_TOKEN', '').strip()
MAX_MB = int(os.environ.get('MAX_MB', '150'))

FOREIGN = ('3ds', 'switch', 'wiiu', 'wii', 'gamecube', 'gc', 'android', 'linux',
           'macos', 'mac', 'windows', 'win32', 'win64', 'win', 'x64', 'x86',
           'ps4', 'ps3', 'nx', 'steam', 'epic', 'funkey', 'rg35xx', 'miyoo', 'nspire',
           'dreamcast', 'xbox', 'ios', 'web', 'wasm', 'dsi', 'gba', 'n64')
EXTRA = ('data', 'patch', 'gamefiles', 'assets', 'source', 'symbols', 'debug')

def load(n):
    with open(os.path.join(ROOT, n), 'rb') as f:
        return json.loads(f.read().decode('utf-8', 'replace'))

def api(url):
    h = {'User-Agent': 'vitadbtoo', 'Accept': 'application/vnd.github+json'}
    if TOKEN:
        h['Authorization'] = 'Bearer ' + TOKEN
    for _ in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(10)
        except Exception:
            time.sleep(5)
    return None

def repo_of(a):
    for field in ('release_page', 'source'):
        m = re.match(r'https?://github\.com/([^/]+)/([^/#?]+)', a.get(field) or '')
        if m:
            return '%s/%s' % (m.group(1), m.group(2).replace('.git', ''))
    return None

def slug(s):
    s = re.sub(r'[_\-]+', ' ', s.lower())
    s = re.sub(r'\bv?\d+[._]\d[\d._]*\b', '', s)
    s = re.sub(r'\b(vita|psvita|ps vita|port|release|final|nightly)\b', '', s)
    return re.sub(r'[^a-z0-9]', '', s)

def vernum(s):
    m = re.findall(r'\d+', s or '')
    return [int(x) for x in m[:4]]

def newer(new, old):
    a, b = vernum(new), vernum(old)
    if not a or not b:
        return True
    return a > b

def usable(name, want_ext, entry_slug):
    low = name.lower()
    if not low.endswith(want_ext):
        return 0
    stem = re.sub(r'\.[a-z0-9]+$', '', low)
    for bad in FOREIGN:
        if bad in stem:
            return 0
    score = difflib.SequenceMatcher(None, entry_slug, slug(stem)).ratio()
    if any(k in stem for k in EXTRA):
        score -= 0.35
    if low.endswith('.vpk'):
        score += 0.15
    return score

changes, skipped = [], []
for fname in ('apps.json', 'psp_apps.json', 'preserved/plugins.json', 'preserved/tools.json'):
    path = os.path.join(ROOT, fname)
    d = load(fname)
    dirty = False
    is_psp = fname == 'psp_apps.json'
    for a in d:
        if 'github.com' not in a.get('url', ''):
            continue
        key = repo_of(a)
        if not key:
            continue
        cur = a['url'].rsplit('/', 1)[-1]
        if 'DrDecki/VitaHomebrewDB' in a['url']:
            cur = re.sub(r'^\d+-', '', cur)
        want_ext = ('.vpk', '.zip', '.7z', '.rar') if not fname.startswith('preserved/plugins') else ('.suprx', '.skprx', '.zip')
        rel = api('https://api.github.com/repos/%s/releases?per_page=5' % key)
        if not rel:
            continue
        es = slug(a['name'])
        best, best_score, best_tag, best_date = None, 0.0, None, ''
        for r in rel:
            if r.get('draft') or r.get('prerelease'):
                continue
            for x in r.get('assets', []):
                sc = usable(x['name'], want_ext, es)
                if sc > best_score:
                    best, best_score, best_tag = x, sc, r['tag_name']
                    best_date = r.get('published_at', '')
            if best:
                break
        if not best or best['name'] == cur:
            continue
        cur_score = usable(cur, want_ext, es)
        if not newer(best_tag or best['name'], a.get('version', '')):
            skipped.append('%s: %s looks older than %s, keeping it' % (a['name'], best_tag or best['name'], a.get('version')))
            continue
        if best_date and a.get('date') and best_date[:10] <= a['date']:
            skipped.append('%s: %s is from %s, the entry already has %s' % (a['name'], best_tag, best_date[:10], a['date']))
            continue
        cur_stem = re.sub(r'\d', '', slug(re.sub(r'\.[a-z0-9]+$', '', cur.lower())))
        new_stem = re.sub(r'\d', '', slug(re.sub(r'\.[a-z0-9]+$', '', best['name'].lower())))
        if cur_stem and new_stem and cur_stem not in new_stem and new_stem not in cur_stem:
            skipped.append('%s: %s is a different file, not a newer %s' % (a['name'], best['name'], cur))
            continue
        if cur.lower().endswith('.vpk') and not best['name'].lower().endswith('.vpk'):
            skipped.append('%s: %s is an archive, the entry links a VPK' % (a['name'], best['name']))
            continue
        if 'v.' + (best_tag or '').lstrip('vV.') == a.get('version', ''):
            skipped.append('%s: %s is the same version, nothing to update' % (a['name'], best_tag))
            continue
        if best_score < 0.55 or best_score < cur_score:
            skipped.append('%s: best candidate %s scored %.2f, keeping %s' % (a['name'], best['name'], best_score, cur))
            continue
        gross = best['size'] > MAX_MB * 1048576
        blob = None
        if not gross:
            try:
                req = urllib.request.Request(best['browser_download_url'], headers={'User-Agent': 'vitadbtoo'})
                with urllib.request.urlopen(req, timeout=300) as r:
                    blob = r.read()
            except Exception as e:
                skipped.append('%s: download failed, %s' % (a['name'], str(e)[:40]))
                continue
        old_v, old_f = a.get('version', '?'), cur
        a['url'] = best['browser_download_url']
        a['size'] = str(len(blob) if blob is not None else best['size'])
        a['hash'] = hashlib.md5(blob).hexdigest() if blob is not None else ''
        if best_tag:
            a['version'] = 'v.' + best_tag.lstrip('vV.')
        changes.append('- **%s** %s -> %s  \n  `%s` -> `%s` (%.1f MB, match %.2f)' % (
            a['name'], old_v, a.get('version'), old_f, best['name'], best['size'] / 1048576.0, best_score))
        dirty = True
        time.sleep(0.5)
    if dirty:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(d, f, indent=4, ensure_ascii=False)

body = ['## Updates found\n']
body += changes if changes else ['None.\n']
if skipped:
    body.append('\n<details><summary>%d candidates skipped</summary>\n' % len(skipped))
    body += ['- ' + s for s in skipped]
    body.append('</details>\n')
open(os.path.join(ROOT, 'update_report.md'), 'w', encoding='utf-8').write('\n'.join(body))

print('\n'.join(changes) if changes else 'no updates')
print('---')
print('%d updates, %d skipped' % (len(changes), len(skipped)))
if os.environ.get('GITHUB_OUTPUT'):
    with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
        f.write('count=%d\n' % len(changes))
