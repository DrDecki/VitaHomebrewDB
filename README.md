# VitaHomebrewDB

A homebrew catalogue for PSVITA/PSTV and PSP. It started as a rescue of
[VitaDB](https://www.rinnegatamante.eu/vitadb) after the official service went offline on
2026-07-31, and everything that database held is preserved here. It has kept growing since,
with entries VitaDB never carried.

This repository is the catalogue: application metadata, icons, screenshots and trailers, served as
static files over GitHub Pages at `https://drdecki.github.io/VitaHomebrewDB/`.

## What survived

The metadata comes from a local client cache (`ux0:data/VitaDB`) captured on **2026-07-31**,
the last state of the database before shutdown. The plugin and PC tool catalogues were
recovered from the Internet Archive. Download links were then resolved individually, either
to the author's GitHub release or to an archived copy of the original file.

Every entry keeps its original curated metadata: name, version, author, description,
changelog, requirements, category, release date and download count. That part cannot be
reconstructed from repositories, which is what makes this catalogue worth keeping.


[CATALOGUE.md](CATALOGUE.md) lists every entry with its author, version and download.

<!-- STATS -->
| | Entries | With a working download |
| --- | ---: | ---: |
| PSVITA homebrews | 1019 | 1019 |
| Plugins | 123 | 123 |
| PSP homebrews | 127 | 127 |
| PC tools | 27 | 27 |
| **Total** | **1296** | **1296 (100%)** |

45 further entries have been added since the shutdown and are not part of
what VitaDB held. They are listed separately in [ADDED.md](ADDED.md).

| Asset | Recovered |
| --- | ---: |
| Metadata | 100% (1296 entries) |
| Icons | 100% (1368) |
| Screenshots | 100% (2186 of 2186) |
| Trailers | 100% (62 of 62) |
| Data files | 100% (137 of 137) |
| In-game trophies | 100% (28 of 28 sets) |

Nothing is missing at the moment. [WANTED.md](WANTED.md) fills back up on its own
when something breaks or a new entry arrives without a working link.
<!-- /STATS -->

## Files

| Path | Contents |
| --- | --- |
| `apps.json` | PSVITA homebrews |
| `psp_apps.json` | PSP homebrews |
| `minimal.json` | id, titleid and hashes, for the update daemon |
| `icons/` | app icons, `<sha256>.png` |
| `icons.zip` | all icons as one archive |
| `screenshots/` | recovered screenshots |
| `preserved/plugins.json` | plugin catalogue |
| `preserved/tools.json` | PC tool catalogue |
| `WANTED.md` | entries whose download is still missing |

The plugin and tool catalogues live under `preserved/` because the original client never
listed them; they were separate sections of the VitaDB website. They are kept in the same
schema so a client can consume them the same way.

## Using this catalogue

Every entry carries a direct download URL in its `url` field, so a client does not need a
redirect endpoint. Downloads point either at a GitHub release asset or at an archived copy
on `web.archive.org`; both have been verified on hardware.

If you are writing a client against this, note that download counts are frozen at their
2026-07-31 values. Static hosting cannot count downloads, so sorting by popularity reflects
the state at shutdown and will not change.

Known consumers: [VitaForge](https://github.com/josephinoo/vitaForge) by josephinoo.
If you build another one, open an issue and it can be listed here.

## What is missing

Nothing. Every entry has a working download, and every screenshot, trailer, data file and
trophy set VitaDB carried has been recovered. None of it depends on the old webhost any
more: what the authors no longer serve themselves is mirrored here.

Download counts are the one exception. They are frozen at the numbers VitaDB recorded on
2026-07-31, because static hosting cannot count. Sorting by popularity still works, it just
describes the day the site went down.

Themes are unaffected and continue to work: they have always been hosted separately at
[CatoTheYounger97/vitaDB_themes](https://github.com/CatoTheYounger97/vitaDB_themes).

## Maintaining

Adding a homebrew, given a direct URL to its VPK:

```
python3 add_app.py --url <vpk-url> --type port --author "Name" --desc "Short description" \
                   --source https://github.com/... --release-page https://github.com/.../releases
python3 build_db.py
```

`add_app.py` reads the title, title ID, version and icon out of the VPK itself and computes
size and MD5. `build_db.py` regenerates `minimal.json` and `icons.zip` and verifies icon
coverage. Run it after any change to `apps.json`, `psp_apps.json` or `icons/`.

`mkwanted.py` regenerates `WANTED.md`.

Anyone can run these; they only touch a local checkout. To contribute an entry,
fork the repository, run the two commands above and open a pull request. What
gets merged is still reviewed by hand, because a wrong URL in the catalogue is
worse than a missing one.

## Credits and takedowns

VitaDB was created and run by **Rinnegatamante**. The catalogue is his work and that of
every homebrew author in it; this repository only keeps it reachable.

Thanks to **FundedBlade** for pointing at the GameBrew wiki and the PSP homebrew
library on archive.org, which together closed over a hundred gaps, and to
**josephinoo** for building [VitaForge](https://github.com/josephinoo) against this
catalogue and for the API tips.

If you are an author and want your application removed, open an issue and it will be taken
down.

## License

The scripts in this repository (`build_db.py`, `add_app.py`, `stats.py`,
`mkwanted.py` and the rest) are MIT licensed, see [LICENSE](LICENSE). Use them
however you like.

The catalogue itself is a different matter and is **not** covered by that
licence. Application names, descriptions, changelogs, icons and screenshots are
the work of Rinnegatamante and of the individual homebrew authors. This
repository preserves and redistributes them so the catalogue stays reachable; it
claims no ownership over them. Clients are welcome to consume the JSON files,
and anyone who wants their own work removed only has to open an issue.

If you build a client or another catalogue on top of this data, please link back
to this repository. The metadata is not mine to license, so this is a request
rather than a condition, but a fair amount of work went into recovering it and
being credited for that is the only thing asked in return.

## Support

This is a spare-time project and the catalogue is free to use, with or without a client of mine. If it saved you a homebrew you thought was gone, there is a [Ko-fi](https://ko-fi.com/drdecki).
