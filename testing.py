import configs

mongo = configs.mongo
order_id = "1"
mongo.update_one('orders', {'order_id': order_id, 'info': {'$exists': True}}, {'info.comment': "sffbafba"})
