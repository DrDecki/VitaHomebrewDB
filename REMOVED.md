# Removed entries

Entries listed here were in the catalog and were removed on purpose.
`watch_vitadb.py` keeps their VitaDB ids in `NIGHTLY_ONLY` so the daily
report does not suggest them again.

## Nightly-only builds, removed 2026-09-14

A nightly URL always serves the newest build, so the catalog cannot
describe a defined state: the stored hash is stale within hours, no
client can tell whether an update is due, and users report bugs that
were fixed weeks ago. The developer of Nazi Zombies Portable asked for
his entry to be removed for these reasons; the same applies to the rest.

| VitaDB id | Name |
| --- | --- |
| 186 | RetroArch |
| 405 | ScummVM Buildbot |
| 553 | Daedalus X64 |
| 815 | YoYo Loader Vita |
| 910 | Nazi Zombies Portable: Reboot (PSP) |
| 1028 | Nazi Zombies Portable |
| 1093 | NooDS |
| 1504 | Jazz² Resurrection |

Entries with a tagged release stay in the catalog even when the author
also publishes nightlies. vita-savemgr was moved to its 2.0.0 release
instead of being removed.

If any of these projects starts publishing tagged releases with a Vita
build attached, remove its id from `NIGHTLY_ONLY` and add the entry back.
