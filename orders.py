import time
from datetime import datetime, timedelta
import configs
import functions
import main
import piles
import users
import clients
import pandas as pd
import pages
from functions import ts
import math
from collections import OrderedDict


def orders(_all=False):
    req_vals = dict(main.request.values)
    rev = True
    if not users.validate_user():
        return users.logout()
    if 'order_id' in main.session.keys():
        main.session['job_id'] = ""
        return main.redirect('/edit_order')
    query = {'info.type': {'$ne': 'integration'}, 'info.status': {'$nin': ['canceled', 'Delivered', 'PartlyDelivered', 'PartlyDeliveredClosed']}, 'info.costumer_id': {'$ne': '58'},
             'info.date_created': {'$gte': functions.ts('html_date', 150), '$lte': functions.ts('html_date') + 'T23:59:59'}}
    defaults = {'from': functions.ts('html_date', 150), 'to': functions.ts('html_date')}
    if req_vals:
        if 'date_from' in req_vals:
            query['info.date_created']['$gte'] = req_vals['date_from']
            defaults['from'] = req_vals['date_from']
        if 'date_to' in req_vals:
            query['info.date_created']['$lte'] = req_vals['date_to'] + 'T23:59:59'
            defaults['to'] = req_vals['date_to']

    if 'user_config' in main.session:
        if 'search' in main.session['user_config']:
            if main.session['user_config']['search']:
                del query['info.status']
                del query['info.costumer_id']
                exclude = ['reverse']
                for k in main.session['user_config']['search']:
                    if k == 'info.status':
                        defaults[k] = main.session['user_config']['search'][k]
                        if main.session['user_config']['search'][k] == 'Production':
                            query[k] = {'$in': ['Production', 'InProduction']}
                        else:
                            query[k] = str(main.session['user_config']['search'][k])
                    elif k not in exclude:
                        defaults[k] = main.session['user_config']['search'][k]
                        val = str(main.session['user_config']['search'][k])
                        if '(' in val or ')' in val:
                            val = val.split(' ')
                            arr = []
                            for v in val:
                                arr.append({k: {'$regex': v.replace(')', '').replace('(', '')}})
                            query['$and'] = arr
                        else:
                            query[k] = {'$regex': val}
                    elif k == 'reverse':
                        rev = False
    # Read all orders data with Info, mean that it's not including order rows
    orders_data = main.mongo.read_collection_list('orders', query)
    if not orders_data:
        if 'info.date_created' in query:
            del query['info.date_created']
            orders_data = main.mongo.read_collection_list('orders', query)
    dictionary = pages.get_dictionary()
    dictionary['rebar$'] = 'רשת סטנדרט'
    orders_info = []
    sites_search_list = []
    for order in orders_data:
        row = order['info'].copy()
        row['order_id'] = order['order_id']
        row['status'] = 'order_status_' + row['status']
        finished_cntr = 0
        finished_weight = 0
        for r in order['rows']:
            if r['status'] not in ['NEW', 'Processed', 'Production', 'InProduction']:
                finished_cntr += 1
                if 'weight' in r:
                    finished_weight += float(r['weight'])
        row['finished'] = finished_cntr
        row['finished_weight'] = round(finished_weight,2)
        # if 'linked_orders' in row:
        #     temp = row['linked_orders'].copy()
        #     row['linked_orders'] = ''
        #     row['linked_orders_tot_w'] = 0#int(row['total_weight'])
        #     linked = []
        #     for i in temp:
        #         linked.append(i['order_id'])
        #         # rows, info = get_order_data(i['order_id'])
        #         # row['linked_orders_tot_w'] += int(info['total_weight'])
        #         if i['order_id'] != row['order_id']:
        #             order_type = i['type']
        #             if i['type'] in dictionary:
        #                 order_type = dictionary[i['type']]
        #             row['linked_orders'] += '\n[{} : {}] '.format(i['order_id'], order_type)
        #     linked_orders = main.mongo.read_collection_list('orders', {'order_id': {'$in': linked}})
        #     for ll in linked_orders:
        #         row['linked_orders_tot_w'] += int(ll['info']['total_weight'])
        orders_info.append(row)
        if 'info.costumer_name' in defaults:
            if 'costumer_site' in row:
                if row['costumer_site'] not in sites_search_list:
                    sites_search_list.append(row['costumer_site'])
    orders_info.sort(key=lambda k: int(k['order_id'].replace('R','').replace('K','')), reverse=rev)
    ord_types = configs.order_types.copy()
    ord_types.insert(3, 'rebar$')
    reb_cat = configs.rebar_catalog
    search = {}
    if 'search' in main.session['user_config']:
        search = main.session['user_config']['search']
    return main.render_template('orders.html', orders=orders_info, display_items=main.configs.data_to_display['orders'],
                                dictionary=dictionary, defaults=defaults, search=search,
                                order_types=ord_types, order_statuses=configs.order_statuses, sites_search_list=sites_search_list, reb_cat=reb_cat, diams=list(configs.weights.keys()))


