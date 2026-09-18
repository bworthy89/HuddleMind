from pathlib import Path
from datetime import datetime
import zlib



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