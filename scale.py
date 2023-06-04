import functions
import main
from datetime import datetime

import pages
import reports
import users


def main_page():
    info = []
    req_form = dict(main.request.form)
    if 'scale' in main.session.keys():  # Info entered
        if main.session['scale']:
            # Current scaling info
            cur = main.session['scale']
            sensors = []
            for i in range(len(cur['lc'])):
                if cur['lc'][i]:
                    sensors.append(cur['site']['sensors'][i])
            cur_weight = get_weight(cur['site'])
            cur_scale = main.mongo.read_collection_one('documents', {'doc_id': cur['doc_id']}, 'Scaling')
            if not cur_scale:
                cur_scale = []
            else:
                cur_scale = cur_scale['lines']
            # Add new line to report
            if 'product' in req_form:
                if 'lc1' in req_form:
                    if req_form['lc1']:
                        cur['lc'][0] = True
                else:
                    cur['lc'][0] = False
                if 'lc2' in req_form:
                    if req_form['lc2']:
                        cur['lc'][1] = True
                else:
                    cur['lc'][1] = False
                weight = calc_weight(req_form, cur['site'])
                if weight:
                    new_line = weight
                    new_line['barcode'] = ''
                    doc = {'order_id': ''}
                    if req_form['barcode']:
                        decoded = reports.Images.decode_qr(req_form['barcode'])
                        if decoded:
                            doc['order_id'] = decoded['order_id']
                            new_line['barcode'] = 'Order: ' + decoded['order_id'] + '   Job: ' + decoded['job_id']
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
        return main.redirect('/scale')
    sites = list(main.mongo.read_collection_one('data_lists', {'name': 'sites'}, 'Scaling')['data'].keys())  # ['MIGRASH', 'MIFAL']
    return main.render_template('/scaling.html', info=info, user=main.session['username'],
                                sites=sites, defaults={'site': 'MIGRASH'},
                                dictionary=pages.get_dictionary(main.session['username']))


def get_weight(site_info):
    crr, sensors = site_info['crr'], site_info['sensors']
    crr_data = main.mongo.read_collection_one('weights', db_name='Scaling',
                                              query={'CRR_ID': crr, 'error': {'$exists': False}})
    ret = ['', '', '', '']
    for sensor in range(len(sensors)):
        if sensors[sensor] in crr_data:
            cur_sense = crr_data[sensors[sensor]]
            avg = sum(cur_sense['collector'][0]) / len(cur_sense['collector'][0])
            act = cur_sense['actual']
            tolerance = 0.03
            if not act * (1 - tolerance) < avg < act * (1 + tolerance):
                ret[sensor] = "ERROR"
            else:
                ret[sensor * 2] = datetime.strptime(cur_sense['last_update'], '%d-%m-%Y_%H-%M-%S-%f').strftime('%d/%m/%Y %H:%M:%S')
                ret[sensor * 2 + 1] = round((act - float(cur_sense['tare'])) * 1000)
                if ret[sensor * 2 + 1] < 0:
                    ret[sensor * 2 + 1] = 0
        else:
            print("No data from Sensor:", sensors[sensor])
    return ret


def form_request(req_form):
    scale_data = {'doc_id': gen_id(), 'lc': [False, False]}
    for item in req_form:
        if item == 'site':
            site = main.mongo.read_collection_one('data_lists', db_name='Scaling',
                                                  query={'name': 'sites', 'data.' + req_form[item]: {'$exists': True}})
            if not site:
                return {}
            scale_data['site'] = site['data'][req_form['site']]
            for sensor in range(len(site['data'][req_form['site']]['sensors'])):
                scale_data['lc'][sensor] = True
        elif 'BF2D@Hj ' in req_form[item]:
            order_id = reports.Images.decode_qr(req_form[item])['order_id']
            order_info = main.mongo.read_collection_one('orders',
                                                        {'order_id': order_id, 'info': {'$exists': True}})['info']
            if item in order_info:
                scale_data[item] = order_info[item]
            else:
                return {}
        else:
            scale_data[item] = req_form[item].replace('MBC__', '')
    return scale_data


def gen_id():
    return functions.ts('s')


def print_scale():
    if 'scale' not in main.session.keys():
        return
    elif not main.session['scale']:
        return
    info = main.session['scale']
    doc = main.mongo.read_collection_one('documents', {'doc_id': info['doc_id']}, db_name='Scaling')
    if not doc:
        return
    # Keep original template for multi pages todo: TBD
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
    for line in range(len(doc['lines'])):
        l_st = str(line + 1)
        bartender_format['line'+l_st] = l_st
        bartender_format['weight'+l_st] = doc['lines'][line]['weight']
        bartender_format['ts'+l_st] = "---"  # doc['lines'][line]['timestamp']  # TODO: gen description
        bartender_format['product'+l_st] = doc['lines'][line]['product']
    reports.Bartender.bt_create_print_file('Page4', 'scaling_report', [bartender_format])


def calc_weight(req, site_info):
    cur_weight = get_weight(site_info)
    ret = {'ts': '', 'weight': 0}
    if 'lc1' in req:
        ret['weight'] += cur_weight[1]
        if not ret['ts']:
            ret['ts'] = cur_weight[0]
    if 'lc2' in req:
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
