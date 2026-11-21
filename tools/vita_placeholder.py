import hashlib, io, json, os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageChops
src, halo = sys.argv[1], 10
im = Image.open(src).convert('RGBA'); bg = Image.new('RGBA', im.size, (255,255,255,255)); bg.alpha_composite(im)
pad = halo * 2 + 4; g = Image.new('L', (bg.width + 2*pad, bg.height + 2*pad), 255); g.paste(bg.convert('L'), (pad, pad))
m = g.point(lambda v: 0 if v < 128 else 255); ImageDraw.floodfill(m, (0, 0), 128)
cons = m.point(lambda v: 0 if v == 128 else 255)
ring = ImageChops.subtract(cons.filter(ImageFilter.MaxFilter(2*halo+1)), cons)
out = Image.new('L', g.size, 0); out.paste(g, (0, 0), cons); out.paste(255, (0, 0), ring)
out = out.crop(ImageChops.add(cons, ring).getbbox()); w = 116; h = round(out.height * w / out.width)
fin = Image.new('L', (128, 128), 0); fin.paste(out.resize((w, h), Image.LANCZOS), ((128-w)//2, (128-h)//2))
buf = io.BytesIO(); fin.convert('RGB').save(buf, 'PNG'); png = buf.getvalue()
name = hashlib.sha256(png).hexdigest() + '.png'; open('icons/' + name, 'wb').write(png); print('  Icon: icons/%s' % name)
d = json.load(open('apps.json', encoding='utf-8')); n = 0
for a in d:
    if not (a.get('icon') or '').strip() or not os.path.exists('icons/' + a['icon'].strip()):
        a['icon'] = name; n += 1; print('    %-5s %s' % (a['id'], a['name']))
json.dump(d, open('apps.json', 'w', encoding='utf-8'), indent=4, ensure_ascii=False); print('  %d Eintraege mit Ersatz-Icon' % n)
