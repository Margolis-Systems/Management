import bcrypt

import pages
import db_handler
import pandas as pd
mongo = db_handler.DBHandle()

job_ids_df = mongo.read_collection_df('orders', query={'order_id': "2_R", 'info': {'$exists': False}})
print(job_ids_df)
