# Ideas and open ends

Notes on what is worth doing next, and on things that were tried and did not work,
so nobody spends an evening rediscovering them.

## A second copy of the mirror

Everything the catalog serves that authors no longer host themselves lives in one
place: the `mirror` release tag on this repository, tied to a single GitHub account.

VitaDB went offline on 31.07.2026, came back partially, went away again, and returned
in full weeks later. Nothing was lost in the end, but for a while nobody knew that.
A catalog that exists because one host went away should not depend on one host.

A second copy somewhere unrelated would fix it. archive.org is the obvious candidate
but has suspended bulk uploads before, so it cannot be the only answer either.

This matters more than anything else on this page.

## GitHub Pages is close to its limit

The site is about 900 MB and GitHub Pages stops at 1 GB. Screenshots take most of
it. `icons.zip` (41 MB) is the easy first step, moving it to the mirror release.
Moving the screenshots is the real fix.

## Nightly builds

Some projects only publish rolling tags or Actions artifacts that expire after
90 days. The catalog leaves them out for now. A separate list, fed from a rolling
`nightly` tag on the mirror, would be one way to carry them.

## Watching sources

`watch_reddit.py` and `watch_report.py` run daily and open an issue listing new posts
from r/vitahacks and r/VitaPiracy. Reddit closed anonymous RSS access in November
2026; even private feed keys answer "Not Found". The posts now come from
[Arctic Shift](https://arctic-shift.photon-reddit.com), a public archive of Reddit
with an open API. No account and no key are needed.

`watch_vitadb.py` compares VitaDB's four lists with this catalog and opens an issue
for entries it does not carry yet.

X has no affordable API at all. This is the awkward part, because the idea came from
devnoname120, who announces his own releases there and nowhere else. Posts on X will
keep arriving by hand.

## Updates

`tools/update_all.py` checks every entry against its GitHub or GitLab release once a
day, including releases that ship the VPK inside a ZIP. Release lookups go through
GraphQL in batches of 50: the Actions token allows 1000 REST calls an hour, which is
why the old bot silently missed updates once it ran out. Pre-releases are only taken
when the entry is a pre-release itself or the project publishes nothing else.

`tools/vitadb_updates.py` picks up new versions that VitaDB hosts itself. Entries are
matched by title ID first, because several projects share one repository.

git.silica.codes is not polled. The server answers automated requests with a crawler
trap, so the entries hosted there are checked by hand.

## What is not added

`blocklist.json` lists authors and titles that will not be added again, each with
its reason. Both watch scripts and the sync tools read it.

Releases that ship commercial game data are not added, not even the VPK alone.

## Lessons

A 403 on a directory says nothing about the files inside it. VitaDB's
`/vitadb/screenshots/` refused a listing, but every single file answered, which is
how all 2186 screenshots came back.

## Download counts are frozen

The `downloads` figures are VitaDB's numbers from 31.07.2026 and will never change.
Static hosting cannot count. Sorting by popularity still works, it just describes the
day the site went down.
