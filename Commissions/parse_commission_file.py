import csv





def parse_commission_file(file_name):
	
	sorted_commission_list = create_commission_list_of_dicts(file_name)
	sorted_commission_set_list = create_commission_set_list(sorted_commission_list)
	
	'''
	print()
	print(sorted_commission_set_list)
	print()
	print(sorted_commission_list)
	print()
	'''
	
	return sorted_commission_set_list, sorted_commission_list

def create_commission_list_of_dicts(file_name):

	with open(file_name, 'r', encoding='utf-8-sig') as file:
    		csv_reader = csv.DictReader(file)
    		commission_list = [row for row in csv_reader]
    		
	sorted_commission_list = sorted(commission_list, key=lambda x: (x['spayee_number'], x['scontract_type_desc']))
	
	return sorted_commission_list
    	

def create_commission_set_list(sorted_commission_list):

	commission_set_list = set()
	
	for row in sorted_commission_list:
		spayee_number = row["spayee_number"]
		commission_set_list.add(spayee_number)
		
	sorted_commission_set_list = sorted(commission_set_list)
		
	return sorted_commission_set_list


if __name__ == "__main__":

	file_name = "/home/bwdrkr2/Data/Consulting/Capital/Commissions/Commission_File/SCSRPT057 Commission Summary.csv"
	parse_commission_file(file_name)
	
	print("Done")
	
	
	
	
	
	
	
	
	

