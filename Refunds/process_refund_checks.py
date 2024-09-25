from parse_cancellations_file import parse_cancellation_file
from datetime import date
import datetime
import calendar
import uuid
import json
import xmltodict
import os
from jinja2 import Environment, FileSystemLoader, select_autoescape
from decimal import Decimal
from sqs_send_message import send_fifo_sqs_message
from boto_session_manager import select_service
from sqs_get_message_v2 import receive_message, delete_message
import csv

today = date.today()
today_str = str(today)
log_file_date = f"Refunds-log-{today}.csv"
log_file_name = os.path.join("/home/jessedance/DRK_dev/capital_output_logs/claims_logs/", log_file_date)
f = open(log_file_name, "w")




def process_file_name(file_name, additional_file_name):

	cancellations_list_of_dicts, list_of_names, list_of_payee_ids, pac_refund_list, nvps_refund_list = parse_cancellation_file(file_name, additional_file_name)
	month_name, check_date = get_check_dates()
	print()
	print("Month Name : ", month_name)
	print("Check Date : ", check_date)
	print()

	
	job_uuid = get_uuid()
	request_msg_que = 'https://sqs.us-east-2.amazonaws.com/028067736227/qb_xml_requests_msg_que.fifo'
	response_msg_que = 'https://sqs.us-east-2.amazonaws.com/028067736227/vendor_response_msg_que.fifo'


	max_cancellations_per_check = 15
	cancellations_by_id_grouped = []

	payee_count = len(list_of_payee_ids)
	prev_payee = ""
	payees_found = 0
	payees_not_found = 0
	vendors_created = 0
	vendors_not_created = 0
	vendors_modified = 0

	checks_processed = 0
	check_errors = 0 
	total_payments_processed = 0 
	total_payments_not_processed = 0

	create_csv_vendor_headings(today_str, file_name)

	#first sort into groups of 15 claims by name for each check
	for payee_id in list_of_payee_ids:

		print()
		print(payee_id)

		cancellations_by_id = list(filter(lambda name: name['Account'] == payee_id, cancellations_list_of_dicts))
		cancellations_by_id_max = []

		sublist_cancellation_count = 0

		for cancellation in cancellations_by_id:

			sublist_cancellation_count +=1
			cancellations_by_id_max.append(cancellation)

			if sublist_cancellation_count == max_cancellations_per_check:

				cancellations_by_id_grouped.append(list(cancellations_by_id_max))
				sublist_cancellation_count = 0
				cancellations_by_id_max.clear()


		if cancellations_by_id_max:

			cancellations_by_id_grouped.append(list(cancellations_by_id_max))
			cancellations_by_id_max.clear()



	#print(json.dumps(cancellations_by_id_grouped, indent = 4))

	for cancellation_group in cancellations_by_id_grouped:

		payee_id = get_group_payee_id(cancellation_group)

		vendor_found, qb_listid, qb_edit_sequence, qb_name, qb_companyname, qb_addr1, qb_addr2, qb_addr3, qb_city, qb_state, qb_postalcode, qb_country, qb_phone, qb_email, qb_notes, qb_vendortaxident, qb_nameoncheck = process_vendor_query_template(today_str, job_uuid, request_msg_que, response_msg_que, payee_id)
		
		#@@vendor_found = 'Y'


		if vendor_found == "N":
			print('VVVVVVVVVVVVVVVVVVVVVVV')
			print(payee_id)
			print('payee not found')
			print('VVVVVVVVVVVVVVVVVVVVVVV')

			if prev_payee != payee_id:
				payees_not_found += 1
			

			vendor_name, companyname, addr1, addr2, addr3, city, state, postalcode, country, phone, email, notes, vendortaxident = get_payee_data(cancellation_group)
			csv_line = f'"QB vendor not found", "{payee_id}", "{companyname}", "{addr1}", "{addr2}", "{addr3}", "{city}", "{state}", "{postalcode}", "{phone}", "{email}", "{notes}", "{vendortaxident}"\n'
			f.write(csv_line)

			
			vendor_added = process_vendor_add_template(today_str, job_uuid, request_msg_que, response_msg_que, vendor_name, companyname, addr1, addr2, addr3, city, state, postalcode, phone, email, notes, vendortaxident)
			
			if vendor_added == 'Y':
				print('VVVVVVVVVVVVVVVVVVVVVVV')
				print(payee_id)
				print('Vendor Added')
				print('VVVVVVVVVVVVVVVVVVVVVVV')

				csv_line = f'"QB vendor added", "{payee_id}", "{companyname}", "{addr1}", "{addr2}", "{addr3}", "{city}", "{state}", "{postalcode}", "{phone}", "{email}", "{notes}", "{vendortaxident}"\n'
				f.write(csv_line)
				if prev_payee != payee_id:
					vendors_created += 1
				
				
			if vendor_added == 'N':
				print('VVVVVVVVVVVVVVVVVVVVVVV')
				print(payee_id)
				print('Vednor Not Added')
				print('VVVVVVVVVVVVVVVVVVVVVVV')

				csv_line = f'"QB vendor not added", "{vendor_name}", "{companyname}", "{addr1}", "{addr2}", "{addr3}", "{city}", "{state}", "{postalcode}", "{phone}", "{email}", "{notes}", "{vendortaxident}"\n'
				f.write(csv_line)
				if prev_payee != payee_id:
					vendors_not_created += 1
			prev_payee = payee_id
				
			
		if vendor_found == "Y":
			print('VVVVVVVVVVVVVVVVVVVVVVV')
			print(payee_id)
			print('payee found')
			print('VVVVVVVVVVVVVVVVVVVVVVV')

			if prev_payee != payee_id:
				payees_found += 1
			

			vendor_name, companyname, addr1, addr2, addr3, city, state, postalcode, country, phone, email, notes, vendortaxident = get_payee_data(cancellation_group)

			data_changes = compare_se_to_qb_data(vendor_name, companyname, addr1, addr2, addr3, city, state, postalcode, country, phone, email, notes, vendortaxident, qb_companyname, qb_addr1, qb_addr2, qb_addr3, qb_city, qb_state, qb_postalcode, qb_country, qb_phone, qb_email, qb_notes, qb_vendortaxident, qb_nameoncheck)
			
			
			if data_changes == True:
				
				payeeactive = '1'
				completed_vendor_mod_template = create_vendor_mod(qb_listid, qb_edit_sequence, payeeactive, companyname, addr1, addr2, addr3, city, state, postalcode)
				vendor_mod_sqs_msg = create_sqs_msg(completed_vendor_mod_template, today_str, job_uuid, request_msg_que, response_msg_que)	
				send_sqs_msg(vendor_mod_sqs_msg, request_msg_que)
				received_vendor_mod_sqs_msg = receive_sqs_msg(response_msg_que)

				csv_line = f'"QB vendor modified", "{vendor_name}", "{companyname}", "{addr1}", "{addr2}", "{addr3}", "{city}", "{state}", "{postalcode}", "{phone}", "{email}", "{notes}", "{vendortaxident}"\n'
				f.write(csv_line)
				if prev_payee != payee_id:
					vendors_modified += 1
			prev_payee = payee_id


	print("payees found : ", payees_found)
	print("payees not found : ", payees_not_found)
	print("vendors created: ", vendors_created)
	print("vendors not created: ", vendors_not_created)
	print("vendors modified: ", vendors_modified)
	print()			

	create_csv_vendor_totals(payee_count, payees_found, vendors_modified, payees_not_found, vendors_created, vendors_not_created)

	#Create checks
	processed_line_list = []
	not_processed_line_list = []
	for cancellation_group in cancellations_by_id_grouped:

		payee_id = get_group_payee_id(cancellation_group)

		check_amount = 0
		#@@check_filled = 'Y'
		check_filled = process_bill_template(today_str, job_uuid, request_msg_que, response_msg_que, payee_id, check_date, cancellation_group)
		if check_filled == 'Y':	
			checks_processed +=1

			for cancellation in cancellation_group:
				
				payee_name = cancellation['Payee Name']
				payee_number = cancellation['Account']
				contract_number = cancellation['Contract Number']
				cancellation_amount = cancellation['Cancellation_Amt']
				check_amount += Decimal(cancellation_amount)
				total_payments_processed += Decimal(cancellation_amount)
				contract_holder_last_name = cancellation['Contract Holder Last Name']
				#seller_name = cancellation['Seller Name']
				csv_line = f'"{payee_name}", "{payee_number}", "{cancellation_amount}", "{contract_holder_last_name}", \n'
				processed_line_list.append(csv_line)
			csv_line = create_csv_refunds_total_line("check", check_amount)
			processed_line_list.append(csv_line)



		if check_filled == 'N':
			check_errors +=1

			for cancellation in cancellation_group:
				
				payee_name = cancellation['Payee Name']
				payee_number = cancellation['Account']
				contract_number = cancellation['Contract Number']
				cancellation_amount = cancellation['Cancellation_Amt']
				check_amount += Decimal(cancellation_amount)
				total_payments_not_processed += Decimal(cancellation_amount)
				contract_holder_last_name = cancellation['Contract Holder Last Name']
				#seller_name = cancellation['Seller Name']
				csv_line = f'"{payee_name}", "{payee_number}", "{cancellation_amount}", "{contract_holder_last_name}", \n'
				not_processed_line_list.append(csv_line)
			csv_line = create_csv_refunds_total_line("check", check_amount)
			not_processed_line_list.append(csv_line)

	create_csv_refunds_processed_headings()
	csv_line = create_csv_refunds_total_line("processed", total_payments_processed)
	processed_line_list.append(csv_line)
	write_csv_lines_from_list(processed_line_list)

	print("Checks processed: ", checks_processed)
	print("Checks not processed: ", check_errors)

	csv_data = '\n'
	f.write(csv_data)

	create_csv_refunds_not_processed_headings()
	csv_line = create_csv_refunds_total_line("not processed", total_payments_not_processed)
	not_processed_line_list.append(csv_line)
	write_csv_lines_from_list(not_processed_line_list)
	#f.close()

	write_pac_refunds(pac_refund_list, file_name, today_str)
	write_nvps_refunds(nvps_refund_list, file_name, today_str)



