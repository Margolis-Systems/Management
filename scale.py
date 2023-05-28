import functions
import main
from datetime import datetime
import reports
import users


def main_page():
    # cur_scale = [{'ts': functions.ts(), 'weight': '1.3T', 'product': 'ברזל', 'barcode': 'order: XX, line: XX'}]
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
            cur_weight = get_weight(cur['site']['crr'], sensors)
            cur_scale = main.mongo.read_collection_one('documents', {'id': cur['id']}, 'Scaling')
            if not cur_scale:
                cur_scale = []
            else:
                cur_scale = cur_scale['lines']
            # Add new line to report
            if 'product' in req_form:
                if 'lc1' in req_form:
                    if req_form['lc1']:
                        cur['lc'][0] = True
                if 'lc2' in req_form:
                    if req_form['lc2']:
                        cur['lc'][1] = True
                new_line = {}
                for item in req_form:
                    if 'lc' not in item:
                        new_line[item] = req_form[item]
                if req_form['barcode']:
                    decoded = reports.Images.decode_qr(req_form['barcode'])
                    if decoded:
                        new_line['barcode'] = 'Order: ' + decoded['order_id'] + '   Job: ' + decoded['job_id']
                cur_scale.append(new_line)
                doc = {'id': cur['id'], 'lines': cur_scale}
                main.mongo.upsert_collection_one('documents', {'id': cur['id']}, doc, 'Scaling')
            product_types = main.mongo.read_collection_one('data_lists', {'name': 'product_types'}, 'Scaling')['data']
            info = [cur, product_types, cur_weight, cur_scale]
    elif req_form:  # Enter info
        cur = form_request(req_form)
        if cur:
            main.session['scale'] = cur
        return main.redirect('/scale')
    return main.render_template('/scaling.html', info=info, user=main.session['username'],
                                sites=['ROMAN', 'MESH'], defaults={'site': 'ROMAN'})  # TODO: sites and defaults mongo


def get_weight(crr, sensors):
    crr_data = main.mongo.read_collection_one('weights', db_name='Scaling',
                                              query={'CRR_ID': crr, 'error': {'$exists': False}})
    total_weight = 0
    last_update = ""
    for sensor in sensors:
        if sensor in crr_data:
            total_weight += (float(crr_data[sensor]['actual']) - float(crr_data[sensor]['tare']))
            cur_ts = datetime.strptime(crr_data[sensor]['last_update'],
                                       '%d-%m-%Y_%H-%M-%S-%f').strftime('%d-%m-%Y %H:%M:%S')
            if not last_update or cur_ts < last_update:
                last_update = cur_ts
        else:
            print("No data from Sensor:", sensor)
    return str(total_weight), last_update


def form_request(req_form):
    scale_data = {'id': gen_id(), 'lc': [False, False]}
    for item in req_form:
        if item == 'site':
            site = main.mongo.read_collection_one('data_lists', db_name='Scaling',
                                                  query={'name': 'sites', 'data.' + req_form[item]: {'$exists': True}})
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
    return "1"
