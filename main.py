# Server
import flask
from flask import Flask, render_template, url_for, request, session, redirect, send_file
from waitress import serve
import bcrypt
# ERP libs
import configs
import db_handler
import pages
import reports
doc_gen = reports.Reports()
bartender = reports.Bartender()
mongo = db_handler.DBHandle()
app = Flask("Management system")


@app.route('/')
def index():
    if not validate_user():
        return logout()
    if 'username' in session:
        user = session['username']
        session.clear()
        session['username'] = user
        login_user = mongo.read_collection_one(configs.users_collection, {'name': session['username']})
        if login_user['group'] > 10:
            return render_template('main.html')
        else:
            return render_template('scan.html', order="", msg="")
    return render_template('login.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username_input = request.form['username'].lower()
        login_user = mongo.read_collection_one(configs.users_collection, {'name': username_input})
        if login_user:
            if bcrypt.hashpw(request.form['pass'].encode('utf-8'), login_user['password']) == login_user['password']:
                session['username'] = username_input
                resp = flask.make_response()
                resp.headers['location'] = url_for('index')
                resp.set_cookie('userhash', username_input)
                return resp, 302
    return render_template('login.html', msg="סיסמה שגויה")


@app.route('/logout', methods=['POST', 'GET'])
def logout():
    session.clear()
    return redirect('/login')


@app.route('/register', methods=['POST', 'GET'])
def register():
    user_group = validate_user()
    if not user_group:
        return logout()
    elif user_group < 99:
        return index()
    message = ""
    if request.method == 'POST':
        existing_user = mongo.read_collection_one(configs.users_collection, {'name': request.form['username'].lower()})
        if existing_user is None:
            mongo.insert_collection_one(configs.users_collection, {'name': request.form['username'].lower(), 'password':
                                        bcrypt.hashpw(request.form['pass'].encode('utf-8'), bcrypt.gensalt()),
                                        'group': 0, 'lang': 'he'})
            session['username'] = request.form['username']
            return redirect(url_for('index'))
        message = "That username already exists!"
    return render_template('register.html', msg=message)


def validate_user():
    # todo: complete
    # username = request.cookies.get('userhash')
    # if username:
    #     login_user = mongo.read_collection_one(configs.users_collection, {'name': username})
    #     if login_user:
    #         session['username'] = username
    #         print(username)
    if 'username' in session.keys():
        user_data = mongo.read_collection_one(configs.users_collection, {'name': session['username']})
        if user_data:
            return user_data['group']
    return False


@app.route('/orders', methods=['GET'])
def orders():
    if not validate_user():
        return logout()
    if 'order_id' in session.keys():
        return redirect('/edit_order')
    orders_list, display_those_keys = pages.orders()
    dictionary = pages.get_dictionary(session['username'])
    return render_template('orders.html', orders=orders_list, display_items=display_those_keys,
                           dictionary=dictionary)


@app.route('/edit_order', methods=['POST', 'GET'])
def edit_order():
    if not validate_user():
        return logout()
    if len(list(request.values)) == 1:
        order_id = list(request.values)[0]
        session['order_id'] = order_id
    elif len(request.form.keys()) > 1:
        pages.new_order_row()
        return redirect('/orders')
    if 'order_id' not in session.keys():
        return redirect('/orders')
    order_data, page_data = pages.edit_order_data()

    if not order_data:
        return close_order()
    return render_template('/edit_order.html', order_data=order_data, patterns=page_data[1], lists=page_data[0],
                           dictionary=page_data[2], rebar_data={})


@app.route('/edit_row', methods=['POST', 'GET'])
def edit_row():
    if not validate_user():
        return logout()
    if request.method == 'GET':
        session['order_id'], session['job_id'] = list(request.values)[0].split('job')
        order_data, page_data = pages.edit_order_data()
        if order_data:
            return render_template('/edit_row.html', order_data=order_data, patterns=page_data[1], lists=page_data[0],
                                   dictionary=page_data[2], rebar_data={})
    pages.new_order_row()
    return redirect('/orders')


@app.route('/new_order', methods=['POST', 'GET'])
def new_order():
    if not validate_user():
        return logout()
    client = ""
    order_type = ""
    if 'client' in request.form.keys():
        if 'site' in request.form.keys():
            session['order_id'] = pages.new_order(request.form)
            return redirect('/orders')
        else:
            client = request.form['client']
    if len(list(request.values)) == 1:
        order_type = list(request.values)[0]
    elif 'type' in request.form.keys():
        order_type = request.form['type']
    client_list, sites_list = pages.gen_client_list(client)
    return render_template('/pick_client.html', clients=client_list, site=sites_list, order_type=order_type)


@app.route('/close', methods=['GET'])
def close_order():
    if not validate_user():
        return logout()
    if len(list(request.values)) > 0:
        req_vals = list(request.values)
        additional_func = req_vals[0]
        if additional_func == 'delete':
            mongo.delete_many('orders', {'order_id': session['order_id']})
        elif additional_func == 'scan':
            return redirect('/scan')
    user = session['username']
    session.clear()
    session['username'] = user
    return redirect('/orders')


@app.route('/scan', methods=['POST', 'GET'])
def scan():
    if not validate_user():
        return logout()
    full_id = ""
    order_id = ""
    msg = ""
    status = ""
    if 'scan' in request.form.keys():
        order_id, job_id = reports.Images.decode_qr(request.form['scan'])
    elif 'order_id' in request.form.keys() and 'close' not in request.form.keys():
        order_id, job_id = request.form['order_id'].split("_")
        mongo.update_one(configs.orders_collection, {'order_id': order_id, 'job_id': job_id},
                         {'$set': {'status': request.form['status']}}, upsert=True)
    if order_id:
        job = mongo.read_collection_one(configs.orders_collection, {'order_id': order_id, 'job_id': job_id})
        if job:
            full_id = order_id + "_" + job_id
            if job['status'] == 'New':
                status = session['username'] + "__Start"
            elif job['status'] == session['username'] + "__Start":
                status = session['username'] + "__Finish"
            else:
                full_id = ""
                msg = job['status']
        else:
            msg = "Not found"
    else:
        msg = "Wrong input"
    return render_template('/scan.html', order=full_id, msg=msg, status=status)


@app.route('/jobs', methods=['POST', 'GET'])
def jobs():
    if not validate_user():
        return logout()
    order_type = "regular"
    if 'order_type' in request.form.keys():
        order_type = request.form['order_type']
    jobs_list = pages.jobs_list(order_type)
    dictionary = pages.get_dictionary(session['username'])
    return render_template('/jobs.html', jobs=jobs_list, dictionary=dictionary)


@app.route('/shape_editor', methods=['POST', 'GET'])
def shape_editor():
    shape_data = {}
    if request.form:
        shape_data = {'edges': 0, 'shape': request.form['shape_data'], 'tot_len': 0}
        for item in range(1, int(configs.shapes[shape_data['shape']]['edges']) + 1):
            shape_data['tot_len'] += int(request.form[str(item)])
        pages.new_order_row()
    else:
        req_vals = list(request.values)
        if len(req_vals) > 0:
            shape_data = {'shape': req_vals[0], 'edges': range(1, configs.shapes[req_vals[0]]['edges'] + 1), 'img_plot':"/static/images/shapes/"+req_vals[0]+".png"}
    shapes = {}
    for shape in configs.shapes:
        shapes[shape] = configs.shapes[shape]['description']
    return render_template('/shape_editor.html', shapes=shapes, shape_data=shape_data)


@app.route('/choose_printer', methods=['POST', 'GET'])
def choose_printer():
    printer_list = []
    if request.form:
        printer = request.form['printer']
        bartender.net_print(session['order_id'], printer, request.form['print_type'])
        return redirect('/orders')
    else:
        print_type = list(request.values)[0]
        printer_list = configs.printers[print_type]
    return render_template('/choose_printer.html', printer_list=printer_list, print_type=print_type)


'''
@app.route('/clients', methods=['POST'])
@app.route('/new_client', methods=['POST'])
@app.route('/scale', methods=['POST'])
@app.route('/mep', methods=['POST'])
'''

production = False
if __name__ == '__main__':
    app.secret_key = 'dffd$%23E3#@1FG'
    if production:
        serve(app, host=configs.server, port=configs.server_port)
    else:
        app.run(debug=True, host=configs.server, port=configs.server_port)
