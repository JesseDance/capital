import csv
import json




def parse_claim_file(file_name):
	
	sorted_claim_list = create_claim_list_of_dicts(file_name)

	list_of_names = create_list_of_names(sorted_claim_list)


	
	print()
	for item in sorted_claim_list:
        	print(json.dumps(item, indent = 4))
	print()
	for item in list_of_names:
		print(json.dumps(item, indent = 4))
	print()
	
	
	return sorted_claim_list, list_of_names

def create_claim_list_of_dicts(file_name):

	with open(file_name, 'r', encoding='utf-8-sig') as file:
		csv_reader = csv.DictReader(file)
		claim_list = [row for row in csv_reader]

	sorted_claim_list = sorted(claim_list, key=lambda x: (x['payee_name'], x['claim_number']))
	
	return sorted_claim_list

def create_list_of_names(sorted_claim_list):

	list_of_names = {item['payee_name'] for item in sorted_claim_list}
	
	return sorted(list_of_names)

if __name__ == "__main__":

	file_name = "/home/jessedance/development/capital/claims_checks/master_extract.csv"
	parse_claim_file(file_name)

	print("Done")
