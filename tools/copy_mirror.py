import json, os, shutil, subprocess, sys, tempfile, time, urllib.request
SRC, DST = 'DrDecki/VitaHomebrewDB', os.environ.get('MIRROR_COPY_TARGET', 'DrDecki/VitaDBtoo')
def gh(*a, out=True): return subprocess.run(['gh'] + list(a), capture_output=True, text=out)
def pause():
    rl = json.loads(gh('api', 'rate_limit').stdout or '{}').get('resources', {}).get('core', {})
    w = max(60, rl.get('reset', 0) - int(time.time()) + 30) if rl.get('remaining', 1000) < 100 else 600
    print('    Limit erreicht, warte %d Minuten (%s)' % (w // 60, time.strftime('bis %H:%M', time.localtime(time.time() + w))), flush=True); time.sleep(w)
def run(*a):
    while True:
        r = gh(*a)
        if r.returncode == 0: return r
        if 'rate limit' in r.stderr.lower() or 'secondary' in r.stderr.lower(): pause(); continue
        return r
def assets(repo, tag):
    r = run('api', '--paginate', 'repos/%s/releases/tags/%s' % (repo, tag), '--jq', '.assets[] | [.name, .size, .browser_download_url] | @tsv')
    if r.returncode: return None
    return {l.split('\t')[0]: (int(l.split('\t')[1]), l.split('\t')[2]) for l in r.stdout.splitlines() if l.strip()}
tags = [t for t in run('api', '--paginate', 'repos/%s/releases' % SRC, '--jq', '.[].tag_name').stdout.split() if t.startswith(('mirror', 'shots-')) or t == 'nightly']
total = 0
for tag in sorted(tags):
    src = assets(SRC, tag) or {}; dst = assets(DST, tag)
    if dst is None:
        run('release', 'create', tag, '--repo', DST, '--title', tag, '--notes', 'Copy of the %s release of %s.' % (tag, SRC)); dst = {}
    todo = [n for n, (s, u) in src.items() if dst.get(n, (None,))[0] != s]
    for i in range(0, len(todo), 20):
        tmp = tempfile.mkdtemp(); paths = []
        for n in todo[i:i + 20]:
            try:
                with urllib.request.urlopen(urllib.request.Request(src[n][1], headers={'User-Agent': 'VitaHomebrewDB'}), timeout=1800) as r, open(os.path.join(tmp, n), 'wb') as f: shutil.copyfileobj(r, f)
                paths.append(os.path.join(tmp, n))
            except Exception as e: print('    %s: Download fehlgeschlagen %s' % (n, type(e).__name__))
        if paths:
            r = run('release', 'upload', tag, '--repo', DST, '--clobber', *paths)
            if r.returncode: print('    %s: Upload-Fehler %s' % (tag, r.stderr.strip()[:100]))
        shutil.rmtree(tmp); time.sleep(3)
    dst = assets(DST, tag) or {}
    miss = [n for n, (s, u) in src.items() if dst.get(n, (None,))[0] != s]
    total += len(miss)
    print('  %-10s %4d Dateien, %4d kopiert%s  (%s)' % (tag, len(src), len(todo) - len(miss), '' if not miss else ', FEHLEN %d' % len(miss), time.strftime('%H:%M')), flush=True)
print('\nvollstaendig' if not total else '\n%d Dateien fehlen noch, nochmal starten' % total)
sys.exit(1 if total else 0)
