from datetime import datetime, timedelta
import configs
import functions
import main
import users
import clients
import pandas as pd
import pages
from functions import ts
import math
from collections import OrderedDict


def orders():
    if not users.validate_user():
        return users.logout()
    if 'order_id' in main.session.keys():
        main.session['job_id'] = ""
        return main.redirect('/edit_order')
    query = {'info': {'$exists': True}, 'info.type': {'$ne': 'integration'}}
    if 'user_config' in main.session:
        if 'search' in main.session['user_config']:
            if main.session['user_config']['search']:
                query = main.session['user_config']['search']
    if 'filter' in main.session['user_config']:
        if main.session['user_config']['filter']:
            query['info.type'] = {'$regex': main.session['user_config']['filter']}
    defaults = {'from': functions.ts('html_date', 14), 'to': functions.ts('html_date')}
    if main.request.form:
        req_form = dict(main.request.form)
        for item in req_form:
            if 'date' in item:
                defaults['from'] = req_form['date_from']
                defaults['to'] = req_form['date_to']
                query['info.date_created'] = {'$gte': req_form['date_from'], '$lte': req_form['date_to'] + 'T23:59:59'}
            else:
                if req_form[item]:
                    query[item] = {'$regex': req_form[item]}
    main.session['user_config']['search'] = query
    main.session.modified = True
    # Read all orders data with Info, mean that it's not including order rows
    orders_data = main.mongo.read_collection_list('orders', query)
    orders_info = []
    for order in orders_data:
        row = order['info'].copy()
        row['order_id'] = order['order_id']
        row['status'] = 'order_status_' + row['status']
        orders_info.append(row)
    dictionary = pages.get_dictionary(main.session['username'])
    orders_info.sort(key=lambda k: int(k['order_id'].replace('R','')), reverse=True)
    print(dictionary)
    return main.render_template('orders.html', orders=orders_info, display_items=main.configs.data_to_display['orders'],
                                dictionary=dictionary, defaults=defaults)


