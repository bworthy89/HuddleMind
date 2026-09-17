from pathlib import Path
from datetime import datetime

def find_dynasty_files(save_folder):
    dynasty_files = []

    for item in save_folder.iterdir():
        if item.is_file() and item.name.startswith("DYNASTY-"):
            dynasty_files.append(item)

    return dynasty_files

save_folder = Path(r"C:\Users\bwort\OneDrive\Documents\EA SPORTS College Football 27\saves")

print("Save folder:", save_folder)

if not save_folder.is_dir():
    print("Save folder not found:", save_folder)
    raise SystemExit

dynasty_files = find_dynasty_files(save_folder)

for item in dynasty_files:
    modified_time = item.stat().st_mtime
    modified_date = datetime.fromtimestamp(modified_time)
    print(item.name, "- Last modified:", modified_date)

print("Dynasty saves found:", len(dynasty_files))

if dynasty_files:
    newest_save = dynasty_files[0]

    for save in dynasty_files:
        if save.stat().st_mtime > newest_save.stat().st_mtime:
            newest_save = save
    print("Most recently modified:", newest_save.name)
else:
    print("No dynasty saves found.")





