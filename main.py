# Server
from flask import Flask, render_template, url_for, request, session, redirect, send_file
from waitress import serve
import bcrypt
# Python libs
import json
# ERP libs
import db_handler
import pages
import prints

doc_gen = prints.Reports()

mongo = db_handler.DBHandle()
with open("config.json") as config_file:
    config = json.load(config_file)
app = Flask("Management system")


@app.route('/')
def index():
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
                return redirect(url_for('index'))
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
            mongo.insert_collection_one(config['users_collection'], {'name': request.form['username'],
                                        'password': bcrypt.hashpw(request.form['pass'].encode('utf-8'), bcrypt.gensalt())})
            session['username'] = request.form['username']
            return redirect(url_for('index'))
        message = "That username already exists!"
    return render_template('register.html', msg=message)


@app.route('/orders', methods=['GET'])
def orders():
    if 'order_id' in session.keys():
        return redirect('/edit_order')
    data_to_display = ['order_id', 'costumer_id', 'date_created']
    orders_list = pages.orders(data_to_display)
    return render_template('orders.html', orders=orders_list, display_items=data_to_display)


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
    order_data, order_type = pages.edit_order(order_id)
    if not order_data:
        return close_order()
    # todo: generate lists and patterns
    patterns = {'סוג': "10X10|15X15|20X20", 'קוטר': "5.5|6.5|8|10", 'צורה': "1|2|3|4|5|6|7|8|9|10",
                'מקט': "2006080100|2006080200|2006080300"}
    lists = {'סוג': ["10X10", "15X15", "20X20"], 'קוטר': [5.5, 6.5, 8, 10], 'צורה': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
             'מקט': ["2006080100", "2006080200", "2006080300"]}
    return render_template(order_type, order_data=order_data, patterns=patterns, lists=lists)


@app.route('/new_order', methods=['POST', 'GET'])
def new_order():
    if request.method == 'POST':
        session['order_id'] = pages.new_order(request.form)
        return redirect('/orders')
    else:
        if len(list(request.values)) > 0:
            order_type = list(request.values)[0]
        else:
            order_type = ""
        return render_template('/pick_client.html', clients=pages.gen_client_list, order_type=order_type)


@app.route('/close', methods=['GET'])
def close_order():
    if len(list(request.values)) > 0:
        additional_func = list(request.values)[0]
        # todo: complete functions
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
    order_id = ""
    msg = ""
    if request.method == 'POST':
        if 'scan' in request.form.keys():
            order_id = request.form['scan']
            # todo: finish
            job_id = order_id
            job = mongo.read_collection_one(config['orders_collection'], {'job_id':job_id})
            if job:
                msg = "Not found"
        else:
            job_id = request.form['order_id']
            job = mongo.read_collection_one(config['orders_collection'], {'job_id':job_id})
            if job:
                mongo.update_one(config['orders_collection'], {'job_id': job_id},
                                 {'$set': {'status': list(request.form.keys())[1]}}, upsert=True)
            else:
                msg = "Not found"
    return render_template('/scan.html', order=order_id, msg=msg)


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