def new_order(client="", order_type=""):
    user_group = users.validate_user()
    if not user_group:
        return users.logout()
    req_form = dict(main.request.form)
    if 'name' in req_form or client:
        if 'site' in req_form and 'sites_list' in main.session.keys():
            if 'order_type' in req_form and 'order_id' in main.session.keys():
                if req_form['order_type'] == main.session['order_id']:
                    doc = {'info.costumer_name': req_form['name'],
                           'info.costumer_id':
                               main.mongo.read_collection_one('costumers', {'name': req_form['name']})['id'],
                           'info.costumer_site': req_form['site']}
                    main.mongo.update_one('orders', {'order_id': main.session['order_id'], 'info': {'$exists': True}},
                                          doc, '$set')
                    return main.redirect('/orders')
            if req_form['site'] in main.session['sites_list']:
                main.session['sites_list'] = []
                user = main.session['username']
                client = req_form['name']
                client_id = main.mongo.read_collection_one('costumers', {'name': client})['id']
                site = req_form['site']
                order_type = req_form['order_type']
                order_id = new_order_id()
                order = {'order_id': order_id, 'info': {'created_by': user, 'date_created': ts(), 'date_delivery': ts(),
                                                        'type': order_type, 'costumer_name': client,
                                                        'costumer_id': client_id,
                                                        'costumer_site': site, 'status': 'NEW'}, 'rows': []}
                main.mongo.insert_collection_one('orders', order)
                main.session['order_id'] = order_id
                return main.redirect('/orders')
        elif 'name' in req_form:
            client = req_form['name']
    if len(list(main.request.values)) == 1 and not order_type:
        order_type = list(main.request.values)[0]
    elif 'order_type' in req_form:
        order_type = req_form['order_type']
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
    if 'R' in order_id:
        return
    req_form_data = dict(main.request.form)
    req_vals = dict(main.request.values)
    order = main.mongo.read_collection_one('orders', {'order_id': order_id, 'info': {'$exists': True}})
    if 'rows' not in order:
        order['rows'] = []
    job_id = str(len(order['rows']) + 1)
    if 'addbefore' in req_vals:
        job_id = req_vals['addbefore']
    elif 'job_id' in main.session:
        if main.session['job_id']:
            job_id = main.session['job_id']
    new_row = {'order_id': order_id, 'job_id': job_id, 'status': 'NEW', 'date_created': ts()}
    if 'x_length' in req_form_data.keys():
        new_row['x_length'] = []
        new_row['x_pitch'] = []
        new_row['y_length'] = []
        new_row['y_pitch'] = []
    for item in req_form_data:
        if req_form_data[item].isnumeric():
            req_form_data[item] = str(int(req_form_data[item]))
        if req_form_data[item] not in ['---', ''] and '_hid' not in item:
            if '_length' in item or '_pitch' in item:
                new_row[item[:item.find('h') + 1]].append(req_form_data[item])
            else:
                new_row[item] = req_form_data[item]
    # Order data handling
    if 'diam_x' in new_row:
        new_row['mkt'] = "2005020000"
        bars_x = 1
        bars_y = 1
        if 'trim_y_start' not in new_row:
            new_row['trim_y_start'] = 5
            new_row['y_length'][0] = int(new_row['y_length'][0]) - 5
        if 'trim_y_end' not in new_row:
            new_row['trim_y_end'] = 5
            new_row['y_length'][-1] = int(new_row['y_length'][-1]) - 5
        if 'trim_x_start' not in new_row:
            new_row['trim_x_start'] = 5
            new_row['x_length'][0] = int(new_row['x_length'][0]) - 5
        if 'trim_x_end' not in new_row:
            new_row['trim_x_end'] = 5
            new_row['x_length'][0] = int(new_row['x_length'][0]) - 5
        for i in range(len(new_row['x_length'])):
            if new_row['y_pitch'][i] != "0":
                new_row['trim_x_end'] = str(float(new_row['trim_x_end']) +
                                            int(new_row['x_length'][i]) % int(new_row['y_pitch'][i])).replace('.0', '')
                new_row['x_length'][i] = str(
                    int(new_row['x_length'][i]) - (int(new_row['x_length'][i]) % int(new_row['y_pitch'][i])))
                bars_y += math.floor(int(new_row['x_length'][i]) / int(new_row['y_pitch'][i]))
            else:
                bars_y += 1
        new_row['length'] = sum(list(map(int, new_row['y_length'])))
        new_row['width'] = sum(list(map(int, new_row['x_length'])))
        new_row['length'] += int(float(new_row['trim_y_start']) + float(new_row['trim_y_end']))
        new_row['width'] += int(float(new_row['trim_x_start']) + float(new_row['trim_x_end']))
        for i in range(len(new_row['y_length'])):
            if new_row['x_pitch'][i] != "0":
                new_row['trim_y_end'] = str(int(new_row['trim_y_end']) +
                                            int(new_row['y_length'][i]) % int(new_row['x_pitch'][i]))
                new_row['y_length'][i] = str(
                    int(new_row['y_length'][i]) - (int(new_row['y_length'][i]) % int(new_row['x_pitch'][i])))
                bars_x += math.floor(int(new_row['y_length'][i]) / int(new_row['x_pitch'][i]))
            else:
                bars_x += 1
        x_pitch = '(' + ')('.join(new_row['x_pitch']) + ')'
        y_pitch = '(' + ')('.join(new_row['y_pitch']) + ')'
        new_row['x_bars'] = int(bars_x)
        new_row['y_bars'] = int(bars_y)
        new_row['x_weight'] = calc_weight(new_row['diam_x'], new_row['width'], bars_x)
        new_row['y_weight'] = calc_weight(new_row['diam_y'], new_row['length'], bars_y)
        new_row['description'] = "H" + str(new_row['width']) + "X" + str(bars_x) + "X" + str(new_row['diam_x']) + \
                                 "WBX" + x_pitch + " V" + str(new_row['length']) + "X" + str(bars_y) + "X" + \
                                 str(new_row['diam_y']) + "WBX" + y_pitch
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
        new_row['weight'] = round(
            float(main.configs.rebar_catalog[new_row['mkt']]['unit_weight']) * float(new_row['quantity']), 1)
        if 'הזמנת_ייצור' in new_row:
            peripheral_orders([x_bars, y_bars], order_id, job_id)
    elif 'shape' in req_form_data:
        new_row['description'] = ""
        if float(new_row['diam']) < 7:
            new_row['bar_type'] = "חלק"
        new_row['shape_data'] = req_form_data['shape_hid'].split(',')
        new_row['shape_ang'] = configs.shapes[new_row['shape']]['ang']
        new_row['weight'] = calc_weight(new_row['diam'], new_row['length'], new_row['quantity'])
    else:
        # Order comment
        if 'comment_hid' in req_form_data:
            order['info']['comment'] = req_form_data['comment_hid']
        if 'date_delivery_hid' in req_form_data:
            order['info']['date_delivery'] = req_form_data['date_delivery_hid']
        main.mongo.update_one('orders', {'order_id': new_row['order_id']}, order, '$set')
        return
    # Takes to manual input for weight
    if 'weight' in req_form_data:
        if req_form_data['weight'].replace('.', '').isdigit():
            new_row['weight'] = float(req_form_data['weight'])
    for item in new_row:
        if isinstance(new_row[item], int):
            new_row[item] = str(new_row[item])
    order['info']['total_weight'] = new_row['weight']
    for i in range(len(order['rows'])):
        if i >= len(order['rows']):
            break
        if 'job_id' in main.session.keys():
            if order['rows'][i]['job_id'] == main.session['job_id']:
                order['rows'].pop(i)
                if i >= len(order['rows']):
                    break
        if 'addbefore' in req_vals:
            if int(order['rows'][i]['job_id']) >= int(req_vals['addbefore']):
                order['rows'][i]['job_id'] = str(int(order['rows'][i]['job_id'])+1)
        order['info']['total_weight'] += int(order['rows'][i]['weight'])
    order['rows'].append(new_row)
    order['info']['total_weight'] = round(order['info']['total_weight'])
    order['info']['rows'] = len(order['rows'])
    main.mongo.update_one('orders', {'order_id': new_row['order_id']}, order, '$set')


