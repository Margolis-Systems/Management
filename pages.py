import functions
import main
import users
import reports
import orders
import os


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
            for _ang in range(1, len(shape_data['angels']) + 1):
                dtd_order.append('ang_'+str(_ang))
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
                defaults = {'edges': job_data['shape_data'], 'ang': job_data['shape_ang']}
    return main.render_template('/shape_editor.html', shapes=shapes, shape_data=shape_data, defaults=defaults,
                                datatodisp=datatodisp, dtd_order=dtd_order)


def choose_printer():
    copies = 1
    if main.request.form:
        disable_weight = False
        if 'disable_weight' in main.request.form:
            disable_weight = True
        printer = main.request.form['printer']
        print_type = main.request.form['print_type']
        if 'sub_type' in main.request.form.keys():
            if main.request.form['sub_type']:
                print_type = main.request.form['sub_type']
        if 'copies' in main.request.form.keys():
            if main.request.form['copies']:
                copies = int(main.request.form['copies'])
        for r in range(copies):
            reports.Bartender.net_print(main.session['order_id'], printer, print_type, disable_weight)
        if main.request.form['print_type'] == 'label':
            orders.update_order_status('Processed', main.session['order_id'])
        return '', 204
    else:
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
                                defaults={'printer': default_printer, 'copies': copies}, sub_type=sub_type)


def scan():
    if not users.validate_user():
        return users.logout()
    order_id = ""
    job_id = ""
    order = main.mongo.read_collection_one('orders', {'status': 'Start', 'status_updated_by': main.session['username']})
    if order:
        order_id = order['order_id']
        job_id = order['job_id']
    msg = ""
    status = ""
    if 'scan' in main.request.form.keys():
        decode = reports.Images.decode_qr(main.request.form['scan'])
        order_id, job_id = decode['order_id'], decode['job_id']
    elif 'order_id' in main.request.form.keys() and 'close' not in main.request.form.keys():
        order_id = main.request.form['order_id']
        job_id = main.request.form['job_id']
        orders.update_order_status(main.request.form['status'], order_id, job_id)
        return main.redirect('/scan')
    if order_id:
        job = main.mongo.read_collection_one(main.configs.orders_collection, {'order_id': order_id, 'job_id': job_id})
        if job:
            if job['status'] == 'Production':
                status = "Start"
            elif job['status'] == "Start":
                status = "Finished"
            else:
                msg = job['status']
                order_id = ''
        else:
            msg = "Not found"
    return main.render_template('/scan.html', order=order_id, job=job_id, msg=msg, status=status)


def get_defaults():
    return {}


def order_files():
    order_id = main.session['order_id']
    msg = ""
    if main.request.method == 'POST':
        try:
            attach_dir = os.getcwd() + '\\attachments\\orders'
            f = main.request.files['file']
            # file_dir = os.path.join(main.app.instance_path, attach_dir, order_id)
            file_dir = os.path.join(attach_dir, order_id)
            if not os.path.exists(file_dir):
                os.makedirs(file_dir)
            # file_name = main.secure_filename(f.filename)
            file_name = f.filename
            file = os.path.join(file_dir, file_name)
            if os.path.exists(file):
                file = functions.uniquify(file)
            f.save(file)
            doc = {'name': file_name, 'timestamp': functions.ts(), 'user': main.session['username'], 'id': gen_file_id(),
                   'description': main.request.form['description'], 'link': file, 'order_id': order_id}
            main.mongo.insert_collection_one('attachments', doc)
            return main.redirect('/order_files')
        except Exception as e:
            # print(e)
            msg = "Internal Error"
    files = main.mongo.read_collection_list('attachments', {'order_id': order_id})
    return main.render_template('/order_files.html', files=files, message=msg)


def download_attachment():
    attach_dir = os.getcwd() + '\\attachments\\orders'
    order_id = main.session['order_id']
    file_name = main.mongo.read_collection_one('attachments', {'id': list(main.request.values)[0]})['name']
    file = os.path.join(attach_dir, order_id, file_name)
    return main.send_from_directory(os.path.dirname(file), os.path.basename(file), as_attachment=True)


def gen_file_id():
    new_id = 1
    last_attach = main.mongo.read_collection_last('attachments', 'id')
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
            query = {'info.date_created': {'$gte': report_date['from'], '$lte': report_date['to']+'00:00:00'}}
            if 'client_name' in req_vals.keys():
                query['client_name'] = req_vals['client_name']
            if 'username' in req_vals.keys():
                query['username'] = req_vals['username']
            _report_data = list(main.mongo.read_collection_list('orders', query))
            if _report_data:
                for item in _report_data:
                    item['info']['total_weight'] = int(item['info']['total_weight'])
                    report_data.append(item['info'])
    # Print
    if 'print' in req_vals:
        title = req_vals['print']
        reports.Docs.print_doc(title, report_data)
    return main.render_template('/reports.html', date=report_date, report_data=report_data, report=report)


def machines_page():
    # todo: complete
    return main.render_template('machines.html', machine_list=[1,2,3,4], users_list=['a','b','c'])
