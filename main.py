# Server
import sys

from flask import Flask, render_template, url_for, request, session, redirect, flash, send_from_directory, make_response, Response
from waitress import serve
from werkzeug.utils import secure_filename
import os
# ERP libs
import data_logger
import configs
import db_handler
import functions
import mesh
import pages
import clients
import users
import orders
import scale
import plot_edit
import weights
import scan as scans
import hashav_api as hashav
from operator import itemgetter

mongo = db_handler.DBHandle()
app = Flask("Management system")


@app.route('/')
def index():
    if not users.validate_user():
        return redirect('/login')
    if 'username' in session:
        user = session['username']
        session.clear()
        session['user_config'] = {}
        session['username'] = user
        login_user = mongo.read_collection_one(configs.users_collection, {'name': session['username']})
        if login_user['group'] == 11:
            return redirect('/productionov')
        elif login_user['group'] > 10:
            return render_template('main.html', user=user)
        elif login_user['group'] == 2:
            return redirect('/weights')
        elif login_user['group'] == 3:
            return redirect('/scaleov')
        else:
            return redirect('/scan')
    return render_template('login.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    return users.login()


@app.route('/logout', methods=['POST', 'GET'])
def logout():
    return users.logout()


@app.route('/register', methods=['POST', 'GET'])
def register():
    if users.validate_user() < 99:
        return '', 204
    return users.register()


@app.route('/update_user', methods=['POST', 'GET'])
def update_user():
    if users.validate_user() < 99:
        return '', 204
    return users.edit_user()


@app.route('/orders', methods=['POST', 'GET'])
def orders_page():
    if users.validate_user() < 10:
        return redirect('/')
    return orders.orders()


@app.route('/all_orders', methods=['POST', 'GET'])
def all_orders_page():
    if users.validate_user() < 10:
        return redirect('/')
    return orders.orders(True)


@app.route('/edit_order', methods=['POST', 'GET'])
def edit_order():
    if users.validate_user() < 10:
        return redirect('/')
    return orders.edit_order()


@app.route('/edit_row', methods=['POST', 'GET'])
def edit_row():
    if users.validate_user() < 10:
        return redirect('/')
    return orders.edit_row()


@app.route('/new_order', methods=['POST', 'GET'])
def new_order(client="", order_type=""):
    if users.validate_user() < 10:
        return redirect('/')
    return orders.new_order()


@app.route('/close', methods=['GET'])
def close_order():
    return orders.close_order()


@app.route('/delete_rows', methods=['POST'])
def delete_rows():
    return orders.delete_rows()


@app.route('/scan', methods=['POST', 'GET'])
def scan():
    return scans.scan()


@app.route('/shape_editor', methods=['POST', 'GET'])
def shape_editor():
    if users.validate_user() < 10:
        return '', 204
    return pages.shape_editor()


@app.route('/choose_printer', methods=['POST', 'GET'])
def choose_printer():
    if users.validate_user() < 10:
        return '', 204
    return pages.choose_printer()


@app.route('/order_files', methods=['POST', 'GET'])
def order_files():
    if users.validate_user() < 10:
        return '', 204
    return pages.order_files()


@app.route('/split_order', methods=['POST', 'GET'])
def split_order():
    if users.validate_user() < 10:
        return '', 204
    return orders.split_order()


@app.route('/link_order', methods=['POST', 'GET'])
def link_order():
    if users.validate_user() < 10:
        return '', 204
    return orders.link_order()


@app.route('/upload_csv', methods=['POST', 'GET'])
def upload_csv():
    #curl -i -X POST -H "Content-Type: multipart/form-data" -F "file=@C:\Users\user\Downloads\1.csv;filename=1.csv" 10.0.0.25:5000/upload_csv
    if request.files:
        src = list(request.files.keys())[0]
        file_name = request.files[src].filename
        file_name = os.path.basename(file_name)
        if not os.path.exists("c:\\server\\csv\\{}\\".format(src)):
            os.mkdir("c:\\server\\csv\\{}\\".format(src))
        request.files[src].save("c:\\server\\csv\\{}\\{}".format(src, file_name))
        if src == 'Reshet_Roman':
            mesh.reshet_csv_data(file_name)
    return '', 204


@app.route('/order_file_upload', methods=['POST', 'GET'])
def order_file_upload():
    return pages.order_files()


@app.route('/download_attachment', methods=['POST', 'GET'])
def download_attachment():
    if users.validate_user() < 10:
        return '', 204
    return pages.download_attachment()


@app.route('/delete_attachment', methods=['POST', 'GET'])
def delete_attachment():
    if users.validate_user() < 10:
        return '', 204
    return pages.delete_attachment()


@app.route('/clients', methods=['POST', 'GET'])
def clients_page():
    if users.validate_user() < 10:
        return '', 204
    users.clear()
    return clients.clients()


@app.route('/edit_client', methods=['POST', 'GET'])
def edit_client():
    if users.validate_user() < 10:
        return '', 204
    return clients.edit_client()


@app.route('/delete_client', methods=['POST', 'GET'])
def delete_client():
    if users.validate_user() < 10:
        return '', 204
    return clients.delete_client()


@app.route('/change_order_status', methods=['GET', 'POST'])
def change_order_status():
    if users.validate_user() < 10:
        return '', 204
    return orders.change_order_status()


@app.route('/cancel_order', methods=['GET', 'POST'])
def cancel_order():
    if users.validate_user() < 10:
        return '', 204
    return orders.cancel_order()


@app.route('/copy_order', methods=['GET', 'POST'])
def copy_order():
    if users.validate_user() < 10:
        return '', 204
    return orders.copy_order()


@app.route('/split_row', methods=['GET', 'POST'])
def split_row():
    if users.validate_user() < 10:
        return '', 204
    return orders.split_row()


@app.route('/remove_site', methods=['POST', 'GET'])
def remove_site():
    return clients.remove_site()


@app.route('/scale', methods=['POST', 'GET'])
def scaling():
    return scale.main_page()


@app.route('/weights', methods=['POST', 'GET'])
def weights_page():
    if 'username' not in session:
        return redirect('/')
    return weights.main_page()


@app.route('/weights_history', methods=['POST', 'GET'])
def weights_history():
    history = mongo.read_collection_list('documents', {'doc.id': {'$exists': True}, 'doc.lines.0': {'$exists': True}}, 'Scaling')
    return render_template('/weight/history.html', data=history)


@app.route('/scaleov', methods=['POST', 'GET'])
def scale_overview():
    return scale.overview()


@app.route('/productionov', methods=['POST', 'GET'])
def productionov():
    return orders.overview()


@app.route('/scaling_weight', methods=['POST', 'GET'])
def scaling_weight():
    req_vals = dict(request.values)
    if 'new' in req_vals:
        if 'weights' in session:
            if 'selected' in session['weights']:
                selected = session['weights']['selected'].split(' : ')
                site = selected[0]
                sensor = selected[1]
                return weights.get_weights_data(site, sensor)
        return {}
        # return scale.read_weights()
    if 'scale' not in session:
        session['scale'] = {'site': {'crr': '1', 'sensors': ['3c1b', '3c1c']}}
        # return {}
    elif 'site' not in session['scale']:
        session['scale'] = {'site': {'crr': '1', 'sensors': ['3c1b', '3c1c']}}
        # return {}
    cur_weight = scale.get_weight(session['scale']['site'])
    return {'ts1': cur_weight[0], 'weight1': cur_weight[1], 'ts2': cur_weight[2], 'weight2': cur_weight[3]}


@app.route('/tare_scale', methods=['POST', 'GET'])
def tare_scale():
    scale.tare_scale(session['scale']['site'])
    return scale.main_page()


@app.route('/print_scale', methods=['POST', 'GET'])
def print_scale():
    scale.print_scale()
    users.clear()
    return '', 204


@app.route('/new_scale', methods=['POST', 'GET'])
def new_scale():
    users.clear()
    return scale.main_page()


@app.route('/scaling_pick_crane', methods=['POST', 'GET'])
def scaling_pick_crane():
    return scale.pick_crane()


@app.route('/scale_delete_last', methods=['POST', 'GET'])
def scale_delete_last():
    return scale.delete_report_row(-1)


@app.route('/scale_report', methods=['POST', 'GET'])
def scale_report():
    return scale.scale_report()


@app.route('/delete_report_row', methods=['POST', 'GET'])
def delete_report_row():
    if users.validate_user() < 10:
        return '', 204
    return scale.delete_report_row()


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


@app.route('/machines', methods=['POST', 'GET'])
def machines():
    if users.validate_user() < 90:
        return '', 204
    return pages.machines_page()


@app.route('/setconf', methods=['POST', 'GET'])
def setconf():
    if users.validate_user() < 99:
        return '', 204
    req_vals = request.values.to_dict()
    username = session['username']
    new_conf = {'lang': req_vals['lang']}
    mongo.update_one('users', {'name': username}, new_conf, '$set')
    return '', 204


@app.route('/file_listener', methods=['POST', 'GET'])
def file_listener():
    return pages.file_listener()


@app.route('/integration_orders', methods=['POST', 'GET'])
def integration_orders():
    intg_orders = mongo.read_collection_list('production_log', {'order_id': {'$regex': '2207'}})
    intg_orders = sorted(intg_orders, key=lambda x: int(x['job_id']))
    intg_orders = sorted(intg_orders, key=lambda x: int(x['order_id']))
    dtd = ['order_id', 'job_id', 'status', 'machine_id', 'machine_name', 'username', 'operator', 'diam', 'length',
           'quantity', 'weight', 'Start_ts', 'Finished_ts']
    return render_template('integration_orders.html', orders=intg_orders, data_to_display=dtd, dictionary=pages.get_dictionary())


@app.route('/reload_config', methods=['POST', 'GET'])
def reload_config():
    if users.validate_user() < 99:
        return '', 204
    configs.read_mongo_conf()
    configs.read_shapes()
    return redirect('/')


@app.route('/data_req', methods=['POST', 'GET'])
def data_req():
    ret = {}
    if users.validate_user() < 10:
        return ret
    req_vals = dict(request.values)
    if 'clients' in req_vals:
        client_list, sites_list = clients.gen_client_list()
        ret = {'clients': client_list}
    elif 'sites' in req_vals:
        client_list, sites_list = clients.gen_client_list(req_vals['sites'])
        ret = {'clients': client_list, 'sites': sites_list}
    elif 'order_types':
        ret = {}
    return ret


@app.route('/hashav', methods=['POST', 'GET'])
def hashav_export():
    if 'clear' in request.values:
        if 'hashav' in session:
            del session['hashav']
        return redirect('/hashav')
    client_list = hashav.costumers
    items = hashav.items
    drivers = hashav.drv_list
    if request.form:
        rf = dict(request.form)
        ord_ids = []
        for k in rf:
            if 'order_id' in k and rf[k]:
                ord_ids.append(rf[k])
        if ord_ids:
            session['hashav'] = {'data': hashav.format_data(ord_ids, rf['client'], rf['driver'], rf['split']),
                                 'ids': ord_ids}
        return redirect('/hashav')
    if 'hashav' in session:
        data = session['hashav']
    else:
        data = []
    return render_template('hashav/hashav.html', costumers=client_list, items=items, client='', drivers=drivers, data=data)


production = False
if len(sys.argv) > 1:
    if sys.argv[1] == 'True':
        production = True


if __name__ == '__main__':
    # 054200076

    app.secret_key = 'dffd$%23E3#@1FG'
    if production:
        if not os.path.isdir('h:'):
            functions.send_sms('שרת צומת ברזל הופעל מחדש')
        with open('pid.txt', 'w') as pid:
            pid.write(str(os.getpid()))
        serve(app, host=configs.server, port=configs.server_port, threads=100)
    else:
        app.run(debug=True, host=configs.server)  # , port=configs.server_port)
