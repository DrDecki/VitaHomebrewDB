# Maps old spellings of an author to the name of their repository account, in every entry
# and in every part of a multi-author field. Run after repo_authors.py --write.
import json, re, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
A = json.load(open('author_aliases.json', encoding='utf-8'))
FS = ('apps.json', 'psp_apps.json', 'preserved/plugins.json', 'preserved/tools.json')
n = 0
for f in FS:
    d = json.load(open(f, encoding='utf-8'))
    for a in d:
        old = a.get('author') or ''
        parts = re.split(r'(\s*\\?&\s*|\s*,\s*|\s+and\s+)', old)
        new = ''.join(A.get(p.strip(), p) if i % 2 == 0 else p for i, p in enumerate(parts))
        if new != old: a['author'] = new; n += 1; print('%s %-5s %-35s %s -> %s' % (f[:4], a['id'], a['name'][:35], old, new))
    json.dump(d, open(f, 'w', encoding='utf-8'), indent=4, ensure_ascii=False)
print('%d Namensteile angepasst' % n)
