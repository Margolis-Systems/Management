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
shapes = {}


def read_shapes():
    with open(main_dir+'lists\\shapes.json', encoding="utf-8") as shapes_file:
        shapes_json = json.load(shapes_file)
        global shapes
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
data_to_display = {}
weights = {}
rebar_catalog = {}
girders_catalog = {}

print_dict = {}
bartender_formats = {}


def read_mongo_conf():
    global data_to_display
    global weights
    global rebar_catalog
    global girders_catalog

    global print_dict
    global bartender_formats
    data_to_display = mongo.read_collection_one("data_lists", {"name": "data_to_display"})['data']
    weights = mongo.read_collection_one("data_lists", {"name": "weights"})['data']
    rebar_catalog = mongo.read_collection_one("data_lists", {"name": "rebar_catalog"})['data']
    girders_catalog = mongo.read_collection_one("data_lists", {"name": "girders_catalog"})['data']

    print_dict = mongo.read_collection_one('data_lists', {'name': 'bartender_dict'})['data']
    bartender_formats = mongo.read_collection_one('data_lists', {'name': 'bartender_formats'})['data']


read_shapes()
read_mongo_conf()
# todo: read from mongo
reports_dir = os.getcwd()+'\\reports\\'
print_dicts = {'regular': {}, 'rebar': {}, 'pile': {}, 'girders': {}}

printers = mongo.read_collection_one('data_lists', {'name': 'printers'})['data']
circle = ['6', '8', '9', '10', '11', '16', '20', '35', '36', '37', '39', '40', '41', '42', '44', '63', '66', '68',
           '76', '77', '78', '79', '80', '81', '82', '83', '91', '92', '103', '119', '120', '135', '139', '140', '161',
           '216', '331', '925', '965', '966']
_circle = ['925', '966', '215', '216', '78', '79', '119', '68', '36', '44', '16', '6', '331', '161', '82', '120']
phones_to_notify = ['0509595953', '0509393938', '0528008018', '0509393934']
html_no_float = ['quantity']
order_types = ['regular', 'rebar_special', 'rebar', 'R', 'girders', 'piles']
new_order_types = ['regular', 'rebar', 'rebar_special', 'piles', 'girders']
order_statuses = ['NEW', 'Processed', 'Production', 'Finished', 'Loaded', 'PartlyDelivered', 'Delivered',
                  'PartlyDeliveredClosed', 'Outsource', 'canceled']
all_statuses = ['NEW', 'Processed', 'Production', 'InProduction', 'Start', 'Finished', 'Loaded', 'PartlyDelivered', 'Delivered',
                  'PartlyDeliveredClosed', 'Outsource', 'canceled']
oper_multi_scan = ['operator34', 'operator17', 'operator18']
bend_diam = {'5.5': 2.2, '6.5': 3, '8': 3.2, '10': 4, '12': 4.8, '14': 5.6, '16': 6.4, '18': 7.2, '20': 14, '22': 15.4, '24':17.5, '25': 17.5, '28': 19.6, '32': 22.4, '36': 25.2}
