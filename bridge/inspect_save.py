from pathlib import Path
from datetime import datetime
import zlib

def read_u32_be(data, offset):
    if offset < 0 or offset + 4 > len(data):
        raise ValueError("Four-byte read is outside the available data.")

    return int.from_bytes(data[offset:offset + 4], byteorder="big")

def read_table_summary(data, table_start):
    if table_start < 0 or table_start + 168 > len(data):
        raise ValueError("Table header is outside the available data.")

    if data[table_start + 148:table_start + 152] != b"SPBF":
        raise ValueError("Expected an SPBF table marker.")

    name_bytes = data[table_start:table_start + 128]
    name = name_bytes.split(b"\x00", 1)[0].decode("ascii")
    table_id = read_u32_be(data, table_start + 128)
    store_length = read_u32_be(data, table_start + 164)

    record_header = table_start + 168 + store_length

    if record_header + 56 > len(data):
        raise ValueError("Record header is outside the available data.")

    if data[record_header + 32:record_header + 36] != b"BSFT":
        raise ValueError("Expected a BSFT record-section marker.")

    return {
        "name": name,
        "table_id": table_id,
        "store_length": store_length,
        "record_header_start": record_header,
        "record_count": read_u32_be(data, record_header + 8),
        "record_capacity": read_u32_be(data, record_header + 48),
        "record_words": read_u32_be(data, record_header + 44),
        "field_count": read_u32_be(data, record_header + 52),
    }



save_file = Path(
    r"C:\Users\bwort\OneDrive\Documents\EA SPORTS College Football 27\saves"
) / "DYNASTY-TULANENEW-AUTOSAVE"

if not save_file.is_file():
    print("Save file not found:", save_file)
    raise SystemExit

with save_file.open("rb") as file:
    header = file.read(82)

if len(header) < 82:
    print("File is too short for the header fields we inspect.")
    raise SystemExit

if header[:8] != b"FBCHUNKS":
    print("Unexpected file signature:", header[:8])
    raise SystemExit

print("File size:", save_file.stat().st_size, "bytes")
print("Bytes read:", len(header))

for offset in range(0,  len(header), 16):
    row = header[offset:offset + 16]
    print(offset, ":", row.hex(" "))

name_bytes = header[34:62]
database_name = name_bytes.split(b"\x00", 1)[0].decode("ascii")

print("Database name:", database_name)

year_bytes = header[22:24]
year = int.from_bytes(year_bytes, "little")

print("Year bytes:", year_bytes.hex(" "))
print("Header year:", year)

month = int.from_bytes(header[24:26], byteorder="little")
day = int.from_bytes(header[26:28], byteorder="little")
hour = int.from_bytes(header[28:30], byteorder="little")
minute = int.from_bytes(header[30:32], byteorder="little")
second = int.from_bytes(header[32:34], byteorder="little")

print("Header date:", year, month, day)
print("Header time:", hour, minute, second)

save_timestamp = datetime(year, month, day, hour, minute, second)
print("Header timestamp:", save_timestamp)

schema_major = int.from_bytes(header[62:66], byteorder="little")
schema_minor = int.from_bytes(header[66:70], byteorder="little")

print("Schema major:", schema_major)
print("Schema minor:", schema_minor)

chunk_size = int.from_bytes(header[74:78], byteorder="little")
chunk_start = 82
chunk_end = chunk_start + chunk_size
file_size = save_file.stat().st_size

print("Candidate compressed size:", chunk_size)
print("Candidate chunk end:", chunk_end)
print("Fits within file:", chunk_end <= file_size)

if chunk_size < 2 or chunk_end > file_size:
    print("Invalid candidate chunk range.")
    raise SystemExit

with save_file.open("rb") as file:
    file.seek(chunk_start)
    chunk_prefix = file.read(2)

print("Candidate chunk prefix:", chunk_prefix.hex(" "))

with save_file.open("rb") as file:
    file.seek(chunk_start)
    compressed_data = file.read(chunk_size)

if len(compressed_data) != chunk_size:
    print("Could not read the complete candidate chunk.")
    raise SystemExit

decompressor = zlib.decompressobj()
output_limit = 64 * 1024 * 1024

try:
    unpacked_data = decompressor.decompress(
        compressed_data, output_limit
    )

except zlib.error as error:
    print("Decompression failed:", error)
    raise SystemExit

print("Decompressed bytes:", len(unpacked_data))

