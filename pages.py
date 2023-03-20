import db_handler
import pandas as pd
from datetime import datetime

mongo = db_handler.DBHandle()
# Data lists
weight = mongo.read_collection_one("data_lists", {"name": "weights"})['data']
shapes = mongo.read_collection_one("data_lists", {"name": "shapes"})['data']
rebar_catalog = mongo.read_collection_one("data_lists", {"name": "rebar_catalog"})['data']

'''________________________PAGES___________________________ '''


def orders(data_to_display):
    # Read all orders data with Info, mean that it's not including order rows
    orders_df = mongo.read_collection_df('orders', query={'info': {'$exists': True}})
    if not orders_df.empty:
        # normalize json to df
        info_df = pd.json_normalize(orders_df['info'])
        # add order id from main df
        new_df = pd.concat([orders_df['order_id'], info_df], axis=1)
        return new_df[data_to_display].to_dict('index')
    else:
        return []


def edit_order(order_id):
    # Read all data of this order
    rows, info = get_order_data(order_id)
    # 0: Not required, 1: Required, 2: Autofill, 3: Drop menu, 4: Checkbox
    if info['type'] == 'rebar':
        data_to_display = {'שורה': 2, 'מקט': 3, 'כמות': 1, 'קוטר': 2, 'סוג': 2, 'אורך': 2, 'רוחב': 2, 'הזמנת_ייצור': 4,
                           'משקל': 2}
    elif info['type'] == 'rebar_special':
        data_to_display = {'שורה': 2, 'מקט': 2, 'כמות': 1, 'קוטר_x': 3, 'קוטר_y': 3, 'סוג': 3, 'אורך': 1, 'רוחב': 1,
                           'הזמנת_ייצור': 4, 'משקל': 2}
    else:
        data_to_display = {'שורה': 2, 'מספר_ברזל': 0, 'אלמנט': 0, 'קוטר': 3, 'צורה': 3, 'כמות': 1, 'אורך': 2, 'משקל': 2}
    order_data = {'info': info, 'data_to_display': data_to_display, 'order_rows': rows}
    lists, patterns = gen_patterns(info['type'])
    return order_data, lists, patterns


'''_____________________FUNCTIONS___________________________'''


def get_order_data(order_id, reverse=True):
    order = mongo.read_collection_df('orders', query={'order_id': order_id})
    if order.empty:
        return False, False
    info = order[order['info'].notnull()]['info'][0]
    order_data = order[order['info'].isnull()].drop(['info'], axis=1).fillna("").to_dict('index')
    rows = []
    for key in order_data:
        row_data = order_data[key]
        row_data['שורה'] = key
        rows.append(row_data)
    info['order_id'] = order_id
    rows.sort(key=lambda k: k['שורה'], reverse=reverse)
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
    # order = {'order_id': order_id, 'info': info_data}
    order = {'order_id': order_id, 'info': {'date_created': ts(), 'costumer_id': client, 'costumer_site': site,
                                            'type': order_type}}
    mongo.insert_collection_one('orders', order)
    return order_id


def new_order_row(req_form_data, order_id):
    new_row = {'order_id': order_id, 'job_id': gen_job_id(order_id), 'status': 'New'}
    special_list = ['shape_data', 'משקל_יח']
    for item in req_form_data:
        if item not in special_list:
            new_row[item] = req_form_data[item]

    if 'מקט' in req_form_data:
        cat_item = rebar_catalog[req_form_data['מקט']]
        for item in cat_item:
            if item not in special_list:
                new_row[item] = cat_item[item]

    if 'shape_data' in req_form_data:
        print()
        # todo: complete
    else:
        new_row['מקט'] = "2005020000"
        new_row['תיאור'] = "רשת מיוחדת"
        new_row['משקל'] = round(calc_bars_weight(new_row, order_id), 1)
    # mongo.upsert_collection_one('orders', {'_id': doc_id}, new_row)
    mongo.insert_collection_one('orders', new_row)


