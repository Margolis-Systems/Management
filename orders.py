import configs
import main
import users
import clients
import pandas as pd
import pages
from functions import ts
import math


def orders():
    if not users.validate_user():
        return users.logout()
    if 'order_id' in main.session.keys():
        main.session['job_id'] = ""
        return main.redirect('/edit_order')
    query = {'info': {'$exists': True}}
    if main.request.form:
        req_form = dict(main.request.form)
        for item in req_form:
            if req_form[item]:
                query[item] = {'$regex': req_form[item]}
    # Read all orders data with Info, mean that it's not including order rows
    orders_df = main.mongo.read_collection_df('orders', query=query)

    if orders_df.empty:
        if not main.request.form:
            return main.render_template('orders.html', orders={}, display_items=[], dictionary={})
        return main.redirect('/orders')
    # normalize json to df
    info_df = pd.json_normalize(orders_df['info'])
    info_df['date_created'] = pd.to_datetime(info_df['date_created'], format='%d-%m-%Y %H:%M:%S')
    # add order id from main df
    new_df = pd.concat([orders_df['order_id'], info_df], axis=1)
    for item in main.configs.data_to_display['orders']:
        if item not in new_df.columns:
            new_df[item] = ""
    orders_info = new_df[
        main.configs.data_to_display['orders']].copy()  # .sort_values(by='date_created', ascending=False)
    sorter = {'NEW': 0, 'Processed': 1, 'Production': 2}
    orders_info['sorter'] = orders_info['status'].map(sorter)
    orders_info['status'] = 'order_status_' + orders_info['status'].astype(str)
    orders_info.sort_values(by=['sorter', 'date_created'], ascending=[True, False], inplace=True)
    dictionary = pages.get_dictionary(main.session['username'])
    return main.render_template('orders.html', orders=orders_info.to_dict('index'),
                                display_items=main.configs.data_to_display['orders'],
                                dictionary=dictionary)


def new_order(client="", order_type=""):
    user_group = users.validate_user()
    if not user_group:
        return users.logout()
    if 'name' in main.request.form.keys() or client:
        if 'site' in main.request.form.keys() and 'sites_list' in main.session.keys():
            if main.request.form['site'] in main.session['sites_list']:
                main.session['sites_list'] = []
                user = main.session['username']
                client = main.request.form['name']
                client_id = main.mongo.read_collection_one('costumers', {'name': client})['id']
                site = main.request.form['site']
                order_type = main.request.form['order_type']
                order_id = new_order_id()
                order = {'order_id': order_id, 'info': {'created_by': user, 'date_created': ts(), 'type': order_type,
                                                        'costumer_name': client, 'costumer_id': client_id,
                                                        'costumer_site': site, 'status': 'NEW'}}
                main.mongo.insert_collection_one('orders', order)
                main.session['order_id'] = order_id
                return main.redirect('/orders')
        elif 'name' in main.request.form.keys():
            client = main.request.form['name']
    if len(list(main.request.values)) == 1 and not order_type:
        order_type = list(main.request.values)[0]
    elif 'order_type' in main.request.form.keys():
        order_type = main.request.form['order_type']
    client_list, sites_list = clients.gen_client_list(client)
    permission = False
    if user_group > 50:
        permission = True
    if sites_list:
        main.session['sites_list'] = sites_list
    return main.render_template('/pick_client.html', clients=client_list, site=sites_list, order_type=order_type,
                                permission=permission)


