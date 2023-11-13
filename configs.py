import json
import os
from collections import OrderedDict
import db_handler

mongo = db_handler.DBHandle()

main_dir = "C:\\Server\\"
if not os.path.exists(main_dir):
    main_dir = "C:\\projects\\Tzomet\\Management\\"
with open(main_dir+'config.json', 'r', encoding="utf-8") as config_file:
    config = json.load(config_file)

with open(main_dir+'lists\\shapes.json') as shapes_file:
    shapes_json = json.load(shapes_file)
    shapes = dict(OrderedDict(sorted(shapes_json.items(), key=lambda t: int(t[0]))))

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

data_to_display = mongo.read_collection_one("data_lists", {"name": "data_to_display"})['data']
weights = mongo.read_collection_one("data_lists", {"name": "weights"})['data']
rebar_catalog = mongo.read_collection_one("data_lists", {"name": "rebar_catalog"})['data']
girders_catalog = mongo.read_collection_one("data_lists", {"name": "girders_catalog"})['data']

print_dict = mongo.read_collection_one('data_lists', {'name': 'bartender_dict'})['data']
bartender_formats = mongo.read_collection_one('data_lists', {'name': 'bartender_formats'})['data']
# todo: read from mongo
reports_dir = os.getcwd()+'\\reports\\'
print_dicts = {'regular': {}, 'rebar': {}, 'pile': {}, 'girders': {}}

printers = mongo.read_collection_one('data_lists', {'name': 'printers'})['data']
circle = ['925', '966', '215', '216', '78', '79', '119', '68', '36', '44', '16', '6', '331']
order_types = {'regular', 'rebar', 'R', 'girders', 'piles'}
order_statuses = {'NEW', 'Processed', 'Production', 'Finished', 'Loading', 'Delivered', 'PartlyDelivered',
                  'PartlyDeliveredClosed', 'Outsource'}
