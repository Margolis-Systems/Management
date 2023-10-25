import sys
from datetime import datetime
sys.path.insert(1, 'C:\\Server')
import configs
import orders

mongo = configs.mongo
all_orders = mongo.read_collection_list('orders')
for order in all_orders:
    flag = False
    while 'order_status_' in order['info']['status']:
        order['info']['status'] = order['info']['status'].replace('order_status_', '')
        flag = True
    while ' ' in order['info']['status']:
        order['info']['status'] = order['info']['status'].replace(' ', '')
        flag = True
    ord_id = order['order_id']
    if int(ord_id.replace('R','')) > 800 and order['info']['type']!='integration':
        print(order['order_id'])
        for r in order['rows']:
            while 'order_status_' in r['status']:
                r['status'] = r['status'].replace('order_status_', '')
                flag = True
            while ' ' in r['status']:
                r['status'] = r['status'].replace(' ', '')
                flag = True
    if flag:
        mongo.update_one('orders', {'order_id':order['order_id']}, order, '$set')
