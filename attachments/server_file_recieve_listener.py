import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import pymongo
from datetime import datetime, timedelta

db = pymongo.MongoClient('localhost')['ERP']
coll = db['file_listener']

class Watcher:
    DIRECTORY_TO_WATCH = "H:\\web_scan"

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
            print("Error")

        self.observer.join()


class Handler(FileSystemEventHandler):

    @staticmethod
    def on_any_event(event):
        dist_dir = "C:\\listener"
        if event.is_directory:
            return None
        elif event.event_type == 'created':
            # Take any action here when a file is first created.
            filename = os.path.basename(event.src_path)
            if filename[-4:] == '.pdf':
                username = filename.replace('.pdf', '')
                Handler.save_file(username, event.src_path)
        # elif event.event_type == 'modified':
            # Taken any action here when a file is modified.

    @staticmethod
    def save_file(username, f, description=''):
        attach_dir = 'C:\\Server\\attachments\\orders'
        temp = mongo.read_collection_one('file_listener', {'username': username})
        if 'order_id' in temp:
            if temp['timestamp'] < (datetime.now() - timedelta(minutes=2)):
                print('outdated')
                return
            order_id = temp['order_id']
        else:
            print(username, ' :user not found')
            return
        # f = main.request.files['file']
        file_dir = os.path.join(attach_dir, order_id)
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
        # file_name = main.secure_filename(f.filename)
        file_name = f.filename
        file = os.path.join(file_dir, file_name)
        if os.path.exists(file):
            file = Handler.uniquify(file)
        f.save(file)
        doc = {'name': file_name, 'timestamp': Handler.ts(), 'user': username, 'id': Handler.gen_file_id(),
               'description': description, 'link': file, 'order_id': order_id}
        db['attachments'].insert_one(doc)

    @staticmethod
    def gen_file_id():
        new_id = 1
        # query[sort_by] = {'$exists': True}
        dic = db['attachments'].find_one({'id': {'$exists': True}}, {'_id': False}, sort=[(sort_by, -1)])
        last_attach = mongo.read_collection_last('attachments', 'id')
        if last_attach:
            new_id = int(last_attach['id']) + 1
        return str(new_id)

    @staticmethod
    def ts(mode="", days=0):
        if not mode:
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        elif mode == "file_name":
            return datetime.now().strftime('%d-%m-%Y_%H-%M-%S-%f')
        elif mode == 's':
            return datetime.now().strftime('%Y%m%d%H%M%S%f')[:16]
        elif mode == 'html_date':
            return (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    @staticmethod
    def uniquify(path):
        filename, extension = os.path.splitext(path)
        counter = 1
        while os.path.exists(path):
            path = filename + "(" + str(counter) + ")" + extension
            counter += 1
        return path


if __name__ == '__main__':
    w = Watcher()
    w.run()
