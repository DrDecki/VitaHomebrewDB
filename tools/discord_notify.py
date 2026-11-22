import json, os, subprocess, time, urllib.request
HOOK = os.environ.get('DISCORD_WEBHOOK'); BEFORE = os.environ.get('BEFORE', ''); AFTER = os.environ.get('AFTER', 'HEAD')
FILES = {'apps.json': 'PS Vita', 'psp_apps.json': 'PSP', 'preserved/plugins.json': 'Plugin', 'preserved/tools.json': 'PC tool'}
ICON = 'https://raw.githubusercontent.com/DrDecki/VitaHomebrewDB/main/icons/'
if not HOOK: print('kein Webhook gesetzt'); raise SystemExit
if not BEFORE or set(BEFORE) == {'0'}: BEFORE = AFTER + '~1'
def load(rev, f):
    r = subprocess.run(['git', 'show', '%s:%s' % (rev, f)], capture_output=True)
    try: return {a['id']: a for a in json.loads(r.stdout)} if r.returncode == 0 else {}
    except Exception: return {}
lines = []
for f, kind in FILES.items():
    old, new = load(BEFORE, f), load(AFTER, f)
    for i, a in new.items():
        o = old.get(i); link = 'https://drdecki.github.io/#app-%s' % i
        tail = ' <%s>' % link if link else ''
        if o is None:
            lines.append((True, '**%s** %s by %s was added to VitaHomebrewDB (%s).%s' % (a['name'], a.get('version') or '', a.get('author') or '?', kind, tail)))
        elif (o.get('version') or '') != (a.get('version') or ''):
            lines.append((False, '**%s** was updated to %s (was %s).%s' % (a['name'], a.get('version'), o.get('version'), tail)))
def post(body):
    req = urllib.request.Request(HOOK, data=json.dumps(body).encode(), headers={'Content-Type': 'application/json', 'User-Agent': 'VitaHomebrewDB'})
    urllib.request.urlopen(req, timeout=30); time.sleep(2)
print('%d Aenderungen' % len(lines))
if len(lines) > 30:
    neu = sum(1 for n, l in lines if n)
    post({'content': '**VitaHomebrewDB:** %d new entries and %d updates. Full list: <https://github.com/DrDecki/VitaHomebrewDB/blob/main/ADDED.md>' % (neu, len(lines) - neu)})
else:
    for n, l in lines: post({'content': l, 'flags': 4})
