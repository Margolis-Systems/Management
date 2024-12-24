import csv
import main


def reshet_csv_data(csv_dir):
    out = []
    mach_info = main.mongo.read_collection_one('machines', {'machine_id': 33})
    cur_order = ''
    idx = -1
    with open('{}/{}'.format(main.configs.csv_dir, csv_dir), 'r', newline='') as f:
        data = csv.reader(f, delimiter=';')
        for r in data:
            r[0] = csv_dir.replace('.csv', '')
            if r[3] != cur_order:
                cur_order = r[3]
                idx += 1
                out.append({'quantity': 1, 'diam1': r[7], 'diam2': r[8], 'bars_x': r[9], 'bars_y': r[10], 'step1': r[11],
                            'step2': r[12], 'length': r[13], 'width': r[14], 'Start_ts': '{} {}'.format(r[0], r[1]),
                            'description': '{}_{}'.format(csv_dir, idx), 'info.costumer_name': '', 'order_id': csv_dir, 'job_id': idx})
                out[idx].update(mach_info)
            else:
                out[idx]['quantity'] += 1
                out[idx]['Finished_ts'] = '{} {}'.format(r[0], r[1])
    for i in out:
        if i['diam1'].replace('.0', '') in main.configs.weights or i['diam1'].replace('.0', '') in main.configs.weights:
            i['unit_weight'] = round((float(i['length']) * float(i['bars_x']) * main.configs.weights[i['diam1'].replace('.0', '')] / 1000) +
                                     (float(i['width']) * float(i['bars_y']) * main.configs.weights[i['diam2'].replace('.0', '')] / 1000), 2)
        else:
            i['unit_weight'] = 0
        i['weight'] = i['unit_weight'] * i['quantity']
        main.mongo.update_one('production_log', {'description': i['description']}, i, '$set', upsert=True)
    return out
