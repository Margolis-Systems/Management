import base64
import json

import configs
import functions
import main
import production_reports
import users
import reports
import orders
import os
from datetime import datetime


def get_dictionary():
    username = main.session['username']
    main_dir = "C:\\Server\\"
    if not os.path.exists(main_dir):
        main_dir = "C:\\projects\\Tzomet\\Management\\"

    with open(main_dir+'lists\\dictionary.json', encoding='utf-8') as dicts_file:
        all_dicts = json.load(dicts_file)
    lang = main.mongo.read_collection_one('users', {'name': username})['lang']
    dictionary = all_dicts[lang]
    dictionary.update(all_dicts['default'])
    return dictionary


def gen_patterns(order_type='regular'):
    from collections import OrderedDict
    lists = {}
    patterns = {}
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
        # diam = ['5.5', '6.5', '7.5', '8', '10', '12', '14', '16', '18']
        diam = list(main.configs.weights.keys())
        diam.sort(key=lambda k: float(k))
        cat_num = []
        rebar_type = []
        rebar_type.sort()
        cat_num.sort()
        patterns = {'pitch_x': '|'.join(rebar_type), 'pitch_y': '|'.join(rebar_type), 'diam_x': '|'.join(diam),
                    'diam_y': '|'.join(diam), 'mkt': '|'.join(cat_num)}
        lists = {'pitch_x': rebar_type, 'pitch_y': rebar_type, 'diam_x': diam, 'diam_y': diam,
                 'mkt': list(main.configs.rebar_catalog.keys())}
    elif order_type == 'girders':
        lists['mkt'] = list(main.configs.girders_catalog.keys())
    elif order_type == 'piles':
        diam = list(main.configs.weights.keys())
        diam.sort(key=lambda k: float(k))
        bend = ['חוץ', 'פנים', 'שושנה', 'טבעת חיזוק']
        lists = {'spiral_diam': diam, 'bend': bend}
        patterns = {'spiral_diam': '|'.join(diam), 'bend': '|'.join(bend)}
    else:
        shapes_list = main.configs.shapes.keys()
        diam = list(main.configs.weights.keys())
        diam.sort(key=lambda k: float(k))
        bar_type = ['מצולע', 'חלק']
        lists = {'diam': diam, 'shape': shapes_list, 'bar_type': bar_type}
        patterns = {'diam': '|'.join(diam), 'shape': '|'.join(shapes_list), 'bar_type': '|'.join(bar_type)}
    return lists, patterns


def shape_editor():
    shape_data = {}
    shapes = {}
    datatodisp = {}
    dtd_order = []
    diam_limits = {}
    defaults = {'edges': [], 'ang': []}
    if main.request.form:
        shape_data = {'edges': 0, 'shape': main.request.form['shape_data'], 'tot_len': 0, 'shape_data': main.request.form['1']}
        if main.request.form['shape_data'] == '332':
            shape_data['tot_len'] = int(main.request.form['1']) * 3.25
        elif main.request.form['shape_data'] == '331':
            shape_data['tot_len'] = int(main.request.form['1']) * 3.14 + 30
        elif main.request.form['shape_data'] == '330':
            shape_data['tot_len'] = int(main.request.form['1']) * 3.14 / 2 + 20
        elif main.request.form['shape_data'] == '340':
            shape_data['tot_len'] = int(main.request.form['1'])
            shape_data['shape_data'] = '{},{}'.format(main.request.form['1'],main.request.form['2'])
        else:
            for item in range(1, int(main.configs.shapes[shape_data['shape']]['edges']) + 1):
                shape_data['tot_len'] += int(float(main.request.form[str(item)]))
                if item > 1:
                    shape_data['shape_data'] += ',' + main.request.form[str(item)]
    else:
        req_vals = dict(main.request.values)
        if 'shape' in req_vals:
            if req_vals['shape'] in main.configs.shapes:
                shape_conf = main.configs.shapes[req_vals['shape']]
                if 'ang' in shape_conf:
                    ang = shape_conf['ang']
                else:
                    ang = []
                shape_data = {'shape': req_vals['shape'], 'edges': list(range(1, shape_conf['edges'] + 1)),
                              'img_plot': "/static/images/shapes/" + req_vals['shape'] + ".png",
                              'angels': ang}
                defaults['ang'] = ang
                dtd_order = list(map(str, shape_data['edges']))
                for item in dtd_order:
                    datatodisp[item] = 1
                if 'diam' in req_vals:
                    diam_limits = {req_vals['diam']: 'test'}
            else:
                shape_data = {'edges': 0}
        else:
            for shape in main.configs.shapes:
                if os.path.exists("static\\images\\shapes\\" + shape + ".png"):  # C:\\server\\
                    shapes[shape] = {'description': main.configs.shapes[shape]['description'],
                                     'edges': main.configs.shapes[shape]['edges']}

    if 'job_id' in main.session:
        if main.session['job_id']:
            job_data, info = orders.get_order_data(main.session['order_id'], main.session['job_id'])
            if job_data:
                job_data = job_data[0]
                if 'shape_data' in job_data:
                    defaults = {'edges': job_data['shape_data'], 'ang': job_data['shape_ang']}
    return main.render_template('/shape_editor.html', shapes=shapes, shape_data=shape_data, defaults=defaults,
                                datatodisp=datatodisp, dtd_order=dtd_order, diam_limits=diam_limits)