def overview():
    if not users.validate_user():
        return main.redirect('/')
    query = {'info.type': 'regular', 'info.status': {'$regex': 'Production'}, 'info.costumer_id': {'$ne': '58'}}
    orders_data = main.mongo.read_collection_list('orders', query)
    orders_info = []
    for o in orders_data:
        row = {'order_id': o['order_id']}
        row.update(o['info'])
        orders_info.append(row)
        row['status'] = 'order_status_' + row['status']
        finished_cntr = 0
        for r in o['rows']:
            if r['status'] not in ['NEW', 'Processed', 'Production', 'InProduction']:
                finished_cntr += 1
        row['finished'] = finished_cntr
    orders_info.sort(key=lambda k: int(k['order_id'].replace('R', '')), reverse=True)
    if len(orders_info)%2:
        orders_info.append({'finished': 0})
    return main.render_template('productionov.html', orders=orders_info, display_items=main.configs.data_to_display['productionov'],
                                dictionary=pages.get_dictionary())


def new_order(client="", order_type=""):
    user_group = users.validate_user()
    if not user_group:
        return users.logout()
    req_form = dict(main.request.form)
    types = configs.new_order_types
    order_id = ''
    req_vals = list(main.request.values)
    if 'name' in req_form or client:
        if 'site' in req_form and 'sites_list' in main.session.keys():
            if 'order_id' in req_form and 'order_id' in main.session.keys():
                if req_form['order_id'] == main.session['order_id']:
                    doc = {'info.costumer_name': req_form['name'],
                           'info.costumer_id':
                               main.mongo.read_collection_one('costumers', {'name': req_form['name']})['id'],
                           'info.costumer_site': req_form['site'], 'info.type': req_form['order_type']}
                    main.mongo.update_one('orders', {'order_id': main.session['order_id'], 'info': {'$exists': True}},
                                          doc, '$set')
                    main.mongo.update_one('orders', {'order_id': '{}R'.format(main.session['order_id'])}, {'info.comment': req_form['name']}, '$set')
                    return main.render_template('/close_window.html')
            if req_form['site'] in main.session['sites_list']:
                main.session['sites_list'] = []
                user = main.session['username']
                client = req_form['name']
                client_id = main.mongo.read_collection_one('costumers', {'name': client})['id']
                site = req_form['site']
                order_type = req_form['order_type']
                order_id = new_order_id()
                order = {'order_id': order_id, 'info': {'created_by': user, 'date_created': ts(), 'date_delivery': ts('html_date'),
                                                        'type': order_type, 'costumer_name': client,
                                                        'costumer_id': client_id,
                                                        'costumer_site': site, 'status': 'NEW'}, 'rows': []}
                main.mongo.insert_collection_one('orders', order)
                main.session['order_id'] = order_id
                return main.redirect('/orders')
        elif 'name' in req_form:
            client = req_form['name']
            order_id = req_form['order_id']
    if req_vals and not order_type and not req_form:
        order_id = req_vals[0]
        ord_rows, ord_info = get_order_data(order_id)
        if ord_info:
            order_type = ord_info['type']
            if ord_rows:
                types = [ord_info['type']]
        else:
            order_type = req_vals[0]
            order_id = ''
    elif 'order_type' in req_form:
        order_type = req_form['order_type']
    client_list, sites_list = clients.gen_client_list(client)
    permission = False
    if user_group > 50:
        permission = True
    if sites_list:
        sites = []
        for s in sites_list:
            sites.append(s['name'])
        main.session['sites_list'] = sites
    return main.render_template('/pick_client.html', clients=client_list, site=sites_list, order_type=order_type,
                                permission=permission, dictionary=pages.get_dictionary(), types=types, order_id=order_id)


