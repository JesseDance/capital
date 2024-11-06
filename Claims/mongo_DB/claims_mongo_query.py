__version__ = '1.0.0'

import sys
from datetime import datetime
from datetime import date
import calendar
import os
import pymongo
import csv
import json
from parse_claims_file import parse_claim_files
from mongo_connect_package.mongo_connect import setup_mongo_connection
from bson.objectid import ObjectId
from bson.json_util import loads


today = date.today()
today_str = str(today)
log_file_date = f"MongoDB-Query-Report-{today}.csv"
log_file_name = os.path.join("/home/jessedance/DRK_dev/capital_output_logs/claims_logs/", log_file_date)
f = open(log_file_name, "w")




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


def find_reinsurance_treaty(mdb, reinsurance_treaty_name):
    collection_name = "reinsurance_companies"
    mycol = mdb[collection_name]
    
    # convert object to dictionary 
    response = []
    
    response = mycol.find_one({

        "$and": [
    
        { "reinsurance_company": { "$eq": reinsurance_treaty_name }}
       
    ]})
    return response

def get_check_dates():

    today = datetime.date.today()
    first = today.replace(day=1)
    lastMonth = first - datetime.timedelta(days=1)
    lastMonth = lastMonth.strftime("%m")
    datetime_object = datetime.datetime.strptime(lastMonth, "%m")
    month_name = datetime_object.strftime("%b")
    current_year = date.today().year
    month = int(lastMonth)
    last_day_month = calendar.monthrange(current_year, month)[1]
    check_date = f"{current_year}-{lastMonth}-{last_day_month}"
    
    return month_name, check_date

def write_report_headings():

    col_1 = 'Claim Number'
    col_2 = 'Reinsurance Treaty Name'
    col_3 = 'Seller Name'
    col_4 = 'Contract Holder Last Name'

    report_data = f"{col_1}, {col_2}, {col_3}, {col_4} \n" 
    f.write(report_data)


def write_treaty_mismatch_to_report(claim_dict):

    col_1 = claim_dict['Claim Number']
    col_2 = claim_dict['Reinsurance Treaty Name']
    col_3 = claim_dict['Seller Name']
    col_4 = claim_dict['Contract Holder Last Name']

    report_data = f"{col_1}, {col_2}, {col_3}, {col_4} \n" 
    f.write(report_data)


def serialize(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


if __name__ == "__main__":

    file_name = "/home/jessedance/DRK_dev/capital_extracts/Claims_data/CLAIMS_2024082215202191"
    additional_file_name = "/home/jessedance/DRK_dev/capital_extracts/Claims_data/Additional_Claims_info_9.20.24.csv"

    claim_list, list_of_names, list_of_payee_ids = parse_claim_files(file_name, additional_file_name)

    print('ZZZZZZZZZZZZZZZZZZZZZZZZZZZ')
    print('Z                         Z')
    print('Z    CONNECTING TO MDB    Z')
    print('Z                         Z')
    print('ZZZZZZZZZZZZZZZZZZZZZZZZZZZ')

    mdb = setup_mongo_connection()

    print('ZZZZZZZZZZZZZZZZZZZZZZZZZZZ')
    print('Z                         Z')
    print('Z    CONNECT SUCCESS      Z')
    print('Z                         Z')
    print('ZZZZZZZZZZZZZZZZZZZZZZZZZZZ')

    report_data = "Claim queries in mongoDB \n"
    f.write(report_data)

    write_report_headings()


    check_date = datetime(2024,11,4)
    print("check date: ", check_date)
    print("alternative check date: ", datetime(2024,11,4))
    check_type = "Claims"
    
    for payee_id in list_of_payee_ids:
        
        qb_vendor_name=payee_id

        result = find_one_qb_vendor_config(mdb=mdb, qb_vendor_name=qb_vendor_name, check_type=check_type, check_date=check_date)
        print("Mongo DB Date Result : ")
        print(json.dumps(result, default = serialize, indent = 4))

        if result is None:

            print('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
            print('X                             X')
            print('X       NO CONFIG FOUND       X')
            print('X                             X')
            print('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
    
    #f.close()


    for claim_dict in claim_list:


        reinsurance_treaty_name = claim_dict['Reinsurance Treaty Name']
        #reinsurance_treaty_name = "Brookmont Insurance Company"

        result = find_reinsurance_treaty(mdb=mdb, reinsurance_treaty_name=reinsurance_treaty_name)
        print("Mongo DB Result : ",result)

        if result is None:

            print('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
            print('X                             X')
            print('X    ERROR FINDING TREATY     X')
            print('X                             X')
            print('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')

            write_treaty_mismatch_to_report(claim_dict)

    f.close()
    
