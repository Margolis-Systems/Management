import sys

sys.path.insert(1, 'C:\\Server')
import configs


mongo = configs.mongo
import pandas as pd
def get_order_data_V1(order_id, job_id="", split="", reverse=True):
    query = {'order_id': order_id, 'job_id': {'$ne': "0"}, 'info': {'$exists': False}, 'type': {'$ne': 'integration'}}
    if job_id:
        query['job_id'] = job_id
    if split:
        query['order_split'] = int(split)
    order_data = list(mongo.read_collection_list('orders', query))
    # if not order_data:
    #     return None, None, None
    additional = mongo.read_collection_one('orders', {'order_id': order_id, 'job_id': "0"})
    info = mongo.read_collection_one('orders', {'order_id': order_id, 'info': {'$exists': True}})['info']
    if info['type'] == 'R':
        info['type'] = 'regular'
    info['order_id'] = order_id
    for row in order_data:
        row['status'] = 'order_status_' + row['status']
        if info['type'] == 'rebar':
            row['diam'] = row['diam_x']
            row['pitch'] = row['x_pitch']
    info['order_id'] = order_id
    # info['status'] = 'order_status_' + info['status']
    order_data.sort(key=lambda k: int(k['job_id']), reverse=reverse)
    return order_data.copy(), info, additional


query = {'info': {'$exists': True}, 'info.type': 'integration'}
orders_df = mongo.read_collection_df('orders', query=query)
info_df = pd.json_normalize(orders_df['info'])
new_df = pd.concat([orders_df['order_id'], info_df], axis=1).fillna(0)
ord_list = list(new_df['order_id'])
mongo.delete_many('orders', {'job_id': '0'})
for ord_id in ord_list:
    rows, info, ad = get_order_data_V1(ord_id, reverse=False)
    del(info['order_id'])
    doc = {'order_id': ord_id, 'info': info, 'rows': rows}
    mongo.delete_many('orders', {'order_id': ord_id})
    mongo.insert_collection_one('orders', doc)
