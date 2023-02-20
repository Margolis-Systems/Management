import os
import shutil

def clear_folder(dfolder_dir):
    shutil.rmtree(dfolder_dir)
    os.mkdir(dfolder_dir)

def clean_reports_temp():
    cwd = os.path.dirname(__file__)
    clear_folder(os.path.join(cwd,'reports\\report_output'))
    clear_folder(os.path.join(cwd,'reports\\reports_temp'))

if (__name__) == '__main__':
    clean_reports_temp()