def new_order_row():
    # new_row new row
    if 'order_id' not in main.session:
        return
    order_id = main.session['order_id']
    if 'R' in order_id or 'K' in order_id:
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
        req_form_data[item] = req_form_data[item].strip()
        if '\n' in req_form_data[item]:
            spl = req_form_data[item].split('\n')
            req_form_data[item] = "".join(spl)
            spl = req_form_data[item].split('\r')
            req_form_data[item] = " ".join(spl)
        if item in configs.html_no_float and '.' in req_form_data[item]:
            req_form_data[item] = str(int(float(req_form_data[item])))
        # if req_form_data[item].isnumeric():
        #     req_form_data[item] = str(int(req_form_data[item]))
        if req_form_data[item] not in ['---', ''] and '_hid' not in item:
            if '_length' in item:
                new_row[item[:item.find('h') + 1]].append(req_form_data[item])
                if item.replace('length', 'pitch') not in req_form_data:
                    new_row[item[:item.find('h') + 1].replace('length', 'pitch')].append(req_form_data[item])
                elif req_form_data[item.replace('length', 'pitch')] in ['0', '']:
                    new_row[item[:item.find('h') + 1].replace('length', 'pitch')].append(req_form_data[item])
                else:
                    new_row[item[:item.find('h') + 1].replace('length', 'pitch')].append(req_form_data[item.replace('length', 'pitch')])
            elif '_pitch' in item:
                continue
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
        new_row['length'] = sum(list(map(int, new_row['y_length'])))
        new_row['width'] = sum(list(map(int, new_row['x_length'])))
        new_row['length'] += int(float(new_row['trim_y_start']) + float(new_row['trim_y_end']))
        new_row['width'] += int(float(new_row['trim_x_start']) + float(new_row['trim_x_end']))
        for i in range(len(new_row['x_length'])):
            if new_row['x_pitch'][i] != "0":
                new_row['trim_x_end'] = str(float(new_row['trim_x_end']) +
                                            int(new_row['x_length'][i]) % int(new_row['x_pitch'][i])).replace('.0', '')
                new_row['x_length'][i] = str(
                    int(new_row['x_length'][i]) - (int(new_row['x_length'][i]) % int(new_row['x_pitch'][i])))
                bars_y += math.floor(int(new_row['x_length'][i]) / int(new_row['x_pitch'][i]))
            else:
                bars_y += 1
        for i in range(len(new_row['y_length'])):
            if new_row['y_pitch'][i] != "0":
                new_row['trim_y_end'] = str(float(new_row['trim_y_end']) +
                                            int(new_row['y_length'][i]) % int(new_row['y_pitch'][i]))
                new_row['y_length'][i] = str(
                    int(new_row['y_length'][i]) - (int(new_row['y_length'][i]) % int(new_row['y_pitch'][i])))
                bars_x += math.floor(int(new_row['y_length'][i]) / int(new_row['y_pitch'][i]))
            else:
                bars_x += 1
        x_pitch = '(' + ')('.join(list(set(new_row['x_pitch']))) + ')'
        y_pitch = '(' + ')('.join(list(set(new_row['y_pitch']))) + ')'
        new_row['x_bars'] = int(bars_x)
        new_row['y_bars'] = int(bars_y)
        new_row['x_weight'] = calc_weight(new_row['diam_x'], new_row['width'], bars_x)
        new_row['y_weight'] = calc_weight(new_row['diam_y'], new_row['length'], bars_y)
        new_row['description'] = "H" + str(new_row['width']) + "X" + str(bars_x) + "X" + str(new_row['diam_x']) + \
                                 "WBX" + y_pitch + " V" + str(new_row['length']) + "X" + str(bars_y) + "X" + \
                                 str(new_row['diam_y']) + "WBX" + x_pitch
        new_row['unit_weight'] = round(new_row['x_weight'] + new_row['y_weight'], 2)
        new_row['weight'] = round(new_row['unit_weight'] * int(new_row['quantity']), 2)
        if 'הזמנת_ייצור' in new_row:
            x_bars = {'length': new_row['width'], 'qnt': bars_x * int(new_row['quantity']), 'diam': new_row['diam_x']}
            y_bars = {'length': new_row['length'], 'qnt': bars_y * int(new_row['quantity']), 'diam': new_row['diam_y']}
            peripheral_orders([x_bars, y_bars], order_id, job_id)
    elif 'mkt' in new_row:
        if new_row['mkt'] in main.configs.rebar_catalog:
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
        elif new_row['mkt'] in main.configs.girders_catalog:
            cat = main.configs.girders_catalog[new_row['mkt']]
            new_row['shape'] = new_row['mkt']
            new_row['weight'] = float(cat['unit_weight']) * int(new_row['quantity'])
            new_row['unit_weight'] = cat['unit_weight']
    elif 'shape' in req_form_data:
        if new_row['shape'] not in configs.shapes:
            return '', 204
        new_row['description'] = ""
        if float(new_row['diam']) < 7:
            new_row['bar_type'] = "חלק"
        new_row['shape_data'] = req_form_data['shape_hid'].split(',')
        new_row['shape_ang'] = configs.shapes[new_row['shape']]['ang']
        new_row['weight'] = calc_weight(new_row['diam'], new_row['length'], new_row['quantity'])
    elif 'spiral' in new_row:
        weight, new_row['length'] = piles.calc_weight(new_row)
        new_row['weight'] = weight['total']
        new_row['pile_weight'] = weight['pile']
        new_row['pipe_weight'] = weight['pipes']
        if 'bend' in new_row:
            if 'bend_len' not in new_row:
                new_row['bend_len'] = '20'
            new_row['length'] += int(new_row['bend_len'])
        if 'הזמנת_ייצור' in new_row:
            bars = []
            if 'bars' in new_row:
                bars.append({'length': new_row['bars_len'], 'qnt': int(new_row['bars'])*int(new_row['quantity']), 'diam': new_row['bars_diam']})
            if 'bars_1' in new_row:
                bars.append({'length': new_row['bars_len_1'], 'qnt': int(new_row['bars_1'])*int(new_row['quantity']), 'diam': new_row['bars_diam_1']})
            if bars:
                peripheral_orders(bars, order_id, job_id, 'K')
    else:
        # Order comment
        if 'comment_hid' in req_form_data:
            order['info']['comment'] = req_form_data['comment_hid']
        if 'date_delivery_hid' in req_form_data:
            order['info']['date_delivery'] = req_form_data['date_delivery_hid']
        main.mongo.update_one('orders', {'order_id': new_row['order_id']}, order, '$set')
        return
    # Takes to manual input for weightNYDESK
    if 'weight' in req_form_data:
        if req_form_data['weight'].replace('.', '').isdigit():
            new_row['weight'] = float(req_form_data['weight'])
        if 'unit_weight' in new_row:
            new_row['unit_weight'] = round(new_row['weight'] / int(new_row['quantity']),2)
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
        order['info']['total_weight'] += float(order['rows'][i]['weight'])
    order['rows'].append(new_row)
    # order['info']['total_weight'] = round(order['info']['total_weight'])
    order['info']['total_weight'] = str(int(order['info']['total_weight']))
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
    if order_data['info']['type'] == 'piles':
        defaults['3%'] = 'Yes'
        defaults['הזמנת_ייצור'] = 'Yes'
    return main.render_template('/edit_order.html', order_data=order_data, patterns=page_data[1], lists=page_data[0],
                                dictionary=page_data[2], rebar_data={}, defaults=defaults, msg=msg)


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
        if info['type'] == 'rebar':
            row['diam'] = row['diam_x']
            row['pitch'] = row['x_pitch']
    order_data.sort(key=lambda k: int(k['job_id']), reverse=reverse)
    return order_data.copy(), info


