import orders
import csv
from functions import ts


def hashav_csv_read(file):
    ret = []
    with open(file, 'r', newline='') as f:
        csv_r = csv.reader(f)
        for r in csv_r:
            new = {'code': r[0], 'id': r[1], 'description': r[2]}
            ret.append(new)
    return ret


# todo: mongo
costumers = hashav_csv_read('lists\\לקוחות.csv')
items = hashav_csv_read('lists\\פריטים.csv')
header = ['doc_length', 'costumer_id', 'verify_id', 'doc_type', 'costumer_name', 'adr1', 'adr2', 'verify_id2',
          'date1', 'date2', 'agent', 'storage', 'details', 'white_storage', 'white_agent', 'white_pricing',
          'main_discount', 'nds', 'copies', 'curency', 'chnge_rate', 'item_id', 'quantity', 'price', 'item_curency',
          'discount', 'item_chnge_rate', 'item_description', 'unit', 'tax', 'sec_id', 'commision', 'packages',
          'no_nds', 'phone', 'date3', 'comment', 'verify_id3', 'pricing_code', 'exp_date', 'batch', 'index',
          'expired', 'printed_id', 'add_text', 'add_text2', 'add_text3', 'add_text4', 'add_text5', 'add_phone',
          'add_phone2', 'add_phone3', 'destrib_line', 'line_num', 'base_line_num', 'add_comment', 'add_comment2',
          'add_sum', 'add_sum2', 'murshe', 'tnua_id', 'email', 'refnum', 'file_title', 'file_trans', 'contact_name',
          'trans_price_code', 'sec_item_description', 'in_out_card', 'date4', 'tnua_items', 'tnua_storage',
          'curency_est', 'export_adr', 'export_comment', 'type', 'type_ptor', 'exchange_rate', 'add_date',
          'add_date2', 'add_num', 'add_num2', 'add_date_tnua', 'add_date2_tnua', 'add_num_tnua', 'add_num2_tnua']


def save_csv(data, file_name=''):
    if not file_name:
        file_name = 'c:\\hashav_test\\IMOVEIN_{}.csv'.format(ts('file_name'))
    with open(file_name, 'w', encoding='utf8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writerows(data)
    return file_name


def save_doc(data, file_name=''):
    if not file_name:
        file_name = 'R:\\REP\\api\\IMOVEIN_{}.doc'.format(ts('s'))
    with open(file_name, 'w', encoding='utf8', newline='') as f:
        for r in data:
            f.write(r)
    return file_name


def export_order(order_id, jobs=None):
    rows, info = orders.get_order_data(order_id)
    data = []
    for r in rows:
        if not jobs or r['job_id'] in jobs:
            # new = {'verify_id': r['order_id'], 'doc_type': 31, 'agent': 2, 'storage': 1, 'item_id': '100010', 'quantity': 100.00, }
            new = ''
            data.append(new)
    save_doc(data)