def get_group_payee_id(cancellation_group):
	for cancellation in cancellation_group:
		group_payee_id = cancellation['Account']

	return group_payee_id


def create_vendor_query_template(payee_id):

	env = Environment(loader=FileSystemLoader("templates/"),autoescape=select_autoescape())
	template = env.get_template("Vendor_Query.XML")
	completed_template = template.render(Vendor_Name=payee_id)

	return completed_template


def process_vendor_query_template(today_str, job_uuid, request_msg_que, response_msg_que, payee_id):

	completed_template = create_vendor_query_template(payee_id)
	query_msg = create_sqs_msg(completed_template, today_str, job_uuid, request_msg_que, response_msg_que )
	send_sqs_msg(query_msg, request_msg_que)
	qb_response_dict = receive_sqs_msg(response_msg_que)
	print("XXXXXXXXXXXXXXXXXXX")
	print(qb_response_dict)
	print("XXXXXXXXXXXXXXXXXXX")
	api_name = "VendorQueryRs"
	job_number, job_date, request_date_time, response_date_time, request_number, request_msg_que, response_msg_que, quickbooks_response_dict = get_response_details(qb_response_dict)
	statuscode, statusseverity, statusmessage = get_response_status(quickbooks_response_dict, api_name)

	print("")
	print("Status Code : ",statuscode)

	if statuscode == "0":

		vendor_found = "Y"


		qb_listid, qb_edit_sequence, qb_name, qb_companyname, qb_addr1, qb_addr2, qb_addr3, qb_city, qb_state, qb_postalcode, qb_country, qb_phone, qb_email, qb_notes, qb_vendortaxident, qb_nameoncheck = get_vendor_query_data(quickbooks_response_dict)

		print("Done in Query Data")
	
		print()
		print("Dance Jesse")	
		print()
		print("QB Vendor Response Dict : ",quickbooks_response_dict)
		print("Vendor Template :", completed_template)
		print()		
		print("Vendor Status : ", statuscode)
		print("Vendor Severity : ",statusseverity)
		print("Vendor Status :",statusmessage)
		print("Dance Jesse")
		print()

	else:

		vendor_found = "N"
		qb_listid = ""
		qb_edit_sequence = ""
		qb_name = ""
		qb_companyname = ""
		qb_addr1 = ""
		qb_addr2 = ""
		qb_addr3 = ""
		qb_city = ""
		qb_state = ""
		qb_postalcode = ""
		qb_country = ""
		qb_phone = ""
		qb_email = ""
		qb_notes = ""
		qb_vendortaxident = ""
		qb_nameoncheck = ""


	return vendor_found, qb_listid, qb_edit_sequence, qb_name, qb_companyname, qb_addr1, qb_addr2, qb_addr3, qb_city, qb_state, qb_postalcode, qb_country, qb_phone, qb_email, qb_notes, qb_vendortaxident, qb_nameoncheck


