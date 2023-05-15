# Server
import flask
from flask import Flask, render_template, url_for, request, session, redirect, send_file
from waitress import serve
import bcrypt
import os
# ERP libs
import configs
import db_handler
import pages
import reports
mongo = db_handler.DBHandle()
app = Flask("Management system")

with open('C:\\Server\\pid.txt', 'w') as pid:
    pid.write(str(os.getpid()))


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
    msg = ""
    if request.method == 'POST':
        msg = "סיסמה שגויה"
        username_input = request.form['username'].lower()
        login_user = mongo.read_collection_one(configs.users_collection, {'name': username_input})
        if login_user:
            if bcrypt.hashpw(request.form['pass'].encode('utf-8'), login_user['password']) == login_user['password']:
                session['username'] = username_input
                resp = flask.make_response()
                resp.headers['location'] = url_for('index')
                resp.set_cookie('userhash', username_input)
                return resp, 302
    return render_template('login.html', msg=msg)


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
        session['job_id'] = ""
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
        if 'order_id' in request.values.keys():
            session['order_id'] = request.values['order_id']
        else:
            session['order_id'] = list(request.values)[0]
    elif len(request.form.keys()) > 1:
        pages.new_order_row()
        return redirect('/orders')
    if 'order_id' not in session.keys():
        return redirect('/orders')
    order_data, page_data = pages.edit_order_data()

    if not order_data:
        return close_order()
    # todo: gen_defaults
    defaults = {'bar_type': 'מצולע', 'comment': order_data}
    return render_template('/edit_order.html', order_data=order_data, patterns=page_data[1], lists=page_data[0],
                           dictionary=page_data[2], rebar_data={}, defaults=defaults)


@app.route('/edit_row', methods=['POST', 'GET'])
def edit_row():
    if not validate_user():
        return logout()
    if request.method == 'GET':
        session['order_id'], session['job_id'] = list(request.values)[0].split('job')
        order_data, page_data = pages.edit_order_data()
        if order_data:
            defaults = {}
            for item in order_data['order_rows'][0]:

                if isinstance(order_data['order_rows'][0][item], list):
                    for li in range(len(order_data['order_rows'][0][item])):
                        if li > 0:
                            defaults[item+"_"+str(li - 1)] = order_data['order_rows'][0][item][li]
                        else:
                            defaults[item] = order_data['order_rows'][0][item][li]
                else:
                    defaults[item] = order_data['order_rows'][0][item]
            print(order_data)
            return render_template('/edit_row.html', order_data=order_data, patterns=page_data[1], lists=page_data[0],
                                   dictionary=page_data[2], defaults=defaults)
    pages.new_order_row()
    return redirect('/orders')


@app.route('/new_order', methods=['POST', 'GET'])
def new_order(client="", order_type=""):
    user_group = validate_user()
    if not user_group:
        return logout()
    if 'name' in request.form.keys() or client:
        if 'site' in request.form.keys() and 'sites_list' in session.keys():
            if request.form['site'] in session['sites_list']:
                session['sites_list'] = []
                session['order_id'] = pages.new_order(request.form)
                return redirect('/orders')
        elif 'name' in request.form.keys():
            client = request.form['name']
    if len(list(request.values)) == 1 and not order_type:
        order_type = list(request.values)[0]
    elif 'order_type' in request.form.keys():
        order_type = request.form['order_type']
    client_list, sites_list = pages.gen_client_list(client)
    permission = False
    if user_group > 50:
        permission = True
    if sites_list:
        session['sites_list'] = sites_list
    return render_template('/pick_client.html', clients=client_list, site=sites_list, order_type=order_type, permission=permission)


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
        decode = reports.Images.decode_qr(request.form['scan'])
        order_id, job_id = decode['order_id'], decode['job_id']
    elif 'order_id' in request.form.keys() and 'close' not in request.form.keys():
        order_id, job_id = request.form['order_id'].split("|")
        pages.change_order_status(request.form['status'], order_id, job_id)
        return redirect('/scan')
    if order_id:
        job = mongo.read_collection_one(configs.orders_collection, {'order_id': order_id, 'job_id': job_id})
        if job:
            full_id = order_id + "|" + job_id
            if job['status'] == 'Production':
                status = session['username'] + "__Start"
            elif job['status'] == session['username'] + "__Start":
                status = "Finished"
            else:
                full_id = ""
                msg = job['status']
        else:
            msg = "Not found"
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
            shape_data = {'shape': req_vals[0], 'edges': range(1, configs.shapes[req_vals[0]]['edges'] + 1),
                          'img_plot': "/static/images/shapes/"+req_vals[0]+".png"}
    shapes = {}
    for shape in configs.shapes:
        if os.path.exists("C:\\server\\static\\images\\shapes\\" + shape + ".png"):
            shapes[shape] = configs.shapes[shape]['description']
    return render_template('/shape_editor.html', shapes=shapes, shape_data=shape_data)