def new_order_row():
    order_id = main.session['order_id']
    req_form_data = main.request.form
    temp_order_data = main.mongo.read_collection_one('orders', {'order_id': order_id, 'job_id': "0"})
    info = main.mongo.read_collection_one('orders', {'order_id': order_id, 'info': {'$exists': True}})
    if info['info']['status'] != "NEW":
        return
    # Order comment
    if 'comment_hid' in req_form_data:
        main.mongo.update_one('orders', {'order_id': order_id, 'info': {'$exists': True}},
                                        {'info.comment': req_form_data['comment_hid']}, '$set')
    # Order peripheral data handling
    if 'shape_data' in req_form_data.keys():
        new_row = {'order_id': order_id, 'job_id': "0"}
        for item in req_form_data:
            if item.isdigit() or item == 'shape_data' or 'ang' in item:
                new_row[item] = req_form_data[item]
        main.mongo.upsert_collection_one('orders', {'order_id': order_id, 'job_id': "0"}, new_row)
        return
    else:
        job_id = gen_job_id(order_id)
        if 'job_id' in main.session.keys():
            if main.session['job_id'] != "":
                job_id = main.session['job_id']
        new_row = {'order_id': order_id, 'job_id': job_id, 'status': 'NEW', 'date_created': ts()}
        if 'x_length' in req_form_data.keys():
            new_row['x_length'] = []
            new_row['x_pitch'] = []
            new_row['y_length'] = []
            new_row['y_pitch'] = []
        for item in req_form_data:
            if req_form_data[item] not in ['---', ''] and '_hid' not in item:
                if '_length' in item or '_pitch' in item:
                    new_row[item[:item.find('h') + 1]].append(req_form_data[item])
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
                new_row['x_length'][i] = str(
                    int(new_row['x_length'][i]) - (int(new_row['x_length'][i]) % int(new_row['x_pitch'][i])))
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
                new_row['y_length'][i] = str(
                    int(new_row['y_length'][i]) - (int(new_row['y_length'][i]) % int(new_row['y_pitch'][i])))
                bars_x += math.floor(int(new_row['y_length'][i]) / int(new_row['y_pitch'][i]))
            else:
                bars_x += 1
        x_pitch = '(' + ')('.join(new_row['x_pitch']) + ')'
        y_pitch = '(' + ')('.join(new_row['y_pitch']) + ')'
        # x_length = '('+')('.join(new_row['x_length'])+')'
        # y_length = '('+')('.join(new_row['y_length'])+')'
        new_row['x_bars'] = int(bars_x)
        new_row['y_bars'] = int(bars_y)
        new_row['x_weight'] = calc_weight(new_row['diam_x'], new_row['width'], bars_x)
        new_row['y_weight'] = calc_weight(new_row['diam_y'], new_row['length'], bars_y)
        new_row['description'] = "V" + str(new_row['width']) + "X" + str(bars_x) + "X" + str(
            new_row['diam_x']) + "WBX" + x_pitch + \
                                 " H" + str(new_row['length']) + "X" + str(bars_y) + "X" + str(
            new_row['diam_y']) + "WBX" + y_pitch
        new_row['unit_weight'] = round(new_row['x_weight'] + new_row['y_weight'], 2)
        new_row['weight'] = round(new_row['unit_weight'] * int(new_row['quantity']), 2)
        if 'הזמנת_ייצור' in new_row:
            x_bars = {'length': new_row['width'], 'qnt': bars_x * int(new_row['quantity']), 'diam': new_row['diam_x']}
            y_bars = {'length': new_row['length'], 'qnt': bars_y * int(new_row['quantity']), 'diam': new_row['diam_y']}
            peripheral_orders([x_bars, y_bars], order_id, job_id)
    elif 'mkt' in new_row:
        cat_item = main.configs.rebar_catalog[new_row['mkt']]
        for item in cat_item:
            if item not in ['pack_quantity']:
                new_row[item] = cat_item[item]
        pitch = int(new_row['x_pitch'])
        x_bars = {'length': new_row['width'], 'qnt': int(int(new_row['quantity']) * (int(new_row['length']) / pitch)),
                  'diam': new_row['diam_x']}
        y_bars = {'length': new_row['length'],
                  'qnt': int(((int(new_row['width']) - 10) / pitch + 1) * int(new_row['quantity'])),
                  'diam': new_row['diam_y']}
        new_row['description'] = "V250X" + str(int(int(new_row['length']) / pitch)) + "X" + new_row[
            'diam_x'] + "WBX" + str(pitch) + \
                                 " H600X" + str(int((int(new_row['width']) - 10) / pitch + 1)) + "X" + new_row[
                                     'diam_y'] + "WBX" + str(pitch)
        new_row['weight'] = round(
            float(main.configs.rebar_catalog[new_row['mkt']]['unit_weight']) * float(new_row['quantity']), 1)
        if 'הזמנת_ייצור' in new_row:
            peripheral_orders([x_bars, y_bars], order_id, job_id)
    elif 'shape' in req_form_data:
        new_row['description'] = ""
        if int(new_row['diam']) < 7:
            new_row['bar_type'] = "חלק"
        if temp_order_data:
            if temp_order_data['shape_data'] == new_row['shape']:
                new_row['shape_data'] = []
                new_row['shape_ang'] = configs.shapes[new_row['shape']]['ang']
                for item in temp_order_data:
                    if item.isdigit():
                        new_row['shape_data'].append(temp_order_data[item])
                    elif 'ang_' in item:
                        new_row['shape_ang'][int(item.replace('ang_', '')) - 1] = temp_order_data[item]
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
    main.mongo.upsert_collection_one('orders', {'order_id': new_row['order_id'], 'job_id': new_row['job_id']}, new_row)
    order_rows_count = main.mongo.count_docs('orders', query={'order_id': new_row['order_id'], 'info': {'$exists': False},
                                                              'job_id': {'$ne': '0'}})
    main.mongo.update_one('orders', {'order_id': new_row['order_id']}, {'info.rows': str(order_rows_count)}, '$set')


