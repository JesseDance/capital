__version__ = '1.0.0'
import sys
from datetime import datetime
from datetime import date
import os
import pymongo
import csv
import json
from mongo_connect_package.mongo_connect import setup_mongo_connection
from bson.objectid import ObjectId
from bson.json_util import loads


today = date.today()
today_str = str(today)
log_file_date = f"Reins-Treaty-Report-{today}.csv"
log_file_name = os.path.join("/home/jessedance/DRK_dev/capital_output_logs/treaty_mismatch/", log_file_date)
f = open(log_file_name, "w")

def parse_treaty_file(treaty_file_name):

    claim_treaty_list = []
    
    #reads second file
    with open(treaty_file_name, 'r', encoding='utf-8-sig') as file:
        csv_reader = csv.DictReader(file)

        
        for row in csv_reader:
            #strips white space and "$ and ," for each row
            stripped_row = {key: value.replace('$', '').replace(',', '').strip() for key, value in row.items()}
            claim_treaty_list.append(stripped_row)


    return claim_treaty_list


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


if __name__ == "__main__":

    treaty_file_name = "/home/jessedance/DRK_dev/capital_extracts/Claims_data/Additional_Claims_info_6.12.24.csv"
    claim_treaty_list = parse_treaty_file(treaty_file_name)
    print(json.dumps(claim_treaty_list, indent = 4))

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

    report_data = "Treaties mismatching in mongoDB \n"
    f.write(report_data)

    write_report_headings()

    check_type="Claims"
    qb_vendor_name="Kozlowski COmpany"

    for claim_dict in claim_treaty_list:

        reinsurance_treaty_name = claim_dict['Reinsurance Treaty Name']
        #reinsurance_treaty_name = "Brookmont Insurance Company"

        result = find_reinsurance_treaty(mdb=mdb, reinsurance_treaty_name=reinsurance_treaty_name)
        print("Mongo DB Result : ",result)

        if result is None:

            print('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
            print('X                            X')
            print('X    ERROR FINDING PAYEE     X')
            print('X                            X')
            print('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')

            write_treaty_mismatch_to_report(claim_dict)

    f.close()
