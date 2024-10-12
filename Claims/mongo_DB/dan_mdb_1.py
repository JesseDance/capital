__version__ = '1.0.0'
import sys
from datetime import datetime
import pymongo

from bson.objectid import ObjectId
from bson.json_util import loads


program_name = "dan_mdb.py"


def find_qb_vendor_config_xx(mdb, qb_vendor_name, check_type):
    collection_name = "qb_customer_vendor_config"
    mycol = mdb[collection_name]
    
    # convert object to dictionary 
    response = []
    
    response = list(mycol.find({
        "$and": [
    
        { "qb_vendor_name": { "$eq": qb_vendor_name }}, 
        { "check_type":  { "$eq": check_type }},
        
    ]}))
    return response


def find_reinsurance_treaty(mdb, reinsurance_treaty_name):
    collection_name = "reinsurance_treaty"
    mycol = mdb[collection_name]
    
    # convert object to dictionary 
    response = []
    
    response = mycol.find_one({

        "$and": [
    
        { "reinsurance_treaty": { "$eq": reinsurance_treaty_name }}
       
    ]})
    return response


def get_record_count_job_run(job_run: str, mdb: object):

    collection_name = "rates"
    mycol = mdb[collection_name]
    
    # convert object to dictionary 
    response_list = []
    result_data = {}
    
    response = list(mycol.aggregate([
    # Match the documents possible
        { "$match": { "job_run": { "$eq": job_run } }},

    # Group the documents
        { "$group": {
            "_id": {
                "job_run": "$job_run"
            },
        "count": { "$sum": 1 }

        }},

    ]))
    if response:
        result = response[0] 
        result_data = {}
        result_data.update({'job_run': result['_id']['job_run']})
        result_data.update({'count': result['count']})
    return result_data


'''
def find_one_qb_vendor_config(mdb, qb_vendor_name, check_type):
    collection_name = "qb_customer_vendor_config"
    mycol = mdb[collection_name]
    
    # convert object to dictionary 
    response = []
    
    response = mycol.find_one({
        "$and": [
    
        { "qb_vendor_name": { "$eq": qb_vendor_name }}, 
        { "check_type":     { "$eq": check_type }}
    ]})
    return response
'''

def find_one_qb_vendor_config(mdb, qb_vendor_name, check_type, check_date):
    collection_name = "qb_customer_vendor_config"
    mycol = mdb[collection_name]
    
    # convert object to dictionary 
    response = []
    
    response = mycol.find_one({
        "$and": [
    
        { "qb_vendor_name": { "$eq": qb_vendor_name }}, 
        { "check_type":     { "$eq": check_type }},
        { "effective_from_date":        { "$lte": check_date }},
        { "effective_to_date":          { "$gte": check_date }}
    ]})
    return response



if __name__ == "__main__":
    print("started")
    from mongo_connect_package.mongo_connect import setup_mongo_connection
    print("line 117")
    mdb = setup_mongo_connection()
    print("line 119")
    #subcat_code = "TV"
    #subcat_desc = "TV"
    #category_code = "CE"
    #tier_code = "TV"
    #find_subcat_dup(mdb, subcat_code, subcat_desc, category_code, tier_code)  

    
    #get_holds_overides_mongo("Greenbrier Chevrolet Buick","Claims Check")
    check_type="Claims"
    qb_vendor_name="Kozlowski COmpany"
    #check_type="Claims Check"
    #qb_vendor_name="Greenbrier Chevrolet Buick"

    print("line 133")

    reinsurance_treaty_name = "Brookmont Insurance Company"
    #reinsurance_treaty_name = "1"
    check_date = datetime(2024,6,6)
    print("line 138")

    
    
    

    result = find_one_qb_vendor_config(mdb=mdb, qb_vendor_name=qb_vendor_name, check_type=check_type, check_date=check_date)
    print("Mongo DB Date Result : ",result)

    print("line 147")

    result = find_reinsurance_treaty(mdb=mdb, reinsurance_treaty_name=reinsurance_treaty_name)
    print("Mongo DB Result : ",result)
    
    print("line 152")