def calc_bars_weight(req_form_data, order_id):
    # if 'שארית' in req_form_data:
    #     if req_form_data['שארית'].isdigit:
    #         trim = float(req_form_data['שארית'])
    #     else:
    #         trim = 0
    # else:
    #     trim = 10
    trim = 10
    if 'קוטר' in req_form_data:
        if req_form_data['קוטר'].isdigit:
            if "." in req_form_data['קוטר']:
                y_diam = x_diam = float(req_form_data['קוטר'])
            else:
                y_diam = x_diam = int(req_form_data['קוטר'])
        else:
            y_diam = x_diam = 0
    else:
        if "." in req_form_data['קוטר_x']:
            x_diam = float(req_form_data['קוטר_x'])
        else:
            x_diam = int(req_form_data['קוטר_x'])
        if "." in req_form_data['קוטר_y']:
            y_diam = float(req_form_data['קוטר_y'])
        else:
            y_diam = int(req_form_data['קוטר_y'])
    if 'הזמנת_ייצור' in req_form_data:
        create_peripheral_order = True
    else:
        create_peripheral_order = False
    rebar_len = float(req_form_data['אורך'])
    rebar_width = float(req_form_data['רוחב'])
    hole = int(req_form_data['סוג'].split('X')[0])
    qnt = float(req_form_data['כמות'])
    # todo: validate actual calculation. Eli Shalit may have been wrong----------------------------
    x_bars = {'qnt': ((rebar_len - 20) / hole) * qnt, 'length': rebar_width, 'diam': x_diam}
    y_bars = {'qnt': ((rebar_width - trim) / hole + 1) * qnt, 'length': rebar_len, 'diam': y_diam}
    # ---------------------------------------------------------------------------------------------
    if create_peripheral_order:
        peripheral_orders([x_bars, y_bars], order_id)
    total_weight = (x_bars['qnt'] * x_bars['length'] * weight[str(x_diam)] +
                    y_bars['qnt'] * y_bars['length'] * weight[str(y_diam)]) / 100
    return total_weight


def gen_client_list():
    return []


def peripheral_orders(add_orders, order_id):
    # todo: gen order id + write origin order_id and job_id in description
    order_id += "_R"
    for order in add_orders:
        order_weight = float(order['length']) * float(order['qnt']) * weight[str(order['diam'])] / 100
        info = {'costumer_id': 'צומת ברזל', 'date_created': ts(), 'type': 'regular'}
        mongo.upsert_collection_one('orders', {'order_id': order_id, 'info': {'$exists': True}},
                                    {'order_id': order_id, 'info': info})
        peripheral_order = {'order_id': order_id, 'job_id': gen_job_id(order_id), 'status': "New", 'כמות': order['qnt'],
                            'צורה': 1, 'אורך': order['length'], 'קוטר': order['diam'], 'משקל': order_weight}
        mongo.insert_collection_one('orders', peripheral_order)


def ts(mode=""):
    if not mode:
        return datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    elif mode == "file_name":
        return datetime.now().strftime('%d-%m-%Y_%H-%M-%S')


def gen_job_id(order_id):
    job_ids_df = mongo.read_collection_df('orders', query={'order_id': order_id, 'info': {'$exists': False}})
    if job_ids_df.empty:
        return "1"
    job_ids = job_ids_df['job_id'].tolist()
    return str(int(max(job_ids)) + 1)


def gen_patterns(order_type='regular'):
    if order_type == 'rebar':
        catalog = mongo.read_collection_one('data_lists', query={'name': 'rebar_catalog'})['data']
        diam = []
        cat_num = []
        rebar_type = []
        for item in catalog:
            if catalog[item]['קוטר'] not in diam:
                diam.append(catalog[item]['קוטר'])
            if item not in cat_num:
                cat_num.append(item)
            if catalog[item]['סוג'] not in rebar_type:
                rebar_type.append(catalog[item]['סוג'])
        diam.sort()
        rebar_type.sort()
        cat_num.sort()
        patterns = {'סוג': '|'.join(rebar_type), 'קוטר': '|'.join(diam), 'מקט': '|'.join(cat_num)}
        lists = {'סוג': rebar_type, 'קוטר': diam, 'מקט': catalog}
        return lists, patterns
    elif order_type == 'rebar_special':
        catalog = mongo.read_collection_one('data_lists', query={'name': 'rebar_catalog'})['data']
        diam = []
        cat_num = []
        rebar_type = []
        for item in catalog:
            if catalog[item]['קוטר'] not in diam:
                diam.append(catalog[item]['קוטר'])
            if item not in cat_num:
                cat_num.append(item)
            if catalog[item]['סוג'] not in rebar_type:
                rebar_type.append(catalog[item]['סוג'])
        diam.sort()
        rebar_type.sort()
        cat_num.sort()
        patterns = {'סוג': '|'.join(rebar_type), 'קוטר_x': '|'.join(diam), 'קוטר_y': '|'.join(diam), 'מקט': '|'.join(cat_num)}
        lists = {'סוג': rebar_type, 'קוטר_x': diam, 'קוטר_y': diam, 'מקט': catalog}
        return lists, patterns
    else:
        # TODO: complete
        return {}, {}
