__version__ = '1.1.0' 
import pymongo
import json 
from bson.objectid import ObjectId
from secrets_manager_package.secret_from_secret_manager import get_secret


program_name = "mongo_connect.py"



#-begin-prod
def setup_mongo_connection():
    secret_data = get_secret('m_db_name')
    secret_data_d = json.loads(secret_data)
    assign_db = secret_data_d.get('assign_db')
    mClient, mdb = create_mongo_client_with_db(assign_db)
    return mdb


def create_mongo_client_with_db(assign_db):
    mClient = None
    secret_data = get_secret('m-connect')
    secret_data_d = json.loads(secret_data)
    
    if secret_data:
        mClient = pymongo.MongoClient(secret_data_d.get('mongo_connection'))
    else:
        print("")
        print("ERROR getting mongo_connection from secrets.")
        print("")
        
    mdb = mClient[assign_db]
    return mClient, mdb
#-end-prod
