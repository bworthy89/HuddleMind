from pathlib import Path
from datetime import datetime

save_file = Path(
    r"C:\Users\bwort\OneDrive\Documents\EA SPORTS College Football 27\saves"
) / "DYNASTY-TULANENEW-AUTOSAVE"

if not save_file.is_file():
    print("Save file not found:", save_file)
    raise SystemExit

with save_file.open("rb") as file:
    header = file.read(64)

if len(header) < 64:
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