import concurrent.futures, hashlib, io, json, os, re, struct, sys, threading, urllib.request, zipfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP = os.path.expanduser('~/psp_icons_map.json')
LIMIT = int(sys.argv[sys.argv.index('--limit') + 1]) if '--limit' in sys.argv else None
UA = {'User-Agent': 'VitaHomebrewDB'}

class RangeFile(io.RawIOBase):
    BLK = 65536
    def __init__(self, url):
        r = urllib.request.urlopen(urllib.request.Request(url, headers=dict(UA, Range='bytes=0-0')), timeout=60)
        self.url, self.size, self.pos, self.cache = r.geturl(), int(r.headers['Content-Range'].split('/')[-1]), 0, {}
    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.pos
    def seek(self, o, w=0):
        self.pos = o if w == 0 else self.pos + o if w == 1 else self.size + o
        return self.pos
    def block(self, n):
        if n not in self.cache:
            a = n * self.BLK; b = min(a + self.BLK, self.size) - 1
            self.cache[n] = urllib.request.urlopen(urllib.request.Request(self.url, headers=dict(UA, Range='bytes=%d-%d' % (a, b))), timeout=60).read()
        return self.cache[n]
    def read(self, n=-1):
        if n is None or n < 0: n = self.size - self.pos
        out = bytearray()
        while len(out) < n and self.pos < self.size:
            blk = self.block(self.pos // self.BLK); off = self.pos % self.BLK
            k = min(n - len(out), len(blk) - off); out += blk[off:off + k]; self.pos += k
        return bytes(out)
    def readinto(self, buf):
        if self.pos >= self.size: return 0
        blk = self.block(self.pos // self.BLK); off = self.pos % self.BLK
        n = min(len(buf), len(blk) - off); buf[:n] = blk[off:off + n]; self.pos += n
        return n

def icon(url):
    z = zipfile.ZipFile(RangeFile(url))
    ebs = [i for i in z.infolist() if i.filename.upper().endswith('EBOOT.PBP') and '%' not in i.filename and i.file_size > 40]
    if not ebs: return None, 'kein EBOOT'
    ebs.sort(key=lambda i: (i.filename.count('/'), -i.file_size))
    with z.open(ebs[0]) as e:
        h = e.read(40)
        if h[:4] != b'\x00PBP': return None, 'kein PBP'
        off = struct.unpack('<8I', h[8:40])
        if off[2] <= off[1]: return None, 'ohne ICON0'
        data = e.read(off[2] - 40)
    png = data[off[1] - 40:off[2] - 40]
    if png[:8] != b'\x89PNG\r\n\x1a\n': return None, 'ICON0 kein PNG'
    return png, 'ok'

done = json.load(open(MAP)) if os.path.exists(MAP) else {}
psp = json.load(open(os.path.join(ROOT, 'psp_apps.json'), encoding='utf-8'))
todo = [a for a in psp if not (a.get('icon') or '').strip() and a['url'].lower().endswith('.zip') and a['id'] not in done]
if LIMIT: todo = todo[:LIMIT]
print('%d Eintraege zu pruefen' % len(todo), flush=True)
lock = threading.Lock(); n = [0]
def job(a):
    try: png, why = icon(a['url'])
    except Exception as ex: png, why = None, type(ex).__name__
    with lock:
        if png:
            h = hashlib.sha256(png).hexdigest()
            open(os.path.join(ROOT, 'icons', h + '.png'), 'wb').write(png)
            done[a['id']] = h + '.png'
        else:
            done[a['id']] = '-' + why
        n[0] += 1
        if LIMIT: print('  %-5s %-30s %s' % (a['id'], a['name'][:30], 'Icon' if png else why), flush=True)
        if n[0] % 50 == 0:
            json.dump(done, open(MAP, 'w'))
            ok = sum(1 for v in done.values() if not v.startswith('-'))
            print('  %d / %d, davon %d mit Icon' % (n[0], len(todo), ok), flush=True)
with concurrent.futures.ThreadPoolExecutor(4) as ex: list(ex.map(job, todo))
json.dump(done, open(MAP, 'w'))
ok = sum(1 for v in done.values() if not v.startswith('-'))
print('fertig: %d geprueft, %d mit Icon' % (len(done), ok))
