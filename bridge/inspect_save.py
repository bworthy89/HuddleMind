from pathlib import Path
from datetime import datetime
import zlib
# ElementTree reads XML documents using Pythons standard Library.
import xml.etree.ElementTree as ET

def read_u32_be(data, offset):
    if offset < 0 or offset + 4 > len(data):
        raise ValueError("Four-byte read is outside the available data.")

    return int.from_bytes(data[offset:offset + 4], byteorder="big")

def decode_candidate_int_array_value(raw_value):
    #Accept only values that fit in one unsigned 32-bit word.
    if not 0 <= raw_value < 2 ** 32:
        raise ValueError("Array value is outside the unsigned 32-bit range")

    #The reference parser preserves raw zero in its int[] decoding branch.
    if raw_value == 0:
        return 0

    #Remove the bias used by the reference parser's 32-bit int[] branch.
    #Applying this rule to our table still depends on its schema settings.
    return raw_value - (2 ** 31)

def read_position_members(schema_path):
    # Parse the local XML export without modifying the file.
    schema_tree = ET.parse(schema_path)
    schema_root = schema_tree.getroot()

    # Select PositionE explicitly rather than taking the first enum.
    position_enum = schema_root.find(
        "./schemas/enum[@name='PositionE']"
    )

    # Stop if the file does not contain the expected enum.
    if position_enum is None:
        raise ValueError("PositionE enum not found in the schema.")

    # Return the member elements for further processing.
    return position_enum.findall("attribute")

def group_position_names(position_members):
    # Group names by stored enum value without discarding aliases.
    # The caller supplies the member elements from the PositionE XML.
    names_by_value = {}

    for member in position_members:
        position_name = member.get("name")

        # Reject missing or blank names before building the alias groups.
        # A missing XML attribute returns None; a present name is a string
        if position_name is None or  not position_name.strip():
            raise ValueError("PositionE member has a missing or blank name.")

        # Convert the XML value to an integer for matching save data.
        # Missing values produce TypeError; invalid numeric text produces ValueError.
        try:
            position_value = int(member.get("value"))
        except (TypeError, ValueError) as error:
            # Include the member name so a malformed entry is easy to locate.
            raise ValueError(
                f"PositionE member {position_name!r} has a missing or invalid integer value."
            ) from error

        # Each value gets its own list of names.
        if position_value not in names_by_value:
            names_by_value[position_value] = []

        names_by_value[position_value].append(position_name)

    # Return the completed groups for inspection and label selection.
    return names_by_value



def build_position_labels(names_by_value):
    # Apply our PositionE display policy without changing the alais groups.
    labels = {}

    for position_value, names in names_by_value.items():
        # Exclude trailing-underscore aliases and boundry markers.
        display_names = [
            name
            for name in names
            if not name.endswith("_")
        ]

        # Leave missing or ambiguous choices unmapped.
        # The caller can then use its Unknown (...) fallback.
        if len(display_names) == 1:
            labels[position_value] = display_names[0]

    return labels

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

# Keep each sampled OverallPercentage record's position and SPline link.
# Key by source row so seperate records remain separate.
overall_links = {}

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

    # The exported schema identifies field 0 as PercentageSpline
    # and field 1 as the PlayerPosition enum value.
    overall_links[row_number] = {
        "position_value": raw_field_1,
        "spline_reference": (candidate_table_id, candidate_row)
    }

    print(
        "Possible reference:",
        "table:", candidate_table_id,
        "row", candidate_row,
    )
# Display the associations collected from the sampled source records.
print("Collected OverallPercentage links:", overall_links)

# Read the locally exported PositionE schema without modifying it.
# This path is specific to the current development PC.
position_schema_path = Path(r"E:\aibridgemod\positionE.FTX")

# Load the enum members through the reusable XML reader
position_members = read_position_members(position_schema_path)
print("Parsed enum members:", len(position_members))

# Preserve all names and aliases using the reusable grouping helper.
position_names_by_value = group_position_names(position_members)

# Inspect the groups used by our three sampled OverallPercentage records.
for position_value in (16, 7, 12):
    print(
        "Position names:",
        position_value,
        "->",
        position_names_by_value.get(position_value, [])
    )


# Select unambiguous display labels while retaining the original alias groups.
position_labels = build_position_labels(position_names_by_value)



