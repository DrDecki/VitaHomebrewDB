import json, re, os

ROOT = os.path.dirname(os.path.abspath(__file__))

def load(n):
    with open(os.path.join(ROOT, n), 'rb') as f:
        return json.loads(f.read().decode('utf-8', 'replace'))

used = set()
apps = load('apps.json')
for a in apps:
    m = re.search(r'files/vitadb/(.+)$', a['url'])
    if m:
        used.add(m.group(1))

arch = []
p = '/tmp/cdx_len.txt'
if os.path.exists(p):
    for line in open(p):
        q = line.split()
        if len(q) >= 3 and q[2] == '200':
            m = re.search(r'files/vitadb/(.+)$', q[0])
            if m and m.group(1) not in used:
                arch.append(m.group(1))

rows = []
for fname, label in (('apps.json', 'Vita'), ('psp_apps.json', 'PSP'),
                     ('preserved/plugins.json', 'Plugin'), ('preserved/tools.json', 'Tool')):
    for a in load(fname):
        if 'get_hb_url' in a['url']:
            src = a.get('release_page') or a.get('source') or ''
            rows.append((label, a['name'], a['version'], a['author'], a['size'], src, a['id']))

out = []
out.append('# Wanted: missing downloads\n')
if not rows:
    out = ['# Nothing wanted right now' + chr(10) + chr(10)]
    out.append('Every entry VitaDB held on 31.07.2026 has a working download again.' + chr(10) + chr(10))
    out.append('That took the whole scene, not one person. LiEnby kept an old cbpsdb mirror' + chr(10))
    out.append('alive that still had files nobody else could find. ChassyFlaps went through the' + chr(10))
    out.append('list by hand and sent back a page of sources. devnoname120 turned up PSVitaStuff,' + chr(10))
    out.append('the very last one missing. Cimmerian-Iter insisted early on that anything handed' + chr(10))
    out.append('over should be verified, which is why every recovered file here was matched' + chr(10))
    out.append('against the size VitaDB recorded. GameBrew and Brewology had quietly kept copies' + chr(10))
    out.append('for years. Several authors simply sent their own builds when asked.' + chr(10) + chr(10))
    out.append('Thank you.' + chr(10) + chr(10))
    out.append('If something breaks again, or you spot an entry pointing at the wrong file,' + chr(10))
    out.append('open an issue. This page will fill back up on its own when it needs to.' + chr(10))
    open(os.path.join(ROOT, 'WANTED.md'), 'w', encoding='utf-8').writelines(out)
    print('WANTED.md: nichts offen')
    raise SystemExit
out.append('These %d entries survive in the catalog with full metadata, but their download\n' % len(rows))
out.append('link died with the VitaDB webhost and could not be recovered automatically.\n\n')
out.append('If you have one of these files, or know where it lives now, please open an issue\n')
out.append('or a pull request.\n\n')
out.append('**What is needed is a stable direct URL a PSVITA can fetch without a browser.**\n')
out.append('A GitHub release asset works. An archive.org item works. An itch.io page does not,\n')
out.append('because it serves through signed one-time links. A page that only works in a browser\n')
out.append('is still a useful lead: send it anyway and the file can be mirrored here.\n')
out.append('If the file matches the MD5 listed in the catalog it is the exact build VitaDB\n')
out.append('served, which settles any doubt about what it is.\n\n')
out.append('The file size below is the one VitaDB recorded, which makes it easy to confirm a\n')
out.append('candidate is the right build.\n\n')
out.append('Everything GameBrew still hosts has already been recovered and mirrored: 108 entries\n')
out.append('were restored that way. A [GameBrew](https://www.gamebrew.org) link in the table below\n')
out.append('therefore means the wiki documents the homebrew but holds no copy of the file.\n\n')
out.append('The last column collects other leads. `cbpsdb` points at an old mirror of VitaDB\n')
out.append('kept by LiEnby at [gitlab.com/SilicaAndPina/cbpsdb](https://gitlab.com/SilicaAndPina/cbpsdb);\n')
out.append('those files predate this snapshot, so none of them match the MD5 recorded here and\n')
out.append('entries marked `?` share a title ID with other homebrew. `lead` entries were found by\n')
out.append('contributors. Verify anything before trusting it.\n\n')
out.append('| Type | Name | Version | Author | Size | Known source | GameBrew | Other leads |\n')
out.append('| --- | --- | --- | --- | ---: | --- | --- | --- |\n')
gb = {}
if os.path.exists(os.path.join(ROOT, 'gamebrew_refs.json')):
    gb = json.load(open(os.path.join(ROOT, 'gamebrew_refs.json')))

cb = {}
if os.path.exists(os.path.join(ROOT, 'cbpsdb_refs.json')):
    cb = json.load(open(os.path.join(ROOT, 'cbpsdb_refs.json')))

comm = {}
if os.path.exists(os.path.join(ROOT, 'community_refs.json')):
    comm = json.load(open(os.path.join(ROOT, 'community_refs.json')))

for t, n, v, au, sz, src, aid in sorted(rows):
    size = '%.1f MB' % (int(sz) / 1048576.0) if sz and sz.isdigit() else '?'
    link = '[link](%s)' % src if src else '-'
    g = gb.get(aid)
    if g and g.get('dl'):
        ref = '[page](https://www.gamebrew.org/wiki/%s) / [file](%s)' % (g['page'].replace(' ', '_'), g['dl'])
    elif g:
        ref = '[page](https://www.gamebrew.org/wiki/%s)' % g['page'].replace(' ', '_')
    else:
        ref = '-'
    leads = []
    c = cb.get(aid)
    if c:
        leads.append('[cbpsdb](%s)%s' % (c['url'], ' ?' if c['ambiguous'] else ''))
    if aid in comm:
        leads.append('[lead](%s)' % comm[aid])
    out.append('| %s | %s | %s | %s | %s | %s | %s | %s |\n' % (t, n.replace('|', ''), v, au.replace('|', ''), size, link, ref, ' '.join(leads) if leads else '-'))

if arch:
    out.append('\n## Unmatched archived files\n\n')
    out.append('The Internet Archive holds %d further files from the old webhost that could not\n' % len(arch))
    out.append('be matched to an entry above. Filenames rarely match the display name, so this\n')
    out.append('needs someone who recognises them.\n\n```\n')
    for f in sorted(arch):
        out.append(f + '\n')
    out.append('```\n')

open(os.path.join(ROOT, 'WANTED.md'), 'w').write(''.join(out))
print('WANTED.md: %d fehlende Eintraege, %d unzugeordnete Archivdateien' % (len(rows), len(arch)))
