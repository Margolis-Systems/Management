import db_handler
import pandas as pd
from datetime import datetime
import configs
import main
import math

mongo = db_handler.DBHandle()


def orders():
    # Read all orders data with Info, mean that it's not including order rows
    orders_df = mongo.read_collection_df('orders', query={'info': {'$exists': True}})
    if not orders_df.empty:
        # normalize json to df
        info_df = pd.json_normalize(orders_df['info'])
        info_df['date_created'] = pd.to_datetime(info_df['date_created'], format='%d-%m-%Y %H:%M:%S')
        # add order id from main df
        new_df = pd.concat([orders_df['order_id'], info_df], axis=1)
        for item in configs.data_to_display['orders']:
            if item not in new_df.columns:
                new_df[item] = ""
        orders_info = new_df[configs.data_to_display['orders']].sort_values(by='date_created', ascending=False)
        return orders_info.to_dict('index'), configs.data_to_display['orders']
    else:
        return [], []


def edit_order_data():
    order_id, username = main.session['order_id'], main.session['username']
    job_id = ""
    if 'job_id' in main.session.keys():
        job_id = main.session['job_id']
    # Read all data of this order
    rows, info, additional = get_order_data(order_id, job_id)
    # if info['created_by'] != main.session['username']:
    #     return {}, []
    # 0: Not required, 1: Required, 2: Autofill, 3: Drop menu, 4: Checkbox
    keys_to_display = configs.data_to_display['new_row_' + info['type']]
    order_data = {'info': info, 'data_to_display': keys_to_display, 'order_rows': rows}
    if additional:
        order_data['include_data'] = additional
    if info['type'] == 'rebar_special':
        order_data['include'] = 'spec_rebar_editor.html'
    lists, patterns = gen_patterns(info['type'])
    dictionary = get_dictionary(username)
    return order_data, [lists, patterns, dictionary]


def jobs_list(order_type='regular'):
    type_list = mongo.read_collection_df('orders', query={'info.type': order_type})
    type_list = type_list['order_id'].to_list()
    all_orders = mongo.read_collection_df('orders', query={'order_id': {'$in': type_list}, 'job_id': {'$ne': "0"}})
    all_jobs = all_orders[all_orders['job_id'].notna()]
    if all_jobs.empty:
        return {}
    all_jobs = all_jobs.sort_values(by=['order_id', 'job_id'], ascending=[False, True])
    columns = ['order_id', 'job_id', 'status', 'date_created', 'description']
    return all_jobs[columns].to_dict('records')


def get_dictionary(username):
    all_dicts = mongo.read_collection_one('data_lists', {'name': 'dictionary'})['data']
    lang = mongo.read_collection_one('users', {'name': username})['lang']
    dictionary = all_dicts[lang]
    return dictionary


def get_order_data(order_id, job_id="", reverse=True):
    order = mongo.read_collection_df('orders', query={'order_id': order_id, 'job_id': {'$ne': "0"}})
    additional = mongo.read_collection_one('orders', {'order_id': order_id, 'job_id': "0"})
    # order = mongo.read_collection_df('orders', query={'order_id': order_id})
    if order.empty:
        return False, False
    info = order[order['info'].notnull()]['info'][0]
    order_data_df = order[order['info'].isnull()].drop(['info'], axis=1).fillna("")
    if not order_data_df.empty:
        order_data_df['weight'] = order_data_df['weight'].astype(int)
    order_data = order_data_df.to_dict('index')
    rows = []
    for key in order_data:
        if job_id == "" or order_data[key]['job_id'] == job_id:
            row_data = order_data[key]
            rows.append(row_data)
    info['order_id'] = order_id
    rows.sort(key=lambda k: int(k['job_id']), reverse=reverse)
    return rows, info, additional


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
                                            'costumer_name': client, 'costumer_id': client_id, 'costumer_site': site, 'status': 'NEW'}}
    mongo.insert_collection_one('orders', order)
    return order_id