def edit_order():
    if not users.validate_user():
        return users.logout()
    req_vals = list(main.request.values)
    if main.request.form:
        new_order_row()
        return main.redirect('/orders')
    elif req_vals:
        main.session['order_id'] = req_vals[0]
    if 'order_id' not in main.session.keys():
        return main.redirect('/orders')
    order_data, page_data = edit_order_data()
    if not order_data:
        return close_order()
    defaults = {'bar_type': 'מצולע'}
    msg = ''
    # Copy last element fix
    if order_data['order_rows']:
        if 'element' in order_data['order_rows'][0]:
            defaults['element'] = order_data['order_rows'][0]['element']
    return main.render_template('/edit_order.html', order_data=order_data, patterns=page_data[1], lists=page_data[0],
                                dictionary=page_data[2], rebar_data={}, defaults=defaults, msg=msg, )


def get_order_data(order_id, job_id="", split="", reverse=True):
    query = {'order_id': order_id, 'info': {'$exists': True}}
    _order_data = main.mongo.read_collection_one('orders', query)
    if not _order_data:
        return {}, {}
    info = _order_data['info'].copy()
    order_data = []
    # total_weight = 0
    for row in _order_data['rows']:
        # total_weight += row['weight']
        row['weight'] = round(row['weight'])
        if job_id:
            if row['job_id'] == job_id:
                order_data.append(row)
                break
        elif split:
            if 'order_split' in row:
                if str(row['order_split']) == split:
                    order_data.append(row)
        else:
            order_data.append(row)
    if info['type'] == 'R':
        info['type'] = 'regular'
    info['order_id'] = order_id
    for row in order_data:
        row['status'] = 'order_status_' + row['status']
        if info['type'] == 'rebar':
            row['diam'] = row['diam_x']
            row['pitch'] = row['x_pitch']
    info['status'] = 'order_status_' + info['status']
    # print(round(total_weight), info)
    order_data.sort(key=lambda k: int(k['job_id']), reverse=reverse)
    return order_data.copy(), info


def new_order_id():
    new_id = "1"
    orders_df = main.mongo.read_collection_df('orders',
                                              query={'info': {'$exists': True}, 'info.type': {'$ne': 'integration'}})
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
    rows, info = get_order_data(order_id, job_id)
    del info['costumer_id']
    if not info:
        return {}, [], 0
    if info['type'] == 'R':
        keys_to_display = main.configs.data_to_display['new_row_regular']
    else:
        keys_to_display = main.configs.data_to_display['new_row_' + info['type']]
    if info['status'] != 'NEW':
        keys_to_display['status_updated_by'] = 2
    order_data = {'info': info, 'data_to_display': keys_to_display, 'order_rows': rows,
                  'dtd_order': list(keys_to_display.keys())}
    # if additional:
    #     order_data['include_data'] = additional
    if info['type'] == 'rebar_special':
        order_data['include'] = 'spec_rebar_editor.html'
        order_data['dtd_order'].extend(
            ['trim_x_start', 'trim_x_end', 'x_length', 'x_pitch', 'trim_y_start', 'trim_y_end', 'y_length', 'y_pitch'])
    lists, patterns = pages.gen_patterns(info['type'])
    dictionary = pages.get_dictionary(username)
    if 'total_weight' not in info:
        info['total_weight'] = 0
    return order_data, [lists, patterns, dictionary]


