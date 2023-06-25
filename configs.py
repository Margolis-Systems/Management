import json
import os

import db_handler

mongo = db_handler.DBHandle()

conf_dir = "C:\\Server\\config.json"
if not os.path.exists(conf_dir):
    conf_dir = "C:\\projects\\Tzomet\\Management\\config.json"
with open(conf_dir, 'r', encoding="utf-8") as config_file:
    config = json.load(config_file)

server = config['server']
server_port = config['server_port']
mongo_adr = config['mongo_adr']
db_users = config['db_users']
db_main = config['db_main']
orders_collection = config['orders_collection']
users_collection = config['users_collection']
orders_reverse = config['orders_reverse']
net_print_dir = config['net_print_dir']
company_name = config['company_name']
# rebar_weights = mongo.read_collection_one("data_lists", {"name": "rebar_weights"})['data']
data_to_display = mongo.read_collection_one("data_lists", {"name": "data_to_display"})['data']
weights = mongo.read_collection_one("data_lists", {"name": "weights"})['data']
shapes = mongo.read_collection_one("data_lists", {"name": "shapes"})['data']
rebar_catalog = mongo.read_collection_one("data_lists", {"name": "rebar_catalog"})['data']
print_dict = mongo.read_collection_one('data_lists', {'name': 'bartender_dict'})['data']
bartender_formats = mongo.read_collection_one('data_lists', {'name': 'bartender_formats'})['data']
printers = mongo.read_collection_one('data_lists', {'name': 'printers'})['data']
