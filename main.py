# Server
import flask

import data_logger
import main
from flask import Flask, render_template, url_for, request, session, redirect, flash, send_from_directory
from waitress import serve
from werkzeug.utils import secure_filename
import os
# ERP libs
import configs
import db_handler
import pages
import clients
import users
import orders
import scale
import plot_edit

mongo = db_handler.DBHandle()
app = Flask("Management system")

with open('pid.txt', 'w') as pid:  # C:\\Server\\
    pid.write(str(os.getpid()))


@app.route('/')
def index():
    if not users.validate_user():
        return logout()
    if 'username' in session:
        user = session['username']
        session.clear()
        main.session['user_config'] = {}
        session['username'] = user
        login_user = mongo.read_collection_one(configs.users_collection, {'name': session['username']})
        if login_user['group'] > 10:
            return render_template('main.html', user=user)
        else:
            return redirect('/scale')
    return render_template('login.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    return users.login()


@app.route('/logout', methods=['POST', 'GET'])
def logout():
    return users.logout()


@app.route('/register', methods=['POST', 'GET'])
def register():
    return users.register()


@app.route('/orders', methods=['POST', 'GET'])
def orders_page():
    return orders.orders()


@app.route('/edit_order', methods=['POST', 'GET'])
def edit_order():
    return orders.edit_order()


@app.route('/edit_row', methods=['POST', 'GET'])
def edit_row():
    return orders.edit_row()


@app.route('/new_order', methods=['POST', 'GET'])
def new_order(client="", order_type=""):
    return orders.new_order()


@app.route('/close', methods=['GET'])
def close_order():
    return orders.close_order()


@app.route('/scan', methods=['POST', 'GET'])
def scan():
    return pages.scan()


@app.route('/jobs', methods=['POST', 'GET'])
def jobs():
    users.clear()
    return pages.jobs()


@app.route('/shape_editor', methods=['POST', 'GET'])
def shape_editor():
    return pages.shape_editor()


@app.route('/choose_printer', methods=['POST', 'GET'])
def choose_printer():
    return pages.choose_printer()


@app.route('/order_files', methods=['POST', 'GET'])
def order_files():
    return pages.order_files()


@app.route('/order_file_upload', methods=['POST', 'GET'])
def order_file_upload():
    return pages.order_files()


@app.route('/download_attachment', methods=['POST', 'GET'])
def download_attachment():
    return pages.download_attachment()


@app.route('/clients', methods=['POST', 'GET'])
def clients_page():
    users.clear()
    return clients.clients()


@app.route('/edit_client', methods=['POST', 'GET'])
def edit_client():
    return clients.edit_client()


@app.route('/delete_client', methods=['POST', 'GET'])
def delete_client():
    return clients.delete_client()


@app.route('/change_order_status', methods=['GET', 'POST'])
def change_order_status():
    return orders.change_order_status()


@app.route('/cancel_order', methods=['GET', 'POST'])
def cancel_order():
    return orders.cancel_order()


@app.route('/copy_order', methods=['GET', 'POST'])
def copy_order():
    return orders.copy_order()


@app.route('/remove_site', methods=['POST', 'GET'])
def remove_site():
    return clients.remove_site()


@app.route('/scale', methods=['POST', 'GET'])
def scaling():
    # users.clear()
    return scale.main_page()


@app.route('/scaling_weight', methods=['POST', 'GET'])
def scaling_weight():
    cur_weight = scale.get_weight(main.session['scale']['site'])
    return {'ts1': cur_weight[0], 'weight1': cur_weight[1], 'ts2': cur_weight[2], 'weight2': cur_weight[3]}


@app.route('/tare_scale', methods=['POST', 'GET'])
def tare_scale():
    scale.tare_scale(main.session['scale']['site'])
    return scale.main_page()


@app.route('/print_scale', methods=['POST', 'GET'])
def print_scale():
    scale.print_scale()
    users.clear()
    return scale.main_page()


@app.route('/new_scale', methods=['POST', 'GET'])
def new_scale():
    users.clear()
    return scale.main_page()


@app.route('/scaling_pick_crane', methods=['POST', 'GET'])
def scaling_pick_crane():
    return scale.pick_crane()


@app.route('/scale_delete_last', methods=['POST', 'GET'])
def scale_delete_last():
    return scale.delete_last()


@app.route('/scale_report', methods=['POST', 'GET'])
def scale_report():
    return scale.scale_report()


@app.route('/dl_post', methods=['POST', 'GET'])
def dl_post():
    data_logger.save_dl_data()
    print('DataLogger POST\n', dict(request.values))
    return '', 204


@app.route('/plot_edit', methods=['POST', 'GET'])
def plot_editor():
    return plot_edit.plot_edit()


@app.route('/user_config', methods=['POST', 'GET'])
def user_config():
    return users.user_configs()


@app.route('/reports', methods=['POST', 'GET'])
def reports_page():
    return pages.reports_page()


'''
@app.route('/mep', methods=['POST'])
'''

production = False
if __name__ == '__main__':
    app.secret_key = 'dffd$%23E3#@1FG'
    if production:
        serve(app, host=configs.server, port=configs.server_port)
    else:
        app.run(debug=True, host=configs.server, port=configs.server_port)
