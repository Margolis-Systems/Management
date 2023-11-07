import main
import users
import pages


def clients():
    query = {}
    if main.request.form:
        req_form = dict(main.request.form)
        for item in req_form:
            if req_form[item]:
                query[item] = {'$regex': req_form[item]}
    clients_list = main.mongo.read_collection_df('costumers', query=query).to_dict('index')
    display_those_keys = ['name', 'id']
    dictionary = pages.get_dictionary()
    return main.render_template('clients.html', clients=clients_list, display_items=display_those_keys,
                                dictionary=dictionary)


def edit_client(client_id=""):
    user_group = users.validate_user()
    if not user_group:
        return users.logout()
    elif user_group < 50:
        return '', 204
    req_vals = list(main.request.values)
    if len(req_vals) == 1 and not client_id:
        client_id = req_vals[0]
    elif 'id' in main.request.form:
        client_id = main.request.form['id']
    client_data = main.mongo.read_collection_one('costumers', {'id': client_id})
    if main.request.method == 'POST':
        if main.request.form:
            if not client_data:
                client_id = add_new_client(main.request.form['name'])
                client_data = main.mongo.read_collection_one('costumers', {'id': client_id})
            for item in main.request.form:
                if 'site' in item:
                    new_site = main.request.form[item].strip()
                    if new_site and new_site not in client_data['sites']:
                        main.mongo.update_one('costumers', {'id': client_id}, {'sites': new_site}, '$push')  # , upsert=True)
                elif item not in ['return_to', 'order_type', 'id']:
                    main.mongo.update_one('costumers', {'id': client_id}, {item: main.request.form[item]}, '$set')
            return main.redirect('/edit_client?'+client_id)
    client_data = main.mongo.read_collection_one('costumers', {'id': client_id})
    return main.render_template('edit_client.html', client_data=client_data)


def gen_client_id():
    new_client_id = "1"
    costumers_df = main.mongo.read_collection_df('costumers')
    if costumers_df.empty:
        return new_client_id
    costumers_df['id'] = costumers_df['id'].astype('int')
    costumers_df.sort_values(by='id', inplace=True)
    last_id = costumers_df.iloc[-1]['id']
    return str(last_id + 1)


def add_new_client(client_name):
    client_id = gen_client_id()
    new_client_data = {'name': client_name, 'id': client_id, 'sites': []}
    main.mongo.insert_collection_one('costumers', new_client_data)
    return client_id


def delete_client():
    user_group = users.validate_user()
    if not user_group:
        return users.logout()
    elif user_group < 50:
        return '', 204
    req_vals = list(main.request.values)
    if len(req_vals) == 1:
        client_id = req_vals[0]
        if client_id:
            main.mongo.delete_many('costumers', {'id': client_id})
    return main.redirect('/clients')


def remove_site():
    user_group = users.validate_user()
    if not user_group:
        return users.logout()
    elif user_group > 70:
        client_id = main.request.values['client_id']
        site = main.request.values['site']
        main.mongo.update_one('costumers', {'id': client_id}, {'sites': site}, '$pull')
        return edit_client(client_id)
    return '', 204


def gen_client_list(client=""):
    sites_list = ""
    client_list = []
    if client:
        client_data = main.mongo.read_collection_one('costumers', {'name': client})
        if client_data:
            sites_list = client_data['sites']
            client_list = client
            return client_list, sites_list
    costumers = main.mongo.read_collection_df('costumers')
    if not costumers.empty:
        client_list = costumers['name'].to_list()
    return client_list, sites_list
