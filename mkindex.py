import json, os

ROOT = os.path.dirname(os.path.abspath(__file__))
LAST_VITADB_ID = 1449

def load(n):
    with open(os.path.join(ROOT, n), 'rb') as f:
        return json.loads(f.read().decode('utf-8', 'replace'))

def live(a):
    return 'get_hb_url' not in a.get('url', '') and not a.get('url', '').endswith('.php')

def esc(s):
    return (s or '').replace('|', '\\|').replace('\n', ' ').strip()

cats = [('PSVITA homebrews', 'apps.json'), ('Plugins', 'preserved/plugins.json'),
        ('PSP homebrews', 'psp_apps.json'), ('PC tools', 'preserved/tools.json')]

def tabelle(entries):
    out = ['| Name | Author | Version | Size | Download | Source |\n',
           '| --- | --- | --- | ---: | --- | --- |\n']
    for a in sorted(entries, key=lambda x: x['name'].lower()):
        mb = int(a.get('size') or 0) / 1048576.0
        dl = '[download](%s)' % a['url'] if live(a) else '—'
        src = a.get('source') or a.get('release_page') or ''
        src = '[repo](%s)' % src if src else '—'
        out.append('| %s | %s | %s | %.1f MB | %s | %s |\n' % (
            esc(a['name']), esc(a.get('author')), esc(a.get('version')), mb, dl, src))
    return out

for datei, titel, pick, vorwort in (
    ('CATALOGUE.md', 'Catalogue',
     lambda a: True,
     'Every entry in the catalogue, with the download it currently resolves to.\n'
     'The ones added since 31.07.2026 are also listed on their own in\n'
     '[ADDED.md](ADDED.md).\n'),
    ('ADDED.md', 'Added since 31.07.2026',
     lambda a: int(a['id']) > LAST_VITADB_ID,
     'Everything here arrived after the snapshot this catalogue preserves. Some came\n'
     'from VitaDB once it returned, some straight from their authors, some from the\n'
     'wider scene. They are kept apart so the preserved catalogue stays exactly what\n'
     'it was on the day the service went down.\n'),
):
    out = ['# %s\n\n' % titel, vorwort, '\n']
    n = 0
    groesse = 0
    for label, f in cats:
        e = [a for a in load(f) if pick(a)]
        if not e:
            continue
        out.append('## %s (%d)\n\n' % (label, len(e)))
        out += tabelle(e)
        out.append('\n')
        n += len(e)
        groesse += sum(int(a.get('size') or 0) + int(a.get('data_size') or 0) for a in e)
    if groesse:
        out.append('%d entries, %.1f GB in total.\n' % (n, groesse / 1073741824.0))
    with open(os.path.join(ROOT, datei), 'w', encoding='utf-8') as fh:
        fh.write(''.join(out))
    print('%s: %d Eintraege' % (datei, n))