@app.route('/choose_printer', methods=['POST', 'GET'])
def choose_printer():
    if request.form:
        printer = request.form['printer']
        reports.Bartender.net_print(session['order_id'], printer, request.form['print_type'])
        if request.form['print_type'] == 'label':
            pages.change_order_status('Processed', session['order_id'])
        return '', 204
    else:
        print_type = list(request.values)[0]
        default_printer = mongo.read_collection_one('users', {'name': session['username']})
        if default_printer:
            default_printer = default_printer['default_printer'][print_type]
        printer_list = configs.printers[print_type]
    return render_template('/choose_printer.html', printer_list=printer_list, print_type=print_type, defaults={'printer':default_printer})


@app.route('/clients', methods=['POST', 'GET'])
def clients():
    clients_list = mongo.read_collection_df('costumers').to_dict('index')
    display_those_keys = ['name', 'id']
    dictionary = pages.get_dictionary(session['username'])
    return render_template('clients.html', clients=clients_list, display_items=display_those_keys,
                           dictionary=dictionary)


@app.route('/edit_client', methods=['POST', 'GET'])
def edit_client(client_id=""):
    user_group = validate_user()
    if not user_group:
        return logout()
    elif user_group < 50:
        return '', 204
    req_vals = list(request.values)
    if len(req_vals) == 1 and not client_id:
        client_id = req_vals[0]
    elif 'id' in request.form:
        client_id = request.form['id']
    client_data = mongo.read_collection_one('costumers', {'id': client_id})
    if request.method == 'POST':
        if request.form:
            if not client_data:
                client_id = add_new_client(request.form['name'])
                client_data = mongo.read_collection_one('costumers', {'id': client_id})
            for item in request.form:
                if 'site' in item:
                    new_site = request.form[item]
                    if new_site and new_site not in client_data['sites']:
                        mongo.update_one_push('costumers', {'id': client_id}, {'sites': new_site}, upsert=True)
                elif item not in ['return_to', 'order_type', 'id']:
                    mongo.update_one_set('costumers', {'id': client_id}, {item: request.form[item]})
            return redirect('/edit_client?'+client_id)
            # if 'order_type' in request.form.keys():
            #     order_type = request.form['order_type']
            #     return_to_page = request.form['return_to']
            #     if return_to_page == 'pick_client':
            #         return new_order(client=request.form['name'], order_type=order_type)
    client_data = mongo.read_collection_one('costumers', {'id': client_id})
    return render_template('edit_client.html', client_data=client_data)


def gen_client_id():
    new_client_id = "1"
    costumers_df = mongo.read_collection_df('costumers')
    if costumers_df.empty:
        return new_client_id
    costumers_df['id'] = costumers_df['id'].astype('int')
    costumers_df.sort_values(by='id', inplace=True)
    last_id = costumers_df.iloc[-1]['id']
    return str(last_id + 1)


def add_new_client(client_name):
    client_id = gen_client_id()
    new_client_data = {'name': client_name, 'id': client_id, 'sites': []}
    mongo.insert_collection_one('costumers', new_client_data)
    return client_id


@app.route('/delete_client', methods=['POST', 'GET'])
def delete_client():
    user_group = validate_user()
    if not user_group:
        return logout()
    elif user_group < 50:
        return '', 204
    req_vals = list(request.values)
    if len(req_vals) == 1:
        client_id = req_vals[0]
        if client_id:
            mongo.delete_many('costumers', {'id': client_id})
    return redirect('/clients')


@app.route('/change_order_status', methods=['GET', 'POST'])
def change_order_status():
    user_group = validate_user()
    if not user_group:
        return logout()
    elif user_group < 80:
        return '', 204
    if request.form:
        pages.change_order_status(request.form['status'], request.form['order_id'])
        return '', 204
    return render_template('change_order_status.html', order_id=session['order_id'])


'''
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
