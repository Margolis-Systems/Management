import orders
import csv
import reports
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
drv_list = hashav_csv_read('lists\\נהגים.csv')
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
            f.write(r+'\n')
    return file_name


def export_order(order_id, client_id, driver, split=''):
    rows, info = orders.get_order_data(order_id, split=split)
    summary = reports.spec_sum(rows, info)
    data = []
    qnt_code = {'חישוק': 91258, 'חישוק מיוחד': 91259, 'אלמנט מיוחד חלק': 91269, 'מדרגה': 0, 'ספסלים': 91260}  # todo: מדרגה
    weight_code = {'חיתוך': 91255, 'כיפוף': 91256, 'ספירלים': 91267, 'תוספת_ברזל_עגול_עד_12_ממ': 91257,
                 'תוספת_ברזל_עגול_מעל_14_ממ': 91262, 'ברזל_ארוך': 1007, 'תוספת_ברזל_28_ממ_ומעלה': 91263}
    for r in summary:
        if r in weight_code:
            q = int(summary[r]['weight'])
            item_id = weight_code[r]
        else:
            q = int(summary[r]['qnt'])
            item_id = qnt_code[r]
        new = '{:5s} {:6s} 31 {:3d} 1 {:9d} {:9.2f}'.format(client_id, order_id, driver, item_id, q)
        data.append(new)
    save_doc(data)
    # todo: call bat file

