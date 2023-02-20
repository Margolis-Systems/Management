#Server
from flask import Flask, render_template, url_for, request, session, redirect, send_file
from waitress import serve
import bcrypt
#Python libs
import datetime
import json
import os
#ERP libs
import db_handler
import pages
import prints

mongo = db_handler.DBHandle()
with open("config.json") as config_file: config = json.load(config_file)
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
            mongo.insert_collection_one(config['users_collection'], {'name': request.form['username'], 'password': bcrypt.hashpw(request.form['pass'].encode('utf-8'), bcrypt.gensalt())})
            session['username'] = request.form['username']
            return redirect(url_for('index'))
        message = "That username already exists!"
    return render_template('register.html', msg=message)


@app.route('/orders', methods=['GET'])
def orders():
    if 'order_id' in session.keys():
        return redirect('/edit_order')
    data_to_display = ['order_id', 'costumer', 'date_created']
    orders_list = pages.orders(data_to_display)
    return render_template('orders.html', orders=orders_list, display_items=data_to_display)


@app.route('/edit_order', methods=['POST', 'GET'])
def edit_order():
    if 'order_id' in session.keys():
        order_id = session['order_id']
    else:
        if len(list(request.values)) == 1:
            order_id = list(request.values)[0]
            session['order_id'] = order_id
        elif len(list(request.values)) > 1:
            order_id = session['order_id']
            pages.new_order_row(request.form, order_id)
        else:
            return redirect('/orders')
    order_data, order_type = pages.edit_order(order_id)
    if not order_data:
        return close_order()
    return render_template(order_type, order_data=order_data)


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
    if len(list(request.values)) > 1:
        additional_func = list(request.values)[0]
        if additional_func == 'cancel':
            mongo.delete_many('orders', {'order_id': session['prder_id']})
        elif additional_func == 'print':
            prints.reports.fill_word_doc()
    user = session['username']
    session.clear()
    session['username'] = user
    return redirect('/orders')

'''
@app.route('/clients', methods=['POST'])
@app.route('/new_client', methods=['POST'])
@app.route('/scan', methods=['POST'])
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