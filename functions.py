from datetime import datetime, timedelta
import os
import main


def ts(mode="", days=0):
    if not mode:
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    elif mode == "file_name":
        return datetime.now().strftime('%d-%m-%Y_%H-%M-%S-%f')
    elif mode == 's':
        return datetime.now().strftime('%Y%m%d%H%M%S%f')[:16]
    elif mode == 'html_date':
        return (datetime.now()-timedelta(days=days)).strftime('%Y-%m-%d')


def uniquify(path):
    filename, extension = os.path.splitext(path)
    counter = 1
    while os.path.exists(path):
        path = filename + "(" + str(counter) + ")" + extension
        counter += 1
    return path


def log(operation):
    main.mongo.insert_collection_one('logs', {'username': main.session['username'],
                                              'timestamp': ts(), 'operation': operation})
