import sys

sys.path.insert(1, 'C:\\Server')
import configs


mongo = configs.mongo
query = {'title':'order_status_change',"operation.status":{'$nin':['NEW','Processed','Production','canceled']} }
logs = mongo.read_collection_list('logs', query)
ddd = {}
for l in logs:
    if l['operation']['order_id'] not in ddd:
        ddd[l['operation']['order_id']] = l['timestamp']
        print(l['operation']['order_id'], l['timestamp'], l['operation']['status'])
