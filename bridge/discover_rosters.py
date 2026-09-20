"""Read-only research probe for schema-backed team names and roster references.

This deliberately decodes only whole-word fields. Packed fields and occupancy
need separate validation before this becomes an application adapter.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import zlib


def u32(data, offset):
    if offset < 0 or offset + 4 > len(data):
        raise ValueError("Integer outside available data")
    return int.from_bytes(data[offset:offset + 4], "big")


def table(data, start):
    if start < 0 or start + 168 > len(data):
        raise ValueError("Truncated table header")
    marker = data[start + 148:start + 152]
    if marker not in (b"SPBF", b"ASTO"):
        raise ValueError("Unsupported table marker")
    header = start + 168 + u32(data, start + 164)
    section = data[header + 32:header + 36]
    if section not in (b"BSFT", b"CMPC"):
        raise ValueError("Unsupported record marker")
    count, words, fields = (u32(data, header + i) for i in (8, 44, 52))
    metadata = header + 64
    records = metadata + 4 * (count if marker == b"ASTO" else fields)
    strings = records + count * words * 4
    string_end = strings + u32(data, header + 20)
    if string_end > len(data):
        raise ValueError("Table data exceeds database")
    return dict(name=data[start:start + 128].split(b"\0")[0].decode("ascii"),
                id=u32(data, start + 128), count=count, words=words,
                fields=fields, metadata=metadata, records=records,
                strings=strings, string_end=string_end, marker=marker.decode())


def word_field(data, info, attributes, row, name):
    if not 0 <= row < info["count"] or len(attributes) != info["fields"]:
        raise ValueError("Row or schema member count mismatch")
    index = next(i for i, item in enumerate(attributes) if item["name"] == name)
    offset = u32(data, info["metadata"] + index * 4)
    offsets = [u32(data, info["metadata"] + i * 4) for i in range(len(attributes))]
    following = min((x for x in offsets if x > offset), default=info["words"] * 32)
    if offset % 32 or following - offset < 32 or offset + 32 > info["words"] * 32:
        raise ValueError(f"{name} is not an isolated whole-word field")
    value = u32(data, info["records"] + row * info["words"] * 4 + offset // 8)
    attribute = attributes[index]
    if attribute["type"] == "string":
        # String words point into this table's secondary byte section.
        start = info["strings"] + value
        if start < info["strings"] or start >= info["string_end"]:
            raise ValueError("String pointer outside secondary section")
        end = min(start + int(attribute["maxLength"]), info["string_end"])
        return data[start:end].split(b"\0")[0].decode("utf-8")
    return value


def inspect(save, schema):
    raw = save.read_bytes()  # One snapshot; never open a game save for writing.
    if len(raw) < 82 or raw[:8] != b"FBCHUNKS":
        raise ValueError("Not a supported save header")
    size = int.from_bytes(raw[74:78], "little")
    if 82 + size > len(raw):
        raise ValueError("Truncated compressed chunk")
    decoder = zlib.decompressobj()
    data = decoder.decompress(raw[82:82 + size], 64 * 1024 * 1024)
    if not decoder.eof or decoder.unused_data or decoder.unconsumed_tail or data[:4] != b"FrTk":
        raise ValueError("Incomplete or unsupported database chunk")
    schemas = {s["name"]: s for s in json.loads(gzip.decompress(schema.read_bytes()))["schemas"]}
    candidates = {}
    # Marker searching remains a discovery technique, not a table directory parser.
    for marker in (b"SPBF", b"ASTO"):
        cursor = 0
        while (cursor := data.find(marker, cursor)) >= 0:
            try:
                info = table(data, cursor - 148)
                candidates.setdefault(info["id"], []).append(info)
            except (ValueError, UnicodeError):
                pass
            cursor += 4
    teams = []
    for choices in candidates.values():
        for info in choices:
            if info["name"] != "Team":
                continue
            for row in range(info["count"]):
                attrs = schemas["Team"]["attributes"]
                record = {key: word_field(data, info, attrs, row, key)
                          for key in ("DisplayName", "LongName", "Roster")}
                target_id, target_row = divmod(record.pop("Roster"), 1 << 17)
                record.update(table=info["id"], row=row, roster_table=target_id, roster_row=target_row)
                targets = candidates.get(target_id, [])
                if len(targets) == 1 and targets[0]["name"] == "Player[]":
                    target = targets[0]
                    if target["marker"] != "ASTO" or target_row >= target["count"]:
                        raise ValueError("Invalid roster array reference")
                    length = u32(data, target["metadata"] + target_row * 4)
                    if length > target["words"]:
                        raise ValueError("Roster length exceeds row capacity")
                    players = []
                    for slot in range(length):
                        reference = u32(data, target["records"] + (target_row * target["words"] + slot) * 4)
                        if reference == 0:
                            continue
                        player_id, player_row = divmod(reference, 1 << 17)
                        tables = candidates.get(player_id, [])
                        if len(tables) != 1 or tables[0]["name"] != "Player":
                            raise ValueError("Ambiguous or missing Player target")
                        player = {key: word_field(data, tables[0], schemas["Player"]["attributes"], player_row, key)
                                  for key in ("FirstName", "LastName")}
                        player.update(table=player_id, row=player_row)
                        players.append(player)
                    record["players"] = players
                teams.append(record)
    return dict(save_sha256=hashlib.sha256(raw).hexdigest(),
                schema_sha256=hashlib.sha256(schema.read_bytes()).hexdigest(),
                caveat="Candidate rows; occupancy and packed fields not yet verified", teams=teams)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("save", type=Path)
    parser.add_argument("schema", type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect(args.save, args.schema), indent=2))