def _new_order_id():
    new_id = '1'
    orders_df = main.mongo.read_collection_df('orders',
                                              query={'info': {'$exists': True}, 'info.type': {'$ne': 'integration'}})
    if orders_df.empty:
        return new_id
    order_ids_list = orders_df['order_id'].unique().tolist()
    for _id in order_ids_list:
        if _id.isdigit():
            if int(_id) >= int(new_id):
                new_id = int(_id) + 1
    return str(new_id)


def new_order_id():
    main.mongo.update_one('data_lists', {'name': 'ids'}, {'order_id': 1}, '$inc')
    new_id = main.mongo.read_collection_one('data_lists', {'name': 'ids'})['order_id']
    return str(new_id)


def edit_order_data():
    order_id = main.session['order_id']
    job_id = ""
    if 'job_id' in main.session.keys():
        job_id = main.session['job_id']
    # Read all data of this order
    rows, info = get_order_data(order_id, job_id)
    del info['costumer_id']
    if not info:
        return {}, [], 0
    if info['type'] == 'R' or info['type'] == 'K':
        keys_to_display = main.configs.data_to_display['new_row_regular']
    else:
        keys_to_display = main.configs.data_to_display['new_row_' + info['type']]
    if info['status'] != 'NEW':
        keys_to_display['status_updated_by'] = 2
    locked = bool(main.mongo.read_collection_one('orders', {'order_id': order_id, 'rows': {"$elemMatch": {"status": {"$in": ['Finished', 'InProduction']}}}}))
    order_data = {'info': info, 'data_to_display': keys_to_display, 'order_rows': rows,
                  'dtd_order': list(keys_to_display.keys()), 'locked': locked}
    if info['type'] == 'rebar_special':
        order_data['include'] = 'spec_rebar_editor.html'
        order_data['dtd_order'] = ['job_id', 'mkt', 'quantity', 'הזמנת_ייצור', 'חיתוך', 'diam_x', 'diam_y', 'length',
                                   'width', 'weight', 'pack_quantity', 'trim_x_start', 'trim_x_end', 'x_length', 'x_pitch',
                                   'x_length1', 'x_pitch1', 'x_length2', 'x_pitch2', 'x_length3', 'x_pitch3', 'x_length4',
                                   'x_pitch4', 'x_length5', 'x_pitch5', 'x_length6', 'x_pitch6', 'x_length7', 'x_pitch7',
                                   'x_length8', 'x_pitch8', 'x_length9', 'x_pitch9', 'x_length10', 'x_pitch10', 'x_length11',
                                   'x_pitch11', 'x_length12', 'x_pitch12', 'x_length13', 'x_pitch13', 'x_length14',
                                   'x_pitch14', 'x_length15', 'x_pitch15', 'x_length16', 'x_pitch16', 'x_length17',
                                   'x_pitch17', 'x_length18', 'x_pitch18', 'x_length19', 'x_pitch19', 'trim_y_start',
                                   'trim_y_end', 'y_length', 'y_pitch', 'y_length1', 'y_pitch1', 'y_length2', 'y_pitch2',
                                   'y_length3', 'y_pitch3', 'y_length4', 'y_pitch4', 'y_length5', 'y_pitch5', 'y_length6',
                                   'y_pitch6', 'y_length7', 'y_pitch7', 'y_length8', 'y_pitch8', 'y_length9', 'y_pitch9',
                                   'y_length10', 'y_pitch10', 'y_length11', 'y_pitch11', 'y_length12', 'y_pitch12', 'y_length13',
                                   'y_pitch13', 'y_length14', 'y_pitch14', 'y_length15', 'y_pitch15', 'y_length16', 'y_pitch16',
                                   'y_length17', 'y_pitch17', 'y_length18', 'y_pitch18', 'y_length19', 'y_pitch19', 'bend1', 'bend2', 'bend3']
    elif info['type'] == 'piles':
        order_data['include'] = 'piles_editor.html'
        order_data['dtd_order'].extend(
            ['spiral', 'pitch', 'spiral_1', 'pitch_1', 'spiral_2', 'pitch_2', 'spiral_3', 'pitch_3', 'bars', 'bars_diam', 'bars_len',
             'bars_1', 'bars_diam_1', 'bars_len_1', 'rings', 'rings_diam', 'pipes', 'pipe_diam', 'pipe_len', 'pipe_thick', 'pile_comment'])
    lists, patterns = pages.gen_patterns(info['type'])
    dictionary = pages.get_dictionary()
    if 'total_weight' not in info:
        info['total_weight'] = 0
    return order_data, [lists, patterns, dictionary]


