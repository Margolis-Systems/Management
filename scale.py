import functions
import main
from datetime import datetime, timedelta
from operator import itemgetter
import pages
import reports
import users


def main_page():
    permission = users.validate_user()
    if not permission:
        return users.logout()
    info = []
    perm = False
    req_form = dict(main.request.form)
    scale = ''
    if 'scale' in main.session.keys():  # Info entered
        scale = main.session['scale']
    if scale:
        # Current scaling info
        cur = main.session['scale']
        if 'site' not in cur:
            main.session['scale'] = {}
            return main.redirect('/scale')
        cur_weight = get_weight(cur['site'])
        cur_scale = main.mongo.read_collection_one('documents', {'doc_id': cur['doc_id']}, 'Scaling')
        if not cur_scale:
            cur_scale = []
        else:
            cur_scale = cur_scale['lines']
        # Add new line to report
        if 'product' in req_form:
            weight = calc_weight(req_form)
            if weight:
                new_line = weight
                new_line['description'] = ''
                if req_form['length']:
                    new_line['description'] += ' א:' + req_form['length']
                if req_form['diam']:
                    new_line['description'] += ' ק:' + req_form['diam']
                if req_form['quantity']:
                    new_line['description'] += ' כ:' + req_form['quantity']
                if not new_line['description']:
                    new_line['description'] = '---'
                new_line['barcode'] = ''
                doc = {'order_id': ''}
                if req_form['barcode']:
                    decode = reports.Images.decode_qr(req_form['barcode'])
                    if decode:
                        doc['order_id'] = decode['order_id']
                        new_line['barcode'] = '{} [ {} ] : {}KG'.format(decode['order_id'], decode['job_id'], decode['weight'])
                cur_scale.append(new_line)
                for item in cur:
                    if isinstance(cur[item], str):
                        doc[item] = cur[item]
                doc['lines'] = cur_scale
                main.mongo.upsert_collection_one('documents', {'doc_id': cur['doc_id']}, doc, 'Scaling')
                return main.redirect('/scale')
        product_types = main.mongo.read_collection_one('data_lists', {'name': 'product_types'}, 'Scaling')['data']
        info = [cur, product_types, cur_weight, cur_scale]
    elif req_form:  # Enter info
        cur = form_request(req_form)
        if cur:
            main.session['scale'] = cur
            main.session.modified = True
        return main.redirect('/scale')
    doc_list = []
    if permission > 50:
        perm = True
        doc_df = main.mongo.read_collection_df_sort('documents', 'doc_id', 'Scaling',
                                                    {'$where': "this.lines.length > 0"}, 50).to_dict('index')
        for doc in doc_df:
            doc_info = {}
            for item in doc_df[doc]:
                if item in ['doc_id', 'driver', 'vehicle_id']:
                    doc_info[item] = doc_df[doc][item]
            doc_info['scale_start'] = doc_df[doc]['lines'][0]['timestamp']
            doc_info['scale_end'] = doc_df[doc]['lines'][-1]['timestamp']
            doc_list.append(doc_info)
        doc_list.sort(key=itemgetter('doc_id'), reverse=True)
    sites = list(main.mongo.read_collection_one('data_lists', {'name': 'sites'}, 'Scaling')['data'].keys())
    return main.render_template('/scaling.html', info=info, user=main.session['username'], sites=sites, defaults={},
                                dictionary=pages.get_dictionary(), doc_list=doc_list, perm=perm)


def overview():
    permission = users.validate_user()
    if not permission:
        return users.logout()
    site = 'MIFAL'
    site_info = {'MIFAL': {'crr': '1', 'sensors': ['3c1b', '3c1c']}}
    _weights = get_weight(site_info[site])
    w1 = round(float(_weights[1]))
    w2 = round(float(_weights[3]))
    weights = [w1, w2, round(w1+w2)]
    return main.render_template('/scale_overview.html', weights=weights, dictionary=pages.get_dictionary(), site=site)


