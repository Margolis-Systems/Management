import sys

sys.path.insert(1, 'C:\\Server')
import configs


mongo = configs.mongo
# query = {'title':'order_status_change',"operation.status":{'$nin':['NEW','Processed','Production','canceled']} }
# logs = mongo.read_collection_list('logs', query)
# ddd = {}
# for l in logs:
#     if l['operation']['order_id'] not in ddd:
#         ddd[l['operation']['order_id']] = l['timestamp']
#         print(l['operation']['order_id'], l['timestamp'], l['operation']['status'])

all_orders = mongo.read_collection_list('orders')
for order in all_orders:
    print(order['order_id'])
    for r in order['rows']:
        while 'order_status_' in r['status']:
            r['status'] = r['status'].replace('order_status_', '')
    mongo.update_one('orders', {'order_id': order['order_id']}, order, '$set')