def new_order_row():
    order_id = main.session['order_id']
    req_form_data = main.request.form
    temp_order_data = mongo.read_collection_one('orders', {'order_id': order_id, 'job_id': "0"})
    # Order comment
    if 'comment_hid' in req_form_data:
        mongo.update_one_set('orders', {'order_id': order_id, 'info': {'$exists': True}},
                             {'info.comment': req_form_data['comment_hid']})
    # Order peripheral data handling
    if 'shape_data' in req_form_data.keys():
        new_row = {'order_id': order_id, 'job_id': "0"}
        for item in req_form_data:
            if item.isdigit() or item == 'shape_data':
                new_row[item] = req_form_data[item]
        mongo.upsert_collection_one('orders', {'order_id': order_id, 'job_id': "0"}, new_row)
        return
    else:
        job_id = gen_job_id(order_id)
        if 'job_id' in main.session.keys():
            if main.session['job_id'] != "":
                job_id = main.session['job_id']
        new_row = {'order_id': order_id, 'job_id': job_id, 'status': 'New', 'date_created': ts()}
        if 'x_length' in req_form_data.keys():
            new_row['x_length'] = []
            new_row['x_pitch'] = []
            new_row['y_length'] = []
            new_row['y_pitch'] = []
        for item in req_form_data:
            if req_form_data[item] not in ['---', ''] and '_hid' not in item:
                if '_length' in item or '_pitch' in item:
                    new_row[item[:item.find('h')+1]].append(req_form_data[item])
                else:
                    new_row[item] = req_form_data[item]
    # Order data handling
    if 'diam_x' in new_row:  # or 'diam_y'
        new_row['mkt'] = "2005020000"
        bars_x = 1
        bars_y = 1
        for i in range(len(new_row['x_length'])):
            if new_row['x_pitch'][i] != "0":
                new_row['trim_x_end'] = str(int(new_row['trim_x_end']) +
                                            int(new_row['x_length'][i]) % int(new_row['x_pitch'][i]))
                new_row['x_length'][i] = str(int(new_row['x_length'][i]) - (int(new_row['x_length'][i]) % int(new_row['x_pitch'][i])))
                bars_y += math.floor(int(new_row['x_length'][i]) / int(new_row['x_pitch'][i]))
            else:
                bars_y += 1
        new_row['length'] = sum(list(map(int, new_row['y_length'])))
        new_row['width'] = sum(list(map(int, new_row['x_length'])))
        new_row['length'] += int(new_row['trim_y_start']) + int(new_row['trim_y_end'])
        new_row['width'] += int(new_row['trim_x_start']) + int(new_row['trim_x_end'])
        for i in range(len(new_row['y_length'])):
            if new_row['y_pitch'][i] != "0":
                new_row['trim_y_end'] = str(int(new_row['trim_y_end']) +
                                            int(new_row['y_length'][i]) % int(new_row['y_pitch'][i]))
                new_row['y_length'][i] = str(int(new_row['y_length'][i]) - (int(new_row['y_length'][i]) % int(new_row['y_pitch'][i])))
                bars_x += math.floor(int(new_row['y_length'][i]) / int(new_row['y_pitch'][i]))
            else:
                bars_x += 1
        x_pitch = '('+')('.join(new_row['x_pitch'])+')'
        y_pitch = '('+')('.join(new_row['y_pitch'])+')'
        # x_length = '('+')('.join(new_row['x_length'])+')'
        # y_length = '('+')('.join(new_row['y_length'])+')'
        new_row['x_bars'] = int(bars_x)
        new_row['y_bars'] = int(bars_y)
        new_row['x_weight'] = calc_weight(new_row['diam_x'], new_row['width'], bars_x)
        new_row['y_weight'] = calc_weight(new_row['diam_y'], new_row['length'], bars_y)
        new_row['description'] = "V"+str(new_row['width'])+"X"+str(bars_x)+"X"+str(new_row['diam_x'])+"WBX"+x_pitch + \
                                 " H"+str(new_row['length'])+"X"+str(bars_y) + "X"+str(new_row['diam_y'])+"WBX"+y_pitch
        new_row['unit_weight'] = new_row['x_weight'] + new_row['y_weight']
        new_row['weight'] = new_row['unit_weight'] * int(new_row['quantity'])
        if 'הזמנת_ייצור' in new_row:
            x_bars = {'length': new_row['width'], 'qnt': bars_x * int(new_row['quantity']), 'diam': new_row['diam_x']}
            y_bars = {'length': new_row['length'], 'qnt': bars_y * int(new_row['quantity']), 'diam': new_row['diam_y']}
            peripheral_orders([x_bars, y_bars], order_id, job_id)
    elif 'mkt' in new_row:
        cat_item = configs.rebar_catalog[new_row['mkt']]
        for item in cat_item:
            if item not in ['pack_quantity']:
                new_row[item] = cat_item[item]
        pitch = int(new_row['x_pitch'])
        x_bars = {'length': new_row['width'], 'qnt': int(int(new_row['quantity']) * (int(new_row['length']) / pitch)),
                  'diam': new_row['diam_x']}
        y_bars = {'length': new_row['length'],
                  'qnt': int(((int(new_row['width']) - 10) / pitch + 1) * int(new_row['quantity'])),
                  'diam': new_row['diam_y']}
        new_row['description'] = "V250X"+str(int(int(new_row['length']) / pitch))+"X"+new_row['diam_x']+"WBX"+str(pitch) +\
                                 " H600X"+str(int((int(new_row['width']) - 10) / pitch + 1))+"X"+new_row['diam_y']+"WBX"+str(pitch)
        new_row['weight'] = round(float(configs.rebar_catalog[new_row['mkt']]['unit_weight']) * float(new_row['quantity']), 1)
        if 'הזמנת_ייצור' in new_row:
            peripheral_orders([x_bars, y_bars], order_id, job_id)
    elif 'shape' in req_form_data:
        new_row['description'] = ""
        if int(new_row['diam']) < 7:
            new_row['bar_type'] = "חלק"
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
                print("Shape data not compatible with form data")
                return
        else:
            # No shape data
            print("No shape data")
            return
    else:
        return
    for item in new_row:
        if isinstance(new_row[item], int):
            new_row[item] = str(new_row[item])
    mongo.upsert_collection_one('orders', {'order_id': new_row['order_id'], 'job_id': new_row['job_id']}, new_row)


