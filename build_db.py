#!/usr/bin/env python3
import json, os, sys, zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))

def load(name):
    with open(os.path.join(ROOT, name), 'rb') as f:
        return json.loads(f.read().decode('utf-8', 'replace'))

apps = load('apps.json')

minimal = []
for a in apps:
    minimal.append({
        'id': a.get('id', ''),
        'titleid': a.get('titleid', ''),
        'hash': a.get('hash', ''),
        'hash2': a.get('hash2', ''),
    })

with open(os.path.join(ROOT, 'minimal.json'), 'w') as f:
    json.dump(minimal, f, separators=(',', ':'))
print('minimal.json: %d entries' % len(minimal))

icon_dir = os.path.join(ROOT, 'icons')
icons = sorted(n for n in os.listdir(icon_dir) if n.endswith('.png'))

zip_path = os.path.join(ROOT, 'icons.zip')
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for n in icons:
        z.write(os.path.join(icon_dir, n), n)
print('icons.zip: %d icons, %.1f MB' % (len(icons), os.path.getsize(zip_path) / 1048576.0))

needed = set()
for db in ('apps.json', 'psp_apps.json'):
    for a in load(db):
        if a.get('icon'):
            needed.add(a['icon'])
missing = needed - set(icons)
print('icon coverage: %d/%d needed present' % (len(needed) - len(missing), len(needed)))
if missing:
    print('MISSING: %s' % sorted(missing)[:5])
    sys.exit(1)


def _ensure_added():
    import datetime, json, os
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    for f in ('apps.json', 'psp_apps.json', 'preserved/plugins.json', 'preserved/tools.json'):
        d = json.load(open(f, encoding='utf-8'))
        fehlt = [a for a in d if not a.get('added')]
        if fehlt:
            for a in fehlt: a['added'] = now
            json.dump(d, open(f, 'w', encoding='utf-8'), indent=4, ensure_ascii=False)
            print('added nachgetragen: %d in %s' % (len(fehlt), f))

_ensure_added()
