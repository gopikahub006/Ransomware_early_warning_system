import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

RISK_MAP = {
    "created": 1,
    "modified": 2,
    "deleted": 10,
    "moved": 25
}

class FileEventHandler(FileSystemEventHandler):
    def __init__(self, event_queue):
        self.event_queue = event_queue

    def on_created(self, event):
        self.push_event("File_Created", event.src_path, 1)

    def on_modified(self, event):
        self.push_event("File_Modified", event.src_path, 2)

    def on_deleted(self, event):
        self.push_event("File_Deleted", event.src_path, 10)

    def on_moved(self, event):
        self.push_event("File_Renamed", event.dest_path, 25)

    def push_event(self, etype, file, risk):
        self.event_queue.put({
            "timestamp": time.time(),
            "type": etype,
            "file": file,
            "risk": risk
        })


class RealFileMonitor(threading.Thread):
    def __init__(self, path, event_queue):
        super().__init__(daemon=True)
        self.path = path
        self.event_queue = event_queue
        self.observer = Observer()

    def run(self):
        handler = FileEventHandler(self.event_queue)
        self.observer.schedule(handler, self.path, recursive=True)
        self.observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()

    def stop(self):
        self.observer.stop()
        self.observer.join()
