import json, os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
NEW = os.path.join(ROOT, 'watch_new.json')

if not os.path.exists(NEW):
    print('keine watch_new.json')
    sys.exit(0)

kand = [k for k in json.load(open(NEW, encoding='utf-8')) if not k['uebersprungen']]
if not kand:
    print('nichts zu melden')
    sys.exit(0)

# Beitraege mit einem Link auf eine Datei oder ein Repository zuerst
def rang(k):
    t = (k['title'] + ' ' + k['text']).lower()
    p = 0
    if re.search(r'\.vpk|\.skprx|\.suprx|releases/download', t):
        p -= 2
    if 'github.com' in t or 'itch.io' in t:
        p -= 1
    if k.get('schon_drin'):
        p += 5
    return p

bekannt = set()
for f in ('apps.json', 'psp_apps.json', 'preserved/plugins.json', 'preserved/tools.json'):
    for a in json.load(open(os.path.join(ROOT, f), encoding='utf-8')):
        for feld in (a.get('url', ''), a.get('source', ''), a.get('release_page', '')):
            m = re.search(r'github\.com/([^/\s]+/[^/\s]+)', feld or '')
            if m:
                bekannt.add(m.group(1).lower().rstrip('.git'))

for k in kand:
    k['repos'] = {m.group(1).lower().rstrip('.git') for m in
                  re.finditer(r'github\.com/([^/\s"\'<>]+/[^/\s"\'<>]+)', k['title'] + ' ' + k['text'])}
    k['schon_drin'] = bool(k['repos'] & bekannt)

kand.sort(key=rang)

lines = ['New posts from the subreddits this catalog watches.',
         'Nothing here has been checked. Skim the titles and ignore the rest.', '']
for k in kand:
    m = re.search(r'(https?://(?:github\.com|itch\.io|[^\s<>"\']*\.(?:vpk|zip|7z))[^\s<>"\']*)', k['text'])
    extra = '  —  %s' % m.group(1)[:70] if m else ''
    mark = '  `already in the catalog`' if k['schon_drin'] else ''
    lines.append('- [%s](%s) *(r/%s)*%s%s' % (k['title'][:110].replace('|', ''), k['url'], k['sub'], extra, mark))
lines.append('')
lines.append('Close this issue once you have looked through it.')

open(os.path.join(ROOT, 'watch_issue.md'), 'w', encoding='utf-8').write('\n'.join(lines))
print('%d Beitraege in watch_issue.md' % len(kand))
