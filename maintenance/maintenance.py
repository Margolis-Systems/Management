import json
import os
import sys
import shutil
import requests
import bson

sys.path.insert(1, 'C:\\Server')
import configs


mongo = configs.mongo


def clear_folder(folder_dir):
    shutil.rmtree(folder_dir)
    os.mkdir(folder_dir)


def clean_reports_temp():
    cwd = os.path.dirname(__file__)
    clear_folder(os.path.join(cwd, '../reports/report_output'))
    clear_folder(os.path.join(cwd, '../reports/reports_temp'))
    clear_folder(os.path.join(cwd, '../static/img'))


def mongo_backup():
    mongo.dump("C:\\DB_backup")


def mongo_restore(backup_dir):
    mongo.restore(backup_dir)


def calc_rows_count_for_orders():
    orders_info_df = mongo.read_collection_df('orders', query={'info': {'$exists': True}})
    for order_id in orders_info_df['order_id']:
        order_rows_count = mongo.count_docs('orders', query={'order_id': order_id, 'info': {'$exists': False},
                                                             'job_id': {'$ne': '0'}})
        mongo.update_one('orders', {'order_id': order_id}, {'info.rows': str(order_rows_count)}, '$set')


def clean_empty_orders():
    orders_info_df = mongo.read_collection_df('orders', query={'info': {'$exists': True}})
    for order_id in orders_info_df['order_id']:
        order_rows_count = mongo.count_docs('orders', query={'order_id': order_id, 'info': {'$exists': False},
                                                             'job_id': {'$ne': '0'}})
        if order_rows_count == 0:
            mongo.delete_many('orders', {'order_id': order_id})


def add_ang():
    shapes = configs.shapes.copy()
    for shape in shapes:
        print(shape)
        shapes[shape]['ang'] = get_ang(shapes[shape])
    with open(os.path.dirname(os.getcwd()) + '\\lists\\shapes.json', 'w') as f:
        json.dump(shapes, f)
    configs.mongo.update_one('data_lists', {'name': 'shapes'}, {'data': shapes}, '$set')


def get_ang(shape_data):
    ang = []
    for ind in list(range(1, len(shape_data['draw_positions'])-1)):
        pos1, pos2, pos3 = shape_data['draw_positions'][ind - 1], shape_data['draw_positions'][ind], shape_data['draw_positions'][ind+1]
        print(pos1, pos2, pos3)
        if (pos1[0] - pos2[0] == 0 or pos1[1] - pos2[1] == 0) and (pos3[0] - pos2[0] == 0 or pos3[1] - pos2[1] == 0):
            ang.append(90)
        else:
            ang.append(45)
    return ang


def update_orders_total_weight():
    orders_df = mongo.read_collection_df('orders', query={'info': {'$exists': True}})
    order_data_df = mongo.read_collection_df('orders', query={'info': {'$exists': False}, 'job_id': {'$ne': "0"}})
    orders = orders_df['order_id'].to_list()
    for order in orders:
        total_weight = sum(order_data_df[order_data_df['order_id'] == order]['weight'].to_list())
        mongo.update_one('orders', {'order_id': order}, {'info.total_weight': int(total_weight)}, '$set')


def mesh_description():
    cat = mongo.read_collection_one('data_lists',{'name': 'rebar_catalog'})
    for item in cat['data']:
        diam = cat["data"][item]["diam_x"]
        len = cat["data"][item]["length"]
        wid = cat["data"][item]["width"]
        pit = cat["data"][item]["y_pitch"]
        cat['data'][item]['description'] = f'רשת סטנדרט קוטר {diam} {len}*{wid} חור {pit}*{pit}'
        print(cat['data'][item]['description'])
        mongo.update_one('data_lists', {'name':'rebar_catalog'}, cat, '$set')


def reorder_job_id():
    order_id = '64'  # main.session['order_id']
    job_list = list(mongo.read_collection_list('orders', {'order_id': order_id,
                                                          'info': {'$exists': False}}))
    rows = len(job_list)
    index = 1
    if job_list:
        for job in job_list:
            if job['job_id'] != '0':
                mongo.update_one('orders', {'order_id': order_id, 'job_id': job['job_id']},
                                      {'job_id': str(index)}, '$set')
                index += 1
        mongo.update_one('orders', {'order_id': order_id, 'info': {'$exists': True}},
                              {'info.rows': str(rows)}, '$set')


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


