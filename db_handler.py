import pandas as pd
import json
from pymongo import MongoClient

'''

'''
with open("config.json") as config_file:
    config = json.load(config_file)

class DBHandle:
    def con_to_mongo_default(self, db_name):
        if db_name:
            db = MongoClient(config['mongo_adr'])[db_name]
        else:
            db = MongoClient(config['mongo_adr'])[config['db_main']]
        return db

    def con_to_mongo(self, mongo_adr, db_name):
        db = MongoClient(mongo_adr)[db_name]
        return db

    def read_collection_df(self, collect, db_name="", query={}):
        db = DBHandle.con_to_mongo_default(self, db_name)
        db.validate_collection(collect)
        cur = db[collect].find(query,{'_id': False})
        df = pd.DataFrame(list(cur))
        return df

    def read_collection_one_var(self, collect, var_name, query={}, db_name=""):
        db = DBHandle.con_to_mongo_default(self, db_name)
        db.validate_collection(collect)
        dic = db[collect].find_one(query,{'_id': False})
        return dic[var_name]

    def read_collection_one(self, collect, query={}, db_name=""):
        db = DBHandle.con_to_mongo_default(self, db_name)
        db.validate_collection(collect)
        dic = db[collect].find_one(query, {'_id': False})
        return dic

    def read_collection_last(self, collect, sort_by, query={}, db_name=""):
        db = DBHandle.con_to_mongo_default(self, db_name)
        db.validate_collection(collect)
        dic = db[collect].find_one(query, {'_id': False}, sort=[(sort_by, -1)])
        return dic

    def insert_collection_one(self, collect, doc, db_name=""):
        db = DBHandle.con_to_mongo_default(self, db_name)
        db.validate_collection(collect)
        collection = db[collect]
        collection.insert_one(doc)

    def upsert_collection_one(self, collect, key, doc, db_name=""):
        db = DBHandle.con_to_mongo_default(self, db_name)
        db.validate_collection(collect)
        collection = db[collect]
        collection.replace_one(key, doc, upsert=True)

    def insert_collection_many(self, collect, df, db_name=""):
        db = DBHandle.con_to_mongo_default(self, db_name)
        db.validate_collection(collect)
        collection = db[collect]
        res = df.to_dict('records')
        collection.insert_many(res)

    def truncate_collection(self, collect, db_name=""):
        db = DBHandle.con_to_mongo_default(self, db_name)
        db.validate_collection(collect)
        collection = db[collect]
        collection.delete_many({})

    def delete_many(self, collect, query={}, db_name=""):
        db = DBHandle.con_to_mongo_default(self, db_name)
        db.validate_collection(collect)
        collection = db[collect]
        collection.delete_many(query)

    def update_one(self, collect, key, doc, upsert=False, db_name=""):
        db = DBHandle.con_to_mongo_default(self, db_name)
        db.validate_collection(collect)
        collection = db[collect]
        collection.update_one(key, doc, upsert=upsert)