if not decompressor.eof:
    print("Decompression did not reach the end of the stream.")
    raise SystemExit

if decompressor.unused_data or decompressor.unconsumed_tail:
    print("Candidate Chunk did not match exactly one complete stream.")
    raise SystemExit

if unpacked_data[:4] != b"FrTk":
    print("Unexpected database signature:", unpacked_data[:4])
    raise SystemExit

print("Complete zlib stream and FrTk signature verified.")
print("Stream complete:", decompressor.eof)
print("Bytes after stream:", len(decompressor.unused_data))
print("Unprocessed input bytes:", len(decompressor.unconsumed_tail))
print("Decompressed prefix:", unpacked_data[:16])

database_header = unpacked_data[:128]

print("Decompressed database header:")

for offset in range(0, len(database_header), 16):
    row = database_header[offset:offset + 16]
    print(offset, ":", row.hex(" "))

field_bytes = database_header[44:48]

big_endian_value = int.from_bytes(field_bytes, byteorder="big")
little_endian_value = int.from_bytes(field_bytes, byteorder="little")

print("Bytes at offset 44:", field_bytes.hex(" "))
print("As big-endian:", big_endian_value)
print("As little-endian:", little_endian_value)
print("Matches outer schema major:", big_endian_value == schema_major)

inner_schema_major = read_u32_be(database_header, 44)
inner_schema_minor = read_u32_be(database_header, 40)

print("Outer schema:", schema_major, schema_minor)
print("Inner schema:", inner_schema_major, inner_schema_minor)

asset_table_offset = int.from_bytes(
    database_header[4:8], byteorder="big"
)
asset_entry_count = int.from_bytes(
    database_header[36:40], byteorder="big"
)

asset_table_end = asset_table_offset + asset_entry_count * 8

print("Candidate asset-table offset:", asset_table_offset)
print("Candidate asset entry count:", asset_entry_count)
print("Candidate asset-table end:", asset_table_end)
print("Fits within database:", asset_table_end <= len(unpacked_data))

if asset_table_offset < len(database_header) or asset_table_end > len(unpacked_data):
    print("Invalid candidate asset-table range.")
    raise SystemExit

print("First asset-reference entries:")

for index in range(min(5, asset_entry_count)):
    entry_offset = asset_table_offset + index * 8

    asset_id = int.from_bytes(
        unpacked_data[entry_offset:entry_offset + 4],
        byteorder="big",
    )
    reference = int.from_bytes(
        unpacked_data[entry_offset + 4:entry_offset + 8],
        byteorder="big",
    )

    table_id, row_number = divmod(reference, 2 ** 17)

    print(
        "Entry:", index,
        "| Asset ID:", asset_id,
        "| Table ID:", table_id,
        "| Row:", row_number,
    )

marker_offset = unpacked_data.find(b"SPBF", asset_table_end)

if marker_offset == -1:
    print("No SPBF marker found after the asset-reference area.")
    raise SystemExit

print("Candidate SPBF marker offset:", marker_offset)

sample_start = max(0, marker_offset - 32)
sample_end = min(len(unpacked_data), marker_offset + 64)

for offset in range(sample_start, sample_end, 16):
    row = unpacked_data[offset:min(offset + 16, sample_end)]
    print(offset, ":", row.hex(" "), "|", repr(row))


table_start = marker_offset - 148

if table_start < asset_table_end or table_start + 152 > len(unpacked_data):
    print("Invalid candidate table-header range.")
    raise SystemExit

table_name_bytes = unpacked_data[table_start:table_start + 128]
table_name = table_name_bytes.split(b"\x00", 1)[0].decode("ascii")

table_id = int.from_bytes(
    unpacked_data[table_start + 128:table_start + 132],
    byteorder="big",
)

print("Candidate table start:", table_start)
print("Candidate table name:", table_name)
print("Candidate table ID:", table_id)
print("Name-area length:", len(table_name_bytes))
print("Raw name area:", repr(table_name_bytes))
print("All name bytes zero:", all(value == 0 for value in table_name_bytes))

next_marker_offset = unpacked_data.find(b"SPBF", marker_offset + 4)

if next_marker_offset == -1:
    print("No further SPBF marker found.")
    raise SystemExit

next_table_start = next_marker_offset - 148

if next_table_start < asset_table_end or next_table_start + 152 > len(unpacked_data):
    print("Invalid next candidate table-header range.")
    raise SystemExit

next_name_bytes = unpacked_data[next_table_start:next_table_start + 128]
next_name = next_name_bytes.split(b"\x00", 1)[0].decode("ascii")