if __name__ == '__main__':
    # mongo_backup()
    # add_ang()
    # update_orders_total_weight()
    # mongo_restore("C:\\Projects\\Tzomet\\old ver\\05-07-2023_13-59-27-825881")
    # order_id = 10
    # mongo.delete_many('orders', {})
    # mesh_description()
    # resp = mongo.read_uniq('machines', 'machine_id', {'machine_name': 'MS'})
    # print(resp)
    li = [{"order_id": "424", "info": {"created_by": "ירדן", "date_created": "2023-08-16 09:25:17", "date_delivery": "", "type": "regular", "costumer_name": 'שי חי יזמות והשקעות בע"מ', "costumer_id": "6", "costumer_site": "קרית ים ", "status": "NEW", "comment": "תקרה קומת קרקע בניין 1 ", "rows": 185, "total_weight": 5479, "in_use": "ירדן"}},
{"order_id": "424", "job_id": "1", "status": "NEW", "date_created": "2023-08-16 09:25:59", "element": "ק1", "bar_type": "מצולע", "diam": "14", "quantity": "2", "shape": "1", "length": "630", "weight": 15.2, "description": "", "shape_data": ["630"], "shape_ang": []},
{"order_id": "424", "job_id": "2", "status": "NEW", "date_created": "2023-08-16 09:26:06", "element": "ק1", "bar_type": "מצולע", "diam": "16", "quantity": "2", "shape": "1", "length": "630", "weight": 19.9, "description": "", "shape_data": ["630"], "shape_ang": []},
{"order_id": "424", "job_id": "3", "status": "NEW", "date_created": "2023-08-16 09:26:12", "element": "ק1", "bar_type": "מצולע", "diam": "14", "quantity": "2", "shape": "1", "length": "400", "weight": 9.7, "description": "", "shape_data": ["400"], "shape_ang": []},
{"order_id": "424", "job_id": "4", "status": "NEW", "date_created": "2023-08-16 09:26:38", "element": "ק1", "bar_type": "מצולע", "diam": "12", "quantity": "2", "shape": "2", "length": "410", "weight": 7.3, "description": "", "shape_data": ["15", "395"], "shape_ang": ["-90"]},
{"order_id": "424", "job_id": "5", "status": "NEW", "date_created": "2023-08-16 09:26:50", "element": "1", "bar_type": "מצולע", "diam": "8", "quantity": "24", "shape": "925", "length": "124", "weight": 11.8, "description": "", "shape_data": ["9", "29", "24", "29", "24", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "6", "status": "NEW", "date_created": "2023-08-16 09:26:59", "element": "1", "bar_type": "מצולע", "diam": "8", "quantity": "30", "shape": "925", "length": "144", "weight": 17.1, "description": "", "shape_data": ["9", "49", "14", "49", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "7", "status": "NEW", "date_created": "2023-08-16 09:27:10", "element": "ק2", "bar_type": "מצולע", "diam": "14", "quantity": "4", "shape": "4", "length": "240", "weight": 11.6, "description": "", "shape_data": ["15", "210", "15"], "shape_ang": ["-90", "-90"]},
{"order_id": "424", "job_id": "8", "status": "NEW", "date_created": "2023-08-16 09:27:17", "element": "ק2", "bar_type": "מצולע", "diam": "16", "quantity": "4", "shape": "4", "length": "240", "weight": 15.1, "description": "", "shape_data": ["15", "210", "15"], "shape_ang": ["-90", "-90"]},
{"order_id": "424", "job_id": "9", "status": "NEW", "date_created": "2023-08-16 09:27:22", "element": "ק2", "bar_type": "מצולע", "diam": "14", "quantity": "2", "shape": "1", "length": "500", "weight": 12.1, "description": "", "shape_data": ["500"], "shape_ang": []},
{"order_id": "424", "job_id": "10", "status": "NEW", "date_created": "2023-08-16 09:27:29", "element": "ק2", "bar_type": "מצולע", "diam": "12", "quantity": "2", "shape": "1", "length": "310", "weight": 5.5, "description": "", "shape_data": ["310"], "shape_ang": []},
{"order_id": "424", "job_id": "11", "status": "NEW", "date_created": "2023-08-16 09:27:39", "element": "2", "bar_type": "מצולע", "diam": "8", "quantity": "25", "shape": "925", "length": "204", "weight": 20.1, "description": "", "shape_data": ["9", "79", "14", "79", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "12", "status": "NEW", "date_created": "2023-08-16 09:27:48", "element": "2", "bar_type": "מצולע", "diam": "8", "quantity": "8", "shape": "925", "length": "184", "weight": 5.8, "description": "", "shape_data": ["9", "69", "14", "69", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "13", "status": "NEW", "date_created": "2023-08-16 09:28:05", "element": "ק3", "bar_type": "מצולע", "diam": "14", "quantity": "2", "shape": "4", "length": "290", "weight": 7.0, "description": "", "shape_data": ["15", "260", "15"], "shape_ang": ["-90", "-90"]},
{"order_id": "424", "job_id": "14", "status": "NEW", "date_created": "2023-08-16 09:28:12", "element": "ק3", "bar_type": "מצולע", "diam": "16", "quantity": "2", "shape": "4", "length": "290", "weight": 9.2, "description": "", "shape_data": ["15", "260", "15"], "shape_ang": ["-90", "-90"]},
{"order_id": "424", "job_id": "15", "status": "NEW", "date_created": "2023-08-16 09:28:23", "element": "3", "bar_type": "מצולע", "diam": "8", "quantity": "16", "shape": "925", "length": "124", "weight": 7.8, "description": "", "shape_data": ["9", "29", "24", "29", "24", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "16", "status": "NEW", "date_created": "2023-08-16 09:28:30", "element": "ק4", "bar_type": "מצולע", "diam": "14", "quantity": "2", "shape": "1", "length": "730", "weight": 17.6, "description": "", "shape_data": ["730"], "shape_ang": []},
{"order_id": "424", "job_id": "17", "status": "NEW", "date_created": "2023-08-16 09:28:35", "element": "ק4", "bar_type": "מצולע", "diam": "16", "quantity": "2", "shape": "1", "length": "580", "weight": 18.3, "description": "", "shape_data": ["580"], "shape_ang": []},
{"order_id": "424", "job_id": "18", "status": "NEW", "date_created": "2023-08-16 09:28:59", "element": "4", "bar_type": "מצולע", "diam": "8", "quantity": "40", "shape": "925", "length": "104", "weight": 16.4, "description": "", "shape_data": ["9", "29", "14", "29", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "19", "status": "NEW", "date_created": "2023-08-16 09:29:09", "element": "ק5", "bar_type": "מצולע", "diam": "14", "quantity": "6", "shape": "1", "length": "600", "weight": 43.5, "description": "", "shape_data": ["600"], "shape_ang": []},
{"order_id": "424", "job_id": "20", "status": "NEW", "date_created": "2023-08-16 09:29:26", "element": "5", "bar_type": "מצולע", "diam": "8", "quantity": "12", "shape": "925", "length": "144", "weight": 6.8, "description": "", "shape_data": ["9", "49", "14", "49", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "21", "status": "NEW", "date_created": "2023-08-16 09:29:36", "element": "5", "bar_type": "מצולע", "diam": "8", "quantity": "45", "shape": "925", "length": "104", "weight": 18.5, "description": "", "shape_data": ["9", "29", "14", "29", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "22", "status": "NEW", "date_created": "2023-08-16 09:29:52", "element": "ק6", "bar_type": "מצולע", "diam": "16", "quantity": "14", "shape": "1", "length": "700", "weight": 154.6, "description": "", "shape_data": ["700"], "shape_ang": []},
{"order_id": "424", "job_id": "23", "status": "NEW", "date_created": "2023-08-16 09:30:34", "element": "ק6/", "bar_type": "מצולע", "diam": "32", "quantity": "20", "shape": "4", "length": "406", "weight": 512.4, "description": "", "shape_data": ["27", "352", "27"], "shape_ang": ["-90", "-90"]},
{"order_id": "424", "job_id": "24", "status": "NEW", "date_created": "2023-08-16 09:30:55", "element": "6", "bar_type": "מצולע", "diam": "16", "quantity": "70", "shape": "925", "length": "272", "weight": 300.5, "description": "", "shape_data": ["13", "79", "44", "79", "44", "13"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "25", "status": "NEW", "date_created": "2023-08-16 09:31:11", "element": "6", "bar_type": "מצולע", "diam": "16", "quantity": "70", "shape": "925", "length": "202", "weight": 223.1, "description": "", "shape_data": ["13", "44", "44", "44", "44", "13"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "26", "status": "NEW", "date_created": "2023-08-16 09:31:28", "element": "ק7", "bar_type": "מצולע", "diam": "14", "quantity": "2", "shape": "2", "length": "595", "weight": 14.4, "description": "", "shape_data": ["15", "580"], "shape_ang": ["-90"]},
{"order_id": "424", "job_id": "27", "status": "NEW", "date_created": "2023-08-16 09:31:34", "element": "ק7", "bar_type": "מצולע", "diam": "16", "quantity": "2", "shape": "2", "length": "595", "weight": 18.8, "description": "", "shape_data": ["15", "580"], "shape_ang": ["-90"]},
{"order_id": "424", "job_id": "28", "status": "NEW", "date_created": "2023-08-16 09:31:39", "element": "ק7", "bar_type": "מצולע", "diam": "14", "quantity": "3", "shape": "1", "length": "800", "weight": 29.0, "description": "", "shape_data": ["800"], "shape_ang": []},
{"order_id": "424", "job_id": "29", "status": "NEW", "date_created": "2023-08-16 09:31:51", "element": "ק7", "bar_type": "מצולע", "diam": "14", "quantity": "2", "shape": "1", "length": "590", "weight": 14.3, "description": "", "shape_data": ["590"], "shape_ang": []},
{"order_id": "424", "job_id": "30", "status": "NEW", "date_created": "2023-08-16 09:31:58", "element": "ק7", "bar_type": "מצולע", "diam": "16", "quantity": "2", "shape": "2", "length": "715", "weight": 22.6, "description": "", "shape_data": ["15", "700"], "shape_ang": ["-90"]},
{"order_id": "424", "job_id": "31", "status": "NEW", "date_created": "2023-08-16 09:32:04", "element": "ק7", "bar_type": "מצולע", "diam": "16", "quantity": "2", "shape": "4", "length": "620", "weight": 19.6, "description": "", "shape_data": ["15", "590", "15"], "shape_ang": ["-90", "-90"]},
{"order_id": "424", "job_id": "32", "status": "NEW", "date_created": "2023-08-16 09:32:09", "element": "ק7", "bar_type": "מצולע", "diam": "14", "quantity": "2", "shape": "1", "length": "450", "weight": 10.9, "description": "", "shape_data": ["450"], "shape_ang": []},
{"order_id": "424", "job_id": "33", "status": "NEW", "date_created": "2023-08-16 09:32:14", "element": "ק7", "bar_type": "מצולע", "diam": "16", "quantity": "2", "shape": "1", "length": "450", "weight": 14.2, "description": "", "shape_data": ["450"], "shape_ang": []},
{"order_id": "424", "job_id": "34", "status": "NEW", "date_created": "2023-08-16 09:32:51", "element": "7", "bar_type": "מצולע", "diam": "8", "quantity": "30", "shape": "925", "length": "104", "weight": 12.3, "description": "", "shape_data": ["9", "29", "14", "29", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "35", "status": "NEW", "date_created": "2023-08-16 09:32:59", "element": "7", "bar_type": "מצולע", "diam": "8", "quantity": "45", "shape": "925", "length": "124", "weight": 22.0, "description": "", "shape_data": ["9", "29", "24", "29", "24", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "36", "status": "NEW", "date_created": "2023-08-16 09:33:06", "element": "7", "bar_type": "מצולע", "diam": "8", "quantity": "50", "shape": "925", "length": "184", "weight": 36.3, "description": "", "shape_data": ["9", "69", "14", "69", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "37", "status": "NEW", "date_created": "2023-08-16 09:33:26", "element": "ק8", "bar_type": "מצולע", "diam": "20", "quantity": "3", "shape": "1", "length": "670", "weight": 49.6, "description": "", "shape_data": ["670"], "shape_ang": []},
{"order_id": "424", "job_id": "38", "status": "NEW", "date_created": "2023-08-16 09:33:39", "element": "ק8/", "bar_type": "מצולע", "diam": "32", "quantity": "2", "shape": "2", "length": "622", "weight": 78.5, "description": "", "shape_data": ["27", "595"], "shape_ang": ["-90"]},
{"order_id": "424", "job_id": "39", "status": "NEW", "date_created": "2023-08-16 09:34:07", "element": "ק8/", "bar_type": "מצולע", "diam": "32", "quantity": "2", "shape": "1", "length": "595", "weight": 75.1, "description": "", "shape_data": ["595"], "shape_ang": []},
{"order_id": "424", "job_id": "40", "status": "NEW", "date_created": "2023-08-16 09:34:21", "element": "ק8", "bar_type": "מצולע", "diam": "14", "quantity": "4", "shape": "4", "length": "480", "weight": 23.2, "description": "", "shape_data": ["15", "450", "15"], "shape_ang": ["-90", "-90"]},
{"order_id": "424", "job_id": "41", "status": "NEW", "date_created": "2023-08-16 09:34:35", "element": "ק8", "bar_type": "מצולע", "diam": "16", "quantity": "4", "shape": "4", "length": "480", "weight": 30.3, "description": "", "shape_data": ["15", "450", "15"], "shape_ang": ["-90", "-90"]},
{"order_id": "424", "job_id": "42", "status": "NEW", "date_created": "2023-08-16 09:34:44", "element": "8", "bar_type": "מצולע", "diam": "8", "quantity": "45", "shape": "925", "length": "124", "weight": 22.0, "description": "", "shape_data": ["9", "29", "24", "29", "24", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "43", "status": "NEW", "date_created": "2023-08-16 09:34:52", "element": "8", "bar_type": "מצולע", "diam": "8", "quantity": "60", "shape": "925", "length": "184", "weight": 43.6, "description": "", "shape_data": ["9", "69", "14", "69", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "44", "status": "NEW", "date_created": "2023-08-16 09:35:08", "element": "ק8", "bar_type": "מצולע", "diam": "14", "quantity": "2", "shape": "1", "length": "600", "weight": 14.5, "description": "", "shape_data": ["600"], "shape_ang": []},
{"order_id": "424", "job_id": "45", "status": "NEW", "date_created": "2023-08-16 09:35:15", "element": "ק8", "bar_type": "מצולע", "diam": "16", "quantity": "2", "shape": "4", "length": "390", "weight": 12.3, "description": "", "shape_data": ["15", "360", "15"], "shape_ang": ["-90", "-90"]},
{"order_id": "424", "job_id": "46", "status": "NEW", "date_created": "2023-08-16 09:35:22", "element": "ק8", "bar_type": "מצולע", "diam": "14", "quantity": "2", "shape": "1", "length": "450", "weight": 10.9, "description": "", "shape_data": ["450"], "shape_ang": []},
{"order_id": "424", "job_id": "47", "status": "NEW", "date_created": "2023-08-16 09:35:30", "element": "ק8", "bar_type": "מצולע", "diam": "14", "quantity": "2", "shape": "1", "length": "450", "weight": 10.9, "description": "", "shape_data": ["450"], "shape_ang": []},
{"order_id": "424", "job_id": "48", "status": "NEW", "date_created": "2023-08-16 09:35:40", "element": "8", "bar_type": "מצולע", "diam": "8", "quantity": "35", "shape": "925", "length": "104", "weight": 14.4, "description": "", "shape_data": ["9", "29", "14", "29", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "49", "status": "NEW", "date_created": "2023-08-16 09:36:02", "element": "8", "bar_type": "מצולע", "diam": "8", "quantity": "25", "shape": "925", "length": "184", "weight": 18.2, "description": "", "shape_data": ["9", "69", "14", "69", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "50", "status": "NEW", "date_created": "2023-08-16 09:36:10", "element": "ק9", "bar_type": "מצולע", "diam": "14", "quantity": "6", "shape": "1", "length": "700", "weight": 50.7, "description": "", "shape_data": ["700"], "shape_ang": []},
{"order_id": "424", "job_id": "51", "status": "NEW", "date_created": "2023-08-16 09:36:18", "element": "ק9", "bar_type": "מצולע", "diam": "16", "quantity": "6", "shape": "2", "length": "715", "weight": 67.7, "description": "", "shape_data": ["15", "700"], "shape_ang": ["-90"]},
{"order_id": "424", "job_id": "52", "status": "NEW", "date_created": "2023-08-16 09:36:22", "element": "ק9", "bar_type": "מצולע", "diam": "14", "quantity": "4", "shape": "1", "length": "630", "weight": 30.4, "description": "", "shape_data": ["630"], "shape_ang": []},
{"order_id": "424", "job_id": "53", "status": "NEW", "date_created": "2023-08-16 09:36:34", "element": "ק9", "bar_type": "מצולע", "diam": "16", "quantity": "2", "shape": "4", "length": "1200", "weight": 37.9, "description": "", "shape_data": ["15", "1170", "15"], "shape_ang": ["-90", "-90"]},
{"order_id": "424", "job_id": "54", "status": "NEW", "date_created": "2023-08-16 09:36:48", "element": "9", "bar_type": "מצולע", "diam": "8", "quantity": "90", "shape": "925", "length": "184", "weight": 65.4, "description": "", "shape_data": ["9", "69", "14", "69", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "55", "status": "NEW", "date_created": "2023-08-16 09:36:56", "element": "9", "bar_type": "מצולע", "diam": "8", "quantity": "90", "shape": "925", "length": "124", "weight": 44.1, "description": "", "shape_data": ["9", "29", "24", "29", "24", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "56", "status": "NEW", "date_created": "2023-08-16 09:37:06", "element": "ק10", "bar_type": "מצולע", "diam": "14", "quantity": "4", "shape": "4", "length": "590", "weight": 28.5, "description": "", "shape_data": ["15", "560", "15"], "shape_ang": ["-90", "-90"]},
{"order_id": "424", "job_id": "57", "status": "NEW", "date_created": "2023-08-16 09:37:12", "element": "ק10", "bar_type": "מצולע", "diam": "16", "quantity": "4", "shape": "4", "length": "590", "weight": 37.2, "description": "", "shape_data": ["15", "560", "15"], "shape_ang": ["-90", "-90"]},
{"order_id": "424", "job_id": "58", "status": "NEW", "date_created": "2023-08-16 09:37:22", "element": "10", "bar_type": "מצולע", "diam": "8", "quantity": "80", "shape": "925", "length": "164", "weight": 51.8, "description": "", "shape_data": ["9", "59", "14", "59", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "59", "status": "NEW", "date_created": "2023-08-16 09:37:55", "element": "ק11", "bar_type": "מצולע", "diam": "12", "quantity": "12", "shape": "4", "length": "300", "weight": 32.0, "description": "", "shape_data": ["15", "270", "15"], "shape_ang": ["-90", "-90"]},
{"order_id": "424", "job_id": "60", "status": "NEW", "date_created": "2023-08-16 09:38:04", "element": "ק11", "bar_type": "מצולע", "diam": "14", "quantity": "14", "shape": "1", "length": "300", "weight": 50.7, "description": "", "shape_data": ["300"], "shape_ang": []},
{"order_id": "424", "job_id": "61", "status": "NEW", "date_created": "2023-08-16 09:38:14", "element": "11", "bar_type": "מצולע", "diam": "8", "quantity": "70", "shape": "925", "length": "184", "weight": 50.9, "description": "", "shape_data": ["9", "69", "14", "69", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "62", "status": "NEW", "date_created": "2023-08-16 09:39:11", "element": "ק12", "bar_type": "מצולע", "diam": "14", "quantity": "6", "shape": "1", "length": "800", "weight": 58.0, "description": "", "shape_data": ["800"], "shape_ang": []},
{"order_id": "424", "job_id": "63", "status": "NEW", "date_created": "2023-08-16 09:39:01", "element": "ק12", "bar_type": "מצולע", "diam": "16", "quantity": "6", "shape": "1", "length": "615", "weight": 58.2, "description": "", "shape_data": ["615"], "shape_ang": []},
{"order_id": "424", "job_id": "64", "status": "NEW", "date_created": "2023-08-16 09:39:23", "element": "12", "bar_type": "מצולע", "diam": "8", "quantity": "130", "shape": "925", "length": "184", "weight": 94.5, "description": "", "shape_data": ["9", "69", "14", "69", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "65", "status": "NEW", "date_created": "2023-08-16 09:39:39", "element": "ק13", "bar_type": "מצולע", "diam": "14", "quantity": "4", "shape": "1", "length": "800", "weight": 38.7, "description": "", "shape_data": ["800"], "shape_ang": []},
{"order_id": "424", "job_id": "66", "status": "NEW", "date_created": "2023-08-16 09:39:46", "element": "ק13", "bar_type": "מצולע", "diam": "16", "quantity": "4", "shape": "1", "length": "770", "weight": 48.6, "description": "", "shape_data": ["770"], "shape_ang": []},
{"order_id": "424", "job_id": "67", "status": "NEW", "date_created": "2023-08-16 09:39:57", "element": "13", "bar_type": "מצולע", "diam": "8", "quantity": "100", "shape": "925", "length": "164", "weight": 64.8, "description": "", "shape_data": ["9", "59", "14", "59", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "68", "status": "NEW", "date_created": "2023-08-16 09:40:08", "element": "ק14", "bar_type": "מצולע", "diam": "12", "quantity": "8", "shape": "1", "length": "500", "weight": 35.5, "description": "", "shape_data": ["500"], "shape_ang": []},
{"order_id": "424", "job_id": "69", "status": "NEW", "date_created": "2023-08-16 09:40:14", "element": "ק14", "bar_type": "מצולע", "diam": "12", "quantity": "8", "shape": "1", "length": "265", "weight": 18.8, "description": "", "shape_data": ["265"], "shape_ang": []},
{"order_id": "424", "job_id": "70", "status": "NEW", "date_created": "2023-08-16 09:40:28", "element": "14", "bar_type": "מצולע", "diam": "8", "quantity": "70", "shape": "925", "length": "104", "weight": 28.8, "description": "", "shape_data": ["9", "29", "14", "29", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "71", "status": "NEW", "date_created": "2023-08-16 09:40:36", "element": "ק15", "bar_type": "מצולע", "diam": "14", "quantity": "8", "shape": "1", "length": "250", "weight": 24.2, "description": "", "shape_data": ["250"], "shape_ang": []},
{"order_id": "424", "job_id": "72", "status": "NEW", "date_created": "2023-08-16 09:40:43", "element": "ק15", "bar_type": "מצולע", "diam": "12", "quantity": "8", "shape": "4", "length": "208", "weight": 14.8, "description": "", "shape_data": ["15", "178", "15"], "shape_ang": ["-90", "-90"]},
{"order_id": "424", "job_id": "73", "status": "NEW", "date_created": "2023-08-16 09:40:57", "element": "15", "bar_type": "מצולע", "diam": "8", "quantity": "30", "shape": "925", "length": "204", "weight": 24.2, "description": "", "shape_data": ["9", "79", "14", "79", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "74", "status": "NEW", "date_created": "2023-08-16 09:41:11", "element": "16", "bar_type": "מצולע", "diam": "14", "quantity": "75", "shape": "925", "length": "130", "weight": 117.8, "description": "", "shape_data": ["12", "29", "24", "29", "24", "12"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "75", "status": "NEW", "date_created": "2023-08-16 09:41:25", "element": "16", "bar_type": "מצולע", "diam": "16", "quantity": "33", "shape": "925", "length": "342", "weight": 178.1, "description": "", "shape_data": ["13", "114", "44", "114", "44", "13"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "76", "status": "NEW", "date_created": "2023-08-16 09:41:34", "element": "16", "bar_type": "מצולע", "diam": "16", "quantity": "66", "shape": "925", "length": "202", "weight": 210.4, "description": "", "shape_data": ["13", "44", "44", "44", "44", "13"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "77", "status": "NEW", "date_created": "2023-08-16 09:41:56", "element": "K", "bar_type": "מצולע", "diam": "8", "quantity": "30", "shape": "925", "length": "104", "weight": 12.3, "description": "", "shape_data": ["9", "29", "14", "29", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "78", "status": "NEW", "date_created": "2023-08-16 09:42:07", "element": "K", "bar_type": "מצולע", "diam": "8", "quantity": "14", "shape": "925", "length": "164", "weight": 9.1, "description": "", "shape_data": ["9", "59", "14", "59", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "79", "status": "NEW", "date_created": "2023-08-16 09:42:25", "element": "K", "bar_type": "מצולע", "diam": "8", "quantity": "28", "shape": "925", "length": "194", "weight": 21.5, "description": "", "shape_data": ["9", "74", "14", "74", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "80", "status": "NEW", "date_created": "2023-08-16 09:42:34", "element": "K", "bar_type": "מצולע", "diam": "8", "quantity": "42", "shape": "925", "length": "104", "weight": 17.3, "description": "", "shape_data": ["9", "29", "14", "29", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "81", "status": "NEW", "date_created": "2023-08-16 09:42:43", "element": "K", "bar_type": "מצולע", "diam": "8", "quantity": "42", "shape": "925", "length": "124", "weight": 20.6, "description": "", "shape_data": ["9", "29", "24", "29", "24", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "82", "status": "NEW", "date_created": "2023-08-16 09:42:51", "element": "K", "bar_type": "מצולע", "diam": "8", "quantity": "28", "shape": "925", "length": "204", "weight": 22.6, "description": "", "shape_data": ["9", "79", "14", "79", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "83", "status": "NEW", "date_created": "2023-08-16 09:42:59", "element": "K", "bar_type": "מצולע", "diam": "8", "quantity": "15", "shape": "925", "length": "124", "weight": 7.3, "description": "", "shape_data": ["9", "39", "14", "39", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "84", "status": "NEW", "date_created": "2023-08-16 09:43:07", "element": "K", "bar_type": "מצולע", "diam": "8", "quantity": "16", "shape": "925", "length": "184", "weight": 11.6, "description": "", "shape_data": ["9", "69", "14", "69", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "85", "status": "NEW", "date_created": "2023-08-16 09:43:17", "element": "K", "bar_type": "מצולע", "diam": "8", "quantity": "15", "shape": "925", "length": "124", "weight": 7.3, "description": "", "shape_data": ["9", "29", "24", "29", "24", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "86", "status": "NEW", "date_created": "2023-08-16 09:43:25", "element": "K", "bar_type": "מצולע", "diam": "8", "quantity": "28", "shape": "925", "length": "164", "weight": 18.1, "description": "", "shape_data": ["9", "59", "14", "59", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "87", "status": "NEW", "date_created": "2023-08-16 09:43:35", "element": "K", "bar_type": "מצולע", "diam": "8", "quantity": "15", "shape": "925", "length": "124", "weight": 7.3, "description": "", "shape_data": ["9", "29", "24", "29", "24", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "88", "status": "NEW", "date_created": "2023-08-16 09:43:43", "element": "K", "bar_type": "מצולע", "diam": "8", "quantity": "28", "shape": "925", "length": "184", "weight": 20.4, "description": "", "shape_data": ["9", "69", "14", "69", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "89", "status": "NEW", "date_created": "2023-08-16 09:43:52", "element": "K", "bar_type": "מצולע", "diam": "8", "quantity": "14", "shape": "925", "length": "224", "weight": 12.4, "description": "", "shape_data": ["9", "89", "14", "89", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "90", "status": "NEW", "date_created": "2023-08-16 09:44:00", "element": "K", "bar_type": "מצולע", "diam": "8", "quantity": "14", "shape": "925", "length": "204", "weight": 11.3, "description": "", "shape_data": ["9", "79", "14", "79", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "91", "status": "NEW", "date_created": "2023-08-16 09:44:35", "element": "קE", "bar_type": "מצולע", "diam": "14", "quantity": "4", "shape": "1", "length": "450", "weight": 21.7, "description": "", "shape_data": ["450"], "shape_ang": []},
{"order_id": "424", "job_id": "92", "status": "NEW", "date_created": "2023-08-16 09:44:40", "element": "קE", "bar_type": "מצולע", "diam": "16", "quantity": "4", "shape": "1", "length": "450", "weight": 28.4, "description": "", "shape_data": ["450"], "shape_ang": []},
{"order_id": "424", "job_id": "93", "status": "NEW", "date_created": "2023-08-16 09:44:50", "element": "קE", "bar_type": "מצולע", "diam": "14", "quantity": "2", "shape": "1", "length": "500", "weight": 12.1, "description": "", "shape_data": ["500"], "shape_ang": []},
{"order_id": "424", "job_id": "94", "status": "NEW", "date_created": "2023-08-16 09:44:59", "element": "קE", "bar_type": "מצולע", "diam": "12", "quantity": "2", "shape": "4", "length": "295", "weight": 5.2, "description": "", "shape_data": ["15", "265", "15"], "shape_ang": ["-90", "-90"]},
{"order_id": "424", "job_id": "95", "status": "NEW", "date_created": "2023-08-16 09:45:11", "element": "E", "bar_type": "מצולע", "diam": "8", "quantity": "31", "shape": "925", "length": "104", "weight": 12.7, "description": "", "shape_data": ["9", "29", "14", "29", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "96", "status": "NEW", "date_created": "2023-08-16 09:45:25", "element": "קE", "bar_type": "מצולע", "diam": "14", "quantity": "4", "shape": "1", "length": "368", "weight": 17.8, "description": "", "shape_data": ["368"], "shape_ang": []},
{"order_id": "424", "job_id": "97", "status": "NEW", "date_created": "2023-08-16 09:45:38", "element": "קE", "bar_type": "מצולע", "diam": "16", "quantity": "4", "shape": "1", "length": "368", "weight": 23.2, "description": "", "shape_data": ["368"], "shape_ang": []},
{"order_id": "424", "job_id": "98", "status": "NEW", "date_created": "2023-08-16 09:45:48", "element": "E", "bar_type": "מצולע", "diam": "8", "quantity": "22", "shape": "925", "length": "124", "weight": 10.8, "description": "", "shape_data": ["9", "39", "14", "39", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "99", "status": "NEW", "date_created": "2023-08-16 09:45:56", "element": "E", "bar_type": "מצולע", "diam": "8", "quantity": "22", "shape": "925", "length": "164", "weight": 14.3, "description": "", "shape_data": ["9", "59", "14", "59", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "100", "status": "NEW", "date_created": "2023-08-16 09:46:04", "element": "E", "bar_type": "מצולע", "diam": "8", "quantity": "10", "shape": "925", "length": "204", "weight": 8.1, "description": "", "shape_data": ["9", "79", "14", "79", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "101", "status": "NEW", "date_created": "2023-08-16 09:46:15", "element": "E", "bar_type": "מצולע", "diam": "8", "quantity": "50", "shape": "925", "length": "104", "weight": 20.5, "description": "", "shape_data": ["9", "29", "14", "29", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "102", "status": "NEW", "date_created": "2023-08-16 09:46:24", "element": "E", "bar_type": "מצולע", "diam": "8", "quantity": "7", "shape": "925", "length": "124", "weight": 3.4, "description": "", "shape_data": ["9", "29", "24", "29", "24", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "103", "status": "NEW", "date_created": "2023-08-16 09:46:33", "element": "E", "bar_type": "מצולע", "diam": "8", "quantity": "12", "shape": "925", "length": "184", "weight": 8.7, "description": "", "shape_data": ["9", "69", "14", "69", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "104", "status": "NEW", "date_created": "2023-08-16 09:46:41", "element": "E", "bar_type": "מצולע", "diam": "8", "quantity": "28", "shape": "925", "length": "104", "weight": 11.5, "description": "", "shape_data": ["9", "29", "14", "29", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "105", "status": "NEW", "date_created": "2023-08-16 09:47:28", "element": "קK", "bar_type": "מצולע", "diam": "12", "quantity": "2", "shape": "2", "length": "515", "weight": 9.1, "description": "", "shape_data": ["15", "500"], "shape_ang": ["-90"]},
{"order_id": "424", "job_id": "106", "status": "NEW", "date_created": "2023-08-16 09:47:32", "element": "קK", "bar_type": "מצולע", "diam": "12", "quantity": "2", "shape": "1", "length": "300", "weight": 5.3, "description": "", "shape_data": ["300"], "shape_ang": []},
{"order_id": "424", "job_id": "107", "status": "NEW", "date_created": "2023-08-16 09:47:38", "element": "קK", "bar_type": "מצולע", "diam": "16", "quantity": "2", "shape": "1", "length": "600", "weight": 18.9, "description": "", "shape_data": ["600"], "shape_ang": []},
{"order_id": "424", "job_id": "108", "status": "NEW", "date_created": "2023-08-16 09:47:46", "element": "קK", "bar_type": "מצולע", "diam": "12", "quantity": "2", "shape": "1", "length": "300", "weight": 5.3, "description": "", "shape_data": ["300"], "shape_ang": []},
{"order_id": "424", "job_id": "109", "status": "NEW", "date_created": "2023-08-16 09:47:51", "element": "קK", "bar_type": "מצולע", "diam": "16", "quantity": "2", "shape": "1", "length": "700", "weight": 22.1, "description": "", "shape_data": ["700"], "shape_ang": []},
{"order_id": "424", "job_id": "110", "status": "NEW", "date_created": "2023-08-16 09:47:55", "element": "קK", "bar_type": "מצולע", "diam": "16", "quantity": "3", "shape": "1", "length": "440", "weight": 20.8, "description": "", "shape_data": ["440"], "shape_ang": []},
{"order_id": "424", "job_id": "111", "status": "NEW", "date_created": "2023-08-16 09:48:00", "element": "קK", "bar_type": "מצולע", "diam": "16", "quantity": "3", "shape": "1", "length": "650", "weight": 30.8, "description": "", "shape_data": ["650"], "shape_ang": []},
{"order_id": "424", "job_id": "112", "status": "NEW", "date_created": "2023-08-16 09:48:05", "element": "קK", "bar_type": "מצולע", "diam": "16", "quantity": "2", "shape": "1", "length": "520", "weight": 16.4, "description": "", "shape_data": ["520"], "shape_ang": []},
{"order_id": "424", "job_id": "113", "status": "NEW", "date_created": "2023-08-16 09:48:10", "element": "קK", "bar_type": "מצולע", "diam": "14", "quantity": "4", "shape": "1", "length": "760", "weight": 36.7, "description": "", "shape_data": ["760"], "shape_ang": []},
{"order_id": "424", "job_id": "114", "status": "NEW", "date_created": "2023-08-16 09:48:20", "element": "קK", "bar_type": "מצולע", "diam": "14", "quantity": "4", "shape": "18", "length": "240", "weight": 11.6, "description": "", "shape_data": ["120", "120"], "shape_ang": ["45"]},
{"order_id": "424", "job_id": "115", "status": "NEW", "date_created": "2023-08-16 09:48:40", "element": "K", "bar_type": "מצולע", "diam": "8", "quantity": "105", "shape": "925", "length": "184", "weight": 76.3, "description": "", "shape_data": ["9", "69", "14", "69", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "116", "status": "NEW", "date_created": "2023-08-16 09:48:53", "element": "קG", "bar_type": "מצולע", "diam": "16", "quantity": "6", "shape": "2", "length": "645", "weight": 61.1, "description": "", "shape_data": ["15", "630"], "shape_ang": ["-90"]},
{"order_id": "424", "job_id": "117", "status": "NEW", "date_created": "2023-08-16 09:48:59", "element": "קG", "bar_type": "מצולע", "diam": "16", "quantity": "4", "shape": "1", "length": "457", "weight": 28.8, "description": "", "shape_data": ["457"], "shape_ang": []},
{"order_id": "424", "job_id": "118", "status": "NEW", "date_created": "2023-08-16 09:49:04", "element": "קG", "bar_type": "מצולע", "diam": "14", "quantity": "4", "shape": "1", "length": "457", "weight": 22.1, "description": "", "shape_data": ["457"], "shape_ang": []},
{"order_id": "424", "job_id": "119", "status": "NEW", "date_created": "2023-08-16 09:49:14", "element": "G", "bar_type": "מצולע", "diam": "8", "quantity": "50", "shape": "925", "length": "164", "weight": 32.4, "description": "", "shape_data": ["9", "59", "14", "59", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "120", "status": "NEW", "date_created": "2023-08-16 09:49:23", "element": "קG", "bar_type": "מצולע", "diam": "14", "quantity": "2", "shape": "1", "length": "436", "weight": 10.5, "description": "", "shape_data": ["436"], "shape_ang": []},
{"order_id": "424", "job_id": "121", "status": "NEW", "date_created": "2023-08-16 09:49:28", "element": "קG", "bar_type": "מצולע", "diam": "16", "quantity": "2", "shape": "1", "length": "436", "weight": 13.8, "description": "", "shape_data": ["436"], "shape_ang": []},
{"order_id": "424", "job_id": "122", "status": "NEW", "date_created": "2023-08-16 09:49:38", "element": "G", "bar_type": "מצולע", "diam": "8", "quantity": "26", "shape": "925", "length": "104", "weight": 10.7, "description": "", "shape_data": ["9", "29", "14", "29", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "123", "status": "NEW", "date_created": "2023-08-16 09:49:47", "element": "קE", "bar_type": "מצולע", "diam": "12", "quantity": "2", "shape": "1", "length": "400", "weight": 7.1, "description": "", "shape_data": ["400"], "shape_ang": []},
{"order_id": "424", "job_id": "124", "status": "NEW", "date_created": "2023-08-16 09:49:54", "element": "קE", "bar_type": "מצולע", "diam": "14", "quantity": "2", "shape": "1", "length": "395", "weight": 9.5, "description": "", "shape_data": ["395"], "shape_ang": []},
{"order_id": "424", "job_id": "125", "status": "NEW", "date_created": "2023-08-16 09:50:00", "element": "קE", "bar_type": "מצולע", "diam": "14", "quantity": "2", "shape": "1", "length": "670", "weight": 16.2, "description": "", "shape_data": ["670"], "shape_ang": []},
{"order_id": "424", "job_id": "126", "status": "NEW", "date_created": "2023-08-16 09:50:05", "element": "קE", "bar_type": "מצולע", "diam": "14", "quantity": "2", "shape": "1", "length": "660", "weight": 15.9, "description": "", "shape_data": ["660"], "shape_ang": []},
{"order_id": "424", "job_id": "127", "status": "NEW", "date_created": "2023-08-16 09:50:13", "element": "קE", "bar_type": "מצולע", "diam": "14", "quantity": "2", "shape": "1", "length": "178", "weight": 4.3, "description": "", "shape_data": ["178"], "shape_ang": []},
{"order_id": "424", "job_id": "128", "status": "NEW", "date_created": "2023-08-16 09:50:19", "element": "קE", "bar_type": "מצולע", "diam": "16", "quantity": "2", "shape": "1", "length": "178", "weight": 5.6, "description": "", "shape_data": ["178"], "shape_ang": []},
{"order_id": "424", "job_id": "129", "status": "NEW", "date_created": "2023-08-16 09:50:27", "element": "קE", "bar_type": "מצולע", "diam": "16", "quantity": "2", "shape": "1", "length": "178", "weight": 5.6, "description": "", "shape_data": ["178"], "shape_ang": []},
{"order_id": "424", "job_id": "130", "status": "NEW", "date_created": "2023-08-16 09:50:44", "element": "קE", "bar_type": "מצולע", "diam": "14", "quantity": "2", "shape": "1", "length": "178", "weight": 4.3, "description": "", "shape_data": ["178"], "shape_ang": []},
{"order_id": "424", "job_id": "131", "status": "NEW", "date_created": "2023-08-16 09:50:56", "element": "קE", "bar_type": "מצולע", "diam": "16", "quantity": "4", "shape": "1", "length": "370", "weight": 23.4, "description": "", "shape_data": ["370"], "shape_ang": []},
{"order_id": "424", "job_id": "132", "status": "NEW", "date_created": "2023-08-16 09:51:01", "element": "קE", "bar_type": "מצולע", "diam": "14", "quantity": "4", "shape": "1", "length": "370", "weight": 17.9, "description": "", "shape_data": ["370"], "shape_ang": []},
{"order_id": "424", "job_id": "133", "status": "NEW", "date_created": "2023-08-16 09:51:12", "element": "E", "bar_type": "מצולע", "diam": "8", "quantity": "48", "shape": "925", "length": "104", "weight": 19.7, "description": "", "shape_data": ["9", "29", "14", "29", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "134", "status": "NEW", "date_created": "2023-08-16 09:51:19", "element": "E", "bar_type": "מצולע", "diam": "8", "quantity": "12", "shape": "925", "length": "184", "weight": 8.7, "description": "", "shape_data": ["9", "69", "14", "69", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "135", "status": "NEW", "date_created": "2023-08-16 09:51:27", "element": "E", "bar_type": "מצולע", "diam": "8", "quantity": "7", "shape": "925", "length": "124", "weight": 3.4, "description": "", "shape_data": ["9", "29", "24", "29", "24", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "136", "status": "NEW", "date_created": "2023-08-16 09:51:35", "element": "E", "bar_type": "מצולע", "diam": "8", "quantity": "22", "shape": "925", "length": "164", "weight": 14.3, "description": "", "shape_data": ["9", "59", "14", "59", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "137", "status": "NEW", "date_created": "2023-08-16 09:51:44", "element": "E", "bar_type": "מצולע", "diam": "8", "quantity": "22", "shape": "925", "length": "124", "weight": 10.8, "description": "", "shape_data": ["9", "39", "14", "39", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "138", "status": "NEW", "date_created": "2023-08-16 09:51:59", "element": "קE", "bar_type": "מצולע", "diam": "14", "quantity": "2", "shape": "1", "length": "178", "weight": 4.3, "description": "", "shape_data": ["178"], "shape_ang": []},
{"order_id": "424", "job_id": "139", "status": "NEW", "date_created": "2023-08-16 09:52:06", "element": "קE", "bar_type": "מצולע", "diam": "16", "quantity": "2", "shape": "1", "length": "178", "weight": 5.6, "description": "", "shape_data": ["178"], "shape_ang": []},
{"order_id": "424", "job_id": "140", "status": "NEW", "date_created": "2023-08-16 09:52:17", "element": "E", "bar_type": "מצולע", "diam": "8", "quantity": "12", "shape": "925", "length": "204", "weight": 9.7, "description": "", "shape_data": ["9", "79", "14", "79", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "141", "status": "NEW", "date_created": "2023-08-16 09:52:47", "element": "קF", "bar_type": "מצולע", "diam": "14", "quantity": "3", "shape": "1", "length": "800", "weight": 29.0, "description": "", "shape_data": ["800"], "shape_ang": []},
{"order_id": "424", "job_id": "142", "status": "NEW", "date_created": "2023-08-16 09:53:05", "element": "F", "bar_type": "מצולע", "diam": "8", "quantity": "30", "shape": "925", "length": "264", "weight": 31.3, "description": "", "shape_data": ["9", "54", "69", "54", "69", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "143", "status": "NEW", "date_created": "2023-08-16 09:53:17", "element": "F", "bar_type": "מצולע", "diam": "8", "quantity": "22", "shape": "925", "length": "164", "weight": 14.3, "description": "", "shape_data": ["9", "59", "14", "59", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "144", "status": "NEW", "date_created": "2023-08-16 09:53:26", "element": "F", "bar_type": "מצולע", "diam": "8", "quantity": "40", "shape": "925", "length": "124", "weight": 19.6, "description": "", "shape_data": ["9", "29", "24", "29", "24", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "145", "status": "NEW", "date_created": "2023-08-16 09:53:36", "element": "קF", "bar_type": "מצולע", "diam": "14", "quantity": "2", "shape": "1", "length": "450", "weight": 10.9, "description": "", "shape_data": ["450"], "shape_ang": []},
{"order_id": "424", "job_id": "146", "status": "NEW", "date_created": "2023-08-16 09:53:41", "element": "קF", "bar_type": "מצולע", "diam": "16", "quantity": "2", "shape": "1", "length": "450", "weight": 14.2, "description": "", "shape_data": ["450"], "shape_ang": []},
{"order_id": "424", "job_id": "147", "status": "NEW", "date_created": "2023-08-16 09:53:51", "element": "F", "bar_type": "מצולע", "diam": "8", "quantity": "28", "shape": "925", "length": "104", "weight": 11.5, "description": "", "shape_data": ["9", "29", "14", "29", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "148", "status": "NEW", "date_created": "2023-08-16 09:54:01", "element": "קF", "bar_type": "מצולע", "diam": "14", "quantity": "2", "shape": "1", "length": "593", "weight": 14.3, "description": "", "shape_data": ["593"], "shape_ang": []},
{"order_id": "424", "job_id": "149", "status": "NEW", "date_created": "2023-08-16 09:54:06", "element": "קF", "bar_type": "מצולע", "diam": "16", "quantity": "2", "shape": "1", "length": "593", "weight": 18.7, "description": "", "shape_data": ["593"], "shape_ang": []},
{"order_id": "424", "job_id": "150", "status": "NEW", "date_created": "2023-08-16 09:54:18", "element": "F", "bar_type": "מצולע", "diam": "8", "quantity": "29", "shape": "925", "length": "124", "weight": 14.2, "description": "", "shape_data": ["9", "29", "24", "29", "24", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "151", "status": "NEW", "date_created": "2023-08-16 09:54:29", "element": "קG", "bar_type": "מצולע", "diam": "16", "quantity": "3", "shape": "2", "length": "715", "weight": 33.8, "description": "", "shape_data": ["15", "700"], "shape_ang": ["-90"]},
{"order_id": "424", "job_id": "152", "status": "NEW", "date_created": "2023-08-16 09:54:33", "element": "קG", "bar_type": "מצולע", "diam": "14", "quantity": "3", "shape": "1", "length": "800", "weight": 29.0, "description": "", "shape_data": ["800"], "shape_ang": []},
{"order_id": "424", "job_id": "153", "status": "NEW", "date_created": "2023-08-16 09:54:40", "element": "קG", "bar_type": "מצולע", "diam": "16", "quantity": "2", "shape": "4", "length": "1200", "weight": 37.9, "description": "", "shape_data": ["15", "1170", "15"], "shape_ang": ["-90", "-90"]},
{"order_id": "424", "job_id": "154", "status": "NEW", "date_created": "2023-08-16 09:54:44", "element": "קG", "bar_type": "מצולע", "diam": "14", "quantity": "2", "shape": "1", "length": "630", "weight": 15.2, "description": "", "shape_data": ["630"], "shape_ang": []},
{"order_id": "424", "job_id": "155", "status": "NEW", "date_created": "2023-08-16 09:54:49", "element": "קG", "bar_type": "מצולע", "diam": "14", "quantity": "2", "shape": "1", "length": "630", "weight": 15.2, "description": "", "shape_data": ["630"], "shape_ang": []},
{"order_id": "424", "job_id": "156", "status": "NEW", "date_created": "2023-08-16 09:54:54", "element": "קG", "bar_type": "מצולע", "diam": "16", "quantity": "3", "shape": "2", "length": "715", "weight": 33.8, "description": "", "shape_data": ["15", "700"], "shape_ang": ["-90"]},
{"order_id": "424", "job_id": "157", "status": "NEW", "date_created": "2023-08-16 09:54:58", "element": "קG", "bar_type": "מצולע", "diam": "14", "quantity": "3", "shape": "1", "length": "800", "weight": 29.0, "description": "", "shape_data": ["800"], "shape_ang": []},
{"order_id": "424", "job_id": "158", "status": "NEW", "date_created": "2023-08-16 09:55:09", "element": "G", "bar_type": "מצולע", "diam": "8", "quantity": "78", "shape": "925", "length": "124", "weight": 38.2, "description": "", "shape_data": ["9", "29", "24", "29", "24", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "159", "status": "NEW", "date_created": "2023-08-16 09:55:19", "element": "G", "bar_type": "מצולע", "diam": "8", "quantity": "60", "shape": "925", "length": "184", "weight": 43.6, "description": "", "shape_data": ["9", "69", "14", "69", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "160", "status": "NEW", "date_created": "2023-08-16 09:55:29", "element": "קG", "bar_type": "מצולע", "diam": "14", "quantity": "2", "shape": "1", "length": "450", "weight": 10.9, "description": "", "shape_data": ["450"], "shape_ang": []},
{"order_id": "424", "job_id": "161", "status": "NEW", "date_created": "2023-08-16 09:55:34", "element": "קG", "bar_type": "מצולע", "diam": "16", "quantity": "2", "shape": "1", "length": "450", "weight": 14.2, "description": "", "shape_data": ["450"], "shape_ang": []},
{"order_id": "424", "job_id": "162", "status": "NEW", "date_created": "2023-08-16 09:55:44", "element": "G", "bar_type": "מצולע", "diam": "8", "quantity": "25", "shape": "925", "length": "104", "weight": 10.3, "description": "", "shape_data": ["9", "29", "14", "29", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "163", "status": "NEW", "date_created": "2023-08-16 09:55:52", "element": "G", "bar_type": "מצולע", "diam": "8", "quantity": "62", "shape": "925", "length": "124", "weight": 30.4, "description": "", "shape_data": ["9", "29", "24", "29", "24", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "164", "status": "NEW", "date_created": "2023-08-16 09:56:00", "element": "קG", "bar_type": "מצולע", "diam": "16", "quantity": "4", "shape": "1", "length": "600", "weight": 37.9, "description": "", "shape_data": ["600"], "shape_ang": []},
{"order_id": "424", "job_id": "165", "status": "NEW", "date_created": "2023-08-16 09:56:06", "element": "קG", "bar_type": "מצולע", "diam": "16", "quantity": "2", "shape": "1", "length": "400", "weight": 12.6, "description": "", "shape_data": ["400"], "shape_ang": []},
{"order_id": "424", "job_id": "166", "status": "NEW", "date_created": "2023-08-16 09:56:20", "element": "קA", "bar_type": "מצולע", "diam": "14", "quantity": "2", "shape": "1", "length": "490", "weight": 11.8, "description": "", "shape_data": ["490"], "shape_ang": []},
{"order_id": "424", "job_id": "167", "status": "NEW", "date_created": "2023-08-16 09:56:25", "element": "קA", "bar_type": "מצולע", "diam": "12", "quantity": "2", "shape": "1", "length": "325", "weight": 5.8, "description": "", "shape_data": ["325"], "shape_ang": []},
{"order_id": "424", "job_id": "168", "status": "NEW", "date_created": "2023-08-16 09:56:35", "element": "A", "bar_type": "מצולע", "diam": "8", "quantity": "21", "shape": "925", "length": "104", "weight": 8.6, "description": "", "shape_data": ["9", "29", "14", "29", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "169", "status": "NEW", "date_created": "2023-08-16 09:56:46", "element": "קB", "bar_type": "מצולע", "diam": "14", "quantity": "2", "shape": "1", "length": "480", "weight": 11.6, "description": "", "shape_data": ["480"], "shape_ang": []},
{"order_id": "424", "job_id": "170", "status": "NEW", "date_created": "2023-08-16 09:56:53", "element": "קB", "bar_type": "מצולע", "diam": "12", "quantity": "2", "shape": "4", "length": "345", "weight": 6.1, "description": "", "shape_data": ["15", "315", "15"], "shape_ang": ["-90", "-90"]},
{"order_id": "424", "job_id": "171", "status": "NEW", "date_created": "2023-08-16 09:57:02", "element": "B", "bar_type": "מצולע", "diam": "8", "quantity": "14", "shape": "925", "length": "164", "weight": 9.1, "description": "", "shape_data": ["9", "59", "14", "59", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "172", "status": "NEW", "date_created": "2023-08-16 09:57:11", "element": "קC", "bar_type": "מצולע", "diam": "14", "quantity": "2", "shape": "1", "length": "480", "weight": 11.6, "description": "", "shape_data": ["480"], "shape_ang": []},
{"order_id": "424", "job_id": "173", "status": "NEW", "date_created": "2023-08-16 09:57:17", "element": "קC", "bar_type": "מצולע", "diam": "12", "quantity": "2", "shape": "1", "length": "325", "weight": 5.8, "description": "", "shape_data": ["325"], "shape_ang": []},
{"order_id": "424", "job_id": "174", "status": "NEW", "date_created": "2023-08-16 09:57:26", "element": "C", "bar_type": "מצולע", "diam": "8", "quantity": "15", "shape": "925", "length": "104", "weight": 6.2, "description": "", "shape_data": ["9", "29", "14", "29", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "175", "status": "NEW", "date_created": "2023-08-16 09:57:35", "element": "קD", "bar_type": "מצולע", "diam": "14", "quantity": "2", "shape": "4", "length": "540", "weight": 13.0, "description": "", "shape_data": ["15", "510", "15"], "shape_ang": ["-90", "-90"]},
{"order_id": "424", "job_id": "176", "status": "NEW", "date_created": "2023-08-16 09:57:41", "element": "קD", "bar_type": "מצולע", "diam": "12", "quantity": "2", "shape": "4", "length": "540", "weight": 9.6, "description": "", "shape_data": ["15", "510", "15"], "shape_ang": ["-90", "-90"]},
{"order_id": "424", "job_id": "177", "status": "NEW", "date_created": "2023-08-16 09:57:51", "element": "D", "bar_type": "מצולע", "diam": "8", "quantity": "28", "shape": "925", "length": "104", "weight": 11.5, "description": "", "shape_data": ["9", "29", "14", "29", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "178", "status": "NEW", "date_created": "2023-08-16 09:57:58", "element": "קE", "bar_type": "מצולע", "diam": "12", "quantity": "2", "shape": "1", "length": "480", "weight": 8.5, "description": "", "shape_data": ["480"], "shape_ang": []},
{"order_id": "424", "job_id": "179", "status": "NEW", "date_created": "2023-08-16 09:58:02", "element": "קE", "bar_type": "מצולע", "diam": "14", "quantity": "2", "shape": "1", "length": "480", "weight": 11.6, "description": "", "shape_data": ["480"], "shape_ang": []},
{"order_id": "424", "job_id": "180", "status": "NEW", "date_created": "2023-08-16 09:58:17", "element": "E", "bar_type": "מצולע", "diam": "8", "quantity": "24", "shape": "925", "length": "104", "weight": 9.9, "description": "", "shape_data": ["9", "29", "14", "29", "14", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "181", "status": "NEW", "date_created": "2023-08-16 09:59:41", "element": "קF", "bar_type": "מצולע", "diam": "14", "quantity": "2", "shape": "1", "length": "465", "weight": 11.2, "description": "", "shape_data": ["465"], "shape_ang": []},
{"order_id": "424", "job_id": "182", "status": "NEW", "date_created": "2023-08-16 09:59:56", "element": "F", "bar_type": "מצולע", "diam": "8", "quantity": "22", "shape": "925", "length": "194", "weight": 16.9, "description": "", "shape_data": ["9", "69", "19", "69", "19", "9"], "shape_ang": ["-90", "90", "90", "90", "-90"]},
{"order_id": "424", "job_id": "183", "status": "NEW", "date_created": "2023-08-16 10:00:08", "element": "קF", "bar_type": "מצולע", "diam": "16", "quantity": "2", "shape": "4", "length": "620", "weight": 19.6, "description": "", "shape_data": ["15", "590", "15"], "shape_ang": ["-90", "-90"]},
{"order_id": "424", "job_id": "184", "status": "NEW", "date_created": "2023-08-16 10:00:14", "element": "קF", "bar_type": "מצולע", "diam": "14", "quantity": "2", "shape": "1", "length": "590", "weight": 14.3, "description": "", "shape_data": ["590"], "shape_ang": []},
{"order_id": "424", "job_id": "185", "status": "NEW", "date_created": "2023-08-16 10:00:19", "element": "קF", "bar_type": "מצולע", "diam": "16", "quantity": "2", "shape": "2", "length": "715", "weight": 22.6, "description": "", "shape_data": ["15", "700"], "shape_ang": ["-90"]}]
    mongo.delete_many('orders', {'order_id':'427'})
    for item in li:
        mongo.insert_collection_one('orders', item)