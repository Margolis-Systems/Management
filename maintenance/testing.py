import sys
from datetime import datetime

import os
import piles
import reports

sys.path.insert(1, 'C:\\Server')
import configs

mongo = configs.mongo
# all_orders = list(mongo.read_collection_list('orders', {'info.costumer_id': {'$ne': '58'}, 'info.type':'rebar_special','info.status': {'$in':['NEW','Processed','Production','Inproduction']}}))
all_orders = list(mongo.read_collection_list('orders', {'info.type': {'$ne': 'integration'}}))
# order = mongo.read_collection_one('orders', {'order_id': '4304'})


def find_not_updated():
    hist = []
    for order in all_orders:
        cur_status = order['info']['status']
        if cur_status in ['Delivered']:
            for r in order['rows']:
                if r['status'] not in ['Delivered', 'Finished']:
                    if order['order_id'] not in hist and int(order['order_id']) > 679:
                        hist.append(order['order_id'])
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


