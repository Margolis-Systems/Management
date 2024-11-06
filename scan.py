import users
import main
import orders
import configs
import reports
import functions
from pages import get_dictionary


def scan():
    if not users.validate_user():
        return users.logout()
    order_id = ""
    job_id = ""
    msg = ""
    status = ""
    quantity = ''
    label_id = ''
    decode = {}
    operators = {}
    user = main.session['username']
    user_data = users.get_user_data()
    machine = main.mongo.read_collection_one('machines', {'username': user})
    req_form = dict(main.request.form)
    if 'user' in req_form:
        user = req_form['user']
    if not machine:
        msg = 'לא הוקצתה מכונה למפעיל'
        operators = main.mongo.read_collection_list('machines', {})
        print(operators)
    # ----------- Dual scan (start and stop) ------------------------
    order = main.mongo.read_collection_one('orders', {'rows': {'$elemMatch': {'status': 'Start',
                                           'status_updated_by': {'$regex': user}}}})
    if order:
        order_id = order['order_id']
        for r in order['rows']:
            if 'status_updated_by' in r:
                if r['status'] == 'Start' and user in r['status_updated_by']:
                    job_id = r['job_id']
    # ---------------------------------------------------------------
    if 'scan' in req_form.keys():
        decode = reports.Images.decode_qr(req_form['scan'])
        if 'order_id' in decode:
            order_id, job_id = decode['order_id'], decode['job_id']
        if 'weight' in decode:
            if decode['weight'].isnumeric():
                decode['weight'] = int(decode['weight'])
        if 'label_id' in decode:
            scanned = main.mongo.read_collection_one('scanned_labels', {'id': decode['label_id']})
            if scanned and user not in configs.oper_multi_scan:
                order_id = ''
                msg = '^Finished^'
            else:
                label_id = decode['label_id']
    elif 'order_id' in req_form.keys() and 'close' not in req_form.keys():
        order_id = req_form['order_id']
        job_id = req_form['job_id']
        status = req_form['status'].replace('order_status_', '')
        for spl in job_id.split(','):
            job, info = orders.get_order_data(order_id, job_id)
            if 'label_id' in req_form:
                scanned = main.mongo.read_collection_one('scanned_labels', {'id': req_form['label_id']})
                if scanned and user not in configs.oper_multi_scan:
                    continue
                elif 'status_updated_by' not in job:
                    pass
                    pass
                elif user in job['status_updated_by']:
                    order_id = ''
                    msg = '^Finished^'
                    break
            req_form['job_id'] = spl
            if 'quantity' in req_form:
                main.mongo.update_one('orders',
                                      {'order_id': order_id, 'rows': {"$elemMatch": {"job_id": {"$eq": job_id}}}},
                                      {'rows.$.qnt_done_'+user: int(req_form['quantity'])}, '$inc')
            else:
                main.mongo.update_one('orders',
                                      {'order_id': order_id, 'rows': {"$elemMatch": {"job_id": {"$eq": job_id}}}},
                                      {'rows.$.qnt_done_' + user: int(job[0]['quantity'])}, '$set')
            if not job:
                break
            qnt_done = 0
            job, info = orders.get_order_data(order_id, job_id)
            for k in job[0]:
                if 'qnt_done_' in k:
                    if job[0][k] > qnt_done:
                        qnt_done = job[0][k]
            main.mongo.update_one('orders',
                                  {'order_id': order_id, 'rows': {"$elemMatch": {"job_id": {"$eq": job_id}}}},
                                  {'rows.$.qnt_done': qnt_done}, '$set')
            rows, info = orders.get_order_data(order_id, job_id)
            if int(rows[0]['quantity']) <= rows[0]['qnt_done']:
                orders.update_order_status(status, order_id, job_id)
            production_log(req_form)
            if 'label_id' in req_form:
                if req_form['label_id']:
                    main.mongo.insert_collection_one('scanned_labels', {'id': req_form['label_id']})
        return main.redirect('/scan')
    if order_id:
        # todo: redo without integration?
        rows, info = orders.get_order_data(order_id)
        row = decode.copy()
        add_info = {'status': 'Production', 'type': 'integration', 'date_created': functions.ts(),
                    'status_updated_by': user}
        row.update(add_info)
        if not rows:
            # Create integration order
            info = {'costumer_name': '', 'costumer_id': '', 'created_by': user, 'costumer_site': '',
                    'date_created': functions.ts(), 'type': 'integration', 'status': 'Production'}
            order = {'order_id': order_id, 'info': info, 'rows': [row]}
            main.mongo.insert_collection_one('orders', order)
        else:
            info['status'] = info['status'].replace('order_status_', '')
            order = {'order_id': order_id, 'info': info, 'rows': rows}
            for r in order['rows']:
                if r['job_id'] == job_id:
                    row = r
        row['status'] = row['status'].replace('order_status_', '')
        if 'status' in row and 'operator' in user:
            if row['status'] in ['Production', 'Processed']:
                row['status'] = 'InProduction'
                orders.update_order_status('InProduction', order_id)
            if row['status'] in ['InProduction', 'PartlyDelivered']:
                status = 'Finished'
            elif user in configs.oper_multi_scan and "Finished" in row['status']:
                if 'status_updated_by' not in row:
                    status = 'Finished'
                elif user not in row['status_updated_by']:
                    status = 'Finished'
                else:
                    msg = row['status']
                    order_id = ''
            else:
                msg = row['status']
                order_id = ''
            quantity = int(row['quantity'])
            if 'status_updated_by' not in row:
                row['status_updated_by'] = ''
            if 'qnt_done_'+user in row:
                quantity = quantity - row['qnt_done_'+user]
            if 'pack_quantity' in row:
                if quantity >= int(row['pack_quantity']):
                    quantity = decode['quantity']
            if info['type'] == 'piles':
                quantity = 1
        elif row['status'] == 'Finished' and 'amasa' in user:
            status = 'Loaded'
        else:
            msg = row['status']
            order_id = ''
        if quantity == 0:
            msg = row['status']
            order_id = ''
    return main.render_template('/scan.html', order=order_id, job=job_id, msg=msg, status=status, machine=machine,
                                dictionary=get_dictionary(), user={'name': user_data['name'], 'lang': user_data['lang']},
                                quantity=quantity, label_id=label_id, operators=operators)