def get_vendor_query_data(quickbooks_response_dict):


	listid =  ""
	edit_sequence = ""
	vendor_name = ""
	companyname = ""
	addr1 = ""
	addr2 = ""
	addr3 = ""
	city = ""
	state = ''
	postalcode = ""
	country = ""
	phone = ""
	email = ""
	notes = ""
	vendortaxident = ""
	nameoncheck = ""

	
	listid = quickbooks_response_dict.get('QBXML').get('QBXMLMsgsRs').get('VendorQueryRs').get('VendorRet').get('ListID')
	if listid == None:
		listid = ""
	edit_sequence = quickbooks_response_dict.get('QBXML').get('QBXMLMsgsRs').get('VendorQueryRs').get('VendorRet').get('EditSequence')
	if edit_sequence == None:
		edit_sequence = ""
	vendor_name = quickbooks_response_dict.get('QBXML').get('QBXMLMsgsRs').get('VendorQueryRs').get('VendorRet').get('Name')
	if vendor_name == None:
		vendor_name = ""
	companyname = quickbooks_response_dict.get('QBXML').get('QBXMLMsgsRs').get('VendorQueryRs').get('VendorRet').get('CompanyName')
	if companyname == None:
		companyname = ""
	addr1 = quickbooks_response_dict.get('QBXML').get('QBXMLMsgsRs').get('VendorQueryRs').get('VendorRet').get('VendorAddress').get('Addr1')
	if addr1 == None:
		addr1 = ""
	addr2 = quickbooks_response_dict.get('QBXML').get('QBXMLMsgsRs').get('VendorQueryRs').get('VendorRet').get('VendorAddress').get('Addr2')
	if addr2 == None:
		addr2 = ""
	addr3 = quickbooks_response_dict.get('QBXML').get('QBXMLMsgsRs').get('VendorQueryRs').get('VendorRet').get('VendorAddress').get('Addr3')
	if addr3 == None:
		addr3 = ""
	city = quickbooks_response_dict.get('QBXML').get('QBXMLMsgsRs').get('VendorQueryRs').get('VendorRet').get('VendorAddress').get('City')
	if city == None:
		city = ""
	state = quickbooks_response_dict.get('QBXML').get('QBXMLMsgsRs').get('VendorQueryRs').get('VendorRet').get('VendorAddress').get('State')
	if state == None:
		state = ""
	postalcode = quickbooks_response_dict.get('QBXML').get('QBXMLMsgsRs').get('VendorQueryRs').get('VendorRet').get('VendorAddress').get('PostalCode')
	if postalcode == None:
		postalcode = ""
	country = quickbooks_response_dict.get('QBXML').get('QBXMLMsgsRs').get('VendorQueryRs').get('VendorRet').get('VendorAddress').get('Country')
	if country == None:
		country = ""
	phone = quickbooks_response_dict.get('QBXML').get('QBXMLMsgsRs').get('VendorQueryRs').get('VendorRet').get('Phone')
	if phone == None:
		phone = ""
	email = quickbooks_response_dict.get('QBXML').get('QBXMLMsgsRs').get('VendorQueryRs').get("VendorRet").get("Email")
	if email == None:
		email = ""
	notes = quickbooks_response_dict.get('QBXML').get('QBXMLMsgsRs').get('VendorQueryRs').get("VendorRet").get("Notes")
	if notes == None:
		notes = ""
	vendortaxident = quickbooks_response_dict.get('QBXML').get('QBXMLMsgsRs').get('VendorQueryRs').get("VendorRet").get("VendorTaxIdent")
	if vendortaxident == None:
		vendortaxident = ""
	nameoncheck = quickbooks_response_dict.get('QBXML').get('QBXMLMsgsRs').get('VendorQueryRs').get('VendorRet').get("NameOnCheck")
	if nameoncheck == None:
		nameoncheck = ""


	return listid, edit_sequence, vendor_name, companyname, addr1, addr2, addr3, city, state, postalcode, country, phone, email, notes, vendortaxident, nameoncheck


