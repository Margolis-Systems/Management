from pymongo import MongoClient, ASCENDING
from datetime import datetime
import pandas as pd
import configs
import bson
import gc
import os


class DBHandle:
    def con_to_mongo_default(self, db_name):
        if db_name:
            db = MongoClient(configs.mongo_adr)[db_name]
        else:
            db = MongoClient(configs.mongo_adr)[configs.db_main]
        return db

    @staticmethod
    def con_to_mongo(mongo_adr, db_name):
        db = MongoClient(mongo_adr)[db_name]
        return db

    def read_collection_df(self, collect, db_name="", query=dict({})):
        gc.collect()
        db = self.con_to_mongo_default(db_name)
        db.validate_collection(collect)
        cur = db[collect].find(query, {'_id': False})
        df = pd.DataFrame(list(cur))
        return df

    def read_collection_df_sort(self, collect, sort_by, db_name="", query=dict({}), limit=0):
        gc.collect()
        db = self.con_to_mongo_default(db_name)
        db.validate_collection(collect)
        if limit:
            cur = db[collect].find(query, {'_id': False}).sort([(sort_by, -1)]).limit(limit)
        else:
            cur = db[collect].find(query, {'_id': False}).sort([(sort_by, -1)])
        df = pd.DataFrame(list(cur))
        return df

    def read_collection_one_sort(self, collect, sort_by, db_name="", query=dict({}), limit=0):
        db = self.con_to_mongo_default(db_name)
        db.validate_collection(collect)
        if limit:
            cur = db[collect].find(query, {'_id': False}).sort([(sort_by, -1)]).limit(limit)
        else:
            cur = db[collect].find(query, {'_id': False}).sort([(sort_by, -1)])
        ret = list(cur)
        if cur:
            if len(ret) == 1:
                return ret[0]
            return ret
        return {}

    def read_uniq(self, collection, fields, query={}, db_name=''):
        db = self.con_to_mongo_default(db_name)
        return db[collection].distinct(fields, query)

    def read_collection_one_var(self, collect, var_name, query=dict({}), db_name=""):
        db = self.con_to_mongo_default(db_name)
        db.validate_collection(collect)
        dic = db[collect].find_one(query, {'_id': False})
        return dic[var_name]

    def read_collection_one(self, collect, query=dict({}), db_name=""):
        db = self.con_to_mongo_default(db_name)
        db.validate_collection(collect)
        dic = db[collect].find_one(query, {'_id': False})
        return dic

    def read_collection_list(self, collect, query=dict({}), db_name="", limit=0):
        db = self.con_to_mongo_default(db_name)
        db.validate_collection(collect)
        if limit:
            dic = db[collect].find(query, {'_id': False}).sort([('_id', -1)]).limit(limit)
            return dic
        try:
            dic = list(db[collect].find(query, {'_id': False}))
        except Exception as e:
            print('read_list:\n{}\n{}'.format(e, query))
            return []
        return dic

    def read_collection_last(self, collect, sort_by, query=dict({}), db_name=""):
        db = self.con_to_mongo_default(db_name)
        db.validate_collection(collect)
        query[sort_by] = {'$exists': True}
        dic = db[collect].find_one(query, {'_id': False}, sort=[(sort_by, -1)])
        return dic

    def insert_collection_one(self, collect, doc, db_name=""):
        db = self.con_to_mongo_default(db_name)
        db.validate_collection(collect)
        collection = db[collect]
        collection.insert_one(doc)

    def upsert_collection_one(self, collect, key, doc, db_name="", upsert=True):
        db = self.con_to_mongo_default(db_name)
        db.validate_collection(collect)
        collection = db[collect]
        collection.replace_one(key, doc, upsert=upsert)

    def insert_collection_many(self, collect, df, db_name=""):
        db = self.con_to_mongo_default(db_name)
        db.validate_collection(collect)
        collection = db[collect]
        res = df.to_dict('records')
        collection.insert_many(res)

    def truncate_collection(self, collect, db_name=""):
        db = self.con_to_mongo_default(db_name)
        db.validate_collection(collect)
        collection = db[collect]
        collection.delete_many({})

    def delete_many(self, collect, query=dict({}), db_name=""):
        db = self.con_to_mongo_default(db_name)
        db.validate_collection(collect)
        collection = db[collect]
        collection.delete_many(query)

    def update_one(self, collect, key, doc, query, upsert=False, db_name=""):
        db = self.con_to_mongo_default(db_name)
        db.validate_collection(collect)
        collection = db[collect]
        # print(query,':', doc)
        return collection.update_one(key, {query: doc}, upsert=upsert)

    def update_many(self, collect, key, doc, query, upsert=False, db_name=""):
        db = self.con_to_mongo_default(db_name)
        db.validate_collection(collect)
        collection = db[collect]
        return collection.update_many(key, {query: doc}, upsert=upsert)

    def dump(self, path, collections=[], db_name=""):
        db = self.con_to_mongo_default(db_name)
        ts = datetime.now().strftime('%d-%m-%Y_%H-%M-%S-%f')
        path = os.path.join(path, ts)
        os.mkdir(path)
        if not collections:
            collections = db.list_collection_names()
        for coll in collections:
            with open(os.path.join(path, f'{coll}.bson'), 'wb+') as f:
                for doc in db[coll].find():
                    f.write(bson.BSON.encode(doc))

    def restore(self, path, db_name="", col=''):
        db = self.con_to_mongo_default(db_name)
        for coll in os.listdir(path):
            if coll.endswith('.bson') and (not col or col == coll):
                try:
                    with open(os.path.join(path, coll), 'rb+') as f:
                        data = f.read()
                        if data:
                            db[coll.split('.')[0]].insert_many(bson.decode_all(data))
                except Exception as e:
                    self.delete_many(coll.split('.')[0])
                    try:
                        with open(os.path.join(path, coll), 'rb+') as f:
                            db[coll.split('.')[0]].insert_many(bson.decode_all(data))
                    except Exception as e:
                        print(e)

    def count_docs(self, collect, query=dict({}), db_name=""):
        db = self.con_to_mongo_default(db_name)
        db.validate_collection(collect)
        collection = db[collect]
        return collection.count_documents(query)

    def create_index(self, collect, filed_name, db_name=""):
        db = self.con_to_mongo_default(db_name)
        db.validate_collection(collect)
        db[collect].create_index([(filed_name, ASCENDING)])
