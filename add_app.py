import argparse, datetime, hashlib, json, os, struct, sys, tempfile, urllib.request, zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
TYPES = {'original': '1', 'port': '2', 'utility': '4', 'emulator': '5'}

def parse_sfo(buf):
    magic, ver, kt, dt, n = struct.unpack_from('<4sIIII', buf, 0)
    if magic != b'\0PSF':
        raise ValueError('not a param.sfo')
    out = {}
    for i in range(n):
        ko, fmt, dlen, dmax, do = struct.unpack_from('<HHIII', buf, 20 + i * 16)
        k = buf[kt + ko:buf.index(b'\0', kt + ko)].decode()
        v = buf[dt + do:dt + do + dlen]
        out[k] = v.rstrip(b'\0').decode('utf-8', 'replace') if fmt == 0x0204 else struct.unpack_from('<I', v)[0]
    return out

def load(name):
    with open(os.path.join(ROOT, name), 'rb') as f:
        return json.loads(f.read().decode('utf-8', 'replace'))

p = argparse.ArgumentParser()
p.add_argument('--url', required=True)
p.add_argument('--type', required=True, choices=sorted(TYPES))
p.add_argument('--author', required=True)
p.add_argument('--desc', required=True)
p.add_argument('--name')
p.add_argument('--version')
p.add_argument('--titleid')
p.add_argument('--long-desc', default='')
p.add_argument('--source', default='')
p.add_argument('--release-page', default='')
p.add_argument('--data', default='')
p.add_argument('--changelog', default='- First Release')
p.add_argument('--requirements', default='')
p.add_argument('--tags', default='')
p.add_argument('--psp', action='store_true')
a = p.parse_args()

target = 'psp_apps.json' if a.psp else 'apps.json'
apps = load(target)
belegt = []
for f in ('apps.json', 'psp_apps.json', 'preserved/plugins.json', 'preserved/tools.json'):
    belegt += load(f)
next_id = str(max(int(x['id']) for x in belegt) + 1)

print('downloading %s' % a.url)
tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.vpk')
req = urllib.request.Request(a.url, headers={'User-Agent': 'vitadbtoo'})
with urllib.request.urlopen(req, timeout=120) as r:
    while True:
        chunk = r.read(1 << 20)
        if not chunk:
            break
        tmp.write(chunk)
tmp.close()

blob = open(tmp.name, 'rb').read()
size = str(len(blob))
md5 = hashlib.md5(blob).hexdigest()
print('size %s bytes, md5 %s' % (size, md5))

with zipfile.ZipFile(tmp.name) as z:
    names = {n.lower(): n for n in z.namelist()}
    sfo_name = names.get('sce_sys/param.sfo')
    if not sfo_name:
        print('ERROR: sce_sys/param.sfo not found in vpk')
        sys.exit(1)
    sfo = parse_sfo(z.read(sfo_name))
    icon_name = names.get('sce_sys/icon0.png')
    icon_data = z.read(icon_name) if icon_name else None

print('param.sfo: TITLE=%s TITLE_ID=%s APP_VER=%s' % (
    sfo.get('TITLE'), sfo.get('TITLE_ID'), sfo.get('APP_VER')))

name = a.name or sfo.get('TITLE', '')
titleid = a.titleid or sfo.get('TITLE_ID', '')
version = a.version or ('v.' + str(sfo.get('APP_VER', '1.00')).lstrip('0') or 'v.1.0')

if not icon_data:
    print('ERROR: sce_sys/icon0.png not found in vpk')
    sys.exit(1)
icon_file = hashlib.sha256(icon_data).hexdigest() + '.png'
os.makedirs(os.path.join(ROOT, 'icons'), exist_ok=True)
open(os.path.join(ROOT, 'icons', icon_file), 'wb').write(icon_data)
print('icon saved as icons/%s' % icon_file)

if any(x['id'] == next_id for x in apps):
    print('ERROR: id %s already exists' % next_id)
    sys.exit(1)
if any(x['titleid'] == titleid for x in apps):
    print('WARNING: titleid %s already used by another app' % titleid)

entry = {
    'name': name, 'icon': icon_file, 'version': version, 'author': a.author,
    'type': TYPES[a.type], 'description': a.desc, 'id': next_id,
    'date': datetime.date.today().isoformat(), 'titleid': titleid,
    'screenshots': '', 'long_description': a.long_desc or a.desc,
    'downloads': '0', 'status': '0', 'source': a.source,
    'release_page': a.release_page, 'trailer': '', 'size': size,
    'data_size': '0', 'hash': md5, 'hash2': '', 'changelog': a.changelog,
    'requirements': a.requirements, 'trophies': '0', 'tags': a.tags,
    'score': '0', 'url': a.url, 'data': a.data,
}
if a.psp:
    del entry['score']

apps.insert(0, entry)
with open(os.path.join(ROOT, target), 'w') as f:
    json.dump(apps, f, indent=4, ensure_ascii=False)

os.unlink(tmp.name)
print('')
print('added "%s" as id %s to %s' % (name, next_id, target))
print('now run: python3 build_db.py')