def edit_row():
    if not users.validate_user():
        return users.logout()
    req_vals = dict(main.request.values)
    if 'cancel_row' in req_vals:
        cancel_row(main.session['order_id'], main.session['job_id'])
        return main.redirect('/orders')
    if main.request.method == 'GET':
        main.session['order_id'] = req_vals['order_id']
        if 'job_id' in req_vals:
            main.session['job_id'] = req_vals['job_id']
        order_data, page_data = edit_order_data()
        if order_data:
            if order_data['order_rows'][0]['status'] not in ['InProduction', 'Finished']:
                order_data['dtd_order'] = list(order_data['data_to_display'].keys())
                defaults = {'bar_type': 'מצולע'}
                if 'addbefore' in req_vals:
                    defaults['addbefore'] = req_vals['addbefore']
                else:
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
    job_id = ''
    if main.request.form:
        order_id = main.request.form['order_id']
        if 'job_id' in req_vals:
            job_id = main.request.form['job_id']
            if 'cancel_row' in req_vals:
                cancel_row(order_id, job_id)
                return '', 204
        update_order_status(main.request.form['status'], order_id, job_id)
        return '', 204
    if req_vals:
        if 'order_id' in req_vals:
            order_id = req_vals['order_id']
        else:
            order_id = main.session['order_id']
        if 'job_id' in req_vals:
            job_id = req_vals['job_id']
    else:
        order_id = main.session['order_id']
    return main.render_template('change_order_status.html', order_id=order_id, job_id=job_id,
                                status_history=get_status_history(order_id, job_id), dictionary=pages.get_dictionary())


def cancel_order():
    user_group = users.validate_user()
    if not user_group:
        return users.logout()
    elif user_group < 70:
        return '', 204
    order_id = main.session['order_id']
    return main.render_template('cancel_order.html', order_id=order_id)


