import base64

import functions
import main
import users
import reports
import orders
import os
import pandas as pd
import pages


def jobs_list(order_type='regular'):
    type_list = main.mongo.read_collection_df('orders', query={'info.type': order_type})
    type_list = type_list['order_id'].to_list()
    all_orders = main.mongo.read_collection_df('orders', query={'order_id': {'$in': type_list},
                                                                'job_id': {'$ne': "0", '$exists': True},
                                                                'status': {'$nin': ['NEW', 'Processed']}})
    info_list = list(main.mongo.read_collection_list('orders', {'order_id': {'$in': type_list}, 'info': {'$exists': True}}))
    cost_n = {}
    ord_type = {}
    for i in info_list:
        if i['order_id'] not in cost_n.keys():
            cost_n[i['order_id']] = i['info']['costumer_name']
            ord_type[i['order_id']] = i['info']['type']
    all_orders['costumer_name'] = all_orders['order_id'].map(cost_n)
    all_orders['type'] = all_orders['order_id'].map(ord_type)
    if all_orders.empty:
        return {}
    all_jobs = all_orders[all_orders['job_id'].notna()]
    sorter = {'Finished': 2, 'Production': 0, 'Start': 1}
    all_jobs['sorter'] = all_jobs['status'].map(sorter)
    all_jobs.sort_values(by=['sorter', 'date_created'], ascending=[True, False], inplace=True)
    all_jobs['status'] = 'order_status_' + all_jobs['status'].astype(str)
    columns = ['costumer_name', 'order_id', 'job_id', 'type', 'status', 'date_created', 'description']
    return all_jobs[columns].to_dict('records')


def get_dictionary(username):
    all_dicts = main.mongo.read_collection_one('data_lists', {'name': 'dictionary'})['data']
    lang = main.mongo.read_collection_one('users', {'name': username})['lang']
    dictionary = all_dicts[lang]
    return dictionary


def gen_patterns(order_type='regular'):
    if order_type == 'rebar':
        diam = []
        cat_num = []
        rebar_type = []
        for item in main.configs.rebar_catalog:
            if main.configs.rebar_catalog[item]['diam_x'] not in diam:
                diam.append(main.configs.rebar_catalog[item]['diam_x'])
            if item not in cat_num:
                cat_num.append(item)
            if main.configs.rebar_catalog[item]['x_pitch'] not in rebar_type:
                pitch = main.configs.rebar_catalog[item]['x_pitch'] + "X" + main.configs.rebar_catalog[item]['y_pitch']
                rebar_type.append(pitch)
        diam.sort()
        rebar_type.sort()
        cat_num.sort()
        patterns = {'pitch': '|'.join(rebar_type), 'diam': '|'.join(diam), 'mkt': '|'.join(cat_num)}
        lists = {'pitch': rebar_type, 'diam': diam, 'mkt': list(main.configs.rebar_catalog.keys())}
    elif order_type == 'rebar_special':
        diam = ['5.5', '6.5', '7.5', '8', '10', '12', '14', '16', '18']
        cat_num = []
        rebar_type = []
        rebar_type.sort()
        cat_num.sort()
        patterns = {'pitch_x': '|'.join(rebar_type), 'pitch_y': '|'.join(rebar_type), 'diam_x': '|'.join(diam),
                    'diam_y': '|'.join(diam), 'mkt': '|'.join(cat_num)}
        lists = {'pitch_x': rebar_type, 'pitch_y': rebar_type, 'diam_x': diam, 'diam_y': diam,
                 'mkt': list(main.configs.rebar_catalog.keys())}
    else:
        shapes_list = main.configs.shapes.keys()
        diam = list(main.configs.weights.keys())
        diam.sort(key=lambda k: float(k))
        bar_type = ['מצולע', 'חלק']
        lists = {'diam': diam, 'shape': shapes_list, 'bar_type': bar_type}
        patterns = {'diam': '|'.join(diam), 'shape': '|'.join(shapes_list), 'bar_type': '|'.join(bar_type)}
    return lists, patterns


def jobs():
    if not users.validate_user():
        return users.logout()
    order_type = "regular"
    if 'filter' in main.session['user_config']:
        if main.session['user_config']['filter']:
            order_type = main.session['user_config']['filter']
    dictionary = get_dictionary(main.session['username'])
    return main.render_template('/jobs.html', jobs=jobs_list(order_type), dictionary=dictionary)


