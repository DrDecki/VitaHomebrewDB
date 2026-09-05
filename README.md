# VitaHomebrewDB

Homebrew catalog for PSVITA/PSTV and PSP.

VitaDB went offline on 31.07.2026. This started as a backup of it and kept going from
there. Everything VitaDB had is here, plus a lot that arrived later.

Metadata, icons, screenshots and trailers, served as static files over GitHub Pages at
`https://drdecki.github.io/VitaHomebrewDB/`.

## What survived

The metadata comes from a local client cache (`ux0:data/VitaDB`) captured on **2026-07-31**,
the last state of the database before shutdown. The plugin and PC tool catalogs were
recovered from the Internet Archive. Download links were then resolved individually, either
to the author's GitHub release or to an archived copy of the original file.

Every entry keeps its original curated metadata: name, version, author, description,
changelog, requirements, category, release date and download count. None of that can be
rebuilt from a repository.


[CATALOG.md](CATALOG.md) lists every entry with its author, version and download.

<!-- STATS -->
| | Entries | With a working download |
| --- | ---: | ---: |
| PSVITA homebrews | 1019 | 1019 |
| Plugins | 123 | 123 |
| PSP homebrews | 127 | 127 |
| PC tools | 27 | 27 |
| **Total** | **1296** | **1296 (100%)** |

The table above counts the catalog as it stood on 2026-07-31. Another 98 entries
have been added since, from VitaDB, from the authors themselves and from the wider
scene; those are listed separately in [ADDED.md](ADDED.md).

**31.5 GB** in total.

| Asset | Recovered |
| --- | ---: |
| Metadata | 100% (1296 entries) |
| Icons | 100% (1411) |
| Screenshots | 100% (2186 of 2186) |
| Trailers | 100% (62 of 62) |
| Data files | 100% (137 of 137) |
| In-game trophies | 100% (28 of 28 sets) |

Nothing is missing right now. [WANTED.md](WANTED.md) fills up again
if a link breaks or an entry turns up without one.
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
| `preserved/plugins.json` | plugin catalog |
| `preserved/tools.json` | PC tool catalog |
| `WANTED.md` | entries whose download is still missing |

The plugin and tool catalogs live under `preserved/` because the original client never listed
them, they were separate sections of the website. Same schema as the others, so a client can
read them the same way.

## Using this catalog

Every entry carries a direct download URL in its `url` field, so a client does not need a
redirect endpoint. Most point at a release asset on the author's own repository; what the
authors no longer host is mirrored here, either on the `mirror` release tag or, for small
files, served straight from GitHub Pages. A few sit on archive.org items. Every URL is
checked regularly and all of them answer.

Download counts are frozen at their 2026-07-31 values, because static hosting cannot count.
Sorting by popularity still works, it just describes the day the site went down.

Known consumers: [VitaForge](https://github.com/josephinoo/vitaForge) by josephinoo.
If you build another one, open an issue and it can be listed here.

## What is missing

Nothing. Every entry has a working download, and every screenshot, trailer, data file and
trophy set VitaDB carried is here. None of it still depends on the old webhost.

Themes are unaffected. They have always been hosted separately at
[CatoTheYounger97/vitaDB_themes](https://github.com/CatoTheYounger97/vitaDB_themes).

## Adding an entry

Open an [issue](https://github.com/DrDecki/VitaHomebrewDB/issues) with a link to the
release, or say so on [Discord](https://discord.gg/bwEVFMnDDA). Author, version and a
one-line description help, but a link on its own is fine. Everything else is read out of
the VPK.

Entries are added by hand, not automatically.

The scripts are in this repository: `add_app.py` adds an entry, `build_db.py` regenerates
`minimal.json` and `icons.zip`, `stats.py` and `mkindex.py` rewrite the README tables and
the listings, `mkwanted.py` rebuilds `WANTED.md`.

## Credits and takedowns

VitaDB was created and run by **Rinnegatamante**. The catalog is his work and that of every
homebrew author in it. This repository just keeps it reachable.

Thanks to **FundedBlade** for pointing at the GameBrew wiki and the PSP homebrew library on
archive.org, which closed over a hundred gaps, and to **josephinoo** for building
[VitaForge](https://github.com/josephinoo/vitaForge) against this catalog.

If you are an author and want your application removed, open an issue and it will be taken
down.

## License

The scripts in this repository (`build_db.py`, `add_app.py`, `stats.py`,
`mkwanted.py` and the rest) are MIT licensed, see [LICENSE](LICENSE). Use them
however you like.

The catalog itself is **not** covered by that license. Names, descriptions, changelogs, icons
and screenshots belong to Rinnegatamante and to the homebrew authors. This repository only
keeps them online and claims nothing. Clients are welcome to use the JSON files, and any
author who wants their work removed can open an issue.

If you build a client or another catalog on this data, please link back here. It is a request,
not a condition, since the metadata is not mine to license.

## Support

Spare-time project, free to use. If it saved you a homebrew you thought was gone, there is a
[Ko-fi](https://ko-fi.com/drdecki).
