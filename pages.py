import db_handler
import pandas as pd
from datetime import datetime

import main

mongo = db_handler.DBHandle()
# Data lists
# rebar_weights = mongo.read_collection_one("data_lists", {"name": "rebar_weights"})['data']
data_to_display = mongo.read_collection_one("data_lists", {"name": "data_to_display"})['data']
weights = mongo.read_collection_one("data_lists", {"name": "weights"})['data']
shapes = mongo.read_collection_one("data_lists", {"name": "shapes"})['data']
rebar_catalog = mongo.read_collection_one("data_lists", {"name": "rebar_catalog"})['data']

'''________________________PAGES___________________________ '''


def orders():
    # Read all orders data with Info, mean that it's not including order rows
    orders_df = mongo.read_collection_df('orders', query={'info': {'$exists': True}})
    if not orders_df.empty:
        # normalize json to df
        info_df = pd.json_normalize(orders_df['info'])
        # add order id from main df
        new_df = pd.concat([orders_df['order_id'], info_df], axis=1)
        return new_df[data_to_display['orders']].to_dict('index'), data_to_display['orders']
    else:
        return [], []


def edit_order_data():
    order_id, username = main.session['order_id'], main.session['username']
    job_id = ""
    if 'job_id' in main.session.keys():
        job_id = main.session['job_id']
    # Read all data of this order
    rows, info = get_order_data(order_id, job_id)
    # 0: Not required, 1: Required, 2: Autofill, 3: Drop menu, 4: Checkbox
    keys_to_display = data_to_display['new_row_' + info['type']]
    order_data = {'info': info, 'data_to_display': keys_to_display, 'order_rows': rows}
    if info['type'] == 'rebar_special':
        order_data['include'] = 'spec_rebar_editor.html'
    lists, patterns = gen_patterns(info['type'])
    dictionary = get_dictionary(username)
    return order_data, [lists, patterns, dictionary]


def jobs_list(order_type='regular'):
    type_list = mongo.read_collection_df('orders', query={'info.type': order_type})
    type_list = type_list['order_id'].to_list()
    all_orders = mongo.read_collection_df('orders', query={'order_id': {'$in': type_list}})
    all_jobs = all_orders[all_orders['job_id'].notna()]
    if all_jobs.empty:
        return {}
    all_jobs = all_jobs.sort_values(by=['order_id', 'job_id'], ascending=[False, True])
    columns = ['order_id', 'job_id', 'status', 'date_created', 'description']
    return all_jobs[columns].to_dict('records')


'''_____________________FUNCTIONS___________________________'''


def get_dictionary(username):
    all_dicts = mongo.read_collection_one('data_lists', {'name': 'dictionary'})['data']
    lang = mongo.read_collection_one('users', {'name': username})['lang']
    dictionary = all_dicts[lang]
    return dictionary


def get_order_data(order_id, job_id="", reverse=True):
    order = mongo.read_collection_df('orders', query={'order_id': order_id})
    if order.empty:
        return False, False
    info = order[order['info'].notnull()]['info'][0]
    order_data = order[order['info'].isnull()].drop(['info'], axis=1).fillna("").to_dict('index')
    rows = []
    for key in order_data:
        if job_id == "" or order_data[key]['job_id'] == job_id:
            row_data = order_data[key]
            row_data['job_id'] = order_data[key]['job_id']
            rows.append(row_data)
    info['order_id'] = order_id
    rows.sort(key=lambda k: int(k['job_id']), reverse=reverse)
    return rows, info


def new_order_id():
    new_id = "1"
    orders_df = mongo.read_collection_df('orders', query={'info': {'$exists': True}})
    if orders_df.empty:
        return new_id
    order_ids_list = orders_df['order_id'].unique().tolist()
    for _id in order_ids_list:
        if _id.isdigit():
            if int(_id) >= int(new_id):
                new_id = str(int(_id) + 1)
    return new_id


