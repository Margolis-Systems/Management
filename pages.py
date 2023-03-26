import db_handler
import pandas as pd
from datetime import datetime

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


def edit_order_data(order_id, job_id=""):
    # Read all data of this order
    rows, info = get_order_data(order_id, job_id)
    # 0: Not required, 1: Required, 2: Autofill, 3: Drop menu, 4: Checkbox
    keys_to_display = data_to_display['new_row_'+info['type']]
    order_data = {'info': info, 'data_to_display': keys_to_display, 'order_rows': rows}
    lists, patterns = gen_patterns(info['type'])
    # todo: dictionaries to mongo
    dictionary = gen_dictionary('edit_' + info['type'])
    return order_data, [lists, patterns, dictionary]


def jobs_list():
    all_jobs = mongo.read_collection_df('orders', query={'info': {'$exists': False}})
    if all_jobs.empty:
        return {}
    all_jobs = all_jobs.sort_values(by=['order_id', 'job_id'], ascending=[False, True])
    columns = ['order_id', 'job_id', 'status', 'date_created', 'תיאור']
    return all_jobs[columns].to_dict('records')


'''_____________________FUNCTIONS___________________________'''


def gen_dictionary(page_name):
    dictionary = {'costumer_id': "שם לקוח", 'costumer_site': "אתר לקוח", 'date_created': "נוצר בתאריך", 'order_id': "מספר הזמנה", 'type': "סוג הזמנה"
                  , 'regular': "רגילה", 'rebar': "רשת", 'rebar_special': "רשת מיוחדת", 'job_id': "מספר שורה", 'status': "סטטוס"}
    if page_name == 'edit_rebar':
        for obj in rebar_catalog:
            dictionary[obj] = '⌀' + rebar_catalog[obj]['קוטר'] + "  " + rebar_catalog[obj]['פסיעה']
    # todo: complete
    # elif order_type == 'rebar_special':
    #
    # else:

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
            row_data['שורה'] = order_data[key]['job_id']
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
    order = {'order_id': order_id, 'info': {'date_created': ts(), 'costumer_id': client, 'costumer_site': site,
                                            'type': order_type}}
    mongo.insert_collection_one('orders', order)
    return order_id


def new_order_row(req_form_data, order_id, job_id=""):
    # order_info = mongo.read_collection_one('orders', {'order_id': order_id, 'info': {'$exists': True}})
    if not job_id:
        # dc = order_info['info']['date_created']
        job_id = gen_job_id(order_id)
    else:
        mongo.delete_many('orders', {'order_id': order_id, 'job_id': job_id})
    #     dc = ts()
    new_row = {'order_id': order_id, 'job_id': job_id, 'status': 'New', 'date_created': ts()}
    special_list = ['shape_data', 'משקל_יח']
    for item in req_form_data:
        if item not in special_list:
            new_row[item] = req_form_data[item]

    if 'מקט' in req_form_data:
        cat_item = rebar_catalog[req_form_data['מקט']]
        for item in cat_item:
            if item not in special_list:
                new_row[item] = cat_item[item]
        new_row['משקל'] = round(float(rebar_catalog[req_form_data['מקט']]['משקל_יח']) * float(new_row['כמות']), 1)
        if 'הזמנת_ייצור' in req_form_data:
            step = int(new_row['פסיעה'].split('X')[0])
            x_bars = {'length': new_row['רוחב'], 'qnt': int(new_row['כמות']) * (int(new_row['אורך']) / step),
                      'diam': new_row['קוטר']}
            y_bars = {'length': new_row['אורך'], 'qnt': int(new_row['כמות']) * (int(new_row['רוחב']) - 10) / (step + 1),
                      'diam': new_row['קוטר']}
            peripheral_orders([x_bars, y_bars], order_id)

    if 'shape_data' in req_form_data:
        print()
        # todo: complete
    elif 'מקט' not in req_form_data:
        new_row['מקט'] = "2005020000"
        new_row['תיאור'] = "רשת מיוחדת קוטר" + new_row['קוטר_x'] + "|" + new_row['קוטר_x'] + "\n" + new_row['פסיעה_x'] + "X" + new_row['פסיעה_y'] \
                           + "פסיעה:" + "\n" + new_row['אורך'] + "X" + new_row['רוחב']
        new_row['משקל'] = round(calc_bars_weight(new_row, order_id), 1)
    # mongo.upsert_collection_one('orders', {'_id': doc_id}, new_row)
    mongo.insert_collection_one('orders', new_row)