def edit_order():
    if not users.validate_user():
        return users.logout()
    if len(list(main.request.values)) == 1:
        # if 'order_id' in main.request.values.keys():
        #     main.session['order_id'] = main.request.values['order_id']
        # else:
        #     main.session['order_id'] = list(main.request.values)[0]
        main.session['order_id'] = list(main.request.values)[0]
    elif len(main.request.form.keys()) > 1:
        new_order_row()
        return main.redirect('/orders')
    if 'order_id' not in main.session.keys():
        return main.redirect('/orders')
    order_data, page_data = edit_order_data()
    if not order_data:
        return close_order()
    # todo: gen_defaults
    defaults = {'bar_type': 'מצולע', 'comment': order_data}
    return main.render_template('/edit_order.html', order_data=order_data, patterns=page_data[1], lists=page_data[0],
                                dictionary=page_data[2], rebar_data={}, defaults=defaults)


def get_order_data(order_id, job_id="", reverse=True):
    order = main.mongo.read_collection_df('orders', query={'order_id': order_id, 'job_id': {'$ne': "0"}})
    additional = main.mongo.read_collection_one('orders', {'order_id': order_id, 'job_id': "0"})
    if order.empty:
        return False, False, False
    info = order[order['info'].notnull()]['info'][0]
    order_data_df = order[order['info'].isnull()].drop(['info'], axis=1).fillna("")
    if not order_data_df.empty:
        # order_data_df['weight'] = order_data_df['weight'].astype(int)
        order_data_df['weight'] = order_data_df['weight'].round(1)
        order_data_df['status'] = 'order_status_' + order_data_df['status'].astype(str)
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
    orders_df = main.mongo.read_collection_df('orders', query={'info': {'$exists': True}})
    if orders_df.empty:
        return new_id
    order_ids_list = orders_df['order_id'].unique().tolist()
    for _id in order_ids_list:
        if _id.isdigit():
            if int(_id) >= int(new_id):
                new_id = str(int(_id) + 1)
    return new_id


def edit_order_data():
    order_id, username = main.session['order_id'], main.session['username']
    job_id = ""
    if 'job_id' in main.session.keys():
        job_id = main.session['job_id']
    # Read all data of this order
    rows, info, additional = get_order_data(order_id, job_id)
    # if info['created_by'] != main.session['username']:

    if not info:
        return {}, []

    # 0: Not required, 1: Required, 2: Autofill, 3: Drop menu, 4: Checkbox
    keys_to_display = main.configs.data_to_display['new_row_' + info['type']]
    order_data = {'info': info, 'data_to_display': keys_to_display, 'order_rows': rows}
    if additional:
        order_data['include_data'] = additional
    if info['type'] == 'rebar_special':
        order_data['include'] = 'spec_rebar_editor.html'
    lists, patterns = pages.gen_patterns(info['type'])
    dictionary = pages.get_dictionary(username)
    return order_data, [lists, patterns, dictionary]


