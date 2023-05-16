import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import shutil


class Watcher:
    DIRECTORY_TO_WATCH = "H:\\NetCode"
    # dist_dir = "C:\\listener"

    def __init__(self):
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except:
            self.observer.stop()
            print ("Error")

        self.observer.join()


class Handler(FileSystemEventHandler):

    @staticmethod
    def on_any_event(event):
        dist_dir = "C:\\listener"
        if event.is_directory:
            return None

        elif event.event_type == 'created':
            # Take any action here when a file is first created.
            print ("Received created event - %s." % event.src_path)

        elif event.event_type == 'modified':
            # Taken any action here when a file is modified.
            filename = os.path.basename(event.src_path)
            dist = os.path.join(dist_dir, filename)
            if '.bmp' not in dist:
                try:
                    shutil.copy(event.src_path, dist)
                except Exception as e:
                    print(e)
            print ("Received modified event - %s." % event.src_path)


if __name__ == '__main__':
    w = Watcher()
    w.run()