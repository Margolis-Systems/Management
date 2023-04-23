import db_handler
import pandas as pd
from datetime import datetime
import configs
import main

mongo = db_handler.DBHandle()
# Data lists
# rebar_weights = mongo.read_collection_one("data_lists", {"name": "rebar_weights"})['data']
# data_to_display = mongo.read_collection_one("data_lists", {"name": "data_to_display"})['data']
# weights = mongo.read_collection_one("data_lists", {"name": "weights"})['data']
# shapes = mongo.read_collection_one("data_lists", {"name": "shapes"})['data']
# rebar_catalog = mongo.read_collection_one("data_lists", {"name": "rebar_catalog"})['data']

'''________________________PAGES___________________________ '''


def orders():
    # Read all orders data with Info, mean that it's not including order rows
    orders_df = mongo.read_collection_df('orders', query={'info': {'$exists': True}})
    if not orders_df.empty:
        # normalize json to df
        info_df = pd.json_normalize(orders_df['info'])
        # add order id from main df
        new_df = pd.concat([orders_df['order_id'], info_df], axis=1)
        return new_df[configs.data_to_display['orders']].to_dict('index'), configs.data_to_display['orders']
    else:
        return [], []


def edit_order_data():
    order_id, username = main.session['order_id'], main.session['username']
    job_id = ""
    if 'job_id' in main.session.keys():
        job_id = main.session['job_id']
    # Read all data of this order
    rows, info = get_order_data(order_id, job_id)
    # #todo: return None if order 'NEW' from another user
    # 0: Not required, 1: Required, 2: Autofill, 3: Drop menu, 4: Checkbox
    keys_to_display = configs.data_to_display['new_row_' + info['type']]
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
    order = mongo.read_collection_df('orders', query={'order_id': order_id, 'job_id': {'$ne': "0"}})
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
    user = main.session['username']
    client = info_data['client']
    client_id = ""
    site = info_data['site']
    order_type = info_data['type']
    order_id = new_order_id()
    order = {'order_id': order_id, 'info': {'created_by': user, 'date_created': ts(), 'type': order_type,
                                            'costumer_name': client, 'costumer_id': client_id, 'costumer_site': site}}
    mongo.insert_collection_one('orders', order)
    return order_id


def new_order_row():
    order_id = main.session['order_id']
    req_form_data = main.request.form
    temp_order_data = mongo.read_collection_one('orders', {'order_id': order_id, 'job_id': "0"})
    # Order peripheral data handling
    if 'x_form' in req_form_data.keys() or 'y_form' in req_form_data.keys() or 'shape_data' in req_form_data.keys():
        if temp_order_data and 'shape_data' not in req_form_data.keys():
            new_row = temp_order_data.copy()
        else:
            new_row = {'order_id': order_id, 'job_id': "0"}
        if 'x_form' in req_form_data:
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
            for item in req_form_data:
                if item.isdigit() or item == 'shape_data':
                    new_row[item] = req_form_data[item]
        mongo.upsert_collection_one('orders', {'order_id': order_id, 'job_id': "0"}, new_row)
        return
    else:
        job_id = gen_job_id(order_id)
        new_row = {'order_id': order_id, 'job_id': job_id, 'status': 'New', 'date_created': ts()}
        for item in req_form_data:
            if req_form_data[item] not in ['---', ''] and '_hid' not in item:
                new_row[item] = req_form_data[item]
    # Order data handling
    if 'mkt' in new_row:
        cat_item = configs.rebar_catalog[new_row['mkt']]
        for item in cat_item:
            if item not in ['unit_weight', 'pack_quantity']:
                new_row[item] = cat_item[item]
        new_row['weight'] = round(
            float(configs.rebar_catalog[new_row['mkt']]['unit_weight']) * float(new_row['quantity']), 1)
        if 'הזמנת_ייצור' in new_row:
            pitch = int(new_row['pitch'].split('X')[0])
            x_bars = {'length': new_row['width'], 'qnt': int(new_row['quantity']) * (int(new_row['length']) / pitch),
                      'diam': new_row['diam']}
            y_bars = {'length': new_row['length'],
                      'qnt': ((int(new_row['width']) - 10) / pitch + 1) * int(new_row['quantity']),
                      'diam': new_row['diam']}
            peripheral_orders([x_bars, y_bars], order_id, job_id)
    elif 'diam_x' in new_row:  # or 'diam_y'
        new_row['mkt'] = "2005020000"
        if 'length' in new_row and 'width' in new_row:
            new_row['description'] = "רשת מיוחדת קוטר" + new_row['diam_x'] + "|" + new_row['diam_y'] + \
                                     "\n" + new_row['length'] + "X" + new_row['width']
        else:
            # Peripheral data not compatible with form data
            return
        # todo: complete
        x_bars = 0
        y_bars = 0
        new_row['weight'] = calc_weight(new_row['diam_x'], new_row['width'],
                                        x_bars) + calc_weight(new_row['diam_y'], new_row['length'], y_bars)
        if temp_order_data:
            for item in temp_order_data:
                if item != 'job_id':
                    new_row[item] = temp_order_data[item]
        mongo.delete_many('orders', {'order_id': order_id, 'job_id': "0"})
    elif 'shape' in req_form_data:
        if temp_order_data:
            if temp_order_data['shape_data'] == new_row['shape']:
                shape_data = []
                for item in temp_order_data:
                    if item.isdigit():
                        shape_data.append(temp_order_data[item])
                new_row['shape_data'] = shape_data
                new_row['weight'] = calc_weight(new_row['diam'], new_row['length'], new_row['quantity'])
            else:
                # Shape data not compatible with form data
                return
        else:
            # No shape data
            return
    else:
        return
    mongo.upsert_collection_one('orders', {'order_id': new_row['order_id'], 'job_id': new_row['job_id']}, new_row)


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


