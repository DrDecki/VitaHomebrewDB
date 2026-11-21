import json, os
ICON = '18746b487153dc1ca3d728ce57b841b6e8faeca65a0900aa46864f73d07642c8.png'
d = json.load(open('apps.json', encoding='utf-8')); n = 0
for a in d:
    if not (a.get('icon') or '').strip() or not os.path.exists('icons/' + a['icon'].strip()):
        a['icon'] = ICON; n += 1; print('    %-5s %s' % (a['id'], a['name']))
json.dump(d, open('apps.json', 'w', encoding='utf-8'), indent=4, ensure_ascii=False); print('  %d Eintraege mit VitaDB-Standard-Icon' % n)