def edit_row():
    if not users.validate_user():
        return users.logout()
    req_vals = dict(main.request.values)
    if main.request.method == 'GET':
        main.session['order_id'] = req_vals['order_id']
        if 'job_id' in req_vals:
            main.session['job_id'] = req_vals['job_id']
        order_data, page_data = edit_order_data()
        if order_data:
            order_data['dtd_order'] = list(order_data['data_to_display'].keys())
            defaults = {'bar_type': 'מצולע'}
            if 'addbefore' in req_vals:
                defaults['addbefore'] = req_vals['addbefore']
            else:
                # print(order_data['order_rows'])
                defaults.update(order_data['order_rows'][0])
                spec_ = ['x_length', 'x_pitch', 'y_length', 'y_pitch']
                for item in spec_:
                    if item in defaults:
                        for i in range(len(defaults[item])):
                            if i > 0:
                                defaults[item+'_'+str(i)] = defaults[item][i]
                        defaults[item] = defaults[item][0]
            return main.render_template('/edit_row.html', order_data=order_data, patterns=page_data[1],
                                        lists=page_data[0], dictionary=page_data[2], defaults=defaults)
    new_order_row()
    return main.redirect('/orders')


def change_order_status():
    user_group = users.validate_user()
    if not user_group:
        return users.logout()
    elif user_group < 70:
        return '', 204
    req_vals = dict(main.request.values)
    if main.request.form:
        if '|' in main.request.form['order_id']:
            temp = main.request.form['order_id'].split('|')
            order_id = temp[0]
            job_id = temp[1]
        else:
            order_id = main.request.form['order_id']
            job_id = ''
        update_order_status(main.request.form['status'], order_id, job_id)
        return '', 204
    if req_vals:
        if 'order_id' in req_vals:
            order_id = req_vals['order_id']
        else:
            order_id = main.session['order_id']
        if 'job_id' in req_vals:
            order_id += '|' + req_vals['job_id']
    else:
        order_id = main.session['order_id']
    return main.render_template('change_order_status.html', order_id=order_id)


def cancel_order():
    user_group = users.validate_user()
    if not user_group:
        return users.logout()
    elif user_group < 70:
        return '', 204
    order_id = main.session['order_id']
    return main.render_template('cancel_order.html', order_id=order_id)


def update_order_status(new_status, order_id, job_id=""):
    order = main.mongo.read_collection_one('orders', {'order_id': order_id})
    while 'order_status_' in new_status:
        new_status = new_status.replace('order_status_', '')
    if not order:
        return
    flag = True
    if job_id != "":
        for i in range(len(order['rows'])):
            if order['rows'][i]['job_id'] == job_id:
                order['rows'][i]['status'] = new_status
                order['rows'][i]['status_updated_by'] = main.session['username']
                functions.log('job_status_change', {'order_id': order_id, 'job_id': job_id, 'status': new_status})
            if order['rows'][i]['job_id'] != 'Finished':
                flag = False
        if flag:
            update_order_status('Finished', order_id)
    else:
        order['info']['status'] = new_status
        for i in range(len(order['rows'])):
            if order['rows'][i]['status'] in ['NEW', 'Processed', 'Production']:
                order['rows'][i]['status'] = new_status
        if 'reason' in main.request.form:
            functions.log('cancel_order', main.request.form['reason'])
            order['info']['cancel_reason'] = main.request.form['reason']
        else:
            if 'cancel_reason' in order['info']:
                del order['info']['cancel_reason']
        functions.log('order_status_change', {'order_id': order_id, 'status': new_status})
        if new_status == 'Processed' and order['info']['costumer_name'] not in ['צומת ברזל', 'טסטים \ בדיקות']:
            msg = 'הודפסה הזמנה לקוח מס. {order_id}\nמתאריך: {date_created}\n לתאריך אספקה:{date_delivery}\nלקוח: {costumer_name}\nאתר: {costumer_site}\nמשקל: {total_weight} \nשורות: {rows} \n{username} ' \
                .format(order_id=order_id, date_created=order['info']['date_created'], date_delivery=order['info']['date_delivery'],
                        costumer_name=order['info']['costumer_name'], costumer_site=order['info']['costumer_site'],
                        total_weight=order['info']['total_weight'], rows=order['info']['rows'], username=main.session['username'])
            phone_book = ['0509595953', '0509393938', '0528008018']
            functions.send_sms(msg, phone_book)
    main.mongo.update_one('orders', {'order_id': order_id}, order, '$set')


