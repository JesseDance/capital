from datetime import date
import datetime
import calendar
import json
from jinja2 import Environment, FileSystemLoader, select_autoescape
from decimal import Decimal

def parse_cancellation_file(file_name):

	sorted_cancellation_list = create_list_of_cancellatoins(file_name)

	list_of_names = create_list_of_names(sorted_cancellation_list)

	return sorted_cancellation_list, list_of_names


def create_list_of_cancellatoins(file_name):

	with open(file_name, 'r') as file:

			cancellation_list = []

			contract_cancellation_trailer_list = []

			for row in file:

				record_id = row[0:2].strip()

				if record_id == 'C2':

					carrier = row[2:6].strip()
					filler = row[6:7].strip()
					account_number = row[7:25].strip()
					claim_number = row[25:41].strip()
					contract_number = row[41:61].strip()
					sequence_number = row[61:68].strip()
					check_date = row[68:76].strip()
					check_amount = row[76:86].replace('*','').strip()
					comment1 = row[86:136].strip()
					comment2 = row[136:186].strip()
					comment3 = row[186:236].strip()
					check_number = row[236:256].strip()
					payee_name = row[256:336].strip()
					payee_address1 = row[336:386].strip()
					payee_address2 = row[386:436].strip()
					payee_city = row[436:461].strip()
					payee_state = row[461:463].strip()
					payee_zip = row[463:473].strip()
					audit_date = row[473:481].strip()
					tax_amount1 = row[481:491].replace('*','').strip()
					tax_1_registration_number = row[491:511].strip()
					tax_amount2 = row[511:521].replace('*','').strip()
					tax_2_registration_number = row[521:541].strip()
					payee_language = row[541:543].strip()
					rate_book = row[543:555].strip()
					plan_code = row[555:557].strip()
					dealer_state = row[557:559].strip()
					program_id = row[559:563].strip()
					new_or_used = row[563:564].strip()
					check_type = row[564:567].strip()
					contract_holder_first_name = row[567:597].strip()
					contract_holder_middle_initial = row[597:598].strip()
					contract_holder_last_name = row[598:658].strip()
					vendor_customer_number = row[658:708].strip()
					check_cleared_date = row[708:716].strip()
					

					claim_dict = {
						'Record Id': record_id,
						'Carrier': carrier,
						'Account': account_number,
						'Claim Number': claim_number,
						'Contract Number': contract_number,
						'Sequence Number': sequence_number,
						'Check Date': check_date,
						'Cancellation Amt': check_amount,
						'Comment1': comment1,
						'Comment2': comment2,
						'Comment3': comment3,
						'Check Number': check_number,
						'Payee Name': payee_name,
						'Payee Address1': payee_address1,
						'Payee Address2': payee_address2,
						'Payee City': payee_city,
						'Payee State': payee_state,
						'Payee Zip': payee_zip,
						'Audit Date': audit_date,
						'Tax Amount 1': tax_amount1,
						'Tax 1 Registration Number': tax_1_registration_number,
						'Tax Amount 2': tax_amount2,
						'Tax 2 Registration Number': tax_2_registration_number,
						'Payee Language': payee_language,
						'Rate Book': rate_book,
						'Plan Code': plan_code,
						'Dealer State': dealer_state,
						'Program ID': program_id,
						'New Used': new_or_used,
						'Check Type': check_type,
						'Contract Holder First Name': contract_holder_first_name,
						'Contract Holder Middle Initial': contract_holder_middle_initial,
						'Contract Holder Last Name': contract_holder_last_name,
						'Vendor_Customer_No': vendor_customer_number,
						'Check Cleared Date': check_cleared_date
					}

					cancellation_list.append(claim_dict)

				if record_id == '99':

					carrier = row[2:6].strip()
					sequence_number = row[61:68].strip()
					date = row[68:76].strip()
					total_check_amount = row[76:86].replace('*','').strip()
					comment = row[86:136].strip()
					check_number = row[186:206].strip()
					payee_name = row[206:286].strip()
					payee_address1 = row[286:336].strip()
					payee_address2 = row[336:386].strip()
					payee_city = row[386:411].strip()
					tax_amount1 = row[443:453].replace('*','').strip()
					tax_amount2 = row[473:483].replace('*','').strip()
					check_type = row[2571:2574].strip()

					check_trailer_dict = {
						'Record Id': record_id,
						'Carrier': carrier,
						'Sequence Number': sequence_number,
						'Date': date,
						'Total Check Amount': total_check_amount,
						'Comment': comment1,
						'Check Number': check_number,
						'Payee Name': payee_name,
						'Payee Address1': payee_address1,
						'Payee Address2': payee_address2,
						'Payee City': payee_city,
						'Tax Amount 1': tax_amount1,
						'Tax Amount 2': tax_amount2,
						'Check Type': check_type
						}

					contract_cancellation_trailer_list.append(check_trailer_dict)

	sorted_cancellation_list = sorted(cancellation_list, key=lambda x: (x['Payee Name'], x['Contract Number']))

	return sorted_cancellation_list


def get_memo_data(cancellation_dict):

	#creates check_memo 
	contract_number = claim_dict['Contract Number']
	last_name = claim_dict['Contract Holder Last Name']
	seller_name = claim_dict['Seller Name']

	check_memo = f"{contract_number}/{last_name}/{seller_name}"

	return check_memo

def create_list_of_names(sorted_cancellation_list):

	#creates a list of each unique name in the list of dicts
	list_of_names = {item['Payee Name'] for item in sorted_cancellation_list}

	return sorted(list_of_names)



def print_list(sorted_cancellation_list, list_of_names):
	#print(json.dumps(sorted_cancellation_list, indent = 4))
	print(json.dumps(list_of_names, indent = 4))
	for cancellation in sorted_cancellation_list:
		print(cancellation)





if __name__ == "__main__":

	file_name = "/home/jessedance/development/capital/Cancellations/REFUNDS_20240612070442343"
	sorted_cancellation_list, list_of_names = parse_cancellation_file(file_name)

	print_list(sorted_cancellation_list, list_of_names)