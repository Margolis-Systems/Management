import sys
from datetime import datetime

import piles

sys.path.insert(1, 'C:\\Server')
import configs
import orders

mongo = configs.mongo
all_orders = list(mongo.read_collection_list('orders', {'info.type': {'$ne': 'integration'}}))


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


def fix_status(orders_list):
    for ordr in orders_list:
        flag = False
        for r in ordr['rows']:
            if 'order_status_' in r['status']:
                flag = True
                while 'order_status_' in r['status']:
                    r['status'] = r['status'].replace('order_status_', '')
        if flag:
            print(ordr['order_id'])
            mongo.update_one('orders', {'order_id': ordr['order_id']}, ordr, '$set')


def validate_log():
    for order in all_orders:
        logg = list(mongo.read_collection_list('logs', {'title': 'order_status_change', 'operation.order_id':order['order_id']}))
        if logg:
            if logg[-1]['operation']['status'] != order['info']['status']:
                print(order['order_id'],order['info']['status'],logg[-1]['operation']['status'])

weights = {}
for order in all_orders:
    if 'total_weight' in order['info']:
        weights[order['order_id']] = order['info']['total_weight']
    else:
        weights[order['order_id']] = 0
for order in all_orders:
    if 'linked_orders' in order['info']:
        for i in range(len(order['info']['linked_orders'])):
            l_id = order['info']['linked_orders'][i]['order_id']
            mongo.update_one('orders', {'order_id': order['order_id']}, {'info.linked_orders.{}.total_weight'.format(i): weights[l_id]}, '$set')