def update_order_status(new_status, order_id, job_id="", force=False):
    order = main.mongo.read_collection_one('orders', {'order_id': order_id})
    import re
    # ---------- over protection ------------------------
    while 'order_status_' in new_status:
        new_status = new_status.replace('order_status_', '')
    while ' ' in new_status:
        new_status = new_status.replace(' ', '')
    # ---------- over protection ------------------------
    if not force:
        if not order:# or (order['info']['status'] in ['InProduction', 'Finished'] and new_status in ['NEW', 'Processed', 'Production']):
            return
    flag = True
    if job_id != "":
        for spl in job_id.split(','):
            for i in range(len(order['rows'])):
                if order['rows'][i]['job_id'] == spl:
                    order['rows'][i]['status'] = new_status
                    order['rows'][i]['status_updated_by'] = main.session['username'] + ' : ' + ts()
                    functions.log('job_status_change', {'order_id': order_id, 'job_id': spl, 'status': new_status})
                status_list = configs.all_statuses
                only_fwd_cond = status_list.index(new_status) < status_list.index(order['info']['status'])
                if order['rows'][i]['status'] != new_status or new_status not in ['Finished', 'Loaded'] or only_fwd_cond:
                    flag = False
            if flag:
                dic = {'Finished': 'Finished', 'Loaded': 'Delivered'}
                order['info']['status'] = dic[new_status]
    else:
        order['info']['status'] = new_status
        if re.search('NEW|Processed|Production', new_status):
            for i in range(len(order['rows'])):
                if re.search('NEW|Processed|Production', order['rows'][i]['status']) or force:
                    order['rows'][i]['status'] = new_status
        if not force:
            if 'reason' in main.request.form:
                functions.log('cancel_order', main.request.form['reason'])
                order['info']['cancel_reason'] = main.request.form['reason']
            else:
                if 'cancel_reason' in order['info']:
                    if 'history' not in order['info']:
                        order['info']['history'] = []
                    order['info']['history'].append('canceled: '+order['info']['cancel_reason'])
                    del order['info']['cancel_reason']
            functions.log('order_status_change', {'order_id': order_id, 'status': new_status})
            if new_status == 'Processed' and order['info']['costumer_name'] not in ['צומת ברזל', 'טסטים \ בדיקות', 'מלאי חצר']:
                dictionary = pages.get_dictionary()
                msg = 'הודפסה הזמנה לקוח מס. {order_id}\nמתאריך: {date_created}\n לתאריך אספקה:{date_delivery}\nלקוח: {costumer_name}\nאתר: {costumer_site}\nמשקל: {total_weight} \nשורות: {rows} [{type}] \n{username} ' \
                    .format(order_id=order_id, date_created=order['info']['date_created'], date_delivery=order['info']['date_delivery'],
                            costumer_name=order['info']['costumer_name'], costumer_site=order['info']['costumer_site'],
                            total_weight=order['info']['total_weight'], rows=order['info']['rows'], username=main.session['username'], type=dictionary[order['info']['type']])
                phone_book = configs.phones_to_notify
                functions.send_sms(msg, phone_book)
    order['info']['last_status_update'] = ts()
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
            for r in order['rows']:
                if r['status'] in ['InProduction', 'Finished']:
                    return main.redirect('/orders')
            indx_to_del = None
            order['info']['total_weight'] = 0
            for i in range(len(order['rows'])):
                if 'job_id' not in main.session:
                    return main.redirect('/orders')
                order['info']['total_weight'] += order['rows'][i]['weight']
                if int(order['rows'][i]['job_id']) > int(main.session['job_id']) and ('R' not in order_id and 'K' not in order_id):
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


def peripheral_orders(add_orders, order_id, orig_job_id, indicator="R"):
    if indicator == "R":
        description = "הזמנת ייצור להכנת רשת. מספר הזמנת מקור: " + order_id + " שורה מספר: " + orig_job_id
    elif indicator == 'K':
        description = "הזמנת ייצור להכנת כלונסאות. מספר הזמנת מקור: " + order_id + " שורה מספר: " + orig_job_id
    else:
        description = ''
    rows, original_info = get_order_data(order_id)
    order_id += indicator
    rows, info = get_order_data(order_id)
    if not info:
        info = {'costumer_name': 'מלאי חצר', 'costumer_id': '114', 'created_by': main.session['username'], 'date_created': ts(),
                'type': indicator, 'status': 'NEW', 'costumer_site': original_info['costumer_site'], 'comment': original_info['costumer_name']}
        rows = []
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
    info['rows'] = len(rows)
    update_order = {'order_id': order_id, 'rows': rows, 'info': info}
    main.mongo.update_one('orders', {'order_id': order_id},
                          update_order, '$set', upsert=True)