def choose_printer():
    copies = 1
    order = main.mongo.read_collection_one('orders', {'order_id': main.session['order_id']})
    if main.request.form:
        req_form = dict(main.request.form)
        printer = req_form['printer']
        if 'copies' in req_form:
            if req_form['copies']:
                copies = int(req_form['copies'])
        # ------------------------------------------
        split = ''
        select_jobs = []
        if 'split' in req_form:
            split = req_form['split']
        if 'print_select' in req_form:
            try:
                if '-' in req_form['print_select']:
                    temp = req_form['print_select'].split('-')
                    select_jobs = list(range(int(temp[0]), int(temp[1])+1))
                elif ',' in req_form['print_select']:
                    temp = req_form['print_select'].split(',')
                    for t in temp:
                        select_jobs.append(int(t))
                elif req_form['print_select'].isdigit():
                    select_jobs = [req_form['print_select']]
            except:
                select_jobs = []
            select_jobs = [str(x) for x in select_jobs]
        disable_weight = False
        if 'disable_weight' in req_form:
            disable_weight = True
        print_type = req_form['print_type']
        if 'sub_type' in req_form:
            if req_form['sub_type']:
                print_type = req_form['sub_type']
        # ------------------------------------------------
        if print_type == 'pdf':
            return reports.Print.print_template(order['order_id'], disable_weight, select_jobs=select_jobs, split=split)
        elif print_type == 'label':
            orders.update_order_status('Processed', main.session['order_id'])
        for r in range(copies):
            # If not asked for specific split, print all parts
            if not split:
                _split = []
                if order:
                    for ro in order['rows']:
                        if 'order_split' in ro and (ro['order_id'] in select_jobs or not select_jobs):
                            if str(ro['order_split']) not in _split:
                                _split.append(str(ro['order_split']))
                if _split:
                    for i in range(len(_split)):
                        reports.Bartender.net_print(main.session['order_id'], printer, print_type, disable_weight,
                                                        select_jobs=select_jobs, split=_split[i])
                else:
                    reports.Bartender.net_print(main.session['order_id'], printer, print_type, disable_weight,
                                                    select_jobs=select_jobs)

            else:
                reports.Bartender.net_print(main.session['order_id'], printer, print_type, disable_weight,
                                                select_jobs=select_jobs, split=split)
        return '', 204
    else:
        split = []
        if order:
            for r in order['rows']:
                if 'order_split' in r:
                    if str(r['order_split']) not in split:
                        split.append(str(r['order_split']))
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
        if print_type.replace('test_', '') in main.configs.printers:
            printer_list = main.configs.printers[print_type.replace('test_', '')]
        else:
            printer_list = []
    return main.render_template('/choose_printer.html', printer_list=printer_list, print_type=print_type,
                                defaults={'printer': default_printer, 'copies': copies}, sub_type=sub_type, split=split
                                , pat='|'.join(split))


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
            if main.request.files:
                if save_file(order_id, main.request.files['file'], description):
                    return main.redirect('/order_files')
                return '', 204
        except Exception as e:
            print('order_files', e)
            msg = "Internal Error"
    ord_ids = [order_id]
    rows, info = orders.get_order_data(order_id)
    if 'linked_orders' in info:
        for li in info['linked_orders']:
            if li['order_id'] not in ord_ids:
                ord_ids.append(li['order_id'])
    files = main.mongo.read_collection_list('attachments', {'order_id': {'$in': ord_ids}})
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
        if not temp:
            return False
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
    return True


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
    req_vals = dict(main.request.values)
    req_form = dict(main.request.form)
    # Report type handle
    report = ''
    if 'report' in req_vals.keys():
        report = req_vals['report']
    if 'report' in req_form:
        del req_form['report']
    weight_multp = 1000
    report_date = {'from': functions.ts('html_date'), 'to': functions.ts('html_date')}
    data_to_display = ['order_id', 'created_by', 'date_created', 'date_delivery', 'type', 'costumer_name',
                       'costumer_id', 'costumer_site', 'status', 'total_weight', 'rows']
    mid = ''
    report_data = []
    statuses = list(configs.order_statuses)
    ord_types = list(configs.new_order_types)
    if report == 'production':
        statuses = []
        query = {'Start_ts': {'$gte': report_date['from'], '$lte': report_date['to'] + ' 23:59:59'}}
        detailed = ['machine_id', 'machine_name', 'username', 'operator', 'weight', 'quantity', 'length', 'diam',
                    'Start_ts', 'Finished_ts', 'order_id', 'job_id', 'work_time']
        data_to_display = ['machine_id', 'machine_name', 'operator', 'lines', 'quantity', 'weight',
                           'work_time', 'ht_avg']
        if 'machine_id' in req_vals:
            if 'plant' in query:
                del query['plant']
            mid = req_vals['machine_id']
            query['machine_id'] = int(mid)
            data_to_display = detailed
        if req_form:
            for k in req_form:
                if k in ['date_from', 'date_to']:
                    query['Start_ts'] = {'$gte': req_form['date_from'] + ' 00:00:00',
                                         '$lte': req_form['date_to'] + ' 23:59:59'}
                    report_date = {'from': req_form['date_from'], 'to': req_form['date_to']}
                elif 'plant' in k:
                    if 'plant' not in query:
                        query['plant'] = {'$in': []}
                    query['plant']['$in'].append(req_form[k])
            if 'plant' in query:
                if 'ראשי' in query['plant']['$in']:
                    query['plant']['$in'].append('רומן')
        report_data = production_reports.report(query)
    elif report == 'month_prod':
        statuses = []
        today = functions.ts('html_date')
        if req_form:
            if 'date_from' in req_form:
                today = req_form['date_from']
        report_date = {'from': today[:-2]+'01', 'to': today[:-2]+'31'}
        query = {'Start_ts': {'$gte': today[:-2]+'01', '$lte': today[:-2]+'31 23:59:59'}}
        if req_form:
            for k in req_form:
                if 'plant' in k:
                    if 'plant' not in query:
                        query['plant'] = {'$in': []}
                    query['plant']['$in'].append(req_form[k])
            if 'plant' in query:
                if 'ראשי' in query['plant']['$in']:
                    query['plant']['$in'].append('רומן')
        if 'plant' not in query:
            query['plant'] = {'$in': ['ראשי', 'רומן']}
        report_data = production_reports.report(query, detaile=False)
        report_data.insert(0, {'operator': 'דוח חודשי', 'machine_name': '---------', 'quantity': '---------', 'weight': '---------', 'order_id': '0'})
        report_data.append({'operator': 'דוח יומי', 'machine_name': '---------', 'quantity': '---------', 'weight': '---------', 'order_id': '0'})
        query['Start_ts'] = {'$gte': today+' 00:00:00', '$lte': today+' 23:59:59'}
        temp_report_data = production_reports.report(query, detaile=False)
        report_data.extend(temp_report_data)
        data_to_display = ['machine_id', 'machine_name', 'operator', 'quantity', 'weight',
                           'work_time', 'work_days', 'ht_avg']
    else:
        if 'report_query' in main.session and not report:
            query = main.session['report_query']
        else:
            query = {'info.status': {'$ne': 'canceled'}, 'info.type': {'$ne': 'integration'}, 'rows': {'$gt': {'size': 0}},
                     'info.costumer_name': {'$nin': ['טסטים \\ בדיקות', 'צומת ברזל', 'מלאי חצר']},
                     'info.date_created': {'$gte': report_date['from']+' 00:00:00', '$lte': report_date['to']+' 23:59:59'}}
        if report == 'status':
            report_date['from'] = ''
            query['info.status'] = 'Processed'
            query['info.type'] = 'regular'
            if 'info.date_created' in query:
                del query['info.date_created']
        elif report == 'open_orders':
            report_date['from'] = ''
            query['info.status'] = {'$nin': ['Delivered', 'canceled','PartlyDeliveredClosed']}
            if 'info.date_created' in query:
                del query['info.date_created']
        if req_form:
            for k in req_form:
                if k in ['date_from', 'date_to']:
                    query['info.date_created'] = {'$gte': req_form['date_from']+' 00:00:00', '$lte': req_form['date_to']+' 23:59:59'}
                    report_date = {'from': req_form['date_from'], 'to': req_form['date_to']}
                elif 'type' in k:
                    if 'info.type' in query:
                        if '$in' in query['info.type']:
                            query['info.type']['$in'].append(req_form[k])
                            continue
                    query['info.type'] = {'$in': [req_form[k]]}
                elif 'status' in k:
                    if 'info.status' in query:
                        if '$in' in query['info.status']:
                            query['info.status']['$in'].append(req_form[k])
                            if req_form[k] == 'Production':
                                query['info.status']['$in'].append('InProduction')
                            continue
                    query['info.status'] = {'$in': [req_form[k]]}
                    if req_form[k] == 'Production':
                        query['info.status']['$in'].append('InProduction')
                elif k == 'info.costumer_name':
                    if req_form[k]:
                        query[k] = {'$regex': req_form[k]}
                else:
                    if req_form[k]:
                        query[k] = req_form[k]
        main.session['report_query'] = query
        main.session.modified = True
        all_orders = list(main.mongo.read_collection_list('orders', query))
        # todo: sort_by client_name -> move last loop inside
        orders_data = []
        total_weight = {'global': 0, 'temp': 0}
        for order in all_orders:
            if 'order_id' in order['info']:
                del order['info']['order_id']
            new_row = {'order_id': order['order_id']}
            new_row.update(order['info'])
            if 'comment' in new_row:
                del new_row['comment']
            new_row['status'] = 'order_status_' + new_row['status']
            new_row['date_created'] = datetime.strptime(new_row['date_created'], '%Y-%m-%d %H:%M:%S')
            if 'rows' not in order:
                order['rows'] = []
            if 'total_weight' not in new_row:
                new_row['total_weight'] = 0
            total_weight['global'] += int(new_row['total_weight']) / weight_multp
            type_dict = {'regular': 'סהכ ברזל','R': 'סהכ ייצור רשת', 'K': 'סהכ ייצור קלונסאות', 'rebar': 'סהכ רשת', 'rebar_special': 'סהכ כוורת', 'piles': 'סהכ כלונסאות', 'integration':'אלי שליט', 'girders': 'סהכ מסבכונים'}
            ord_type = type_dict[new_row['type']]
            if ord_type not in total_weight:
                total_weight[ord_type] = int(new_row['total_weight']) / weight_multp
            else:
                total_weight[ord_type] += int(new_row['total_weight']) / weight_multp
            orders_data.append(new_row)
        orders_data.sort(key=lambda k: k['costumer_name'])
        total_weight['temp'] = 0
        template_row = {}
        if orders_data:
            last_client = orders_data[0]['costumer_name']
            for item in orders_data[0]:
                template_row[item] = ''
        template_row['costumer_name'] = 'סהכ ללקוח'
        for row in orders_data:
            row['total_weight'] = int(row['total_weight'])
            row['total_weight'] = round(row['total_weight'] / weight_multp, 2)
            if row['costumer_name'] == last_client:
                total_weight['temp'] += row['total_weight']
            else:
                template_row['total_weight'] = round(total_weight['temp'], 2)
                report_data.append(template_row.copy())
                total_weight['temp'] = row['total_weight']
                last_client = row['costumer_name']
            report_data.append(row)
        template_row['total_weight'] = round(total_weight['temp'], 2)
        report_data.append(template_row.copy())

        for weight in total_weight:
            if weight in ['global', 'temp']:
                continue
            template_row['total_weight'] = round(total_weight[weight], 2)
            template_row['costumer_name'] = weight
            report_data.append(template_row.copy())
        template_row['costumer_name'] = 'סהכ כללי'
        template_row['total_weight'] = round(total_weight['global'], 2)
        report_data.append(template_row.copy())
    return main.render_template('/reports.html', date=report_date, report_data=report_data, report=report, machine_id=mid,
                                dictionary=get_dictionary(), data_to_display=data_to_display, statuses=statuses, types=ord_types)


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
    scanner = main.mongo.read_collection_one('users', {'name': main.session['username']})
    if 'default_scanner' in scanner:
        main.mongo.upsert_collection_one('attachments', {'name': scanner['default_scanner']},
                                         {'name': scanner['default_scanner'], 'order_id': order_id})
    return '', 204


def delete_attachment():
    if not users.validate_user():
        return users.logout()
    main.mongo.delete_many('attachments', {'id': list(main.request.values)[0]})
    return order_files()