def calc_bars_weight(req_form_data, order_id):
    # todo: update TBD --according to new special rebar
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
    qnt = float(req_form_data['כמות'])
    x_bars = {'qnt': rebar_len / float(req_form_data['פסיעה_x']) * qnt, 'length': rebar_width, 'diam': x_diam}
    y_bars = {'qnt': ((rebar_width - trim) / float(req_form_data['פסיעה_y']) + 1) * qnt, 'length': rebar_len, 'diam': y_diam}
    # ---------------------------------------------------------------------------------------------
    if create_peripheral_order:
        peripheral_orders([x_bars, y_bars], order_id)
    total_weight = (x_bars['qnt'] * x_bars['length'] * weights[str(x_diam)] +
                    y_bars['qnt'] * y_bars['length'] * weights[str(y_diam)]) / 100
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


def peripheral_orders(add_orders, order_id):
    description = "הזמנת ייצור להכנת רשת. מספר הזמנת מקור: " + order_id
    order_id += "_R"
    mongo.delete_many('orders', {'order_id': order_id, 'status': 'New'})
    for order in add_orders:
        order_weight = float(order['length']) * float(order['qnt']) * weights[str(order['diam'])] / 100
        info = {'costumer_id': 'צומת ברזל', 'date_created': ts(), 'type': 'regular'}
        mongo.upsert_collection_one('orders', {'order_id': order_id, 'info': {'$exists': True}},
                                    {'order_id': order_id, 'info': info})
        peripheral_order = {'order_id': order_id, 'job_id': gen_job_id(order_id), 'status': "New", 'date_created': ts(),
                            'תיאור': description, 'כמות': order['qnt'], 'צורה': 1, 'אורך': order['length'],
                            'קוטר': order['diam'], 'משקל': order_weight}
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
        catalog = mongo.read_collection_one('data_lists', query={'name': 'rebar_catalog'})['data']
        diam = []
        cat_num = []
        rebar_type = []
        for item in catalog:
            if catalog[item]['קוטר'] not in diam:
                diam.append(catalog[item]['קוטר'])
            if item not in cat_num:
                cat_num.append(item)
            if catalog[item]['פסיעה'] not in rebar_type:
                rebar_type.append(catalog[item]['פסיעה'])
        diam.sort()
        rebar_type.sort()
        cat_num.sort()
        patterns = {'פסיעה': '|'.join(rebar_type), 'קוטר': '|'.join(diam), 'מקט': '|'.join(cat_num)}
        lists = {'פסיעה': rebar_type, 'קוטר': diam, 'מקט': catalog}
    elif order_type == 'rebar_special':
        catalog = mongo.read_collection_one('data_lists', query={'name': 'rebar_catalog'})['data']
        # todo: --------------
        diam = ['5.5', '6.5', '7.5', '8', '10', '12', '14', '16', '18']
        # todo: --------------
        cat_num = []
        rebar_type = []
        for item in catalog:
            # if catalog[item]['קוטר'] not in diam:
            #     diam.append(catalog[item]['קוטר'])
            if item not in cat_num:
                cat_num.append(item)
            if catalog[item]['פסיעה'].split('X')[0] not in rebar_type:
                rebar_type.append(catalog[item]['פסיעה'].split('X')[0])
        # diam.sort()
        rebar_type.sort()
        cat_num.sort()
        patterns = {'פסיעה_x': '|'.join(rebar_type), 'פסיעה_y': '|'.join(rebar_type), 'קוטר_x': '|'.join(diam), 'קוטר_y': '|'.join(diam), 'מקט': '|'.join(cat_num)}
        lists = {'פסיעה_x': rebar_type, 'פסיעה_y': rebar_type, 'קוטר_x': diam, 'קוטר_y': diam, 'מקט': catalog}
    else:
        # TODO: complete
        lists = {}
        patterns = {}
    return lists, patterns
