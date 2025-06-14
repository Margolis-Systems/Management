import datetime
import main
import orders


def main_page():
    if 'func' in main.request.values:
        func = main.request.values['func']
        if func == 'new':
            doc = {'doc': {'id': gen_doc_id(), 'lines': [], 'total': 0}}
            if 'weights' in main.session:
                if 'selected' in main.session['weights']:
                    doc['selected'] = main.session['weights']['selected']
            update_user_session({})
            update_user_session(doc)
        elif func == 'tare':
            if 'weights' in main.session:
                if 'selected' in main.session['weights']:
                    site, sensor = get_site_sensor()
                    tare(site, sensor)
        elif func == 'tare0':  # todo: disable?
            if 'weights' in main.session:
                if 'selected' in main.session['weights']:
                    site, sensor = get_site_sensor()
                    tare(site, sensor, 0)
        elif func == 'select':
            update_user_session({'selected': main.request.values['sensor']})
        elif func == 'weight':
            if 'weights' in main.session:
                if 'selected' in main.session['weights']:
                    site, sensor = get_site_sensor()
                    weight = get_weights_data(site, sensor)
                    if weight['actual']-weight['tare'] <= 0:
                        return main.redirect('/weights')
                    doc = main.session['weights']['doc']
                    if 'total' not in doc:
                        doc['total'] = 0
                    doc['lines'].append({'ts': weight['ts'], 'gross': weight['actual'],
                                         'net': weight['actual']-weight['tare'], 'tare': weight['tare']})
                    doc['total'] += doc['lines'][-1]['net']
                    if 'product' in main.session['weights']:
                        doc['lines'][-1]['product'] = main.session['weights']['product']
                    update_user_session({'doc': doc, 'product': ''})
                    tare(site, sensor)
        elif func == 'remove':
            if 'weights' in main.session:
                if 'selected' in main.session['weights']:
                    site, sensor = get_site_sensor()
                    doc = main.session['weights']['doc']
                    if doc['lines']:
                        doc['total'] -= doc['lines'][-1]['net']
                        doc['lines'].pop()
                        if doc['lines']:
                            tare(site, sensor, doc['lines'][-1]['gross'])
                        else:
                            tare(site, sensor)
                        update_user_session({'doc': doc})
        elif func == 'print':
            if 'doc' in main.request.values:
                if main.request.values['doc']:
                    doc = main.mongo.read_collection_one('documents', {'doc.id': main.request.values['doc']}, 'Scaling')
                    if 'bon' in main.request.values:  # todo: maybe by user
                        return main.render_template('/weight/printb.html', doc=doc)
                    return main.render_template('/weight/print.html', doc=doc)
            return main.render_template('close_window.html')
        elif func == 'split':
            if 'weights' in main.session:
                if not main.request.values['weight'].isnumeric():
                    return main.redirect('/weights')
                doc = main.session['weights']['doc']
                idx = int(main.request.values['line'])
                weight = int(main.request.values['weight'])
                if len(doc['lines']) > idx:
                    new_line = doc['lines'][idx].copy()
                    doc['lines'][idx]['gross'] -= weight
                    doc['lines'][idx]['net'] -= weight
                    new_line['tare'] = doc['lines'][idx]['gross']
                    new_line['net'] = weight
                    doc['lines'].insert(idx+1, new_line)
                    update_user_session({'doc': doc})
        return main.redirect('/weights')
    data = {}
    drv_l = main.mongo.read_collection_one('data_lists', {'name': 'trucks_list'}, 'Scaling')['data']
    products_list = main.mongo.read_collection_one('data_lists', {'name': 'product_types'}, 'Scaling')['data']
    weights_data = get_weights_data()
    if main.request.form:
        req = dict(main.request.form)
        for item in req:
            if 'product' in item and item != 'product':
                if 'weights' in main.session:
                    if 'selected' in main.session['weights']:
                        doc = main.session['weights']['doc']
                        doc['lines'][int(item.replace('product', ''))]['type'] = req[item]
                        update_user_session({'doc': doc})
            elif item == 'order_id':
                data[item] = req[item]
                rows, info = orders.get_order_data(req[item])
                if info:
                    data['order_total'] = info['total_weight']
                    data['costumer'] = info['costumer_name']
                    data['site'] = info['costumer_site']
            elif item in ['driver', 'plate', 'costumer', 'site', 'product']:
                if req[item]:
                    data[item] = req[item]

        update_user_session(data)
    if 'weights' in main.session:
        data.update(dict(main.session['weights']))
        if 'doc' in data:
            if len(data['doc']['lines']) > 0:
                main.mongo.update_one('documents', {'doc.id': data['doc']['id']}, data, '$set', True, 'Scaling')
    else:
        return main.redirect('/weights?func=new')
    # if main.session['username'] == 'baruch':
    #     return main.render_template('weight/mobile.html', weights=weights_data, drv_l=drv_l, products_list=products_list, data=data)
    return main.render_template('weight/main.html', weights=weights_data, drv_l=drv_l, products_list=products_list, data=data)


