import os
import shutil
import configs
import db_handler


def clear_folder(folder_dir):
    shutil.rmtree(folder_dir)
    os.mkdir(folder_dir)


def clean_reports_temp():
    cwd = os.path.dirname(__file__)
    clear_folder(os.path.join(cwd, 'reports\\report_output'))
    clear_folder(os.path.join(cwd, 'reports\\reports_temp'))
    clear_folder(os.path.join(cwd, 'static\\img'))


def mongo_backup():
    db_handler.DBHandle.dump("C:\\DB_backup")


if __name__ == '__main__':
    # clean_reports_temp()
    configs.mongo.delete_many('orders')
    mongo_backup()
