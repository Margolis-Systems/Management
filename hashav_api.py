import orders
import csv
from functions import ts


def save_csv(data, file_dir=''):
    if not file_dir:
        file_dir = 'c:\\hashav_test\\{}.csv'.format(ts('file_name'))
    header = []
    with open(file_dir, 'w', encoding='utf8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(data)
    return file_dir


def export_order(order_id, jobs=[]):
    order = orders.get_order_data(order_id)
    for r in order['rows']