def update_user_session(data):
    if 'weights' not in main.session or not data:
        main.session['weights'] = {}
    for k in data:
        main.session['weights'][k] = data[k]
    main.session.modified = True


def get_weights_data(site='', sensor=''):
    # todo: validate TS
    query = {'station_id': {'$exists': True}}
    if site:
        query['station_id'] = site
    temp = main.mongo.read_collection_list('weights', query, 'Scaling')
    if sensor:
        if ' | ' in sensor:
            sensor = sensor.split(' | ')[0]
        data = temp[0]
        if 'dual' in data:
            s1 = data[sensor]
            if 'tare' not in s1:
                s1['tare'] = 0
            s2 = data[data['dual'][sensor]]
            if 'tare' not in s2:
                s2['tare'] = 0
            data = {'actual': s1['actual'] + s2['actual'], 'tare': int(s1['tare']) + int(s2['tare'])}
        elif sensor in data:
            data = data[sensor]
            if 'tare' not in data:
                data['tare'] = 0
        else:
            return {}
    else:
        data = []
        for sen in temp:
            if 'dual' in sen:
                ignore = []
                for s in sen['dual']:
                    if s not in ignore:
                        ignore.extend([s, sen['dual'][s]])
                        name = '{} | {}'.format(s, sen['dual'][s])
                        comb = {name: {'actual': sen[s]['actual'] + sen[sen['dual'][s]]['actual'], 'tare': 0},
                                'station_id': sen['station_id']}
                        if 'tare' in sen[s]:
                            comb[name]['tare'] += int(sen[s]['tare'])
                        if 'tare' in sen[sen['dual'][s]]:
                            comb[name]['tare'] += int(sen[sen['dual'][s]]['tare'])
                        data.append(comb)
            else:
                data.append(sen)
    return data


def tare(site, sensor, val=None):
    cur = get_weights_data(site, sensor)
    if not cur:
        return
    if val is not None:
        cur_gross = val
    else:
        if 'actual' in cur and 'info' not in cur:
            cur_gross = cur['actual']
        else:
            return
    main.mongo.update_one('weights', {'station_id': site}, {'{}.tare'.format(sensor): cur_gross}, '$set', db_name='Scaling')


def gen_doc_id():
    return datetime.datetime.now().strftime('%Y%m%d%H%M%S')


def get_site_sensor():
    selected = main.session['weights']['selected'].split(' : ')
    site = selected[0]
    sensor = selected[1]
    return site, sensor


def weights_manual_page():
    if 'func' in main.request.values:
        func = main.request.values['func']
        if func == 'new':
            doc = {'doc': {'id': gen_doc_id(), 'lines': [], 'total': 0}}
            if 'weights' in main.session:
                if 'selected' in main.session['weights']:
                    doc['selected'] = main.session['weights']['selected']
            update_user_session({})
            update_user_session(doc)
        elif func == 'print':
            if 'doc' in main.request.values:
                if main.request.values['doc']:
                    doc = main.mongo.read_collection_one('documents', {'doc.id': main.request.values['doc']}, 'Scaling')
                    if 'bon' in main.request.values:  # todo: maybe by user
                        return main.render_template('/weight/printb.html', doc=doc)
                    return main.render_template('/weight/print.html', doc=doc)
            return main.render_template('close_window.html')
        elif func == 'split':
            if 'weights' in main.session:
                if not main.request.values['weight'].isnumeric():
                    return main.redirect('/weights')
                doc = main.session['weights']['doc']
                idx = int(main.request.values['line'])
                weight = int(main.request.values['weight'])
                if len(doc['lines']) > idx:
                    new_line = doc['lines'][idx].copy()
                    doc['lines'][idx]['gross'] -= weight
                    doc['lines'][idx]['net'] -= weight
                    new_line['tare'] = doc['lines'][idx]['gross']
                    new_line['net'] = weight
                    doc['lines'].insert(idx+1, new_line)
                    update_user_session({'doc': doc})
    data = {}
    drv_l = main.mongo.read_collection_one('data_lists', {'name': 'trucks_list'}, 'Scaling')['data']
    products_list = main.mongo.read_collection_one('data_lists', {'name': 'product_types'}, 'Scaling')['data']
    if main.request.form:
        req = dict(main.request.form)
        print(req)
    if 'weights' in main.session:
        data.update(dict(main.session['weights']))
        if 'doc' in data:
            if len(data['doc']['lines']) > 0:
                main.mongo.update_one('documents', {'doc.id': data['doc']['id']}, data, '$set', True, 'Scaling')
    else:
        return main.redirect('/weights_manual?func=new')
    return main.render_template('weight/manual.html', drv_l=drv_l, products_list=products_list, data=data)