def copy_order():
    client_list, sites_list = clients.gen_client_list()
    order_id = ''
    client = ''
    site = ''
    if main.request.form:
        req_form = dict(main.request.form)
        order_id = req_form['order_id']
        order = main.mongo.read_collection_one('orders', {'order_id': order_id})
        if not order:
            order_id = ''
        else:
            client, sites_list = clients.gen_client_list(order['info']['costumer_name'])
            site = order['info']['costumer_site']
            # client_list = [client_list]
        if 'copies' in req_form:
            copies = int(req_form['copies'])
            for copy in list(range(copies)):
                new_id = new_order_id()
                order['order_id'] = new_id
                order['info']['date_created'] = ts()
                order['info']['date_delivery'] = ts('html_date')
                order['info']['created_by'] = main.session['username']
                order['info']['costumer_name'] = req_form['client']
                order['info']['costumer_id'] = main.mongo.read_collection_one('costumers', {'name': req_form['client']})['id']
                order['info']['costumer_site'] = req_form['site']
                for row in order['rows']:
                    row['order_id'] = new_id
                    row['status'] = 'NEW'
                    row['date_created'] = order['info']['date_created']
                    if 'status_updated_by' in row:
                        del row['status_updated_by']
                        for key in list(row.keys()):
                            if 'qnt_done' in key:
                                del row[key]
                    if 'order_split' in row:
                        del row['order_split']
                    # todo: if הזמנת ייצור
                main.mongo.insert_collection_one('orders', order)
                update_order_status('NEW', new_id, force=True)
            return '', 204
    return main.render_template('/copy_order.html', order_id=order_id, client_list=client_list, sites_list=sites_list, client=client, site=site)


def split_order():
    order_id = main.session['order_id']
    rows, info = get_order_data(order_id)
    if main.request.form:
        req_form = dict(main.request.form)
        splits = []
        for i in req_form:
            if req_form[i] not in splits and req_form[i].isnumeric():
                splits.append(req_form[i])
        if len(splits) < 2:
            if 'split' in info:
                del info['split']
        else:
            info['split'] = len(splits)
        for i in range(len(rows)):
            if rows[i]['job_id'] in req_form:
                if req_form[rows[i]['job_id']]:
                    rows[i]['order_split'] = req_form[rows[i]['job_id']]
                else:
                    rows[i]['order_split'] = 1
            elif len(splits) < 2:
                if 'order_split' in rows[i]:
                    del rows[i]['order_split']
        if 'reason' in main.request.form:
            functions.log('split_order', main.request.form['reason'])
            info['split_reason'] = main.request.form['reason']
        else:
            if 'split_reason' in info:
                if 'history' not in info:
                    info['history'] = []
                info['history'].append('split: ' + info['split_reason'])
                del info['split_reason']
                for r in rows:
                    if 'order_split' in r:
                        del r['order_split']
        main.mongo.update_one('orders', {'order_id': order_id}, {'info': info, 'rows': rows}, '$set')
        return '', 204
    if 'split_reason' in info:
        split_reason = info['split_reason']
    else:
        split_reason = ''
    return main.render_template('/split_order.html', order=rows, split_reason=split_reason)


def link_order():
    if 'order_id' not in main.session:
        return '', 204
    order_data, order_info = get_order_data(main.session['order_id'])
    if main.request.form:
        req_form = dict(main.request.form)
        link_order_id = req_form['order_id']
        link_order_data, link_order_info = get_order_data(link_order_id)
        cur_l = {}
        to_l = {}
        for key in ['order_id', 'type', 'comment', 'total_weight']:
            if key in link_order_info:
                to_l[key] = link_order_info[key]
            if key in order_info:
                cur_l[key] = order_info[key]
        _link = [cur_l, to_l]
        if 'linked_orders' in order_info:
            _link.extend(order_info['linked_orders'])
        if 'linked_orders' in link_order_info:
            _link.extend(link_order_info['linked_orders'])
        link = []
        _filter = []
        for i in _link:
            if i['order_id'] not in _filter:
                _filter.append(i['order_id'])
                link.append(i)
        for lin in link:
            main.mongo.update_one('orders', {'order_id': lin['order_id']}, {'info.linked_orders': link}, '$set')
        return main.redirect('/link_order')
    elif main.request.values:
        req_vals = dict(main.request.values)
        unlink_order_id = req_vals['order_id']
        link = []
        for i in order_info['linked_orders']:
            if i['order_id'] != unlink_order_id:
                link.append(i)
        for lin in link:
            if len(link) == 1:
                link = []
            main.mongo.update_one('orders', {'order_id': lin['order_id']}, {'info.linked_orders': link}, '$set')
        main.mongo.update_one('orders', {'order_id': unlink_order_id}, {'info.linked_orders': []}, '$set')
        return main.redirect('/link_order')
    linked_orders = []
    if 'linked_orders' in order_info:
        linked_orders = order_info['linked_orders']
    return main.render_template('/link_order.html', linked_orders=linked_orders, cur_order=main.session['order_id'], dictionary=pages.get_dictionary())


def get_status_history(order_id, job_id):
    query = {'title': 'order_status_change', 'operation.order_id': order_id}
    if job_id:
        query['title'] = 'job_status_change'
        query['operation.job_id'] = job_id
    hist = main.mongo.read_collection_list('logs', query)
    ret = []
    if hist:
        for i in hist:
            ret.append({'username': i['username'], 'timestamp': i['timestamp'], 'status': i['operation']['status']})
    return ret


