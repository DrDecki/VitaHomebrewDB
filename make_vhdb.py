import json
import os
import struct
import sys
import zlib
from collections import Counter, defaultdict
from datetime import date

REPO = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(REPO, "vhdb.bin")

MAGIC = b"VHDB"
FORMAT_VERSION = 1
HEADER_SIZE = 64
RECORD_SIZE = 128

FLAG_TROPHIES = 1 << 0
FLAG_HAS_DATA = 1 << 1
FLAG_HAS_SHOTS = 1 << 2
FLAG_HAS_TRAILER = 1 << 3
FLAG_HASH2 = 1 << 4

SOURCES = [
    ("apps.json", 0, "vita"),
    ("psp_apps.json", 1, "psp"),
    (os.path.join("preserved", "plugins.json"), 2, "plugin"),
    (os.path.join("preserved", "tools.json"), 3, "tool"),
]


class StringBlob:
    def __init__(self):
        self.buf = bytearray(b"\x00")
        self.seen = {"": 0}

    def add(self, value):
        if value is None:
            value = ""
        value = str(value)
        if value in self.seen:
            return self.seen[value]
        offset = len(self.buf)
        self.buf += value.encode("utf-8") + b"\x00"
        self.seen[value] = offset
        return offset


def load_catalog(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, dict):
        return list(data.values())
    return data


def to_int(value, fallback=0):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return fallback


def pack_date(value):
    text = (value or "").strip()
    if len(text) != 10:
        return 0
    try:
        parts = text.replace("/", "-").split("-")
        return int(parts[0]) * 10000 + int(parts[1]) * 100 + int(parts[2])
    except (IndexError, ValueError):
        return 0


def pack_md5(value):
    text = (value or "").strip().lower()
    if len(text) != 32:
        return b"\x00" * 16, False
    try:
        return bytes.fromhex(text), True
    except ValueError:
        return b"\x00" * 16, False


def pack_titleid(value):
    raw = (value or "").strip().encode("ascii", "ignore")[:12]
    return raw + b"\x00" * (12 - len(raw))


def build():
    blob = StringBlob()
    records = []
    meta = []
    per_platform = Counter()
    per_type = defaultdict(list)
    missing = []

    for filename, platform, label in SOURCES:
        path = os.path.join(REPO, filename)
        entries = load_catalog(path)
        if entries is None:
            missing.append(filename)
            continue
        for entry in entries:
            get = entry.get
            flags = 0
            if to_int(get("trophies")) > 0:
                flags |= FLAG_TROPHIES
            if (get("data") or "").strip():
                flags |= FLAG_HAS_DATA
            if (get("screenshots") or "").strip():
                flags |= FLAG_HAS_SHOTS
            if (get("trailer") or "").strip():
                flags |= FLAG_HAS_TRAILER

            hash1, _ = pack_md5(get("hash"))
            hash2, valid2 = pack_md5(get("hash2"))
            if valid2:
                flags |= FLAG_HASH2

            fields = [
                blob.add(get("name")),
                blob.add(get("author")),
                blob.add(get("version")),
                blob.add(get("icon")),
                blob.add(get("description")),
                blob.add(get("long_description")),
                blob.add(get("changelog")),
                blob.add(get("requirements")),
                blob.add(get("needs")),
                blob.add(get("url")),
                blob.add(get("data")),
                blob.add(get("source")),
                blob.add(get("release_page")),
                blob.add(get("trailer")),
                blob.add(get("screenshots")),
                blob.add(get("tags")),
                to_int(get("size")),
                to_int(get("data_size")),
                pack_date(get("date")),
                to_int(get("id")),
            ]

            record = struct.pack(
                "<20I12s16s16sBBBB",
                *fields,
                pack_titleid(get("titleid")),
                hash1,
                hash2,
                to_int(get("type")) & 0xFF,
                flags,
                platform,
                0,
            )
            if len(record) != RECORD_SIZE:
                raise SystemExit("record size is %d, expected %d" % (len(record), RECORD_SIZE))

            records.append(record)
            meta.append(((get("name") or "").lower(), pack_date(get("date"))))
            per_platform[label] += 1
            if platform == 0:
                per_type[to_int(get("type"))].append(get("name") or "")

    count = len(records)
    if count == 0:
        raise SystemExit("no entries found, run this inside the catalogue checkout")

    order_name = sorted(range(count), key=lambda i: (meta[i][0], i))
    order_date = sorted(range(count), key=lambda i: (-meta[i][1], meta[i][0]))

    record_block = b"".join(records)
    string_block = bytes(blob.buf)
    index_name = struct.pack("<%dI" % count, *order_name)
    index_date = struct.pack("<%dI" % count, *order_date)

    records_off = HEADER_SIZE
    strings_off = records_off + len(record_block)
    idx_name_off = strings_off + len(string_block)
    if idx_name_off % 4:
        pad = 4 - (idx_name_off % 4)
        string_block += b"\x00" * pad
        idx_name_off += pad
    idx_date_off = idx_name_off + len(index_name)

    body = record_block + string_block + index_name + index_date
    catalog_hash = zlib.crc32(body) & 0xFFFFFFFF

    today = date.today()
    built = today.year * 10000 + today.month * 100 + today.day

    header = struct.pack(
        "<4s10I",
        MAGIC,
        FORMAT_VERSION,
        built,
        count,
        RECORD_SIZE,
        records_off,
        strings_off,
        len(string_block),
        idx_name_off,
        idx_date_off,
        catalog_hash,
    )
    header += b"\x00" * (HEADER_SIZE - len(header))

    with open(OUT, "wb") as handle:
        handle.write(header)
        handle.write(body)

    total = HEADER_SIZE + len(body)
    print("wrote %s" % OUT)
    print("entries      %d" % count)
    print("records      %d bytes" % len(record_block))
    print("strings      %d bytes" % len(string_block))
    print("indexes      %d bytes" % (len(index_name) + len(index_date)))
    print("total        %d bytes (%.2f MB)" % (total, total / 1048576.0))
    print("catalog_hash %08x" % catalog_hash)
    if missing:
        print("skipped      %s" % ", ".join(missing))
    print("platforms    %s" % dict(per_platform))
    print("")
    print("vita type values, three names each:")
    for key in sorted(per_type):
        sample = ", ".join(per_type[key][:3])
        print("  type %d  %4d entries  %s" % (key, len(per_type[key]), sample))


if __name__ == "__main__":
    build()
    sys.exit(0)
