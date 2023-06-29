import os
import shutil
os.chdir(os.path.dirname(os.getcwd()))
import configs


mongo = configs.mongo


def clear_folder(folder_dir):
    shutil.rmtree(folder_dir)
    os.mkdir(folder_dir)


def clean_reports_temp():
    cwd = os.path.dirname(__file__)
    clear_folder(os.path.join(cwd, '../reports/report_output'))
    clear_folder(os.path.join(cwd, '../reports/reports_temp'))
    clear_folder(os.path.join(cwd, '../static/img'))


def mongo_backup():
    mongo.dump("C:\\DB_backup")


def mongo_restore(backup_dir):
    mongo.restore(backup_dir)


def calc_rows_count_for_orders():
    orders_info_df = mongo.read_collection_df('orders', query={'info': {'$exists': True}})
    for order_id in orders_info_df['order_id']:
        order_rows_count = mongo.count_docs('orders', query={'order_id': order_id, 'info': {'$exists': False},
                                                             'job_id': {'$ne': '0'}})
        mongo.update_one('orders', {'order_id': order_id}, {'info.rows': str(order_rows_count)}, '$set')


def clean_empty_orders():
    orders_info_df = mongo.read_collection_df('orders', query={'info': {'$exists': True}})
    for order_id in orders_info_df['order_id']:
        order_rows_count = mongo.count_docs('orders', query={'order_id': order_id, 'info': {'$exists': False},
                                                             'job_id': {'$ne': '0'}})
        if order_rows_count == 0:
            mongo.delete_many('orders', {'order_id': order_id})


def add_ang():
    shapes = configs.shapes.copy()
    for shape in shapes:
        shapes[shape]['ang'] = list(range(1, len(shapes[shape]['positions'])))
    print(configs.shapes)
    configs.mongo.update_one('data_lists', {'name': 'shapes'}, {'data': shapes}, '$set')


if __name__ == '__main__':
    mongo_backup()
    # add_ang()
    # mongo_restore("C:\\Projects\\Tzomet\\old ver\\25-06-2023_10-34-50-663724")
