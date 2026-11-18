import html, json, os, re, time, urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
SUBS = ('vitahacks', 'VitaPiracy')
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
SEEN = os.path.join(ROOT, 'watch_seen.json')
EIGENE = ('vitadbtoo', 'drdecki.github.io')
# Hilfe-Anfragen beginnen fast immer so. Nur der Titelanfang wird geprueft,
# weil Ankuendigungstexte weiter unten oft selbst um Rueckmeldung bitten.
FRAGEN = ('help', 'how do i', 'how to', 'how can i', 'is there a way', 'anyone know',
          'does anyone', 'can someone', 'can anyone', 'need help', 'looking for',
          'why is', 'why does', 'what is the best', 'question', 'issue with',
          'problem with', 'trouble with')

seen = set(json.load(open(SEEN))) if os.path.exists(SEEN) else set()

def fetch(sub):
    u = 'https://arctic-shift.photon-reddit.com/api/posts/search?subreddit=%s&limit=100&sort=desc' % sub
    with urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'VitaHomebrewDB watch'}), timeout=60) as r:
        data = json.load(r).get('data') or []
    out = []
    for p in data:
        out.append({'id': p.get('name') or 't3_' + (p.get('id') or ''),
                    'title': html.unescape(p.get('title') or '').strip(),
                    'url': 'https://www.reddit.com' + (p.get('permalink') or ''),
                    'text': (html.unescape(p.get('selftext') or '') + ' ' + (p.get('url') or ''))[:1200]})
    return out

kandidaten = []
for sub in SUBS:
    try:
        alle = fetch(sub)
    except Exception as e:
        print('r/%-14s %s' % (sub, getattr(e, 'code', type(e).__name__)))
        continue
    neu = 0
    for e in alle:
        if not e['id'] or e['id'] in seen:
            continue
        seen.add(e['id'])
        neu += 1
        e['sub'] = sub
        low = (e['title'] + ' ' + e['text']).lower()
        titel = e['title'].lower().lstrip('[( ')
        frage = titel.startswith(FRAGEN) or e['title'].rstrip().endswith('?')
        eigen = any(w in low for w in EIGENE)
        e['uebersprungen'] = 'eigenes Projekt' if eigen else ('Frage' if frage else '')
        kandidaten.append(e)
    print('r/%-14s %d neue von %d' % (sub, neu, len(alle)))
    time.sleep(15)

json.dump(sorted(seen), open(SEEN, 'w'))
json.dump(kandidaten, open(os.path.join(ROOT, 'watch_new.json'), 'w'), indent=1, ensure_ascii=False)
print()
uebrig = [k for k in kandidaten if not k['uebersprungen']]
print('%d neue Beitraege, %d nach dem Vorfilter' % (len(kandidaten), len(uebrig)))