def new_order(info_data):
    client = info_data['client']
    site = info_data['site']
    order_type = info_data['type']
    order_id = new_order_id()
    order = {'order_id': order_id, 'info': {'date_created': ts(), 'costumer_id': client, 'costumer_site': site,
                                            'type': order_type}}
    mongo.insert_collection_one('orders', order)
    return order_id


def new_order_row():
    order_id = main.session['order_id']
    job_id = gen_job_id(order_id)
    new_row = {'order_id': order_id, 'job_id': job_id, 'status': 'New', 'date_created': ts()}
    req_form_data = main.request.form
    if 'x_form' in req_form_data.keys() or 'y_form' in req_form_data.keys() or 'shape_data' in req_form_data.keys():
        new_row['job_id'] = "0"
        editor_new_row = mongo.read_collection_one('orders', {'order_id': order_id, 'job_id': "0"})
    else:
        for item in req_form_data:
            if req_form_data[item] != '---':
                new_row[item] = req_form_data[item]
    if 'mkt' in new_row:
        cat_item = rebar_catalog[new_row['mkt']]
        for item in cat_item:
            if item not in ['unit_weight', 'pack_quantity']:
                new_row[item] = cat_item[item]
        new_row['weight'] = round(float(rebar_catalog[new_row['mkt']]['unit_weight']) * float(new_row['quantity']), 1)
        if 'הזמנת_ייצור' in new_row:
            pitch = int(new_row['pitch'].split('X')[0])
            x_bars = {'length': new_row['width'], 'qnt': int(new_row['quantity']) * (int(new_row['length']) / pitch),
                      'diam': new_row['diam']}
            y_bars = {'length': new_row['length'],
                      'qnt': ((int(new_row['width']) - 10) / pitch + 1) * int(new_row['quantity']),
                      'diam': new_row['diam']}
            peripheral_orders([x_bars, y_bars], order_id, job_id)
    elif 'diam_x' in new_row:  # or 'diam_y'
        editor_new_row = mongo.read_collection_one('orders', {'order_id': order_id, 'job_id': "0"})
        new_row['mkt'] = "2005020000"
        new_row['description'] = "רשת מיוחדת קוטר" + new_row['diam_x'] + "|" + new_row['diam_x'] + \
                                 "\n" + new_row['length'] + "X" + new_row['width']
        new_row['weight'] = round(calc_bars_weight(), 1)
        for item in editor_new_row:
            if item != 'job_id':
                new_row[item] = editor_new_row[item]
        mongo.delete_many('orders', {'order_id': order_id, 'job_id': "0"})
    else:
        if editor_new_row:
            new_row = editor_new_row.copy()
        # main.session['job_id'] = job_id
        if 'shape_data' in req_form_data:
            print(new_row['shape_data'])
            # todo: complete
        elif 'x_form' in req_form_data:
            if 'x_pitch' in new_row:
                new_row['x_pitch'].append(req_form_data['x_pitch'])
                new_row['x_length'].append(req_form_data['x_length'])
            else:
                new_row['x_pitch'] = [req_form_data['x_pitch']]
                new_row['x_length'] = [req_form_data['x_length']]
        elif 'y_form' in req_form_data:
            if 'y_pitch' in new_row:
                new_row['y_pitch'].append(req_form_data['y_pitch'])
                new_row['y_length'].append(req_form_data['y_length'])
            else:
                new_row['y_pitch'] = [req_form_data['y_pitch']]
                new_row['y_length'] = [req_form_data['y_length']]
        else:
            return
    mongo.upsert_collection_one('orders', {'order_id': new_row['order_id'], 'job_id': new_row['job_id']}, new_row)


def calc_bars_weight():
    total_weight = 0
    return total_weight


def gen_client_list(client):
    sites_list = []
    client_list = []
    client_data = {}
    if client:
        client_data = mongo.read_collection_one('costumers', {'name': client})
    else:
        costumers = mongo.read_collection_df('costumers')
        if not costumers.empty:
            client_list = costumers['name'].to_list()
    if client_data:
        sites_list = client_data['sites']
        client_list = client
    return client_list, sites_list


