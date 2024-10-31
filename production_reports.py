import main
from datetime import datetime
from operator import itemgetter


def report(query, detaile=True):
    machines_id = []
    machine_list = []
    report_data = []
    req_vals = dict(main.request.values)
    temp_report_data = list(main.mongo.read_collection_list('production_log', query))
    temp_report_data = sorted(temp_report_data, key=itemgetter('machine_id', 'Start_ts'))
    if temp_report_data:
        machine_id = temp_report_data[0]['machine_id']
        time0 = datetime.now() - datetime.now()
        doubles = {}
        total = {'weight': 0, 'quantity': 0, 'work_time': time0, 'lines': 0, 'ht_avg': 0}
        peripheral = {'weight': 0, 'quantity': 0, 'lines': 0, 'operator': 'מלאי חצר'}
        double_total = {'weight': 0, 'quantity': 0, 'lines': 0}
        machine_total = {'weight': 0, 'quantity': 0, 'machine_id': temp_report_data[0]['machine_id'],
                         'machine_name': temp_report_data[0]['machine_name'],
                         'username': temp_report_data[0]['username'], 'operator': temp_report_data[0]['operator'],
                         'work_time': time0, 'lines': 0, 'work_days': []}
        for i in range(len(temp_report_data)):
            line = temp_report_data[i]
            if line['info']['costumer_name'] in ['מלאי חצר']:
                peripheral['weight'] += float(line['weight']) / 1000
                peripheral['quantity'] += int(line['quantity'])
                peripheral['lines'] += 1
            if machine_total['machine_id'] in machines_id:
                machines_id.remove(machine_total['machine_id'])
            # todo: fix!!!
            # if line['machine_id'] in [34, 18]:
            #     if label_id produces
            #         double...
            if line['order_id'] not in doubles:
                doubles[line['order_id']] = [line['job_id']]
            elif line['job_id'] not in doubles[line['order_id']]:
                doubles[line['order_id']].append(line['job_id'])
            elif line['machine_id'] in [34, 17, 18, 1]:
                double_total['weight'] += float(line['weight']) / 1000
                double_total['quantity'] += int(line['quantity'])
                double_total['lines'] += 1
            line['weight'] = round(float(line['weight'] / 1000), 4)
            # todo: ------------------ ??????? -------------------
            if line['machine_id'] != machine_id:
                if machine_total['work_time'].total_seconds() > 0:
                    machine_total['ht_avg'] = round(
                        machine_total['weight'] / (machine_total['work_time'].total_seconds() / 3600), 2)
                else:
                    machine_total['ht_avg'] = 0
                for key in total:
                    total[key] += machine_total[key]
                machine_total['weight'] = round(machine_total['weight'], 2)
                machine_total['work_days'] = len(machine_total['work_days'])
                report_data.append(machine_total)
                machine_id = line['machine_id']
                machine_total = {'weight': 0, 'quantity': 0, 'machine_id': line['machine_id'],
                                 'machine_name': line['machine_name'],
                                 'username': line['username'], 'operator': line['operator'], 'work_time': time0,
                                 'lines': 0, 'work_days': []}
            line['work_time'] = datetime.strptime(line['Finished_ts'], '%Y-%m-%d %H:%M:%S') - datetime.strptime(
                line['Start_ts'], '%Y-%m-%d %H:%M:%S')
            if line['Start_ts'][:10] not in machine_total['work_days']:
                machine_total['work_days'].append(line['Start_ts'][:10])
            if machine_total['lines'] > 0:
                temp = datetime.strptime(line['Start_ts'], '%Y-%m-%d %H:%M:%S') - datetime.strptime(
                    temp_report_data[i - 1]['Finished_ts'], '%Y-%m-%d %H:%M:%S')
                if temp > line['work_time']:
                    line['work_time'] = temp
            if detaile:
                report_data.append(line)
            # todo: ----------------------------------------------
            machine_total['weight'] += float(line['weight'])
            machine_total['quantity'] += int(line['quantity'])
            machine_total['lines'] += 1
            if 'work_time' in line:
                machine_total['work_time'] += line['work_time']
        if machine_total['work_time'].total_seconds() > 0:
            machine_total['ht_avg'] = round(
                machine_total['weight'] / (machine_total['work_time'].total_seconds() / 3600), 2)
        else:
            machine_total['ht_avg'] = 0
        for key in total:
            total[key] += machine_total[key]
        machine_total['weight'] = round(machine_total['weight'], 2)
        machine_total['work_days'] = len(machine_total['work_days'])
        report_data.append(machine_total)
        empty_line = {'weight': 0, 'quantity': 0, 'machine_id': 'machine_id', 'machine_name': 'machine_name',
                      'username': 'username', 'operator': 'operator', 'work_time': 0, 'lines': 0}
        for _mid in machines_id:
            new_line = empty_line.copy()
            for m in machine_list:
                if m['machine_id'] == _mid:
                    for i in m:
                        new_line[i] = m[i]
                    break
            report_data.append(new_line)
        if 'machine_id' not in req_vals:
            total['operator'] = 'סה"כ לדו"ח:'
            total['weight'] = round(total['weight'], 2)
            del total['ht_avg']
            del total['work_time']
            # del total['']
            report_data.append(total)
            peripheral['weight'] = round(peripheral['weight'], 2)
            report_data.append(peripheral)
            double_total['operator'] = 'סה"כ שורות משותפות'
            double_total['weight'] = round(double_total['weight'], 2)
            report_data.append(double_total.copy())
            for key in double_total:
                if key == 'operator':
                    double_total[key] = 'סה"כ משקל בפועל'
                else:
                    double_total[key] = round(total[key] - double_total[key], 2)
            report_data.append(double_total)
    return report_data