def shape_editor():
    shape_data = {}
    shapes = {}
    datatodisp = {}
    dtd_order = []
    defaults = {'edges': [], 'ang': []}
    if main.request.form:
        shape_data = {'edges': 0, 'shape': main.request.form['shape_data'], 'tot_len': 0}
        if main.request.form['shape_data'] != '332':
            for item in range(1, int(main.configs.shapes[shape_data['shape']]['edges']) + 1):
                shape_data['tot_len'] += int(main.request.form[str(item)])
        else:
            if 'x' in main.request.form['2'] or 'X' in main.request.form['2']:
                loops = main.request.form['2'].replace('X','x')
                loops = loops.split('x')
                tot_l = 0
                for _l in loops:
                    if tot_l == 0:
                        tot_l += int(_l)
                    else:
                        tot_l *= int(_l)
            else:
                tot_l = int(main.request.form['2'])
            shape_data['tot_len'] = int(main.request.form['1']) * tot_l * 3.25
        orders.new_order_row()
    else:
        req_vals = list(main.request.values)
        if len(req_vals) > 0:
            if 'ang' in main.configs.shapes[req_vals[0]]:
                ang = main.configs.shapes[req_vals[0]]['ang']
            else:
                ang = []
            shape_data = {'shape': req_vals[0], 'edges': list(range(1, main.configs.shapes[req_vals[0]]['edges'] + 1)),
                          'img_plot': "/static/images/shapes/" + req_vals[0] + ".png",
                          'angels': ang}
            defaults['ang'] = ang
            dtd_order = list(map(str, shape_data['edges']))
            # for _ang in range(1, len(shape_data['angels']) + 1):
            #     dtd_order.append('ang_'+str(_ang))
            for item in dtd_order:
                datatodisp[item] = 1
        else:
            for shape in main.configs.shapes:
                if os.path.exists("static\\images\\shapes\\" + shape + ".png"):  # C:\\server\\
                    shapes[shape] = {'description': main.configs.shapes[shape]['description'],
                                     'edges': main.configs.shapes[shape]['edges']}
    if 'job_id' in main.session:
        if main.session['job_id']:
            job_data = main.mongo.read_collection_one('orders', {'order_id': main.session['order_id'], 'job_id': main.session['job_id']})
            if job_data:
                if 'shape_data' in job_data:
                    defaults = {'edges': job_data['shape_data'], 'ang': job_data['shape_ang']}
    return main.render_template('/shape_editor.html', shapes=shapes, shape_data=shape_data, defaults=defaults,
                                datatodisp=datatodisp, dtd_order=dtd_order)


def choose_printer():
    copies = 1
    if main.request.form:
        req_form = dict(main.request.form)
        split = ''
        if 'split' in req_form:
            split = req_form['split']
        disable_weight = False
        if 'disable_weight' in req_form:
            disable_weight = True
        printer = req_form['printer']
        print_type = req_form['print_type']
        if 'sub_type' in req_form:
            if req_form['sub_type']:
                print_type = req_form['sub_type']
        if 'copies' in req_form:
            if req_form['copies']:
                copies = int(req_form['copies'])
        for r in range(copies):
            if not split:
                _split = main.mongo.read_uniq('orders', 'order_split', {'order_id': main.session['order_id']})
                if not _split:
                    _split.append('')
                for i in range(len(_split)):
                    reports.Bartender.net_print(main.session['order_id'], printer, print_type, disable_weight, split=_split[i])
            else:
                reports.Bartender.net_print(main.session['order_id'], printer, print_type, disable_weight, split=split)
        if main.request.form['print_type'] == 'label':
            orders.update_order_status('Processed', main.session['order_id'])
        return '', 204
    else:
        split = main.mongo.read_uniq('orders', 'order_split', {'order_id': main.session['order_id']})
        split = [str(s) for s in split]
        req_vals = list(main.request.values)
        sub_type = ''
        print_type = req_vals[0]
        if len(req_vals) > 1:
            sub_type = req_vals[1]
        default_printer = main.mongo.read_collection_one('users', {'name': main.session['username']})
        if default_printer:
            if print_type == 'page':
                copies = 2
            if print_type.replace('test_', '') in default_printer['default_printer']:
                default_printer = default_printer['default_printer'][print_type.replace('test_', '')]
            else:
                default_printer = ''
        else:
            default_printer = ''
        printer_list = main.configs.printers[print_type.replace('test_', '')]
    return main.render_template('/choose_printer.html', printer_list=printer_list, print_type=print_type,
                                defaults={'printer': default_printer, 'copies': copies}, sub_type=sub_type, split=split
                                , pat='|'.join(split))


