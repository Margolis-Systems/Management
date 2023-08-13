import datetime

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
                query['info.date_created'] = {'$gte': req_form['date_from'], '$lte': req_form['date_to']+'T23:59:59'}
            else:
                if req_form[item]:
                    query[item] = {'$regex': req_form[item]}
    # Read all orders data with Info, mean that it's not including order rows
    orders_df = main.mongo.read_collection_df('orders', query=query)
    if orders_df.empty:
        if not main.request.form:
            return main.render_template('orders.html', orders={}, display_items=[], dictionary={}, defaults={})
        return main.redirect('/orders')
    main.session['user_config']['search'] = query
    main.session.modified = True
    # normalize json to df
    info_df = pd.json_normalize(orders_df['info'])
    info_df['date_created'] = pd.to_datetime(info_df['date_created'], format='%Y-%m-%d %H:%M:%S')
    # add order id from main df
    new_df = pd.concat([orders_df['order_id'], info_df], axis=1).fillna(0)
    for item in main.configs.data_to_display['orders']:
        if item not in new_df.columns:
            new_df[item] = ""
    orders_info = new_df[main.configs.data_to_display['orders']].copy()
    orders_info['status'] = 'order_status_' + orders_info['status'].astype(str)
    if orders_info['total_weight'].any():
        orders_info['total_weight'] = orders_info['total_weight'].astype(int)
    if orders_info['split'].any():
        orders_info['split'] = orders_info['split'].astype(int)
    orders_info.sort_values(by=['date_created'], ascending=[False], inplace=True)
    dictionary = pages.get_dictionary(main.session['username'])
    return main.render_template('orders.html', orders=orders_info.to_dict('index'),
                                display_items=main.configs.data_to_display['orders'],
                                dictionary=dictionary, defaults=defaults)


