from datetime import datetime, timedelta
import os
import main
import requests


def ts(mode="", days=0):
    if not mode:
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    elif mode == "file_name":
        return datetime.now().strftime('%d-%m-%Y_%H-%M-%S-%f')
    elif mode == 's':
        return datetime.now().strftime('%Y%m%d%H%M%S%f')[:16]
    elif mode == 'html_date':
        return (datetime.now()-timedelta(days=days)).strftime('%Y-%m-%d')
    elif mode == 'w':
        return datetime.now().strftime('%d-%m-%Y %H-%M-%S')


def uniquify(path):
    filename, extension = os.path.splitext(path)
    counter = 1
    while os.path.exists(path):
        path = filename + "(" + str(counter) + ")" + extension
        counter += 1
    return path


def log(title, operation):
    user = 'None'
    if 'username' in main.session:
        user = main.session['username']
    log_data = {'username': user, 'timestamp': ts(), 'title': title, 'operation': operation}
    main.mongo.insert_collection_one('logs', log_data)


def send_sms(msg, _dist_numbers=[]):
    target_url = 'http://port2sms.com/Scripts/mgrqispi.dll'
    dist_numbers = ''
    if not _dist_numbers:
        _dist_numbers = ['0502201747']
    for num in _dist_numbers:
        dist_numbers += num + ';'
    post_data = {'Appname': 'Port2SMS', 'prgname': 'HTTP_SimpleSMS1', 'AccountID': '1008',
                 'UserID': '10096', 'UserPass': 'Zo2486!', 'Phone': dist_numbers, 'Text': msg, 'Sender': 'ERP'}
    resp = requests.post(target_url, data=post_data)
    return resp
