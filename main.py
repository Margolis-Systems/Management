# Server
import flask
from flask import Flask, render_template, url_for, request, session, redirect, send_file
from waitress import serve
import bcrypt
# Python libs
import json
# ERP libs
import db_handler
import pages
import reports

doc_gen = reports.Reports()

mongo = db_handler.DBHandle()
with open("config.json") as config_file:
    config = json.load(config_file)
app = Flask("Management system")


@app.route('/')
def index():
    # validate_user()
    if 'username' in session:
        login_user = mongo.read_collection_one(config['users_collection'], {'name': session['username']})
        if login_user['group'] > 0:
            return render_template('main.html')
        else:
            return render_template('scan.html', order="", msg="")
    return render_template('login.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        login_user = mongo.read_collection_one(config['users_collection'], {'name': request.form['username']})
        if login_user:
            if bcrypt.hashpw(request.form['pass'].encode('utf-8'), login_user['password']) == login_user['password']:
                session['username'] = request.form['username']
                resp = flask.make_response()
                resp.headers['location'] = url_for('index')
                resp.set_cookie('userhash', request.form['username'])
                return resp, 302
    return render_template('login.html', msg="סיסמה שגויה")


@app.route('/logout', methods=['POST', 'GET'])
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/register', methods=['POST', 'GET'])
def register():
    message = ""
    if request.method == 'POST':
        existing_user = mongo.read_collection_one(config['users_collection'], {'name': request.form['username']})
        if existing_user is None:
            mongo.insert_collection_one(config['users_collection'], {'name': request.form['username'], 'password':
                                        bcrypt.hashpw(request.form['pass'].encode('utf-8'), bcrypt.gensalt())})
            session['username'] = request.form['username']
            return redirect(url_for('index'))
        message = "That username already exists!"
    return render_template('register.html', msg=message)


def validate_user():
    # todo: complete
    username = request.cookies.get('userhash')
    if username:
        login_user = mongo.read_collection_one(config['users_collection'], {'name': username})
        if login_user:
            session['username'] = username
            print(username)


@app.route('/orders', methods=['GET'])
def orders():
    if 'order_id' in session.keys():
        return redirect('/edit_order')
    orders_list, display_those_keys = pages.orders()
    return render_template('orders.html', orders=orders_list, display_items=display_those_keys,
                           dictionary=pages.gen_dictionary('orders'))


@app.route('/edit_order', methods=['POST', 'GET'])
def edit_order():
    if len(list(request.values)) == 1:
        order_id = list(request.values)[0]
        session['order_id'] = order_id
    elif len(list(request.values)) > 1:
        order_id = session['order_id']
        pages.new_order_row(request.form, order_id)
        return redirect('/orders')
    elif 'order_id' in session.keys():
        order_id = session['order_id']
    else:
        return redirect('/orders')
    order_data, page_data = pages.edit_order_data(order_id)
    if not order_data:
        return close_order()
    return render_template('/edit_order.html', order_data=order_data, patterns=page_data[1], lists=page_data[0],
                           dictionary=page_data[2])


@app.route('/edit_row', methods=['POST', 'GET'])
def edit_row():
    if request.method == 'GET':
        session['order_id'], session['job_id'] = list(request.values)[0].split('job')
        order_data, page_data = pages.edit_order_data(session['order_id'], session['job_id'])
        if order_data:
            return render_template('/edit_row.html', order_data=order_data, patterns=page_data[1], lists=page_data[0],
                                   dictionary=page_data[2])
    pages.new_order_row(request.form, session['order_id'], job_id=session['job_id'])
    return redirect('/orders')


@app.route('/new_order', methods=['POST', 'GET'])
def new_order():
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
    if len(list(request.values)) > 0:
        req_vals = list(request.values)
        additional_func = req_vals[0]
        if additional_func == 'delete':
            mongo.delete_many('orders', {'order_id': session['order_id']})
        elif additional_func == 'print':
            file_name = doc_gen.generate_order_report(session['order_id'])
            if file_name:
                return send_file(file_name, as_attachment=True)
        elif additional_func == 'scan':
            return redirect('/scan')
    user = session['username']
    session.clear()
    session['username'] = user
    return redirect('/orders')


@app.route('/scan', methods=['POST', 'GET'])
def scan():
    full_id = ""
    order_id = ""
    msg = ""
    status = ""
    if 'scan' in request.form.keys():
        order_id, job_id = reports.Images.decode_qr(request.form['scan'])
    elif 'order_id' in request.form.keys() and 'close' not in request.form.keys():
        order_id, job_id = request.form['order_id'].split("_")
        mongo.update_one(config['orders_collection'], {'order_id': order_id, 'job_id': job_id},
                         {'$set': {'status': request.form['status']}}, upsert=True)
    if order_id:
        job = mongo.read_collection_one(config['orders_collection'], {'order_id': order_id, 'job_id': job_id})
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
    jobs_list = pages.jobs_list()
    return render_template('/jobs.html', jobs=jobs_list, dictionary=pages.gen_dictionary('jobs'))

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
        serve(app, host=config['server'], port=config['server_port'])
    else:
        app.run(debug=True, host=config['server'], port=config['server_port'])
