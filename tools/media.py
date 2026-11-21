import os, subprocess
REPO = 'DrDecki/VitaHomebrewDB'
BASE = 'https://github.com/%s/releases/download/' % REPO
MIRROR_RE = r'https://github\.com/DrDecki/VitaHomebrewDB/releases/download/mirror(-\d+)?/'
LIMIT = 990
def _gh(*a): return subprocess.run(['gh'] + list(a) + ['--repo', REPO], capture_output=True, text=True)
def _names(tag):
    r = _gh('release', 'view', tag, '--json', 'assets', '--jq', '.assets[].name')
    return set(r.stdout.split()) if r.returncode == 0 else None
def _upload(tag, path, title, notes):
    if _names(tag) is None: _gh('release', 'create', tag, '--title', title, '--notes', notes)
    return _gh('release', 'upload', tag, path, '--clobber').returncode == 0
def mirror_upload(path):
    name, n = os.path.basename(path), 1
    while True:
        tag = 'mirror' if n == 1 else 'mirror-%d' % n
        names = _names(tag)
        if names is None or name in names or len(names) < LIMIT:
            ok = _upload(tag, path, 'Mirror %d' % n, 'Files the catalog serves that their authors no longer host (part %d).' % n)
            return BASE + tag + '/' + name if ok else None
        n += 1
def shot_upload(path):
    name = os.path.basename(path); c = name[0].lower()
    tag = 'shots-' + (c if c in '0123456789abcdef' else 'x')
    ok = _upload(tag, path, 'Screenshots ' + tag[-1], 'Catalog screenshots whose file name starts with "%s".' % tag[-1])
    return BASE + tag + '/' + name if ok else None
