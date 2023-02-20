import db_handler
import json
import os
import pandas as pd
from datetime import datetime

mongo = db_handler.DBHandle()
# Data lists
weight = mongo.read_collection_one("data_lists", {"name": "weights"})['data']
shapes = mongo.read_collection_one("data_lists", {"name": "shapes"})['data']

'''________________________PAGES___________________________ '''


def orders(data_to_display):
    # Read all orders data with Info, mean that it's not including order rows
    orders_df = mongo.read_collection_df('orders', query={'info': {'$exists': True}})
    if not orders_df.empty:
        # normalize json to df
        info_df = pd.json_normalize(orders_df['info'])
        # add order id from main df
        new_df = pd.concat([orders_df['order_id'],info_df], axis=1)
        return new_df[data_to_display].to_dict('index')
    else:
        return None


def edit_order(order_id):
    # Read all data of this order
    order = mongo.read_collection_df('orders', query={'order_id': order_id})
    info = order[order['info'].notnull()]['info'][0]
    rows = order[order['info'].isnull()].drop(['info'], axis=1).to_dict('index')
    info['order_id'] = order_id
    if info['type'] == 'rebar':
        # order_type = 'rebar_edit.html'
        data_to_display = {'קוטר': True, 'סוג': True, 'כמות': True, 'משקל': False, 'הזמנת_ייצור': False, 'אורך': True,
                           'רוחב': True}
    else:
        # order_type = 'edit.html'
        data_to_display = {'מספר_ברזל': False ,'אלמנט': False, 'קוטר': True, 'צורה': True, 'כמות': True, 'משקל': False,
                           'אורך': False}
    order_type = '/rebar_edit.html'
    # data_to_display = ['קוטר','חור','כמות','משקל','מלאי']
    # data_to_display = {'קוטר': True, 'חור': True, 'כמות': True, 'משקל': False, 'מלאי': False, 'אורך':False, 'צורה':False}

    order_data = {'info': info, 'data_to_display': data_to_display, 'order_rows': rows}
    return order_data, order_type


'''_____________________FUNCTIONS___________________________'''


def new_order_id():
    orders_df = mongo.read_collection_df('orders', query={'info': {'$exists': True}})
    if orders_df.empty:
        return 1
    return str(int(max(orders_df['order_id'].unique().tolist())) + 1)


def new_order(info_data):
    client = info_data['client']
    site = info_data['site']
    order_type = info_data['type']
    order_id = new_order_id()
    # order = {'order_id': order_id, 'info': info_data}
    order = {'order_id': order_id, 'info': {'costumer': client, 'site': site, 'date_created': ts(), 'type': order_type}}
    mongo.insert_collection_one('orders', order)
    return order_id


def new_order_row(req_form_data, order_id):
    new_row = {'order_id': order_id}
    special_list = ['shape_data']
    for item in req_form_data:
        if item not in special_list:
            new_row[item] = req_form_data[item]
    if 'shape_data' in req_form_data:
        print()
        # todo: complete
    else:
        bars_len = calc_bars_len(req_form_data)
        new_row['משקל'] = int(bars_len * float(req_form_data['כמות']) * weight[req_form_data['קוטר']] / 100)
    # mongo.upsert_collection_one('orders', {'_id': doc_id}, new_row)
    mongo.insert_collection_one('orders', new_row)


def calc_bars_len(req_form_data):
    if 'שארית' in req_form_data:
        if req_form_data['שארית'].isdigit:
            trim = float(req_form_data['שארית'])
        else:
            trim = 0
    else:
        trim = 10

    if 'קוטר' in req_form_data:
        if req_form_data['קוטר'].isdigit:
            y_diam = x_diam = int(req_form_data['קוטר'])
        else:
            y_diam = x_diam = 0
    else:
        x_diam = float(req_form_data['קוטר_x'])
        y_diam = float(req_form_data['קוטר_y'])

    if 'ייצור_למלאי' in req_form_data: # todo: complete
        creat_perepherial_order = True
    else:
        creat_perepherial_order = False

    rebar_len = float(req_form_data['אורך'])
    rebar_width = float(req_form_data['רוחב'])
    hole = int(req_form_data['סוג'].split('X')[0])
    qnt = float(req_form_data['כמות'])
    x_bars = {'qnt': (rebar_len / hole) * qnt, 'length': rebar_width, 'diam': x_diam}
    y_bars = {'qnt': (rebar_width / hole - trim) * qnt, 'length': rebar_len, 'diam': y_diam}
    if creat_perepherial_order:
        peripheral_orders([x_bars, y_bars])
    return (x_bars['qnt'] * x_bars['length'] * weight[str(x_bars['diam'])] +
            y_bars['qnt'] * y_bars['length'] * weight[str(y_bars['diam'])]) / 100


def gen_client_list():
    return []


def peripheral_orders(add_orders): # todo: complete
    for order in add_orders:
        order_id = 'מלאי'
        order_weight = float(order['length']) * float(order['qnt']) * weight[str(order['diam'])] / 100
        info = {'costumer': 'מלאי', 'date_created': ts()}
        mongo.upsert_collection_one('orders', {'order_id': 'מלאי'}, {'order_id': order_id, 'info': info})
        peripheral_order = {'order_id': order_id, 'כמות': order['qnt'], 'צורה': 1, 'אורך': order['length'],
                             'קוטר': order['diam'], 'משקל': order_weight}
        mongo.insert_collection_one('orders', peripheral_order)


def ts():
    return datetime.now().strftime('%d-%m-%Y %H:%M:%S')