def scan():
    if not users.validate_user():
        return users.logout()
    order_id = ""
    job_id = ""
    msg = ""
    status = ""
    decode = {}
    order = main.mongo.read_collection_one('orders', {'status': 'Start', 'status_updated_by': main.session['username']})
    if order:
        order_id = order['order_id']
        job_id = order['job_id']
    if 'scan' in main.request.form.keys():
        decode = reports.Images.decode_qr(main.request.form['scan'])
        decode['weight'] = int(decode['weight'])
        order_id, job_id = decode['order_id'], decode['job_id']
        # TODO: if username in machines collection
        # print(decode)
        # {'order_id': '22071206', 'job_id': '1', 'length': '4000', 'quantity': '200', 'weight': '710', 'diam': '12'}
    elif 'order_id' in main.request.form.keys() and 'close' not in main.request.form.keys():
        req_form = dict(main.request.form)
        order_id = req_form['order_id']
        job_id = req_form['job_id']
        status = main.request.form['status']
        orders.update_order_status(status, order_id, job_id)
        # TODO: report
        production_log(req_form)
        return main.redirect('/scan')
    if order_id:
        job = main.mongo.read_collection_one(main.configs.orders_collection, {'order_id': order_id, 'job_id': job_id})
        if not job and decode:
            integration_order = decode.copy()
            add_info = {'status': 'Production', 'type': 'integration', 'date_created': functions.ts(), 'status_updated_by': main.session['username']}
            integration_order.update(add_info)
            main.mongo.insert_collection_one('orders', integration_order)
            info = {'costumer_name': '', 'costumer_id': '', 'created_by': main.session['username'], 'costumer_site': '',
                    'date_created': functions.ts(), 'type': 'integration', 'status': 'Production'}
            main.mongo.upsert_collection_one('orders', {'order_id': order_id, 'info': {'$exists': True}},
                                             {'order_id': order_id, 'info': info})
            orders.update_orders_total_weight(order_id)
        job = main.mongo.read_collection_one(main.configs.orders_collection, {'order_id': order_id, 'job_id': job_id})
        if job['status'] == 'Production':
            status = "Start"
        elif job['status'] == "Start":
            status = "Finished"
        elif job['status'] == "NEW":
            orders.update_order_status('Production', order_id)
            status = "Start"
        else:
            msg = job['status']
            order_id = ''
        # else:
        #     msg = "Not found"
    return main.render_template('/scan.html', order=order_id, job=job_id, msg=msg, status=status, dictionary=get_dictionary(main.session['username']), user=main.session['username'])


def get_defaults():
    return {}


def order_files():
    description = ""
    no_upload = True
    if 'description' in main.request.form:
        description = main.request.form['description']
    if 'order_id' in dict(main.request.values):
        order_id = main.request.values['order_id']
    elif 'order_id' in main.session:
        order_id = main.session['order_id']
        no_upload = False
    else:
        order_id = '0'
    msg = ""
    if main.request.method == 'POST':
        try:
            save_file(order_id, main.request.files['file'], description)
            return main.redirect('/order_files')
        except Exception as e:
            print(e)
            msg = "Internal Error"
    files = main.mongo.read_collection_list('attachments', {'order_id': order_id})
    return main.render_template('/order_files.html', files=files, message=msg, order_id=order_id, no_upload=no_upload)