def gen_client_list(client=""):
    sites_list = ""
    client_list = []
    if client:
        client_data = mongo.read_collection_one('costumers', {'name': client})
        if client_data:
            sites_list = client_data['sites']
            client_list = client
            return client_list, sites_list
    costumers = mongo.read_collection_df('costumers')
    if not costumers.empty:
        client_list = costumers['name'].to_list()
    return client_list, sites_list


def calc_weight(diam, length, qnt):
    return round(float(length) * float(qnt) * configs.weights[str(diam)] / 100, 2)


def peripheral_orders(add_orders, order_id, job_id):
    description = "הזמנת ייצור להכנת רשת. מספר הזמנת מקור: " + order_id + " שורה מספר: " + job_id
    order_id += "_R"
    for order in add_orders:
        order_weight = calc_weight(order['diam'], order['length'], order['qnt'])
        info = {'costumer_name': 'צומת ברזל', 'created_by': main.session['username'], 'date_created': ts(),
                'type': 'for_production'}
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
        return datetime.now().strftime('%d-%m-%Y_%H-%M-%S-%f')


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
            if configs.rebar_catalog[item]['diam_x'] not in diam:
                diam.append(configs.rebar_catalog[item]['diam_x'])
            if item not in cat_num:
                cat_num.append(item)
            if configs.rebar_catalog[item]['x_pitch'] not in rebar_type:
                pitch = configs.rebar_catalog[item]['x_pitch'] + "X" + configs.rebar_catalog[item]['y_pitch']
                rebar_type.append(pitch)
        diam.sort()
        rebar_type.sort()
        cat_num.sort()
        patterns = {'pitch': '|'.join(rebar_type), 'diam': '|'.join(diam), 'mkt': '|'.join(cat_num)}
        lists = {'pitch': rebar_type, 'diam': diam, 'mkt': list(configs.rebar_catalog.keys())}
    elif order_type == 'rebar_special':
        diam = ['5.5', '6.5', '7.5', '8', '10', '12', '14', '16', '18']
        cat_num = []
        rebar_type = []
        # for item in configs.rebar_catalog:
        #     if item not in cat_num:
        #         cat_num.append(item)
        #     if configs.rebar_catalog[item]['pitch'].split('X')[0] not in rebar_type:
        #         rebar_type.append(configs.rebar_catalog[item]['pitch'].split('X')[0])
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
        bar_type = ['מצולע', 'חלק']
        lists = {'diam': diam, 'shape': shapes_list, 'bar_type': bar_type}
        patterns = {'diam': '|'.join(diam), 'shape': '|'.join(shapes_list), 'bar_type': '|'.join(bar_type)}
    return lists, patterns
