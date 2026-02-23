import json
import os
import sys
import shutil
import requests
import bson

# import orders

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
    mongo.dump("C:\\DB_backup", db_name="Scaling")


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


def fix_weight_integ_ord():
    to_fix = mongo.read_collection_list('production_log', {'quantity': {'$exists': False}})
    for ord in to_fix:
        job, info = orders.get_order_data(ord['order_id'], ord['job_id'])
        print(job)
        ord['weight'] = job[0]['weight']
        ord['quantity'] = job[0]['quantity']
        print(ord)
        ersp = mongo.update_one('production_log', {'order_id': ord['order_id'], 'job_id': ord['job_id']}, ord, '$set')
        print(ersp.matched_count)


def fix_job_id(order_id):
    order = mongo.read_collection_one('orders', {'order_id': order_id})
    order['rows'].sort(key=lambda k: int(k['job_id']))
    i = 1
    for r in order['rows']:
        r['job_id'] = str(i)
        i += 1
    mongo.update_one('orders', {'order_id': order_id}, {'rows': order['rows']}, '$set')


def restore_order(path, order_id):
    with open(os.path.join(path, 'orders.bson'), 'rb+') as f:
        data = f.read()
        all_orders = bson.decode_all(data)
        for order in all_orders:
            if order['order_id'] == str(order_id):
                del order['_id']
                mongo.update_one('orders', {'order_id': order_id}, order, '$set', upsert=True)
                print('done')
                # print(order)


def move_rows(orig_ord, dest_ord, row_num):
    orig = mongo.read_collection_one('orders', {'order_id': orig_ord})
    rows_to_move = []
    for r in orig['rows']:
        if 'inner_id' in r:
            if r['job_id'] == '46':
                rows_to_move.append(r)
    for r in rows_to_move:
        orig['rows'].remove(r)
        r['order_id'] = dest_ord
    mongo.update_one('orders', {'order_id': orig_ord}, orig, '$set')
    mongo.update_one('orders', {'order_id': dest_ord}, {'rows': rows_to_move}, '$set')


def split_fix():
    all_orders = mongo.read_collection_list("orders", {"rows.0.order_split":{"$exists":True}})
    for order in all_orders:
        splits = []
        for row in order["rows"]:
            if "order_split" in row:
                if row["order_split"] not in splits:
                    splits.append(row["order_split"])
        if splits:
            if "split" not in order["info"]:
                #mongo.update_one("orders", {"order_id": order["order_id"]}, {"info.split": len(splits),"split_reason":"fix 25.8.25"}, "$set")
                print(order["order_id"], len(splits))
            elif len(splits) != order["info"]["split"]:

                print(order["order_id"],len(splits),order["info"]["split"])
                #mongo.update_one("orders", {"order_id":order["order_id"]}, {"info.split":len(splits)},"$set")




if __name__ == '__main__':
    #mongo_backup()
    split_fix()
    # restore_order('C:\\DB_backup\\04-02-2025_20-00-04-198126 - Copy', '12577')
    # mongo.restore('C:\\DB_backup\\18-07-2024_08-07-07-483181')#, col='data_lists.bson')
