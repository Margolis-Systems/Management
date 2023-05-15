import configs

mongo = configs.mongo


def change_order_status(new_status, order_id, job_id=""):
    if job_id:
        mongo.update_one_set('orders', {'order_id': order_id, 'job_id': job_id}, {'status': new_status})
    else:
        mongo.update_one_set('orders', {'order_id': order_id, 'info': {'$exists': True}}, {'info.status': new_status})
        mongo.update_many_set('orders', {'order_id': order_id, 'info': {'$exists': False}}, {'status': new_status})


# change_order_status('Production', '6_R')