def get_weight(site_info):
    ret = ['', '0', '', '0']
    if 'crr' in site_info:
        crr, sensors = site_info['crr'], site_info['sensors']
        crr_data = main.mongo.read_collection_one('weights', db_name='Scaling',
                                                  query={'CRR_ID': crr, 'error': {'$exists': False}})
        for sensor in range(len(sensors)):
            if sensors[sensor] in crr_data:
                cur_sense = crr_data[sensors[sensor]]
                # Compare last update timestamp with current time - tolerance
                last_update = datetime.strptime(cur_sense['last_update'], '%d-%m-%Y_%H-%M-%S-%f')
                delta = datetime.now() - timedelta(seconds=30)
                # Validate the stability of the read values
                avg = sum(cur_sense['collector'][0]) / len(cur_sense['collector'][0])
                act = cur_sense['actual']
                tolerance = 0.03
                if not act * (1 - tolerance) < avg < act * (1 + tolerance):
                    ret[sensor * 2] = "Not stable"
                elif delta > last_update:
                    ret[sensor * 2] = "COMMUNICATION ERROR"
                else:
                    ret[sensor * 2] = last_update.strftime('%d/%m/%Y %H:%M:%S')
                    ret[sensor * 2 + 1] = round((act - float(cur_sense['tare'])) * 1000)
                    if ret[sensor * 2 + 1] < 0:
                        ret[sensor * 2 + 1] = 0
            else:
                print("No data from Sensor:", sensors[sensor])
    return ret


def form_request(req_form):
    scale_data = {'doc_id': gen_id()}
    for item in req_form:
        if item == 'site':
            site = main.mongo.read_collection_one('data_lists', db_name='Scaling',
                                                  query={'name': 'sites', 'data.' + req_form[item]: {'$exists': True}})
            if not site:
                return {}
            scale_data['site'] = site['data'][req_form['site']]
        elif 'BF2D@Hj ' in req_form[item]:
            decode = reports.Images.decode_qr(req_form[item])
            if decode:
                scale_data[item] = '{} [ {} ] : {}KG'.format(decode['order_id'], decode['job_id'], decode['weight'])
            else:
                return {}
        else:
            scale_data[item] = req_form[item].replace('MBC__', '')
    return scale_data


def gen_id():
    return functions.ts('s')


def print_scale():
    req = dict(main.request.values)
    if 'scale' not in main.session.keys():
        return
    elif not main.session['scale']:
        return
    info = main.session['scale']
    doc = main.mongo.read_collection_one('documents', {'doc_id': info['doc_id']}, db_name='Scaling')
    if not doc:
        return
    # Keep original template for multi pages
    template = main.mongo.read_collection_one('data_lists', {'name': 'bartender_dict'})['data']['scaling_report']
    # Add info
    template['start_ts'] = doc['lines'][0]['timestamp'][:19]
    template['end_ts'] = doc['lines'][-1]['timestamp'][:19]
    template['username'] = main.session['username']
    bartender_format = template.copy()
    for item in doc:
        if item in bartender_format:
            bartender_format[item] = doc[item]
    # Add lines
    last_line = 0
    total_weight = 0
    lines_qnt = len(doc['lines'])
    report_data = []
    i = 0
    # TODO: multi page
    while i == 0:
        new_line = bartender_format.copy()
        for line in range(lines_qnt):
            l_st = str(line + 1)
            new_line['line'+l_st] = l_st
            new_line['weight'+l_st] = doc['lines'][line]['weight']
            if 'description' in doc['lines'][line]:
                new_line['ts'+l_st] = doc['lines'][line]['description']
            else:
                new_line['ts'+l_st] = "---"
            new_line['product'+l_st] = doc['lines'][line]['product']
            total_weight += int(doc['lines'][line]['weight'])
            last_line = str(line + 2)
        if True:
            new_line['ts' + last_line] = "סהכ משקל:"
            new_line['product' + last_line] = str(total_weight)
            report_data.append(new_line)
            break
        report_data.append(new_line)
    reports.Bartender.bt_create_print_file(req['printer'], 'scaling_report', report_data)