def calc_weight(diam, length, qnt):
    return round(float(length) * float(qnt) * configs.weights[str(diam)] / 100, 2)


def peripheral_orders(add_orders, order_id, job_id):
    description = "הזמנת ייצור להכנת רשת. מספר הזמנת מקור: " + order_id + "\nשורה מספר: " + job_id
    order_id += "_R"
    for order in add_orders:
        order_weight = calc_weight(order['length'], order['qnt'], order['diam'])
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
        diam = []
        cat_num = []
        rebar_type = []
        for item in configs.rebar_catalog:
            if configs.rebar_catalog[item]['diam'] not in diam:
                diam.append(configs.rebar_catalog[item]['diam'])
            if item not in cat_num:
                cat_num.append(item)
            if configs.rebar_catalog[item]['pitch'] not in rebar_type:
                rebar_type.append(configs.rebar_catalog[item]['pitch'])
        diam.sort()
        rebar_type.sort()
        cat_num.sort()
        patterns = {'pitch': '|'.join(rebar_type), 'diam': '|'.join(diam), 'mkt': '|'.join(cat_num)}
        lists = {'pitch': rebar_type, 'diam': diam, 'mkt': list(configs.rebar_catalog.keys())}
    elif order_type == 'rebar_special':
        diam = ['5.5', '6.5', '7.5', '8', '10', '12', '14', '16', '18']
        cat_num = []
        rebar_type = []
        for item in configs.rebar_catalog:
            if item not in cat_num:
                cat_num.append(item)
            if configs.rebar_catalog[item]['pitch'].split('X')[0] not in rebar_type:
                rebar_type.append(configs.rebar_catalog[item]['pitch'].split('X')[0])
        rebar_type.sort()
        cat_num.sort()
        patterns = {'pitch_x': '|'.join(rebar_type), 'pitch_y': '|'.join(rebar_type), 'diam_x': '|'.join(diam),
                    'diam_y': '|'.join(diam), 'mkt': '|'.join(cat_num)}
        lists = {'pitch_x': rebar_type, 'pitch_y': rebar_type, 'diam_x': diam, 'diam_y': diam,
                 'mkt': list(configs.rebar_catalog.keys())}
    else:
        shapes_list = configs.shapes.keys()
        diam = list(configs.weights.keys())
        diam.sort(key=lambda k: float(k))
        lists = {'diam': diam, 'shape': shapes_list}
        patterns = {'diam': '|'.join(diam), 'shape': '|'.join(shapes_list)}
    return lists, patterns
