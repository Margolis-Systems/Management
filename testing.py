import json
import os
import db_handler
import pages
import pandas as pd

mongo = db_handler.DBHandle()
with open("config.json") as config_file: config = json.load(config_file)
order = mongo.read_collection_df('orders', query={'order_id': 3})

info = order[order['info'].notnull()]['info'][0]
order_data = order[order['info'].isnull()].drop(['info'], axis=1).to_dict('index')
print(info)
print(order_data)