# Label each source record while preserving its actual SPline reference.
for overall_row, link in overall_links.items():
    position_value = link["position_value"]
    spline_table, spline_row = link["spline_reference"]

    # Keep unrecognized values visible instead of guessing a position.
    position_label = position_labels.get(
        position_value,
        f"Unknown ({position_value})"
    )

    print(
        "OverallPercentage row:", overall_row,
        "| Position:", position_label,
        "| Spline table:", spline_table,
        "| Spline row:", spline_row,
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

spline_metadata_start = (
    target_table_start + 232 + spline_summary["store_length"]
)
spline_metadata_end = (
    spline_metadata_start + spline_summary["field_count"] * 4
)

if spline_metadata_end > len(unpacked_data):
    print("Spline field metadata extends beyond the database.")
    raise SystemExit

print("Spline field metadata starts:", spline_metadata_start)
print("Spline field metadata ends", spline_metadata_end)

for field_index in range(spline_summary["field_count"]):
    descriptor_offset = spline_metadata_start + field_index * 4
    bit_offset = read_u32_be(unpacked_data,descriptor_offset)

    print("Spline field:", field_index, "| Descriptor bit offset:", bit_offset)

spline_record_size = spline_summary["record_words"] * 4
spline_record_start = spline_metadata_end
spline_record_end = (
    spline_record_start
    + spline_summary["record_count"] * spline_record_size
)

if spline_record_size != 8 or spline_record_end > len(unpacked_data):
    print("Unexpected Spline record size of range.")
    raise SystemExit

print("Candidate Spline record start:", spline_record_start)
print("Candidate Spline record end:", spline_record_end)

#Keep each sampled Spline row's X/Y references for Later array Lookup.
#Store both table IDs androw numbers so we can check the destination.
spline_references = {}

for row_number in range(min(3, spline_summary["record_count"])):
    row_start = spline_record_start + row_number * spline_record_size
    record_bytes = unpacked_data[row_start:row_start + spline_record_size]

    print(
        "Spline row:", row_number,
        "| Raw bytes:", record_bytes.hex(" "),
        "| First u32:", read_u32_be(record_bytes, 0),
        "| Second u32:", read_u32_be(record_bytes, 4),
    )

    #In this spline layout, Y starts at bit 0 and X starts at bit 32.
    #Each reference occupies one complete four-byte word.
    #CacuculateY is marked final in the schema and is skipped.

    y_reference = read_u32_be(record_bytes, 0)
    x_reference = read_u32_be(record_bytes, 4)

    #split each reference into its table ID and 17-bit row number.
    y_table, y_row = divmod(y_reference, 2 ** 17)
    x_table, x_row = divmod(x_reference, 2 ** 17)
    spline_references[row_number] = {
        "x": (x_table, x_row),
        "y": (y_table, y_row),
    }

    print("Spline X reference:", "table", x_table, "row", x_row)
    print("Spline Y reference:", "table", y_table, "row", y_row)

# Show the collected references once, after all sampled rows are read.
print("Collected Spline references:", spline_references)

linked_table_start = None
search_offset = asset_table_end

while True:
    found_marker = unpacked_data.find(b"SPBF", search_offset)

    if found_marker == -1:
        break

    search_offset = found_marker + 4
    candidate_start = found_marker - 148

    if candidate_start < asset_table_end:
        continue

    candidate_id = read_u32_be(unpacked_data, candidate_start +128)

    if candidate_id == 4722:
        linked_table_start = candidate_start
        break

if linked_table_start is None:
    print("Candidate table 4722 was not found.")
else:
    linked_summary = read_table_summary(unpacked_data, linked_table_start)
    print("Linked table start:", linked_table_start)
    print("Linked table summary:", linked_summary)
    print(
        "Rows 0-5 fit declared capacity:",
        linked_summary["record_capacity"] >= 6,
    )
for marker in (b"ASTO", b"SPEX"):
    search_offset = asset_table_end

    while True:
        found_marker = unpacked_data.find(marker, search_offset)

        if found_marker == -1:
            break

        search_offset = found_marker + 4
        candidate_start = found_marker - 148

        if candidate_start < asset_table_end:
            continue

        candidate_id = read_u32_be(unpacked_data, candidate_start + 128)

        if candidate_id == 4722:
            name_bytes = unpacked_data[candidate_start:candidate_start + 128]

            print("Alternate candidate marker:", marker)
            print("Alternate candidate start:", candidate_start)
            print("Alternate candidate ID:", candidate_id)
            print("Alternate candidate name:", name_bytes.split(b"\x00", 1)[0])
            candidate_store_length = read_u32_be(
                unpacked_data, candidate_start + 164
            )
            candidate_record_header = (
                candidate_start + 168 + candidate_store_length
            )

            print("Alternate store length:", candidate_store_length)
            print("Alternate record-header start:", candidate_record_header)
            print(
                "Alternate record-section marker:",
                unpacked_data[
                    candidate_record_header + 32:
                    candidate_record_header + 36
                ],
            )

            print("Alternate record-header bytes:")

            for relative_offset in range(0, 64, 16):
                start = candidate_record_header + relative_offset
                header_bytes = unpacked_data[start:start + 16]

                print(
                    relative_offset, ":",
                    header_bytes.hex(" "),
                    "|", repr(header_bytes),
                )

            array_record_count = read_u32_be(
                unpacked_data, candidate_record_header + 8
            )
            array_record_capacity = read_u32_be(
                unpacked_data, candidate_record_header + 48
            )
            array_record_words = read_u32_be(
                unpacked_data, candidate_record_header + 44
            )

            print("Candidate array record count:", array_record_count)
            print("Candidate array capacity:", array_record_capacity)
            print("Candidate array record words:", array_record_words)
            print(
                "Spline reference rows 0–5 fit capacity:",
                array_record_capacity >= 6,
            )

            array_entries_start = candidate_record_header + 64
            array_entries_end = (
                array_entries_start + array_record_count * 4
            )

            array_record_size = array_record_words * 4
            array_records_start = array_entries_end
            array_records_end = (
                array_records_start
                + array_record_count * array_record_size
            )

            print("Candidate array entries start:", array_entries_start)
            print("Candidate array entries end:", array_entries_end)
            print("Candidate array record size:", array_record_size)
            print("Candidate array records start:", array_records_start)
            print("Candidate array records end:", array_records_end)
            print(
                "Candidate array records fit database:",
                array_records_end <= len(unpacked_data),
            )

            if not (
                0 <= array_entries_start
                <= array_entries_end
                <= len(unpacked_data)
            ):
                raise SystemExit("Candidate array entries are outside the database.")

            for array_row in range(min(6, array_record_count)):
                entry_start = array_entries_start + array_row * 4
                entry_bytes = unpacked_data[entry_start:entry_start + 4]
                entry_value = read_u32_be(unpacked_data, entry_start)

                print(
                    "Array entry:", array_row,
                    "| Raw bytes:", entry_bytes.hex(" "),
                    "| As big-endian:", entry_value,
                )

            if not (
                0 <= array_records_start
                <= array_records_end
                <= len(unpacked_data)
            ):
                raise SystemExit("Candidate array records are outside the database.")

            #Keep each sampled array under its row number for Later Lookup
            decoded_array_rows = {}
            # Load the six array rows used by our three sampled Splines.
            for array_row in range(min(6, array_record_count)):
                row_start = (
                    array_records_start + array_row * array_record_size
                )

                raw_values = []

                for word_index in range(array_record_words):
                    word_start = row_start + word_index * 4
                    raw_values.append(
                        read_u32_be(unpacked_data, word_start)
                    )

                print("Candidate array row:", array_row, "| Raw u32 values:", raw_values)

                #Decode each word using the candidate int[] conversion.
                #The helper preserves raw zero and removes the bias otherwise.
                #Keep raw_vales unchanged for comparison.
                candidate_values = [
                    decode_candidate_int_array_value(value)
                    for value in raw_values
                ]

                #Store this decoded row without changing its raw values
                decoded_array_rows[array_row] = candidate_values

                print(
                    "Candidate array row:", array_row,
                    "| Candidate decoded values:", candidate_values,
                )

            # Follow each sampled Spline row's saved X/Y references:
            for spline_row, references in spline_references.items():
                current_spline_reference = (
                    spline_summary["table_id"],
                    spline_row,
                )

                # Find sampled OverallPercentage records thar reference it.
                # Keep a list because multiple records could share a SPline.
                linked_positions = []

                for link in overall_links.values():
                    if link["spline_reference"] == current_spline_reference:
                        position_value = link["position_value"]
                        linked_positions.append(
                            position_labels.get(
                                position_value,
                                f"Unknown ({position_value})"
                            )
                        )

                # A missing sampled link does not mean the Spline is unused.
                position_text = (
                    ",".join(linked_positions)
                    if linked_positions
                    else "No sampled position link"
                )


                x_table, x_row = references["x"]
                y_table, y_row = references["y"]

                # The decoded arrays belong to this candidate table.
                # A row number alone is not enough to identify a record.
                if x_table != candidate_id or y_table != candidate_id:
                    print("Skipping Spline row:", spline_row, "| Different target table")
                    continue

                # Only six array rows are currently loaded for inspection.
                # An unloaded row is not necessarily an invalid reference.
                if x_row not in decoded_array_rows or y_row not in decoded_array_rows:
                    print("Skipping Spline row:", spline_row, "| Target row not loaded")
                    continue

                x_values = decoded_array_rows[x_row]
                y_values = decoded_array_rows[y_row]

                # Prevent zip from silently dropping unmatched elements.
                if len(x_values) != len(y_values):
                    raise ValueError(
                        f"Spline row {spline_row}: X and Y lengths do not match."
                    )

                # Report whether the sampled X values strictly increase.
                # This does not implement interpolation.

                x_is_strictly_increasing = all(
                    current_x < next_x
                    for current_x, next_x in zip(x_values, x_values[1:])
                )

                print(
                    "Candidate Spline Row:", spline_row,
                    "| Position:", position_text,
                    "| X array row:", x_row,
                    "| Y array row:", y_row,
                    "| X strictly increasing:", x_is_strictly_increasing,
                )

                for x_value, y_value in zip(x_values, y_values):
                    print("X:", x_value, "| Y:", y_value)