def new_order(client="", order_type=""):
    user_group = users.validate_user()
    if not user_group:
        return users.logout()
    if 'name' in main.request.form.keys() or client:
        if 'site' in main.request.form.keys() and 'sites_list' in main.session.keys():
            if 'order_type' in main.request.form and 'order_id' in main.session.keys():
                if main.request.form['order_type'] == main.session['order_id']:
                    doc = {'info.costumer_name': main.request.form['name'],
                           'info.costumer_id': main.mongo.read_collection_one('costumers', {'name': main.request.form['name']})['id'],
                           'info.costumer_site': main.request.form['site']}
                    main.mongo.update_one('orders', {'order_id': main.session['order_id'], 'info': {'$exists': True}}, doc, '$set')
                    return main.redirect('/orders')
            if main.request.form['site'] in main.session['sites_list']:
                main.session['sites_list'] = []
                user = main.session['username']
                client = main.request.form['name']
                client_id = main.mongo.read_collection_one('costumers', {'name': client})['id']
                site = main.request.form['site']
                order_type = main.request.form['order_type']
                order_id = new_order_id()
                order = {'order_id': order_id, 'info': {'created_by': user, 'date_created': ts(), 'date_delivery': ts(),
                                                        'type': order_type, 'costumer_name': client, 'costumer_id': client_id,
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
    # info = main.mongo.read_collection_one('orders', {'order_id': order_id, 'info': {'$exists': True}})
    # if info['info']['status'] != "NEW":
    #     return
    # Order peripheral data handling
    if 'shape_data' in req_form_data.keys():
        new_row = {'order_id': order_id, 'job_id': "0"}
        for item in req_form_data:
            if item.isdigit() or item == 'shape_data' or 'ang' in item:
                new_row[item] = " ".join(req_form_data[item].split())
        main.mongo.upsert_collection_one('orders', {'order_id': order_id, 'job_id': "0"}, new_row)
        return

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
    # Order comment
    if 'comment_hid' in req_form_data:
        main.mongo.update_one('orders', {'order_id': order_id, 'info': {'$exists': True}},
                              {'info.comment': req_form_data['comment_hid']}, '$set')
    if 'date_delivery_hid' in req_form_data:
        date_delivery = req_form_data['date_delivery_hid']
        main.mongo.update_one('orders', {'order_id': order_id, 'info': {'$exists': True}},
                              {'info.date_delivery': date_delivery}, '$set')
    # Order data handling
    if 'diam_x' in new_row:  # or 'diam_y'
        new_row['mkt'] = "2005020000"
        bars_x = 1
        bars_y = 1
        for i in range(len(new_row['x_length'])):
            if new_row['x_pitch'][i] != "0":
                new_row['trim_x_end'] = str(float(new_row['trim_x_end']) +
                                            int(new_row['x_length'][i]) % int(new_row['x_pitch'][i])).replace('.0','')
                new_row['x_length'][i] = str(
                    int(new_row['x_length'][i]) - (int(new_row['x_length'][i]) % int(new_row['x_pitch'][i])))
                bars_y += math.floor(int(new_row['x_length'][i]) / int(new_row['x_pitch'][i]))
            else:
                bars_y += 1
        new_row['length'] = sum(list(map(int, new_row['y_length'])))
        new_row['width'] = sum(list(map(int, new_row['x_length'])))
        new_row['length'] += int(float(new_row['trim_y_start']) + float(new_row['trim_y_end']))
        new_row['width'] += int(float(new_row['trim_x_start']) + float(new_row['trim_x_end']))
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
        # new_row['description'] = "V250X" + str(int(int(new_row['length']) / pitch)) + "X" + new_row[
        #     'diam_x'] + "WBX" + str(pitch) + \
        #                          " H600X" + str(int((int(new_row['width']) - 10) / pitch + 1)) + "X" + new_row[
        #                              'diam_y'] + "WBX" + str(pitch)
        new_row['weight'] = round(
            float(main.configs.rebar_catalog[new_row['mkt']]['unit_weight']) * float(new_row['quantity']), 1)
        if 'הזמנת_ייצור' in new_row:
            peripheral_orders([x_bars, y_bars], order_id, job_id)
    elif 'shape' in req_form_data:
        temp_order_data = main.mongo.read_collection_one('orders', {'order_id': order_id, 'job_id': "0"})
        new_row['description'] = ""
        if float(new_row['diam']) < 7:
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
            else:
                main.mongo.update_one('orders', {'order_id': new_row['order_id'], 'job_id': new_row['job_id']},
                                        new_row, '$set')
                return
            if new_row['shape'] == '332':
                new_row['weight'] = calc_weight(new_row['diam'], new_row['length'], 1)
            else:
                new_row['weight'] = calc_weight(new_row['diam'], new_row['length'], new_row['quantity'])
            # else:
            #     # Shape data not compatible with form data
            #     print("Shape data not compatible with form data\n", main.session)
            #     return
        else:
            # No shape data
            print("No shape data\n", main.session)
            return
    else:
        return
    # Takes to manual input for weight
    if 'weight' in req_form_data:
        if req_form_data['weight'].replace('.', '').isdigit():
            new_row['weight'] = float(req_form_data['weight'])
    for item in new_row:
        if isinstance(new_row[item], int):
            new_row[item] = str(new_row[item])
    main.mongo.upsert_collection_one('orders', {'order_id': new_row['order_id'], 'job_id': new_row['job_id']}, new_row) #, upsert=True
    update_orders_total_weight()
    req_vals = dict(main.request.values)
    if 'addbefore' in req_vals:
        if req_vals['addbefore']:
            reorder_job_id(req_vals['addbefore'])


def edit_order():
    if not users.validate_user():
        return users.logout()
    if len(list(main.request.values)) == 1:
        main.session['order_id'] = list(main.request.values)[0]
    elif len(main.request.form.keys()) > 1:
        new_order_row()
        return main.redirect('/orders')
    if 'order_id' not in main.session.keys():
        return main.redirect('/orders')
    order_data, page_data, total_weight = edit_order_data()
    if not order_data:
        return close_order()
    defaults = {'bar_type': 'מצולע'}
    msg = ''
    # Copy last element fix
    if order_data['order_rows']:
        if 'element' in order_data['order_rows'][0]:
            defaults['element'] = order_data['order_rows'][0]['element']
    return main.render_template('/edit_order.html', order_data=order_data, patterns=page_data[1], lists=page_data[0],
                                dictionary=page_data[2], rebar_data={}, defaults=defaults, total_weight=total_weight,
                                msg=msg,)


def get_order_data(order_id, job_id="", split="", reverse=True):
    query = {'order_id': order_id, 'job_id': {'$ne': "0"}, 'info': {'$exists': False}, 'type': {'$ne': 'integration'}}
    if job_id:
        query['job_id'] = job_id
    if split:
        query['order_split'] = int(split)
    order_data = list(main.mongo.read_collection_list('orders', query))
    # if not order_data:
    #     return None, None, None
    additional = main.mongo.read_collection_one('orders', {'order_id': order_id, 'job_id': "0"})
    info = main.mongo.read_collection_one('orders', {'order_id': order_id, 'info': {'$exists': True}})['info']
    if info['type'] == 'R':
        info['type'] = 'regular'
    info['order_id'] = order_id
    for row in order_data:
        row['status'] = 'order_status_' + row['status']
        if info['type'] == 'rebar':
            row['diam'] = row['diam_x']
            row['pitch'] = row['x_pitch']
    info['order_id'] = order_id
    info['status'] = 'order_status_' + info['status']
    order_data.sort(key=lambda k: int(k['job_id']), reverse=reverse)
    return order_data.copy(), info, additional


def new_order_id():
    new_id = "1"
    orders_df = main.mongo.read_collection_df('orders', query={'info': {'$exists': True}, 'info.type': {'$ne': 'integration'}})
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
    del info['costumer_id']
    if not info:
        return {}, [], 0
    if info['type'] == 'R':
        keys_to_display = main.configs.data_to_display['new_row_regular']
    else:
        keys_to_display = main.configs.data_to_display['new_row_' + info['type']]
    order_data = {'info': info, 'data_to_display': keys_to_display, 'order_rows': rows,
                  'dtd_order': list(keys_to_display.keys())}
    if additional:
        order_data['include_data'] = additional
    if info['type'] == 'rebar_special':
        order_data['include'] = 'spec_rebar_editor.html'
        order_data['dtd_order'].extend(
            ['trim_x_start', 'trim_x_end', 'x_length', 'x_pitch', 'trim_y_start', 'trim_y_end', 'y_length', 'y_pitch'])
    lists, patterns = pages.gen_patterns(info['type'])
    dictionary = pages.get_dictionary(username)
    if 'total_weight' not in info:
        info['total_weight'] = 0
    return order_data, [lists, patterns, dictionary], round(info['total_weight'])


def edit_row():
    if not users.validate_user():
        return users.logout()
    req_vals = dict(main.request.values)
    if main.request.method == 'GET':
        main.session['order_id'] = req_vals['order_id']
        if 'job_id' in req_vals:
            main.session['job_id'] = req_vals['job_id']
        order_data, page_data, total_weight = edit_order_data()
        if order_data:
            order_data['dtd_order'] = list(order_data['data_to_display'].keys())
            defaults = {'bar_type': 'מצולע'}
            for item in order_data['order_rows'][0]:
                if isinstance(order_data['order_rows'][0][item], list):
                    for li in range(len(order_data['order_rows'][0][item])):
                        if li > 0:
                            defaults[item + "_" + str(li - 1)] = order_data['order_rows'][0][item][li]
                        else:
                            defaults[item] = order_data['order_rows'][0][item][li]
                elif 'job_id' in req_vals:
                    defaults[item] = order_data['order_rows'][0][item]
                    defaults[item] = order_data['order_rows'][0][item]
                elif 'addbefore' in req_vals:
                    defaults['addbefore'] = req_vals['addbefore']
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
            order_id += '|'+req_vals['job_id']
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
    rows, info, additional = get_order_data(order_id)
    if job_id != "":
        resp = main.mongo.update_one('orders', {'order_id': order_id, 'job_id': job_id},
                                     {'status': new_status, 'status_updated_by': main.session['username']}, '$set')
        if resp.matched_count > 0:
            functions.log('job_status_change', {'order_id': order_id, 'job_id': job_id, 'status': new_status})
            if new_status == 'Production':
                if main.mongo.read_collection_one('orders', {'order_id': order_id+'R'}):
                    update_order_status(new_status, order_id+'R')
        if not rows:
            return
        for row in rows:
            if row['status'] != "order_status_Finished":
                return
        update_order_status('Finished', order_id)
    else:
        resp = main.mongo.update_one('orders', {'order_id': order_id, 'info': {'$exists': True}}, {'info.status':
                                     new_status, 'info.status_updated_by': main.session['username']}, '$set')
        main.mongo.update_many('orders', {'order_id': order_id, 'info': {'$exists': False},'status':{'$ne':"Finished"}},
                               {'status': new_status, 'status_updated_by': main.session['username']}, '$set')
        if 'reason' in main.request.form:
            functions.log('cancel_order', main.request.form['reason'])
            main.mongo.update_one('orders', {'order_id': order_id, 'info': {'$exists': True}},
                                  {'info.cancel_reason': main.request.form['reason']}, '$set')
        else:
            main.mongo.update_one('orders', {'order_id': order_id, 'info': {'$exists': True}},
                                  {'info.cancel_reason': ''}, '$unset')
        if resp.matched_count > 0:
            functions.log('order_status_change', {'order_id': order_id, 'status': new_status})
            if new_status == 'Processed' and main.session['username'] not in ['Baruch', 'baruch']:
                msg = 'הודפסה הזמנה לקוח מס. {order_id}\nמתאריך: {date_created}\n לתאריך אספקה:{date_delivery}\nלקוח: {costumer_name}\nאתר: {costumer_site}\nמשקל: {total_weight} \nשורות: {rows} \n{username} '\
                    .format(order_id=order_id, date_created=info['date_created'], date_delivery=info['date_delivery'], costumer_name=info['costumer_name'], costumer_site=info['costumer_site'], total_weight=info['total_weight'], rows=info['rows'], username=main.session['username'])
                phone_book = ['0509595953', '0509393938', '0528008018', '0502201747']
                functions.send_sms(msg, phone_book)


def close_order():
    if not users.validate_user():
        return users.logout()
    if len(list(main.request.values)) > 0:
        req_vals = list(main.request.values)
        additional_func = req_vals[0]
        if additional_func == 'delete_order':
            main.mongo.delete_many('orders', {'order_id': main.session['order_id']})
        elif additional_func == 'delete_row':
            main.mongo.delete_many('orders', {'order_id': main.session['order_id'], 'job_id': main.session['job_id']})
            update_orders_total_weight()
            reorder_job_id()
            return main.redirect('/orders')
        elif additional_func == 'scan':
            return main.redirect('/scan')
    users.clear()
    return main.redirect('/orders')


def update_orders_total_weight(order_id=''):
    if not order_id:
        order_id = main.session['order_id']
    order_data_df = main.mongo.read_collection_df('orders', query={'info': {'$exists': False}, 'order_id': order_id, 'job_id': {'$ne': "0"}})
    rows_count = len(order_data_df.index)
    if rows_count == 0:
        total_weight = 0
    else:
        total_weight = sum(order_data_df[order_data_df['order_id'] == order_id]['weight'].to_list())
    if not math.isnan(total_weight):
        main.mongo.update_one('orders', {'order_id': order_id, 'info': {'$exists': True}}, {'info.total_weight': int(total_weight), 'info.rows': rows_count}, '$set')


def reorder_job_id(job_id=''):
    order_id = main.session['order_id']
    job_list, info, additional = get_order_data(main.session['order_id'], reverse=False)
    rows = len(job_list)
    index = 1
    if job_list:
        if job_id:
            main.mongo.update_one('orders', {'order_id': order_id, 'job_id': job_list[-1]['job_id']},
                                  {'job_id': str(rows+1)}, '$set')
        for job in job_list:
            if job['job_id'] != '0' and index <= rows:
                if job['job_id'] == job_id:
                    index += 1
                main.mongo.update_one('orders', {'order_id': order_id, 'job_id': job['job_id']},
                                        {'job_id': str(index)}, '$set')
                index += 1
        if job_id:
            main.mongo.update_one('orders', {'order_id': order_id, 'job_id': str(rows+1)},
                                  {'job_id': job_id}, '$set')
    main.mongo.update_one('orders', {'order_id': order_id, 'info': {'$exists': True}},
                          {'info.rows': str(rows)}, '$set')


def calc_weight(diam, length, qnt):
    return round(float(length) * float(qnt) * main.configs.weights[str(diam)] / 100, 2)


def peripheral_orders(add_orders, order_id, orig_job_id):
    description = "הזמנת ייצור להכנת רשת. מספר הזמנת מקור: " + order_id + " שורה מספר: " + orig_job_id
    order_id += "R"
    for order in range(len(add_orders)):
        job_id = str(order+1) + '_' + orig_job_id
        order_weight = calc_weight(add_orders[order]['diam'], add_orders[order]['length'], add_orders[order]['qnt'])
        info = {'costumer_name': 'צומת ברזל', 'costumer_id': '0', 'created_by': main.session['username'],
                'date_created': ts(), 'type': 'R', 'status': 'NEW'}
        main.mongo.upsert_collection_one('orders', {'order_id': order_id, 'info': {'$exists': True}},
                                         {'order_id': order_id, 'info': info})
        peripheral_order = {'order_id': order_id, 'job_id': job_id, 'status': 'NEW', 'date_created': ts(),
                            'description': description, 'quantity': add_orders[order]['qnt'], 'shape': "1",
                            'length': add_orders[order]['length'], 'bar_type': 'מצולע',
                            'diam': add_orders[order]['diam'], 'weight': order_weight,
                            'shape_data': [add_orders[order]['length']],'element': 'שורה: '+orig_job_id}
        main.mongo.upsert_collection_one('orders', {'order_id': order_id, 'job_id': job_id}, peripheral_order)
    order_data = main.mongo.read_collection_df('orders', query={'order_id': order_id,
                                                                'info': {'$exists': False}, 'job_id': {'$ne': '0'}})
    weight_list = order_data['weight'].to_list()
    total_weight = sum(weight_list)
    main.mongo.update_one('orders', {'order_id': order_id, 'info': {'$exists': True}},
                          {'info.total_weight': round(total_weight), 'info.rows': len(weight_list)}, '$set')


def gen_job_id(order_id):
    job_ids_df = main.mongo.read_collection_df('orders', query={'order_id': order_id, 'info': {'$exists': False}})
    if job_ids_df.empty:
        return "1"
    job_ids = job_ids_df['job_id'].astype(int).tolist()
    return str(int(max(job_ids)) + 1)


def copy_order():
    if main.request.form:
        req_form = dict(main.request.form)
        order_id = req_form['order_id']
        copies = int(req_form['copies'])
        for copy in list(range(copies)):
            new_id = new_order_id()
            order_data = list(main.mongo.read_collection_list('orders', {'order_id': order_id}))
            for doc in order_data:
                doc['order_id'] = new_id
                if 'info' in doc:
                    doc['info']['status'] = 'NEW'
                else:
                    doc['status'] = 'NEW'
                main.mongo.insert_collection_one('orders', doc)
        return '', 204
    return main.render_template('/copy_order.html')


def split_order():
    rows, info, adit = get_order_data(main.session['order_id'], reverse=False)
    if main.request.form:
        req_form = dict(main.request.form)
        for item in req_form:
            if req_form[item]:
                split = int(req_form[item])
            else:
                split = 1
            main.mongo.update_one('orders', {'order_id': main.session['order_id'], 'job_id': item}, {'order_split': split}, '$set')
        _split = main.mongo.read_uniq('orders', 'order_split', {'order_id': main.session['order_id']})
        main.mongo.update_one('orders', {'order_id': main.session['order_id'], 'info': {'$exists':True}}, {'info.split': len(_split)}, '$set')
        if len(_split) == 1:
            main.mongo.update_many('orders', {'order_id': main.session['order_id'], 'job_id': {'$exists': True}},
                                   {'order_split': split}, '$unset')
            main.mongo.update_one('orders', {'order_id': main.session['order_id'], 'info': {'$exists':True}}, {'info.split': len(_split)}, '$unset')
        return '', 204
    return main.render_template('/split_order.html', order=rows)