def production_log(form_data):
    log = form_data.copy()
    job_data, info = orders.get_order_data(log['order_id'], log['job_id'])
    keys_to_log = ['weight', 'length', 'quantity', 'diam']
    if 'user' in form_data:
        user = form_data['user']
        del log['user']
    else:
        user = main.session['username']
    machine_data = main.mongo.read_collection_one('machines', {'username': user})
    if not machine_data:
        return
    if 'quantity' in log:
        log['weight'] = job_data[0]['weight'] * int(log['quantity'])/int(job_data[0]['quantity'])
    else:
        log['quantity'] = job_data[0]['quantity']
        log['weight'] = job_data[0]['weight']
    for item in keys_to_log:
        if item in job_data[0] and item not in log:
            log[item] = job_data[0][item]
    log['info.costumer_name'] = info['costumer_name']
    log.update(machine_data)
    log['Start_ts'] = functions.ts()
    log['Finished_ts'] = functions.ts()
    if 'quantity' in log:
        if int(log['quantity']) < int(job_data[0]['quantity']):

            main.mongo.update_one('production_log', {'order_id': log['order_id'], 'job_id': log['job_id'],
                                                     'machine_id': machine_data['machine_id']}, {}, '$set')
    main.mongo.update_one('production_log', {'order_id': log['order_id'], 'job_id': log['job_id'],'machine_id': machine_data['machine_id'], 'Start_ts': log['Start_ts']}, log, '$set', upsert=True)
