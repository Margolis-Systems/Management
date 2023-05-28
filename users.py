import main
import bcrypt


def login():
    msg = ""
    if main.request.method == 'POST':
        msg = "סיסמה שגויה"  # todo: web dictionary
        username_input = main.request.form['username'].lower()
        login_user = main.mongo.read_collection_one(main.configs.users_collection, {'name': username_input})
        if login_user:
            if bcrypt.hashpw(main.request.form['pass'].encode('utf-8'), login_user['password']) == login_user['password']:
                main.session['username'] = username_input
                resp = main.flask.make_response()
                resp.headers['location'] = main.url_for('index')
                resp.set_cookie('userhash', username_input)
                return resp, 302
    return main.render_template('login.html', msg=msg)


def logout():
    main.session.clear()
    return main.redirect('/login')


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
                                        'group': 0, 'lang': 'he'})
            main.session['username'] = main.request.form['username']
            return main.redirect(main.url_for('index'))
        message = "That username already exists!"
    return main.render_template('register.html', msg=message)


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
    main.session.clear()
    main.session['username'] = user
