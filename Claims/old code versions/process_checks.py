from parse_claims_file import parse_claim_files
from process_checks_log_csv import write_log
from datetime import date
import datetime
import calendar
import json
from jinja2 import Environment, FileSystemLoader, select_autoescape
from decimal import Decimal
import process_checks_log_csv

def process_file_name(file_name, additional_file_name):

	claims_list_of_dicts, list_of_names = parse_claim_files(file_name, additional_file_name)
	month_name, check_date = get_check_dates()

	max_claims_per_check = 15
	claims_by_distinct_name_grouped = []

	log_detail_list = []
	log_header_line = create_log_header_line()
	log_detail_list.append(log_header_line)
	total_payment_amount_processed = 0 



	for distinct_name in list_of_names:

		print()
		print(distinct_name)

		total_claim_count = 0
		sublist_claim_count = 0
		check_amount = 0
		payee_amount = 0
		check_templates_filled = 0
		

		claims_by_distinct_name = list(filter(lambda name: name['Payee Name'] == distinct_name, claims_list_of_dicts))
		claims_by_name_max = []

		for claim in claims_by_distinct_name:

			sublist_claim_count +=1
			claims_by_name_max.append(claim)
			total_claim_count += 1
			
			claim_amount = claim['Check Amt']
			check_amount += Decimal(claim_amount)
			payee_amount += Decimal(claim_amount)
			total_payment_amount_processed += Decimal(claim_amount)
			log_detail_line = create_log_detail_line(claim)
			log_detail_list.append(list(log_detail_line))

			if sublist_claim_count == max_claims_per_check:
				print("items in sublist:", sublist_claim_count)
				claims_by_distinct_name_grouped.append(list(claims_by_name_max))
				sublist_claim_count = 0
				claims_by_name_max.clear()

				log_check_total_line = ['', '', '', '', '', '', check_amount]
				log_detail_list.append(list(log_check_total_line))
				check_amount = 0

		if claims_by_name_max:
			print("items in sublist:", sublist_claim_count)
			claims_by_distinct_name_grouped.append(list(claims_by_name_max))

			log_check_total_line = ['', '', '', '', '', '', check_amount]
			log_detail_list.append(list(log_check_total_line))
			check_amount = 0


		log_payee_total_line = ['', '', '', '', '', '', '', payee_amount]
		log_detail_list.append(list(log_payee_total_line))


	for claim_group in claims_by_distinct_name_grouped:

		completed_template = create_check_template(distinct_name, check_date, claim_group)
		print(completed_template)
		check_templates_filled +=1







		
		print("total claims for this name: ", total_claim_count)
		print("total groups so far: ", len(claims_by_distinct_name_grouped))
		print()


	print("total check templates filled: ", check_templates_filled)
	print()
	log_total_payment_processed_line = ['', '', '', '', '', '', '', '', total_payment_amount_processed]
	log_detail_list.append(list(log_total_payment_processed_line))
	process_checks_log_csv.main(log_detail_list)

	'''
	for item in claims_by_distinct_name_grouped:
		print(json.dumps(item, indent = 4))
	print("total groups: ", len(claims_by_distinct_name_grouped))
	'''


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

def create_check_template(distinct_name, check_date, claim_group):

	env = Environment(loader=FileSystemLoader("templates/"),autoescape=select_autoescape())
	template = env.get_template("CheckAdd.xml")

	FullName = distinct_name
	TxnDate = check_date
	Claim_List = claim_group
	completed_template = template.render(FullName=FullName, TxnDate=TxnDate, Claim_List=Claim_List)

	return completed_template

def create_log_detail_line(claim_dict):

	name = claim_dict['Payee Name']
	payee_number = claim_dict['Payee Number']
	record_id = claim_dict['Record Id']
	contract_number = claim_dict['Contract Number']
	claim_number = claim_dict['Contract Number']
	check_amount = claim_dict['Check Amt']

	row_list = [name, payee_number, record_id, contract_number, claim_number, check_amount]

	return row_list


def create_log_header_line():

	heading_list = [ 'Payee Name', 'Payee Number', 'Record Id', 'Contract Number', 'Contract Number', 'Claim Amt', 'Check Amt', 'Payee Amt', 'Total Amount Processed']

	return heading_list


if __name__ == "__main__":

	file_name = "/home/jessedance/development/capital/claims_checks/CLAIMS_20240610140346166"
	additional_file_name = "/home/jessedance/development/capital/claims_checks/Additional_Claims_info_6.12.24.csv"
	process_file_name(file_name, additional_file_name)