def save_file(order_id, f, description):
    file_name = f.filename
    if 'username' in main.session:
        username = main.session['username']
    else:
        username = file_name.replace('.pdf','')
    if order_id == '0':
        scanner = file_name.replace('.pdf', '') + '_scanner'
        temp = main.mongo.read_collection_one('attachments', {'name': scanner})
        order_id = temp['order_id']
        main.mongo.delete_many('attachments', {'name': scanner})
    attach_dir = os.getcwd() + '\\attachments\\orders'
    # f = main.request.files['file']
    file_dir = os.path.join(attach_dir, order_id)
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)
    # file_name = main.secure_filename(f.filename)
    file = os.path.join(file_dir, file_name)
    if os.path.exists(file):
        file = functions.uniquify(file)
    f.save(file)
    doc = {'name': file_name, 'timestamp': functions.ts(), 'user': username, 'id': gen_file_id(),
           'description': description, 'link': file, 'order_id': order_id}
    main.mongo.insert_collection_one('attachments', doc)


def download_attachment():
    req_vals = dict(main.request.values)
    file = main.mongo.read_collection_one('attachments', {'id': req_vals['doc_id']})['link']
    as_atach = True
    if 'show' in req_vals:
        as_atach = False
    return main.send_from_directory(os.path.dirname(file), os.path.basename(file), as_attachment=as_atach)


def gen_file_id():
    new_id = 1
    last_attach = main.mongo.read_collection_last('attachments', 'timestamp')
    if last_attach:
        new_id = int(last_attach['id']) + 1
    return str(new_id)


def reports_page():
    report_date = {'from': functions.ts('html_date'), 'to': functions.ts('html_date')}
    report_data = []
    report = ''
    req_vals = dict(main.request.values)
    # Report date handle
    if main.request.form:
        req_form = dict(main.request.form)
        for item in req_form:
            if 'date' in item:
                report_date['from'] = req_form['date_from']
                report_date['to'] = req_form['date_to']
    # Report type handle
    if 'report' in req_vals.keys():
        report = req_vals['report']
        if report == 'production':
            query = {'timestamp': {'$gte': report_date['from'], '$lte': report_date['to']}}
            if 'machine' in req_vals.keys():
                query['macine'] = req_vals['machine']
            if 'operator' in req_vals.keys():
                query['username'] = req_vals['operator']
            report_data = list(main.mongo.read_collection_list('machines', query))
        elif report == 'orders':
            query = {'info.date_created': {'$gte': report_date['from'], '$lte': report_date['to'] + '00:00:00'},
                     'info.status': {'$ne': 'canceled'},
                     'info.costumer_name': {'$nin': ['טסטים \\ בדיקות', 'צומת ברזל']}}
            if 'client_name' in req_vals.keys():
                query['client_name'] = req_vals['client_name']
            if 'username' in req_vals.keys():
                query['username'] = req_vals['username']
            # Read all orders data with Info, mean that it's not including order rows
            orders_df = main.mongo.read_collection_df('orders', query=query)
            if not orders_df.empty:
                # normalize json to df
                info_df = pd.json_normalize(orders_df['info'])
                info_df['date_created'] = pd.to_datetime(info_df['date_created'], format='%Y-%m-%d %H:%M:%S')
                # add order id from main df
                new_df = pd.concat([orders_df['order_id'], info_df], axis=1).fillna(0)
                new_df = new_df[['order_id','costumer_name','costumer_site','date_created','date_delivery','type','rows','total_weight','status']]
                new_df['status'] = 'order_status_' + new_df['status'].astype(str)
                new_df.sort_values('costumer_name',inplace=True)
                _report_data = new_df.to_dict('records')
                temp_total_weight = 0
                global_total_weight = new_df['total_weight'].sum()
                last_client = _report_data[0]['costumer_name']
                template_row = {}
                for item in _report_data[0]:
                    template_row[item] = ''
                template_row['costumer_name'] = 'סהכ ללקוח'
                for row in _report_data:
                    if row['costumer_name'] == last_client:
                        temp_total_weight += row['total_weight']
                    else:
                        template_row['total_weight'] = str(temp_total_weight)
                        report_data.append(template_row.copy())
                        temp_total_weight = row['total_weight']
                        last_client = row['costumer_name']
                    report_data.append(row)
                template_row['total_weight'] = temp_total_weight
                report_data.append(template_row.copy())
                template_row['costumer_name'] = 'סהכ כללי'
                template_row['total_weight'] = global_total_weight
                report_data.append(template_row.copy())
        elif report == 'status':
            query = {'info.status': 'Processed', 'info.type': 'regular',
                     'info.costumer_name': {'$nin': ['טסטים \ בדיקות', 'צומת ברזל']}}
            if 'client_name' in req_vals.keys():
                query['client_name'] = req_vals['client_name']
            if 'username' in req_vals.keys():
                query['username'] = req_vals['username']
            # Read all orders data with Info, mean that it's not including order rows
            orders_df = main.mongo.read_collection_df('orders', query=query)
            if not orders_df.empty:
                # normalize json to df
                info_df = pd.json_normalize(orders_df['info'])
                info_df['date_created'] = pd.to_datetime(info_df['date_created'], format='%Y-%m-%d %H:%M:%S')
                # add order id from main df
                new_df = pd.concat([orders_df['order_id'], info_df], axis=1).fillna(0)
                new_df = new_df[['order_id','costumer_name','costumer_site','date_created','date_delivery','type','rows','total_weight','status']]
                new_df['status'] = 'order_status_' + new_df['status'].astype(str)
                new_df.sort_values('costumer_name',inplace=True)
                _report_data = new_df.to_dict('records')
                temp_total_weight = 0
                global_total_weight = new_df['total_weight'].sum()
                last_client = _report_data[0]['costumer_name']
                template_row = {}
                for item in _report_data[0]:
                    template_row[item] = ''
                template_row['costumer_name'] = 'סהכ ללקוח'
                for row in _report_data:
                    if row['costumer_name'] == last_client:
                        temp_total_weight += row['total_weight']
                    else:
                        template_row['total_weight'] = temp_total_weight
                        report_data.append(template_row.copy())
                        temp_total_weight = row['total_weight']
                        last_client = row['costumer_name']
                    report_data.append(row)
                template_row['total_weight'] = temp_total_weight
                report_data.append(template_row.copy())
                template_row['costumer_name'] = 'סהכ כללי'
                template_row['total_weight'] = global_total_weight
                report_data.append(template_row.copy())
    return main.render_template('/reports.html', date=report_date, report_data=report_data, report=report, dictionary=pages.get_dictionary(main.session['username']))


