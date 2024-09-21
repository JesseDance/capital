import csv
import json
from decimal import Decimal



def parse_claim_files(file_name, additional_file_name):

	#creates list of dicts with cleaned and sorted items from first file
	sorted_claim_list = create_claim_list_of_dicts(file_name)

	#reads second file and adds new data for check_memo
	sorted_claim_list_with_memo = parse_additional_file(additional_file_name, sorted_claim_list)

	#creates a list of unique names from the sorted list
	list_of_names = create_list_of_names(sorted_claim_list)

	list_of_payee_ids = create_list_of_payee_ids(sorted_claim_list)

	return sorted_claim_list_with_memo, list_of_names, list_of_payee_ids


def create_claim_list_of_dicts(file_name):

	with open(file_name, 'r') as file:

		claim_list = []

		claim_check_trailer_list = []

		for row in file:

			
			payee_name = row[188:260].strip()

			record_id = row[0:2].strip()

			if record_id == 'C1':

				carrier = row[2:6].strip()
				payee_number = row[7:25].strip()

				payee_number = f'{payee_number}{" V"}'

				claim_number = row[25:41].strip()
				contract_number = row[41:61].strip()
				sequence_number = row[61:68].strip()
				check_date = row[68:76].strip()
				check_amount = row[76:86].replace('*','').strip()
				comment1 = row[86:136].strip()
				comment2 = row[136:186].strip()
				check_number = row[186:206].strip()
				payee_name = row[206:286].strip()
				payee_address1 = row[286:336].strip()
				payee_address2 = row[336:386].strip()
				payee_city = row[386:411].strip()
				payee_state = row[411:413].strip()
				payee_zip = row[413:423].strip()
				repair_order = row[423:443].strip()
				tax_amount1 = row[443:453].replace('*',' ').strip()
				tax_1_registration_number = row[453:473].strip()
				tax_amount2 = row[473:483].replace('*',' ').strip()
				tax_2_registration_number = row[483:503].strip()
				payee_language = row[503:505].strip()
				customer_first_name = row[505:535].strip()
				customer_last_name = row[535:595].strip()
				rate_book = row[595:599].strip()
				plan_code = row[607:609].strip()
				dealer_state = row[609:611].strip()
				program_id = row[611:615].strip()
				new_or_used = row[615:616].strip()

				line_items = row[616:2236].strip()

				'''
				line_item_type = row[608:609].strip()
				job_number = row[609:613].strip()
				loss_code_description = row[613:673].strip()
				amount = row[673:681].strip()
				sales_tax = row[681:689].strip()
				'''

				dealer_number = row[2236:2253].strip()
				payee_fax = row[2253:2264].strip()
				claim_contact = row[2264:2324].strip()
				claim_payee_memo = row[2324:2579].strip()
				check_type = row[2579:2582].strip()
				account_number = row[2582:2602].strip()
				payee_type = row[2602:2603].strip()
				claim_loss_date = row[2603:2611].strip()
				vendor_customer_number = row[2611:2661].strip()
				check_cleared_date = row[2661:2669].strip()
				vin = row[2669:2686].strip()

				contract_holder_last_name = ''
				seller_name = ''
				

				if payee_number == " V":
					payee_number = f"{payee_name} V"


				claim_dict = {
					'Record Id': record_id,
					'Carrier': carrier,
					'Payee Number': payee_number,
					'Claim Number': claim_number,
					'Contract Number': contract_number,
					'Sequence Number': sequence_number,
					'Check Date': check_date,
					'Claim_Amt': check_amount,
					'Comment1': comment1,
					'Comment2': comment2,
					'Check Number': check_number,
					'Payee Name': payee_name,
					'Payee Address1': payee_address1,
					'Payee Address2': payee_address2,
					'Payee City': payee_city,
					'Payee State': payee_state,
					'Payee Zip': payee_zip,
					'Repair Order': repair_order,
					'Tax Amount 1': tax_amount1,
					'Tax 1 Registration Number': tax_1_registration_number,
					'Tax Amount 2': tax_amount2,
					'Tax 2 Registration Number': tax_2_registration_number,
					'Payee Language': payee_language,
					'Customer First Name': customer_first_name,
					'Customer Last Name': customer_last_name,
					'Rate Book': rate_book,
					'Plan Code': plan_code,
					'Dealer State': dealer_state,
					'Program ID': program_id,
					'New or Used': new_or_used,

					'Line Items': line_items,

					'Dealer Number': dealer_number,
					'Payee Fax': payee_fax,
					'Claim Contact': claim_contact,
					'Claim Payee Memo': claim_payee_memo,
					'Check Type': check_type,
					'Account Number': account_number,
					'Payee Type': payee_type,
					'Claim Loss Date': claim_loss_date,
					'Vendor Customer Number': vendor_customer_number,
					'Check Cleared Date': check_cleared_date,
					'VIN': vin,

					'Contract Holder Last Name': contract_holder_last_name,
					'Seller Name': seller_name
				}



				claim_list.append(claim_dict)



	'''
	#read first file into a list of dicts
	with open(file_name, 'r', encoding='utf-8-sig') as file:
		csv_reader = csv.DictReader(file)
		claim_list = []

		for row in csv_reader:
			#strips white space and "$ and ," then adds to dict
			stripped_row = {key: value.replace('$', '').replace(',', '').strip() for key, value in row.items()}
			claim_list.append(stripped_row)
	'''

	#sorts the list by name and claim number
	sorted_claim_list = sorted(claim_list, key=lambda x: (x['Payee Name'], x['Claim Number']))

	return sorted_claim_list