def peripheral_orders(add_orders, order_id, job_id):
    description = "הזמנת ייצור להכנת רשת. מספר הזמנת מקור: " + order_id + "\nשורה מספר: " + job_id
    order_id += "_R"
    # mongo.delete_many('orders', {'order_id': order_id, 'status': 'New'})
    for order in add_orders:
        order_weight = float(order['length']) * float(order['qnt']) * weights[str(order['diam'])] / 100
        info = {'costumer_id': 'צומת ברזל', 'date_created': ts(), 'type': 'regular'}
        mongo.upsert_collection_one('orders', {'order_id': order_id, 'info': {'$exists': True}},
                                    {'order_id': order_id, 'info': info})
        peripheral_order = {'order_id': order_id, 'job_id': gen_job_id(order_id), 'status': "New", 'date_created': ts(),
                            'description': description, 'quantity': order['qnt'], 'shape': 1, 'length': order['length'],
                            'diam': order['diam'], 'weight': order_weight}
        mongo.insert_collection_one('orders', peripheral_order)


def ts(mode=""):
    if not mode:
        return datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    elif mode == "file_name":
        return datetime.now().strftime('%d-%m-%Y_%H-%M-%S.%f')


def gen_job_id(order_id):
    job_ids_df = mongo.read_collection_df('orders', query={'order_id': order_id, 'info': {'$exists': False}})
    if job_ids_df.empty:
        return "1"
    job_ids = job_ids_df['job_id'].tolist()
    return str(int(max(job_ids)) + 1)


def gen_patterns(order_type='regular'):
    if order_type == 'rebar':
        # catalog = mongo.read_collection_one('data_lists', query={'name': 'rebar_catalog'})['data']
        diam = []
        cat_num = []
        rebar_type = []
        for item in rebar_catalog:
            if rebar_catalog[item]['diam'] not in diam:
                diam.append(rebar_catalog[item]['diam'])
            if item not in cat_num:
                cat_num.append(item)
            if rebar_catalog[item]['pitch'] not in rebar_type:
                rebar_type.append(rebar_catalog[item]['pitch'])
        diam.sort()
        rebar_type.sort()
        cat_num.sort()
        patterns = {'pitch': '|'.join(rebar_type), 'diam': '|'.join(diam), 'mkt': '|'.join(cat_num)}
        lists = {'pitch': rebar_type, 'diam': diam, 'mkt': list(rebar_catalog.keys())}
    elif order_type == 'rebar_special':
        # catalog = mongo.read_collection_one('data_lists', query={'name': 'rebar_catalog'})['data']
        # todo: --------------
        diam = ['5.5', '6.5', '7.5', '8', '10', '12', '14', '16', '18']
        # todo: --------------
        cat_num = []
        rebar_type = []
        for item in rebar_catalog:
            # if catalog[item]['diam'] not in diam:
            #     diam.append(catalog[item]['diam'])
            if item not in cat_num:
                cat_num.append(item)
            if rebar_catalog[item]['pitch'].split('X')[0] not in rebar_type:
                rebar_type.append(rebar_catalog[item]['pitch'].split('X')[0])
        # diam.sort()
        rebar_type.sort()
        cat_num.sort()
        patterns = {'pitch_x': '|'.join(rebar_type), 'pitch_y': '|'.join(rebar_type), 'diam_x': '|'.join(diam),
                    'diam_y': '|'.join(diam), 'mkt': '|'.join(cat_num)}
        lists = {'pitch_x': rebar_type, 'pitch_y': rebar_type, 'diam_x': diam, 'diam_y': diam,
                 'mkt': list(rebar_catalog.keys())}
    else:
        shapes_list = shapes.keys()
        diam = weights.keys()
        lists = {'diam': diam, 'shape': shapes_list}
        patterns = {'diam': '|'.join(diam), 'shape': '|'.join(shapes_list)}
    return lists, patterns
