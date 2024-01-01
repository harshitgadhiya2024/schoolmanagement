from pymongo import MongoClient
from init import enviroment

def mongo_connect(app):
    try:
        get_mongourl = enviroment[app.config["enviroment"]]["Mongourl"]
        client = MongoClient(get_mongourl)
        return client

    except Exception as e:
        app.logger.error(f"Error when connecting mongo: {e}")

def data_added(app, db, coll_name, new_dict):
    try:
        coll = db[coll_name]
        coll.insert_one(new_dict)
        return "add_data"

    except Exception as e:
        app.logger.error(f"Error when save data in database: {e}")

# get all data from my table from database
def find_all_data(app, db, coll_name):
    try:
        coll = db[coll_name]
        res = coll.find({})
        return res

    except Exception as e:
        app.logger.error(f"Error when fetch all data in database: {e}")

# get only specific data from my database
def find_spec_data(app, db, coll_name, di):
    try:
        coll = db[coll_name]
        res = coll.find(di)
        return res

    except Exception as e:
        app.logger.error(f"Error when fetch specific data in database: {e}")

def delete_data(app, db, coll_name, di):
    try:
        coll = db[coll_name]
        res = coll.delete_one(di)
        return res

    except Exception as e:
        app.logger.error(f"Error when delete data in database: {e}")

def update_mongo_data(app, db, coll_name, prev_data, update_data):
    try:
        coll = db[coll_name]
        coll.update_one(prev_data, {"$set": update_data})
        return "updated"

    except Exception as e:
        app.logger.error(f"Error when update data in database: {e}")