def parse_additional_file(additional_file_name, sorted_claim_list):
	
	#reads second file
	with open(additional_file_name, 'r', encoding='utf-8-sig') as file:
		csv_reader = csv.DictReader(file)

		
		for row in csv_reader:
			#strips white space and "$ and ," for each row
			stripped_row = {key: value.replace('$', '').replace(',', '').strip() for key, value in row.items()}

			#reads the original list and adds the data to a claim dict if the claim number matches
			for claim in sorted_claim_list:
				if stripped_row['Claim Number'] == claim['Claim Number']:
					claim.update(stripped_row)
		

	#adds the memo to each claim dict
	for claim in sorted_claim_list:
		claim['check_memo'] = get_memo_data(claim)

	return sorted_claim_list


def get_memo_data(claim_dict):

	#creates check_memo 
	claim_number = claim_dict['Claim Number']
	last_name = claim_dict['Contract Holder Last Name']
	seller_name = claim_dict['Seller Name']

	check_memo = f"{claim_number}/{last_name}/{seller_name}"

	return check_memo

def print_list(sorted_claim_list_with_memo):
	print(json.dumps(sorted_claim_list_with_memo[0], indent = 4))
	print(json.dumps(list_of_names, indent = 4))
	print(json.dumps(list_of_payee_ids, indent = 4))
	number_match_error = 0
	successful_matches = 0
	for claim in sorted_claim_list_with_memo:
		if claim['Seller Name'] == '':
			number_match_error += 1
			print(json.dumps(claim, indent = 4))
		if claim['Seller Name'] != '':
			successful_matches += 1
		#print(claim)

	#distinct_name = ''
	#claims_by_distinct_name = list(filter(lambda name: name['Payee Name'] == distinct_name, sorted_claim_list_with_memo))

	print(f'number of match errors: {number_match_error}')
	print(f'number of successful_matches: {successful_matches}')


def create_list_of_names(sorted_claim_list):

	#creates a list of each unique name in the list of dicts
	list_of_names = {item['Payee Name'] for item in sorted_claim_list}

	return sorted(list_of_names)

def create_list_of_payee_ids(sorted_claim_list):

	list_of_payee_ids = {item['Payee Number'] for item in sorted_claim_list}

	return sorted(list_of_payee_ids)

if __name__ == "__main__":

	file_name = "/home/jessedance/DRK_dev/capital_extracts/Claims_data/CLAIMS_2024082215202191"
	additional_file_name = "/home/jessedance/DRK_dev/capital_extracts/Claims_data/Additional_Claims_info_9.20.24.csv"

	sorted_claim_list_with_memo, list_of_names, list_of_payee_ids = parse_claim_files(file_name, additional_file_name)

	print_list(sorted_claim_list_with_memo)
	
	
	