def close_order():
    if not users.validate_user():
        return users.logout()
    if len(list(main.request.values)) > 0:
        req_vals = list(main.request.values)
        additional_func = req_vals[0]
        if additional_func == 'delete_row':
            order_id = main.session['order_id']
            order = main.mongo.read_collection_one('orders', {'order_id': order_id})
            indx_to_del = None
            order['info']['total_weight'] = 0
            for i in range(len(order['rows'])):
                # print(order['rows'][i]['job_id'] ,main.session['job_id'])
                order['info']['total_weight'] += order['rows'][i]['weight']
                if int(order['rows'][i]['job_id']) > int(main.session['job_id']) and 'R' not in order_id:
                    order['rows'][i]['job_id'] = str(int(order['rows'][i]['job_id']) - 1)
                elif int(order['rows'][i]['job_id']) == int(main.session['job_id']):
                    indx_to_del = i
            if indx_to_del:
                order['info']['total_weight'] -= order['rows'][indx_to_del]['weight']
            order['info']['total_weight'] = int(order['info']['total_weight'])
            order['rows'].pop(indx_to_del)
            order['info']['rows'] = len(order['rows'])
            main.mongo.update_one('orders', {'order_id': order_id}, order, '$set')
            return main.redirect('/orders')
        elif additional_func == 'scan':
            return main.redirect('/scan')
    users.clear()
    return main.redirect('/orders')


def calc_weight(diam, length, qnt):
    return round(float(length) * float(qnt) * main.configs.weights[str(diam)] / 100, 2)


def peripheral_orders(add_orders, order_id, orig_job_id):
    description = "הזמנת ייצור להכנת רשת. מספר הזמנת מקור: " + order_id + " שורה מספר: " + orig_job_id
    order_id += "R"
    order_data = main.mongo.read_collection_df('orders', query={'order_id': order_id})
    if order_data.empty:
        info = {'costumer_name': 'צומת ברזל', 'costumer_id': '0', 'created_by': main.session['username'],
                'date_created': ts(), 'type': 'R', 'status': 'NEW'}
        rows = []
    else:
        info = order_data['info'].to_dict()[0]
        rows = order_data['rows'].to_dict()[0]
    for order in range(len(add_orders)):
        job_id = orig_job_id + '_' + str(order + 1)
        to_pop = []
        for i in range(len(rows)):
            if rows[i]['job_id'] == job_id:
                to_pop.insert(0, i)
        for p in to_pop:
            rows.pop(p)
        order_weight = calc_weight(add_orders[order]['diam'], add_orders[order]['length'], add_orders[order]['qnt'])
        rows.append({'order_id': order_id, 'job_id': job_id, 'status': 'NEW', 'date_created': ts(),
                     'description': description, 'quantity': add_orders[order]['qnt'], 'shape': "1",
                     'length': add_orders[order]['length'], 'bar_type': 'מצולע',
                     'diam': add_orders[order]['diam'], 'weight': order_weight,
                     'shape_data': [add_orders[order]['length']], 'element': 'שורה: ' + orig_job_id})
    total_weight = 0
    for row in rows:
        total_weight += row['weight']
    info['total_weight'] = round(total_weight)
    update_order = {'order_id': order_id, 'rows': rows, 'info': info}
    main.mongo.update_one('orders', {'order_id': order_id},
                          update_order, '$set', upsert=True)


def copy_order():
    if main.request.form:
        req_form = dict(main.request.form)
        order_id = req_form['order_id']
        copies = int(req_form['copies'])
        for copy in list(range(copies)):
            new_id = new_order_id()
            order = main.mongo.read_collection_one('orders', {'order_id': order_id})
            # for doc in order_data:
            order['order_id'] = new_id
            order['info']['date_created'] = ts()
            order['info']['created_by'] = main.session['username']
            for row in order['rows']:
                row['order_id'] = new_id
            main.mongo.insert_collection_one('orders', order)
            update_order_status('NEW', new_id)
        return '', 204
    return main.render_template('/copy_order.html')


def split_order():
    order_id = main.session['order_id']
    order = main.mongo.read_collection_one('orders', {'order_id': order_id})
    if main.request.form:
        req_form = dict(main.request.form)
        splits = []
        for i in req_form:
            if req_form[i] not in splits:
                splits.append(i)
        if len(splits) < 2:
            if 'split' in order['info']:
                del order['info']['split']
        for i in range(len(order['rows'])):
            if len(splits) < 2:
                if 'order_split' in order['rows'][i]:
                    del order['rows'][i]['order_split']
            elif order['rows'][i]['job_id'] in req_form:
                if req_form[order['rows'][i]['job_id']]:
                    order['rows'][i]['order_split'] = req_form[order['rows'][i]['job_id']]
                else:
                    order['rows'][i]['order_split'] = 1
        main.mongo.update_one('orders', {'order_id': order_id}, order, '$set')
        return '', 204
    return main.render_template('/split_order.html', order=order['rows'])
