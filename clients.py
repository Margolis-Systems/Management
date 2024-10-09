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
                if item == 'new_site':
                    new_site = main.request.form[item].strip()
                    if new_site and new_site not in client_data['sites']:
                        main.mongo.update_one('costumers', {'id': client_id}, {'sites': {'name': new_site, 'id': gen_site_id(), 'comment': ''}}, '$push')
                elif 'site_' in item:
                    main.mongo.update_one('costumers', {'id': client_id, 'sites': {'$elemMatch': {'id': item[5:]}}}, {'sites.$.name': main.request.form[item]}, '$set')
                elif item not in ['return_to', 'order_type', 'id']:
                    main.mongo.update_one('costumers', {'id': client_id}, {item: main.request.form[item]}, '$set')
            return main.redirect('/edit_client?'+client_id)
    client_data = main.mongo.read_collection_one('costumers', {'id': client_id})
    if client_data:
        if 'comment' not in client_data:
            client_data['comment'] = {}
    return main.render_template('edit_client.html', client_data=client_data)


def gen_client_id():
    ids = main.mongo.read_collection_one('data_lists', {'name': 'ids'})
    if not ids:
        return '1'
    if 'client_id' not in ids:
        main.mongo.update_one('data_lists', {'name': 'ids'}, {'client_id': 1}, '$set')
        return '1'
    main.mongo.update_one('data_lists', {'name': 'ids'}, {'client_id': 1}, '$inc')
    return str(ids['client_id'] + 1)


def gen_site_id():
    ids = main.mongo.read_collection_one('data_lists', {'name': 'ids'})
    if not ids:
        return '1'
    if 'site_id' not in ids:
        main.mongo.update_one('data_lists', {'name': 'ids'}, {'site_id': 1}, '$set')
        return '1'
    main.mongo.update_one('data_lists', {'name': 'ids'}, {'site_id': 1}, '$inc')
    return str(ids['site_id'] + 1)


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
    if client:
        client_data = main.mongo.read_collection_one('costumers', {'name': client})
        if client_data:
            if 'comment' not in client_data:
                client_data['comment'] = {}
            sites_list = client_data['sites']
            return client_data, sites_list
    client_list = main.mongo.read_collection_list('costumers', {})
    return client_list, sites_list
