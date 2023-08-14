import functions
import main
import bcrypt
import datetime


def login():
    msg = ""
    coockie = main.request.cookies.get('userhash')
    if main.request.method == 'POST':
        msg = "סיסמה שגויה"  # todo: web dictionary
        username_input = main.request.form['username'].lower()
        login_user = main.mongo.read_collection_one(main.configs.users_collection, {'name': username_input})
        if login_user:
            if bcrypt.hashpw(main.request.form['pass'].encode('utf-8'), login_user['password']) == login_user['password']:
                main.session.permanent = True
                main.session['username'] = username_input
                main.session['user_config'] = {}
                resp = main.make_response()
                resp.headers['location'] = main.url_for('index')
                expire_date = datetime.datetime.now() + datetime.timedelta(days=1000)
                resp.set_cookie('userhash', username_input, expires=expire_date)
                return resp, 302
            else:
                functions.log('login_fail', {'ip': main.request.remote_addr})
                print('Failed to login from IP:', main.request.remote_addr)
    elif coockie:
        main.session['username'] = coockie
        return main.redirect('/')
    return main.render_template('login.html', msg=msg)


def logout():
    main.session.clear()
    resp = main.make_response()
    resp.headers['location'] = main.url_for('login')
    resp.set_cookie('userhash', '', max_age=0)
    return resp, 302


def register():
    user_group = validate_user()
    if not user_group:
        return logout()
    elif user_group < 99:
        return main.index()
    message = ""
    if main.request.method == 'POST':
        existing_user = main.mongo.read_collection_one(main.configs.users_collection, {'name': main.request.form['username'].lower()})
        if existing_user is None:
            main.mongo.insert_collection_one(main.configs.users_collection, {'name': main.request.form['username'].lower(), 'password':
                                            bcrypt.hashpw(main.request.form['pass'].encode('utf-8'), bcrypt.gensalt()),
                                        'group': 1, 'lang': main.request.form['lang']})
            # main.session['username'] = main.request.form['username']
            # return main.redirect(main.url_for('index'))
        else:
            message = "That username already exists!"
    return main.render_template('register.html', msg=message)


def edit_user():
    req_form = dict(main.request.form)
    doc = {}
    if 'password' in req_form:
        if req_form['password']:
            doc['password'] = bcrypt.hashpw(req_form['pass'].encode('utf-8'), bcrypt.gensalt())
    if 'lang' in req_form:
        if req_form['lang']:
            doc['lang'] = req_form['lang']
    main.mongo.update_one('users', {'name': req_form['username']}, doc, '$set')
    return '', 204


def validate_user():
    # todo: complete
    # username = request.cookies.get('userhash')
    # if username:
    #     login_user = mongo.read_collection_one(configs.users_collection, {'name': username})
    #     if login_user:
    #         session['username'] = username
    #         print(username)
    if 'username' in main.session.keys():
        user_data = main.mongo.read_collection_one(main.configs.users_collection, {'name': main.session['username']})
        if user_data:
            return user_data['group']
    return False


def clear():
    user = main.session['username']
    user_config = main.session['user_config']
    main.session.clear()
    main.session['username'] = user
    main.session['user_config'] = user_config


def user_configs():
    req_vals = dict(main.request.values)
    if req_vals:
        if 'filter' in req_vals:
            main.session['user_config']['filter'] = req_vals['filter']
            main.session['user_config']['search'] = {}
            main.session.modified = True
    return '', 204
