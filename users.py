import configs
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
        login_user = get_user_data(username_input)
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
        existing_user = get_user_data(main.request.form['username'].lower())
        if existing_user is None:
            form = dict(main.request.form)
            new_user = {}
            # todo: 'username and 'group'
            for k in form:
                if k == 'pass':
                    new_user['password'] = bcrypt.hashpw(form[k].encode('utf-8'), bcrypt.gensalt())
                elif '.' in k:
                    ks = k.split('.')
                    if ks[0] not in new_user:
                        new_user[ks[0]] = {}
                    new_user[ks[0]][ks[1]] = form[k]
                else:
                    new_user[k] = form[k]
            main.mongo.insert_collection_one(main.configs.users_collection, new_user)
        else:
            message = "That username already exists!"
    return main.render_template('register.html', msg=message, printers=configs.printers)


def edit_user():
    req_form = dict(main.request.form)
    doc = {}
    k_list = ['lang', 'default_printer.page', 'default_printer.label']
    i_list = ['group']
    for k in req_form:
        if k == 'pass':
            if req_form[k]:
                doc[k] = bcrypt.hashpw(req_form[k].encode('utf-8'), bcrypt.gensalt())
        elif k in k_list:
            if req_form[k]:
                doc[k] = req_form[k]
        elif k in i_list:
            if req_form[k]:
                doc[k] = int(req_form[k])
    main.mongo.update_one('users', {'name': req_form['username']}, doc, '$set')
    return '', 204


def validate_user():
    if 'username' in main.session.keys():
        user_data = get_user_data()
        if user_data:
            return user_data['group']
    return 0


def clear():
    user = main.session['username']
    user_config = main.session['user_config']
    main.session.clear()
    main.session['username'] = user
    main.session['user_config'] = user_config


def user_configs():
    req_vals = dict(main.request.values)
    keys = list(req_vals.keys())
    exclude = ['reverse']
    if not req_vals:
        main.session['user_config'] = {}
        main.session['user_config']['search'] = {}
    if 'search' in keys:
        keys.remove('search')
        if len(keys) == 1:
            if 'search' not in main.session['user_config']:
                main.session['user_config']['search'] = {}
            if keys[0] not in exclude or keys[0] not in main.session['user_config']['search']:
                main.session['user_config']['search'][keys[0]] = req_vals[keys[0]]
            else:
                del main.session['user_config']['search'][keys[0]]
        else:
            main.session['user_config']['search'] = {}
    main.session.modified = True
    return '', 204


def get_user_data(username=''):
    if not username:
        if 'username' not in main.session:
            return {}
        username = main.session['username']
    return main.mongo.read_collection_one(main.configs.users_collection, {'name': username})
