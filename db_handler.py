import pandas as pd
import json
from pymongo import MongoClient

'''

'''
with open("config.json") as config_file:
    config = json.load(config_file)


class DBHandle:
    @staticmethod
    def con_to_mongo_default(db_name):
        if db_name:
            db = MongoClient(config['mongo_adr'])[db_name]
        else:
            db = MongoClient(config['mongo_adr'])[config['db_main']]
        return db

    @staticmethod
    def con_to_mongo(mongo_adr, db_name):
        db = MongoClient(mongo_adr)[db_name]
        return db

    @staticmethod
    def read_collection_df(collect, db_name="", query={}):
        db = DBHandle.con_to_mongo_default(db_name)
        db.validate_collection(collect)
        cur = db[collect].find(query, {'_id': False})
        df = pd.DataFrame(list(cur))
        return df

    @staticmethod
    def read_collection_one_var(collect, var_name, query={}, db_name=""):
        db = DBHandle.con_to_mongo_default(db_name)
        db.validate_collection(collect)
        dic = db[collect].find_one(query, {'_id': False})
        return dic[var_name]

    @staticmethod
    def read_collection_one(collect, query={}, db_name=""):
        db = DBHandle.con_to_mongo_default(db_name)
        db.validate_collection(collect)
        dic = db[collect].find_one(query, {'_id': False})
        return dic

    @staticmethod
    def read_collection_last(collect, sort_by, query={}, db_name=""):
        db = DBHandle.con_to_mongo_default(db_name)
        db.validate_collection(collect)
        dic = db[collect].find_one(query, {'_id': False}, sort=[(sort_by, -1)])
        return dic

    @staticmethod
    def insert_collection_one(collect, doc, db_name=""):
        db = DBHandle.con_to_mongo_default(db_name)
        db.validate_collection(collect)
        collection = db[collect]
        collection.insert_one(doc)

    @staticmethod
    def upsert_collection_one(collect, key, doc, db_name=""):
        db = DBHandle.con_to_mongo_default(db_name)
        db.validate_collection(collect)
        collection = db[collect]
        collection.replace_one(key, doc, upsert=True)

    @staticmethod
    def insert_collection_many(collect, df, db_name=""):
        db = DBHandle.con_to_mongo_default(db_name)
        db.validate_collection(collect)
        collection = db[collect]
        res = df.to_dict('records')
        collection.insert_many(res)

    @staticmethod
    def truncate_collection(collect, db_name=""):
        db = DBHandle.con_to_mongo_default(db_name)
        db.validate_collection(collect)
        collection = db[collect]
        collection.delete_many({})

    @staticmethod
    def delete_many(collect, query={}, db_name=""):
        db = DBHandle.con_to_mongo_default(db_name)
        db.validate_collection(collect)
        collection = db[collect]
        collection.delete_many(query)

    @staticmethod
    def update_one(collect, key, doc, upsert=False, db_name=""):
        db = DBHandle.con_to_mongo_default(db_name)
        db.validate_collection(collect)
        collection = db[collect]
        collection.update_one(key, doc, upsert=upsert)