def edit_row():
    if not users.validate_user():
        return users.logout()
    if main.request.method == 'GET':
        main.session['order_id'], main.session['job_id'] = list(main.request.values)[0].split('job')
        order_data, page_data = edit_order_data()
        if order_data:
            defaults = {}
            for item in order_data['order_rows'][0]:
                if isinstance(order_data['order_rows'][0][item], list):
                    for li in range(len(order_data['order_rows'][0][item])):
                        if li > 0:
                            defaults[item + "_" + str(li - 1)] = order_data['order_rows'][0][item][li]
                        else:
                            defaults[item] = order_data['order_rows'][0][item][li]
                else:
                    defaults[item] = order_data['order_rows'][0][item]
            return main.render_template('/edit_row.html', order_data=order_data, patterns=page_data[1],
                                        lists=page_data[0], dictionary=page_data[2], defaults=defaults)
    new_order_row()
    return main.redirect('/orders')


def change_order_status():
    user_group = users.validate_user()
    if not user_group:
        return users.logout()
    elif user_group < 80:
        return '', 204
    if main.request.form:
        update_order_status(main.request.form['status'], main.request.form['order_id'])
        return '', 204
    return main.render_template('change_order_status.html', order_id=main.session['order_id'])


def update_order_status(new_status, order_id, job_id=""):
    if job_id != "":
        main.mongo.update_one('orders', {'order_id': order_id, 'job_id': job_id}, {'status': new_status}, '$set')
        rows, info, additional = get_order_data(order_id)
        for row in rows:
            if row['status'] != "Finished":
                return
        update_order_status('Finished', order_id)
    else:
        main.mongo.update_one('orders', {'order_id': order_id, 'info': {'$exists': True}},
                                        {'info.status': new_status}, '$set')
        main.mongo.update_many('orders', {'order_id': order_id, 'info': {'$exists': False}},
                                        {'status': new_status}, '$set')


def close_order():
    if not users.validate_user():
        return users.logout()
    if len(list(main.request.values)) > 0:
        req_vals = list(main.request.values)
        additional_func = req_vals[0]
        if additional_func == 'delete':
            main.mongo.delete_many('orders', {'order_id': main.session['order_id']})
        elif additional_func == 'scan':
            return main.redirect('/scan')
    users.clear()
    return main.redirect('/orders')


def calc_weight(diam, length, qnt):
    return round(float(length) * float(qnt) * main.configs.weights[str(diam)] / 100, 2)


def peripheral_orders(add_orders, order_id, job_id):
    description = "הזמנת ייצור להכנת רשת. מספר הזמנת מקור: " + order_id + " שורה מספר: " + job_id
    order_id += "R"
    for order in range(len(add_orders)):
        job_id += '_' + str(order)
        order_weight = calc_weight(add_orders[order]['diam'], add_orders[order]['length'], add_orders[order]['qnt'])
        info = {'costumer_name': 'צומת ברזל', 'created_by': main.session['username'], 'date_created': ts(),
                'type': 'regular', 'status': 'NEW'}
        main.mongo.upsert_collection_one('orders', {'order_id': order_id, 'info': {'$exists': True}},
                                         {'order_id': order_id, 'info': info})
        peripheral_order = {'order_id': order_id, 'job_id': job_id, 'status': 'NEW', 'date_created': ts(),
                            'description': description, 'quantity': add_orders[order]['qnt'], 'shape': "1",
                            'length': add_orders[order]['length'],
                            'diam': add_orders[order]['diam'], 'weight': order_weight,
                            'shape_data': [add_orders[order]['length']]}
        main.mongo.upsert_collection_one('orders', {'order_id': order_id, 'job_id': job_id}, peripheral_order)


def gen_job_id(order_id):
    job_ids_df = main.mongo.read_collection_df('orders', query={'order_id': order_id, 'info': {'$exists': False}})
    if job_ids_df.empty:
        return "1"
    job_ids = job_ids_df['job_id'].astype(int).tolist()
    return str(int(max(job_ids)) + 1)
