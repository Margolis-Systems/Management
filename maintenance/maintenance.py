import os
os.chdir(os.path.dirname(os.getcwd()))
import shutil
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


if __name__ == '__main__':
    mongo_backup()
    # mongo_restore("C:\\Users\\MargoliSys\\Desktop\\15-05-2023_15-37-10-377286")
