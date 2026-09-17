import time

from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Lock

class SaveEventHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.pending_changes = {}
        self.pending_lock = Lock()

    def queue_change(self, file_path):
        changed_file = Path(file_path)

        if not changed_file.name.startswith("DYNASTY-"):
            return

        with self.pending_lock:
            self.pending_changes[changed_file] = time.monotonic()

    def on_created(self, event):
        if not event.is_directory:
                self.queue_change(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self.queue_change(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self.queue_change(event.dest_path)

    def process_pending_changes(self):
        now = time.monotonic()
        ready_files = []

        with self.pending_lock:
            for file_path, last_changed in self.pending_changes.items():
                if now - last_changed >= 1.0:
                    ready_files.append(file_path)

            for file_path in ready_files:
                del self.pending_changes[file_path]

        for file_path in ready_files:
            try:
                details = file_path.stat()
            except FileNotFoundError:
                print("File disappeared before checking:", file_path.name)
                continue

            print(
                "File event:", file_path.name,
                "| Modified:", details.st_mtime_ns,
                "| Bytes:", details.st_size,
            )

watch_folder = Path(
    r"C:\Users\bwort\OneDrive\Documents\EA SPORTS College Football 27\saves"
)

if not watch_folder.is_dir():
    print("Save folder not found:", watch_folder)
    raise SystemExit

handler = SaveEventHandler()
observer = Observer()

observer.schedule(handler, str(watch_folder), recursive=False)
observer.start()

print("Watching:", watch_folder)
print("Press Ctrl+C to stop.")

try:
    while True:
        handler.process_pending_changes()
        time.sleep(0.1)
except KeyboardInterrupt:
    observer.stop()

observer.join()