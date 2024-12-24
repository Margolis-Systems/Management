import csv
import math
import sys
from datetime import datetime

import os
import piles
import reports

sys.path.insert(1, 'C:\\Server')
import configs

mongo = configs.mongo
# all_orders = list(mongo.read_collection_list('orders', {'order_id': '9341'}))
all_orders = list(mongo.read_collection_list('orders', {}))
# order = mongo.read_collection_one('orders', {'order_id': '4304'})


def find_not_updated():
    hist = []
    for order in all_orders:
        cur_status = order['info']['status']
        if cur_status in ['Delivered']:
            for r in order['rows']:
                if r['status'] not in ['Delivered', 'Finished']:
                    if not order['order_id'].isnumeric():
                        continue
                    if order['order_id'] not in hist and int(order['order_id']) > 5000:
                        hist.append(order['order_id'])
                    else:
                        continue
                    print(order['order_id'], r['job_id'])
                    print(cur_status, r['status'], '\n')
    print(hist)
    print(len(hist))


def fix_status(orders_list=None):
    if orders_list is None:
        orders_list = all_orders
    for order in orders_list:
        flag = False
        for r in order['rows']:
            if 'order_status_' in r['status']:
                print(order['order_id'], r['job_id'], r['status'].split('_')[-1], r['status'])
                r['status'] = r['status'].split('_')[-1]
                flag = True
        if flag:
            mongo.update_one('orders', {'order_id': order['order_id']}, order, '$set')


def validate_log():
    for order in all_orders:
        logg = list(mongo.read_collection_list('logs', {'title': 'order_status_change', 'operation.order_id':order['order_id']}))
        if logg:
            if logg[-1]['operation']['status'] != order['info']['status']:
                print(order['order_id'],order['info']['status'],logg[-1]['operation']['status'])


def csv_for_yosi_azulai():
    import csv
    data = []
    total = 0
    for order in all_orders:
        for r in order['rows']:
            if r['diam'] == '36':
                line = [order['order_id'],r['job_id'],r['diam'],r['length'],r['weight']]
                total += int(r['', '', '', 'TOTAL WEIGHT:', 'weight'])
                data.append(line)

    data.append([total])
    with open('c:\\Server\\1.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(data)


def calc_hypotenuse(length, radius):
    length = int(length)
    radius = int(radius)
    ang = 180*length/(math.pi*radius)
    hyp = radius*math.sin(math.radians(ang))/math.sin(math.radians((180-ang)/2))
    return int(hyp)


def check_double_print():
    ok = []
    to_check = []
    logs = mongo.read_collection_list('logs', {'title':'order_status_change', 'operation.status':'Processed'})
    for logg in logs:
        if [logg['operation']['order_id'], logg['timestamp']] not in ok:
            ok.append([logg['operation']['order_id'], logg['timestamp']])
        else:
            to_check.append({'id': logg['operation']['order_id'], 'ts':logg['timestamp']})
    print(to_check)


def prod_weight_count_to_csv():
    # חישוב כמות ברזל שיוצרה במפעל ולא סופקה - דוח שנוצר לעדי
    qry = {'Start_ts': {'$gte': '2024-01-01', '$lte': '2024-30-06 23:59:59'}, 'machine_id': {'$nin': [17,18]}}
    prod = mongo.read_collection_list('production_log', qry, db_name='test')
    not_del = []
    for order in all_orders:
        not_del.append(order['order_id'])
    total_w = 0
    log = []
    for p in prod:
        if p['order_id'] in not_del:
            log.append(p)
            total_w += p['weight']

    with open('c:\\Server\\logg.csv', 'w', newline='') as f:
        header = list(log[0].keys())
        header.extend(['maintenance'])
        writer = csv.DictWriter(f, header)
        writer.writerows(log)
        # writer.writerows(log)
        writer.writerow({'weight': total_w})


def check_weights(fix=False):
    for order in all_orders:
        if 'total_weight' in order['info']:
            tot = 0
            for r in order['rows']:
                tot += r['weight']
            if not float(order['info']['total_weight'])-1 <= tot <= float(order['info']['total_weight']) +1:
            # if not float(order['info']['total_weight']) == tot:
                print('ID: {}, TOTAL: {}, INFO: {}'.format(order['order_id'], tot, order['info']['total_weight']))
                if fix:
                    mongo.update_one('orders', {'order_id': order['order_id']}, {'info.total_weight': round(tot, 2)}, '$set')
        elif len(order['rows']) > 0:
            print('check: ', order['order_id'])


def prod_lod_dbl_label_id():
    prod_logs = mongo.read_collection_list('production_log', {'Start_ts': {'$gte': '2024-10-29 00:00:00'}})
    l_id = []
    for ll in prod_logs:
        if ll['label_id'] not in l_id:
            l_id.append(ll['label_id'])
        else:
            if ll['machine_id'] not in [17, 18, 34]:
                print(ll['label_id'], ll['machine_id'])