next_table_id = int.from_bytes(
    unpacked_data[next_table_start + 128:next_table_start + 132],
    byteorder="big",
)

print("Next candidate marker:", next_marker_offset)
print("Next candidate table start:", next_table_start)
print("Next candidate name:", repr(next_name))
print("Next candidate table ID:", next_table_id)

overall_summary = read_table_summary(unpacked_data, next_table_start)

store_length = overall_summary["store_length"]
record_header_start = overall_summary["record_header_start"]
record_count = overall_summary["record_count"]
record_capacity = overall_summary["record_capacity"]
record_words = overall_summary["record_words"]
field_count = overall_summary["field_count"]
record_size = record_words * 4

print("Candidate store-name length:", store_length)
print("Candidate record count:", record_count)
print("Candidate record capacity:", record_capacity)
print("Candidate record words:", record_words)
print("Candidate record size:", record_size, "bytes")
print("Candidate field count:", field_count)

record_data_start = (
    next_table_start
    + 232
    + store_length
    + field_count * 4
)
record_data_end = record_data_start + record_count * record_size

if record_data_end > len(unpacked_data):
    print("Candidate records extend beyond the database.")
    raise SystemExit

print("Candidate record-data start:", record_data_start)
print("Candidate record-data end:", record_data_end)

for row_number in range(min(3, record_count)):
    row_start = record_data_start + row_number * record_size
    record_bytes = unpacked_data[row_start:row_start + record_size]

    print("Row:", row_number, "| Raw bytes:", record_bytes.hex(" "))

field_metadata_start = next_table_start + 232 + store_length
field_metadata_end = field_metadata_start + field_count * 4

print("Field metadata starts:", field_metadata_start)
print("Field metadata ends:", field_metadata_end)
print("Meets record-data start:", field_metadata_end == record_data_start)

for field_index in range(field_count):
    descriptor_start = field_metadata_start + field_index * 4
    descriptor = unpacked_data[descriptor_start:descriptor_start + 4]

    print(
        "Field:", field_index,
        "| Descriptor bytes:", descriptor.hex(" "),
        "| As big-endian:", int.from_bytes(descriptor, byteorder="big"),
    )

if record_size != 8 or field_count !=2:
    print("This inspection expects two fields in an eight-byte record.")
    raise SystemExit

for row_number in range(min(3, record_count)):
    row_start = record_data_start + row_number * record_size
    record_bytes = unpacked_data[row_start:row_start + record_size]

    raw_field_0 = int.from_bytes(record_bytes[0:4], byteorder="big")
    raw_field_1 = int.from_bytes(record_bytes[4:8], byteorder="big")

    print(
        "Row:", row_number,
        "| Field 0 raw:", raw_field_0,
        "| Field 1 raw:", raw_field_1,
    )

    candidate_table_id, candidate_row = divmod(raw_field_0, 2 ** 17)

    print(
        "Possible reference:",
        "table:", candidate_table_id,
        "row", candidate_row,
    )

target_table_id = 5176
search_offset = asset_table_end
target_table_start = None

while True:
    found_marker = unpacked_data.find(b"SPBF", search_offset)

    if found_marker == -1:
        break

    search_offset = found_marker + 4
    candidate_start = found_marker - 148

    if candidate_start < asset_table_end:
        continue

    found_id = int.from_bytes(
        unpacked_data[candidate_start + 128:candidate_start + 132],
        byteorder="big",
    )

    if found_id == target_table_id:
        target_table_start = candidate_start
        break

if target_table_start is None:
    print("Target table not found amoung SPBF candidates.")
else:
    target_name_bytes = unpacked_data[
        target_table_start:target_table_start + 128
    ]

    print("Target candidate start:", target_table_start)
    print("Target candidate ID:", target_table_id)
    print("Target raw name:", repr(target_name_bytes.split(b"\x00", 1)[0]))

if target_table_start is None:
    raise SystemExit

spline_summary = read_table_summary(unpacked_data, target_table_start)

print("Target table name:", spline_summary["name"])
print("Target table ID:", spline_summary["table_id"])
print("Target record count:", spline_summary["record_count"])
print("Target record capacity:", spline_summary["record_capacity"])
print(
    "Rows 0–2 fit declared capacity:",
    spline_summary["record_capacity"] >= 3,
)

print("Overall summary:", overall_summary)
print("Spline summary:", spline_summary)