def process_vendor_add_template(today_str, job_uuid, request_msg_que, response_msg_que, payee_id ,companyname, addr1, addr2, addr3, city, state, postalcode, phone, email, notes, vendortaxident):

	payee_active = '1'
	completed_template = create_vendor_add_template(payee_active, payee_id, companyname, addr1, addr2, addr3, city, state, postalcode, phone, email, notes, vendortaxident)
	vendor_add_msg = create_sqs_msg(completed_template, today_str, job_uuid, request_msg_que, response_msg_que )
	send_sqs_msg(vendor_add_msg, request_msg_que)
	qb_response_dict = receive_sqs_msg(response_msg_que)
	api_name = "VendorAddRs" 
	job_number, job_date, request_date_time, response_date_time, request_number, request_msg_que, response_msg_que, quickbooks_response_dict = get_response_details(qb_response_dict)
	statuscode, statusseverity, statusmessage = get_response_status(quickbooks_response_dict, api_name)
	
	if statuscode == "0" :
		vendor_added= "Y"
	else:
		vendor_added = "N"

	return vendor_added


def get_payee_data(cancellation_group):

	for cancellation in cancellation_group:
		vendor_name = cancellation['Account']
		companyname = cancellation['Payee Name']
		addr1 = cancellation['Payee Address1']
		addr2 = cancellation['Payee Address2']
		addr3 = ""
		city = cancellation['Payee City']
		state = cancellation['Payee State']
		postalcode = cancellation['Payee Zip']
		country = ""
		phone = ""
		email = ""
		vendortaxident = ""
		notes = ""

	return vendor_name, companyname, addr1, addr2, addr3, city, state, postalcode, country, phone, email, notes, vendortaxident
			