def machines_page():
    req_form = dict(main.request.form)
    if 'machine' in req_form:
        main.mongo.update_one('machines', {'machine_id': int(req_form['machine'])},
                              {'username': req_form['username'], 'operator': req_form['operator_name']}, '$set', upsert=True)
        return main.redirect('/machines')
    elif 'machine_name' in req_form:
        machine_id = 1
        last_id = main.mongo.read_collection_one_sort('machines', 'machine_id',
                                                         query={'machine_id': {'$exists': True}}, limit=1)
        if machine_id:
            machine_id += last_id['machine_id']
        doc = {'machine_id': machine_id}
        doc.update(req_form)
        main.mongo.insert_collection_one('machines', doc)
        return main.redirect('/machines')
    users_list = []
    _users = main.mongo.read_collection_list('users', {'group': {'$lt': 5}})
    machine_list = main.mongo.read_collection_list('machines', {'machine_id': {'$exists': True}})
    for user in _users:
        users_list.append(user['name'])
    return main.render_template('machines.html', machine_list=machine_list, users_list=users_list, msg='')


def file_listener():
    if 'order_id' in dict(main.request.values):
        order_id = main.request.values['order_id']
    else:
        order_id = main.session['order_id']
    scanner = main.mongo.read_collection_one('users',{'name': main.session['username']})['default_scanner']
    main.mongo.upsert_collection_one('attachments', {'name': scanner}, {'name': scanner, 'order_id': order_id})
    return '', 204


def delete_attachment():
    if not users.validate_user():
        return users.logout()
    main.mongo.delete_many('attachments', {'id': list(main.request.values)[0]})
    return order_files()


def production_log(form_data):
    log = form_data.copy()
    log[form_data['status']+'_ts'] = functions.ts()
    job_data = main.mongo.read_collection_one('orders', {'order_id': log['order_id'], 'job_id': log['job_id']})
    keys_to_log = ['weight', 'length', 'quantity', 'diam']
    machine_data = {}
    for item in keys_to_log:
        if item in job_data:
            machine_data[item] = job_data[item]
        else:
            print('production log \nitem not found: ', item)
    log.update(machine_data)
    main.mongo.insert_collection_one('production_log', log)
