import sys
from datetime import datetime

import piles
import reports

sys.path.insert(1, 'C:\\Server')
import configs

mongo = configs.mongo
# all_orders = list(mongo.read_collection_list('orders', {'info.type': {'$ne': 'integration'},'info.costumer_name':{'$regex':'דניה סיבוס'},'info.costumer_site':{'$regex':'אומאמי'}}))
all_orders = list(mongo.read_collection_list('orders', {}))


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


# diff = configs.sscircle.copy()
# for i in configs.circle:
#     if i in diff:
#         diff.remove(i)
# print(diff)
# diff = ['58']
# for o in all_orders:
#     if o['info']['type'] == 'regular':
#         for r in o['rows']:
#             if 'shape' in r:
#                 if r['shape'] in diff:
#                     print(r['order_id'], r['job_id'], r['shape'])

# for sha in configs.shapes:
#     print(sha)
#     reports.Images.create_shape_plot(sha,enable_text_plot=False)

msg = 'הודפסה הזמנה לקוח מס. {order_id}\nמתאריך: {date_created}\n לתאריך אספקה:{date_delivery}\nלקוח: {costumer_name}\nאתר: {costumer_site}\nמשקל: {total_weight} \nשורות: {rows} [{type}] \n{username} ' \
                    .format(order_id='ord_id', date_created='date_created', date_delivery='date_deliver',
                            costumer_name='client', costumer_site='site',
                            total_weight='tot_weight', rows='2', username='user', type='הזמנת ברזל')
print(msg)
