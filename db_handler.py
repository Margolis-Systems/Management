from pymongo import MongoClient
from datetime import datetime
import pandas as pd
import configs
import bson
import gc
import os


class DBHandle:
    @staticmethod
    def con_to_mongo_default(db_name):
        if db_name:
            db = MongoClient(configs.mongo_adr)[db_name]
        else:
            db = MongoClient(configs.mongo_adr)[configs.db_main]
        return db

    @staticmethod
    def con_to_mongo(mongo_adr, db_name):
        db = MongoClient(mongo_adr)[db_name]
        return db

    @staticmethod
    def read_collection_df(collect, db_name="", query={}):
        gc.collect()
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
        query[sort_by] = {'$exists': True}
        dic = db[collect].find_one(query, {'_id': False}, sort=[(sort_by, -1)])
        return dic

    @staticmethod
    def insert_collection_one(collect, doc, db_name=""):
        db = DBHandle.con_to_mongo_default(db_name)
        db.validate_collection(collect)
        collection = db[collect]
        collection.insert_one(doc)

    @staticmethod
    def upsert_collection_one(collect, key, doc, db_name="", upsert=True):
        db = DBHandle.con_to_mongo_default(db_name)
        db.validate_collection(collect)
        collection = db[collect]
        collection.replace_one(key, doc, upsert=upsert)

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
    def update_one_set(collect, key, doc, upsert=False, db_name=""):
        db = DBHandle.con_to_mongo_default(db_name)
        db.validate_collection(collect)
        collection = db[collect]
        collection.update_one(key, {"$set": doc}, upsert=upsert)

    @staticmethod
    def update_many_set(collect, key, doc, upsert=False, db_name=""):
        db = DBHandle.con_to_mongo_default(db_name)
        db.validate_collection(collect)
        collection = db[collect]
        collection.update_many(key, {"$set": doc}, upsert=upsert)

    @staticmethod
    def update_one_push(collect, key, doc, upsert=False, db_name=""):
        db = DBHandle.con_to_mongo_default(db_name)
        db.validate_collection(collect)
        collection = db[collect]
        collection.update_one(key, {"$push": doc}, upsert=upsert)

    @staticmethod
    def dump(path, collections=[], db_name=""):
        db = DBHandle.con_to_mongo_default(db_name)
        ts = datetime.now().strftime('%d-%m-%Y_%H-%M-%S-%f')
        path = os.path.join(path, ts)
        os.mkdir(path)
        if not collections:
            collections = db.list_collection_names()
        for coll in collections:
            with open(os.path.join(path, f'{coll}.bson'), 'wb+') as f:
                for doc in db[coll].find():
                    f.write(bson.BSON.encode(doc))

    @staticmethod
    def restore(path, db_name=""):
        db = DBHandle.con_to_mongo_default(db_name)
        for coll in os.listdir(path):
            print(coll)
            if coll.endswith('.bson'):
                try:
                    with open(os.path.join(path, coll), 'rb+') as f:
                        db[coll.split('.')[0]].insert_many(bson.decode_all(f.read()))
                except Exception as e:
                    print(e)