def create_vendor_add_template(payee_active, payeenumber, companyname, addr1, addr2, addr3, city, state, postalcode, phone, email, notes, vendortaxident):
	
	env = Environment(loader=FileSystemLoader("templates/"),autoescape=select_autoescape())
	template = env.get_template("Vendor_Add.XML")
	
	IsActive = payee_active
	VendorAddName = payeenumber
	CompanyName = companyname
	NameOnCheck = companyname
	Addr1 = addr1
	Addr2 = addr2
	Addr3 = addr3
	City = city
	State = state
	PostalCode = postalcode
	Email = email
	Phone = phone 
	VendorTaxIdent = vendortaxident
	Notes = notes
	completed_template = template.render(IsActive=IsActive,VendorAddName=VendorAddName ,CompanyName=CompanyName, Addr1=Addr1, Addr2=Addr2, Addr3=Addr3, City=City, State=State, PostalCode=PostalCode, Phone=Phone, Email=Email, VendorTaxIdent=VendorTaxIdent, Notes=Notes, NameOnCheck=NameOnCheck)

	return completed_template


def compare_se_to_qb_data(payeenumber, companyname, addr1, addr2, addr3, city, state, postalcode, country, phone, email, notes, vendortaxident, qb_companyname, qb_addr1, qb_addr2, qb_addr3, qb_city, qb_state, qb_postalcode, qb_country, qb_phone, qb_email, qb_notes, qb_vendortaxident, qb_nameoncheck):

	print("COMPANY NAME")
	print(companyname)
	print("COMPANY NAME")
	print("QB COMPANY NAME")
	print(qb_companyname)
	print("QB COMPANY NAME")
	
	

	data_changes = False
	
	companyname = companyname.lower()
	qb_companyname = qb_companyname.lower()
	addr1 = addr1.lower()
	qb_addr1 = qb_addr1.lower()
	addr2 = addr2.lower()
	qb_addr2 = qb_addr2.lower()
	city = city.lower()
	qb_city = qb_city.lower()
	state = state.lower()
	qb_state = qb_state.lower()
	postalcode = postalcode.lower()
	qb_postalcode = qb_postalcode.lower()
	country = country.lower()
	qb_country = qb_country.lower()
	phone = phone.lower()
	qb_phone = qb_phone.lower()
	email = email.lower()
	qb_email = qb_email.lower()
	notes = notes.lower()
	qb_notes = qb_notes.lower()
	
	vendortaxident = str(vendortaxident)
	vendortaxident = vendortaxident.lower()
	qb_vendortaxident = qb_vendortaxident.lower()

	qb_nameoncheck = qb_nameoncheck.lower()
	
	
	companyname = companyname.strip()
	addr1 = addr1.strip()
	addr2 = addr2.strip()
	addr3 = addr3.strip()
	city = city.strip()
	state = state.strip()
	postalcode = postalcode.strip()
	country = country.strip()
	phone = phone.strip()
	email = email.strip()
	notes = notes.strip()
	vendortaxident.strip()

	qb_companyname = qb_companyname.strip()
	qb_addr1 = qb_addr1.strip()
	qb_addr2 = qb_addr2.strip()
	qb_addr3 = qb_addr3.strip()
	qb_city = qb_city.strip()
	qb_state = qb_state.strip()
	qb_postalcode = qb_postalcode.strip()
	qb_country = qb_country.strip()
	qb_phone = qb_phone.strip()
	qb_email = qb_email.strip()
	qb_notes = qb_notes.strip()
	qb_vendortaxident = qb_vendortaxident.strip()
	qb_nameoncheck = qb_nameoncheck.strip()
	

	if qb_nameoncheck != companyname:
		data_changes = True


	#if companyname != qb_companyname:
		#companyname = companyname.strip()
		#data_changes = True

	if addr1 != qb_addr1:
		#addr1 = addr1.strip()
		#print(companyname)
		print("Address 1")
		print("Stone Eagle : ",addr1) 
		print("QuickBooks  : ",qb_addr1)
		print()
		data_changes = True
	if addr2 != qb_addr2:
		#addr2 = addr2.strip()
		print(companyname)
		print("Address 2")
		print("Stone Eagle : ",addr2)
		print("QuickBooks  : ",qb_addr2)
		print()
		data_changes = True
	#if addr3 != qb_addr3:
		#addr3 = addr3.strip()
		#print(companyname)
		#print("Address 3")
		#print("Stone Eagle : ",addr3)
		#print("QuickBooks  : ",qb_addr3)
		#print()
		#data_changes = True		
	if city != qb_city:
		#print(companyname)
		print("City")
		print("Stone Eagle : ",city)
		print("QuickBooks  : ",qb_city)
		print()
		data_changes = True
	if state != qb_state:
		#print(companyname)
		print("State")
		print("Stone Eagle : ",state)
		print("QuickBooks  : ",qb_state)
		print()
		data_changes = True
	if postalcode != qb_postalcode:
		#print(companyname)
		print("Postal Code")
		print("Stone Eagle : ",postalcode)
		print("QuickBooks  : ",qb_postalcode)
		print()
		data_changes = True
	#if country != qb_country:
		#print(companyname)
		#print("Country")
		#print("Stone Eagel : ",country )
		#print("QuickBooks  : ",qb_country)
		#print()
		#data_changes = True
	#if phone != qb_phone:
		#print(companyname)
		#print("Phone")
		#print("Stone Eagle : ",phone)
		#print("QuickBooks  : ",qb_phone)
		#print()
		#data_changes = True
	#if email != qb_email:
		#print(companyname)
		#print("Email")
		#print("Stone Eagle : ",email)
		#print("QuickBooks  : ",qb_email)
		#print()
		#data_changes = True
	'''
	elif notes != qb_notes:
		print("Notes")
		print(notes + " " + qb_notes)
		data_changes = True
	'''
	#if vendortaxident != qb_vendortaxident:
		#print("Tax Changes")
		#print("Tax Changes")
		#print(vendortaxident, qb_vendortaxident)
		#data_changes = True
	
	print("Data Changes ", data_changes)
	
	'''
	if data_changes == True:
		

		
		qb_data = None
		se_data = None
		qb_data = f'"QuickBooks Existing Payee", "{payeenumber}", "{companyname}", "{qb_addr1}", "{qb_addr2}", "{qb_addr3}", "{qb_city}", "{qb_state}", "{qb_postalcode}", "{qb_country}", "{qb_phone}", "{qb_email}", "{qb_notes}"\n'
		se_data = f'"QuickBooks Updated Payee","{payeenumber}", "{companyname}", "{addr1}", "{addr2}", "{addr3}", "{city}", "{state}", "{postalcode}", "{country}", "{phone}", "{email}", "{notes}"\n'
		f.write(qb_data)
		f.write(se_data)

		print(qb_data)
		print(se_data)
	'''
		

	return data_changes 


