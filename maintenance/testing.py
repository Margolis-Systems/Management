def new_order_row():
    order_id = main.session['order_id']
    if 'R' in order_id:
        return
    req_form_data = main.request.form
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
        for i in range(len(new_row['x_length'])):
            if new_row['x_pitch'][i] != "0":
                new_row['trim_x_end'] = str(float(new_row['trim_x_end']) +
                                            int(new_row['x_length'][i]) % int(new_row['x_pitch'][i])).replace('.0', '')
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
        new_row['weight'] = round(
            float(main.configs.rebar_catalog[new_row['mkt']]['unit_weight']) * float(new_row['quantity']), 1)
        if 'הזמנת_ייצור' in new_row:
            peripheral_orders([x_bars, y_bars], order_id, job_id)
    elif 'shape' in req_form_data:
        temp_order_data = main.mongo.read_collection_one('orders', {'order_id': order_id, 'job_id': "0"})
        if not temp_order_data:
            temp_order_data = main.mongo.read_collection_one('orders', {'order_id': order_id, 'job_id': job_id})
            new_row['shape_data'] = temp_order_data['shape_data']
        new_row['description'] = ""
        if float(new_row['diam']) < 7:
            new_row['bar_type'] = "חלק"
        if temp_order_data['shape_data'] == new_row['shape']:
            main.mongo.delete_many('orders', {'order_id': order_id, 'job_id': "0"})
            new_row['shape_data'] = []
            new_row['shape_ang'] = configs.shapes[new_row['shape']]['ang']
            for item in temp_order_data:
                if item.isdigit():
                    new_row['shape_data'].append(temp_order_data[item])
                elif 'ang_' in item:
                    new_row['shape_ang'][int(item.replace('ang_', '')) - 1] = temp_order_data[item]
        if new_row['shape'] == '332':
            new_row['weight'] = calc_weight(new_row['diam'], new_row['length'], 1)
        else:
            new_row['weight'] = calc_weight(new_row['diam'], new_row['length'], new_row['quantity'])
    else:
        return
    # Takes to manual input for weight
    if 'weight' in req_form_data:
        if req_form_data['weight'].replace('.', '').isdigit():
            new_row['weight'] = float(req_form_data['weight'])
    for item in new_row:
        if isinstance(new_row[item], int):
            new_row[item] = str(new_row[item])
    prev = main.mongo.read_collection_one('orders', {'order_id': new_row['order_id'], 'job_id': new_row['job_id']})
    if prev:
        for item in prev:
            if item not in new_row and item in ['shape_data', 'shape_ang']:
                new_row[item] = prev[item]
    main.mongo.upsert_collection_one('orders', {'order_id': new_row['order_id'], 'job_id': new_row['job_id']},
                                     new_row)  # , upsert=True
    update_orders_total_weight()
    req_vals = dict(main.request.values)
    if 'addbefore' in req_vals:
        return
        if req_vals['addbefore']:
            reorder_job_id(req_vals['addbefore'])