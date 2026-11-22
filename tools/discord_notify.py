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
embeds = []
for f, kind in FILES.items():
    old, new = load(BEFORE, f), load(AFTER, f)
    for i, a in new.items():
        o = old.get(i); link = a.get('release_page') or a.get('source') or a.get('url')
        if o is None: title, color, text = 'New: %s' % a['name'], 0x2ecc71, a.get('description') or ''
        elif (o.get('version') or '') != (a.get('version') or ''): title, color, text = 'Updated: %s' % a['name'], 0x3498db, '%s → %s' % (o.get('version'), a.get('version'))
        else: continue
        e = {'title': title[:256], 'url': link, 'color': color, 'description': text[:300],
             'footer': {'text': '%s · %s · %s' % (kind, a.get('author') or '?', a.get('version') or '')}}
        if a.get('icon'): e['thumbnail'] = {'url': ICON + a['icon']}
        embeds.append(e)
def post(body):
    req = urllib.request.Request(HOOK, data=json.dumps(body).encode(), headers={'Content-Type': 'application/json', 'User-Agent': 'VitaHomebrewDB'})
    urllib.request.urlopen(req, timeout=30); time.sleep(2)
print('%d Aenderungen' % len(embeds))
if len(embeds) > 30:
    neu = sum(1 for e in embeds if e['title'].startswith('New')); post({'content': '**VitaHomebrewDB:** %d new entries and %d updates. Full list: <https://github.com/DrDecki/VitaHomebrewDB/blob/main/ADDED.md>' % (neu, len(embeds) - neu)})
else:
    for i in range(0, len(embeds), 10): post({'embeds': embeds[i:i + 10]})