def delete_rows():
    if 'order_id' not in main.session:
        return '', 204
    req_form = dict(main.request.form)
    if req_form:
        total_weight = 0
        order_id = main.session['order_id']
        ids = []
        for item in req_form:
            if 'select_' in item:
                ids.append(req_form[item])
        rows, info = get_order_data(order_id, reverse=False)
        to_del = []
        for r in range(len(rows)):
            row = rows[r]
            if row['status'] in ['InProduction', 'Finished']:
                to_del = []
                break
            if row['job_id'] in ids:
                to_del.append(r)
            else:
                total_weight += row['weight']
                row['job_id'] = str(int(row['job_id'])-len(to_del))
        to_del.reverse()
        for i in to_del:
            rows.pop(i)
        main.mongo.update_one('orders', {'order_id': order_id}, {'rows': rows, 'info.rows': len(rows),
                                                                 'info.total_weight': total_weight}, '$set')
    return main.redirect('/orders')


def manual_pile_peripheral_order(order_id):
    order = main.mongo.read_collection_one('orders', {'order_id': order_id})
    if not order:
        return
    total = {}
    pereph = []
    for r in order['rows']:
        if 'bars' in r:
            if r['bars_diam'] not in total:
                total[r['bars_diam']] = {}
            if r['bars_len'] not in total[r['bars_diam']]:
                total[r['bars_diam']][r['bars_len']] = int(r['bars']) * int(r['quantity'])
            else:
                total[r['bars_diam']][r['bars_len']] += int(r['bars']) * int(r['quantity'])
        if 'bars_1' in r:
            if r['bars_diam_1'] not in total:
                total[r['bars_diam_1']] = {}
            if r['bars_len_1'] not in total[r['bars_diam_1']]:
                total[r['bars_diam_1']][r['bars_len_1']] = int(r['bars_1']) * int(r['quantity'])
            else:
                total[r['bars_diam_1']][r['bars_len_1']] += int(r['bars_1']) * int(r['quantity'])
    for diam in total:
        for lllen in total[diam]:
            pereph.append({'length': lllen, 'diam': diam, 'quantity': total[diam][lllen]})
    peripheral_orders()


def cancel_row(order_id, job_id):
    order = main.mongo.read_collection_one('orders', {'order_id': order_id})
    total = 0
    for r in range(len(order['rows'])):
        if order['rows'][r]['job_id'] == job_id:
            main.mongo.update_one('orders', {'order_id': order_id}, {'rows.{}.weight'.format(str(r)): 0}, '$set')
            main.mongo.update_one('orders', {'order_id': order_id}, {'rows.{}.length'.format(str(r)): '0'}, '$set')
            update_order_status('canceled', order_id, job_id)
        else:
            total += int(order['rows'][r]['weight'])
    main.mongo.update_one('orders', {'order_id': order_id}, {'info.total_weight': str(total)}, '$set')


def split_row():
    req_form = dict(main.request.form)
    if req_form:
        order_id = req_form['order_id']
        job_id = req_form['job_id']
        order, info = get_order_data(order_id, job_id)
        if order:
            order = order[0]
            if req_form['weight']:
                if int(req_form['weight']) >= order['weight']:
                    return '', 204
                new_weight = [int(req_form['weight']), order['weight'] - float(req_form['weight'])]
                quantity = int(int(order['quantity'])*float(req_form['weight'])/order['weight'])
                if quantity <= 0:
                    return '', 204
                quantity = [quantity, int(order['quantity'])-quantity]
            elif req_form['quantity']:
                if int(req_form['quantity']) >= order['quantity']:
                    return '', 204
                quantity = [int(req_form['quantity']), order['quantity'] - int(req_form['quantity'])]
                new_weight = [order['weight'] * quantity[0] / order['quantity']]
                if new_weight[0] <= 0:
                    return '', 204
                new_weight.append(order['weight'] - new_weight[0])
            else:
                return '', 204
            row_update = {'rows.$.quantity': str(quantity[0]), 'rows.$.weight': new_weight[0], 'info.rows': info['rows']+1}
            for k in order:
                if 'qnt_done' in k:
                    row_update['rows.$.'+k] = quantity[0]
                    order[k] = quantity[1]
            main.mongo.update_one('orders', {'order_id': order_id, 'rows': {"$elemMatch": {"job_id": {"$eq": job_id}}}},
                                row_update, '$set')
            order['job_id'] = str(info['rows']+1)
            order['weight'] = new_weight[1]
            order['quantity'] = quantity[1]
            main.mongo.update_one('orders', {'order_id': order_id}, {'rows': order}, '$push')
    return '', 204