def create_vendor_mod(list_id, edit_sequence, payeeactive, company_name, addr1, addr2, addr3, city, state, postal_code):

	env = Environment(loader=FileSystemLoader("templates/"),autoescape=select_autoescape())
	template = env.get_template("Vendor_Mod.XML")
	completed_template = template.render(List_ID=list_id, Edit_Sequence=edit_sequence, IsActive=payeeactive, Company_Name=company_name, Addr1=addr1, Addr2=addr2, Addr3=addr3, City=city, State=state, Postal_Code=postal_code, NameOnCheck=company_name)
	
	print("*KKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK")
	print(completed_template)
	print("*KKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK")
	
	
	
	return completed_template


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

def get_uuid():

	current_uuid = uuid.uuid4()
	current_uuid_str = str(current_uuid)

	return current_uuid_str


def create_check_template(payee_id, check_date, cancellation_group):

	env = Environment(loader=FileSystemLoader("templates/"),autoescape=select_autoescape())
	template = env.get_template("CheckAdd-cancels.xml")

	FullName = payee_id
	TxnDate = check_date
	Cancellation_List = cancellation_group
	completed_template = template.render(FullName=FullName, TxnDate=TxnDate, Cancellation_List=Cancellation_List)

	return completed_template

def create_sqs_msg(completed_template, today_str, job_uuid, request_msg_que, response_msg_que):

	cancellation_dict = {}
	#cancellation_list = []
	
	request_date_time = datetime.datetime.now()
	request_date_time = str(request_date_time)			
	current_uuid_str = get_uuid()
	cancellation_dict["job_number"] = job_uuid
	cancellation_dict["job_date"] = today_str
	cancellation_dict["request_date_time"] = request_date_time
	cancellation_dict["response_date_time"] = " "
	cancellation_dict["request_number"] = current_uuid_str
	cancellation_dict["request_msg_que"] = request_msg_que
	cancellation_dict['response_msg_que'] = response_msg_que
	cancellation_dict["quickbooks_request_xml"] = completed_template
	cancellation_msg= json.dumps(cancellation_dict)
	#cancellation_list.append(cancellation_string)
	cancellation_msg = cancellation_msg + "\n"
	
	print()
	print("SQS Message : ",cancellation_msg)
	print()
	
	
	return cancellation_msg


