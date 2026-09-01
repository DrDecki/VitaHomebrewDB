# Ideas and open ends

What is left to do, and what was already tried and did not work.

## A second copy of the mirror

Everything the catalog serves that authors no longer host lives in one place: the `mirror`
release tag on this repository, on one GitHub account.

VitaDB went offline on 31.07.2026, came back partially, went away again, and returned in
full weeks later. Nothing was lost, but for a while nobody knew that. Worth not repeating here.

archive.org is the obvious second home but has suspended bulk uploads before, so it cannot
be the only one.

## Watching sources

`watch_reddit.py` and `watch_report.py` run daily and open an issue listing new
posts from the subreddits this catalog watches. No API key and no account are
needed. Posts linking to a repository already in the catalog are marked and sorted
to the bottom.

Beyond that the list is unfiltered. A model could sort announcements from support
questions, `watch_judge.py` did that before it was dropped for a plain list and is still
in the git history. At forty posts a day, reading the titles is quicker.

A 403 on a directory says nothing about the files inside it: `/vitadb/screenshots/`
refused a listing the whole time while every single file answered fine, which is how
all 2186 of them came back.

Reddit's JSON API and GBAtemp both answer 403 to anything that is not a browser,
and creating a Reddit API application no longer works without going through their
builder policy. The RSS feeds still work without any of that, which is what these
scripts use. They return 429 if called too quickly, hence the pause between
subreddits.

X has no affordable API. Awkward, because the idea came from devnoname120, who announces
his releases there and nowhere else. Those keep arriving by hand.

## Download counts are frozen

VitaDB's numbers from 31.07.2026, and they stay that way. Static hosting cannot count.