def calc_weight(req):
    if not req['product']:
        req['product'] = 'ברזל'
    # print(req)
    # if not isinstance(req['weight1'], int) or not isinstance(req['weight2']):
    #     return {}
    try:
        cur_weight = [req['timestamp1'], int(req['weight1']), req['timestamp2'], int(req['weight2'])]
    except:
        return {}
    error_msg = ['Not stable', 'COMMUNICATION ERROR']
    if cur_weight[0] in error_msg or cur_weight[2] in error_msg:
        return {}
    ret = {'ts': datetime.now().strftime('%d-%m-%Y %H-%M-%S'), 'weight': 0}
    if cur_weight[1]:
        ret['weight'] += cur_weight[1]
        if not ret['ts']:
            ret['ts'] = cur_weight[0]
    if cur_weight[3]:
        ret['weight'] += cur_weight[3]
        if not ret['ts']:
            ret['ts'] = cur_weight[2]
        elif cur_weight[2] < ret['ts']:
            ret['ts'] = cur_weight[2]
    return {'timestamp': ret['ts'], 'weight': ret['weight'], 'product': req['product']}


def tare_scale(site_info):
    weights = main.mongo.read_collection_one('weights', db_name='Scaling',
                                             query={'CRR_ID': site_info['crr'], 'error': {'$exists': False}})
    tare = {}
    for sensor in site_info['sensors']:
        tare[sensor+'.tare'] = weights[sensor]['actual']
    main.mongo.update_one('weights', {'CRR_ID': site_info['crr']}, tare, '$set', db_name='Scaling', upsert=True)


def pick_crane():
    if main.request.form:
        if 'scale' in main.session.keys():
            site = main.mongo.read_collection_one('data_lists', db_name='Scaling',
                                                  query={'name': 'sites', 'data.' + main.request.form['site']:
                                                      {'$exists': True}})
            if site:
                main.session['scale']['site'] = site['data'][main.request.form['site']]
                main.session.modified = True
                return main.redirect('/scale')
    sites = list(main.mongo.read_collection_one('data_lists', {'name': 'sites'}, 'Scaling')['data'].keys())
    return main.render_template('pick_crane.html', sites=sites)


def delete_last():
    if 'scale' in main.session.keys():  # Info entered
        if main.session['scale']:
            doc_id = main.session['scale']['doc_id']
            main.mongo.update_one('documents', {'doc_id': doc_id}, {'lines': 1}, '$pop', db_name='Scaling')
    return main.redirect('/scale')


def scale_report():
    doc_id = list(main.request.values)[0]
    doc = main.mongo.read_collection_one('documents', {'doc_id': doc_id}, 'Scaling')
    main.session['scale'] = {'doc_id': doc_id}
    main.session.modified = True
    info = {}
    total_weight = 0
    show_in_info = ['order_id', 'costumer', 'driver', 'vehicle_id']
    for item in doc:
        if item in show_in_info:
            info[item] = doc[item]
    for line in doc['lines']:
        total_weight += float(line['weight'])
    return main.render_template('/scale_report.html', doc=doc['lines'], info=info, total=int(total_weight),
                                dictionary=pages.get_dictionary())


def delete_report_row(index=-1):
    permission = users.validate_user()
    if not permission:
        return users.logout()
    if index == -1:
        if len(list(main.request.values)) > 0:
            index = int(list(main.request.values)[0])
    doc_id = main.session['scale']['doc_id']
    doc = main.mongo.read_collection_one('documents', {'doc_id': doc_id}, 'Scaling')
    if doc:
        del doc['lines'][index]
        main.mongo.update_one('documents', {'doc_id': doc_id}, doc, '$set', db_name='Scaling')
    return '', 204