def send_sqs_msg(message, request_msg_que):

	httpsstatuscode = None
	error = "N"
	
	while httpsstatuscode != 200:
		QueueUrl = request_msg_que
		MessageGroupId="qb_xml_request_msg_que"
		status_msg =send_fifo_sqs_message(message, QueueUrl, MessageGroupId)
		responsematadata = status_msg.get("ResponseMetadata")
		httpsstatuscode = responsematadata.get("HTTPStatusCode")
		
		if httpsstatuscode != 200:
			error = "Y"
			# write to report not send to QB
		
	return


def receive_sqs_msg(response_msg_que):

	sqs_msg = None

	while sqs_msg == None:
		QueueUrl = response_msg_que
		msg = receive_message(QueueUrl)
		

		if not msg:
			print("No messages to process in message que")
			#time.sleep(5)
		else:

			receipt_handle = msg.get('receipt_handle')
			
			sqs_msg = msg.get('msg_content')
			delete = delete_message(receipt_handle, QueueUrl)

			print("")
			print("QueueUrl : ",QueueUrl)
			print("Recipt Handle : ",receipt_handle)
			print("SQS Message : ",sqs_msg)
			print("")

	return sqs_msg

def get_response_details(response_msg_dict):

	job_number = response_msg_dict['job_number']
	job_date = response_msg_dict['job_date']
	request_date_time = response_msg_dict['request_date_time']
	response_date_time = response_msg_dict['response_date_time']
	request_number = response_msg_dict['request_number']
	request_msg_que = response_msg_dict['request_msg_que']
	response_msg_que = response_msg_dict['response_msg_que']
	quickbooks_response_xml = response_msg_dict['quickbooks_response_xml']

	quickbooks_response_dict = convert_xml_to_json(quickbooks_response_xml)

	return job_number, job_date, request_date_time, response_date_time, request_number, request_msg_que, response_msg_que, quickbooks_response_dict


def get_response_status(quickbooks_response_dict, api_name):

	statuscode = quickbooks_response_dict['QBXML']['QBXMLMsgsRs'][api_name]['@statusCode']
	statusseverity = quickbooks_response_dict['QBXML']['QBXMLMsgsRs'][api_name]['@statusSeverity']
	statusmessage = quickbooks_response_dict['QBXML']['QBXMLMsgsRs'][api_name]['@statusMessage']

	return statuscode, statusseverity, statusmessage


def convert_xml_to_json(quickbooks_response_xml):

	quickbooks_response_json = xmltodict.parse(quickbooks_response_xml)

	return quickbooks_response_json


def process_bill_template(today_str, job_uuid, request_msg_que, response_msg_que, payee_id, check_date, cancellation_group):

	completed_template = create_check_template(payee_id, check_date, cancellation_group)
	commission_msg = create_sqs_msg(completed_template, today_str, job_uuid, request_msg_que, response_msg_que )
	send_sqs_msg(commission_msg, request_msg_que)
	qb_response_dict = receive_sqs_msg(response_msg_que)
	api_name = "CheckAddRs" 
	job_number, job_date, request_date_time, response_date_time, request_number, request_msg_que, response_msg_que, quickbooks_response_dict = get_response_details(qb_response_dict)
	statuscode, statusseverity, statusmessage = get_response_status(quickbooks_response_dict, api_name)
				
	if statuscode == "0":
		check_filled = 'Y'	
	else:
		check_filled = 'N'

	print(statuscode)
	print(statusseverity)
	print(statusmessage)
	#exit()
				
	return check_filled


def create_csv_vendor_headings(today_str, file_name):


	col_01 = "Message"
	col_02 = "Payee ID"
	col_03 = "Company Name"
	col_04 = "Address Line" 
	col_05 = "Address Line 2"
	col_06 ="Address Line 3"
	col_07 = "City"
	col_08 = "State"
	col_09 = "Zip"
	col_10 = "phone"
	col_11 = "Email"
	col_12 = "Tax Id"
	col_13 = "Notes"
	

	csv_data = "\n"
	f.write(csv_data)
	csv_data = "Refunds extract processing"
	f.write(csv_data)
	csv_data = "\n"
	f.write(csv_data)
	csv_data = f"Date processed: {today_str} \n"
	f.write(csv_data)
	csv_data = f"File name: {file_name} \n"
	f.write(csv_data)
	csv_data = "\n"

	csv_data = f"{col_01}, {col_02}, {col_03}, {col_04}, {col_05}, {col_06}, {col_07}, {col_08}, {col_09}, {col_10}, {col_11}, {col_12}, {col_13} \n" 
	f.write(csv_data)
	csv_data = "\n"
	f.write(csv_data)
	csv_data = "\n"
	f.write(csv_data)


	return


