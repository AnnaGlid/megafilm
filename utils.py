from pymongo import MongoClient

def get_db_handle_local(db_name: str):
    client = MongoClient()
    db = client[db_name]
    return db, client