def create_csv_vendor_totals(payee_count, payees_found, vendors_modified, payees_not_found, vendors_created, vendors_not_created):

	csv_data = "\n"
	f.write(csv_data)
	csv_data = f"Total Payees in extract , {payee_count} \n" 
	f.write(csv_data)
	csv_data = f"Total Payees found in QB , {payees_found} \n" 
	f.write(csv_data)
	csv_data = f"Total Payees modified in QB , {vendors_modified} \n" 
	f.write(csv_data)
	csv_data = f"Total Payees not found in QB , {payees_not_found} \n" 
	f.write(csv_data)
	csv_data = f"Total QB Vendors Created  , {vendors_created} \n" 
	f.write(csv_data)
	csv_data = f"Total QB Vendors Not Created , {vendors_not_created} \n"
	f.write(csv_data)

	
	csv_data = "\n"
	f.write(csv_data)

	return


def create_csv_refunds_processed_headings():


	col_1 = 'Payee Number'
	col_2 = 'Payee Name'

	#col_3 = 'Contract Number'

	col_4 = 'Refund Ammount'

	col_5 = 'Contract Holder Last Name'
	col_6 = 'Check Amount'

	csv_data = 'Refunds Processed'
	f.write(csv_data)
	csv_data = '\n'
	f.write(csv_data)
	csv_data = f"{col_1}, {col_2}, {col_4}, {col_5}, {col_6}\n" 
	f.write(csv_data)

def create_csv_refunds_not_processed_headings():


	col_1 = 'Payee Number'
	col_2 = 'Payee Name'

	#col_3 = 'Contract Number'

	col_4 = 'Refund Amount'

	col_5 = 'Contract Holder Last Name'
	col_6 = 'Check Amount'

	csv_data = 'Refunds Not Processed'
	f.write(csv_data)
	csv_data = '\n'
	f.write(csv_data)
	csv_data = f"{col_1}, {col_2}, {col_4}, {col_5}, {col_6}\n" 
	f.write(csv_data)


def create_csv_refunds_total_line(total_type, cancellation_total):

	if total_type == "check":
		csv_data = f" ,  ,  ,  , {cancellation_total} \n"
		#f.write(csv_data)

	'''
	if total_type == "payee":
		csv_data = f"*, *, *, *, *, {cancellation_total} "
		#f.write(csv_data)
	'''

	if total_type == "processed":
		csv_data = f"Total processed, {cancellation_total} \n"
		#f.write(csv_data)

	if total_type == "not processed":
		csv_data = f"Total not processed, {cancellation_total} \n"
		#f.write(csv_data)


	#csv_data = "\n"
	#f.write(csv_data)

	return csv_data


def write_csv_lines_from_list(line_list):

	for line in line_list:
		csv_data = line
		f.write(csv_data)

	return

def write_pac_refunds(pac_refund_list, file_name, today_str):

	output_file_name = f"pac_extract_{today_str}.csv"

	with open(output_file_name, mode='w', newline='') as j:


		csv_data = "PAC refunds extract processing, \n"
		j.write(csv_data)

		csv_data = "\n"
		j.write(csv_data)
		csv_data = f"Date processed:, {today_str}, \n"
		j.write(csv_data)
		csv_data = f"File name:, {file_name}, \n"
		j.write(csv_data)
		csv_data = "\n"

		headers = pac_refund_list[0].keys()

		csv_writer = csv.DictWriter(j, fieldnames=headers)

		csv_writer.writeheader()

		csv_writer.writerows(pac_refund_list)


	return

def write_nvps_refunds(nvps_refund_list, file_name, today_str):

	output_file_name = f"nvps_extract_{today_str}.csv"

	with open(output_file_name, mode='w', newline='') as k:


		csv_data = "NVPS refunds extract processing, \n"
		k.write(csv_data)

		csv_data = "\n"
		k.write(csv_data)
		csv_data = f"Date processed:, {today_str}, \n"
		k.write(csv_data)
		csv_data = f"File name:, {file_name}, \n"
		k.write(csv_data)
		csv_data = "\n"

		headers = nvps_refund_list[0].keys()

		csv_writer = csv.DictWriter(k, fieldnames=headers)

		csv_writer.writeheader()

		csv_writer.writerows(nvps_refund_list)

	return


if __name__ == "__main__":

	file_name = "/home/jessedance/DRK_dev/capital_extracts/Refunds_data/REFUNDS_20240612070442343"
	additional_file_name = "/home/jessedance/DRK_dev/capital_extracts/Refunds_data/PAC sellers list.csv"
	process_file_name(file_name, additional_file_name)
